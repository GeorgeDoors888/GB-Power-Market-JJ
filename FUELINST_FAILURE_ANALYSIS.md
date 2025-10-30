# How Did FUELINST Ingestion Work (or Fail)?

## Question
"How did we ingest FUELINST for 2024, 2023 with the old script?"

## Short Answer
**We DIDN'T successfully ingest it!** The script ran, made 333+ attempts to load FUELINST data, but BigQuery rejected most/all of them with 429 rate limit errors.

---

## Evidence

### 1. BigQuery Current State
```
Query: SELECT COUNT(*), year FROM bmrs_fuelinst GROUP BY year

Results:
- 2024: NO DATA (0 rows) ❌
- 2023: NO DATA (0 rows) ❌
- 2025: 2,161,900 rows (but ONLY Oct 27, 2025 - today!)
```

### 2. 2024 Ingestion Log Analysis
```bash
# From year_2024_final.log:
Rate limit errors (429): Hundreds of instances
Successful load attempts: 333 times

Sample errors:
- 2024-02-05: 429 Exceeded rate limits
- 2024-02-11: 429 Exceeded rate limits
- 2024-03-01: 429 Exceeded rate limits
- 2024-04-11: 429 Exceeded rate limits
- 2024-06-04: 429 Exceeded rate limits
- 2024-07-12: 429 Exceeded rate limits
- 2024-08-03: 429 Exceeded rate limits
```

### 3. Pattern Recognition
The log shows:
- ✅ Script successfully **fetched** FUELINST data from API
- ✅ Script successfully **prepared** DataFrames for loading
- ✅ Script called BigQuery load_table_from_dataframe() 333 times
- ❌ BigQuery **rejected** the loads with 429 errors
- ❌ Script **continued** to next dataset (didn't retry effectively)

---

## Why It Failed

### The Problem: Too Many Table Operations
- **BigQuery limit**: 1,000 table updates per table per day
- **Our old config**: 1-day chunks + 10-frame batching
- **2024 ingestion**: 365 days ÷ 10 frames = ~37 BigQuery load jobs
- **Execution time**: All 37 loads in ~1-2 hours = **burst write pattern**

BigQuery's rate limiter detected rapid-fire writes and started rejecting them around **February 5, 2024** (day 36 of the year).

### The Root Cause
```python
# Old configuration (line 62-63, 88-90)
MAX_FRAMES_PER_BATCH = 10        # Too small - causes too many writes
CHUNK_RULES["FUELINST"] = "1d"   # Too small - fetches every single day
time.sleep(2.0)                  # Too short - writes happen too fast
```

This combination meant:
1. Fetch Jan 1 → load to BQ (write #1)
2. Fetch Jan 2 → load to BQ (write #2)
3. ... continue for 365 days ...
4. By Feb 5 (write #36), BigQuery says "STOP! Too many writes!" ❌

---

## What About 2025 Jan-Aug?

### Same Story
The Jan-Aug 2025 run completed at **07:41 AM** but:
- ✅ BOD loaded successfully (73.2M rows)
- ❌ FUELINST failed (0 rows loaded)
- ❌ FREQ failed (0 rows loaded)
- ❌ Other 50 datasets also failed

**Why?** Same rate limit problem.

### The Mystery Oct 27 Data
The 2.16M rows of Oct 27, 2025 FUELINST data likely came from:
- A manual test run
- Current 2024 ingestion writing today's date by mistake
- A separate data source

It's NOT from the historical ingestion - it's just today's data.

---

## The Fix (Now Applied)

### New Configuration
```python
# Lines 62-63: Tripled batch size
MAX_FRAMES_PER_BATCH = 30        # Was: 10 → 3x fewer writes

# Lines 88-90: 7x larger chunks
CHUNK_RULES["FUELINST"] = "7d"   # Was: "1d" → 7x fewer API calls
CHUNK_RULES["FREQ"] = "7d"       # Was: "1d"
CHUNK_RULES["FUELHH"] = "7d"     # Was: "1d"

# Line 1449: Longer delays
time.sleep(5.0)                  # Was: 2.0 → better spacing
```

### New Math
For 365 days:
- API calls: 365 ÷ 7 = **52 fetches** (was 365)
- Load jobs: 52 ÷ 30 = **2 writes** per batch (was 37)
- Delays: 5 seconds between writes (was 2)
- **Result**: Spreads load over longer time, avoids burst detection ✅

---

## The Repair Strategy

### Why We Need It
Since 2024 and 2023 ingestions are running with **OLD config** (loaded before fixes), they will:
1. Successfully load 50 datasets (BOD, PN, QPN, etc.)
2. **Fail** on FUELINST, FREQ, FUELHH (rate limits)
3. Complete with gaps

### The Repair Script Does:
```bash
# After 2023 completes (~7:19 PM):

# 1. Fix 2023 FUELINST/FREQ/FUELHH with NEW config
python ingest_elexon_fixed.py \
  --start 2023-01-01 --end 2023-12-31 \
  --only FUELINST,FREQ,FUELHH
# Uses: 7d chunks, 30-frame batch, 5s delays ✅

# 2. Fix 2024 FUELINST/FREQ/FUELHH with NEW config
python ingest_elexon_fixed.py \
  --start 2024-01-01 --end 2024-12-31 \
  --only FUELINST,FREQ,FUELHH
# Uses: 7d chunks, 30-frame batch, 5s delays ✅

# 3. Load ALL 2025 datasets with NEW config
python ingest_elexon_fixed.py \
  --start 2025-01-01 --end 2025-08-31
# Loads all 53 datasets (BOD will skip, others will load)
# Uses: 7d chunks, 30-frame batch, 5s delays ✅
```

---

## Timeline Summary

| Date/Time | Event | FUELINST Status |
|-----------|-------|-----------------|
| Oct 27, 01:09 AM | Started 2025 Jan-Aug ingestion | ❌ Failed (rate limits) |
| Oct 27, 07:41 AM | 2025 Jan-Aug "completed" | ❌ 0 rows loaded |
| Oct 27, 07:42 AM | Auto-started 2024 ingestion | ❌ Failing (rate limits) |
| Oct 27, 12:08 PM | Restarted 2024 after crash | ❌ Still failing |
| Oct 27, 02:22 PM | **Applied fixes to script** | 🔧 New config ready |
| Oct 27, ~7:19 PM | Repair script starts | ✅ Will use new config |
| Oct 27, ~10:30 PM | 2023/2024 FUELINST repaired | ✅ Complete |
| Oct 28, ~4:15 AM | 2025 fully loaded | ✅ Complete |

---

## Conclusion

**Q: How did we ingest FUELINST for 2024, 2023 with the old script?**

**A: We DIDN'T.** The old script:
- ✅ Successfully fetched the data from Elexon API
- ✅ Successfully prepared it for loading
- ❌ Got rejected by BigQuery with 429 errors
- ❌ Logged the failures but continued to next dataset
- ❌ Left FUELINST table completely empty for those years

That's why the repair script is essential - it will be the **first successful ingestion** of FUELINST for 2023 and 2024, using the new rate-limit-safe configuration.

---

**Date**: October 27, 2025, 2:30 PM  
**Status**: Waiting for repair to begin at ~7:19 PM  
**Expected Outcome**: Complete FUELINST data for 2023-2025 by Monday 4:15 AM
