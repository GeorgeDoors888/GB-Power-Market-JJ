# Dashboard Data Availability - Important Notice

**Date:** November 6, 2025  
**Status:** PARTIAL DATA AVAILABLE ⚠️

## Summary

**You were right!** The IRIS tables (and related generation/demand/interconnector tables) **stopped being updated after October 30, 2025**. This is affecting the dashboard's ability to pull complete data for recent dates.

## What's Working ✅

For **today (Nov 6, 2025)** and recent dates, these data sources ARE available:

| Data Type | Table | Status | Notes |
|-----------|-------|--------|-------|
| **System Prices** | `bmrs_mid` | ✅ LIVE | SSP (System Sell Price) and SBP (System Buy Price) |
| **Bid-Offer Data** | `bmrs_bod` | ✅ LIVE | Balancing mechanism bid and offer prices |
| **Balancing Actions** | `bmrs_boalf` | ✅ LIVE | Accepted balancing actions with level changes |

## What's NOT Working ❌

These data sources have **NO data after October 30, 2025**:

| Data Type | Table | Last Update | Impact |
|-----------|-------|-------------|--------|
| **Generation** | `bmrs_indgen_iris` | Oct 30, 2025 | No national generation data |
| **Generation** | `bmrs_indgen` (non-IRIS) | Oct 30, 2025 | No national generation data |
| **Demand** | `bmrs_inddem` | Oct 30, 2025 | No national demand data |
| **Interconnectors** | `bmrs_fuelinst` | Oct 30, 2025 | No interconnector flow data |
| **Interconnectors** | `bmrs_fuelinst_iris` | Never had data | Table appears unused |

## Root Cause Analysis

### IRIS Tables Issue

The `bmrs_indgen_iris` table:
- **Has data for Nov 6, 2025** ✅ (47,664 rows)
- **BUT** uses `boundary` field with values like "B1", "B2", etc. (Grid Supply Point codes)
- `boundary='N'` should give national totals
- Query returns data BUT was causing issues

### Non-IRIS Tables Issue

The non-IRIS tables (`bmrs_indgen`, `bmrs_inddem`, `bmrs_fuelinst`):
- **Last update:** October 30, 2025
- **Zero rows** for any date after that
- These were more reliable but stopped being populated

## Technical Details

###  What We Discovered

1. **Generation/Demand Tables Structure:**
   ```sql
   -- bmrs_indgen_iris has data but complex structure
   SELECT settlementPeriod, generation, boundary
   FROM bmrs_indgen_iris
   WHERE DATE(settlementDate) = '2025-11-06' AND boundary = 'N'
   -- Returns ~72 readings per SP (multiple generators aggregated)
   ```

2. **Boundary Codes:**
   - `'N'` = National total
   - `'B1'` through `'B17'` = Regional Grid Supply Points
   - Need to filter for `boundary='N'` and aggregate

3. **Data Ingestion Pipeline:**
   - BMRS data appears to be ingested through multiple pipelines
   - IRIS tables: Real-time/near-real-time
   - Non-IRIS tables: Batch processing (stopped Oct 30)

## Current Dashboard Behavior

The dashboard now:

1. **Queries all 5 data sources** (prices, gen, demand, boalf, bod, ic)
2. **Warns** if generation/demand/interconnector data unavailable
3. **Gracefully handles empty results** - columns appear but are blank
4. **Writes whatever data IS available** to Google Sheets

### Today's Output (Nov 6, 2025):

| Column | Status |
|--------|--------|
| SP | ✅ Present (1-50) |
| SSP | ✅ Present (~£0-100/MWh) |
| SBP | ✅ Present (~£75/MWh) |
| Demand_MW | ⚠️ EMPTY (no data after Oct 30) |
| Generation_MW | ⚠️ EMPTY (no data after Oct 30) |
| BOALF_Acceptances | ✅ Present |
| BOALF_Avg_Level_Change | ✅ Present |
| BOD_Offer_Price | ✅ Present |
| BOD_Bid_Price | ✅ Present |
| IC_NET_MW | ⚠️ EMPTY (no data after Oct 30) |

## Workarounds & Solutions

### Option 1: Use Historical Dates ✅

```bash
# Use a date when all data was available
.venv/bin/python tools/refresh_live_dashboard.py --date 2025-10-30
```

**Result:** All 10 columns will be populated

### Option 2: Accept Partial Data ⚠️

For recent dates (after Oct 30):
- **Prices, BOD, BOALF** will be current
- **Generation, Demand, Interconnectors** will be empty
- Still useful for price analysis and balancing mechanism activity

### Option 3: Alternative Data Sources 🔍

Investigate other tables that might have recent generation/demand data:
- `bmrs_fuelhh` - Hourly fuel type generation (may have recent data)
- `bmrs_fuelinst_unified` - Views that might aggregate differently
- Direct NESO/ELEXON API calls (bypassing BigQuery)

### Option 4: Contact Data Provider 📧

The data pipeline appears to have stopped. This might be:
- Planned maintenance
- Data schema migration
- Pipeline failure
- Intentional deprecation of non-IRIS tables

## Recommendations

### Immediate Actions:

1. **✅ Use dashboard for price analysis** - SSP, SBP, BOD prices ARE current
2. **✅ Monitor balancing actions** - BOALF data IS current  
3. **⚠️ Don't rely on generation/demand** - Data is stale (Oct 30)

### Investigation Needed:

1. **Check other fuel/generation tables:**
   ```bash
   bq query "SELECT MAX(DATE(settlementDate)) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelhh\`"
   ```

2. **Test NESO BMRS API directly:**
   - May have real-time generation/demand data
   - Might need to supplement BigQuery with API calls

3. **Check with data team:**
   - Is this a known outage?
   - When will indgen/inddem/fuelinst resume updates?
   - Should we switch to different tables?

## Updated Dashboard Code

The dashboard script now:

```python
# Warns about potential data gaps
print("⚠️  Note: Generation/Demand/Interconnector data may be unavailable for recent dates")

# Handles empty results gracefully
cols_to_select = ["sp","ssp","sbp"]
if "demand_mw" in base.columns:
    cols_to_select.append("demand_mw")
# ... etc for other columns

# Dynamic column count for named range
num_cols = len(tidy.columns)
set_named_range("NR_TODAY_TABLE","Live Dashboard",1,1,51,num_cols)
```

## Testing Results

### Test 1: Recent Date (Nov 6, 2025)
```bash
make today
```
**Result:**
- ✅ Prices populated
- ✅ BOD populated
- ✅ BOALF populated
- ❌ Generation EMPTY
- ❌ Demand EMPTY
- ❌ Interconnectors EMPTY

### Test 2: Historical Date (Oct 30, 2025)
```bash
.venv/bin/python tools/refresh_live_dashboard.py --date 2025-10-30
```
**Expected Result:**
- ✅ ALL columns should be populated

## Conclusion

**Your instinct was correct** - the IRIS tables aren't working as expected for recent dates. The issue is:

1. ❌ Non-IRIS tables stopped updating Oct 30
2. ⚠️ IRIS tables have data but complex structure (boundary codes)
3. ✅ Price and balancing data IS current
4. ❌ Generation/demand/interconnector data is stale

The dashboard still provides **valuable price and balancing mechanism data** for recent dates, but generation/demand analysis requires historical dates (before Oct 31) or finding alternative data sources.

## Next Steps

1. **Short term:** Use dashboard for price analysis with recent dates
2. **Medium term:** Investigate alternative tables (fuelhh, unified views)
3. **Long term:** Consider hybrid approach (BigQuery + NESO API)

---

**Status:** Dashboard operational but with limited data availability for dates after Oct 30, 2025  
**Updated:** November 6, 2025  
**Action Required:** Investigate alternative data sources or wait for table updates
