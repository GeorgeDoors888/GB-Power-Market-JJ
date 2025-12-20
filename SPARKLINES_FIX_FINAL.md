# SPARKLINES FIX - ROOT CAUSE FOUND ✅

## Problem
**ALL sparklines missing** - both Top KPIs (row 4) and BM Metrics (rows 16-22)

## Root Causes

### 1. ✅ FIXED: BM Metrics Sparklines
- **Problem**: `add_market_kpis_to_dashboard.py` used `sheet.batch_update(updates)` instead of `sheet.batch_update(updates, value_input_option='USER_ENTERED')`
- **Result**: Formulas treated as strings, not evaluated
- **Fix**: Added `value_input_option='USER_ENTERED'` to line 269
- **Status**: ✅ **16/16 BM metric sparklines working!**

### 2. ❌ CRITICAL: Top KPI Sparklines (Row 4)
- **Problem**: Apps Script `Dashboard.gs` function `setupDashboardLayoutV2()` **merges row 4** (`A4:L4`), destroying individual cell formulas
- **Line**: `Dashboard.gs` line 118
- **Code**: `sheet.getRange('A4:L4').merge()`  ← **THIS DELETES ALL SPARKLINES**
- **Result**: Python adds sparklines → Apps Script merges cells → sparklines deleted
- **Fix**: Changed to `sheet.getRange('A4')` (only A4, leaves C4, E4, G4, I4, K4 free for sparklines)

### 3. Additional Issues
- **57 duplicate protected ranges** on wrong cells (B4, D4, F4 instead of C4, E4, G4, I4, K4)
  - **Fix**: Deleted all via API ✅
- **Wrong sparkline positions** in `update_live_dashboard_v2.py`
  - **Fix**: Changed from B4, D4, F4, G4 to C4, E4, G4, I4, K4 ✅

## ✅ Final Status

**BM Metrics**: ✅ **16/16 sparklines working** (rows 16-22, columns N, R, U, X)

**Top KPIs**: ❌ **0/5 sparklines** - Apps Script still destroying them

## 🚨 ACTION REQUIRED

**YOU MUST UPDATE APPS SCRIPT MANUALLY:**

1. Open Apps Script editor: https://script.google.com/home/projects/1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980/edit

2. Open `Dashboard.gs`

3. Find line 118 (around there):
```javascript
// KPI Section - Advanced Card Layout
sheet.getRange('A4:L4').merge()
  .setValue('🚀 Market Overview')
```

4. **REPLACE WITH**:
```javascript
// KPI Section - Row 4 left unmerged for sparklines (C4, E4, G4, I4, K4)
// Only set text in A4, leave other cells for sparklines
sheet.getRange('A4')
  .setValue('🚀 Market Overview')
```

5. **ALSO** fix line 29 (first function):
```javascript
// OLD (line 29):
sheet.getRange('A4:L4').merge()

// NEW:
sheet.getRange('A4')
```

6. **Save the script** (Ctrl+S or Cmd+S)

7. **Then run Python updater**:
```bash
cd /home/george/GB-Power-Market-JJ
python3 update_live_dashboard_v2.py
```

## Why Apps Script Keeps Running

The execution log shows `onOpen` trigger runs **every time you open the sheet**. This is normal, but the problem is functions that call `setupDashboardLayoutV2()` will merge row 4 and destroy sparklines.

The **PYTHON_MANAGED** flag in AA1 should prevent this, but someone may have called the layout function manually.

## Files Modified

1. ✅ `/home/george/GB-Power-Market-JJ/add_market_kpis_to_dashboard.py` - Line 269
2. ✅ `/home/george/GB-Power-Market-JJ/update_live_dashboard_v2.py` - Lines 1073-1078
3. ⚠️ `/home/george/GB-Power-Market-JJ/clasp-gb-live-2/src/Dashboard.gs` - Lines 29, 118 (NOT DEPLOYED YET)

## Test After Fix

```bash
cd /home/george/GB-Power-Market-JJ
python3 update_live_dashboard_v2.py

# Then verify:
python3 << 'EOF'
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)

sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA').worksheet('Live Dashboard v2')

print("✅ SPARKLINE CHECK:\n")
for col in ['C', 'E', 'G', 'I', 'K']:
    formula = sheet.acell(f'{col}4', value_render_option='FORMULA').value
    if 'SPARKLINE' in str(formula):
        print(f"   ✅ {col}4: WORKING")
    else:
        print(f"   ❌ {col}4: MISSING")
EOF
```

## Expected Result

After fixing Apps Script and running Python updater:
- **Top KPIs**: 5/5 sparklines in C4, E4, G4, I4, K4 ✅
- **BM Metrics**: 16/16 sparklines in rows 16-22 ✅
- **Total**: 21/21 sparklines working ✅

---

**Last Updated**: December 17, 2025 23:00 GMT
**Status**: Apps Script fix ready, awaiting manual deployment
