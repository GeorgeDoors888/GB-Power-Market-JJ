# Search & Analysis Integration - Todo List
**Date**: December 31, 2025
**Status**: 🚧 PLANNING PHASE

---

## 📋 Overview

Integrate the **Search interface** with **Analysis report generation** to enable:
1. Search for BM Units/Assets by GSP, DNO, attributes
2. Generate analysis reports directly from search results
3. Produce same outputs as Analysis sheet (Trend Analysis, Correlation, Statistical Summary, etc.)

---

## 🎯 Phase 1: Search Interface Enhancements

### ✅ TODO #1: Add GSP (Grid Supply Point) Search ⏳ NOT STARTED
**Description**: Enable searching by GSP region

**GSP Regions** (14 regions in GB):
```
_A - Eastern
_B - East Midlands
_C - London
_D - Merseyside and North Wales
_E - Midlands
_F - Northern
_G - North Western
_H - Southern
_J - South Eastern
_K - South Wales
_L - South Western
_M - Yorkshire
_N - Southern Scotland
_P - Northern Scotland
```

**Implementation**:
```python
# In create_search_interface.py
def fetch_gsp_regions() -> List[str]:
    """Fetch GSP regions from BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    SELECT DISTINCT gspgroupid
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE gspgroupid IS NOT NULL
    ORDER BY gspgroupid
    """

    df = client.query(query).to_dataframe()
    return df['gspgroupid'].tolist()
```

**Sheet Location**: Add Row 15
```
Row 15: GSP Region:  [None ▼]  (_A - Eastern, _B - East Midlands, _C - London...)
```

---

### ✅ TODO #2: Add DNO (Distribution Network Operator) Search ⏳ NOT STARTED
**Description**: Enable searching by DNO operator

**DNO List** (14 DNOs in GB):
```
1. Electricity North West (ENWL)
2. Northern Powergrid (NPGN/NPGY)
3. Scottish Power Energy Networks (SPEN - SPD/SPM)
4. Scottish & Southern Electricity Networks (SSEN - SSEH/SSES)
5. UK Power Networks (UKPN - EPN/LPN/SPN)
6. Western Power Distribution (WPD - WMID/EMID/SWALES/SWEST)
   - Now National Grid Electricity Distribution (NGED)
```

**Data Source**: `neso_dno_reference` table or `gb_power.duos_unit_rates`

**Implementation**:
```python
def fetch_dno_list() -> List[str]:
    """Fetch DNO operators from BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    SELECT DISTINCT dno_name
    FROM `{PROJECT_ID}.uk_energy_prod.neso_dno_reference`
    ORDER BY dno_name
    """

    df = client.query(query).to_dataframe()
    return df['dno_name'].tolist()
```

**Sheet Location**: Add Row 16
```
Row 16: DNO Operator:  [None ▼]  (ENWL, NPGN, UKPN-EPN, SSEN-SSEH...)
```

---

### ✅ TODO #3: Add Voltage Level Filter ⏳ NOT STARTED
**Description**: Filter by connection voltage (HV, EHV, 132kV, etc.)

**Voltage Levels**:
```
- LV (Low Voltage): <1 kV
- HV (High Voltage): 11 kV, 33 kV
- EHV (Extra High Voltage): 132 kV
- Transmission: 275 kV, 400 kV
```

**Sheet Location**: Add Row 17
```
Row 17: Voltage Level:  [None ▼]  (LV, HV, EHV, 132kV, 275kV, 400kV)
```

---

### ✅ TODO #4: Fix Generator Search Error ⏳ NOT STARTED
**Description**: "Generator" record type not producing valid command

**Current Issue**:
```
Record Type: Generator
Command: python3 advanced_search_tool_enhanced.py --type "Generator"
Error: "Generator" not recognized as valid type
```

**Valid Record Types**:
- BSC Party
- BM Unit
- NESO Project
- TEC Project
- ~~Generator~~ (use "BM Unit" + Fuel Type filter instead)

**Fix**: Update dropdown to remove "Generator" or map to "BM Unit":
```javascript
// In search_interface.gs
if (criteria.recordType === 'Generator') {
  args.push('--type "BM Unit"');
  // Auto-add fuel type filter if not specified
} else if (criteria.recordType && criteria.recordType !== 'None') {
  args.push('--type "' + criteria.recordType + '"');
}
```

---

## 🎯 Phase 2: Analysis Report Integration

### ✅ TODO #5: Add "Generate Report" Button to Search Results ⏳ NOT STARTED
**Description**: After search completes, enable report generation for selected assets

**Sheet Layout**:
```
Row 16: [🔍 Search]  [🧹 Clear]  [ℹ️ Help]  [📊 Generate Report] ← NEW
```

**Apps Script Function**:
```javascript
function generateReportFromSearch() {
  /**
   * Generate Analysis report for selected search results
   * Reads BMU IDs from results (rows 22+)
   * Calls generate_analysis_report.py with BMU filter
   */
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Search');

  // Get selected rows or all results
  var selection = sheet.getActiveRange();
  var startRow = Math.max(22, selection.getRow());
  var numRows = selection.getNumRows();

  // Extract BMU IDs from column B
  var bmuIds = [];
  for (var i = 0; i < numRows; i++) {
    var id = sheet.getRange(startRow + i, 2).getValue();
    if (id && id !== '') {
      bmuIds.push(id);
    }
  }

  if (bmuIds.length === 0) {
    SpreadsheetApp.getUi().alert('⚠️ No results selected. Please select rows 22+ or run a search first.');
    return;
  }

  // Show report type dialog
  showReportTypeDialog(bmuIds);
}
```

---

### ✅ TODO #6: Create Report Type Selection Dialog ⏳ NOT STARTED
**Description**: Dialog to choose report type (matching Analysis sheet categories)

**13 Report Categories** (from generate_analysis_report.py):
```
1. 📊 Analytics & Derived
2. ⚡ Generation & Fuel Mix
3. 🔌 Interconnectors
4. 💰 Market Prices
5. 🎯 Balancing Mechanism
6. 📈 Demand & Forecasting
7. 🔋 Individual BMU Generation (B1610)
8. ⚙️ System Operations
9. 🌐 Transmission & Grid
10. 💸 Settlement & Imbalance
11. 🔄 Power Flows
12. 📊 Aggregated Generation
13. 🌍 Regional Data
```

**Dialog Implementation**:
```javascript
function showReportTypeDialog(bmuIds) {
  var html = HtmlService.createHtmlOutput(
    '<div style="font-family: Arial; padding: 20px;">' +
    '<h2>📊 Generate Analysis Report</h2>' +
    '<p><strong>Selected Assets:</strong> ' + bmuIds.length + ' BMU(s)</p>' +
    '<p>' + bmuIds.slice(0, 5).join(', ') + (bmuIds.length > 5 ? '...' : '') + '</p>' +
    '<hr>' +
    '<h3>Select Report Type:</h3>' +
    '<select id="reportType" style="width: 100%; padding: 8px; font-size: 14px;">' +
    '<option value="individual_bmu">🔋 Individual BMU Generation (B1610)</option>' +
    '<option value="fuel_mix">⚡ Generation & Fuel Mix</option>' +
    '<option value="balancing">🎯 Balancing Mechanism</option>' +
    '<option value="market_prices">💰 Market Prices</option>' +
    '<option value="demand">📈 Demand & Forecasting</option>' +
    '<option value="analytics">📊 Analytics & Derived</option>' +
    '<option value="system_ops">⚙️ System Operations</option>' +
    '<option value="settlement">💸 Settlement & Imbalance</option>' +
    '<option value="transmission">🌐 Transmission & Grid</option>' +
    '<option value="interconnectors">🔌 Interconnectors</option>' +
    '<option value="power_flows">🔄 Power Flows</option>' +
    '<option value="aggregated">📊 Aggregated Generation</option>' +
    '<option value="regional">🌍 Regional Data</option>' +
    '</select>' +
    '<br><br>' +
    '<h3>Date Range:</h3>' +
    '<label>From: <input type="date" id="fromDate" value="2025-12-01"></label>' +
    '<label>To: <input type="date" id="toDate" value="2025-12-14"></label>' +
    '<br><br>' +
    '<h3>Graph Type:</h3>' +
    '<select id="graphType" style="width: 100%; padding: 8px;">' +
    '<option value="line">Line Chart (Time Series)</option>' +
    '<option value="bar">Bar Chart</option>' +
    '<option value="area">Area Chart (Stacked)</option>' +
    '<option value="scatter">Scatter Plot</option>' +
    '<option value="heatmap">Heatmap</option>' +
    '</select>' +
    '<br><br>' +
    '<h3>Analysis Type:</h3>' +
    '<select id="analysisType" style="width: 100%; padding: 8px;">' +
    '<option value="trend">Trend Analysis (30 days)</option>' +
    '<option value="correlation">Correlation Analysis</option>' +
    '<option value="distribution">Distribution Analysis</option>' +
    '<option value="anomaly">Anomaly Detection</option>' +
    '<option value="statistical">Statistical Summary</option>' +
    '<option value="forecast">Forecasting (7 days)</option>' +
    '</select>' +
    '<hr>' +
    '<button onclick="generateReport()">📊 Generate Report</button> ' +
    '<button onclick="google.script.host.close()">Cancel</button>' +
    '<script>' +
    'function generateReport() {' +
    '  var type = document.getElementById("reportType").value;' +
    '  var from = document.getElementById("fromDate").value;' +
    '  var to = document.getElementById("toDate").value;' +
    '  var graph = document.getElementById("graphType").value;' +
    '  var analysis = document.getElementById("analysisType").value;' +
    '  google.script.run.executeReportGeneration(type, from, to, graph, analysis, ' + JSON.stringify(bmuIds) + ');' +
    '}' +
    '</script>' +
    '</div>'
  ).setWidth(600).setHeight(600);

  SpreadsheetApp.getUi().showModalDialog(html, '📊 Generate Report');
}
```

---

### ✅ TODO #7: Execute Report Generation from Search ⏳ NOT STARTED
**Description**: Call Python script with selected parameters

**Apps Script Function**:
```javascript
function executeReportGeneration(reportType, fromDate, toDate, graphType, analysisType, bmuIds) {
  /**
   * Build and display command to run generate_analysis_report.py
   */

  // Map report type to category name
  var categoryMap = {
    'individual_bmu': '🔋 Individual BMU Generation (B1610)',
    'fuel_mix': '⚡ Generation & Fuel Mix',
    'balancing': '🎯 Balancing Mechanism',
    'market_prices': '💰 Market Prices',
    // ... etc
  };

  var category = categoryMap[reportType];
  var bmuFilter = bmuIds.join(',');

  // Build command
  var command = 'python3 generate_analysis_report.py ' +
                '--category "' + category + '" ' +
                '--from "' + fromDate + '" ' +
                '--to "' + toDate + '" ' +
                '--bmu-filter "' + bmuFilter + '" ' +
                '--graph-type "' + graphType + '" ' +
                '--analysis-type "' + analysisType + '"';

  // Show command dialog
  var html = HtmlService.createHtmlOutput(
    '<div style="font-family: monospace; padding: 20px;">' +
    '<h3>📊 Report Generation Command</h3>' +
    '<p><strong>Report Type:</strong> ' + category + '</p>' +
    '<p><strong>Assets:</strong> ' + bmuIds.length + ' BMU(s)</p>' +
    '<p><strong>Date Range:</strong> ' + fromDate + ' to ' + toDate + '</p>' +
    '<p><strong>Graph:</strong> ' + graphType + '</p>' +
    '<p><strong>Analysis:</strong> ' + analysisType + '</p>' +
    '<hr>' +
    '<p><strong>Run this command in terminal:</strong></p>' +
    '<textarea style="width:100%; height:80px; font-family: monospace;">' + command + '</textarea>' +
    '<p><em>Results will appear in Analysis sheet (rows 18+)</em></p>' +
    '<button onclick="google.script.host.close()">Close</button>' +
    '</div>'
  ).setWidth(700).setHeight(450);

  SpreadsheetApp.getUi().showModalDialog(html, '📊 Run Report Generation');
}
```

---

### ✅ TODO #8: Enhance generate_analysis_report.py with New Parameters ⏳ NOT STARTED
**Description**: Add command-line arguments for graph type and analysis type

**Current Script**: Only supports category, date range, BMU filter

**Add Parameters**:
```python
import argparse

parser = argparse.ArgumentParser(description='Generate analysis reports')
parser.add_argument('--category', type=str, required=True, help='Report category')
parser.add_argument('--from', dest='from_date', type=str, required=True, help='Start date (YYYY-MM-DD)')
parser.add_argument('--to', dest='to_date', type=str, required=True, help='End date (YYYY-MM-DD)')
parser.add_argument('--bmu-filter', type=str, help='Comma-separated BMU IDs')
parser.add_argument('--graph-type', type=str, default='line',
                    choices=['line', 'bar', 'area', 'scatter', 'heatmap'],
                    help='Graph visualization type')
parser.add_argument('--analysis-type', type=str, default='trend',
                    choices=['trend', 'correlation', 'distribution', 'anomaly', 'statistical', 'forecast'],
                    help='Analysis method')

args = parser.parse_args()
```

**Usage Example**:
```bash
python3 generate_analysis_report.py \
  --category "🔋 Individual BMU Generation (B1610)" \
  --from "2025-12-01" \
  --to "2025-12-14" \
  --bmu-filter "E_FARNB-1,E_HAWKB-1" \
  --graph-type "line" \
  --analysis-type "trend"
```

---

## 🎯 Phase 3: Advanced Analysis Features

### ✅ TODO #9: Create Comparative Analysis Mode ⏳ NOT STARTED
**Description**: Compare multiple BMUs side-by-side

**Features**:
- Select 2-10 BMUs from search results
- Generate comparison charts (line graph with multiple series)
- Statistical comparison table (mean, median, std dev per BMU)
- Performance ranking

**Example Output**:
```
📊 Comparative Analysis: E_FARNB-1 vs E_HAWKB-1 vs E_SHOS-1
Period: 2025-12-01 to 2025-12-14

┌──────────────┬──────────────┬──────────────┬──────────────┐
│ BMU          │ Total (MWh)  │ Avg (MW)     │ Peak (MW)    │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ E_FARNB-1    │ 1,671        │ 6.2          │ 50           │
│ E_HAWKB-1    │ 3,168        │ 11.7         │ 50           │
│ E_SHOS-1     │ 36,333       │ 134.4        │ 200          │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

---

### ✅ TODO #10: Add Portfolio Analysis ⏳ NOT STARTED
**Description**: Analyze all assets owned by a party/organization

**Workflow**:
1. Search for organization: "Drax Power Limited"
2. Results show all Drax BMUs
3. Click "📊 Portfolio Analysis"
4. Generate aggregated report:
   - Total portfolio capacity
   - Fuel mix breakdown
   - Revenue analysis (if VLP)
   - Utilization rates
   - Geographic distribution

---

### ✅ TODO #11: Create DNO-Level Aggregation ⏳ NOT STARTED
**Description**: Aggregate all generation within a DNO region

**Example**:
```
Query: DNO = "UKPN-EPN" (Eastern Power Networks)
Report: Regional Generation Analysis
Output:
- Total embedded generation capacity
- Fuel type breakdown
- Peak export vs import
- DUoS charge impact
```

---

### ✅ TODO #12: Add GSP-Level Aggregation ⏳ NOT STARTED
**Description**: Aggregate all generation within a GSP region

**Example**:
```
Query: GSP = "_A" (Eastern)
Report: GSP Regional Analysis
Output:
- Total generation by fuel type
- Demand vs generation balance
- Transmission constraints
- Curtailment events
```

---

## 🎯 Phase 4: Export & Visualization

### ✅ TODO #13: Add Direct Chart Generation ⏳ NOT STARTED
**Description**: Generate charts in Google Sheets (not just data)

**Implementation**:
```python
import gspread
from gspread_formatting import *

def create_chart_in_sheets(sheet, data_range, chart_type, title):
    """Create embedded chart in Google Sheets"""
    requests = [{
        'addChart': {
            'chart': {
                'spec': {
                    'title': title,
                    'basicChart': {
                        'chartType': chart_type.upper(),  # LINE, BAR, AREA, etc.
                        'domains': [{'domain': {'sourceRange': {'sources': [data_range]}}}],
                        'series': [{'series': {'sourceRange': {'sources': [data_range]}}}]
                    }
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {'sheetId': sheet.id, 'rowIndex': 0, 'columnIndex': 12}
                    }
                }
            }
        }
    }]

    sheet.spreadsheet.batch_update({'requests': requests})
```

---

### ✅ TODO #14: Add PDF Export ⏳ NOT STARTED
**Description**: Export report as PDF with charts

**Implementation**:
```python
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def export_report_to_pdf(data, charts, filename):
    """Generate PDF report with charts"""
    with PdfPages(filename) as pdf:
        # Page 1: Summary table
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=data.values, colLabels=data.columns,
                        loc='center', cellLoc='left')
        pdf.savefig(fig, bbox_inches='tight')

        # Page 2+: Charts
        for chart_data, chart_type, title in charts:
            fig, ax = plt.subplots(figsize=(11, 8.5))
            # ... generate chart
            pdf.savefig(fig, bbox_inches='tight')

        # Add metadata
        d = pdf.infodict()
        d['Title'] = 'GB Power Market Analysis Report'
        d['Author'] = 'GB Power Market JJ'
        d['CreationDate'] = datetime.now()
```

---

### ✅ TODO #15: Create Dashboard Summary Sheet ⏳ NOT STARTED
**Description**: Auto-update summary dashboard with key metrics

**Sheet**: New "Search Dashboard" tab

**Layout**:
```
Row 1:  📊 SEARCH & ANALYSIS DASHBOARD
Row 3:  🔍 RECENT SEARCHES
Row 5:  [Last 10 searches with results count]

Row 15: 📈 TOP ASSETS BY GENERATION
Row 17: [Top 10 BMUs by MWh, last 30 days]

Row 27: 💰 VLP REVENUE LEADERS
Row 29: [Top VLP parties by estimated revenue]

Row 39: 🗺️ REGIONAL BREAKDOWN
Row 41: [GSP regions with total capacity]
```

---

## 🎯 Phase 5: Advanced Filters & Intelligence

### ✅ TODO #16: Add Custom SQL Query Mode ⏳ NOT STARTED
**Description**: Power users can write custom BigQuery SQL

**Interface**:
```
Row 18: 🔬 Advanced Mode: [Checkbox]
Row 19: Custom SQL Query:
Row 20: [Large text area for SQL]
Row 21: [Execute Query] button
```

**Safety**:
- Read-only mode (SELECT only, no INSERT/UPDATE/DELETE)
- Query cost estimation before execution
- Row limit (max 10,000)

---

### ✅ TODO #17: Add ML-Based Recommendations ⏳ NOT STARTED
**Description**: Suggest relevant searches based on patterns

**Example**:
```
User searches: "VLP" + "Battery"
System suggests:
  - "Also search for: VLP revenue analysis (last 30 days)"
  - "Related: Frequency response performance for batteries"
  - "Similar assets: Other 50 MW batteries in same GSP"
```

---

### ✅ TODO #18: Create Scheduled Reports ⏳ NOT STARTED
**Description**: Auto-generate reports daily/weekly

**Implementation**:
```javascript
// Apps Script Trigger
function createDailyTrigger() {
  ScriptApp.newTrigger('runDailyVLPReport')
    .timeBased()
    .atHour(7)  // 7 AM daily
    .everyDays(1)
    .create();
}

function runDailyVLPReport() {
  // Auto-generate VLP battery revenue report
  // Email to stakeholders
}
```

---

## 📊 Implementation Priority

### Week 1 (Jan 1-7, 2026) - Critical Fixes
- ✅ **TODO #4**: Fix Generator search error (HIGH PRIORITY)
- ✅ **TODO #1**: Add GSP search
- ✅ **TODO #2**: Add DNO search
- ✅ **TODO #3**: Add voltage level filter

### Week 2 (Jan 8-14, 2026) - Analysis Integration
- ✅ **TODO #5**: Add "Generate Report" button
- ✅ **TODO #6**: Create report type dialog
- ✅ **TODO #7**: Execute report generation
- ✅ **TODO #8**: Enhance generate_analysis_report.py

### Week 3 (Jan 15-21, 2026) - Advanced Features
- ✅ **TODO #9**: Comparative analysis mode
- ✅ **TODO #10**: Portfolio analysis
- ✅ **TODO #11**: DNO-level aggregation
- ✅ **TODO #12**: GSP-level aggregation

### Week 4 (Jan 22-28, 2026) - Visualization & Export
- ✅ **TODO #13**: Direct chart generation
- ✅ **TODO #14**: PDF export
- ✅ **TODO #15**: Dashboard summary sheet

### Month 2+ (Feb 2026+) - Advanced Intelligence
- ✅ **TODO #16**: Custom SQL query mode
- ✅ **TODO #17**: ML-based recommendations
- ✅ **TODO #18**: Scheduled reports

---

## 🔧 Technical Architecture

### Data Flow
```
┌─────────────────┐
│  Search Sheet   │ → User fills criteria (GSP, DNO, BMU, etc.)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Apps Script    │ → Reads criteria, validates, builds command
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Python Script  │ → Queries BigQuery, filters results
│ (advanced_      │
│  search_tool_   │
│  enhanced.py)   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Search Results │ → Displays in rows 22+ (11 columns)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Select Assets  │ → User selects rows, clicks "Generate Report"
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Report Dialog  │ → Choose report type, graph, analysis method
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  generate_      │ → Queries BigQuery, generates report
│  analysis_      │
│  report.py      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Analysis Sheet │ → Results appear in rows 18+
│  + Charts       │
└─────────────────┘
```

---

## 📋 Success Criteria

### Phase 1 Complete When:
- ✅ GSP search dropdown populated (14 regions)
- ✅ DNO search dropdown populated (14 DNOs)
- ✅ Voltage level filter working
- ✅ "Generator" error fixed

### Phase 2 Complete When:
- ✅ "Generate Report" button appears
- ✅ Report type dialog shows all 13 categories
- ✅ Command generated correctly with BMU filter
- ✅ Results appear in Analysis sheet

### Phase 3 Complete When:
- ✅ Comparative analysis working (2+ BMUs)
- ✅ Portfolio analysis aggregates by organization
- ✅ DNO/GSP aggregation producing regional reports

### Phase 4 Complete When:
- ✅ Charts generated directly in sheets
- ✅ PDF export working with embedded charts
- ✅ Dashboard summary auto-updates

---

## 🎯 Phase 6: Dynamic Dropdown Linking & GSP-DNO Integration

### 📋 TODO #19: Add DNO ID to GSP Region Dropdown ⏳ NOT STARTED
**Description**: Show DNO ID alongside GSP region in dropdown for easy identification

**Current GSP Dropdown**:
```
_A - Eastern
_B - East Midlands
_C - London
...
```

**Enhanced GSP Dropdown** (with DNO ID):
```
_A - Eastern (EPN)
_B - East Midlands (EMID)
_C - London (LPN)
_D - Merseyside/N Wales (ENWL)
_E - Midlands (WMID)
_F - Northern (NPGN)
_G - North Western (ENWL)
_H - Southern (SPN)
_J - South Eastern (SPN)
_K - South Wales (SWALES)
_L - South Western (SWEST)
_M - Yorkshire (NPGY)
_N - Southern Scotland (SPD)
_P - Northern Scotland (SSEH)
```

**GSP to DNO Mapping Table**:
```python
GSP_TO_DNO_MAP = {
    '_A': 'EPN',      # Eastern → UK Power Networks Eastern
    '_B': 'EMID',     # East Midlands → WPD/NGED East Midlands
    '_C': 'LPN',      # London → UK Power Networks London
    '_D': 'ENWL',     # Merseyside/N Wales → Electricity North West
    '_E': 'WMID',     # Midlands → WPD/NGED West Midlands
    '_F': 'NPGN',     # Northern → Northern Powergrid Northeast
    '_G': 'ENWL',     # North Western → Electricity North West
    '_H': 'SPN',      # Southern → UK Power Networks South Eastern
    '_J': 'SPN',      # South Eastern → UK Power Networks South Eastern
    '_K': 'SWALES',   # South Wales → WPD/NGED South Wales
    '_L': 'SWEST',    # South Western → WPD/NGED South West
    '_M': 'NPGY',     # Yorkshire → Northern Powergrid Yorkshire
    '_N': 'SPD',      # Southern Scotland → Scottish Power Distribution
    '_P': 'SSEH'      # Northern Scotland → SSEN Hydro
}
```

**Implementation**:
```python
# In add_gsp_dno_voltage_filters.py or create_search_interface.py
GSP_REGIONS_WITH_DNO = [
    "_A - Eastern (EPN)",
    "_B - East Midlands (EMID)",
    "_C - London (LPN)",
    "_D - Merseyside/N Wales (ENWL)",
    "_E - Midlands (WMID)",
    "_F - Northern (NPGN)",
    "_G - North Western (ENWL)",
    "_H - Southern (SPN)",
    "_J - South Eastern (SPN)",
    "_K - South Wales (SWALES)",
    "_L - South Western (SWEST)",
    "_M - Yorkshire (NPGY)",
    "_N - Southern Scotland (SPD)",
    "_P - Northern Scotland (SSEH)"
]
```

**Benefits**:
- Users see which DNO serves each GSP region
- No need to memorize GSP-to-DNO mapping
- Easier filtering by region and operator

---

### 📋 TODO #20: Add DNO ID to DNO Operator Dropdown & Rename to "DNO AREA" ⏳ NOT STARTED
**Description**: 
1. Rename "DNO Operator" to "DNO AREA"
2. Show DNO ID alongside operator name in dropdown

**Current DNO Dropdown**:
```
Row 16: DNO Operator:  [Electricity North West (ENWL) ▼]
```

**Enhanced DNO AREA Dropdown**:
```
Row 16: DNO AREA:  [ENWL - Electricity North West ▼]
```

**DNO List with IDs First**:
```
ENWL - Electricity North West
NPGN - Northern Powergrid Northeast
NPGY - Northern Powergrid Yorkshire
SPD - Scottish Power Distribution
SPM - Scottish Power Manweb
SSEH - SSE Scottish Hydro (Northern Scotland)
SSES - SSE Southern Electric (Southern England)
EPN - UK Power Networks Eastern
LPN - UK Power Networks London
SPN - UK Power Networks South Eastern
WMID - NGED West Midlands
EMID - NGED East Midlands
SWALES - NGED South Wales
SWEST - NGED South West
```

**Implementation**:
```python
# In add_gsp_dno_voltage_filters.py
DNO_OPERATORS_WITH_IDS = [
    "ENWL - Electricity North West",
    "NPGN - Northern Powergrid Northeast",
    "NPGY - Northern Powergrid Yorkshire",
    "SPD - Scottish Power Distribution",
    "SPM - Scottish Power Manweb",
    "SSEH - SSE Scottish Hydro (Northern Scotland)",
    "SSES - SSE Southern Electric (Southern England)",
    "EPN - UK Power Networks Eastern",
    "LPN - UK Power Networks London",
    "SPN - UK Power Networks South Eastern",
    "WMID - NGED West Midlands",
    "EMID - NGED East Midlands",
    "SWALES - NGED South Wales",
    "SWEST - NGED South West"
]
```

**Sheet Update**:
```python
def update_dno_area_label(sheet):
    """Rename DNO Operator to DNO AREA"""
    sheet.update(values=[['DNO AREA:']], range_name='A16')
```

**Benefits**:
- DNO ID shown first (matches industry conventions)
- "AREA" clearer than "Operator" for users
- Consistent with GSP region naming

---

### 📋 TODO #21: Implement Dynamic Dropdown Synchronization ⏳ NOT STARTED
**Description**: When user selects GSP Region or DNO AREA, automatically update the other dropdown to match

**User Experience**:
```
Scenario 1: User selects GSP Region
1. User selects: GSP Region = "_A - Eastern (EPN)"
2. System auto-selects: DNO AREA = "EPN - UK Power Networks Eastern"

Scenario 2: User selects DNO AREA
1. User selects: DNO AREA = "ENWL - Electricity North West"
2. System auto-selects: GSP Region = "_D - Merseyside/N Wales (ENWL)" OR "_G - North Western (ENWL)"
   (Shows first match if multiple GSPs map to same DNO)

Scenario 3: User manually changes selection
1. User selects: GSP Region = "_A - Eastern (EPN)"
2. System auto-selects: DNO AREA = "EPN - UK Power Networks Eastern"
3. User manually changes: DNO AREA = "ENWL - Electricity North West"
4. System auto-selects: GSP Region = "_D - Merseyside/N Wales (ENWL)"
```

**Implementation - Apps Script**:
```javascript
// In search_interface.gs

// Add onEdit trigger
function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  if (sheet.getName() !== 'Search') return;
  
  var range = e.range;
  var row = range.getRow();
  var col = range.getColumn();
  
  // B15 = GSP Region changed
  if (row === 15 && col === 2) {
    syncDnoFromGsp(sheet);
  }
  
  // B16 = DNO AREA changed
  if (row === 16 && col === 2) {
    syncGspFromDno(sheet);
  }
}

function syncDnoFromGsp(sheet) {
  /**
   * When GSP selected, auto-select matching DNO
   */
  var gspValue = sheet.getRange('B15').getValue();
  if (!gspValue || gspValue === 'None' || gspValue === 'All') return;
  
  // Extract DNO ID from GSP selection (text in parentheses)
  var match = gspValue.match(/\(([A-Z]+)\)$/);
  if (!match) return;
  
  var dnoId = match[1];  // e.g., "EPN" from "_A - Eastern (EPN)"
  
  // Find matching DNO AREA option
  var dnoOptions = sheet.getRange('I16:I30').getValues();  // DNO dropdown data
  for (var i = 0; i < dnoOptions.length; i++) {
    var option = dnoOptions[i][0];
    if (option && option.startsWith(dnoId + ' -')) {
      sheet.getRange('B16').setValue(option);
      break;
    }
  }
}

function syncGspFromDno(sheet) {
  /**
   * When DNO selected, auto-select matching GSP (first match)
   */
  var dnoValue = sheet.getRange('B16').getValue();
  if (!dnoValue || dnoValue === 'None' || dnoValue === 'All') return;
  
  // Extract DNO ID (before first hyphen)
  var dnoId = dnoValue.split(' -')[0].trim();  // e.g., "EPN" from "EPN - UK Power Networks Eastern"
  
  // Find matching GSP option
  var gspOptions = sheet.getRange('H15:H29').getValues();  // GSP dropdown data
  for (var i = 0; i < gspOptions.length; i++) {
    var option = gspOptions[i][0];
    if (option && option.indexOf('(' + dnoId + ')') !== -1) {
      sheet.getRange('B15').setValue(option);
      break;
    }
  }
}
```

**Edge Cases**:
1. **Multiple GSPs per DNO** (e.g., ENWL serves both _D and _G)
   - Solution: Select first match alphabetically
   - User can manually override

2. **User clears selection**
   - If user sets GSP to "None", clear DNO AREA
   - If user sets DNO AREA to "None", clear GSP

3. **Manual override**
   - Allow user to manually select different GSP/DNO combination
   - Don't force synchronization if values manually diverged

**Alternative Implementation - Python Backend**:
```python
# In advanced_search_tool_enhanced.py
def validate_gsp_dno_consistency(gsp_region: str, dno_area: str) -> bool:
    """
    Validate that GSP and DNO selections are consistent
    Returns: True if consistent or if one is None
    """
    if not gsp_region or not dno_area:
        return True
    
    # Extract DNO ID from GSP
    gsp_match = re.search(r'\(([A-Z]+)\)$', gsp_region)
    dno_id_from_gsp = gsp_match.group(1) if gsp_match else None
    
    # Extract DNO ID from DNO AREA
    dno_id = dno_area.split(' -')[0].strip()
    
    # Check consistency
    if dno_id_from_gsp and dno_id and dno_id_from_gsp != dno_id:
        logger.warning(f"⚠️ GSP-DNO mismatch: GSP has {dno_id_from_gsp}, DNO AREA has {dno_id}")
        return False
    
    return True
```

**Benefits**:
- **Improved UX**: Less manual data entry
- **Reduced Errors**: Prevents GSP-DNO mismatches
- **Faster Workflow**: Select one field, other auto-populates
- **Educational**: Users learn GSP-to-DNO relationships

---

### 📋 TODO #22: Add BM Unit Name Auto-Lookup ⏳ NOT STARTED
**Description**: When user selects BM Unit ID, automatically populate BM Unit Name (and vice versa)

**User Experience**:
```
Scenario 1: User selects BM Unit ID
1. User selects: BM Unit ID = "E_FARNB-1"
2. System auto-fills: Name field shows "Farnborough BESS"
3. System auto-fills: Organization = "Flexgen"
4. System auto-fills: Fuel Type = "Battery Storage"

Scenario 2: User types BM Unit Name
1. User types in Party/Name Search: "Farnborough"
2. System suggests: BM Unit ID = "E_FARNB-1"
3. System auto-fills organization and fuel type
```

**Implementation - Apps Script**:
```javascript
// In search_interface.gs

function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  if (sheet.getName() !== 'Search') return;
  
  var range = e.range;
  var row = range.getRow();
  var col = range.getColumn();
  
  // B9 = BM Unit ID changed
  if (row === 9 && col === 2) {
    lookupBmuDetails(sheet);
  }
}

function lookupBmuDetails(sheet) {
  /**
   * When BM Unit selected, show details in info panel
   */
  var bmuId = sheet.getRange('B9').getValue();
  if (!bmuId || bmuId === 'None' || bmuId === 'All') return;
  
  // Query BigQuery for BMU details
  var query = 'SELECT bmunitid, ngcbmunitname, leadpartyname, fuel_type, capacity ' +
              'FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data` ' +
              'WHERE bmunitid = "' + bmuId + '" LIMIT 1';
  
  // NOTE: Apps Script cannot directly query BigQuery
  // Options:
  // 1. Pre-populate BMU lookup table in hidden sheet
  // 2. Call Python API endpoint
  // 3. Use Apps Script BigQuery connector (requires setup)
  
  // Option 1: Lookup from hidden sheet (fastest)
  var lookupSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BmuLookup');
  if (!lookupSheet) return;
  
  var data = lookupSheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {  // Skip header
    if (data[i][0] === bmuId) {
      var name = data[i][1];
      var org = data[i][2];
      var fuel = data[i][3];
      var capacity = data[i][4];
      
      // Show info message
      SpreadsheetApp.getUi().alert(
        '📋 BM Unit Details\n\n' +
        'ID: ' + bmuId + '\n' +
        'Name: ' + name + '\n' +
        'Organization: ' + org + '\n' +
        'Fuel Type: ' + fuel + '\n' +
        'Capacity: ' + capacity + ' MW'
      );
      
      break;
    }
  }
}
```

**Python Script to Create BmuLookup Sheet**:
```python
# create_bmu_lookup_sheet.py
def create_bmu_lookup_sheet():
    """Create hidden sheet with BMU lookup data"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        bmunitid,
        ngcbmunitname,
        leadpartyname,
        fuel_type,
        registeredcapacity
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE bmunitid IS NOT NULL
    ORDER BY bmunitid
    """
    
    df = client.query(query).to_dataframe()
    
    # Write to Google Sheets
    sheet = gc.open_by_key(SHEET_ID)
    
    # Create or get BmuLookup sheet
    try:
        lookup_sheet = sheet.worksheet('BmuLookup')
    except:
        lookup_sheet = sheet.add_worksheet('BmuLookup', rows=3000, cols=10)
    
    # Write data
    lookup_sheet.clear()
    lookup_sheet.update([df.columns.tolist()] + df.values.tolist())
    
    # Hide sheet
    lookup_sheet.hide()
    
    print(f"✅ Created BmuLookup sheet with {len(df)} BMU records")
```

**Benefits**:
- **Auto-Complete**: Reduce typing errors
- **Context**: Show BMU details immediately
- **Validation**: Confirm correct asset selected
- **Learning**: Users see asset names and organizations

---

### 📋 TODO #23: Visual Indicator for Synchronized Dropdowns ⏳ NOT STARTED
**Description**: Show visual cue when dropdowns are synchronized

**Visual Indicators**:
```
Row 15: GSP Region:     [_A - Eastern (EPN) ▼]    🔗 Linked to DNO AREA
Row 16: DNO AREA:       [EPN - UK Power Networks Eastern ▼]    🔗 Linked to GSP
```

**Implementation - Conditional Formatting**:
```python
def apply_sync_indicators(sheet):
    """Apply formatting to show synchronized fields"""
    from gspread_formatting import Color, CellFormat, format_cell_range
    
    # Light blue background for synchronized fields
    sync_format = CellFormat(
        backgroundColor=Color(0.85, 0.92, 1.0),  # Light blue
        borders={
            'left': {'style': 'SOLID', 'width': 2, 'color': Color(0.26, 0.52, 0.96)},
            'right': {'style': 'SOLID', 'width': 2, 'color': Color(0.26, 0.52, 0.96)}
        }
    )
    
    # Apply to GSP and DNO fields
    format_cell_range(sheet, 'B15', sync_format)
    format_cell_range(sheet, 'B16', sync_format)
    
    # Add info icons
    sheet.update(values=[['GSP Region: 🔗']], range_name='A15')
    sheet.update(values=[['DNO AREA: 🔗']], range_name='A16')
```

**Benefits**:
- **Clarity**: Users understand fields are linked
- **Discoverability**: New users learn about synchronization feature
- **Status**: Visual confirmation of sync state

---

### Phase 6 Complete When:
- ✅ GSP dropdown shows DNO IDs: "_A - Eastern (EPN)"
- ✅ DNO dropdown renamed to "DNO AREA" with IDs first: "EPN - UK Power Networks Eastern"
- ✅ GSP selection auto-updates DNO AREA
- ✅ DNO AREA selection auto-updates GSP
- ✅ BM Unit selection shows asset details
- ✅ Visual indicators show synchronized fields

---

## 🆘 Current Error Fix

**Root Cause**: "Generator" is not a valid record type in the search tool

**Valid Types**:
- `BSC Party`
- `BM Unit`
- `NESO Project`
- `TEC Project`

**Fix Options**:

**Option 1 - Remove "Generator" from dropdown**:
```python
# In create_search_interface.py, line ~310
record_types = format_dropdown_list([
    'BSC Party', 'BM Unit', 'NESO Project', 'TEC Project',
    # REMOVED: 'Generator', 'Supplier', 'Interconnector'
])
```

**Option 2 - Map to valid type**:
```javascript
// In search_interface.gs, line ~75
if (criteria.recordType === 'Generator') {
  args.push('--type "BM Unit"');
} else if (criteria.recordType === 'Supplier') {
  args.push('--type "BSC Party"');
} else if (criteria.recordType && criteria.recordType !== 'None' && criteria.recordType !== 'All') {
  args.push('--type "' + criteria.recordType + '"');
}
```

**Recommended**: Option 2 (preserve user-friendly names, map internally)

---

## 📁 Related Files

**Search Interface**:
- `search_interface.gs` - Apps Script (needs Generator fix)
- `create_search_interface.py` - Sheet creator (add GSP/DNO dropdowns)
- `advanced_search_tool_enhanced.py` - Search backend

**Analysis System**:
- `generate_analysis_report.py` - Report generator (needs graph/analysis params)
- `analysis_report_generator.gs` - Current Analysis sheet script

**Data Tables**:
- `bmu_registration_data` - BMU details, GSP, DNO (via postcode lookup)
- `neso_dno_reference` - DNO operators
- `dim_party` - Party/organization data

---

*Last Updated: December 31, 2025*
*For implementation, see: SEARCH_INTERFACE_IMPLEMENTATION_COMPLETE.md*

---

## 📊 TODO #31: Diagnose & Fix API/Search Performance Issues ⚠️ HIGH PRIORITY

**Status**: ⏳ NOT STARTED  
**Priority**: HIGH - Search taking >10s

**Problem**: API calls or search execution taking too long

**Quick Diagnosis**:
```bash
# Test search speed
time python3 advanced_search_tool_enhanced.py --org "Flexitricity Limited"

# Test API endpoint  
time curl -X POST http://localhost:5002/search -H "Content-Type: application/json" -d '{"organization": "Flexitricity Limited"}'
```

**Likely Bottlenecks**:
1. BigQuery full table scan (2,718 rows)
2. Python script startup time
3. No result caching

**Quick Fixes**:
- Add @lru_cache to search functions
- Preload BMU data to local SQLite
- Only SELECT needed columns in BigQuery

**Target Performance**: <5s total

---
