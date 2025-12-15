# Live Dashboard v2 - Issue Resolution Summary

**Date**: December 11, 2025  
**Time**: 23:30 GMT  
**Status**: ✅ **RESOLVED**

---

## Issue Report

**User complaint**: "the data is wrong... you're adding all the data together and not doing this properly"

### Symptoms
Dashboard showing values approximately **2-4x too high**:

| Metric | Shown (WRONG) | Actual | Error Factor |
|--------|---------------|--------|--------------|
| Wind   | 49.2 GW      | 11.84 GW | 4.15x |
| CCGT   | 34.0 GW      | 7.66 GW  | 4.44x |
| Nuclear| 14.3 GW      | 3.60 GW  | 3.97x |

---

## Root Cause

### The Problem
IRIS real-time tables (`bmrs_fuelinst_iris`) contain **duplicate records** for the same settlement period, representing **data revisions** published by National Grid at different times.

**Example**:
```
Period 47, Wind generation:
- publishTime 23:05:00 → 11,768 MW (initial)
- publishTime 23:10:00 → 11,841 MW (revised)
```

### Why It Happened
Query was using `SUM(generation)` without filtering to **latest publishTime**, causing it to sum ALL revisions:

```sql
-- BROKEN QUERY
SUM(generation)  -- Sums 11,768 + 11,841 = 23,609 MW ❌
```

**Result**: 23.6 GW instead of 11.8 GW

---

## The Fix

### Solution: Deduplicate by Latest `publishTime`

Added `ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY publishTime DESC)` to all IRIS queries:

```sql
-- FIXED QUERY
WITH deduplicated AS (
    SELECT 
        fuelType,
        generation,
        ROW_NUMBER() OVER (
            PARTITION BY fuelType 
            ORDER BY publishTime DESC  -- Latest revision first
        ) as rn
    FROM bmrs_fuelinst_iris
    WHERE settlementDate = ... AND settlementPeriod = ...
)
SELECT fuelType, SUM(generation) as gen_mw
FROM deduplicated
WHERE rn = 1  -- Only latest revision ✅
GROUP BY fuelType
```

### Files Modified

1. **`update_live_dashboard_v2.py`**
   - `get_generation_mix()` - Fixed generation data query
   - `get_interconnectors()` - Fixed interconnector flows
   - `get_kpis()` - Fixed KPI calculations

2. **`update_gb_live_complete.py`**
   - `get_kpis()` - Fixed KPI calculations  
   - `get_generation_mix()` - Fixed generation data query
   - `get_interconnectors()` - Fixed interconnector flows

---

## Verification

### Before Fix (23:20)
```
Dashboard showed:
  Wind: 49.2 GW ❌
  CCGT: 34.0 GW ❌
  Nuclear: 14.3 GW ❌
```

### After Fix (23:30)
```
Dashboard shows:
  Wind: 11.8 GW ✅
  CCGT: 7.7 GW ✅
  Nuclear: 3.6 GW ✅
```

**Verified against**: gridwatch.co.uk live data (11 Dec 2025, 23:25)

### Test Results

```bash
# Test query with deduplication
BigQuery returned:
  WIND: 11.84 GW ✅
  CCGT: 7.66 GW ✅
  NUCLEAR: 3.60 GW ✅

# Spreadsheet update successful
Dashboard timestamp: 11/12/2025, 23:28:32
Generation mix: 10 fuel types ✅
Interconnectors: 10 connections ✅
```

---

## Technical Details

### Why Duplicates Exist (This is Normal!)

IRIS streaming pipeline receives **real-time updates** from National Grid:

1. **Initial publication**: Values at start of settlement period (e.g., 23:00)
2. **Revised publication**: Updated values 5-10 minutes later (e.g., 23:05, 23:10)
3. **All stored**: IRIS uploader keeps ALL revisions for audit trail

This is **expected behavior** and allows us to:
- Get data immediately (initial values)
- Have accurate data (revised values)
- Track changes (audit trail)

### Historical vs IRIS Tables

| Aspect | Historical Tables | IRIS Tables |
|--------|------------------|-------------|
| Duplicates | ❌ None | ✅ Multiple revisions |
| Query pattern | Simple WHERE | Requires deduplication |
| Coverage | 2020-yesterday | Last 24-48 hours |
| Update | Daily batch | Real-time streaming |

---

## Deployment

### Automatic Rollout
Both cron jobs now use fixed scripts (update every 5 minutes):

```bash
# Cron 1: Basic updater
*/5 * * * * ~/auto_update_dashboard_v2.sh
→ Runs: update_live_dashboard_v2.py ✅ FIXED

# Cron 2: Complete updater with sparklines
*/5 * * * * ~/bg_live_cron.sh
→ Runs: update_gb_live_complete.py ✅ FIXED
```

### Manual Testing
```bash
python3 update_live_dashboard_v2.py
# ✅ Success: Updated at 23:28:32
# ✅ Values correct: Wind 11.8 GW, CCGT 7.7 GW, Nuclear 3.6 GW
```

---

## Prevention: Critical Rule for IRIS Queries

### ⚠️ ALWAYS Deduplicate IRIS Tables

When querying ANY `*_iris` table for specific settlement periods:

```sql
-- TEMPLATE TO COPY
WITH deduplicated AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY [grouping_column]  -- e.g., fuelType, bmUnitId
            ORDER BY publishTime DESC
        ) as rn
    FROM [iris_table]  -- e.g., bmrs_fuelinst_iris
    WHERE settlementDate = ... AND settlementPeriod = ...
)
SELECT * FROM deduplicated WHERE rn = 1
```

### Affected IRIS Tables
All IRIS tables may have duplicates:
- ✅ `bmrs_fuelinst_iris` (FIXED)
- ⚠️ `bmrs_mid_iris` (wholesale prices - check queries)
- ⚠️ `bmrs_freq_iris` (frequency - usually single record)
- ⚠️ `bmrs_boalf_iris` (balancing - check queries)
- ⚠️ `bmrs_indgen_iris` (individual gen - check queries)

---

## Related Issues

### ✅ Resolved by This Fix
- Incorrect generation values (primary issue)
- Incorrect KPI calculations
- Incorrect interconnector flows  
- Incorrect generation mix percentages
- Dashboard timestamp (was already working)

### ⏳ Still Pending (Separate Issues)
- Sparklines (rows 7-8) not populated → Requires Apps Script installation
- Two cron jobs running simultaneously → May cause conflicts, review needed

---

## Documentation Created

1. **`IRIS_DUPLICATE_DATA_FIX.md`** - Full technical analysis
2. **`LIVE_DASHBOARD_V2_FIX_SUMMARY.md`** - This file (executive summary)
3. **`SPREADSHEET_IDS_MASTER_REFERENCE.md`** - Spreadsheet ID reference (created earlier today)
4. **`SPREADSHEET_CONFUSION_RESOLVED.md`** - Spreadsheet ID confusion fix (created earlier today)

---

## Timeline

| Time | Event |
|------|-------|
| 22:45 | User reports: "data is wrong, not updating properly" |
| 23:00 | Diagnosed spreadsheet ID confusion (1MSl8fJ0... vs 1-u794iGngn5...) |
| 23:05 | Fixed spreadsheet IDs in all scripts |
| 23:10 | User reports: "still wrong - you're adding all the data together" |
| 23:15 | Discovered duplicate rows in BigQuery (2 rows per fuelType) |
| 23:20 | Identified root cause: missing publishTime deduplication |
| 23:25 | Applied fix to all IRIS queries in both scripts |
| 23:28 | Tested fix - dashboard now shows correct values ✅ |
| 23:30 | Verified in spreadsheet: Wind 11.8 GW (was 49.2) ✅ |

---

## References

- **Spreadsheet**: [Live Dashboard v2](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)
- **Apps Script ID**: 1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980
- **Verification source**: gridwatch.co.uk
- **BigQuery project**: inner-cinema-476211-u9
- **Dataset**: uk_energy_prod

---

**Status**: ✅ **PRODUCTION FIX DEPLOYED**  
**Next Action**: Monitor for 24 hours to confirm stability  
**Owner**: George Major (george@upowerenergy.uk)

---

*Last Updated: December 11, 2025, 23:30 GMT*
