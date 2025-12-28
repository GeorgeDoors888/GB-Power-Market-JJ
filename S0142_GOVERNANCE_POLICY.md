# S0142 Governance Policy
**Date**: 28 December 2025
**Status**: APPROVED
**Authority**: Data Engineering / Analytics Team

## Executive Summary

This policy governs the ingestion, storage, and usage of Elexon P114 S0142 settlement data in the `uk_energy_prod.elexon_p114_s0142_bpi` table. Settlement data is versioned and mutable, requiring explicit rules for which runs to trust and how to handle duplicates.

**Decision**: **Option 2 - Hybrid Latest-Available Strategy**

## Background

### The Problem

S0142 settlement data is reissued through multiple runs as more accurate information becomes available:

| Run | Timing | Description |
|-----|--------|-------------|
| **II** | T+1 day | Interim Initial - earliest estimate |
| **SF** | T+5 days | Settlement Final - week-end close |
| **R1** | T+1 month | Reconciliation 1 - monthly correction |
| **R2** | T+4 months | Reconciliation 2 - quarterly adjustment |
| **R3** | T+14 months | Reconciliation 3 - annual review |
| **RF** | T+28 months | Reconciliation Final - final authority |
| **DF** | Variable | Default Final - error corrections |

**Key Issue**: Same settlement date/period/unit appears in multiple runs with different values. Without policy, queries return duplicates or inconsistent results.

## Policy Decision: Hybrid Latest-Available

### Strategy

Use **best available run** for each settlement date based on data age:

1. **RF (Reconciliation Final)** if available (data >28 months old) → **Highest Accuracy**
2. **R3** if RF not yet issued (data 14-28 months old) → **Very High Accuracy**
3. **II (Interim Initial)** for recent data (<14 months) → **Timely but preliminary**

### Rationale

**Advantages**:
- ✅ Balances accuracy and timeliness
- ✅ Enables both historical analysis (RF) and real-time monitoring (II)
- ✅ Matches business decision timelines (monthly/quarterly reporting)
- ✅ Avoids 28-month lag on all data
- ✅ Single view for analysts (complexity hidden)

**Disadvantages**:
- ⚠️ Revenue estimates change as runs update (II → R3 → RF)
- ⚠️ Requires deduplication logic in views
- ⚠️ Must communicate data maturity to stakeholders

## Implementation

### 1. Raw Table: elexon_p114_s0142_bpi

**Purpose**: Store ALL runs for audit trail and flexibility

**Schema**: Current schema (includes `settlement_run` column)

**Policy**:
- Ingest all available runs (II, SF, R1, R2, R3, RF, DF)
- Never delete historical runs
- Partition by `settlement_date`
- Cluster by `bm_unit_id`, `settlement_run`

**Query Pattern**: Direct queries must specify run explicitly
```sql
-- CORRECT: Specify run
SELECT * FROM elexon_p114_s0142_bpi
WHERE settlement_run = 'RF' AND settlement_date >= '2022-01-01'

-- INCORRECT: No run filter (returns duplicates)
SELECT * FROM elexon_p114_s0142_bpi
WHERE settlement_date >= '2022-01-01'
```

### 2. Canonical View: p114_settlement_canonical

**Purpose**: Provide single-version-of-truth for analysts

**Implementation**:
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.p114_settlement_canonical` AS
SELECT
  bm_unit_id,
  settlement_date,
  settlement_period,
  settlement_run,
  value2,
  system_price,
  multiplier,
  generation_timestamp,
  zone,
  value1,
  value3,
  _ingested_utc,
  -- Metadata for transparency
  CASE settlement_run
    WHEN 'RF' THEN 'Final (28mo lag)'
    WHEN 'R3' THEN 'High Confidence (14mo lag)'
    WHEN 'R2' THEN 'Medium Confidence (4mo lag)'
    WHEN 'R1' THEN 'Early Reconciliation (1mo lag)'
    WHEN 'SF' THEN 'Settlement Final (5d lag)'
    WHEN 'II' THEN 'Interim (1d lag - preliminary)'
    WHEN 'DF' THEN 'Default/Correction'
    ELSE 'Unknown'
  END as data_maturity
FROM (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY bm_unit_id, settlement_date, settlement_period
      ORDER BY
        -- Run priority: prefer more accurate runs
        CASE settlement_run
          WHEN 'RF' THEN 1  -- Highest priority
          WHEN 'R3' THEN 2
          WHEN 'R2' THEN 3
          WHEN 'R1' THEN 4
          WHEN 'SF' THEN 5
          WHEN 'II' THEN 6
          WHEN 'DF' THEN 7  -- Lowest (except for specific corrections)
          ELSE 8
        END,
        -- If duplicate runs (rare), prefer latest generation
        generation_timestamp DESC
    ) as row_rank
  FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
)
WHERE row_rank = 1
```

**Usage**: Default view for all analysis queries
```sql
-- Analysts should use this view
SELECT * FROM p114_settlement_canonical
WHERE settlement_date >= '2024-01-01'
-- No run filter needed - deduplication handled automatically
```

### 3. Run-Specific Views (Optional)

For scenarios requiring specific run versions:

```sql
-- Real-time monitoring: II only
CREATE OR REPLACE VIEW p114_settlement_interim AS
SELECT * FROM elexon_p114_s0142_bpi
WHERE settlement_run = 'II'

-- Regulatory compliance: RF only
CREATE OR REPLACE VIEW p114_settlement_final AS
SELECT * FROM elexon_p114_s0142_bpi
WHERE settlement_run = 'RF'
```

## Data Quality Rules

### Validation Checks

1. **Period Completeness**: Each date should have 48 periods per unit
```sql
SELECT settlement_date, bm_unit_id, COUNT(DISTINCT settlement_period) as periods
FROM p114_settlement_canonical
WHERE settlement_date = '2024-10-15'
GROUP BY settlement_date, bm_unit_id
HAVING COUNT(DISTINCT settlement_period) != 48
```

2. **System Price Validity**: Prices should be within reasonable bounds
```sql
SELECT COUNT(*) as anomalies
FROM p114_settlement_canonical
WHERE system_price < -500 OR system_price > 10000  -- £/MWh
```

3. **Run Supersession**: Verify RF exists for dates >28 months old
```sql
SELECT settlement_date, MAX(settlement_run) as latest_run
FROM elexon_p114_s0142_bpi
WHERE settlement_date < DATE_SUB(CURRENT_DATE(), INTERVAL 28 MONTH)
GROUP BY settlement_date
HAVING MAX(settlement_run) != 'RF'
```

## Backfill Strategy

### Phase-Based Approach

**Phase 1: Historical Data (2022-2023)**
- **Target Run**: RF only
- **Rationale**: Final settlement available (28-month lag satisfied)
- **Query Window**: generation_date 2024-06-01 to 2025-12-28 (captures RF for 2022-2023 settlement dates)
- **Expected Records**: ~200M BPI records

**Phase 2: Recent History (2024)**
- **Target Run**: R3 primary, supplement with R2/R1 if gaps
- **Rationale**: RF not yet available, R3 is best balance
- **Query Window**: generation_date 2024-03-01 to 2025-12-28
- **Expected Records**: ~100M BPI records

**Phase 3: Current Period (2025)**
- **Target Run**: II (Interim Initial)
- **Rationale**: Only run available for recent data
- **Query Window**: generation_date 2025-01-02 to 2025-12-29
- **Expected Records**: ~100M BPI records

### Incremental Updates

**Policy**: Daily ingestion of II runs for rolling 30-day window
```bash
# Cron: Daily at 02:00
python3 ingest_p114_s0142.py $(date -d "30 days ago" +%Y-%m-%d) $(date +%Y-%m-%d) II
```

**Policy**: Monthly ingestion of R1/R2/R3 runs as they become available
```bash
# Cron: 1st of month at 03:00
python3 ingest_p114_s0142.py $(date -d "14 months ago" +%Y-%m-%01) $(date -d "1 month ago" +%Y-%m-%01) R3
```

### Data Refresh Strategy by Age

**How We Update P114 Settlement Data**:

The hybrid strategy uses different settlement runs based on data age to balance accuracy and timeliness:

1. **Historical Data (>28 months old)**: Use **RF (Reconciliation Final)** runs
   - Most accurate, fully reconciled
   - Available for: 2022-2023 (~730 days)
   - Update frequency: One-time backfill (RF is final, rarely changes)
   - Command: `python3 ingest_p114_batch.py 2022-01-01 2023-12-31 RF`

2. **Recent Historical (14-28 months old)**: Use **R3 (3rd Reconciliation)** runs
   - High confidence, near-final
   - Available for: 2024 (~366 days)
   - Update frequency: One-time backfill, optional R3→RF upgrade when RF becomes available
   - Command: `python3 ingest_p114_batch.py 2024-01-01 2024-12-31 R3`

3. **Current Data (<14 months old)**: Use **II (Interim Initial)** runs
   - Preliminary but timely
   - Available for: 2025 (~300+ days)
   - Update frequency: Daily for rolling window, monthly II→R3 upgrade as R3 becomes available
   - Command: `python3 ingest_p114_batch.py 2025-01-01 2025-12-31 II`

**Automated Full Refresh**:
```bash
# Run complete backfill with hybrid strategy (background process)
nohup ./execute_full_p114_backfill.sh > logs/p114_backfill/full_execution.log 2>&1 &

# This script automatically:
# - Phase 1: Backfills RF for 2022-2023 (730 days, highest accuracy)
# - Phase 2: Backfills R3 for 2024 (366 days, high confidence)
# - Phase 3: Backfills II for 2025 (current year, preliminary)
# - Uses weekly batching to prevent API timeouts
# - Takes 2-3 days to complete (Elexon API rate limit)
```

**Upgrade Path** (as data matures):
- After 14 months: Re-ingest with R3 to upgrade II→R3
- After 28 months: Re-ingest with RF to upgrade R3→RF (optional, marginal improvement)

The canonical view `p114_settlement_canonical` automatically prioritizes RF > R3 > II when multiple runs exist for the same settlement period.

## Stakeholder Communication

### Dashboard Metadata

All dashboards showing P114 data must include:
- **Data Maturity Indicator**: "Final", "High Confidence", or "Preliminary"
- **Last Updated**: Timestamp of most recent ingestion
- **Run Breakdown**: % of data from each run type

Example tooltip:
```
Revenue: £1.2M
Data Maturity: 65% Final (RF), 30% High Confidence (R3), 5% Preliminary (II)
Last Updated: 2025-12-28 02:15 UTC
Note: Recent data subject to revision as reconciliation runs complete
```

### Query Result Annotations

Materialized reports should include metadata:
```sql
SELECT
  bm_unit_id,
  SUM(value2 * system_price * multiplier) as revenue_gbp,
  -- Add maturity breakdown
  COUNT(CASE WHEN settlement_run = 'RF' THEN 1 END) as periods_final,
  COUNT(CASE WHEN settlement_run = 'R3' THEN 1 END) as periods_high_conf,
  COUNT(CASE WHEN settlement_run = 'II' THEN 1 END) as periods_preliminary,
  ROUND(COUNT(CASE WHEN settlement_run = 'RF' THEN 1 END) * 100.0 / COUNT(*), 1) as pct_final
FROM p114_settlement_canonical
WHERE settlement_date >= '2024-01-01'
GROUP BY bm_unit_id
```

## Revision Handling

### When Runs Update

**Scenario**: R3 run replaces II data for Feb 2024

**Impact**:
- Revenue estimates may change by 1-5% (typical)
- Unit rankings may shift slightly
- Trend analysis remains directionally correct

**Communication Template**:
```
Data Update Notice: P114 Reconciliation Run 3
Date: 2025-04-01
Scope: February 2024 settlement data
Previous Run: II (Interim)
New Run: R3 (Reconciliation 3)
Expected Impact: Revenue estimates may adjust ±2-5%
Action Required: Re-run monthly reports for Feb 2024
```

### Audit Trail

Maintain log of run updates:
```sql
CREATE TABLE uk_energy_prod.p114_run_updates (
  update_date DATE,
  settlement_date_start DATE,
  settlement_date_end DATE,
  previous_run STRING,
  new_run STRING,
  records_affected INT64,
  revenue_change_pct FLOAT64,
  notes STRING
)
```

## Exception Handling

### DF (Default Final) Runs

**Policy**: Ingest but flag for review
- DF runs indicate corrections to RF (rare)
- May override RF in canonical view if generation_timestamp is newer
- Requires manual validation before reporting

### Missing Runs

**Policy**: Escalate to Portal support if expected runs missing
- RF expected for dates >28 months: Alert if absent
- R3 expected for dates >14 months: Warning if absent
- II expected for dates >1 day: Info log if absent

## Governance Review

**Frequency**: Quarterly
**Triggers**:
- Significant run variance (>10% revenue change)
- Portal schema changes
- New run types introduced by Elexon

**Review Items**:
1. Run prioritization still optimal?
2. Deduplication logic producing accurate results?
3. Stakeholder feedback on data maturity communication
4. Storage costs vs. value of audit trail

## References

- Elexon P114 Settlement Process: https://www.elexon.co.uk/operations-settlement/
- BMRS Portal API Documentation: https://bmrs.elexon.co.uk/api-documentation
- Internal: `S0142_BACKFILL_STRATEGY.md`
- Internal: `VLP_SETTLEMENT_MECHANISMS_EXPLAINED.md`

---

**Approval**:
- Data Engineering Lead: [Signature Required]
- Analytics Manager: [Signature Required]
- Compliance Officer: [Signature Required]

**Effective Date**: 2025-12-28
**Next Review**: 2026-03-31
