# IRIS Duplicate Data Issue - Root Cause & Fix

**Date**: December 11, 2025  
**Status**: ✅ RESOLVED  
**Impact**: Critical - All generation values were 2-4x too high

## Problem Summary

Live Dashboard v2 was showing incorrect generation data with values approximately 2-4x higher than actual:

| Fuel Type | Shown in Dashboard | Actual Value | Ratio |
|-----------|-------------------|--------------|-------|
| Wind      | 49.2 GW          | 11.84 GW     | 4.15x |
| CCGT      | 34.0 GW          | 7.66 GW      | 4.44x |
| Nuclear   | 14.3 GW          | 3.60 GW      | 3.97x |

## Root Cause Analysis

### The Issue: Duplicate Records in IRIS Tables

The `bmrs_fuelinst_iris` table contains **multiple records for the same settlement period** with different `publishTime` values. These represent **data revisions** as National Grid updates the values.

**Example from Period 47 (Dec 11, 2025)**:

```
fuelType: WIND
Row 1: publishTime=23:10:00, generation=11,841 MW  (latest revision)
Row 2: publishTime=23:05:00, generation=11,768 MW  (earlier revision)
```

### Why This Happened

1. **IRIS streaming pipeline** receives real-time updates from National Grid
2. National Grid publishes **initial values** at the start of each settlement period
3. They then publish **revised values** 5-10 minutes later with updated data
4. The IRIS uploader (`iris_to_bigquery_unified.py`) correctly stores ALL revisions
5. **BUT** queries were using `SUM(generation)` without deduplicating by `publishTime`

### Query Comparison

**❌ BROKEN QUERY** (summing duplicates):
```sql
WITH latest AS (
    SELECT 
        fuelType,
        SUM(generation) as generation_mw  -- Sums ALL revisions!
    FROM bmrs_fuelinst_iris
    WHERE settlementDate = (SELECT MAX(settlementDate)...)
      AND settlementPeriod = (SELECT MAX(settlementPeriod)...)
    GROUP BY fuelType
)
SELECT fuelType, generation_mw / 1000 as gen_gw
FROM latest
```

**Result**: Wind = 23.61 GW (11,841 + 11,768 = 23,609 MW) ❌

**✅ FIXED QUERY** (using latest revision only):
```sql
WITH latest_period AS (
    SELECT MAX(settlementDate) as max_date
    FROM bmrs_fuelinst_iris
),
latest_sp AS (
    SELECT MAX(settlementPeriod) as max_sp
    FROM bmrs_fuelinst_iris
    WHERE settlementDate = (SELECT max_date FROM latest_period)
),
-- Deduplicate by latest publishTime
deduplicated AS (
    SELECT 
        fuelType,
        generation,
        ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY publishTime DESC) as rn
    FROM bmrs_fuelinst_iris
    WHERE settlementDate = (SELECT max_date FROM latest_period)
      AND settlementPeriod = (SELECT max_sp FROM latest_sp)
),
latest AS (
    SELECT 
        fuelType,
        SUM(generation) as generation_mw
    FROM deduplicated
    WHERE rn = 1  -- Only latest publishTime
    GROUP BY fuelType
)
SELECT fuelType, generation_mw / 1000 as gen_gw
FROM latest
```

**Result**: Wind = 11.84 GW (11,841 MW only) ✅

## Files Fixed

### 1. `update_live_dashboard_v2.py`
**Functions updated**:
- `get_generation_mix()` - Lines 128-162
- `get_interconnectors()` - Lines 178-206
- `get_kpis()` - Lines 53-87

**Change**: Added `ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY publishTime DESC)` to select only the latest revision for each fuel type.

### 2. `update_gb_live_complete.py`
**Functions updated**:
- `get_kpis()` - Lines 135-190
- `get_generation_mix()` - Lines 198-236
- `get_interconnectors()` - Lines 246-274

**Change**: Same deduplication logic applied.

## Testing & Verification

### Before Fix:
```
BigQuery query returned:
  WIND: 23.61 GW  ❌
  CCGT: 15.41 GW  ❌
  NUCLEAR: 7.19 GW  ❌
```

### After Fix:
```
BigQuery query returned:
  WIND: 11.84 GW  ✅
  CCGT: 7.66 GW   ✅
  NUCLEAR: 3.60 GW ✅
```

**Verified against**: gridwatch.co.uk live data (Dec 11, 2025, 23:25)

## Why Duplicates Exist in IRIS Data

This is **expected behavior** and actually a **feature** of the IRIS pipeline:

1. **Real-time accuracy**: Get initial values immediately
2. **Data quality**: Receive corrected values as National Grid refines them
3. **Audit trail**: Keep all revisions for analysis
4. **Compliance**: Match National Grid's publication timeline

### Historical vs IRIS Tables

| Aspect | Historical Tables | IRIS Tables (_iris suffix) |
|--------|------------------|---------------------------|
| Source | Elexon BMRS REST API | Azure Service Bus (IRIS) |
| Updates | Daily batch | Real-time streaming |
| Duplicates | None (final data only) | Yes (all revisions) |
| Coverage | 2020 - yesterday | Last 24-48 hours |
| Query pattern | Simple WHERE | Requires deduplication |

## Future Prevention

### ⚠️ CRITICAL RULE for IRIS Queries

**ALWAYS deduplicate IRIS tables by `publishTime`** when querying for specific settlement periods:

```sql
-- Pattern to copy for ALL IRIS queries
WITH deduplicated AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY fuelType  -- Or other grouping column
            ORDER BY publishTime DESC
        ) as rn
    FROM bmrs_fuelinst_iris  -- Or any *_iris table
    WHERE settlementDate = ... AND settlementPeriod = ...
)
SELECT * FROM deduplicated WHERE rn = 1
```

### Tables Affected

All IRIS tables may have duplicate records:
- `bmrs_fuelinst_iris` ✅ FIXED
- `bmrs_mid_iris` (wholesale prices)
- `bmrs_freq_iris` (frequency - typically single record)
- `bmrs_boalf_iris` (balancing acceptances)
- `bmrs_indgen_iris` (individual generation)
- `bmrs_costs_iris` (system prices) - **NOT currently configured in IRIS**

### Checklist for New Queries

When writing queries against IRIS tables:

1. ☑ Are you filtering to a specific settlement period?
2. ☑ Could there be multiple `publishTime` values?
3. ☑ Have you added `ROW_NUMBER() ... ORDER BY publishTime DESC`?
4. ☑ Are you filtering `WHERE rn = 1`?
5. ☑ Have you tested the query returns expected values?

## Related Issues Resolved

This fix also resolved:

- ✅ KPI values (Total Generation, Wind, etc.) now correct
- ✅ Interconnector flows accurate
- ✅ Generation mix percentages correct
- ✅ Dashboard timestamp updating (was working before)
- ⏳ Sparklines still need Apps Script installation (separate issue)

## Deployment

**Automatic**: Both cron jobs will use the fixed scripts on next run (every 5 minutes):

1. `auto_update_dashboard_v2.sh` → `update_live_dashboard_v2.py`
2. `bg_live_cron.sh` → `update_gb_live_complete.py`

**Manual test successful**: Dec 11, 2025, 23:28:32

## References

- **Original issue report**: User message "you're adding all the data together and not doing this properly"
- **Verification data**: gridwatch.co.uk (Dec 11, 2025, 23:25)
- **BigQuery test query**: Dec 11, 2025, 23:22
- **Related docs**: 
  - `STOP_DATA_ARCHITECTURE_REFERENCE.md` (data pipeline overview)
  - `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` (IRIS design)
  - `SPREADSHEET_IDS_MASTER_REFERENCE.md` (spreadsheet configuration)

---

**Last Updated**: December 11, 2025, 23:30  
**Status**: ✅ Production fix deployed  
**Next Review**: Monitor for 24 hours to confirm stability
