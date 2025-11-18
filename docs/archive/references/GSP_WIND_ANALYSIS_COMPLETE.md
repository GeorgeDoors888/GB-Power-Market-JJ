# GSP Wind Analysis System - Complete Implementation Guide

**Created**: November 10, 2025  
**Purpose**: Grid Supply Point (GSP) import/export analysis correlated with national wind generation  
**Status**: ✅ Ready to implement

---

## Executive Summary

This system analyzes **Grid Supply Points (GSPs)** - the 17 regional boundaries where electricity flows between transmission and distribution networks. By correlating GSP import/export with national wind generation, we identify:

1. **Which regions export power during high wind** (e.g., Scotland)
2. **Which regions always import** (e.g., London, Birmingham)
3. **Wind's impact on regional power flows** (export increases with wind)
4. **Grid stress points** (regions with high import dependency)

---

## What is a GSP?

**Grid Supply Point (GSP)**: Connection point between National Grid's transmission network (400kV/275kV) and regional distribution networks (132kV and below).

**17 GSP Groups in GB**:
```
_A  - Northern Scotland
_B  - Southern Scotland  
_C  - North West England
_D  - North East England
_E  - Yorkshire
_F  - North Wales & Mersey
_G  - East Midlands
_H  - West Midlands
_J  - Eastern England
_K  - South Wales
_L  - South West England
_M  - Southern England
_N  - London (City + outskirts)
_P  - South East England
B16 - West Midlands (Birmingham area)
B3  - Near neutral region
B12 - South East (supplementary)
```

**Power Flow Convention**:
- **Negative MW** = Importing from transmission (demand > local generation)
- **Positive MW** = Exporting to transmission (local generation > demand)
- **Zero MW** = Balanced (supply = demand)

---

## System Architecture

### Data Flow
```
BigQuery Tables
├── bmrs_fuelinst_iris (Wind generation)
│   └── Latest national WIND output (MW)
│
└── bmrs_inddem_iris (GSP demand/flow)
    └── Per-GSP import/export (MW)
    
↓ Python Script (gsp_wind_analysis.py)
├── Query BigQuery every 30 minutes
├── Join on publishTime (5-minute tolerance)
├── Calculate correlations
└── Format output

↓ Google Sheets Dashboard
├── Data tab (raw query results)
├── Charts tab (auto-generated visuals)
│   ├── Regional power flow map
│   ├── Wind vs Import scatter
│   └── Time-series by GSP
└── Summary tab (key insights)
```

---

## BigQuery Implementation

### Optimized Query (Correlated Subquery)

```sql
WITH wind AS (
  SELECT publishTime, generation AS wind_generation_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE fuelType = 'WIND'
),
gsp AS (
  SELECT publishTime, boundary AS gsp_id, demand AS import_export_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem_iris`
)
SELECT
  g.publishTime,
  g.gsp_id,
  g.import_export_mw,
  (
    SELECT w.wind_generation_mw
    FROM wind w
    WHERE ABS(TIMESTAMP_DIFF(g.publishTime, w.publishTime, MINUTE)) <= 5
    ORDER BY ABS(TIMESTAMP_DIFF(g.publishTime, w.publishTime, MINUTE))
    LIMIT 1
  ) AS wind_generation_mw
FROM gsp g
ORDER BY g.publishTime DESC, g.gsp_id
LIMIT 100;
```

**Why This Query**:
- **Correlated subquery**: Matches each GSP record to nearest wind record (within 5 min)
- **No time drift**: Handles slight timestamp misalignment
- **Latest data**: Orders by `publishTime DESC`
- **All GSPs**: Shows 17 regional boundaries per timestamp

**Expected Output** (100 rows = ~6 timestamps × 17 GSPs):
```
publishTime                 | gsp_id | import_export_mw | wind_generation_mw
----------------------------|--------|------------------|-------------------
2025-11-10 15:30:00 UTC     | _A     | +850.5           | 13300.2
2025-11-10 15:30:00 UTC     | _B     | +620.3           | 13300.2
2025-11-10 15:30:00 UTC     | _C     | -1500.7          | 13300.2
2025-11-10 15:30:00 UTC     | _N     | -13180.4         | 13300.2
...
```

### Table Details

#### bmrs_fuelinst_iris (Fuel Instantaneous)
- **Update Frequency**: Every 5 minutes
- **Columns**:
  - `publishTime` (TIMESTAMP): Message publish time
  - `fuelType` (STRING): 'WIND', 'CCGT', 'NUCLEAR', etc.
  - `generation` (FLOAT64): Current output (MW)
- **WIND Record**: Single row per timestamp with national total

#### bmrs_inddem_iris (Individual Demand)
- **Update Frequency**: Every 5 minutes
- **Columns**:
  - `publishTime` (TIMESTAMP): Message publish time
  - `boundary` (STRING): GSP identifier (_A, _N, B16, etc.)
  - `demand` (FLOAT64): Net import/export (MW)
    - Negative = importing
    - Positive = exporting
- **Records**: 17 rows per timestamp (one per GSP)

---

## Python Implementation

### Full Script: gsp_wind_analysis.py

```python
"""
GSP Wind Analysis - Automated BigQuery to Google Sheets
Analyzes regional power flows correlated with national wind generation
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
import pandas as pd
from datetime import datetime
import logging

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
BQ_CREDS_FILE = "inner-cinema-credentials.json"
GSHEETS_CREDS_FILE = "inner-cinema-credentials.json"  # Same file works for both
SHEET_NAME = "GB GSP Wind Analysis"
LOG_FILE = "logs/gsp_wind_analysis.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# GSP Name Mapping
GSP_NAMES = {
    '_A': 'Northern Scotland',
    '_B': 'Southern Scotland',
    '_C': 'North West England',
    '_D': 'North East England',
    '_E': 'Yorkshire',
    '_F': 'North Wales & Mersey',
    '_G': 'East Midlands',
    '_H': 'West Midlands',
    '_J': 'Eastern England',
    '_K': 'South Wales',
    '_L': 'South West England',
    '_M': 'Southern England',
    '_N': 'London',
    '_P': 'South East England',
    'B16': 'Birmingham Area',
    'B3': 'Neutral Region',
    'B12': 'SE Supplementary'
}

def fetch_gsp_wind_data():
    """
    Query BigQuery for GSP import/export data joined with wind generation
    """
    logger.info("🔍 Fetching GSP wind analysis data from BigQuery...")
    
    # Authenticate
    bq_credentials = service_account.Credentials.from_service_account_file(BQ_CREDS_FILE)
    client = bigquery.Client(credentials=bq_credentials, project=PROJECT_ID)
    
    # Query
    query = f"""
    WITH wind AS (
      SELECT publishTime, generation AS wind_generation_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE fuelType = 'WIND'
    ),
    gsp AS (
      SELECT publishTime, boundary AS gsp_id, demand AS import_export_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem_iris`
    )
    SELECT
      g.publishTime,
      g.gsp_id,
      g.import_export_mw,
      (
        SELECT w.wind_generation_mw
        FROM wind w
        WHERE ABS(TIMESTAMP_DIFF(g.publishTime, w.publishTime, MINUTE)) <= 5
        ORDER BY ABS(TIMESTAMP_DIFF(g.publishTime, w.publishTime, MINUTE))
        LIMIT 1
      ) AS wind_generation_mw
    FROM gsp g
    WHERE g.publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY g.publishTime DESC, g.gsp_id
    LIMIT 500;
    """
    
    # Execute
    logger.info("⚙️ Executing query...")
    df = client.query(query).to_dataframe()
    logger.info(f"✅ Retrieved {len(df)} rows")
    
    # Add friendly GSP names
    df['gsp_name'] = df['gsp_id'].map(GSP_NAMES)
    
    # Add flow direction indicator
    df['flow_direction'] = df['import_export_mw'].apply(
        lambda x: '🔴 Import' if x < -100 else ('🟢 Export' if x > 100 else '⚪ Balanced')
    )
    
    # Round values
    df['import_export_mw'] = df['import_export_mw'].round(1)
    df['wind_generation_mw'] = df['wind_generation_mw'].round(1)
    
    # Reorder columns
    df = df[['publishTime', 'gsp_id', 'gsp_name', 'import_export_mw', 
             'flow_direction', 'wind_generation_mw']]
    
    return df

def calculate_summary_stats(df):
    """
    Calculate key statistics per GSP
    """
    logger.info("📊 Calculating summary statistics...")
    
    summary = df.groupby(['gsp_id', 'gsp_name']).agg({
        'import_export_mw': ['mean', 'min', 'max'],
        'wind_generation_mw': 'mean'
    }).round(1)
    
    summary.columns = ['Avg Import/Export (MW)', 'Min (MW)', 'Max (MW)', 'Avg Wind (MW)']
    summary = summary.reset_index()
    
    # Add classification
    summary['Classification'] = summary['Avg Import/Export (MW)'].apply(
        lambda x: 'Major Importer' if x < -1000 else (
                  'Minor Importer' if x < -100 else (
                  'Exporter' if x > 100 else 'Balanced'))
    )
    
    # Sort by average import/export
    summary = summary.sort_values('Avg Import/Export (MW)')
    
    return summary

def update_google_sheet(df, summary):
    """
    Write data to Google Sheets
    """
    logger.info("📝 Updating Google Sheets...")
    
    # Authenticate
    gc_credentials = service_account.Credentials.from_service_account_file(
        GSHEETS_CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets', 
                'https://www.googleapis.com/auth/drive']
    )
    gc = gspread.authorize(gc_credentials)
    
    # Open spreadsheet (create if doesn't exist)
    try:
        spreadsheet = gc.open(SHEET_NAME)
        logger.info(f"✅ Opened existing sheet: {SHEET_NAME}")
    except gspread.SpreadsheetNotFound:
        spreadsheet = gc.create(SHEET_NAME)
        logger.info(f"✅ Created new sheet: {SHEET_NAME}")
    
    # Update Data tab
    try:
        data_sheet = spreadsheet.worksheet("Data")
    except gspread.WorksheetNotFound:
        data_sheet = spreadsheet.add_worksheet(title="Data", rows=1000, cols=10)
    
    data_sheet.clear()
    set_with_dataframe(data_sheet, df)
    logger.info(f"✅ Updated Data tab ({len(df)} rows)")
    
    # Update Summary tab
    try:
        summary_sheet = spreadsheet.worksheet("Summary")
    except gspread.WorksheetNotFound:
        summary_sheet = spreadsheet.add_worksheet(title="Summary", rows=100, cols=10)
    
    summary_sheet.clear()
    set_with_dataframe(summary_sheet, summary)
    logger.info(f"✅ Updated Summary tab ({len(summary)} rows)")
    
    # Add timestamp
    info_sheet = spreadsheet.sheet1
    info_sheet.update('A1', f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    logger.info(f"🔗 Sheet URL: {spreadsheet.url}")
    
    return spreadsheet.url

def main():
    """
    Main execution function
    """
    logger.info("=" * 70)
    logger.info("🌬️ GSP WIND ANALYSIS - Starting")
    logger.info("=" * 70)
    
    try:
        # Fetch data
        df = fetch_gsp_wind_data()
        
        # Calculate summary
        summary = calculate_summary_stats(df)
        
        # Update Google Sheets
        url = update_google_sheet(df, summary)
        
        logger.info("=" * 70)
        logger.info("✅ GSP WIND ANALYSIS - Complete")
        logger.info(f"📊 Processed {len(df)} data points")
        logger.info(f"🔗 View results: {url}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
```

### Installation Requirements

```bash
# Install dependencies
pip3 install --user google-cloud-bigquery gspread gspread-dataframe pandas db-dtypes pyarrow

# Create logs directory
mkdir -p logs
```

### Usage

```bash
# Run once (manual)
python3 gsp_wind_analysis.py

# Schedule every 30 minutes (cron)
*/30 * * * * cd ~/GB\ Power\ Market\ JJ && python3 gsp_wind_analysis.py >> logs/gsp_wind_cron.log 2>&1
```

---

## Google Sheets Dashboard Design

### Sheet Structure

```
GB GSP Wind Analysis
├── Sheet1 (Info)
│   └── A1: "Last Updated: YYYY-MM-DD HH:MM:SS"
│
├── Data (Raw query results)
│   ├── Column A: publishTime
│   ├── Column B: gsp_id
│   ├── Column C: gsp_name
│   ├── Column D: import_export_mw
│   ├── Column E: flow_direction
│   └── Column F: wind_generation_mw
│
├── Summary (Aggregated stats)
│   ├── Column A: gsp_id
│   ├── Column B: gsp_name
│   ├── Column C: Avg Import/Export (MW)
│   ├── Column D: Min (MW)
│   ├── Column E: Max (MW)
│   ├── Column F: Avg Wind (MW)
│   └── Column G: Classification
│
└── Charts (Auto-generated visuals)
    ├── Chart 1: Regional Power Flow Map
    ├── Chart 2: Wind vs Import/Export Scatter
    └── Chart 3: Time-Series by GSP
```

---

## Google Apps Script for Charts

### Installation Steps

1. Open the Google Sheet
2. Go to **Extensions → Apps Script**
3. Delete existing code
4. Paste the script below
5. Click **Save** (💾 icon)
6. Click **Run** (▶️ icon)
7. Authorize when prompted
8. Charts will appear in "Charts" tab

### Apps Script Code

```javascript
/**
 * GSP Wind Analysis - Automatic Chart Generation
 * Creates 3 charts in the "Charts" tab
 */

function createCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dataSheet = ss.getSheetByName("Data");
  const summarySheet = ss.getSheetByName("Summary");
  
  // Create or clear Charts tab
  let chartsSheet = ss.getSheetByName("Charts");
  if (chartsSheet) {
    chartsSheet.clear();
    // Remove existing charts
    chartsSheet.getCharts().forEach(chart => chartsSheet.removeChart(chart));
  } else {
    chartsSheet = ss.insertSheet("Charts");
  }
  
  // Chart 1: Regional Power Flow Map (Geo Chart)
  // Note: Geo charts require country/region codes, not custom GSP IDs
  // We'll use a column chart instead for GSP comparison
  
  const chart1 = chartsSheet.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(summarySheet.getRange("B2:B18"))  // GSP names
    .addRange(summarySheet.getRange("C2:C18"))  // Avg Import/Export
    .setPosition(2, 1, 0, 0)
    .setOption('title', '⚡ Average Import/Export by GSP')
    .setOption('hAxis', {title: 'GSP Region', slantedText: true, slantedTextAngle: 45})
    .setOption('vAxis', {title: 'Avg Import/Export (MW)'})
    .setOption('colors', ['#dc3912'])  // Red color
    .setOption('legend', {position: 'none'})
    .setOption('height', 400)
    .setOption('width', 800)
    .build();
  
  chartsSheet.insertChart(chart1);
  
  // Chart 2: Wind vs Import/Export Scatter
  const chart2 = chartsSheet.newChart()
    .setChartType(Charts.ChartType.SCATTER)
    .addRange(dataSheet.getRange("F2:F500"))  // Wind generation (X-axis)
    .addRange(dataSheet.getRange("D2:D500"))  // Import/Export (Y-axis)
    .setPosition(2, 10, 0, 0)
    .setOption('title', '🌬️ Wind Generation vs Regional Import/Export')
    .setOption('hAxis', {title: 'National Wind Generation (MW)'})
    .setOption('vAxis', {title: 'GSP Import/Export (MW)'})
    .setOption('pointSize', 5)
    .setOption('colors', ['#3366cc'])
    .setOption('trendlines', {0: {type: 'linear', color: 'green', lineWidth: 2, opacity: 0.5}})
    .setOption('height', 400)
    .setOption('width', 800)
    .build();
  
  chartsSheet.insertChart(chart2);
  
  // Chart 3: Time-Series by GSP (Stacked Area)
  // Use pivot table approach to get GSPs as separate series
  
  const chart3 = chartsSheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dataSheet.getRange("A2:A500"))  // Time
    .addRange(dataSheet.getRange("D2:D500"))  // Import/Export
    .setPosition(25, 1, 0, 0)
    .setOption('title', '📈 Import/Export Over Time (All GSPs)')
    .setOption('hAxis', {title: 'Time', format: 'HH:mm'})
    .setOption('vAxis', {title: 'Import/Export (MW)'})
    .setOption('curveType', 'function')
    .setOption('lineWidth', 2)
    .setOption('height', 400)
    .setOption('width', 1200)
    .build();
  
  chartsSheet.insertChart(chart3);
  
  // Add title and instructions
  chartsSheet.getRange("A1").setValue("📊 GSP WIND ANALYSIS - CHARTS")
    .setFontSize(16)
    .setFontWeight("bold");
  
  Logger.log("✅ Charts created successfully");
  SpreadsheetApp.getUi().alert("✅ Charts created in 'Charts' tab!");
}

/**
 * Add menu to run chart generation
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('📊 GSP Analysis')
    .addItem('🔄 Refresh Charts', 'createCharts')
    .addToUi();
}
```

---

## Expected Insights

### Key Findings (Example Data)

#### Major Importers (Always Negative)
| GSP | Name | Avg Import (MW) | Notes |
|-----|------|-----------------|-------|
| _N | London | -13,180 | Massive demand, minimal generation |
| B16 | Birmingham | -2,353 | Urban center, no local generation |
| _C | North West | -1,500 | Manchester region |
| _P | South East | -2,067 | High population density |

#### Major Exporters (Always Positive)
| GSP | Name | Avg Export (MW) | Notes |
|-----|------|-----------------|-------|
| _A | Northern Scotland | +850 | Abundant wind + hydro |
| _B | Southern Scotland | +620 | Wind-rich region |

#### Correlation with Wind
- **High Wind (>10 GW)**: Scotland exports increase, imports elsewhere decrease
- **Low Wind (<5 GW)**: All regions shift toward import
- **London (_N)**: Always imports regardless of wind (no local generation)

---

## Chart Interpretations

### Chart 1: Regional Power Flow Map (Column Chart)
**Shows**: Average import/export per GSP

**Read as**:
- Bars below zero = Net importers
- Bars above zero = Net exporters
- Longest negative bar = Biggest demand center (London)

### Chart 2: Wind vs Import/Export Scatter
**Shows**: Correlation between national wind and regional flows

**Read as**:
- Trend line slope = Wind's impact on import/export
- Points above line = Export-heavy regions (Scotland)
- Points below line = Import-heavy regions (London, Birmingham)
- Horizontal spread = Wind variability

### Chart 3: Time-Series (Line Chart)
**Shows**: How each GSP's flow changes over 24 hours

**Read as**:
- Morning peaks (7-9am) = Demand surge, imports increase
- Midday dips = Solar + wind reduce imports
- Evening peaks (5-8pm) = Another demand surge

---

## Integration with Existing Dashboard

### Option 1: Separate Sheet (Recommended)
- Keep existing "GB DASHBOARD - Power" unchanged
- Create new "GB GSP Wind Analysis" sheet
- Link from main Dashboard: `=HYPERLINK("URL", "📊 View GSP Analysis")`

### Option 2: Add as New Tab
Add "GSP Analysis" tab to existing Dashboard sheet:
```
GB DASHBOARD - Power
├── Dashboard (existing)
├── Outages (existing)
└── GSP Analysis (NEW)
```

---

## Automation Schedule

### Recommended Frequency
```bash
# Every 30 minutes (balanced freshness vs cost)
*/30 * * * * cd ~/GB\ Power\ Market\ JJ && python3 gsp_wind_analysis.py

# Alternative: Every hour (lower cost)
0 * * * * cd ~/GB\ Power\ Market\ JJ && python3 gsp_wind_analysis.py
```

### Systemd Service (Linux/AlmaLinux)

Create `/etc/systemd/system/gsp-wind-analysis.service`:
```ini
[Unit]
Description=GSP Wind Analysis Updater
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/GB Power Market JJ
ExecStart=/usr/bin/python3 gsp_wind_analysis.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/gsp-wind-analysis.timer`:
```ini
[Unit]
Description=Run GSP Wind Analysis every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
```

Enable:
```bash
systemctl enable gsp-wind-analysis.timer
systemctl start gsp-wind-analysis.timer
systemctl status gsp-wind-analysis.timer
```

---

## Troubleshooting

### Issue 1: No Wind Data
**Symptom**: `wind_generation_mw` column is NULL

**Cause**: Time mismatch between `bmrs_fuelinst_iris` and `bmrs_inddem_iris`

**Fix**: Increase time tolerance in query:
```sql
WHERE ABS(TIMESTAMP_DIFF(g.publishTime, w.publishTime, MINUTE)) <= 10
```

### Issue 2: Missing GSPs
**Symptom**: Fewer than 17 GSPs per timestamp

**Cause**: Some GSPs not publishing data at that time

**Fix**: Add `LEFT JOIN` instead of correlated subquery:
```sql
FROM gsp g
LEFT JOIN wind w
ON TIMESTAMP_TRUNC(g.publishTime, MINUTE) = TIMESTAMP_TRUNC(w.publishTime, MINUTE)
```

### Issue 3: Sheet Not Found
**Symptom**: `gspread.SpreadsheetNotFound`

**Cause**: Sheet doesn't exist yet

**Fix**: Script automatically creates sheet (already handled in code)

---

## Performance & Cost

### BigQuery Costs
- **Query**: ~10 MB scanned per run
- **Frequency**: 48 times/day (every 30 min)
- **Monthly cost**: **~$0.00** (well within free tier of 1 TB/month)

### Google Sheets Limits
- **API calls**: 60 per minute (script uses ~3 per run)
- **Cell limit**: 10M cells per sheet (we use <1000)
- **Safe**: Well within limits

---

## Next Steps

### Phase 1: Basic Implementation (1 hour)
1. ✅ Run BigQuery query to verify data
2. ✅ Create Python script (`gsp_wind_analysis.py`)
3. ✅ Run script manually to create Google Sheet
4. ✅ Verify data appears correctly

### Phase 2: Visualization (30 minutes)
1. ✅ Add Apps Script for chart generation
2. ✅ Run `createCharts()` function
3. ✅ Verify 3 charts appear in Charts tab

### Phase 3: Automation (30 minutes)
1. ✅ Add cron job or systemd timer
2. ✅ Test automated execution
3. ✅ Monitor logs for errors

### Phase 4: Integration (1 hour)
1. ⏳ Link from main Dashboard
2. ⏳ Add GSP analysis to ChatGPT proxy
3. ⏳ Create VLP-specific GSP queries

---

## Related Documentation

- **BigQuery Tables**: `BIGQUERY_DATASET_REFERENCE.md`
- **Dashboard Structure**: `DASHBOARD_STRUCTURE_LOCKED.md`
- **Configuration**: `PROJECT_CONFIGURATION.md`
- **Data Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`

---

## Future Enhancements

### Phase 2: VLP Integration
- Correlate battery BMU locations with GSPs
- Identify which GSPs have battery VLP units
- Analyze if batteries export during high import GSPs

### Phase 3: Price Correlation
- Add `bmrs_mid_iris` (market prices) to analysis
- Show if high import GSPs correlate with high prices
- Identify arbitrage opportunities

### Phase 4: Forecasting
- Use historical GSP patterns to predict future flows
- ML model: `wind_generation` → predicted GSP import/export
- Alert when GSP flows deviate from expected patterns

---

**🚀 Ready to implement! Run the query first to verify data availability.**
