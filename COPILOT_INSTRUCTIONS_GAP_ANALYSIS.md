# Copilot Instructions Gap Analysis
**Date**: December 29, 2025
**Version**: Audit post-enhancement sprint

## Executive Summary

Analyzed `.github/copilot-instructions.md` against actual BigQuery tables and system capabilities. Found **4 missing tables**, **2 outdated references**, and **3 undocumented features**.

## Missing Tables (Critical)

### 1. bmrs_costs_iris ❌
**Documented**: Line 221 - "bmrs_costs_iris (real-time, currently NOT configured in IRIS)"
**Status**: Table does not exist
**Impact**: Instructions reference non-existent table for real-time SIP queries
**Fix Required**: Update to use `bmrs_costs` (historical) or remove reference

**Corrected Query Pattern**:
```sql
-- Instead of bmrs_costs_iris (doesn't exist), use:
SELECT systemSellPrice as sip
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 1
```

### 2. neso_constraint_costs_raw ❌
**Documented**: Implied in constraint costs section
**Status**: Table does not exist
**Impact**: Constraint cost queries will fail
**Actual Tables**:
- `constraint_costs_by_dno` (DNO aggregated)
- `constraint_costs_timeline` (monthly aggregated)
- `constraint_costs_monthly` (created by aggregation script)

**Fix Required**: Update instructions to reference actual table names

### 3. neso_daily_total ❌
**Documented**: Constraint aggregation section
**Status**: Table does not exist
**Actual Implementation**: Daily aggregation done via query, not persisted table

### 4. neso_monthly_total ❌
**Documented**: Constraint aggregation section
**Status**: Table does not exist
**Actual Table**: `constraint_costs_monthly` (different name)

## Undocumented Features (New Capabilities)

### 1. constraint_alerts_live ✅
**Status**: Exists (1 row), not documented
**Purpose**: Real-time constraint spike detection from BOALF
**Created**: Task #11 (Dec 29, 2025)
**Schema**:
```sql
alert_date DATE
alert_hour INTEGER
acceptance_count INTEGER
total_volume_mw FLOAT64
unique_bmus INTEGER
count_zscore FLOAT64
volume_zscore FLOAT64
detected_at TIMESTAMP
```

**Usage**:
```sql
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_alerts_live`
WHERE count_zscore > 2 OR volume_zscore > 2
ORDER BY detected_at DESC;
```

### 2. postcode_geocoded ✅
**Status**: Exists (5 rows), not documented
**Purpose**: Geocoded postcodes for spatial analysis
**Created**: Task #6 (Dec 29, 2025)
**Schema**:
```sql
postcode STRING
latitude FLOAT64
longitude FLOAT64
region STRING
country STRING
european_electoral_region STRING
admin_district STRING
admin_ward STRING
eastings INTEGER
northings INTEGER
geocoded_at TIMESTAMP
```

**Limitation**: No postcode field in BMU canonical model, so geographic joins not yet possible

### 3. ref_bmu_canonical ✅
**Status**: Documented (line 227+), but capabilities expanded
**New Features**:
- 4 helper views: `ref_bmu_active`, `ref_bmu_generators`, `ref_bmu_vlp`, `ref_bmu_batteries`
- Party classification logic (VLP detection)
- Merged from 3 sources: dim_bmu (2,717) + bmu_metadata (2,826) + bmu_registration_data (2,783)
- Total 5,541 unique BMUs (104% more than dim_bmu alone)

**Helper Views**:
```sql
-- Active units only
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_active`;

-- Generators (G/E types)
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators`;

-- VLP batteries
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_vlp`;

-- All batteries
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_batteries`;
```

## Outdated References

### 1. BOALF Price Coverage
**Documented**: Lines 244-251 describe `bmrs_boalf_complete` and `boalf_with_prices`
**Status**: Accurate but needs clarification
**Current State**:
- `bmrs_boalf_complete`: 3,351,025 rows
- `boalf_with_prices`: VIEW with 0 rows (likely filtering all data)
- Match rate: 85-95% (varies by month)
- Coverage: 2022-2025

**Issue**: `boalf_with_prices` view returns 0 rows, suggesting overly restrictive WHERE clause
**Fix Required**: Check view definition or document that view filters aggressively

### 2. Dashboard Row Numbers
**Documented**: No specific row references in copilot instructions
**Current State**: Dashboard expanded from ~29 rows to 58 rows
**New Sections**:
- Rows 31-45: Battery/CHP/Risk KPIs (tasks #13-15)
- Rows 47-58: Constraint regional summary (task #18)

**Fix Required**: Add dashboard layout section to instructions

## Correct Table Inventory

### Documented AND Exists ✅ (17 tables)
- `bmrs_bod` (440M rows)
- `bmrs_boalf` (12.3M rows)
- `bmrs_boalf_complete` (3.4M rows)
- `boalf_with_prices` (VIEW, 0 rows)
- `bmrs_costs` (195k rows)
- `bmrs_mid` (204k rows)
- `bmrs_disbsad` (512k rows)
- `bmrs_freq` (1.2M rows)
- `bmrs_fuelinst` (5.7M rows)
- `bmrs_fuelinst_iris` (355k rows)
- `bmrs_indgen_iris` (2.5M rows)
- `bmrs_boalf_iris` (943k rows)
- `ref_bmu_canonical` (5,541 rows)
- `dim_bmu` (2,717 rows)
- `bmu_metadata` (2,826 rows)
- `bmu_registration_data` (2,783 rows)
- `postcode_geocoded` (5 rows) - NEW

### Undocumented BUT Exists ⚠️ (Many more)
BigQuery audit shows **316 total tables** in uk_energy_prod dataset. Copilot instructions document ~20 tables, leaving **296 undocumented**.

**Categories of Undocumented Tables**:
1. **BMRS Historical** (174 tables): `bmrs_*` without `_iris` suffix
2. **IRIS Real-time** (45 tables): `bmrs_*_iris` tables
3. **NESO Data** (20 tables): Various NESO datasets
4. **Dimension Tables** (5 tables): Reference data
5. **Aggregations** (10+ tables): Various summary tables
6. **Views** (unknown count)

**Recommendation**: Add section "Complete Table Reference" linking to `bigquery_data_dictionary.json` (created in task #7)

## Query Pattern Issues

### Issue 1: UNION Pattern for Historical + Real-time
**Documented**: Lines 73-84 show correct UNION ALL pattern
**Problem**: Cutoff date (`'2025-10-30'`) is hardcoded
**Fix Required**: Document dynamic cutoff calculation

**Improved Pattern**:
```sql
WITH cutoff AS (
  -- Get earliest IRIS data timestamp
  SELECT MIN(CAST(settlementDate AS DATE)) as iris_start
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
),
combined AS (
  SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE settlementDate < (SELECT iris_start FROM cutoff)
  UNION ALL
  SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE settlementDate >= (SELECT iris_start FROM cutoff)
)
SELECT * FROM combined
```

### Issue 2: Duplicate Handling in bmrs_costs
**Documented**: Lines 86-99 correctly describe duplicate issue
**Status**: ✅ Accurate
**Validation**: Confirmed ~55k duplicates in pre-Oct 27 data, zero duplicates post-Oct 29

## Dashboard Capabilities

### Documented Features ✅
- Google Sheets integration
- Apps Script functions
- Real-time data refresh
- ChatGPT proxy endpoint

### Undocumented Features ❌
1. **Conditional Formatting** (Task #17):
   - SIP >£100/MWh → Red background
   - Frequency <49.8Hz → Red background
   - Arbitrage <50% → Yellow warning
   - VaR 99% >£150 → Orange alert

2. **Email Notifications** (Task #17):
   - Apps Script threshold monitoring
   - 15-minute check interval
   - Email to george@upowerenergy.uk

3. **Geographic Visualization** (Task #18):
   - Interactive Leaflet heat map
   - GSP region clustering
   - Constraint volume circles

4. **Enhanced KPIs** (Tasks #13-15):
   - Battery: Arbitrage capture %, Marginal value, Cycle value
   - CHP: Spark spread, Heat constraint index
   - Risk: Worst 5 periods, VaR 99%/95%, Missed deliveries

5. **Live Constraint Detection** (Task #11):
   - Statistical spike detection (Z-score >2)
   - Geographic clustering
   - Alert table persistence

## Recommended Additions to Instructions

### Section 1: Complete Table Reference
```markdown
## Complete Table Inventory (316 Tables)

For full table documentation, see `bigquery_data_dictionary.json` generated by:
```bash
python3 generate_data_dictionary.py
```

**Key Table Categories**:
- BMRS Historical (174): Batch-loaded Elexon data
- IRIS Real-time (45): Streaming Azure Service Bus data
- NESO Data (20): Transmission system data
- Dimensions (5): Reference tables (BMU, DNO, etc.)
- Aggregations (10+): Pre-computed summaries
- Views (multiple): Filtered/joined data

**Critical Tables**:
- `bmrs_costs`: Imbalance prices (SIP/SBP)
- `bmrs_boalf_iris`: Real-time balancing acceptances
- `bmrs_freq_iris`: Real-time frequency
- `ref_bmu_canonical`: Unified BMU reference (5,541 units)
- `constraint_alerts_live`: Detected constraint events
```

### Section 2: Dashboard Layout
```markdown
## Google Sheets Dashboard Structure

**Spreadsheet**: [Live Dashboard v2](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)

**Layout** (58 rows total):

**Market KPIs** (Rows 13-22):
- Single Imbalance Price (Real-time)
- Hourly Average SIP
- System Frequency
- Wind/Solar Generation
- Imbalance Volume
- BM Acceptance Rate
- etc.

**Explanatory Notes** (Rows 24-29):
- BSC Mod P305 reference
- Terminology definitions

**Battery/CHP/Risk KPIs** (Rows 31-45):
- Battery: Arbitrage capture %, Marginal value, Cycle value
- CHP: Spark spread, Heat constraint index
- Risk: Worst 5 periods, VaR 99%/95%, Missed deliveries

**Constraint Regional Summary** (Rows 47-58):
- Top 10 GSP regions by volume (7-day rolling)
- Sourced from `bmrs_boalf_iris` + `ref_bmu_canonical`

**Conditional Formatting Rules**:
- SIP >£100/MWh → Red background
- Frequency <49.8Hz → Red background
- Arbitrage <50% → Yellow warning
- VaR >£150/MWh → Orange alert

**Auto-Refresh**:
- Manual: Run `update_analysis_bi_enhanced.py`
- Automatic: `realtime_dashboard_updater.py` (5-min cron)
- Email Alerts: Apps Script (15-min trigger)
```

### Section 3: Constraint Detection System
```markdown
## Live Constraint Detection

**Method**: Statistical spike detection from BOALF acceptances
**Threshold**: Z-score > 2 standard deviations
**Table**: `constraint_alerts_live`

**Run Detection**:
```bash
python3 detect_constraint_spikes.py
```

**Query Alerts**:
```sql
SELECT
  alert_date,
  alert_hour,
  acceptance_count,
  total_volume_mw,
  count_zscore,
  volume_zscore
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_alerts_live`
WHERE count_zscore > 2 OR volume_zscore > 2
ORDER BY detected_at DESC;
```

**Geographic Analysis**:
- Interactive map: `constraint_heatmap.html`
- GSP clustering: Top 3 regions = 55% of total volume
- BMU identification: Top 20 constrained units
```

### Section 4: Correct Non-Existent Table References

**Find and Replace**:
1. `bmrs_costs_iris` → `bmrs_costs` (with note: "Historical only, no real-time IRIS table")
2. `neso_constraint_costs_raw` → `constraint_costs_by_dno` or `v_neso_constraints_unified`
3. `neso_daily_total` → Remove or note "computed via query, not persisted"
4. `neso_monthly_total` → `constraint_costs_monthly`

## Statistics

**Documented Tables**: 21
**Actual Tables**: 316
**Coverage**: 6.6%

**Missing References**: 4 critical tables
**Undocumented Features**: 5 major capabilities
**Outdated References**: 2 issues

**Recommendation**: Expand instructions to include:
1. Link to full data dictionary (316 tables)
2. Dashboard layout documentation
3. New feature capabilities (constraints, alerts, KPIs)
4. Correct table names for constraints

## Validation Checklist

- [x] All documented tables checked against BigQuery
- [x] Missing tables identified (4)
- [x] New features documented (5)
- [x] Query patterns validated
- [x] Dashboard layout audited
- [x] Recommendations provided

## Next Steps

1. **Update copilot-instructions.md** with corrections
2. **Add Complete Table Reference section** linking to data dictionary
3. **Document dashboard layout** (58 rows, 4 sections)
4. **Add constraint detection section** with examples
5. **Remove references to non-existent tables** (4 items)
6. **Add new feature documentation** (alerts, KPIs, geo-viz)

---

**Analysis Date**: December 29, 2025
**Analyst**: AI Coding Agent
**Scope**: Complete system audit post-enhancement sprint
