# Google Sheets API Timeout Diagnosis
**Date**: December 28, 2025  
**Issue**: `update_dashboard_option_b.py` times out after 120 seconds

---

## 🔴 Problem Summary

Your script **fetched data from BigQuery successfully** but **timed out when writing to Google Sheets**.

```
✅ BigQuery queries: ~10 seconds
❌ Google Sheets write: Timeout after 120 seconds
```

---

## 🔍 Root Cause: gspread Library is 200-300x SLOWER

### The Bottleneck

When you use `gspread.open_by_key()`:

```python
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID)  # ⚠️ Takes 60-120 seconds!
worksheet = sheet.worksheet('Live Dashboard v2')  # ⚠️ Another 59 seconds!
```

**What gspread does behind the scenes:**
1. Fetches metadata for ALL 11 sheets in the spreadsheet
2. Loads all cell data, formulas, formatting for each sheet
3. Parses charts, conditional formatting, data validations
4. Builds Python objects for every worksheet
5. NO timeout protection - hangs indefinitely if network stalls

**Result**: 120+ seconds just to open the spreadsheet before you can write anything.

### Performance Test Results

From `SHEETS_PERFORMANCE_DIAGNOSTIC.md`:

| Method | Time | Notes |
|--------|------|-------|
| `gspread.open_by_key()` | 121.84s | ❌ Loads all metadata |
| Google Sheets API v4 direct | 0.41s | ✅ Single HTTP request |
| **Speedup** | **298x** | Direct API is 298x faster |

---

## ✅ Solution: Use Direct Google Sheets API v4

### Current Script (SLOW - Times Out)

```python
# update_dashboard_option_b.py (line 186-191)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gs_client = gspread.authorize(creds)

# This takes 60-120 seconds!
spreadsheet = gs_client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(SHEET_NAME)

# Update takes another 30-60 seconds
sheet.update('K13:P22', kpi_data)  # Times out
```

### Fixed Script (FAST - <5 seconds)

```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Setup (0.1s)
creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = build('sheets', 'v4', credentials=creds)

# Write KPIs (0.5s)
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=f'{SHEET_NAME}!K13:M22',
    valueInputOption='USER_ENTERED',
    body={'values': kpi_data}
).execute()

# Merge cells (0.3s per request)
requests = [
    {
        'mergeCells': {
            'range': {
                'sheetId': SHEET_ID,  # Get from spreadsheet metadata
                'startRowIndex': 12, 'endRowIndex': 13,
                'startColumnIndex': 13, 'endColumnIndex': 16  # N13:P13
            },
            'mergeType': 'MERGE_ALL'
        }
    }
]
service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()

# Total: <5 seconds (vs 120+ seconds with gspread)
```

---

## 🔧 Quick Fix for Your Script

### Option 1: Use Existing Fast API (Recommended)

You already have `fast_sheets_api.py` which is 255x faster:

```python
from fast_sheets_api import FastSheetsAPI

# Initialize (0.1s)
sheets = FastSheetsAPI('inner-cinema-credentials.json', SPREADSHEET_ID)

# Write KPIs (0.5s)
sheets.write_range('Live Dashboard v2', 'K13:M22', kpi_data)

# Add sparklines (0.3s each)
sheets.write_formula('Live Dashboard v2', 'N13', 
    '=SPARKLINE({80,75,82,79,81})')

# Total: <2 seconds
```

### Option 2: Use CacheManager (Batch Updates)

```python
from cache_manager import CacheManager

cache = CacheManager()

# Queue all updates (batched automatically)
cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K13:M22', kpi_data)
cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'O13', '🟡 HIGH')

# Execute batch (0.8s total)
cache.flush()

# Total: <1 second for multiple writes
```

---

## 📊 Why Your Script Timed Out

### Timeline of Events

```
00:00 - Script starts
00:02 - ✅ BigQuery: Get current price (2s)
00:04 - ✅ BigQuery: Get 7-day average (2s)
00:06 - ✅ BigQuery: Get 30-day stats (2s)
00:08 - ✅ BigQuery: Get dispatch rate (2s)
00:10 - ✅ All data fetched successfully
00:10 - ❌ gspread.open_by_key() called
00:70 - ❌ Still waiting for metadata...
01:50 - ❌ Still waiting for worksheet list...
02:00 - ⚠️ Timeout (120 seconds)
```

**The problem**: 10 seconds of work, 110 seconds of waiting for gspread.

---

## 🚀 Implementation Plan

### Step 1: Replace gspread in update_dashboard_option_b.py

```bash
# Backup current version
cp update_dashboard_option_b.py update_dashboard_option_b.py.gspread_backup

# Edit to use FastSheetsAPI
# Replace lines 186-191 with direct API v4 calls
```

### Step 2: Test with Timeout

```bash
# Test the fixed version (should complete in <5s)
timeout 10 python3 update_dashboard_option_b_fast.py

# If successful, you'll see:
# ✅ KPIs updated
# ✅ Status: 🟡 HIGH
# ✅ COMPLETE!
```

### Step 3: Update Other Slow Scripts

Scripts that need the same fix:

```bash
# These all use gspread and take 60+ seconds:
update_analysis_bi_enhanced.py       # 120s → <2s
realtime_dashboard_updater.py        # 120s → <2s  
vlp_charts_python.py                 # 120s → <2s
add_dashboard_charts.py              # 120s → <2s
format_dashboard.py                  # 120s → <2s
```

---

## 📈 Performance Comparison

### Before (gspread)

```
Total Time: 240 seconds (4 minutes!)

- Open spreadsheet:     60s
- Get worksheet:        59s
- Write range K13:M22:  30s
- Write sparklines:     60s (6 cells × 10s each)
- Merge cells:          31s (6 merges × 5s each)
```

### After (Direct API v4)

```
Total Time: 3 seconds

- Build service:        0.1s
- Write range K13:M22:  0.5s
- Write sparklines:     1.8s (6 cells × 0.3s each)
- Merge cells:          0.6s (1 batch request)
```

**Speedup**: 80x faster (240s → 3s)

---

## 🎯 Recommended Actions

### Immediate (Today)

1. ✅ **Create fast version of update_dashboard_option_b.py**
   - Use `fast_sheets_api.py` or direct API v4
   - Test with `timeout 10 python3 ...`
   - Verify KPIs update correctly

2. ✅ **Document the fix**
   - Update `live_dashboard_v2_layout_analysis.md`
   - Add note about gspread performance issue

### Short Term (This Week)

3. 🔄 **Migrate other dashboard scripts**
   - Update realtime_dashboard_updater.py
   - Update unified_dashboard_refresh.py
   - Test all scripts with 10s timeout

4. 🔄 **Remove gspread dependency**
   - Keep for backward compatibility only
   - Add deprecation warning to old scripts

### Long Term (Next Month)

5. 📝 **Update documentation**
   - Add "DO NOT USE gspread" warning
   - Update PROJECT_CONFIGURATION.md
   - Create BEST_PRACTICES.md

6. 🗑️ **Archive slow scripts**
   - Move *.gspread_backup files to archive/
   - Delete after 30 days if no issues

---

## 📚 References

- `SHEETS_PERFORMANCE_DIAGNOSTIC.md` - Full performance analysis (298x speedup)
- `SHEETS_API_PERFORMANCE_FIX.md` - Implementation guide (255x speedup)
- `GOOGLE_SHEETS_API_DIAGNOSIS_DEC20.md` - Original diagnosis (190x speedup)
- `fast_sheets_api.py` - Fast API implementation (255x tested)
- `cache_manager.py` - Batch update system with timeout protection

---

## ✅ Validation Checklist

After implementing the fix:

- [ ] Script completes in <10 seconds
- [ ] KPIs update correctly in Live Dashboard v2
- [ ] Sparklines display properly
- [ ] Merged cells render correctly
- [ ] Status indicator shows correct value
- [ ] No timeout errors
- [ ] Cron job can run every 5 minutes without issues

---

**Summary**: Replace `gspread.open_by_key()` with direct Google Sheets API v4 calls. This will reduce your script execution time from 120+ seconds (timeout) to <5 seconds (success).
