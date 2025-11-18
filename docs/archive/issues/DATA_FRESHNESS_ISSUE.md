# ⚠️ Data Freshness Issue - Power Station Warnings

## Problem Summary

The **power station outage warnings system** is working correctly, but the underlying data is **3-6 days old**, limiting its effectiveness for real-time monitoring.

## Current Status (31 Oct 2025)

| Table | Latest Date | Age | Settlement Periods | Purpose |
|-------|-------------|-----|-------------------|---------|
| **bmrs_indo** | 28 Oct | 3 days | 61 | Demand data |
| **bmrs_fuelinst** | 28 Oct | 3 days | 48 (full day) | Wind generation |
| **bmrs_mid** | 30 Oct | 1 day | 2 only! | System prices |
| **demand_outturn** | 25 Oct | 6 days | 48 (full day) | Alternative demand source |

## Impact on Warnings

### ✅ Working Warnings
- **Wind shortfall detection** - Works (bmrs_fuelinst is complete)
- **High wind detection** - Works (bmrs_fuelinst is complete)
- **High demand detection** - Works (bmrs_indo is complete)

### ⚠️ Partially Working
- **Price-based outage warnings** - INCOMPLETE
  - Only 2/48 settlement periods have price data for latest day
  - Cannot detect capacity shortages via high prices
  - Cannot detect excess generation via negative prices

## Root Cause

**Different data ingestion pipelines update at different rates:**

1. **bmrs_fuelinst** (generation) - Updated regularly, 48 periods/day
2. **bmrs_indo** (demand) - Updated regularly but lags 3 days
3. **bmrs_mid** (prices) - **Severely lagging**, only 2 records for latest day

## Solution Options

### Option 1: Use IRIS Real-Time Tables ✅ RECOMMENDED
```python
# Use bmrs_*_iris tables for last 24-48 hours
bmrs_mid_iris      # Real-time prices (30s-2min lag)
bmrs_fuelinst_iris # Real-time generation
bmrs_freq_iris     # Real-time frequency
```

**Pros:**
- Real-time data (30s-2min lag)
- Full settlement period coverage
- Best for outage detection

**Cons:**
- Only covers last 24-48 hours
- Different schema

### Option 2: Accept 3-Day Lag
Keep current system but adjust expectations:
- Warnings show "3 days ago" data
- Useful for historical analysis
- Not suitable for live monitoring

### Option 3: Hybrid Approach ✅ BEST
```python
# Try IRIS first (real-time)
# Fall back to historical if IRIS unavailable
# Show data age clearly
```

## Recommended Actions

### Immediate (Today)
1. ✅ Update script to use **bmrs_mid** instead of **bmrs_bod** for prices
2. ✅ Add warning when price data is incomplete
3. ✅ Show data age prominently

### Short-term (This Week)
4. 🔄 Switch to **bmrs_*_iris tables** for real-time monitoring
5. 🔄 Add IRIS availability check
6. 🔄 Implement hybrid historical/real-time approach

### Long-term (Next Month)
7. ⏭️ Investigate why bmrs_mid is updating slowly
8. ⏭️ Set up data pipeline monitoring
9. ⏭️ Create alert when data lag exceeds threshold

## Current Warnings Output

**Example from 31 Oct 2025:**
```
📅 Latest date: 2025-10-28
⚠️  WARNING: Data is 3 day(s) old (today is 2025-10-31)
   Latest available: 2025-10-28

⚠️  Price data incomplete: 46/48 periods missing (bmrs_mid table lag)
   Power station outage warnings may be inaccurate

✅ SYSTEM WARNINGS:
🟡 WIND SHORTFALL: 9.3GW below expected
🟡 HIGH DEMAND: 48 periods above 30GW (Peak: 30.77GW)
🟢 HIGH WIND: 48 periods above 20GW (Peak: 93.23GW)
```

## What's Working vs Not Working

### ✅ Working Features
- Data retrieval from BigQuery
- Wind generation analysis
- Demand pattern analysis
- Warning logic (correct thresholds)
- Visual chart creation
- Warning section in Sheet1

### ⚠️ Limited by Data Age
- **Real-time outage detection** - Need IRIS tables
- **Current price alerts** - Need complete bmrs_mid data
- **Live capacity shortage warnings** - Need real-time prices

## Next Steps

See: `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` for details on switching to IRIS real-time tables.

**Script to update**: `create_latest_day_chart.py`  
**Target**: Add IRIS table fallback for last 24 hours

---

**Last Updated:** 31 October 2025  
**Status:** Data freshness issue identified, warnings system functional but using old data
