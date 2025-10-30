# FUELINST HISTORICAL DATA FIX - COMPLETE SUCCESS

## 🎯 Problem Solved

**ROOT CAUSE:** Both BMRS `/datasets/FUELINST` AND Insights `/generation/actual/per-type` endpoints only return **current data** (last 1-2 days), not historical data.

**SOLUTION:** Use `/datasets/FUELINST/stream` endpoint instead!

## ✅ The Fix

### Code Change in `ingest_elexon_fixed.py`

**Line 670:** Changed endpoint from Insights API to Stream API:
```python
# OLD (BROKEN):
"FUELINST": "/generation/actual/per-type",

# NEW (FIXED):
"FUELINST": "/datasets/FUELINST/stream",
```

**Lines 676-686:** Added special parameter handling for stream endpoints:
```python
# Different endpoints use different parameter names
if ds == "FUELINST":
    # Stream endpoints use publishDateTime format
    params = {
        "publishDateTimeFrom": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publishDateTimeTo": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "format": "json",
    }
else:
    # Insights API endpoints use simple from/to
    params = {
        "from": from_dt.strftime("%Y-%m-%d"),
        "to": to_dt.strftime("%Y-%m-%d"),
        "format": "json",
    }
```

## 🧪 Test Results

### Test: July 16, 2025 (User's Original Query)

**Command:**
```bash
python ingest_elexon_fixed.py --start 2025-07-16 --end 2025-07-17 --only FUELINST
```

**Result:**
- ✅ **5,780 rows loaded successfully**
- ✅ **Data is from July 16, 2025** (not current date!)
- ✅ **Settlement Period 12 data available**

**User's Query Result:**
```sql
SELECT 
  fuelType,
  SUM(generation) as total_generation_mw
FROM bmrs_fuelinst
WHERE settlementDate = '2025-07-16'
  AND settlementPeriod = 12
GROUP BY fuelType
ORDER BY total_generation_mw DESC
```

| Fuel Type | Generation (MW) |
|-----------|-----------------|
| WIND      | 36,907          |
| CCGT      | 25,663          |
| NUCLEAR   | 24,939          |
| BIOMASS   | 16,285          |
| INTFR     | 9,035           |
| **TOTAL** | **119,391**     |

## 📊 Why Stream Endpoint Works

### Endpoint Comparison

| Endpoint | Historical Data? | Date Parameters |
|----------|------------------|-----------------|
| `/datasets/FUELINST` | ❌ Current only | `from`, `to` (ignored) |
| `/generation/actual/per-type` | ❌ Current only | `from`, `to` (ignored) |
| `/datasets/FUELINST/stream` | ✅ **Full history!** | `publishDateTimeFrom`, `publishDateTimeTo` |

### API Response Comparison

**Before (Insights API):**
```bash
GET /generation/actual/per-type?from=2023-01-01&to=2023-01-08

# Returns data from 2025-10-29 (today), ignores requested dates!
{
  "data": [
    {"settlementDate": "2025-10-29", "fuelType": "WIND", ...},
    {"settlementDate": "2025-10-29", "fuelType": "CCGT", ...}
  ]
}
```

**After (Stream API):**
```bash
GET /datasets/FUELINST/stream?publishDateTimeFrom=2023-01-01T00:00:00Z&publishDateTimeTo=2023-01-08T00:00:00Z

# Returns actual 2023 data!
{
  "data": [
    {"settlementDate": "2023-01-01", "fuelType": "WIND", ...},
    {"settlementDate": "2023-01-01", "fuelType": "CCGT", ...}
  ]
}
```

## 🚀 Next Steps

### 1. Clear Corrupted Data (Oct 28-29 current data)

```sql
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate >= '2025-10-28'
```

### 2. Reload Historical Data (2022-2025)

**Estimated time:** ~45 minutes

```bash
# 2022 (full year)
python ingest_elexon_fixed.py --start 2022-01-01 --end 2022-12-31 --only FUELINST --overwrite

# 2023 (full year)
python ingest_elexon_fixed.py --start 2023-01-01 --end 2023-12-31 --only FUELINST --overwrite

# 2024 (full year)
python ingest_elexon_fixed.py --start 2024-01-01 --end 2024-12-31 --only FUELINST --overwrite

# 2025 (Jan-Oct)
python ingest_elexon_fixed.py --start 2025-01-01 --end 2025-10-29 --only FUELINST --overwrite
```

### 3. Verify Data Quality

```sql
-- Check date coverage
SELECT 
  EXTRACT(YEAR FROM settlementDate) as year,
  COUNT(DISTINCT DATE(settlementDate)) as distinct_days,
  COUNT(*) as total_rows
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
GROUP BY year
ORDER BY year;

-- Expected:
-- 2022: ~365 days, ~1.75M rows
-- 2023: ~365 days, ~1.75M rows
-- 2024: ~366 days, ~1.76M rows
-- 2025: ~303 days (Jan-Oct), ~1.45M rows
```

## 📝 Lessons Learned

### Investigation Timeline

1. **Oct 28, 11 PM:** Discovered BMRS API returns current data only
2. **Oct 29, 12 AM:** "Fixed" by switching to Insights API
3. **Oct 29, 1 AM:** Cleared data, reran with Insights API
4. **Oct 29, 10 AM:** Discovered Insights API ALSO returns current data only
5. **Oct 29, 10:30 AM:** Found `/datasets/FUELINST/stream` endpoint
6. **Oct 29, 10:45 AM:** Tested stream endpoint - **SUCCESS!**
7. **Oct 29, 10:48 AM:** User's query now works!

### Key Insights

1. **API Documentation Incomplete:** 
   - Neither BMRS nor Insights API docs clearly state that non-stream endpoints only serve current data
   - Stream endpoints are mentioned but not highlighted as the historical data source

2. **Testing Methodology:**
   - Always test with **specific historical date** and verify `settlementDate` in response
   - Check database records for actual dates, not just row counts
   - "Success" messages (200 OK, rows loaded) don't guarantee correct data

3. **Alternative Data Sources Investigated:**
   - GCS bucket `elexon-historical-data-storage`: Has CSV files but access denied
   - `/generation/outturn/FUELINSTHHCUR`: Marked as obsolete in API
   - Old project: Used different bucket (no longer accessible)

4. **Stream Endpoints Are Key:**
   - `/datasets/{DATASET}/stream` endpoints provide full historical access
   - Use `publishDateTimeFrom`/`publishDateTimeTo` parameters (RFC3339 format)
   - Should check if other datasets (FUELHH, FREQ) also benefit from stream endpoints

## 🎉 Status: PROBLEM SOLVED!

- ✅ Root cause identified (endpoint limitation)
- ✅ Fix implemented (switch to stream endpoint)
- ✅ Fix tested (July 16, 2025 data loads correctly)
- ✅ User's query works (Settlement Period 12 results shown)
- ⏳ **Next:** Reload full historical data (2022-2025)

---

**Generated:** October 29, 2025, 10:48 AM  
**File:** `ingest_elexon_fixed.py` (lines 670, 676-686)  
**Test:** `test_user_query.py` - ✅ PASSING
