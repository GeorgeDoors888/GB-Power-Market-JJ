# S0142 Full Backfill Strategy
**Date**: 28 December 2025
**Purpose**: Plan comprehensive P114 settlement data backfill for 2022-2025

## Executive Summary

**Goal**: Backfill elexon_p114_s0142_bpi table with complete settlement data for VLP revenue reconciliation

**Target Period**: 2022-01-01 to 2025-12-28 (1,458 days)
**Expected Records**: ~1.4 billion BPI records (~275k per settlement date × 1,458 days × ~3.5 runs average)
**Estimated Storage**: 50-100 GB in BigQuery
**Estimated Runtime**: 100-200 hours (depends on Portal response times and run selection)

## Settlement Run Prioritization

### Understanding Settlement Runs

Elexon processes settlement data through multiple runs as more accurate information becomes available:

| Run Code | Name | Timing | Accuracy | Use Case |
|----------|------|--------|----------|----------|
| **II** | Interim Initial | T+1 day | Lowest | Real-time analysis, latest data |
| **SF** | Settlement Final | T+5 days | Low-Medium | Early settlement |
| **R1** | Reconciliation Run 1 | T+1 month | Medium | Monthly close |
| **R2** | Reconciliation Run 2 | T+4 months | High | Quarterly adjustments |
| **R3** | Reconciliation Run 3 | T+14 months | Very High | Annual reconciliation |
| **RF** | Reconciliation Final | T+28 months | **Highest** | Final settlement (2.3 years post) |
| **DF** | Default Final | Special | Varies | Error corrections |

**Key Insight**: RF runs are most accurate but lag by 28 months. For recent data (2024-2025), R3 or II are the best available.

### Recommended Strategy: **Hybrid Approach**

#### Phase 1: Historical Data (2022-2023) - Use RF Runs
- **Period**: 2022-01-01 to 2023-12-31 (730 days)
- **Run**: RF (Reconciliation Final)
- **Rationale**: RF runs available (28-month lag means RF for 2022-2023 exists as of Nov 2024+)
- **Expected Records**: ~275k × 730 = ~200M BPI records
- **Runtime**: ~50-70 hours
- **Command**:
  ```bash
  python3 ingest_p114_s0142.py 2024-01-01 2025-12-28 RF \
    --settlement-start 2022-01-01 --settlement-end 2023-12-31
  ```
  Note: Query by generation_date (2024-2025) to get RF runs for settlement_date (2022-2023)

#### Phase 2: Recent Data (2024) - Use R3 Runs
- **Period**: 2024-01-01 to 2024-12-31 (366 days)
- **Run**: R3 (Reconciliation Run 3)
- **Rationale**: RF not yet available (28-month lag), R3 is best accurate alternative (14-month lag)
- **Expected Records**: ~275k × 366 = ~100M BPI records
- **Runtime**: ~30-40 hours
- **Command**:
  ```bash
  python3 ingest_p114_s0142.py 2024-03-01 2025-12-28 R3 \
    --settlement-start 2024-01-01 --settlement-end 2024-12-31
  ```
  Note: Query generation dates Mar 2024 onwards to get R3 runs for early 2024

#### Phase 3: Latest Data (2025) - Use II Runs
- **Period**: 2025-01-01 to 2025-12-28 (362 days)
- **Run**: II (Interim Initial)
- **Rationale**: Most recent data, only II runs available
- **Expected Records**: ~275k × 362 = ~100M BPI records
- **Runtime**: ~30-40 hours
- **Command**:
  ```bash
  python3 ingest_p114_s0142.py 2025-01-02 2025-12-29 II \
    --settlement-start 2025-01-01 --settlement-end 2025-12-28
  ```

### Total Backfill Summary
- **Total Records**: ~400M BPI records
- **Total Runtime**: ~110-150 hours (4.5-6 days continuous)
- **Total Storage**: ~50-80 GB in BigQuery
- **Cost**: Within BigQuery free tier (1 TB queries/month)

## Portal API Considerations

### Query Behavior
- **Query Parameter**: `generation_date` (NOT `settlement_date`)
- **Response**: Returns multiple settlement dates per generation date
- **Example**: Query generation_date=2024-12-28 returns RF runs for settlement dates 2022-10-01 to 2022-11-30
- **Implication**: Must query recent generation dates to get older settlement dates (RF lag)

### Rate Limiting
- **Observed**: No rate limit errors in testing (downloads ~20 files/min)
- **Conservative Strategy**: 2 seconds between file downloads, 1 second between date queries
- **Estimated Impact**: Minimal (built into runtime estimates)

### File Naming Convention
```
S0142_YYYYMMDD_RUN_timestamp.gz
   │      │      │       └─ Generation timestamp (hhmmss)
   │      │      └─ Settlement run (II/SF/R1/R2/R3/RF/DF)
   │      └─ Settlement date
   └─ Report type
```

## Script Enhancements Needed

### Current Limitations
1. **No settlement date filtering**: Script processes ALL settlement dates in Portal response
2. **No run filtering post-query**: Downloads all runs if multiple exist
3. **No progress persistence**: Crash requires full restart

### Recommended Enhancements

#### 1. Add Settlement Date Range Filtering
```python
def download_and_parse_s0142(
    generation_start: str,
    generation_end: str,
    settlement_run: str,
    settlement_start: str = None,  # NEW
    settlement_end: str = None     # NEW
):
    """
    Download S0142 files filtered by settlement date range
    """
    for filename, file_info in portal_files.items():
        # Parse settlement date from filename: S0142_20221015_RF_...
        settlement_date_str = filename.split('_')[1]
        settlement_date = datetime.strptime(settlement_date_str, '%Y%m%d')

        # Filter by settlement date range
        if settlement_start and settlement_date < datetime.strptime(settlement_start, '%Y-%m-%d'):
            continue
        if settlement_end and settlement_date > datetime.strptime(settlement_end, '%Y-%m-%d'):
            continue

        # Process file...
```

#### 2. Add Progress Checkpointing
```python
import json

def save_checkpoint(processed_dates):
    """Save progress to JSON file"""
    with open('s0142_checkpoint.json', 'w') as f:
        json.dump({'processed_dates': list(processed_dates)}, f)

def load_checkpoint():
    """Load progress from JSON file"""
    try:
        with open('s0142_checkpoint.json', 'r') as f:
            return set(json.load(f)['processed_dates'])
    except FileNotFoundError:
        return set()
```

#### 3. Add Deduplication Logic
```sql
-- Create deduplicated view
CREATE OR REPLACE VIEW uk_energy_prod.elexon_p114_s0142_bpi_dedup AS
SELECT *
FROM (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY bm_unit_id, settlement_date, settlement_period
      ORDER BY
        CASE settlement_run
          WHEN 'RF' THEN 1
          WHEN 'R3' THEN 2
          WHEN 'R2' THEN 3
          WHEN 'R1' THEN 4
          WHEN 'SF' THEN 5
          WHEN 'II' THEN 6
          WHEN 'DF' THEN 7
        END,
        generation_timestamp DESC
    ) as rn
  FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
)
WHERE rn = 1
```

## Execution Plan

### Pre-Execution Checklist
- [x] P114 key validated (03omen6i9lhv5fa) ✅
- [x] Script tested with sample data (826k records) ✅
- [x] Settlement period extraction working (48 periods) ✅
- [x] System price capture working (£65-£128/MWh) ✅
- [x] BigQuery table created with correct schema ✅
- [ ] Script enhancements implemented (optional but recommended)
- [ ] Disk space verified (need ~20GB temp space for downloads)
- [ ] Monitoring script ready (row count checks)

### Execution Commands

#### Option A: Simple Approach (No Script Changes)
```bash
# Phase 1: RF runs for 2022-2023 (query recent generation dates)
python3 ingest_p114_s0142.py 2024-01-01 2025-12-28 RF > s0142_rf_2022_2023.log 2>&1 &

# Wait for completion (~60 hours)

# Phase 2: R3 runs for 2024
python3 ingest_p114_s0142.py 2024-03-01 2025-12-28 R3 > s0142_r3_2024.log 2>&1 &

# Wait for completion (~35 hours)

# Phase 3: II runs for 2025
python3 ingest_p114_s0142.py 2025-01-02 2025-12-29 II > s0142_ii_2025.log 2>&1 &
```

#### Option B: Enhanced Approach (With Script Updates)
```bash
# Phase 1: RF runs for 2022-2023 (filtered by settlement date)
python3 ingest_p114_s0142_enhanced.py \
  --generation-start 2024-01-01 \
  --generation-end 2025-12-28 \
  --settlement-start 2022-01-01 \
  --settlement-end 2023-12-31 \
  --run RF \
  --checkpoint s0142_rf_checkpoint.json \
  > s0142_rf_2022_2023.log 2>&1 &

# Similar for Phase 2 and Phase 3...
```

### Monitoring During Execution
```bash
# Check progress (count rows)
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT
  settlement_run,
  COUNT(*) as total_records,
  COUNT(DISTINCT settlement_date) as distinct_dates,
  MIN(settlement_date) as earliest_date,
  MAX(settlement_date) as latest_date
FROM \`inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi\`
GROUP BY settlement_run
ORDER BY settlement_run
'''

for row in client.query(query).result():
    print(f'{row.settlement_run}: {row.total_records:,} records, {row.distinct_dates} dates, {row.earliest_date} to {row.latest_date}')
"

# Check VLP unit coverage
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT
  settlement_run,
  COUNT(DISTINCT settlement_date) as dates_with_data
FROM \`inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi\`
WHERE bm_unit_id IN ('FBPGM002', 'FFSEN005')
GROUP BY settlement_run
ORDER BY settlement_run
'''

print('VLP Unit Coverage:')
for row in client.query(query).result():
    print(f'{row.settlement_run}: {row.dates_with_data} dates')
"

# Tail logs
tail -f s0142_rf_2022_2023.log
```

### Post-Execution Validation

#### 1. Check Date Coverage
```sql
SELECT
  settlement_run,
  COUNT(DISTINCT settlement_date) as distinct_dates,
  MIN(settlement_date) as earliest,
  MAX(settlement_date) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
GROUP BY settlement_run
ORDER BY settlement_run;

-- Expected:
-- RF: 730 dates (2022-2023)
-- R3: 366 dates (2024)
-- II: 362 dates (2025)
```

#### 2. Check Period Completeness
```sql
SELECT
  settlement_date,
  COUNT(DISTINCT settlement_period) as periods_count
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
WHERE settlement_date BETWEEN '2022-01-01' AND '2022-01-31'
GROUP BY settlement_date
HAVING COUNT(DISTINCT settlement_period) < 48
ORDER BY settlement_date;

-- Should return 0 rows (all dates have 48 periods)
```

#### 3. Check VLP Unit Presence
```sql
SELECT
  bm_unit_id,
  COUNT(DISTINCT settlement_date) as dates_count,
  MIN(settlement_date) as earliest,
  MAX(settlement_date) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
WHERE bm_unit_id IN ('FBPGM002', 'FFSEN005')
GROUP BY bm_unit_id;

-- Expected: Both units present for ~1,458 dates
```

#### 4. Check System Price Validity
```sql
SELECT
  COUNT(*) as null_price_count,
  COUNT(CASE WHEN system_price < 0 THEN 1 END) as negative_price_count,
  MIN(system_price) as min_price,
  MAX(system_price) as max_price,
  AVG(system_price) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
WHERE settlement_date >= '2022-01-01';

-- Expected:
-- null_price_count: 0
-- negative_price_count: < 1% (negative prices rare but possible)
-- min_price: -£500/MWh (extreme low)
-- max_price: ~£6,000/MWh (spike events)
-- avg_price: £50-£100/MWh
```

## Troubleshooting

### Issue: Portal API Timeout
**Symptom**: `requests.exceptions.Timeout` after 60 seconds
**Solution**: Increase timeout in script: `timeout=120` or `timeout=300`

### Issue: Disk Space Full
**Symptom**: `OSError: [Errno 28] No space left on device`
**Solution**:
- Check space: `df -h /tmp`
- Clean up: `rm -rf /tmp/s0142_*.gz`
- Modify script to process files incrementally (download → parse → delete → repeat)

### Issue: BigQuery Quota Exceeded
**Symptom**: `google.api_core.exceptions.Forbidden: 403 Quota exceeded`
**Solution**:
- Check quota: https://console.cloud.google.com/iam-admin/quotas
- Wait 24 hours for quota reset
- Batch uploads: 10k rows at a time instead of 275k

### Issue: Duplicate Records
**Symptom**: Multiple runs for same settlement date/period
**Solution**: Use deduplication view (see above) or add `DISTINCT` to queries

### Issue: Missing Settlement Dates
**Symptom**: Gaps in settlement_date sequence
**Solution**:
- Check Portal availability for those dates
- Holidays/weekends may have different generation patterns
- Re-run backfill for specific date ranges

## Alternative Strategies

### Strategy B: Run-Agnostic Approach
- Download ALL runs (II, SF, R1, R2, R3, RF, DF) for entire period
- Let BigQuery deduplicate using view (prioritize RF > R3 > R2 > R1 > SF > II)
- **Pros**: Complete data, easy to implement
- **Cons**: 3-7x storage (download all runs), longer runtime, higher costs

### Strategy C: Incremental Approach
- Start with most recent month (Dec 2025, II runs)
- Test reconciliation with BMRS data
- Validate methodology works
- Gradually backfill older data (Nov, Oct, Sept...)
- **Pros**: Fast validation, iterative refinement, lower upfront investment
- **Cons**: Delayed historical analysis, piecemeal progress

### Strategy D: VLP-Only Filtering
- Modify parser to only extract VLP units (FBPGM002, FFSEN005)
- **Pros**: 48× less data (144 records/file vs 275k), much faster, minimal storage
- **Cons**: Loses ability to analyze full market, can't compare VLP to others

**Recommendation**: Use **Hybrid Approach** (Phases 1-3 above) for comprehensive coverage with optimal accuracy/timeliness tradeoff.

## Next Steps

1. **Decision Point**: Choose execution strategy
   - Recommended: **Hybrid Approach** (RF for 2022-2023, R3 for 2024, II for 2025)
   - Alternative: **Incremental Approach** (start with recent data, validate, expand)

2. **Script Enhancement** (Optional): Add settlement date filtering and checkpointing
   - Time investment: 2-3 hours development
   - Benefit: More efficient downloads, resilient to failures

3. **Execute Phase 1**: RF backfill for 2022-2023
   - Command: `python3 ingest_p114_s0142.py 2024-01-01 2025-12-28 RF`
   - Monitor progress: Check logs and BigQuery row counts
   - Validate: Check date coverage and VLP unit presence

4. **Proceed to Reconciliation**: Once Phase 1 complete (~60 hours)
   - Run VLP revenue reconciliation query (Task 12)
   - Validate £2.79M BMRS estimate against P114 actuals
   - Identify discrepancies and investigate

---

**Created**: 28 December 2025
**Author**: GitHub Copilot
**Status**: Ready for execution
**Related**: ingest_p114_s0142.py, VLP_REVENUE_RECONCILIATION_PLAN.md
