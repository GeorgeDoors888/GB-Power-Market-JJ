# Analysis Report Generation - Quick Guide

## ✅ Report IS Working!

The report **successfully generates** and writes data to the Analysis sheet. If you don't see output, **scroll down** to row 17+.

---

## 📍 Where to Find Your Results

### **Location**: Analysis Sheet, starting at Row 17

```
Row 15: 📊 Report Results (header)
Row 16: <empty>
Row 17: ━━━━━━━━━━━━━━━━ (VISUAL SEPARATOR - look below this!)
Row 18: date | settlementPeriod | fuelType | generation_mw (COLUMN HEADERS)
Row 19: 2025-12-29 | 1 | BIOMASS | 52314 (DATA STARTS HERE)
Row 20: 2025-12-29 | 1 | CCGT | 169452
Row 21: 2025-12-29 | 1 | COAL | 0
...
Row 1018: (up to 1000 rows of data)
```

---

## 🔍 Why You Might Not See Output

### **1. Not Scrolling Down** ⬇️
**Problem**: Sheet view is at rows 1-15  
**Solution**: **Scroll down** to row 17+ to see the visual separator and data

### **2. Looking at Wrong Sheet** 📄
**Problem**: Viewing a different sheet (e.g., "Live Dashboard v2", "BESS")  
**Solution**: Click on **"Analysis"** tab at the bottom of Google Sheets

### **3. Data Below Visible Area** 👀
**Problem**: Google Sheets shows rows 1-15 by default  
**Solution**: Use Ctrl+End (Windows) or Cmd+Down (Mac) to jump to last row with data

---

## ✅ How to Verify Data Was Generated

### **Method 1: Check Terminal Output**
After running `python3 generate_analysis_report.py`, you should see:
```
✅ Written 1000 rows to Analysis sheet
   Location: Row 18+ (header at 18, data starts at 19)
   Visual separator at row 17

👀 SCROLL DOWN to see results below row 17 in the Analysis sheet!
✅ Report generation complete!
```

### **Method 2: Check in Google Sheets**
1. Open the spreadsheet
2. Click **"Analysis"** tab (bottom of screen)
3. **Scroll down** to row 17
4. Look for the **━━━━━━** visual separator
5. Data starts at row 19

### **Method 3: Jump to Data**
In Google Sheets:
- Press **Ctrl+G** (Windows) or **Cmd+G** (Mac)
- Type **A17**
- Press Enter
- You'll see the separator and data below

---

## 📊 Example Output

### **Your Settings**:
```
From Date: 29/12/2025
To Date: 30/12/2025
Party Role: All
BMU IDs: 2__AANGE002
Generation Type: All
Report Category: 📊 Analytics & Derived
```

### **Results Generated**:
- **1,600 total rows** from BigQuery
- **1,000 rows displayed** in Google Sheets (limit)
- **Date range**: 2025-12-29 → 2025-12-30
- **Data includes**: Settlement periods, fuel types, generation in MW

---

## 🔧 Troubleshooting

### **"I still don't see any data!"**

**Check 1**: Run this command to verify data exists:
```bash
python3 -c "
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file('inner-cinema-credentials.json')
service = build('sheets', 'v4', credentials=creds)

result = service.spreadsheets().values().get(
    spreadsheetId='1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
    range='Analysis!A19:D22'
).execute()

values = result.get('values', [])
if values:
    print('✅ DATA EXISTS! Found', len(values), 'rows')
    print('First row:', values[0])
else:
    print('❌ No data at row 19')
"
```

**Check 2**: Verify you're looking at the right spreadsheet:
- Spreadsheet ID: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
- Sheet name: **Analysis** (not "Live Dashboard v2")

**Check 3**: Clear browser cache and reload:
- Press **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac)

---

## 💡 Pro Tips

### **1. Use Named Ranges**
Create a named range "ReportResults" for A17:Z1000 to quickly jump to data

### **2. Filter Data**
1. Click row 18 (header row)
2. Click Data → Create a filter
3. Use filter dropdowns to find specific data

### **3. Export to CSV**
1. Select rows 18-1018 (header + data)
2. File → Download → CSV

### **4. Refresh Data**
The report **automatically clears old data** before generating new results. Just run the script again!

---

## 📞 Quick Commands

### **Generate Report**:
```bash
python3 generate_analysis_report.py
```

### **Check Data Exists**:
```bash
python3 -c "from googleapiclient.discovery import build; from google.oauth2.service_account import Credentials; creds = Credentials.from_service_account_file('inner-cinema-credentials.json'); service = build('sheets', 'v4', credentials=creds); result = service.spreadsheets().values().get(spreadsheetId='1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA', range='Analysis!A19:D22').execute(); print('Found', len(result.get('values', [])), 'rows')"
```

### **Test Enhancement Features**:
```bash
python3 test_analysis_enhancements.py
```

---

## ✅ Summary

**The report IS working correctly!**

- ✅ Data clears automatically from row 17 onwards
- ✅ Visual separator added at row 17 (━━━━━━)
- ✅ Column headers at row 18
- ✅ Data starts at row 19
- ✅ Up to 1,000 rows displayed

**Just scroll down to row 17+ to see your results! 👀**

---

**Last Updated**: December 30, 2025  
**Script**: `generate_analysis_report.py` (v2 - Enhanced)  
**Documentation**: `ANALYSIS_ENHANCEMENT_COMPLETE.md`
