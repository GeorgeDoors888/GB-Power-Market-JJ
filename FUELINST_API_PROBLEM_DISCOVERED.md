# FUELINST API Problem - Root Cause Discovered

**Date:** 29 October 2025, 00:40 AM
**Status:** 🚨 CRITICAL BUG FOUND

## 🔍 The Discovery

After investigating why FUELINST repairs "completed successfully" but contain no actual data, I found:

### What Actually Happened:

1. **Script requested correct dates:** `2023-01-01` to `2023-01-08`, etc.
2. **API returned HTTP 200:** No errors reported
3. **Script logged "Successfully loaded":** 294,320 rows for 2023
4. **BigQuery contains the data:** 843,640 rows total in `bmrs_fuelinst`
5. **BUT: ALL data is from 2025-10-28!** ⚠️

### The Proof:

```sql
SELECT 
  _window_from_utc,
  COUNT(*) as row_count,
  MIN(settlementDate) as first_date,
  MAX(settlementDate) as last_date
FROM `bmrs_fuelinst`
GROUP BY _window_from_utc
ORDER BY _window_from_utc
LIMIT 5
```

**Result:**
```
2023-01-01T00:00:00+00:00: 5,660 rows (2025-10-28 to 2025-10-28)  ⚠️
2023-01-08T00:00:00+00:00: 5,660 rows (2025-10-28 to 2025-10-28)  ⚠️
2023-01-15T00:00:00+00:00: 5,660 rows (2025-10-28 to 2025-10-28)  ⚠️
2023-01-22T00:00:00+00:00: 5,660 rows (2025-10-28 to 2025-10-28)  ⚠️
```

The window metadata says "2023-01-01" but the actual data is from TODAY!

## 🎯 Root Cause

**The BMRS `/datasets/FUELINST` endpoint only returns CURRENT data (last 1-2 days), regardless of the date range requested!**

### Evidence:

1. **Logs show correct API request:**
   ```
   Fetching BMRS dataset=FUELINST from=2023-01-01 00:00:00+00:00 to=2023-01-08 00:00:00+00:00
   ```

2. **API returns 200 OK with current data**
   - No error messages
   - Returns ~5,660 rows per week
   - But ALL rows are from 2025-10-28

3. **This is a BMRS API limitation:**
   - BMRS `/datasets/FUELINST` = Live/current data only (snapshot)
   - Insights `/generation/actual/per-type` = Historical data ✅

## ✅ The Solution

**Switch to Insights API for historical fuel generation data:**

### Current (WRONG):
```python
# Uses BMRS datasets API - only returns current data!
url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST"
params = {"from": "2023-01-01T00:00:00Z", "to": "2023-01-08T00:00:00Z"}
```

### Correct (USE THIS):
```python
# Uses Insights API - has full historical data!
url = "https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type"
params = {"from": "2023-01-01", "to": "2023-01-08", "format": "json"}
```

## 📋 Required Changes

### 1. Update `ingest_elexon_fixed.py`

Add FUELINST to the Insights API datasets list (similar to WIND_SOLAR_GEN):

```python
# Around line 660, update the Insights API handling:
if ds in ("WIND_SOLAR_GEN", "DEMAND_FORECAST", "SURPLUS_MARGIN", "FUELINST", "FUELHH"):
    insights_paths = {
        "WIND_SOLAR_GEN": "/generation/actual/per-type/wind-and-solar",
        "FUELINST": "/generation/actual/per-type",  # ← ADD THIS
        "FUELHH": "/generation/actual/per-type/day-total",  # ← ADD THIS
        "DEMAND_FORECAST": "/forecast/demand/total/day-ahead",
        "SURPLUS_MARGIN": "/forecast/surplus/daily",
    }
```

### 2. Clear Bad Data

```sql
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst` WHERE TRUE;
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq` WHERE TRUE;
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelhh` WHERE TRUE;
```

### 3. Rerun Repairs

After code changes, rerun:
```bash
.venv/bin/python ingest_elexon_fixed.py --start 2023-01-01 --end 2023-12-31 \
  --only FUELINST,FUELHH --overwrite
```

Note: FREQ might still use BMRS API if it's truly a live-only metric.

## 🚨 Impact

**ALL historical FUELINST data collection has been failing silently:**

- ✅ 2022: Has BOD and other datasets, but FUELINST is wrong
- ❌ 2023: FUELINST repair loaded Oct 28, 2025 data instead of 2023 data
- ❌ 2024: FUELINST repair loaded Oct 28, 2025 data instead of 2024 data
- ❌ 2025 Jan-Oct: FUELINST repair loaded Oct 28, 2025 data (duplicates!)

**Current state:**
- 843,640 rows in `bmrs_fuelinst` table
- ALL 843,640 rows are from 2025-10-28
- Zero actual historical data despite logs saying "Success"

## 📊 Verification After Fix

After implementing the solution, verify:

```sql
-- Should show data spread across years, not just one date
SELECT 
  EXTRACT(YEAR FROM settlementDate) as year,
  COUNT(*) as row_count,
  MIN(settlementDate) as first_date,
  MAX(settlementDate) as last_date
FROM `bmrs_fuelinst`
GROUP BY year
ORDER BY year
```

**Expected:**
```
2022: X rows (2022-01-01 to 2022-12-31)
2023: X rows (2023-01-01 to 2023-12-31)
2024: X rows (2024-01-01 to 2024-12-31)
2025: X rows (2025-01-01 to 2025-10-28)
```

## 🎓 Lessons Learned

1. **"Successfully loaded" doesn't mean "correct data loaded"**
   - Need to verify data contents, not just HTTP success
   
2. **BMRS vs Insights APIs serve different purposes:**
   - BMRS `/datasets/X` = Live snapshots (current data only)
   - Insights `/generation/actual/...` = Historical archives
   
3. **Always verify data after loading:**
   - Check date ranges match expectations
   - Don't trust "Success" messages alone
   
4. **Window metadata can lie:**
   - Window says "2023-01-01" but data is "2025-10-28"
   - Metadata tracks request dates, not actual data dates

## ⏭️ Next Steps

1. **Code fix:** Update `ingest_elexon_fixed.py` to use Insights API for FUELINST
2. **Clear bad data:** Delete all current FUELINST/FUELHH/FREQ data
3. **Rerun repairs:** Load 2022-2025 FUELINST using correct API
4. **Verify:** Check that data spans full date ranges
5. **Test query:** User's original request for "July 16, 2025 Settlement Period 12"

**Estimated time:** 2-3 hours to fix code, clear data, and reload all years

---

**This discovery explains why FUELINST has been "completing successfully" but contains no useful data - we've been using an API endpoint that only serves live data, not historical archives!**
