# Duplicate Prevention Analysis

## How the Script Prevents Duplicates

### 1. Window-Based Skip Logic ✅

The script uses `_window_from_utc` metadata column to track what data has been loaded:

```python
# Before loading each time window, query what already exists
existing_windows = _get_existing_windows(
    client, BQ_DATASET, table_name, start_dt, end_dt
)

# Query:
SELECT DISTINCT _window_from_utc FROM `table`
WHERE _window_from_utc >= 'start' AND _window_from_utc < 'end'
```

**How it works:**
- Every batch gets a `_window_from_utc` timestamp (e.g., "2025-01-01T00:00:00+00:00")
- Before loading, script queries which windows already exist
- If window exists, **entire window is skipped** (no API call, no BigQuery write)

**Example from current 2024 run:**
```
🔎 Querying existing windows for bmrs_bod between 2024-01-01 and 2024-12-31
Found 365 existing windows for BOD. Will skip these.
```

### 2. What Gets Skipped

When window exists:
```python
if window_start in existing_windows:
    pbar_windows.update(1)
    continue  # ← Skip entire window
```

**This means:**
- No API call to Elexon
- No DataFrame creation
- No BigQuery write
- **Zero duplicate rows created**

### 3. Granularity of Skip Logic

| Dataset | Chunk Size | Skip Granularity |
|---------|-----------|------------------|
| BOD | 1 day | Daily windows |
| FUELINST | 7 days | Weekly windows |
| FREQ | 7 days | Weekly windows |
| Most others | 1 day | Daily windows |

**Critical:** Script skips by **window**, not by individual settlement periods.

### 4. BigQuery's Role ❌

**BigQuery does NOT prevent duplicates:**
- No primary keys
- No unique constraints
- No automatic deduplication
- Tables use `WRITE_APPEND` mode (always adds rows)

From schema check:
```
BMRS_BOD:
  Table type: TABLE
  Clustering: None
  Date/Time columns: ['settlementDate', 'timeFrom', 'timeTo']
  Period columns: ['settlementDate', 'settlementPeriod']

BMRS_FUELINST:
  Date/Time columns: ['publishTime', 'startTime', 'settlementDate']
  Period columns: ['settlementDate', 'settlementPeriod']
```

**If we bypassed the window check, BigQuery would happily insert duplicates.**

## Potential Duplicate Scenarios

### ❌ Scenario 1: Manual Overwrite Flag
```bash
python ingest_elexon_fixed.py --overwrite
```
**Result:** Skips window check, loads everything, creates duplicates

### ✅ Scenario 2: Our Current Plan
```bash
# 2024 main run (now): Loads all datasets, FUELINST will fail
# 2024 repair: --only FUELINST,FREQ,FUELHH loads ONLY failed datasets
# 2025 repair: --exclude BOD loads all EXCEPT BOD
```
**Result:** No duplicates because:
- Main run creates windows for 50/53 datasets
- Repair finds those windows, skips them
- Only loads the 3 missing datasets (FUELINST/FREQ/FUELHH)

### ❌ Scenario 3: If We Used Wrong Date Range
```bash
# If 2024 already has Jan-Mar data
python ingest_elexon_fixed.py --start 2024-01-01 --end 2024-12-31
# Without checking existing windows
```
**Result:** Would create duplicates for Jan-Mar

**But our script prevents this:**
- Always queries `_window_from_utc` first
- Skips windows that exist
- Only loads missing windows

## Verification: Can We Check for Duplicates?

### Method 1: Count Rows Per Settlement Period

For BOD (should be ~30-50 BMUs per settlement period):
```sql
SELECT 
  settlementDate,
  settlementPeriod,
  COUNT(*) as row_count,
  COUNT(DISTINCT bmUnit) as unique_bmus
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE settlementDate = '2025-06-15'
GROUP BY settlementDate, settlementPeriod
ORDER BY settlementDate, settlementPeriod
```

**Expected:** row_count ≈ unique_bmus (30-50 per period)
**If duplicates:** row_count >> unique_bmus (e.g., 100+ rows for same period)

### Method 2: Check for Exact Duplicate Rows

```sql
WITH duplicates AS (
  SELECT 
    settlementDate,
    settlementPeriod,
    bmUnit,
    pnLevelFrom,
    pnLevelTo,
    COUNT(*) as occurrence_count
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE settlementDate BETWEEN '2025-06-01' AND '2025-06-30'
  GROUP BY 1, 2, 3, 4, 5
  HAVING COUNT(*) > 1
)
SELECT * FROM duplicates
LIMIT 100
```

**Expected:** 0 rows (no duplicates)
**If duplicates:** Shows repeated rows with occurrence_count > 1

### Method 3: Check Window Metadata Consistency

```sql
SELECT 
  _window_from_utc,
  COUNT(*) as total_rows,
  COUNT(DISTINCT settlementDate) as unique_dates,
  MIN(settlementDate) as first_date,
  MAX(settlementDate) as last_date
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
GROUP BY _window_from_utc
ORDER BY _window_from_utc
```

**Expected:** Each window should cover 1 day of data (for BOD)
**If duplicates:** Same window appears multiple times or windows overlap

## Current Status Assessment

### 2025 BOD: No Duplicates Risk ✅
- Loaded once (Jan-Aug)
- Repair uses `--exclude BOD`
- BOD windows will be found, skipped
- **Safe**

### 2024 FUELINST/FREQ/FUELHH: No Duplicates Risk ✅
- Main run will fail to load these 3
- Creates no windows for them
- Repair uses `--only FUELINST,FREQ,FUELHH`
- Will find no existing windows
- Loads them fresh
- **Safe**

### 2024 Other 50 Datasets: No Duplicates Risk ✅
- Main run loads successfully
- Creates windows for all
- Repair queries windows
- Finds them all, skips them all
- **Safe**

## Settlement Period vs Window

**Key distinction:**

**Settlement Period** = 30-minute trading period (48 per day)
- Used in data queries
- Business logic concept
- E.g., "Period 15 on 2025-06-15"

**Window** = Time range for API call
- Used for duplicate prevention
- Technical implementation concept
- E.g., "2025-06-15T00:00:00+00:00" (1 day window)

**One window contains many settlement periods:**
- 1-day window = 48 settlement periods
- 7-day window = 336 settlement periods

**Script skips by window, but data is unique per settlement period:**
- If window exists → skip all 48 periods in that day
- No partial loading within a window
- All-or-nothing approach

## Recommendation

### Current Setup is Safe ✅

The script's window-based skip logic is robust:
1. Always queries existing data before loading
2. Skips complete time windows if data exists
3. --exclude and --only flags ensure correct dataset selection
4. No overlap between main runs and repairs

### To Verify Zero Duplicates After Completion

Run these queries after 11:12 PM:

```sql
-- 1. Check for any exact duplicate rows across all key tables
SELECT 
  'bmrs_bod' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT CONCAT(
    CAST(settlementDate AS STRING), '|',
    CAST(settlementPeriod AS STRING), '|',
    bmUnit
  )) as unique_keys
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`

UNION ALL

SELECT 
  'bmrs_fuelinst' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT CONCAT(
    CAST(settlementDate AS STRING), '|',
    CAST(settlementPeriod AS STRING), '|',
    fuelType
  )) as unique_keys
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`

UNION ALL

SELECT 
  'bmrs_freq' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT CAST(measurementTime AS STRING)) as unique_keys
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
```

**Expected:** total_rows ≈ unique_keys for each table

If they match → **Zero duplicates** ✅
If they differ → Some duplicate rows exist ❌

### If Duplicates Are Found (Unlikely)

Use this query to identify and remove them:

```sql
-- Create deduplicated table
CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_deduped` AS
SELECT DISTINCT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`;

-- Verify row counts
SELECT 
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`) as original_rows,
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_deduped`) as deduped_rows;

-- If satisfied, replace original
DROP TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`;
ALTER TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_deduped` 
RENAME TO bmrs_bod;
```

## Summary

✅ **Script has built-in duplicate prevention**
✅ **Uses `_window_from_utc` metadata to track loaded data**
✅ **Current plan (--exclude BOD, --only FUELINST/FREQ/FUELHH) is safe**
✅ **BigQuery can detect duplicates with queries checking settlementDate + settlementPeriod**
❌ **BigQuery does NOT enforce uniqueness automatically**
❌ **Manual --overwrite flag would create duplicates**

**Bottom line:** Your concern is valid, but the script already handles this correctly. We can verify zero duplicates after completion with the SQL queries above.
