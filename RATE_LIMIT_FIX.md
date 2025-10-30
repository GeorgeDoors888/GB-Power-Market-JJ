# BigQuery Rate Limit Fix for FUELINST

## Problem
The 2024 ingestion failed on FUELINST (and likely FREQ, FUELHH) with error:
```
429 Exceeded rate limits: too many table update operations for this table
```

## Root Cause Analysis

### BigQuery Limits
- **1,000 table update operations per table per day**
- Operations must be spread over time, not concentrated in bursts

### Previous Configuration
- `FUELINST`: 1-day chunks
- `MAX_FRAMES_PER_BATCH`: 10 frames before write
- Delay between writes: 2 seconds
- **Result**: 365 days = ~36-37 write operations in ~2 hours = **TOO FAST!**

### Why It Failed
Loading a full year (365 days) in 1-day chunks meant 365 separate API fetches. With batching every 10 frames, this resulted in ~36 BigQuery load jobs executed rapidly (within 1-2 hours), triggering BigQuery's rate limiter designed to prevent burst writes.

## Solution Implemented

### 1. Increased Batch Size
```python
MAX_FRAMES_PER_BATCH = 30  # Was: 10
```
- **Effect**: Reduces number of BigQuery load operations by 3x
- For 365 days: ~12 load jobs instead of ~36

### 2. Increased Chunk Sizes for High-Volume Datasets
```python
"FREQ": "7d",       # Was: "1d"
"FUELINST": "7d",   # Was: "1d"  
"FUELHH": "7d",     # Was: "1d"
```
- **Effect**: Fetches 7 days of data per API call instead of 1
- For 365 days: 52 API calls instead of 365
- Combined with batching: ~2 load jobs per batch vs ~12

### 3. Increased Delays Between Writes
```python
# High-volume datasets (FUELINST, FREQ, FUELHH, BOD)
time.sleep(5.0)  # Was: 2.0

# Other datasets
time.sleep(2.0)  # Unchanged
```
- **Effect**: Spaces out writes to avoid burst detection
- 5 seconds × 12 jobs = 60 seconds minimum spread

### 4. Fixed Dataset Location
```python
ds.location = "US"  # Was: "EU"
```
- Matches actual dataset location to avoid conflicts

## Expected Results

### Before (Failed Configuration)
- 365 days of FUELINST data
- 1-day chunks → 365 API calls
- 10-frame batching → ~36 load jobs
- 2s delays → ~72 seconds total
- **Result**: 36 writes in 72 seconds = **RATE LIMIT HIT** ❌

### After (Fixed Configuration)
- 365 days of FUELINST data
- 7-day chunks → 52 API calls
- 30-frame batching → ~2 load jobs per batch
- 5s delays → longer spacing
- **Result**: Distributed writes over longer period = **SUCCESS** ✅

## Impact on Ingestion Time

### FUELINST Load Time Estimates
- **Before**: ~2 hours for API calls + rapid writes (but FAILS at end)
- **After**: ~2.5 hours for API calls + spaced writes (but SUCCEEDS)

The slightly longer runtime (extra 30 minutes) is worth it to avoid rate limit failures and ensure complete data loading.

## Verification

After 2024 ingestion completes, verify FUELINST loaded properly:

```sql
SELECT 
    EXTRACT(YEAR FROM startTime) as year,
    EXTRACT(MONTH FROM startTime) as month,
    COUNT(*) as rows,
    MIN(DATE(startTime)) as first_date,
    MAX(DATE(startTime)) as last_date
FROM `uk_energy_prod.bmrs_fuelinst`
WHERE EXTRACT(YEAR FROM startTime) = 2024
GROUP BY year, month
ORDER BY month;
```

Expected: All 12 months with data for 2024.

## Next Steps

1. ✅ **Applied**: Changes to `ingest_elexon_fixed.py`
2. ⏳ **Current**: 2024 ingestion running with old config (will need to retry FUELINST)
3. 🔄 **Future**: 2023 ingestion will use new config automatically
4. 📝 **After 2023**: Re-run Jan-Aug 2025 to fill missing datasets using new config

## Files Modified
- `ingest_elexon_fixed.py`: Lines 62-63 (MAX_FRAMES_PER_BATCH), 88-90 (chunk sizes), 326 (location), 1447-1449 (delays)

---
**Date**: October 27, 2025  
**Author**: GitHub Copilot  
**Status**: ✅ Applied, awaiting validation
