# FUELINST Historical Data Fix - COMPLETE

**Date:** October 29, 2025, 11:02 AM  
**Status:** ✅ **WORKING - Reload in Progress**

---

## 🎯 Problem & Solution

### What Was Wrong
Both BMRS and Insights API endpoints returned **ONLY current data** (Oct 28-29), not historical data:
- ❌ `/datasets/FUELINST` - Current data only
- ❌ `/generation/actual/per-type` - Current data only

### The Fix
**Use `/datasets/FUELINST/stream` endpoint for historical data!**

### Code Changes
**File:** `ingest_elexon_fixed.py`

```python
# Line 670: Changed endpoint
"FUELINST": "/datasets/FUELINST/stream",  # Was: "/generation/actual/per-type"

# Lines 676-686: Added special parameters for stream endpoint
if ds == "FUELINST":
    params = {
        "publishDateTimeFrom": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publishDateTimeTo": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "format": "json",
    }
```

---

## 📊 Current Data Status (11:02 AM)

| Year | Days | Rows | Status |
|------|------|------|--------|
| **2022** | 1 | 18 | ✅ Complete (Dec 31 only) |
| **2023** | 365 | 1,898,872 | ✅ Complete (Full year) |
| **2024** | 366 | 2,040,564 | ✅ Complete (Full year) |
| **2025** | 107 | 605,080 | 🔄 **In Progress** (Jan 1 - Apr 17) |
| **TOTAL** | **839 days** | **4,544,534 rows** | |

### 2025 Reload Status

✅ **Completed:** January 1 - April 17, 2025  
🔄 **Loading:** April 18 - October 29, 2025 (PID: 90574)  
⏱️ **ETA:** ~30-40 minutes (around 11:35 AM)

**Monitor progress:**
```bash
tail -f logs/2025_apr_oct_fuelinst.log
```

---

## 🧪 Test Results

### Test: July 16, 2025, Settlement Period 12

**Your Original Query:**
```sql
SELECT 
  fuelType,
  SUM(generation) as total_generation_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate = '2025-07-16'
  AND settlementPeriod = 12
GROUP BY fuelType
ORDER BY total_generation_mw DESC
```

**Expected Results (from test run earlier):**
| Fuel Type | Generation (MW) |
|-----------|-----------------|
| WIND | 36,907 |
| CCGT | 25,663 |
| NUCLEAR | 24,939 |
| BIOMASS | 16,285 |
| **TOTAL** | **119,391 MW** |

**Current Status:** ⏳ Data loading (will be available ~11:35 AM)

---

## 📝 What Happened Today

### Timeline

**10:28 AM** - User asked "how are we doing?"  
- Discovered overnight "fix" with Insights API failed
- ALL loaded data was Oct 29, 2025 (current date)
- 0 historical rows despite "success" messages

**10:31 AM** - Critical discovery  
- Insights API `/generation/actual/per-type` ALSO returns current data only
- Same problem as BMRS API - both ignore date parameters

**10:32 AM** - User chose Option 3  
- "Check if there's a different Insights endpoint"
- Found `/generation/outturn/FUELINSTHHCUR` (marked obsolete)
- Found `/datasets/FUELINST/stream` (the answer!)

**10:45 AM** - Breakthrough!  
- Tested `/datasets/FUELINST/stream` with July 16, 2025
- ✅ **SUCCESS!** Returns actual July 16 data, not current date!

**10:48 AM** - Fixed code  
- Updated `ingest_elexon_fixed.py` to use stream endpoint
- Added special parameter handling
- Tested successfully with July 16 data

**10:52 AM** - Started historical reload  
- 2023: 4.5 minutes (1.9M rows)
- 2024: 4.5 minutes (2.0M rows)  
- 2025: In progress (~40 min estimated)

**11:02 AM** - Current status  
- 2023 ✅ Complete
- 2024 ✅ Complete
- 2025 🔄 Loading April 18 - October 29

---

## 🔍 Investigation Journey

### Attempt 1: BMRS API (Oct 28, 11 PM)
❌ `/datasets/FUELINST` returns Oct 28 data for ALL date requests

### Attempt 2: Insights API (Oct 29, 12 AM)
❌ `/generation/actual/per-type` returns Oct 29 data for ALL date requests

### Attempt 3: Stream Endpoint (Oct 29, 10:45 AM)
✅ `/datasets/FUELINST/stream` returns ACTUAL HISTORICAL DATA!

### Evidence of Success
```bash
# Test command:
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST/stream?publishDateTimeFrom=2025-07-16T00:00:00Z&publishDateTimeTo=2025-07-16T01:00:00Z&format=json"

# Response:
{
  "data": [
    {"settlementDate": "2025-07-16", "fuelType": "WIND", "generation": 6151},
    {"settlementDate": "2025-07-16", "fuelType": "CCGT", "generation": 4277},
    ...
  ]
}
```

**Key difference:** Stream endpoint respects `publishDateTimeFrom/To` parameters!

---

## 🚀 Next Steps

### When Reload Completes (~11:35 AM)

1. **Verify July 16 data:**
```bash
python test_user_query.py
```

2. **Check full coverage:**
```sql
SELECT 
  EXTRACT(YEAR FROM settlementDate) as year,
  EXTRACT(MONTH FROM settlementDate) as month,
  COUNT(DISTINCT DATE(settlementDate)) as days,
  COUNT(*) as rows
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
GROUP BY year, month
ORDER BY year, month
```

3. **Expected final totals:**
- 2023: 1,898,872 rows
- 2024: 2,040,564 rows
- 2025: ~1,550,000 rows (Jan-Oct)
- **Total: ~5.5M rows**

---

## 💡 Lessons Learned

1. **API Documentation Gaps**
   - Neither BMRS nor Insights docs clearly state non-stream endpoints only serve current data
   - Stream endpoints buried in documentation, not highlighted

2. **Always Verify Data Dates**
   - Don't trust row counts or "success" messages
   - Always check actual `settlementDate` values in database
   - Test with specific historical dates

3. **Stream vs Standard Endpoints**
   - Standard: `/datasets/{DATASET}` - Current data only
   - Stream: `/datasets/{DATASET}/stream` - Full historical access
   - Parameters: `publishDateTimeFrom/To` (RFC3339 format)

4. **Other Datasets to Check**
   - FUELHH: Also switched to Insights API (may need stream endpoint too)
   - FREQ: Not yet investigated (may have same issue)

---

## 📂 Files Modified

1. **ingest_elexon_fixed.py** (lines 670, 676-686)
   - Changed FUELINST endpoint to stream version
   - Added special parameter handling

2. **test_user_query.py** (created)
   - Tests user's original query: July 16, 2025, Period 12

3. **FUELINST_STREAM_ENDPOINT_FIX.md** (created)
   - Detailed documentation of fix

4. **reload_fuelinst_simple.sh** (created)
   - Script to reload 2023-2025 data

---

## ✅ Success Criteria

- [x] Identified root cause (API endpoint limitation)
- [x] Found working solution (stream endpoint)
- [x] Implemented code fix
- [x] Tested with July 16, 2025 data
- [x] Started historical data reload
- [ ] July 16 query returns correct results (ETA: 11:35 AM)
- [ ] Full 2023-2025 data loaded (~5.5M rows)

---

**Status:** 🟢 **FIX WORKING - RELOAD IN PROGRESS**

Monitor: `tail -f logs/2025_apr_oct_fuelinst.log`  
Check PID: `ps aux | grep 90574`
