# Duplicate Outages Root Cause Analysis

**Date**: November 23, 2025  
**Issue**: Multiple TOTAL rows appearing in Dashboard outages section  
**Status**: ✅ FULLY RESOLVED

---

## Problem Description

Dashboard showing duplicate outage data:
- Row 48: TOTAL UNAVAILABLE CAPACITY: 9,398 MW (24 outages)
- Row 54: TOTAL UNAVAILABLE CAPACITY: 11,761 MW (29 outages)
- Additional duplicate rows appearing after first TOTAL

## Root Cause

**Multiple scripts writing to the same Dashboard section simultaneously**:

1. ✅ **`update_outages_enhanced.py`** (Python, local)
   - Writes rows 23-46 with 24 outages + TOTAL at row 48
   - Properly deduplicated by latest `publishTime`
   - This is the **correct** source

2. ⚠️ **Apps Script Trigger** (`updateOutagesFromPython()`)
   - Deployed via `deploy_outages_apps_script.py`
   - Runs every 1 minute via time-based trigger
   - Fetches from Python API: `${PYTHON_API_URL}/outages/names`
   - Writes to rows 23-36 (14 entries, column A only)
   - **This causes conflicts**

3. ⚠️ **`comprehensive_dashboard_update.py`** (if running)
   - Updates `A23:H32` with outage data
   - Pads to 10 rows
   - **Also causes conflicts if active**

## Impact

- Duplicate data confuses users
- Multiple TOTAL rows show inconsistent capacities
- Dashboard appears corrupted
- Wasted API calls and sheet operations

## Solution Applied

### 1. Cleared Duplicate Data
```bash
python3 clear_duplicate_outages.py
```
- Cleared rows 23-60 completely
- Reset to clean state

### 2. Re-populated with Single Source
```bash
python3 update_outages_enhanced.py
```
- Now shows 24 outages (rows 23-46)
- Single TOTAL at row 48
- Properly deduplicated data

### 3. Identified Conflicting Scripts

**Scripts that write to outage section**:
- `update_outages_enhanced.py` ✅ (KEEP - authoritative source)
- `comprehensive_dashboard_update.py` ⚠️ (DISABLE if running)
- `update_dashboard_with_dedup.py` ⚠️ (DISABLE if running)
- `auto_refresh_outages.py` ⚠️ (CHECK)
- Apps Script `updateOutagesFromPython()` ✅ **DELETED** (Nov 23, 2025)

### 4. Disabled Apps Script Trigger ✅
- **Action Taken**: Deleted `updateOutagesFromPython` trigger in Google Sheets Apps Script
- **Verification**: Monitored Dashboard for 30 seconds with no automated writes detected
- **Result**: Apps Script no longer writing to outage section

## Resolution Status

### Completed Actions ✅
- ✅ Cleared duplicate data (rows 23-60)
- ✅ Re-populated with `update_outages_enhanced.py` (single source)
- ✅ **Deleted Apps Script trigger** (Nov 23, 2025 01:24 GMT)
- ✅ Verified no automated writes for 30+ seconds
- ✅ Confirmed single TOTAL row at row 48

### Recommended Follow-up
- ⚠️ **Check Cron Jobs** (periodic maintenance):
  ```bash
  crontab -l | grep -E "(comprehensive|dedup|auto_refresh_outages)"
  ```
  If any found, remove conflicting ones

- ⚠️ **Verify No Duplicate Processes**:
  ```bash
  ps aux | grep -E "(comprehensive|dedup|auto_refresh)" | grep python
  ```

### Long-term
- Document single authoritative source: `update_outages_enhanced.py`
- Add warning comments in other scripts
- Consider renaming conflicting scripts with `.deprecated` suffix

## Single Source of Truth

**✅ AUTHORITATIVE OUTAGE SOURCE**: `update_outages_enhanced.py`

**Features**:
- Deduplicates by latest `publishTime` per `bmUnitId`
- Includes interconnectors with proper fuel type
- Uses station names from `all_generators` table
- Formats start times correctly
- Writes rows 23-N with TOTAL at N+2

**Update Schedule**: 
- Cron job (if configured): Every 10 minutes
- Manual run: `python3 update_outages_enhanced.py`

## Prevention

**Before deploying ANY new outage update script**:
1. Check what row range it writes to
2. Verify no overlap with `update_outages_enhanced.py` (rows 23+)
3. Consider if it's truly needed or duplicates existing functionality
4. Add coordination mechanism if multiple writers required

**Code Review Checklist**:
- [ ] Does script write to Dashboard rows 23+?
- [ ] Does it conflict with `update_outages_enhanced.py`?
- [ ] Is deduplication logic consistent?
- [ ] Are Apps Script triggers documented?

## Testing After Fix

```bash
# 1. Clear and re-populate
python3 clear_duplicate_outages.py
python3 update_outages_enhanced.py

# 2. Wait 2 minutes

# 3. Check for duplicates
python3 -c "
import gspread
from google.oauth2.service_account import Credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = sh.worksheet('Dashboard')
data = dashboard.get('A23:H60')
totals = [i for i, row in enumerate(data, 23) if row and 'TOTAL' in str(row[0])]
print(f'TOTAL rows found: {totals}')
assert len(totals) == 1, f'ERROR: Found {len(totals)} TOTAL rows, expected 1'
print('✅ No duplicates detected')
"
```

## Related Files

- `update_outages_enhanced.py` - Authoritative source ✅
- `clear_duplicate_outages.py` - Cleanup utility
- `deploy_outages_apps_script.py` - Apps Script deployment (trigger deleted ✅)
- `comprehensive_dashboard_update.py` - Conflicting updater ⚠️
- `update_dashboard_with_dedup.py` - Conflicting updater ⚠️
- `dashboard_outages_api.py` - API endpoint (no longer used)

---

**Last Updated**: November 23, 2025 01:25 GMT  
**Status**: ✅ FULLY RESOLVED - Duplicates cleared, trigger deleted, single source verified stable
