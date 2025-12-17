# 🎯 Sparklines and Bar Charts - FIXED

**Date**: December 17, 2025  
**Status**: ✅ RESOLVED  
**Issue**: Columns D and E values disappearing after writes  
**Root Cause**: Merged cells C12:F22 + Apps Script overwrites

---

## Problem Summary

When the Python dashboard updater wrote values to columns D (bar charts) and E (sparklines), they immediately disappeared. Only columns A, B, C were visible.

### Symptoms
- API confirmed successful write to B13:D13 (3 cells updated)
- Immediate readback showed only 3 columns: A13, B13, C13
- Column D13 and E13 appeared empty
- No errors thrown - values just vanished

---

## Root Causes Discovered

### 1. **Merged Cells** (Primary Issue)
- Google Sheets had merged cells **C12:F22** (columns C through F, rows 12-22)
- When writing to D13, the value went into the merged cell area
- Only the "anchor" cell (C13) was visible - D/E/F appeared empty
- **Solution**: Unmerged cells C12:F22 using Sheets API

### 2. **Apps Script Conflicts** (Secondary Issue)  
The clasp-deployed Apps Script (`clasp-gb-live-2/`) was interfering:

**Dashboard.gs** `setupDashboardLayoutV2()`:
- Only created headers for columns A, B, C
- Missing D12 (Bar) and E12 (Trend) headers
- **Solution**: Added D12 and E12 headers + PYTHON_MANAGED flag check

**Data.gs** `displayData()`:
- Overwrote column C with SPARKLINE bar charts
- This replaced the TEXT percentage formula
- **Solution**: Added PYTHON_MANAGED flag check to skip function

---

## Implementation Details

### Changes Made

**1. update_live_dashboard_v2.py**:
```python
# Set flag to prevent Apps Script from interfering
sheet.update_acell('AA1', 'PYTHON_MANAGED')

# Add fuel trend sparklines (column E, rows 13-22)
fuel_sparkline_map = {
    'WIND': (13, 2, '#4CAF50'),      # Dashboard row, Data_Hidden row, color
    'NUCLEAR': (14, 3, '#9C27B0'),
    'CCGT': (15, 4, '#FF5722'),
    # ... etc
}

for fuel, (dashboard_row, data_row, color) in fuel_sparkline_map.items():
    sparkline_formula = (
        f'=IF(ISBLANK(Data_Hidden!$B${data_row}:$AW${data_row}),"", '
        f'SPARKLINE(Data_Hidden!$B${data_row}:$AW${data_row}, '
        f'{{"charttype","line";"linewidth",2;"color","{color}"}}))' 
    )
```

**2. clasp-gb-live-2/src/Dashboard.gs**:
```javascript
function setupDashboardLayoutV2(sheet) {
  // Check if Python updater is managing the layout
  const skipAutoLayout = sheet.getRange('AA1').getValue();
  if (skipAutoLayout === 'PYTHON_MANAGED') {
    Logger.log('Skipping layout setup - managed by Python script');
    return;
  }
  
  // Added D12 and E12 headers:
  sheet.getRange('D12').setValue('📊 Bar').setFontWeight('bold');
  sheet.getRange('E12').setValue('📈 Trend (00:00→)').setFontWeight('bold');
}
```

**3. clasp-gb-live-2/src/Data.gs**:
```javascript
function displayData(sheet, data) {
  if (!data) return;
  
  // Skip if Python is managing
  const isPythonManaged = sheet.getRange('AA1').getValue();
  if (isPythonManaged === 'PYTHON_MANAGED') {
    Logger.log('Skipping displayData - managed by Python script');
    return;
  }
  // ...
}
```

**4. Manual Unmerge Operation**:
```python
# Unmerged cells C12:F22 using Google Sheets API
requests = [{
    'unmergeCells': {
        'range': {
            'sheetId': 687718775,
            'startRowIndex': 11,   # Row 12
            'endRowIndex': 23,     # Row 23 (exclusive)
            'startColumnIndex': 2, # Column C
            'endColumnIndex': 6    # Column F (exclusive)
        }
    }
}]
```

---

## Current Layout (Rows 13-22)

| Column | Content | Formula Example |
|--------|---------|-----------------|
| **A** | Fuel name | `🌬️ WIND` |
| **B** | GW value | `16.6` |
| **C** | Share % | `=TEXT(40.7/100,"0.0%")` → `40.7%` |
| **D** | Bar chart | `=REPT("█",MIN(INT(B13*2),50))` → `█████████...` |
| **E** | Trend sparkline | `=SPARKLINE(Data_Hidden!$B$2:$AW$2,...)` → 📈 |

---

## Data_Hidden Sheet Structure

```
Rows 2-11:   Fuel generation timeseries (10 fuels × 48 periods)
             Row 2:  WIND data (B2:AW2)
             Row 3:  NUCLEAR data (B3:AW3)
             ...
             Row 11: PS data (B11:AW11)

Rows 12-21:  Interconnector flows (10 ICs × 48 periods)

Rows 22-26:  KPI timeseries (5 KPIs × 48 periods)
             Row 22: Wholesale Price
             Row 23: Frequency
             Row 24: Total Generation
             Row 25: Wind Output
             Row 26: System Demand

Column A:    Labels
Columns B-AW: Settlement periods 1-48 (00:00 → 23:30)
```

---

## Verification

**Test command**:
```bash
cd ~/GB-Power-Market-JJ && python3 << 'EOF'
from google.oauth2 import service_account
import gspread

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
sheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA').worksheet('Live Dashboard v2')

result = sheet.get('A13:E13', value_render_option='FORMULA')[0]
print(f"✅ Row 13 has {len(result)} columns")
print(f"   A: {result[0]}")  # Fuel name
print(f"   B: {result[1]}")  # GW
print(f"   C: {result[2][:30]}...")  # Share %
print(f"   D: {result[3][:30]}...")  # Bar
print(f"   E: {result[4][:40]}...")  # Sparkline
