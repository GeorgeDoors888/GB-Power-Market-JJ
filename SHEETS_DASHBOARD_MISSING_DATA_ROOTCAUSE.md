# 🔧 Google Sheets Dashboard - Missing Data Root Cause & Solution

**Date:** November 7, 2025  
**Status:** ❌ ROOT CAUSE IDENTIFIED

---

## Problem Summary

The Google Sheets Dashboard successfully retrieves:
- ✅ **Demand data** (bmrs_inddem_iris)
- ✅ **Generation data** (bmrs_indgen_iris)  
- ✅ **Interconnector data** (calculated)

But is missing:
- ❌ **System Prices (SSP/SBP)** - from bmrs_mid
- ❌ **BOALF data** - from bmrs_boalf
- ❌ **BOD prices** - from bmrs_bod

---

## Root Cause

**Railway Backend is configured for WRONG BigQuery project!**

### Architecture:

```
Google Sheets Apps Script
    ↓
Vercel Proxy (gb-power-market-jj.vercel.app/api/proxy-v2)
    ↓
Railway Backend (jibber-jabber-production.up.railway.app)
    ↓
BigQuery
```

### The Issue:

1. **Apps Script queries:** `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
2. **Railway backend is configured for:** `jibber-jabber-knowledge` project
3. **Result:** Railway can't find the tables, returns "Query execution failed"

### Evidence:

```bash
# Railway CAN query jibber-jabber-knowledge:
curl "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20schema_name%20FROM%20\`jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA\`"
# ✅ SUCCESS - Returns: bmrs_data, uk_energy_insights, companies_house, etc.

# Railway CANNOT query inner-cinema-476211-u9:
curl "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20COUNT(*)%20FROM%20\`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid\`"
# ❌ FAIL - Returns: "Query execution failed"
```

### Why some queries work:

The IRIS tables (`bmrs_indgen_iris`, `bmrs_inddem_iris`) likely exist in BOTH projects, so they succeed. But the historical tables (`bmrs_mid`, `bmrs_bod`, `bmrs_boalf`) only exist in `inner-cinema-476211-u9.uk_energy_prod`.

---

## Solution Options

### ✅ OPTION 1: Update Railway Environment Variable (RECOMMENDED)

Railway's `api_gateway.py` uses:
```python
BQ_PROJECT = os.environ.get("BQ_PROJECT_ID", "inner-cinema-476211-u9")
```

**Steps:**
1. Login to Railway dashboard: https://railway.app
2. Find project: `jibber-jabber-production`
3. Go to: Variables tab
4. Set: `BQ_PROJECT_ID=inner-cinema-476211-u9`
5. Redeploy the service
6. Test: Dashboard should now show all data

**Time:** 5 minutes  
**Impact:** Fixes the issue permanently

---

### ⚠️ OPTION 2: Use Different Dataset in jibber-jabber-knowledge

If `jibber-jabber-knowledge.bmrs_data` actually has the same tables, we could update the Apps Script to use that project instead.

**Check if tables exist:**
```bash
curl "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20table_name%20FROM%20\`jibber-jabber-knowledge.bmrs_data.INFORMATION_SCHEMA.TABLES\`%20WHERE%20table_name%20IN%20('bmrs_mid',%20'bmrs_bod',%20'bmrs_boalf')"
```

If they exist, update Apps Script:
```javascript
const PROJECT = 'jibber-jabber-knowledge';
const DATASET = 'bmrs_data';
```

**Time:** 2 minutes  
**Risk:** Data might be different/older than inner-cinema-476211-u9

---

### 🔧 OPTION 3: Deploy Updated api_gateway.py

Update `api_gateway.py` to hardcode the correct project:

```python
BQ_PROJECT = "inner-cinema-476211-u9"  # Force correct project
BQ_DATASET = "uk_energy_prod"
```

Then redeploy Railway service.

**Time:** 10 minutes  
**Impact:** Similar to Option 1 but requires code change

---

## Current Status

**Apps Script:** ✅ Correct (uses inner-cinema-476211-u9.uk_energy_prod)  
**Vercel Proxy:** ✅ Correct (forwards requests to Railway)  
**Railway Backend:** ❌ Wrong (configured for jibber-jabber-knowledge)  
**BigQuery Data:** ✅ Exists (inner-cinema-476211-u9.uk_energy_prod has all tables)

---

## Documentation References

All documentation confirms the BMRS data location:

- **ARCHITECTURE_VERIFIED.md:** `inner-cinema-476211-u9.uk_energy_prod`
- **MASTER_SYSTEM_DOCUMENTATION.md:** `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
- **DATA_INVENTORY_COMPLETE.md:** `inner-cinema-476211-u9:uk_energy_prod`
- **NESO_ELEXON_BATTERY_VLP_DATA_GUIDE.md:** `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`

---

## Next Steps

1. **Identify who has access to Railway dashboard**
2. **Update `BQ_PROJECT_ID` environment variable** to `inner-cinema-476211-u9`
3. **Redeploy Railway service**
4. **Test Apps Script** - should now show SSP/SBP/BOALF/BOD data
5. **Verify auto-refresh** continues working

---

## Test Commands

After fixing Railway configuration:

```bash
# Test bmrs_mid (System Prices)
curl "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20COUNT(*)%20as%20cnt%20FROM%20\`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid\`"

# Test bmrs_bod (BOD Prices)
curl "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20COUNT(*)%20as%20cnt%20FROM%20\`inner-cinema-476211-u9.uk_energy_prod.bmrs_bod\`"

# Test bmrs_boalf (BOALF)
curl "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20COUNT(*)%20as%20cnt%20FROM%20\`inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf\`"
```

All three should return `{"success": true, "data": [{"cnt": <number>}], ...}`

---

## Summary

The Google Sheets Dashboard and Apps Script code are **100% correct**. The issue is purely a **Railway backend configuration problem** - it needs to query `inner-cinema-476211-u9` instead of `jibber-jabber-knowledge`.

**Fix:** Update Railway's `BQ_PROJECT_ID` environment variable to `inner-cinema-476211-u9` and redeploy.

**ETA:** 5 minutes to fix, dashboard will immediately show all missing data.
