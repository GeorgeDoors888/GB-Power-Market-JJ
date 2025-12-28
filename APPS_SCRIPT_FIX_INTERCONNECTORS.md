# Fix Apps Script Overwriting Interconnector Sparklines

## Problem
The Apps Script (`1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`) is **overwriting** the time-series sparklines created by `update_live_metrics.py` with simple single-bar sparklines.

## Root Cause
In `clasp-gb-live-2/src/Data.gs`, lines 216-227, the script writes simple sparklines to column H:

```javascript
// PROBLEMATIC CODE (writes single-bar sparklines):
const interFormulas = data.interconnectors.map((row, i) => {
  const sheetRow = 13 + i;
  const val = parseFloat(row[1]);
  const color = val >= 0 ? "#2ecc71" : "#e74c3c";
  return [`=SPARKLINE(ABS(J${sheetRow}), {"charttype","bar";"max",2000;"color1","${color}"})`];
});
sheet.getRange(13, 8, interFormulas.length, 1).setFormulas(interFormulas);
```

This **overwrites** the proper time-series sparklines from Python that show:
- ✅ All settlement periods (1 to current)
- ✅ Winloss chart type with proper scaling
- ✅ Green for import, red for export
- ✅ Historical flow patterns throughout the day

## Solution

### Option 1: Update Apps Script (Recommended)
Update `Data.gs` to NOT write to column H:

```javascript
// Display interconnectors
if (data.interconnectors && data.interconnectors.length > 0) {
  if (isV2) {
    // v2 Layout:
    // Col G: Connection Name
    // Col H: Sparkline Graphic (DO NOT OVERWRITE - managed by Python)
    
    // Only write Names to G - Python script manages sparklines in H
    const v2InterData = data.interconnectors.map(row => [row[0]]); // G only
    sheet.getRange(13, 7, v2InterData.length, 1).setValues(v2InterData);
    
    // Note: Sparklines in column H are managed by Python script update_live_metrics.py
    // which creates time-series sparklines with proper positive/negative coloring
    // DO NOT write to column H here to avoid overwriting them
    
  } else {
    // v1: Connection in D (col 4), Flow in E (col 5)
    sheet.getRange(13, 4, data.interconnectors.length, 2).setValues(data.interconnectors);
  }
}
```

### Option 2: Disable Apps Script Auto-Refresh
If you don't want to modify the script, disable any triggers that call the Apps Script refresh function.

## Deployment Steps

### Manual Deployment (Google Apps Script Editor):
1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Go to **Extensions → Apps Script**
3. Find `Data.gs` file
4. Locate lines 207-232 (the interconnector display section)
5. Replace with the updated code above
6. Click **Save** (💾 icon)
7. The changes take effect immediately

### Clasp Deployment (from terminal):
```bash
cd /home/george/GB-Power-Market-JJ/clasp-gb-live-2
clasp push
```

## Verification

After updating, check that sparklines persist:

```bash
python3 -c "
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', 
    ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Live Dashboard v2')

# Check East-West sparkline
h14 = sheet.acell('H14', value_render_option='FORMULA').value
print('🇮🇪 East-West (H14):')
print(h14)

if 'winloss' in h14 and len(h14) > 200:
    print('✅ Time-series sparkline is intact')
else:
    print('❌ Apps Script overwrote the sparkline')
"
```

Expected output:
```
🇮🇪 East-West (H14):
=SPARKLINE({-423,-448,-519,-482,-531,...},{"charttype","winloss";"color","green";"negcolor","red"})
✅ Time-series sparkline is intact
```

## Files Modified
- ✅ `clasp-gb-live-2/src/Data.gs` - Updated to not overwrite column H

## Summary
The Apps Script was creating single-value bar charts that overwrote the Python-generated time-series sparklines. The fix removes the sparkline-writing code from Apps Script, allowing the Python script (`update_live_metrics.py`) to fully manage the interconnector sparklines in column H.
