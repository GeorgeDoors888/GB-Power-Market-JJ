# GB Live Dashboard - Complete Documentation

**Date**: December 10, 2025  
**Status**: ✅ Fully Operational  
**Sheet URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit  
**Active Worksheet**: "Live Dashboard"

---

## 🎯 Overview

GB Live Dashboard is a real-time UK energy market dashboard that displays KPIs, generation mix, and interconnector flows by querying BigQuery directly from Google Apps Script.

**Architecture Flow**:
```
Python Script → BigQuery Table → Apps Script → Google Sheets (Live Dashboard)
```

---

## 📁 File Locations

### Python Scripts

#### Main Data Pipeline Script
**File**: `/home/george/GB-Power-Market-JJ/build_publication_table_current.py`  
**Purpose**: Builds the BigQuery publication table with current data from IRIS real-time pipeline  
**Usage**:
```bash
cd ~/GB-Power-Market-JJ
python3 build_publication_table_current.py
```

**What it does**:
- Queries IRIS tables (`bmrs_fuelinst_iris`) for latest date (2025-12-10)
- Aggregates generation data by fuel type
- Calculates KPIs (VLP revenue, wholesale avg, frequency, total gen, wind gen, demand)
- Creates generation mix array (20 fuel types)
- Includes all 10 interconnectors with flow values
- Creates intraday arrays (wind, demand, price by settlement period)
- Writes single-row summary to BigQuery

**Key Configuration**:
```python
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
PUBLICATION_TABLE = "publication_dashboard_live"
LOCATION = "US"
```

#### Legacy Script (Historical Only)
**File**: `/home/george/GB-Power-Market-JJ/build_publication_table_fixed.py`  
**Note**: Only uses historical tables (up to 2025-10-30), does not include IRIS data  
**Status**: Deprecated in favor of `build_publication_table_current.py`

---

### Apps Script Files

**Location**: `/tmp/gb-live-2-final/`  
**Deployment Directory**: Bound to Script ID `1MNNFFYr06n8ohcj6XI3yb6RwtE0kRFkgRHY5QTmi2-rIkGafGAT0Pp1O`

#### 1. Code.gs
**Purpose**: Main entry point, menu creation, BigQuery execution

```javascript
const PROJECT_ID = 'inner-cinema-476211-u9';
const DATASET = 'uk_energy_prod';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('GB Live Dashboard')
    .addItem('Force Refresh Dashboard', 'updateDashboard')
    .addToUi();
}

function updateDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();  // Uses currently active sheet
  
  sheet.clear();
  SpreadsheetApp.flush();
  
  setupDashboardLayout(sheet);
  const data = fetchData();
  
  if (data) {
    displayData(sheet, data);
    createCharts(sheet, data);
    SpreadsheetApp.getUi().alert('Dashboard refresh complete! All ' + 
      data.interconnectors.length + ' interconnectors displayed.');
  } else {
    SpreadsheetApp.getUi().alert('Failed to fetch data. Please check the logs.');
  }
}

function executeBigQuery(query) {
  // Executes BigQuery query using Advanced Service
  // Returns: Array of row objects
}
```

**Key Change**: Uses `getActiveSheet()` instead of `getSheetByName()` to work with any sheet tab

#### 2. Data.gs
**Purpose**: Fetches and displays data from BigQuery

```javascript
const PUBLICATION_TABLE_ID = 'publication_dashboard_live';

function fetchData() {
  const query = `SELECT * FROM \`${PROJECT_ID}.${DATASET}.${PUBLICATION_TABLE_ID}\` 
                 ORDER BY report_date DESC LIMIT 1`;
  
  const results = executeBigQuery(query);
  
  if (!results || results.length === 0) {
    Logger.log('Error: Publication table is empty');
    return null;
  }
  
  const row = results[0].f;
  
  return {
    reportDate: row[0].v,
    kpis: {
      vlpRevenue: parseFloat(row[1].v || '0').toFixed(2),
      wholesaleAvg: parseFloat(row[2].v || '0').toFixed(2),
      frequency: parseFloat(row[3].v || '50.0').toFixed(2),
      totalGen: parseFloat(row[4].v || '0').toFixed(2),
      windGen: parseFloat(row[5].v || '0').toFixed(2),
      demand: parseFloat(row[6].v || '0').toFixed(2)
    },
    generationMix: (row[7].v || []).map(item => [
      item.v.f[0].v,           // Fuel type
      parseFloat(item.v.f[1].v) // MW
    ]),
    interconnectors: (row[8].v || []).map(item => [
      item.v.f[0].v,           // Connection name
      parseFloat(item.v.f[1].v) // Flow MW
    ]),
    intraday: {
      wind: (row[9].v || []).map(val => parseFloat(val.v || 0)),
      demand: (row[10].v || []).map(val => parseFloat(val.v || 0)),
      price: (row[11].v || []).map(val => parseFloat(val.v || 0))
    }
  };
}

function displayData(sheet, data) {
  // Display KPIs in row 7
  const kpiValues = [
    data.kpis.vlpRevenue,
    data.kpis.wholesaleAvg,
    data.kpis.frequency,
    data.kpis.totalGen,
    data.kpis.windGen,
    data.kpis.demand
  ];
  
  for (let i = 0; i < kpiValues.length; i++) {
    const col = i * 2 + 1;
    sheet.getRange(7, col).setValue(kpiValues[i]);
  }
  
  // Display generation mix (starting at row 13, columns A-B)
  if (data.generationMix && data.generationMix.length > 0) {
    sheet.getRange(13, 1, data.generationMix.length, 2).setValues(data.generationMix);
  }
  
  // Display interconnectors (starting at row 13, columns D-E)
  if (data.interconnectors && data.interconnectors.length > 0) {
    sheet.getRange(13, 4, data.interconnectors.length, 2).setValues(data.interconnectors);
  }
}
```

**Critical**: Data starts at **row 13**, with headers at row 12

#### 3. Dashboard.gs
**Purpose**: Creates dashboard layout and formatting

```javascript
function setupDashboardLayout(sheet) {
  sheet.clear();
  sheet.setFrozenRows(2);
  sheet.getRange('1:1000').setBackground('#f3f3f3').setFontColor('#000000');
  sheet.setColumnWidths(1, 12, 150);

  // Row 1: Header
  sheet.getRange('A1:L1').merge()
    .setValue('GB Power Market - Live Executive Dashboard')
    .setBackground('#212121')
    .setFontColor('#ffffff')
    .setFontSize(20)
    .setFontWeight('bold')
    .setHorizontalAlignment('center');
  
  // Row 2: Timestamp
  sheet.getRange('A2:L2').merge()
    .setValue('Last Updated: ' + new Date().toLocaleString('en-GB', 
      { timeZone: 'Europe/London' }))
    .setBackground('#424242')
    .setFontColor('#ffffff')
    .setFontSize(10)
    .setHorizontalAlignment('center');

  // Row 4: KPI Section Header
  sheet.getRange('A4:L4').merge()
    .setValue('Key Performance Indicators (7-Day Trend)')
    .setFontSize(14)
    .setFontWeight('bold');
  
  // Row 5: KPI Headers (6 metrics across columns)
  const kpiHeaders = ['VLP Revenue (£k)', 'Wholesale Avg (£/MWh)', 
    'Grid Frequency (Hz)', 'Total Gen (GW)', 'Wind Gen (GW)', 'Demand (GW)'];
  
  for (let i = 0; i < kpiHeaders.length; i++) {
    const col = i * 2 + 1;
    sheet.getRange(5, col, 1, 2).merge()
      .setValue(kpiHeaders[i])
      .setFontWeight('bold')
      .setHorizontalAlignment('center')
      .setBackground('#eeeeee');
  }
  
  // Row 10: Live Snapshot Section
  sheet.getRange('A10:L10').merge()
    .setValue('Live Market Snapshot')
    .setFontSize(14)
    .setFontWeight('bold');

  // Row 11: Section Headers
  sheet.getRange('A11:B11').merge()
    .setValue('Generation Mix')
    .setFontWeight('bold')
    .setHorizontalAlignment('center')
    .setBackground('#eeeeee');
  
  sheet.getRange('D11:E11').merge()
    .setValue('🌍 Interconnectors')
    .setFontWeight('bold')
    .setHorizontalAlignment('center')
    .setBackground('#eeeeee');
  
  // Row 12: Column Headers
  sheet.getRange('A12').setValue('Fuel Type').setFontWeight('bold');
  sheet.getRange('B12').setValue('MW').setFontWeight('bold');
  sheet.getRange('D12').setValue('Connection').setFontWeight('bold');
  sheet.getRange('E12').setValue('Flow (MW)').setFontWeight('bold');
}
```

#### 4. Charts.gs
**Purpose**: Creates sparklines and charts

```javascript
function createCharts(sheet, data) {
  // KPI Sparklines in row 7
  const kpiData = [
    data.intraday.price,
    data.intraday.demand,
    data.intraday.wind
  ];
  
  // Generation Mix Pie Chart
  if (data.generationMix && data.generationMix.length > 0) {
    const chartDataRange = sheet.getRange(13, 1, data.generationMix.length, 2);
    const chart = sheet.newChart()
      .setChartType(Charts.ChartType.PIE)
      .addRange(chartDataRange)
      .setPosition(13, 4, 0, 0)
      .setOption('title', 'Generation Mix (MW)')
      .setOption('pieHole', 0.4)
      .build();
    sheet.insertChart(chart);
  }
  
  // Intraday Price Chart
  // Additional line charts for price, wind, demand trends
}
```

#### 5. appsscript.json
**Purpose**: Manifest with API configurations

```json
{
  "timeZone": "Europe/London",
  "dependencies": {
    "enabledAdvancedServices": [
      {
        "userSymbol": "BigQuery",
        "version": "v2",
        "serviceId": "bigquery"
      }
    ]
  },
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/bigquery"
  ],
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8"
}
```

**Critical**: BigQuery Advanced Service v2 must be enabled

---

## 📊 BigQuery Data Structure

### Table Location
```
Project: inner-cinema-476211-u9
Dataset: uk_energy_prod
Table:   publication_dashboard_live
Location: US
```

### Table Schema

```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.publication_dashboard_live` (
  report_date DATE,
  vlp_revenue_7d FLOAT64,
  wholesale_avg FLOAT64,
  frequency_avg FLOAT64,
  total_gen FLOAT64,
  wind_gen FLOAT64,
  demand FLOAT64,
  generation_mix ARRAY<STRUCT<fuel STRING, mw FLOAT64>>,
  interconnectors ARRAY<STRUCT<name STRING, flow_mw FLOAT64>>,
  intraday_wind ARRAY<FLOAT64>,
  intraday_demand ARRAY<FLOAT64>,
  intraday_price ARRAY<FLOAT64>
);
```

### Current Data (as of 2025-12-10)

**Single Row Table** with:
- **report_date**: 2025-12-10
- **total_gen**: 73.282 GW
- **wind_gen**: 49.838 GW
- **generation_mix**: 20 fuel types (WIND, NUCLEAR, CCGT, BIOMASS, etc.)
- **interconnectors**: 10 connections (ElecLink, East-West, IFA, Greenlink, IFA2, Moyle, BritNed, Nemo, NSL, Viking Link)
- **intraday arrays**: 4 settlement periods (will expand as day progresses)

### All 10 Interconnectors

1. **ElecLink** (France) - 1000 MW
2. **East-West** (Ireland) - 500 MW
3. **IFA** (France) - 2000 MW
4. **Greenlink** (Ireland) - 500 MW
5. **IFA2** (France) - 1000 MW
6. **Moyle** (N.Ireland) - 500 MW
7. **BritNed** (Netherlands) - 1000 MW
8. **Nemo** (Belgium) - 1000 MW
9. **NSL** (Norway) - 1400 MW
10. **Viking Link** (Denmark) - 1400 MW

---

## 🔄 Data Pipeline

### Source Tables (BigQuery)

**Historical Data** (up to 2025-10-30):
- `bmrs_fuelinst` - Fuel generation by settlement period
- `bmrs_costs` - System prices (SSP/SBP)
- `bmrs_mid` - Market index data
- `bmrs_freq` - Grid frequency

**IRIS Real-Time Data** (2025-10-30+):
- `bmrs_fuelinst_iris` - Real-time fuel generation
- `bmrs_costs_iris` - Real-time system prices (not configured yet)

### Data Refresh Workflow

```
1. Run Python script:
   cd ~/GB-Power-Market-JJ
   python3 build_publication_table_current.py

2. Script queries IRIS for latest date
   → Aggregates all data sources
   → Creates single-row publication table
   → Overwrites previous data

3. In Google Sheets:
   Click: GB Live Dashboard → Force Refresh Dashboard

4. Apps Script:
   → Queries BigQuery publication table
   → Parses JSON results
   → Writes to active sheet
   → Creates charts

5. Dashboard updates with current data
```

---

## 🎨 Dashboard Layout

### Row Structure

```
Row 1:  Header "GB Power Market - Live Executive Dashboard"
Row 2:  Timestamp "Last Updated: [DD/MM/YYYY, HH:MM:SS]"
Row 3:  (Empty)
Row 4:  "Key Performance Indicators (7-Day Trend)"
Row 5:  KPI Headers (6 metrics across 12 columns)
Row 6:  (Empty)
Row 7:  KPI Values (populated from BigQuery)
Row 8:  Units (£k, £/MWh, Hz, GW, GW, GW)
Row 9:  Sparklines (trend indicators)
Row 10: "Live Market Snapshot"
Row 11: Section Headers ("Generation Mix" | "🌍 Interconnectors")
Row 12: Column Headers (Fuel Type, MW | Connection, Flow (MW))
Row 13+: Data rows (generation mix in A-B, interconnectors in D-E)
```

### Column Layout

```
Columns A-B:  Generation Mix (Fuel Type | MW)
Column C:     (Empty separator)
Columns D-E:  Interconnectors (Connection | Flow MW)
Columns F-L:  Charts and additional metrics
```

---

## 🚀 Deployment & Usage

### Initial Setup (One-time)

1. **Install clasp**:
```bash
npm install -g @google/clasp
clasp login
```

2. **Create BigQuery table**:
```bash
cd ~/GB-Power-Market-JJ
python3 build_publication_table_current.py
```

3. **Clone Apps Script project**:
```bash
cd /tmp/gb-live-2-final
clasp clone 1MNNFFYr06n8ohcj6XI3yb6RwtE0kRFkgRHY5QTmi2-rIkGafGAT0Pp1O
```

### Regular Operations

**Update Data**:
```bash
cd ~/GB-Power-Market-JJ
python3 build_publication_table_current.py
```

**Refresh Dashboard**:
1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Make sure "Live Dashboard" tab is active
3. Click: GB Live Dashboard → Force Refresh Dashboard
4. Wait for success message: "Dashboard refresh complete! All 10 interconnectors displayed."

**Deploy Code Changes**:
```bash
cd /tmp/gb-live-2-final
# Edit .gs files as needed
clasp push --force
```

---

## 🐛 Troubleshooting

### Dashboard Not Updating

**Issue**: Timestamp not changing after refresh  
**Solution**: 
- Ensure you're on the "Live Dashboard" tab (not "GB Live 2")
- Apps Script now uses `getActiveSheet()` so whichever tab is active will be updated

### Only 4 Interconnectors Showing

**Issue**: Old data displayed (IFA=1000 instead of 2000)  
**Solution**: 
- Run `python3 build_publication_table_current.py` to update BigQuery
- Refresh dashboard in Google Sheets

### "Array cannot have a null element" Error

**Issue**: NULL values in BigQuery arrays  
**Solution**: Already fixed with `IFNULL()` in `build_publication_table_current.py`

### No Data Returned

**Issue**: BigQuery table empty or query fails  
**Check**:
```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
result = client.query('SELECT COUNT(*) FROM \`inner-cinema-476211-u9.uk_energy_prod.publication_dashboard_live\`')
print(list(result)[0][0], 'rows')
"
```

### OAuth Authorization Required

**Issue**: First run asks for permissions  
**Solution**:
1. Click "Review Permissions"
2. Select your Google account
3. Click "Advanced" → "Go to GB Live 2 (unsafe)"
4. Click "Allow"

---

## 📝 Key Configuration Values

```python
# Python
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
PUBLICATION_TABLE = "publication_dashboard_live"
LOCATION = "US"

# Apps Script
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
PUBLICATION_TABLE_ID = 'publication_dashboard_live'

# Google Sheets
Sheet ID: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
Worksheet: "Live Dashboard"

# Apps Script
Script ID: 1MNNFFYr06n8ohcj6XI3yb6RwtE0kRFkgRHY5QTmi2-rIkGafGAT0Pp1O
```

---

## 📚 Related Documentation

- **Project Configuration**: `PROJECT_CONFIGURATION.md`
- **Data Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **Statistical Analysis**: `STATISTICAL_ANALYSIS_GUIDE.md`
- **IRIS Deployment**: `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`
- **ChatGPT Integration**: `CHATGPT_INSTRUCTIONS.md`

---

## ✅ Verification Commands

**Check BigQuery Table**:
```bash
cd ~/GB-Power-Market-JJ
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
result = list(client.query('SELECT report_date, total_gen, ARRAY_LENGTH(interconnectors) as ic_count FROM \`inner-cinema-476211-u9.uk_energy_prod.publication_dashboard_live\`').result())
print(f'Date: {result[0][0]}, Total Gen: {result[0][1]} GW, Interconnectors: {result[0][2]}')
"
```

**Check Apps Script Deployment**:
```bash
cd /tmp/gb-live-2-final
clasp open  # Opens Apps Script editor in browser
```

**Check Sheet State**:
```bash
python3 -c "
from google.oauth2 import service_account
import gspread
creds = service_account.Credentials.from_service_account_file(
    '/home/george/.config/google-cloud/bigquery-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
gc = gspread.authorize(creds)
ws = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA').worksheet('Live Dashboard')
print(f'Timestamp: {ws.row_values(2)[0]}')
print(f'Total Gen: {ws.row_values(7)[6]}')
"
```

---

## 🔄 Update Schedule

**Manual**: Run Python script and refresh sheet as needed  
**Recommended**: Every 30 minutes during market hours  
**Automated** (future): Cron job + Apps Script time-based trigger

---

**Last Updated**: December 10, 2025  
**Status**: ✅ Production Ready  
**Maintainer**: George Major (george@upowerenergy.uk)
