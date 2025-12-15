# How to Add Sparklines to Live Dashboard v2 - Manual Installation

**Issue**: Rows 7-8 are empty, no sparklines displaying  
**Cause**: Apps Script not installed in spreadsheet  
**Fix**: Manual installation (5 minutes)

---

## 📋 Step-by-Step Installation

### 1. Open Apps Script Editor

1. Go to the spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Click **Extensions** → **Apps Script**
3. You should see the script editor with ID: `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`

### 2. Create New File

1. In the Apps Script editor, click the **+ button** next to "Files"
2. Select **Script** (`.gs` file)
3. Name it: `AddSparklines`

### 3. Paste the Code

Copy and paste this code into the new file:

```javascript
/**
 * Add sparklines to Live Dashboard v2
 * Run this ONCE to create sparkline formulas in rows 7-8
 */
function addSparklinesToDashboard() {
  const ss = SpreadsheetApp.openById('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA');
  const sheet = ss.getSheetByName('Live Dashboard v2') || ss.getSheets()[0];
  const dataSheet = ss.getSheetByName('Data_Hidden');
  
  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('Data_Hidden sheet not found! Run update_gb_live_complete.py first.');
    return;
  }
  
  // Clear existing content in rows 7-8
  sheet.getRange('A7:Z8').clearContent();
  
  // Row 7: Generation Mix Sparklines (columns B-K, 10 fuel types)
  const fuelTypes = ['WIND', 'CCGT', 'NUCLEAR', 'BIOMASS', 'NPSHYD', 'PS', 'OTHER', 'OCGT', 'COAL', 'OIL'];
  
  for (let i = 0; i < fuelTypes.length; i++) {
    const col = String.fromCharCode(66 + i); // B=66, C=67, etc.
    const dataRange = `Data_Hidden!${col}2:${col}49`; // 48 periods of data
    
    // Sparkline formula
    const formula = `=SPARKLINE(${dataRange}, {"charttype","line";"linewidth",2;"color1","#4285F4"})`;
    sheet.getRange(`${col}7`).setFormula(formula);
  }
  
  // Row 8: Price Sparkline (uses column A of Data_Hidden for prices)
  const priceFormula = '=SPARKLINE(Data_Hidden!A2:A49, {"charttype","line";"linewidth",2;"color1","#34A853"})';
  sheet.getRange('B8').setFormula(priceFormula);
  
  // Format rows
  sheet.getRange('A7:Z8').setVerticalAlignment('middle');
  sheet.setRowHeight(7, 60);
  sheet.setRowHeight(8, 60);
  
  SpreadsheetApp.getUi().alert('✅ Sparklines added successfully!\\n\\nRows 7-8 now contain sparkline formulas.\\nData will appear on next update (every 5 minutes).');
}

/**
 * Create menu to run the function
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('📊 Dashboard Tools')
    .addItem('Add Sparklines to Rows 7-8', 'addSparklinesToDashboard')
    .addToUi();
}
```

### 4. Save the Script

1. Click the **Save** icon (💾) or press `Ctrl+S` / `Cmd+S`
2. Give it permission if prompted

### 5. Run the Function

**Option A: Via Menu** (Recommended)
1. Close the Apps Script editor
2. Refresh the spreadsheet
3. You'll see a new menu: **📊 Dashboard Tools**
4. Click it → Select **"Add Sparklines to Rows 7-8"**
5. Authorize if prompted
6. Wait for success message

**Option B: Directly in Editor**
1. In Apps Script editor, select function: `addSparklinesToDashboard`
2. Click **Run** ▶️ button
3. Authorize if prompted
4. Check execution log for success

---

## ✅ Verification

After running, check the spreadsheet:

1. **Row 7**: Should have sparklines in columns B-K (10 fuel types)
2. **Row 8**: Should have price sparkline in column B
3. **Height**: Rows 7-8 should be taller (60px)
4. **Formulas**: Click a cell in row 7/8 - you should see `=SPARKLINE(...)` in formula bar

**Example formula in B7**:
```
=SPARKLINE(Data_Hidden!B2:B49, {"charttype","line";"linewidth",2;"color1","#4285F4"})
```

---

## 🔄 Automatic Updates

Once sparklines are installed:
- ✅ **Data updates every 5 minutes** via cron jobs
- ✅ **Sparklines auto-refresh** when Data_Hidden sheet updates
- ✅ **No manual intervention needed** going forward

---

## 🐛 Troubleshooting

### "Data_Hidden sheet not found"
**Fix**: Run the Python updater first:
```bash
cd /home/george/GB-Power-Market-JJ
python3 update_gb_live_complete.py
```

### "Authorization required"
**Fix**: 
1. Click **Review Permissions**
2. Select your Google account
3. Click **Advanced** → **Go to [project name] (unsafe)**
4. Click **Allow**

### Sparklines show "#REF!" error
**Fix**: Data_Hidden sheet column references might be wrong. Check that:
- Data_Hidden sheet exists
- It has data in columns A-K, rows 2-49
- Run `python3 update_gb_live_complete.py` to populate data

### Sparklines appear but show flat line
**Fix**: Data range might be empty. Check:
```bash
# Verify data is being written
python3 -c "
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA').worksheet('Data_Hidden')
print('Data_Hidden row 2:', sheet.row_values(2))
print('Data_Hidden row 49:', sheet.row_values(49))
"
```

---

## 📝 What This Script Does

1. **Opens** the correct spreadsheet (Live Dashboard v2)
2. **Finds** the Data_Hidden sheet (created by `update_gb_live_complete.py`)
3. **Clears** rows 7-8 (removes any existing content)
4. **Creates** SPARKLINE formulas:
   - Row 7: 10 sparklines (B-K) for each fuel type
   - Row 8: 1 sparkline (B) for price history
5. **Formats** rows (height, alignment)
6. **Shows** success message

---

## 🎯 Expected Result

After installation, your dashboard will show:

**Row 7 (Generation Mix Sparklines)**:
```
| WIND | CCGT | NUCLEAR | BIOMASS | NPSHYD | PS | OTHER | OCGT | COAL | OIL |
| ~~~~ | ~~~~ | ~~~~~~~ | ~~~~~~~ | ~~~~~~ | ~~ | ~~~~~ | ~~~~ | ____ | ___ |
```

**Row 8 (Price Sparkline)**:
```
| Price (£/MWh) |
| ~~~~~~~~~~~~~ |
```

Each `~` represents the sparkline chart showing 48 periods (24 hours) of data.

---

## 🔗 Related Documentation

- **Main Fix**: `LIVE_DASHBOARD_V2_FIX_SUMMARY.md` - Data aggregation fix
- **Technical Details**: `IRIS_DUPLICATE_DATA_FIX.md` - Deduplication logic
- **Update Scripts**: 
  - `update_live_dashboard_v2.py` - Basic updater
  - `update_gb_live_complete.py` - Creates Data_Hidden + sparklines data
- **Original Script**: `add_gb_live_sparklines.gs` - Full version with more features

---

**Last Updated**: December 11, 2025, 23:45  
**Status**: Ready for installation  
**Estimated Time**: 5 minutes
