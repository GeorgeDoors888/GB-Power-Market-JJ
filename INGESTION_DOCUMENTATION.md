# UK Energy Data Ingestion System - Complete Documentation

**Last Updated:** 27 October 2025, 12:45 AM  
**Status:** ✅ RUNNING (PID 13489)  
**Current Phase:** 2025 BOD ingestion (46% complete)

---

## 🎯 System Overview

This system ingests UK energy market data from the BMRS (Balancing Mechanism Reporting Service) API into Google BigQuery for analysis. It processes multiple datasets covering power generation, balancing, frequency, and market operations.

### Key Metrics (Current Run)
- **Start Time:** 27 Oct 2025, 00:13 AM
- **2025 Data:** Jan 1 - Aug 31, 2025 (243 days)
- **2024 Data:** Full year (366 days - leap year) - Auto-starts after 2025
- **Processing Rate:** 23.8 seconds/day (BOD)
- **Expected Completion:** 7:45 AM Monday, 27 Oct 2025

---

## 📁 Core Files

### Python Scripts

#### **ingest_elexon_fixed.py** (PRIMARY INGESTION SCRIPT)
**Purpose:** Main data ingestion engine  
**Location:** `/Users/georgemajor/GB Power Market JJ/ingest_elexon_fixed.py`

**Key Features:**
- Chunk-based processing (1-day to 7-day chunks depending on dataset)
- Automatic skip logic to prevent duplicate ingestion
- BigQuery metadata tracking via `_window_from_utc` and `_window_to_utc`
- Hash-based deduplication using `_hash_key` column
- Rate limiting and retry logic for API calls
- Progress tracking with detailed logging

**Critical Configuration:**
```python
# Chunk sizes (lines 76-130)
CHUNK_RULES = {
    "BOD": "1d",      # 1-day chunks (optimized from 1h for 24x speedup)
    "BOALF": "1d",    # 1-day chunks
    "FREQ": "1d",     # Frequency data
    "INDO": "1d",     # Indicated data
    # ... other datasets
}

# Batch size (line ~150)
MAX_FRAMES_PER_BATCH = 10  # Process 10 chunks before committing
```

**Key Functions:**

1. **`_get_existing_windows()`** (Lines 347-380)
   - **Bug Fix Applied:** Parses string timestamps from BigQuery to datetime objects
   - Prevents type mismatch that caused duplicate loads
   - Returns set of already-ingested time windows
   
   ```python
   # Fixed version includes:
   if isinstance(window_value, str):
       from dateutil import parser
       window_value = parser.parse(window_value)
       if window_value.tzinfo is None:
           window_value = window_value.replace(tzinfo=timezone.utc)
   ```

2. **Main Processing Loop** (Lines 1787-1825)
   - Checks existing windows before fetching
   - Skips already-loaded data
   - Logs progress and successful loads
   - Handles errors with retry logic

**Usage:**
```bash
# Run for 2025
python3 ingest_elexon_fixed.py --start 2025-01-01 --end 2025-08-31

# Run for 2024
python3 ingest_elexon_fixed.py --start 2024-01-01 --end 2024-12-31

# Background execution (survives terminal closure)
nohup python3 ingest_elexon_fixed.py --start 2025-01-01 --end 2025-08-31 > jan_aug_ingest.log 2>&1 &
```

---

#### **remove_bod_duplicates.py**
**Purpose:** Remove duplicate records from BigQuery tables  
**Created:** 27 Oct 2025 (during duplicate cleanup)

**Key Function:**
```python
def deduplicate_table(table_name):
    """
    Remove duplicates using _hash_key column.
    Keeps most recent record based on _ingested_utc.
    """
    # Uses ROW_NUMBER() OVER (PARTITION BY _hash_key ORDER BY _ingested_utc DESC)
    # Creates temp table with unique records
    # Replaces original table
```

**Usage:**
```bash
python3 remove_bod_duplicates.py
```

**Results:**
- First run: Removed 137M+ duplicates from BOD
- Second run: Removed 9.5M+ duplicates from BOALF
- Third run: Removed 633k duplicates across all tables

---

#### **monitor_progress.py**
**Purpose:** Real-time progress monitoring and completion estimates  
**Created:** 27 Oct 2025

**Features:**
- Parses log files for progress updates
- Calculates processing rates
- Estimates completion times
- Shows skipped windows (skip logic verification)
- Extracts successful load counts

**Usage:**
```bash
# Monitor current 2025 ingestion
python3 monitor_progress.py jan_aug_ingest_20251027_001331.log

# Will monitor 2024 ingestion (after auto-start)
python3 monitor_progress.py year_2024_ingest.log
```

**Sample Output:**
```
📊 INGESTION PROGRESS REPORT
Current Dataset: BOD
Progress: 46.1% (112/243 days)
Rate: 23.8 seconds/day
Estimated Completion: 04:37 AM
Windows Skipped: 273
  - BOALF: 242 windows
  - BOD: 31 windows
```

---

### Shell Scripts

#### **run_2025_then_2024.sh**
**Purpose:** Auto-start 2024 ingestion after 2025 completes  
**Location:** `/Users/georgemajor/GB Power Market JJ/run_2025_then_2024.sh`

**How It Works:**
```bash
#!/bin/bash
PID=13489  # Current 2025 ingestion process

while kill -0 $PID 2>/dev/null; do
    sleep 300  # Check every 5 minutes
done

# When 2025 completes, start 2024
nohup /Users/georgemajor/GB\ Power\ Market\ JJ/.venv/bin/python \
    ingest_elexon_fixed.py \
    --start 2024-01-01 \
    --end 2024-12-31 \
    > year_2024_ingest.log 2>&1 &

echo "✅ 2024 ingestion started at $(date)"
```

**Status:** Currently running in background (Terminal 2)

---

#### **cleanup_and_restart_ingestion.sh**
**Purpose:** Stop processes, clean duplicates, restart ingestion  
**Last Used:** 27 Oct 2025, 00:13 AM

**Steps:**
1. Kills existing ingestion processes
2. Runs `remove_bod_duplicates.py` on all `bmrs_*` tables
3. Restarts ingestion with `nohup`
4. Starts auto-2024 monitoring script

**Usage:**
```bash
bash cleanup_and_restart_ingestion.sh
```

---

#### **restart_ingestion.sh**
**Purpose:** Simple restart without cleanup (relies on skip logic)

**Usage:**
```bash
bash restart_ingestion.sh
```

---

## 🗄️ Database Schema

### BigQuery Project
**Project ID:** `inner-cinema-476211-u9`  
**Dataset:** `uk_energy_prod`

### Table Structure (All BMRS Tables)

**Metadata Columns (Added by Ingestion Script):**
- `_ingested_utc` (TIMESTAMP): When row was ingested
- `_window_from_utc` (TIMESTAMP): Start of time window for this batch
- `_window_to_utc` (TIMESTAMP): End of time window for this batch
- `_hash_key` (STRING): Hash of row data for deduplication

**Key Tables:**

1. **`bmrs_bod`** (Bid-Offer Data)
   - Most critical dataset
   - Contains power generation bids and offers
   - ~320k rows per day
   - Current: 5,062,269 unique rows (Jan-Feb 2025)

2. **`bmrs_boalf`** (Bid-Offer Acceptance Level Flags)
   - Acceptance flags for bids/offers
   - COMPLETE for 2025 (Jan-Aug)
   - 3,750,118 unique rows

3. **`bmrs_freq`** (Frequency datasets ~8 tables)
   - Grid frequency measurements
   - Partially loaded for 2025

4. **`bmrs_indo`** (Indicated datasets ~10 tables)
   - Various market indicators
   - Partially loaded for 2025

5. **Other datasets:** PHYBMDATA, MEL, MIL, QPN, PN, etc.

---

## 🔄 Skip Logic System

### How It Works

**Problem Solved:** Prevent re-ingesting already loaded data

**Mechanism:**
1. Before fetching data for a time window (e.g., 2025-04-22 to 2025-04-23)
2. Query BigQuery for existing `_window_from_utc` values
3. If window already exists, skip API call
4. Log skipped window for monitoring

**Implementation:**
```python
# Check existing windows
existing = _get_existing_windows(table_name, start_date, end_date)

# Skip if already loaded
if (window_start, window_end) in existing:
    logger.info(f"⏭️  Skipping {dataset} window {window_start} to {window_end} (already loaded)")
    continue

# Otherwise fetch and load
```

**Critical Bug Fix (Applied 27 Oct 2025):**
- **Problem:** BigQuery returns `_window_from_utc` as STRING, not TIMESTAMP
- **Impact:** String "2025-01-01T00:00:00+00:00" never matched datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
- **Result:** Skip logic failed, created 137M+ duplicates
- **Solution:** Parse strings to datetime objects in `_get_existing_windows()`

---

## 📊 Processing Performance

### Current Performance (27 Oct 2025, 12:45 AM)

**BOD Dataset:**
- Rate: 23.8 seconds/day
- Throughput: 2.52 days/minute
- Rows per day: ~320,000
- Data loaded: 81 days in 32 minutes

**Skip Logic Efficiency:**
- 273 windows skipped (as of 00:45)
- BOALF: 242 windows (100% of data already loaded)
- BOD: 31 windows (January already loaded)
- Saves hours of redundant API calls

### Why 2024 Appears Faster Than 2025

**2025 Timeline:**
- BOD remaining: 0.9 hours
- Other datasets: 3.0 hours (checking/skipping partially loaded data)
- **Total: 3.9 hours**

**2024 Timeline:**
- All datasets: 3.1 hours
- **Total: 3.1 hours**

**Explanation:**
- 2024 starts from ZERO - no existing data to check
- 2025 has PARTIAL data for many datasets (BOALF complete, FREQ partial, etc.)
- The 3.0 hours in 2025 is spent checking which windows exist
- 2024 just loads everything sequentially without skip queries
- **2024 is NOT faster per-day, it's simpler with less overhead**

---

## 🚨 Critical Issues Resolved

### Issue 1: Skip Logic Type Mismatch (RESOLVED)
**Discovered:** 27 Oct 2025, ~00:20 AM  
**Impact:** Created 137M+ duplicates in BOD, 9.5M+ in BOALF

**Root Cause:**
```python
# BigQuery returned strings
'2025-01-01T00:00:00+00:00'

# Code compared to datetime objects
datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)

# Never matched → skip logic failed → duplicates created
```

**Solution:**
```python
# Added string parsing in _get_existing_windows()
if isinstance(window_value, str):
    from dateutil import parser
    window_value = parser.parse(window_value)
    if window_value.tzinfo is None:
        window_value = window_value.replace(tzinfo=timezone.utc)
```

**Verification:**
- Deduplication removed duplicates
- Restart logged "273 windows skipped"
- No new duplicates created (verified at 00:45)

---

### Issue 2: Initial Crash (RESOLVED)
**Occurred:** 26 Oct 2025, 10:48 PM  
**Cause:** Unknown (possibly memory, network, or Mac sleep)

**Impact:**
- Loaded 32 days of BOD (Jan 1 - Feb 1)
- 5,062,269 rows ingested before crash

**Resolution:**
- Set Mac sleep to 0 minutes: `sudo pmset -a sleep 0`
- Display sleep to 2 minutes: `sudo pmset -a displaysleep 2`
- Process won't be interrupted if screen sleeps
- Mac must stay powered on (plugged in recommended)

---

## 🔍 Monitoring Commands

### Check Process Status
```bash
# Find ingestion process
ps aux | grep ingest_elexon_fixed.py | grep -v grep

# Check specific PID (current: 13489)
ps aux | grep 13489 | grep -v grep

# Watch CPU/memory usage
top -pid 13489
```

### Monitor Logs
```bash
# 2025 ingestion (current)
tail -f jan_aug_ingest_20251027_001331.log

# 2024 ingestion (after auto-start)
tail -f year_2024_ingest.log

# Follow last 50 lines
tail -50 jan_aug_ingest_20251027_001331.log

# Search for specific dataset
grep "Successfully loaded.*bod" jan_aug_ingest_20251027_001331.log | tail -5
```

### Progress Tracking
```bash
# Automated progress report
python3 monitor_progress.py jan_aug_ingest_20251027_001331.log

# Count successful loads
grep -c "Successfully loaded" jan_aug_ingest_20251027_001331.log

# Check skip logic working
grep "Skipping.*already loaded" jan_aug_ingest_20251027_001331.log | wc -l

# Most recent dataset
grep "Successfully loaded" jan_aug_ingest_20251027_001331.log | tail -1
```

### BigQuery Verification
```bash
# Check table row counts
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

tables = ['bmrs_bod', 'bmrs_boalf']
for table in tables:
    query = f'SELECT COUNT(*) as cnt FROM uk_energy_prod.{table}'
    result = list(client.query(query).result())[0]
    print(f'{table}: {result.cnt:,} rows')
"

# Check for duplicates (should return 0)
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

query = '''
SELECT _hash_key, COUNT(*) as cnt
FROM uk_energy_prod.bmrs_bod
GROUP BY _hash_key
HAVING COUNT(*) > 1
LIMIT 10
'''
for row in client.query(query).result():
    print(f'Hash: {row._hash_key}, Count: {row.cnt}')
"
```

---

## 📅 Completion Timeline

### Current Status (00:45 AM Monday)

**2025 Ingestion:**
- Started: 00:13 AM
- Current: April 22, 2025 (46% complete)
- Remaining: 131 days
- Estimated completion: **4:37 AM Monday**

**2024 Auto-Start:**
- Monitoring script running
- Will start when PID 13489 completes
- Estimated duration: 3.1 hours
- Estimated completion: **7:45 AM Monday**

**Total Expected Completion: 7:45 AM Monday, 27 Oct 2025**

---

## ⚙️ System Requirements

### Environment
- **Python Version:** 3.11+ (using .venv virtual environment)
- **OS:** macOS (current) or Linux
- **Required Packages:**
  - `google-cloud-bigquery`
  - `pandas`
  - `tqdm`
  - `python-dateutil`
  - `elexon` (custom client)

### Mac Configuration
```bash
# Prevent Mac from sleeping
sudo pmset -a sleep 0

# Allow display to sleep (saves power)
sudo pmset -a displaysleep 2

# Check current settings
pmset -g
```

### BigQuery Permissions
- Service account: `jibber_jabber_key.json`
- Required roles:
  - BigQuery Data Editor
  - BigQuery Job User

---

## 🛠️ Troubleshooting

### Process Stopped/Crashed

**Check if running:**
```bash
ps aux | grep ingest_elexon_fixed.py
```

**Restart with cleanup:**
```bash
bash cleanup_and_restart_ingestion.sh
```

**Restart without cleanup (relies on skip logic):**
```bash
bash restart_ingestion.sh
```

### Too Many Duplicates

**Check for duplicates:**
```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

tables = client.list_tables('uk_energy_prod')
for table in tables:
    if table.table_id.startswith('bmrs_'):
        query = f'''
        SELECT COUNT(*) - COUNT(DISTINCT _hash_key) as duplicates
        FROM uk_energy_prod.{table.table_id}
        '''
        result = list(client.query(query).result())[0]
        if result.duplicates > 0:
            print(f'{table.table_id}: {result.duplicates:,} duplicates')
"
```

**Remove duplicates:**
```bash
python3 remove_bod_duplicates.py
```

### Mac Went to Sleep

**Check if process still running:**
```bash
ps aux | grep 13489
```

**If stopped, restart:**
```bash
bash restart_ingestion.sh
# Skip logic will resume from last position
```

### Slow Progress

**Check current rate:**
```bash
python3 monitor_progress.py jan_aug_ingest_20251027_001331.log
```

**Normal rates:**
- BOD: 20-30 seconds/day
- BOALF: 15-25 seconds/day
- Other datasets: Variable

**If slower than 60 seconds/day:**
- Check network connection
- Check BigQuery quota limits
- Check API rate limits

---

## 📚 Related Documentation

**In This Repository:**
- `QUICK_REFERENCE.md` - Quick command reference
- `DATA_INGESTION_DOCUMENTATION.md` - Earlier ingestion docs
- `DATASET_DISCOVERY_PROBLEM_SUMMARY.md` - API endpoint discovery
- `API_RESEARCH_FINDINGS.md` - BMRS API research

**GitHub Actions:**
- `.github/workflows/clean-repo-check.yml` - Prevents forbidden files
- `.github/copilot-instructions.md` - Project guidelines

---

## 🎓 Key Lessons Learned

1. **Type Checking is Critical**
   - Always verify data types from external sources
   - BigQuery returns timestamps as strings unless explicitly cast
   - Type mismatches cause silent failures

2. **Skip Logic is Essential**
   - Prevents expensive duplicate API calls
   - Enables safe restarts without data loss
   - Must be thoroughly tested with actual data

3. **Chunking Strategy Matters**
   - BOD: 1-day chunks (was 1-hour, 24x speedup)
   - Balance between API calls and data volume
   - Smaller chunks = more API calls = slower
   - Larger chunks = fewer calls but more memory

4. **Monitoring is Non-Negotiable**
   - Long-running processes need visibility
   - Log parsing provides real-time insights
   - Progress estimation helps planning

5. **Deduplication Must Be Built-In**
   - Hash-based deduplication with `_hash_key`
   - Keep most recent record (`_ingested_utc DESC`)
   - Verify no duplicates after every restart

6. **Mac Sleep Settings Matter**
   - Process survives terminal closure (nohup)
   - Process DOES NOT survive Mac sleep/shutdown
   - Set sleep=0 for overnight runs
   - Keep Mac plugged in

---

## 📞 Support Commands Quick Reference

```bash
# Check if running
ps aux | grep 13489

# Monitor logs
tail -f jan_aug_ingest_20251027_001331.log

# Progress report
python3 monitor_progress.py jan_aug_ingest_20251027_001331.log

# Restart if needed
bash restart_ingestion.sh

# Full cleanup + restart
bash cleanup_and_restart_ingestion.sh

# Check BigQuery row counts
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print(list(client.query('SELECT COUNT(*) FROM uk_energy_prod.bmrs_bod').result())[0][0])"
```

---

**Document Version:** 1.0  
**Author:** GitHub Copilot + George Major  
**Last Updated:** 27 October 2025, 00:45 AM
