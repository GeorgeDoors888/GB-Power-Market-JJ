# Excel Dashboard Conversion Guide

**Created:** December 17, 2025  
**Source:** [GB Live 2 Google Sheets](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)  
**Output:** `GB_Power_Market_Dashboard_Enhanced.xlsx`

---

## 📋 Overview

This guide documents the conversion of the Google Sheets dashboard to Excel, including formula translations, design adaptations, and Excel-specific features.

### Files Created

1. **GB_Power_Market_Dashboard.xlsx** - Basic data export
2. **GB_Power_Market_Dashboard_Enhanced.xlsx** - Formatted with Excel styling
3. **create_excel_dashboard.py** - Automated conversion script

---

## 📊 Sheets Included

| Sheet Name | Rows | Purpose | Key Features |
|------------|------|---------|--------------|
| **Live Dashboard v2** | 82 | Main KPI dashboard | Real-time market metrics, generation mix |
| **BtM Calculator** | 51 | Behind-the-meter calculations | Battery revenue calculator |
| **BM Revenue Analysis** | 106 | Balancing mechanism revenue | Revenue by technology, monthly trends |
| **BOALF Price Analysis** | 27 | Acceptance price analysis | Individual acceptance prices vs settlement |
| **BID_OFFER_Definitions** | 95 | Reference guide | Market terminology, bid vs offer definitions |
| **SCRP_Summary** | 47 | Price correlation analysis | Wholesale vs balancing prices |

---

## 🎨 Design & Formatting

### Color Scheme

Matching the Google Sheets orange/blue theme:

```
Primary Blue:   #1F4E78 (Section headers)
Accent Blue:    #4472C4 (Column headers)
Light Blue:     #D9E1F2 (KPI backgrounds)
Orange:         #FF6600 (Main header, highlights)
Green:          #70AD47 (Positive values)
Red:            #FF0000 (Negative values)
Yellow:         #FFC000 (Warnings)
Gray:           #E7E6E6 (Neutral backgrounds)
```

### Typography

- **Headers:** Calibri 14-20pt, Bold, White text
- **Subheaders:** Calibri 12pt, Bold
- **KPI Values:** Calibri 16-18pt, Bold, Blue
- **Body Text:** Calibri 10-11pt

### Layout Features

#### Live Dashboard v2
- **Row 1:** Main header (merged A1:L1) - Orange background
- **Row 2:** Timestamp (merged A2:L2) - Italic gray text
- **Row 4+:** Section headers (merged full width) - Blue background
- **Row 5-6:** KPI cards (alternating columns) - Light blue backgrounds

#### BtM Calculator
- **Input sections:** Light yellow background (#FFF2CC)
- **Output sections:** Light green background (#E2EFDA)
- **Calculation cells:** Bold labels with borders

#### Revenue Analysis
- **Column headers:** Blue background with white text
- **Currency columns:** Format `"£"#,##0.00`
- **Percentage columns:** Format `0.00%`

---

## 🔄 Google Sheets → Excel Formula Conversions

### Common Formula Translations

| Google Sheets | Excel Equivalent | Notes |
|---------------|------------------|-------|
| `=QUERY(...)` | **Manual table/formula** | Excel doesn't have QUERY; use FILTER + pivot tables |
| `=IMPORTRANGE(...)` | **Manual link** | Use external references: `='[file.xlsx]Sheet1'!A1` |
| `=ARRAYFORMULA(...)` | **Dynamic arrays** | Excel 365: Auto-spill arrays (remove ARRAYFORMULA) |
| `=GOOGLEFINANCE(...)` | **Power Query** | Use Data → Get Data → From Web |
| `=NOW()` | `=NOW()` | ✅ Same |
| `=TEXT(A1, "DD/MM/YYYY")` | `=TEXT(A1, "DD/MM/YYYY")` | ✅ Same |
| `=FILTER(...)` | `=FILTER(...)` | ✅ Excel 365 only |
| `=UNIQUE(...)` | `=UNIQUE(...)` | ✅ Excel 365 only |
| `=SORT(...)` | `=SORT(...)` | ✅ Excel 365 only |

### Dashboard-Specific Formulas

#### KPI Calculations

**VLP Revenue (Google Sheets):**
```javascript
=QUERY(BtM!A:Z, "SELECT SUM(D) WHERE A = date '" & TEXT(TODAY(),"yyyy-mm-dd") & "'")
```

**VLP Revenue (Excel):**
```excel
=SUMIF(BtM!A:A, TODAY(), BtM!D:D)
```

#### Wholesale Price

**Google Sheets:**
```javascript
=INDEX(IMPORTRANGE("...", "MID_Price"), MATCH(MAX(MID_Time), MID_Time, 0))
```

**Excel (if data in same workbook):**
```excel
=INDEX(Data_Hidden!A:A, MATCH(MAX(Data_Hidden!B:B), Data_Hidden!B:B, 0))
```

#### Grid Frequency

**Google Sheets:**
```javascript
=INDEX(Freq_Value, MATCH(MAX(Freq_Time), Freq_Time, 0))
```

**Excel:**
```excel
=INDEX(FreqSheet!A:A, MATCH(MAX(FreqSheet!B:B), FreqSheet!B:B, 0))
```

#### Generation Mix Calculations

**Google Sheets (with QUERY):**
```javascript
=QUERY(fuelinst!A:Z, "SELECT B, SUM(C) GROUP BY B ORDER BY SUM(C) DESC")
```

**Excel (manual approach):**
```excel
1. Create pivot table from source data
2. Or use SUMIF for each fuel type:
   =SUMIF(fuelinst!B:B, "Wind", fuelinst!C:C)
```

---

## 📈 Charts & Visualizations

### Chart Types Used

#### 1. Generation Mix (Pie Chart)
**Location:** Live Dashboard v2, below KPIs  
**Data:** Fuel type vs MW output  
**Excel Setup:**
```
1. Select data range (fuel types + MW values)
2. Insert → Pie Chart → 2D Pie
3. Format: Add data labels (%), legend position
```

#### 2. Revenue Timeline (Line Chart)
**Location:** BM Revenue Analysis  
**Data:** Monthly revenue by technology  
**Excel Setup:**
```
1. Select month column + revenue columns
2. Insert → Line Chart → Line with Markers
3. Format: Axis titles, gridlines, color-coded by tech
```

#### 3. Price Comparison (Bar Chart)
**Location:** BOALF Price Analysis  
**Data:** BOALF vs Settlement vs Wholesale prices  
**Excel Setup:**
```
1. Select comparison data
2. Insert → Bar Chart → Clustered Bar
3. Format: Different colors for each price type
```

---

## 🔧 Excel-Specific Features

### 1. Conditional Formatting

**Revenue Analysis - Highlight Top 10:**
```
1. Select revenue column
2. Home → Conditional Formatting → Top/Bottom Rules → Top 10
3. Format: Green fill, dark green text
```

**BtM Calculator - Profit/Loss:**
```
1. Select profit cells
2. Home → Conditional Formatting → Highlight Cell Rules
3. Greater than 0: Green
4. Less than 0: Red
```

### 2. Data Validation

**BtM Calculator - Input Constraints:**
```
1. Select input cells (e.g., battery capacity)
2. Data → Data Validation
3. Settings: Decimal, Between 0 and 100
4. Error Alert: "Must be 0-100 MW"
```

### 3. Named Ranges

**Define named ranges for formulas:**
```
Formulas → Define Name
- VLP_Revenue_Data = BtM!A:D
- MID_Prices = Data_Hidden!A:A
- Freq_Latest = FreqSheet!A1
```

**Use in formulas:**
```excel
=SUM(VLP_Revenue_Data)
=MAX(MID_Prices)
```

### 4. Table Formatting

**Convert data to Excel Tables:**
```
1. Select data range
2. Home → Format as Table → Choose style
3. Benefits:
   - Auto-expand formulas
   - Built-in filters
   - Structured references
```

**Example structured reference:**
```excel
=SUM(RevenueTable[Net Revenue])
```

### 5. Power Query Integration

**For real-time BigQuery data:**
```
1. Data → Get Data → From Other Sources → Blank Query
2. Advanced Editor → Paste M code:

let
    Source = GoogleBigQuery.Database("inner-cinema-476211-u9"),
    uk_energy_prod = Source{[Name="uk_energy_prod"]}[Data],
    bmrs_fuelinst = uk_energy_prod{[Name="bmrs_fuelinst"]}[Data]
in
    bmrs_fuelinst
```

---

## 🔄 Automated Data Refresh

### Method 1: VBA Script

Create `RefreshDashboard.bas`:

```vba
Sub RefreshAllData()
    ' Refresh all data connections
    ThisWorkbook.RefreshAll
    
    ' Update timestamp
    Sheets("Live Dashboard v2").Range("A2").Value = _
        "Last Updated: " & Format(Now, "DD/MM/YYYY, HH:MM:SS")
    
    ' Recalculate formulas
    Application.Calculate
    
    MsgBox "Dashboard refreshed!", vbInformation
End Sub
```

**Assign to button:**
```
1. Developer → Insert → Button
2. Assign macro: RefreshAllData
3. Label: "🔄 Refresh Data"
```

### Method 2: Python Integration

**Update Excel from Python (openpyxl):**

```python
from openpyxl import load_workbook
from google.cloud import bigquery

# Load workbook
wb = load_workbook('GB_Power_Market_Dashboard_Enhanced.xlsx')
ws = wb['Live Dashboard v2']

# Query BigQuery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = "SELECT SUM(revenue) FROM bmrs_boalf_complete WHERE DATE(settlementDate) = CURRENT_DATE()"
result = client.query(query).to_dataframe()

# Update cell
ws['B6'] = float(result.iloc[0, 0])  # VLP Revenue

# Save
wb.save('GB_Power_Market_Dashboard_Enhanced.xlsx')
```

**Schedule with cron:**
```bash
*/15 * * * * cd ~/GB-Power-Market-JJ && python3 update_excel_dashboard.py
```

---

## 📱 Mobile/iPad Compatibility

### OneDrive/SharePoint Integration

1. **Upload to OneDrive:**
   - Right-click file → Share → OneDrive
   - Get shareable link

2. **Open in Excel Mobile:**
   - iPad: Excel app (free for viewing, Office 365 for editing)
   - iPhone: Excel mobile app

3. **Enable offline access:**
   - OneDrive app → Make Available Offline

### Google Sheets Alternative

To continue using iPad with Sheets:

1. **Import Excel to Google Sheets:**
   - Google Drive → New → File Upload
   - Upload `.xlsx` file
   - Right-click → Open with → Google Sheets

2. **Formulas adjust automatically:**
   - Excel SUMIF → Sheets SUMIF ✅
   - Named ranges preserved ✅
   - Charts converted ✅

---

## 🛠️ Maintenance & Updates

### Updating from Google Sheets

**Re-run conversion script:**
```bash
cd ~/GB-Power-Market-JJ
python3 create_excel_dashboard.py
```

**Manual sync:**
```
1. Open both files
2. Google Sheets: File → Download → Microsoft Excel
3. Copy updated data to enhanced version
4. Preserve formatting and formulas
```

### Version Control

**Track changes with Git:**
```bash
git add GB_Power_Market_Dashboard_Enhanced.xlsx
git commit -m "Update: Revenue data for Dec 2025"
git push
```

**Note:** Excel files are binary; use Git LFS for large workbooks:
```bash
git lfs track "*.xlsx"
```

---

## 📚 Resources

### Excel Functions Reference
- [Microsoft Excel Functions](https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb)
- [Dynamic Arrays in Excel 365](https://support.microsoft.com/en-us/office/dynamic-array-formulas-and-spilled-array-behavior-205c6b06-03ba-4151-89a1-87a7eb36e531)

### Power Query / BigQuery
- [Google BigQuery Connector for Excel](https://cloud.google.com/bigquery/docs/connect-excel)
- [Power Query M Reference](https://docs.microsoft.com/en-us/powerquery-m/)

### Openpyxl Documentation
- [Openpyxl Official Docs](https://openpyxl.readthedocs.io/)
- [Styling Cells](https://openpyxl.readthedocs.io/en/stable/styles.html)
- [Working with Charts](https://openpyxl.readthedocs.io/en/stable/charts/introduction.html)

---

## 🚀 Next Steps

1. **Test all formulas** in Excel to ensure accuracy
2. **Add conditional formatting** for visual indicators
3. **Create VBA macros** for automated refresh
4. **Set up Power Query** connections to BigQuery
5. **Design custom charts** for key metrics
6. **Add data validation** to input cells
7. **Create named ranges** for cleaner formulas
8. **Test on iPad** with Excel mobile app

---

## ✅ Completed Features

- ✅ All 6 key sheets converted
- ✅ Professional formatting applied
- ✅ Color scheme matched (orange/blue)
- ✅ Column widths auto-adjusted
- ✅ Headers formatted with merge cells
- ✅ KPI cards styled
- ✅ Number formats applied (currency, percentages)
- ✅ Row heights optimized

## 🔜 Future Enhancements

- 🔜 Add interactive charts for each sheet
- 🔜 Implement Power Query for live BigQuery data
- 🔜 Create VBA refresh macros
- 🔜 Add data validation to input cells
- 🔜 Set up conditional formatting rules
- 🔜 Create named ranges for all data tables
- 🔜 Add sparklines for trend visualization
- 🔜 Implement slicer filters for interactive analysis

---

**Questions?** See `PROJECT_CONFIGURATION.md` or `STOP_DATA_ARCHITECTURE_REFERENCE.md`
