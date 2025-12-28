# Interconnector Sparkline Fix - Complete Guide

## Current Status
✅ **File already updated**: `clasp-gb-live-2/src/Data.gs` lines 207-222 now correctly skips writing to column H

## Problem Summary
Apps Script was overwriting Python-generated time-series sparklines with simple single-bar sparklines.

## Files in Your Apps Script Project
**Script ID**: `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`

Located in: `/home/george/GB-Power-Market-JJ/clasp-gb-live-2/src/`

Files:
- ✅ **Data.gs** - ALREADY FIXED (manages interconnector display)
- Charts.gs - Chart management (not related to interconnectors)
- Code.gs - Menu and version check (not related to interconnectors)
- Dashboard.gs - Layout setup (not related to sparkline writing)
- KPISparklines.gs - Row 4 KPI sparklines only (not interconnectors)
- Menu.gs - Menu functions
- setup_btm_calculator.gs - Calculator setup
- appsscript.json - Project metadata

## What Was Changed in Data.gs

### BEFORE (Lines 210-227) - PROBLEMATIC:
```javascript
// v2 Layout:
// Col G: Connection Name
// Col H-I (Merged): Sparkline Graphic
// Col J: Flow Value (MW)

// 1. Write Names to G and Values to J
const v2InterData = data.interconnectors.map(row => [row[0], '', '', row[1]]); // G, H, I, J
sheet.getRange(13, 7, v2InterData.length, 4).setValues(v2InterData);

// 2. Write Sparklines to H (which fills H-I merge)
const interFormulas = data.interconnectors.map((row, i) => {
  const sheetRow = 13 + i;
  const val = parseFloat(row[1]); // Flow value
  // Green if Import (>=0), Red if Export (<0)
  const color = val >= 0 ? "#2ecc71" : "#e74c3c";
  // Max capacity ~2000MW (IFA) - using ABS(J) for magnitude
  return [`=SPARKLINE(ABS(J${sheetRow}), {"charttype","bar";"max",2000;"color1","${color}"})`];
});
sheet.getRange(13, 8, interFormulas.length, 1).setFormulas(interFormulas); // ❌ OVERWRITES COLUMN H!
```

### AFTER (Lines 210-222) - FIXED:
```javascript
// v2 Layout:
// Col G: Connection Name
// Col H: Sparkline Graphic (DO NOT OVERWRITE - managed by Python update_live_metrics.py)
// Col I: Current Flow Value (MW)

// Only write Names to G - Python script manages sparklines in H
const v2InterData = data.interconnectors.map(row => [row[0]]); // G only
sheet.getRange(13, 7, v2InterData.length, 1).setValues(v2InterData);

// Note: Sparklines in column H are managed by Python script update_live_metrics.py
// which creates time-series sparklines with proper positive/negative coloring
// DO NOT write to column H here to avoid overwriting them
```

## Deployment Instructions

### Option 1: Manual Deployment (Recommended)
1. **Open Apps Script Editor**:
   ```
   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
   Extensions → Apps Script
   ```

2. **Open Data.gs** in the left sidebar

3. **Find lines 207-227** (search for "Display interconnectors")

4. **Verify the code matches** the AFTER version above
   - Should say "DO NOT OVERWRITE"
   - Should only write to column G
   - Should NOT have `sheet.getRange(13, 8, ...)`

5. **If code is OLD**, replace lines 210-227 with the AFTER code above

6. **Save**: Click 💾 icon or Ctrl+S

7. **Done!** Changes take effect immediately (no deployment needed)

### Option 2: Clasp Deployment (From Terminal)
```bash
cd /home/george/GB-Power-Market-JJ/clasp-gb-live-2
clasp push
```

## Verification Steps

### 1. Check Apps Script Code
```bash
# View the current Data.gs file locally
cat /home/george/GB-Power-Market-JJ/clasp-gb-live-2/src/Data.gs | grep -A 20 "Display interconnectors"
```

Expected output should show:
```javascript
// Only write Names to G - Python script manages sparklines in H
const v2InterData = data.interconnectors.map(row => [row[0]]); // G only
sheet.getRange(13, 7, v2InterData.length, 1).setValues(v2InterData);
```

### 2. Check Sparklines in Google Sheets
```bash
cd /home/george/GB-Power-Market-JJ
python3 -c "
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json',
    ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Live Dashboard v2')

# Check East-West interconnector (should have negative values showing export)
h14 = sheet.acell('H14', value_render_option='FORMULA').value
print('🇮🇪 East-West (H14) sparkline:')
print(h14)
print()

if h14 and 'winloss' in h14 and len(h14) > 200:
    print('✅ Time-series sparkline is intact (managed by Python)')
    print('✅ Shows all settlement periods with winloss chart')
    print('✅ Apps Script is NOT overwriting column H')
else:
    print('❌ Single-bar sparkline detected')
    print('❌ Apps Script may still be overwriting column H')
    print('⚠️  Need to update Data.gs in Apps Script Editor')
"
```

### 3. Force Python Update
```bash
# Run Python script to ensure sparklines are written
cd /home/george/GB-Power-Market-JJ
timeout 30 python3 update_live_metrics.py
```

### 4. Check for Triggers
Make sure there are no Apps Script triggers that run the old code:
1. Open Apps Script Editor
2. Click **⏰ Triggers** (clock icon on left sidebar)
3. Look for any triggers calling `displayDashboard()` or similar
4. If found, these will run Data.gs code

## What Each Column Contains Now

| Column | Content | Managed By |
|--------|---------|------------|
| G (7) | Interconnector Name (🇫🇷 IFA, etc.) | Apps Script Data.gs |
| H (8) | Time-series Sparkline (28 periods, winloss) | Python update_live_metrics.py |
| I (9) | (Empty/unused) | - |

## Expected Behavior After Fix

### Python Script (`update_live_metrics.py`):
- Runs every 5 minutes via cron
- Writes to `G13:H22`:
  - Column G: Names
  - Column H: Time-series sparklines

### Apps Script (`Data.gs`):
- Runs when triggered (onOpen, manual, etc.)
- Writes ONLY to column G (names)
- Does NOT touch column H

### Result:
✅ Sparklines persist and show proper time-series data
✅ Green bars for import, red bars for export
✅ All settlement periods displayed (1 to current)
✅ Proper scaling with winloss chart type

## Troubleshooting

### Sparklines Still Being Overwritten?

1. **Check if old Data.gs is cached**:
   - Open Apps Script Editor
   - Hard refresh: Ctrl+Shift+R
   - Check Data.gs code again

2. **Check for triggers**:
   - Apps Script Editor → Triggers (⏰ icon)
   - Remove any triggers calling old functions

3. **Force redeploy**:
   ```bash
   cd /home/george/GB-Power-Market-JJ/clasp-gb-live-2
   clasp push --force
   ```

4. **Check execution logs**:
   - Apps Script Editor → Executions
   - Look for recent runs of `displayDashboard()` or similar
   - Check if they're modifying column H

### Still Not Working?

Run this diagnostic:
```bash
cd /home/george/GB-Power-Market-JJ
python3 -c "
import gspread, time
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json',
    ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Live Dashboard v2')

print('📊 BEFORE UPDATE:')
h14_before = sheet.acell('H14', value_render_option='FORMULA').value
print(f'H14: {h14_before[:80]}...')

print('\\n⏳ Running Python update...')
import subprocess
subprocess.run(['python3', 'update_live_metrics.py'], timeout=30)

print('\\n⏱️  Waiting 5 seconds...')
time.sleep(5)

print('\\n📊 AFTER UPDATE:')
h14_after = sheet.acell('H14', value_render_option='FORMULA').value
print(f'H14: {h14_after[:80]}...')

if h14_before != h14_after:
    print('\\n✅ Sparkline was updated by Python')
else:
    print('\\n⚠️  Sparkline was NOT updated')
"
```

## Summary

✅ **Local file updated**: `clasp-gb-live-2/src/Data.gs`
⏳ **Needs deployment**: Push to Google via Apps Script Editor or clasp
🎯 **Result**: Python script will be sole manager of column H sparklines

**Next Action**: Open Apps Script Editor and verify Data.gs matches the AFTER code above.
