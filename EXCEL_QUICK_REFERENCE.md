# 📊 Excel Dashboard Quick Reference

## Files Created

| File | Size | Description |
|------|------|-------------|
| **GB_Power_Market_Dashboard.xlsx** | 33 KB | Basic data export |
| **GB_Power_Market_Dashboard_Enhanced.xlsx** | 33 KB | Formatted with styling |
| **create_excel_dashboard.py** | - | Automated conversion script |
| **EXCEL_DASHBOARD_GUIDE.md** | - | Complete documentation |

---

## Opening Files

### macOS/Linux
```bash
# LibreOffice (free)
libreoffice GB_Power_Market_Dashboard_Enhanced.xlsx

# Microsoft Excel (if installed)
open -a "Microsoft Excel" GB_Power_Market_Dashboard_Enhanced.xlsx
```

### Windows
```powershell
# Double-click file or:
start GB_Power_Market_Dashboard_Enhanced.xlsx
```

### iPad/iPhone
1. Upload to OneDrive/iCloud
2. Open in Excel mobile app
3. Or: Import to Google Sheets (File → Upload → Open with Sheets)

---

## Sheet Index

| # | Sheet Name | Purpose | Key Metrics |
|---|------------|---------|-------------|
| 1 | **Live Dashboard v2** | Main KPIs | VLP Revenue, Price, Frequency, Generation |
| 2 | **BtM Calculator** | Battery revenue calculator | ROI, Daily revenue, Arbitrage spread |
| 3 | **BM Revenue Analysis** | Revenue by technology | Monthly trends, Top earners |
| 4 | **BOALF Price Analysis** | Individual acceptance prices | Price coverage, Validation flags |
| 5 | **BID_OFFER_Definitions** | Reference guide | Market terminology |
| 6 | **SCRP_Summary** | Price correlations | Wholesale vs balancing |

---

## Key Formula Conversions

| Function | Google Sheets | Excel |
|----------|---------------|-------|
| **Sum if condition** | `=SUMIF(A:A, criteria, B:B)` | ✅ Same |
| **Lookup value** | `=INDEX(A:A, MATCH(MAX(B:B), B:B, 0))` | ✅ Same |
| **Today's date** | `=TODAY()` | ✅ Same |
| **Format date** | `=TEXT(A1, "DD/MM/YYYY")` | ✅ Same |
| **Query data** | `=QUERY(A:Z, "SELECT...")` | ❌ Use FILTER + Pivot |
| **Import range** | `=IMPORTRANGE("id", "Sheet!A1")` | ❌ Use external reference |
| **Array formula** | `=ARRAYFORMULA(A1:A10 * 2)` | ✅ Auto-spill (Excel 365) |

---

## Quick Actions

### Refresh Data
**Method 1: Manual**
```
Data → Refresh All (Ctrl+Alt+F5)
```

**Method 2: Automated (Python)**
```bash
python3 create_excel_dashboard.py
```

### Add Chart
```
1. Select data range
2. Insert → Chart → Choose type
3. Format → Design tab
```

### Format Currency
```
1. Select cells
2. Home → Number Format → Currency
3. Or: Custom format "£"#,##0.00
```

### Conditional Formatting
```
1. Select range
2. Home → Conditional Formatting
3. Choose rule (Top 10, Color Scales, etc.)
```

---

## Common Issues & Fixes

### ❌ Formulas Not Calculating
**Fix:** File → Options → Formulas → Calculation → Automatic

### ❌ Charts Not Updating
**Fix:** Right-click chart → Select Data → Refresh

### ❌ Currency Shows as Number
**Fix:** Format cells as `"£"#,##0.00`

### ❌ Excel 365 Functions Not Working (FILTER, SORT, etc.)
**Fix:** Requires Excel 365/2021. Use pivot tables or VBA macros instead.

---

## Color Reference

```
Headers:        #1F4E78 (Dark Blue) + White text
Subheaders:     #4472C4 (Blue) + White text  
KPI Cards:      #D9E1F2 (Light Blue)
Main Title:     #FF6600 (Orange) + White text
Positive:       #70AD47 (Green)
Negative:       #FF0000 (Red)
Warning:        #FFC000 (Yellow)
Input Fields:   #FFF2CC (Light Yellow)
Output Fields:  #E2EFDA (Light Green)
```

---

## Integration with Google Sheets

### Import Excel to Sheets
```
1. Google Drive → New → File Upload
2. Select .xlsx file
3. Right-click → Open with → Google Sheets
```

### Export from Sheets
```
1. File → Download → Microsoft Excel (.xlsx)
2. Opens in Excel with formulas preserved
```

---

## Automation Script Usage

### Run Conversion
```bash
cd ~/GB-Power-Market-JJ
python3 create_excel_dashboard.py
```

### Schedule Auto-Update (cron)
```bash
# Every 15 minutes
*/15 * * * * cd ~/GB-Power-Market-JJ && python3 create_excel_dashboard.py
```

---

## Support Files

- 📖 **EXCEL_DASHBOARD_GUIDE.md** - Complete documentation
- 🐍 **create_excel_dashboard.py** - Conversion script
- 📊 **Original:** [Google Sheets Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)

---

**Last Updated:** December 17, 2025  
**Status:** ✅ Production Ready
