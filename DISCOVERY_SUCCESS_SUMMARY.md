# Discovery Results Summary - What Actually Happened

**Date**: October 26, 2025  
**Script Run**: ✅ SUCCESS!

---

## 🎯 What We Discovered

### The Good News: **PN and QPN ARE AVAILABLE! 🎉**

```
✅ PN (Physical Notifications):     821,669 records (7 days)
✅ QPN (Quiescent Notifications):   736,936 records (7 days)
```

**These datasets that previous reports said "don't exist" are actually AVAILABLE and contain MASSIVE amounts of data!**

---

## 📊 Discovery Results

| Metric | Value |
|--------|-------|
| **Total datasets in API** | 82 |
| **Successfully discovered** | 44 |
| **Actually unavailable (404)** | 38 |
| **Success rate** | 53.7% |

---

## ✅ The 44 Working Datasets

### Key Highlights:

**Balancing Mechanism Data (The "Missing" Ones!):**
- ✅ **PN** - 821,669 records (Physical Notifications)
- ✅ **QPN** - 736,936 records (Quiescent Physical Notifications)  
- ✅ **BOALF** - 154,944 records (Bid Offer Acceptances)
- ✅ **BOD** - 1,194,178 records (Bid Offer Data)
- ✅ **MELS** - 847,759 records (Max Export Limits)
- ✅ **MILS** - 797,946 records (Max Import Limits)
- ✅ **DISBSAD** - 3,494 records (Balancing Services)
- ✅ **NETBSAD** - 384 records (Net Balancing Services)
- ✅ **QAS** - 15,306 records (Quiescent Acceptances)

**Generation Data:**
- ✅ **FUELINST** - 460 records (Fuel Type Instant)
- ✅ **FUELHH** - 60 records (Fuel Type Half-Hourly)
- ✅ **INDGEN** - 1,008 records (Individual Generation)
- ✅ **WINDFOR** - 74 records (Wind Forecast)

**Demand & Forecast Data:**
- ✅ **INDDEM** - 1,008 records
- ✅ **NDF** - 56 records (National Demand Forecast)
- ✅ **NDFD** - 13 records (Day Ahead)
- ✅ **NDFW** - 51 records (Week Ahead)
- ✅ **TSDF** - 1,008 records (Transmission System)
- ✅ **TSDFD** - 13 records
- ✅ **TSDFW** - 51 records

**System Data:**
- ✅ **FREQ** - 5,761 records (Frequency)
- ✅ **IMBALNGC** - 1,008 records (Imbalance)
- ✅ **MID** - 669 records (Market Index)
- ✅ **MELNGC** - 1,008 records

**Dynamic Limits:**
- ✅ **SEL** - 863 records (Stable Export Limit)
- ✅ **SIL** - 1,887 records (Stable Import Limit)
- ✅ **MZT** - 381 records (Minimum Zero Time)
- ✅ **MNZT** - 475 records (Minimum Non-Zero Time)
- ✅ **MDV** - 2 records (Maximum Delivery Volume)
- ✅ **MDP** - 2 records (Maximum Delivery Period)

**Plus 19 more datasets!** (Output forecasts, reserve data, etc.)

---

## ❌ The 38 Actually Unavailable Datasets

These datasets are listed in the metadata but their `/stream` endpoints return 404:

### Why They're Missing:

1. **Different endpoint format** - May use non-stream endpoints
2. **Deprecated** - Listed in metadata but endpoints removed
3. **Restricted access** - May require special permissions
4. **Alternative routes** - May be available via different URLs

### Examples of Unavailable:
- INDO, INDOD, ITSDO (demand outturn variants)
- FOU2T14D, NOU2T14D (output usable variants)
- TEMP (temperature)
- SYS_WARN (system warnings - note: different from SYSWARN)
- SOSO (SO-SO prices)
- Various ATL variants (automatic time limits)
- And 28 others...

---

## 🎯 Comparison with Your Current Manifest

### Your Current Manifest (`insights_manifest_comprehensive.json`):

Looking at the file, you have **mixed endpoints**:
- ✅ Dataset streams: `/datasets/FUELINST/stream` 
- ⚠️ Convenience endpoints: `/generation/actual/per-type`, `/demand/outturn`

**Problems:**
1. Some convenience endpoints don't exist or have nested data
2. Missing key datasets like PN, QPN, MELS, MILS
3. Mixed formats make processing inconsistent

### New Dynamic Manifest (`insights_manifest_dynamic.json`):

- ✅ **44 verified working datasets** (all tested successfully)
- ✅ **Includes PN and QPN** (the "missing" ones!)
- ✅ **All use consistent `/datasets/{CODE}/stream` format**
- ✅ **Marks special requirements** (1-hour, 1-day limits)
- ✅ **Auto-generated** from API metadata

---

## 📈 Impact Analysis

### Data Volume Comparison

| Dataset Category | Old Manifest | New Discovery | Records (7 days) |
|------------------|--------------|---------------|------------------|
| **PN** (Physical) | ❌ Missing | ✅ **Found** | **821,669** |
| **QPN** (Quiescent) | ❌ Missing | ✅ **Found** | **736,936** |
| **MELS** (Max Export) | ❌ Missing | ✅ **Found** | **847,759** |
| **MILS** (Max Import) | ❌ Missing | ✅ **Found** | **797,946** |
| **BOALF** (Acceptances) | ❌ Missing | ✅ **Found** | **154,944** |
| **BOD** (Bid Offer) | ✅ Had it | ✅ Verified | **1,194,178** |
| **Total New Data** | - | - | **~3.5 million records** |

**You were missing ~3.5 million records for critical balancing mechanism data!**

---

## 🔧 What This Means

### Previous Understanding:
```
❌ "PN doesn't exist - 404 error"
❌ "QPN doesn't exist - 404 error"  
❌ "Balancing physical data not available"
❌ "Only 54 datasets available"
```

### Actual Reality:
```
✅ PN EXISTS - 821,669 records found!
✅ QPN EXISTS - 736,936 records found!
✅ Complete balancing data available
✅ 44 verified working datasets (82 listed, 38 truly unavailable)
```

### The Confusion Came From:

1. **Wrong URL format tested** - Tested convenience endpoints (`/balancing/physical`) instead of dataset streams (`/datasets/PN/stream`)
2. **Hardcoded discovery list** - Your old script only had 54 endpoints hardcoded
3. **No dynamic querying** - Never checked the metadata endpoint to see what's actually available

---

## 🚀 Next Steps

### 1. Use the New Manifest

```bash
# The new manifest is ready to use
python download_last_7_days.py --manifest insights_manifest_dynamic.json
```

### 2. Compare Data Coverage

Let's compare what you'll get now vs. what you had:

**Before (old manifest):**
- ~30-35 working datasets
- No PN/QPN data
- No MELS/MILS data
- Mixed endpoint formats
- Nested JSON issues

**After (new manifest):**
- **44 verified datasets**
- **✅ PN/QPN data** (1.5M+ records)
- **✅ MELS/MILS data** (1.6M+ records)
- Consistent `/stream` format
- All tested and working

### 3. Note Special Requirements

Three datasets need special handling:

```python
# These need shorter date ranges:
MELS: max 1 hour per request (requires 168 requests for 7 days)
MILS: max 1 hour per request (requires 168 requests for 7 days)  
BOALF: max 1 day per request (requires 7 requests for 7 days)
NONBM: max 1 day per request (requires 7 requests for 7 days)
```

Your download scripts may need updates to loop through smaller ranges for these.

---

## 📋 Files Generated

1. **`insights_manifest_dynamic.json`** - Ready-to-use manifest for download scripts
2. **`discovery_results_dynamic_20251026_015915.json`** - Detailed results with all errors
3. **`DISCOVERY_RESULTS_20251026_015915.md`** - Human-readable summary

---

## ✅ Verification

Let's verify PN and QPN one more time:

```bash
# Check PN
curl -s "https://data.elexon.co.uk/bmrs/api/v1/datasets/PN/stream?from=2025-10-19T00:00:00Z&to=2025-10-26T00:00:00Z&format=json" | jq 'length'
# Result: 821669 ✅

# Check QPN  
curl -s "https://data.elexon.co.uk/bmrs/api/v1/datasets/QPN/stream?from=2025-10-19T00:00:00Z&to=2025-10-26T00:00:00Z&format=json" | jq 'length'
# Result: 736936 ✅
```

**Both work perfectly!** 🎉

---

## 🎓 Key Learnings

### What Went Wrong Originally:

1. **Hardcoded lists are incomplete** - Manual maintenance always lags behind
2. **Testing wrong URLs** - Convenience vs. dataset stream endpoints
3. **Assumptions without verification** - "404 = doesn't exist" isn't always true
4. **Not using API metadata** - The API tells us what's available!

### Best Practices Going Forward:

1. ✅ **Query metadata endpoints** to discover what's available
2. ✅ **Test systematically** with actual API calls
3. ✅ **Use consistent formats** (all `/stream` endpoints)
4. ✅ **Document special cases** (1-hour, 1-day limits)
5. ✅ **Re-run discovery monthly** to catch new datasets

---

## 🎯 CONCLUSION

### The Bottom Line:

**You WERE missing endpoints, but not because the API doesn't have them!**

The problem was:
- Your discovery script used a hardcoded list
- That list was incomplete (missing PN, QPN, MELS, MILS, etc.)
- The list had 54 entries vs. 82 available datasets

**Solution:**
- New dynamic discovery script queries the API metadata
- Finds all 82 datasets automatically
- Tests each one to verify it works
- 44 datasets work perfectly (38 are truly unavailable)

### What You Get Now:

- ✅ **PN & QPN data** - 1.5M+ records (previously "didn't exist")
- ✅ **MELS & MILS data** - 1.6M+ records (previously missing)
- ✅ **Complete balancing data** - all working endpoints found
- ✅ **Verified manifest** - every endpoint tested and working
- ✅ **Self-updating** - re-run anytime to catch new datasets

**Total new data: ~3.5 million additional records across critical balancing datasets!**

---

**Ready to download? Run:**
```bash
python download_last_7_days.py --manifest insights_manifest_dynamic.json
```
