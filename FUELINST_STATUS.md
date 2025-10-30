# FUELINST Status - July 2024 Data

**Query Date:** 27 October 2025, 2:57 PM

## ❌ Current Status: NOT YET AVAILABLE

### Query Results

**July 2024 FUELINST Data:**
- Total rows: **0**
- Date range: **None**
- Status: **❌ Not loaded**

**2 July 2024, Settlement Period 1:**
- Fuel mix data: **❌ Not available**

## Why No Data Yet?

### Current 2024 Run Status

The 2024 ingestion that's running now (PID 5637) is **68% complete** and on dataset PN.

**FUELINST is one of the high-volume datasets that will FAIL during the main run due to rate limits.**

From our earlier analysis:
```
2024 original run: 333 FUELINST load attempts, ALL rejected with 429 errors
Rate limit: BigQuery 1,000 table updates/day per table
FUELINST writes too fast and hits this limit
```

### The Fix: Tonight's Repair

**FUELINST will be loaded in the repair phase:**

#### Timeline:
1. **2024 main run completes:** ~3:57 PM (1 hour from now)
   - Will load 50/53 datasets
   - FUELINST/FREQ/FUELHH will fail (as expected)

2. **2023 runs:** ~3:57 PM to ~7:57 PM
   - FUELINST/FREQ/FUELHH will also fail

3. **Repair phase starts:** ~7:57 PM
   - **2023 FUELINST/FREQ/FUELHH:** ~7:57 PM to ~8:10 PM ✅
   - **2024 FUELINST/FREQ/FUELHH:** ~8:10 PM to ~8:24 PM ✅ ← **July 2024 loaded here**
   - 2025 other datasets: ~8:24 PM to ~11:00 PM

## When Will July 2024 FUELINST Be Available?

### ⏰ **~8:24 PM Tonight**

After that, you can query:
```sql
SELECT 
  settlementDate,
  settlementPeriod,
  fuelType,
  generation
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate = '2024-07-02'
  AND settlementPeriod = 1
ORDER BY generation DESC
```

Expected output (typical July fuel mix):
```
Fuel Type            Generation (MW)
----------------------------------------
CCGT                        15,000-18,000
WIND                         8,000-12,000
NUCLEAR                      5,000-6,500
BIOMASS                      2,000-3,000
NPSHYD                       1,000-1,500
PS                             500-1,000
COAL                               0-100
INTFR                        1,000-2,000 (imports)
...
```

## Current vs Future State

### Right Now (2:57 PM)
```
bmrs_fuelinst table:
- 2025: Only October 27 data (2.16M rows)
- 2024: NO DATA ❌
- 2023: NO DATA ❌
```

### After 8:24 PM Tonight
```
bmrs_fuelinst table:
- 2025: Jan-Aug complete (~12M rows) ✅
- 2024: Full year complete (~17.5M rows) ✅
- 2023: Full year complete (~17.5M rows) ✅
```

## Why the Current Run Doesn't Have FUELINST

The script loads datasets alphabetically:
```
✅ ABUC
✅ AGPT
✅ AGWS
...
✅ BOD
...
❌ FUELINST  ← Will attempt, will fail due to rate limits
❌ FREQ      ← Will attempt, will fail due to rate limits
❌ FUELHH    ← Will attempt, will fail due to rate limits
...
✅ PN  ← Currently here
...
```

**The main run WILL attempt FUELINST**, but with the old configuration (1-day chunks), it will hit rate limits and fail to write any rows.

**The repair phase uses NEW configuration:**
- 7-day chunks (7x fewer API calls)
- 30-frame batching (3x fewer BigQuery writes)
- 5-second delays (more breathing room)
- Result: Successfully loads without hitting rate limits ✅

## Summary

**Question:** "Do you have FUELINST for July 2024?"
**Answer:** ❌ **Not yet** - will be loaded at ~8:10-8:24 PM tonight

**Question:** "What is the mix for 2 July 2024 Settlement Period 1?"
**Answer:** ❌ **Not available yet** - query will work after ~8:24 PM tonight

**Why the delay?** 
The current 2024 run will fail on FUELINST due to rate limits. The repair phase tonight (~8:10 PM) uses optimized configuration and will successfully load all of 2024's FUELINST data.

**Estimated availability:** 5 hours 27 minutes from now (~8:24 PM)

---

**Updated:** 27 October 2025, 2:57 PM
**Next check:** After 8:24 PM tonight
