# 🏗️ Architecture Overview

Complete system architecture documentation for GB-Power-Market-JJ - BESS Dashboard & Energy Analysis System.

---

## 📋 Table of Contents

- [System Architecture](#system-architecture)
- [Component Design](#component-design)
- [Data Flow](#data-flow)
- [Integration Points](#integration-points)
- [Storage Architecture](#storage-architecture)
- [Security Architecture](#security-architecture)
- [Performance Considerations](#performance-considerations)
- [Scalability](#scalability)

---

## 🎯 System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                          │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Google Sheets Dashboard V2                      │   │
│  │  Spreadsheet ID: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc│   │
│  │                                                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ BESS Sheet   │  │ Control Panel│  │ Cost Table   │      │   │
│  │  │ (285 rows)   │  │ (K4:N46)     │  │ (A250:F285)  │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  │                                                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ Time Period  │  │ HH Profile   │  │ DNO Data     │      │   │
│  │  │ Dropdown(L6) │  │ (Rows 22-69) │  │ (B6:H6)      │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          AUTOMATION LAYER                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │           Google Apps Script (V8 Runtime)                    │   │
│  │           Script ID: 1svUewU3Q0n77ku0VJgtJ3GquVsSRii...     │   │
│  │                                                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ Menu System  │  │ Auto-Triggers│  │ Validators   │      │   │
│  │  │ (8 items)    │  │ (onEdit)     │  │ (MPAN/Post)  │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  │                                                               │   │
│  │  Functions: refreshDnoLookup(), calculatePpaArbitrage(),     │   │
│  │            generateHhProfile(), validateMpan()               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Python Analysis Engine                     │   │
│  │                      Python 3.9+                             │   │
│  │                                                               │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ Core Analysis Scripts (1,950 lines)                  │   │   │
│  │  │                                                        │   │   │
│  │  │  • calculate_ppa_arbitrage.py (500L)                 │   │   │
│  │  │    └─ 24-month profitability analysis                │   │   │
│  │  │    └─ 34,560 settlement periods                      │   │   │
│  │  │    └─ Time-band statistics                           │   │   │
│  │  │                                                        │   │   │
│  │  │  • calculate_bess_revenue.py (580L)                  │   │   │
│  │  │    └─ 5 revenue streams                              │   │   │
│  │  │    └─ SO payment calculations                        │   │   │
│  │  │    └─ Capacity market integration                    │   │   │
│  │  │                                                        │   │   │
│  │  │  • visualize_ppa_costs.py (433L)                     │   │   │
│  │  │    └─ Stacked bar charts (1,440 SPs)                │   │   │
│  │  │    └─ 7-component cost breakdown                     │   │   │
│  │  │    └─ PNG export (matplotlib)                        │   │   │
│  │  │                                                        │   │   │
│  │  │  • update_bess_dashboard.py (437L)                   │   │   │
│  │  │    └─ Time period controls                           │   │   │
│  │  │    └─ Cost breakdown table                           │   │   │
│  │  │    └─ Dashboard formatting                           │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ Utility Scripts (420 lines)                          │   │   │
│  │  │                                                        │   │   │
│  │  │  • generate_hh_profile.py (180L)                     │   │   │
│  │  │  • calculate_energy_costs.py (240L)                  │   │   │
│  │  │  • deploy_bess_complete.py                           │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA ACCESS LAYER                            │
│                                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │   Google APIs        │  │   Vercel Proxy       │                │
│  │                      │  │                      │                │
│  │  • Sheets API v4     │  │  Edge Functions      │                │
│  │    gspread 6.2.1     │  │  CORS handling       │                │
│  │                      │  │  Rate limiting       │                │
│  │  • BigQuery API      │  │  Request caching     │                │
│  │    bq 3.25.0         │  │                      │                │
│  │                      │  │  gb-power-market-    │                │
│  │  • Drive API         │  │  jj.vercel.app       │                │
│  │    OAuth2 SA         │  │                      │                │
│  └──────────────────────┘  └──────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA STORAGE LAYER                          │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Google BigQuery Data Warehouse                  │   │
│  │              Project: inner-cinema-476211-u9                 │   │
│  │              Dataset: uk_energy_prod                         │   │
│  │              Location: EU (multi-region)                     │   │
│  │                                                               │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ Tables:                                              │   │   │
│  │  │                                                        │   │   │
│  │  │  • balancing_prices                                  │   │   │
│  │  │    └─ settlement_date, settlement_period, ssp        │   │   │
│  │  │    └─ 2+ years history (~35,000 rows)               │   │   │
│  │  │    └─ Updated: Real-time via Elexon BMRS            │   │   │
│  │  │                                                        │   │   │
│  │  │  • duos_tariff_rates                                 │   │   │
│  │  │    └─ dno_code, voltage_level, time_band, rate      │   │   │
│  │  │    └─ 23 DNOs × 3 voltages × 3 bands = 207 rows     │   │   │
│  │  │    └─ Updated: Annually (April)                      │   │   │
│  │  │                                                        │   │   │
│  │  │  • dno_duos_rates                                    │   │   │
│  │  │    └─ Time-band definitions (RED/AMBER/GREEN)        │   │   │
│  │  │    └─ Hour ranges by DNO                             │   │   │
│  │  │                                                        │   │   │
│  │  │  • neso_dno_reference                                │   │   │
│  │  │    └─ mpan_id, dno_key, dno_name, gsp_group         │   │   │
│  │  │    └─ 14 rows (MPAN 10-23)                           │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Google Sheets Storage                           │   │
│  │                                                               │   │
│  │  • Dashboard V2: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc│   │
│  │    └─ BESS Sheet (285 rows × 20 columns)                    │   │
│  │    └─ Live updates via gspread                              │   │
│  │    └─ Formatted cells, data validation, conditional format  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Local File Storage                              │   │
│  │                                                               │   │
│  │  • ppa_cost_analysis.png (664 KB)                           │   │
│  │  • ppa_cost_summary.png (477 KB)                            │   │
│  │  • logs/*.log (rotating, 7-day retention)                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Component Design

### 1. Dashboard Layer (Google Sheets)

**Purpose:** User interface and data display

**Components:**
- **BESS Sheet** - Main data sheet (285 rows)
- **Control Panel** - User inputs (K4:N46)
- **Cost Table** - Rate reference (A250:F285)
- **Results Areas** - Analysis outputs (Rows 90+)

**Key Cells:**
| Cell | Purpose | Type | Example |
|------|---------|------|---------|
| A6 | Postcode | Input | "SW2 5UP" |
| B6 | MPAN ID | Dropdown | 14 (NGED-WM) |
| A10 | Voltage | Dropdown | HV |
| B10:D10 | DUoS Rates | Auto-filled | 1.764, 0.205, 0.011 |
| B17:B19 | Battery kW | Input | 500, 1500, 2500 |
| B21 | PPA Price | Input | 150 |
| L6 | Time Period | Dropdown | 1 Year |

**Data Validation:**
- MPAN: List from NESO reference (10-23)
- Voltage: List ("LV", "HV", "EHV")
- Time Period: List ("All Data", "Non-COVID Data", "Since SLP Data", "1 Year", "2 Year")

### 2. Apps Script Layer

**Purpose:** Automation, validation, menu system

**Architecture:**
```javascript
// Main Entry Points
function onOpen() { /* Creates menu on sheet open */ }
function onEdit(e) { /* Triggers on cell edit */ }

// Menu Functions
function refreshDnoLookup() { /* DNO data from BigQuery */ }
function calculatePpaArbitrage() { /* Prompt for Python script */ }
function generateHhProfile() { /* 48 half-hourly periods */ }
function validateMpan() { /* MPAN format check */ }
function validatePostcode() { /* UK postcode regex */ }
function showStatus() { /* Display current config */ }
function showHelp() { /* HTML modal with docs */ }

// Helper Functions
function updateDuosRates(dnoShortCode) { /* Populate B10:D10 */ }
function parseTimeBand(bandStr) { /* Parse "16:00-19:30" */ }
```

**Event Triggers:**
- `onOpen()` - Sheet loads → Create menu
- `onEdit()` - Cell B6 changes → `refreshDnoLookup()`
- `onEdit()` - Cell A10 changes → `updateDuosRates()`

**External API Calls:**
```javascript
// Vercel Proxy for BigQuery
POST https://gb-power-market-jj.vercel.app/api/proxy-v2
Body: {
  "query": "SELECT ... FROM neso_dno_reference WHERE mpan_id = '14'"
}
```

### 3. Python Analysis Engine

**Purpose:** Heavy computation, data processing, visualization

**Module Structure:**
```python
# calculate_ppa_arbitrage.py
├─ get_system_prices(start_date, end_date)  # BigQuery → SSP data
├─ calculate_total_cost(ssp, time_band)     # Cost components
├─ analyze_profitability(prices, ppa_price) # Margin analysis
├─ generate_monthly_stats(results)          # Aggregations
└─ write_to_sheet(summary, details)         # gspread output

# calculate_bess_revenue.py
├─ calculate_arbitrage_revenue()   # Buy GREEN, sell RED
├─ calculate_so_payments()         # FFR, DCR, DM, DR, BID, BOD
├─ calculate_capacity_market()     # £6/kW/year
├─ calculate_ppa_revenue()         # Contract × discharge
└─ write_revenue_breakdown()       # Rows 170-205

# visualize_ppa_costs.py
├─ get_system_prices()             # 30 days data
├─ calculate_cost_components()     # 7 components per SP
├─ create_stacked_bar_chart()      # matplotlib figure
├─ create_summary_charts()         # 4-chart grid
└─ export_to_png()                 # Save files

# update_bess_dashboard.py
├─ create_time_period_dropdown()   # L6 dropdown
├─ create_cost_breakdown_table()   # A250:F285
├─ create_period_definitions()     # K8:N25
└─ add_usage_instructions()        # K27:N46
```

**Dependency Graph:**
```
gspread 6.2.1
  └─ google-auth 2.35.0
       └─ google-auth-oauthlib 1.2.1

google-cloud-bigquery 3.25.0
  └─ google-api-core
       └─ google-auth

pandas 2.2.3
  └─ numpy 2.1.3

matplotlib 3.9.2
  └─ pillow
  └─ numpy

seaborn 0.13.2
  └─ matplotlib
  └─ pandas
```

### 4. Data Access Layer

**Google APIs:**
```python
# Authentication
from google.oauth2.service_account import Credentials

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery'
]

credentials = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=scopes
)

# Google Sheets
import gspread
client = gspread.authorize(credentials)
sheet = client.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
bess = sheet.worksheet('BESS')

# BigQuery
from google.cloud import bigquery
bq_client = bigquery.Client(
    credentials=credentials,
    project='inner-cinema-476211-u9'
)
```

**Vercel Proxy:**
```javascript
// Edge Function (Vercel)
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  // Parse BigQuery request
  const { query } = req.body;
  
  // Execute query
  const results = await bigQueryClient.query(query);
  
  // Return formatted response
  return res.json({ rows: results });
}
```

---

## 🔄 Data Flow

### Flow 1: DNO Lookup

```
1. USER ACTION
   └─ Enter MPAN ID in B6: "14"
        ▼
2. TRIGGER
   └─ onEdit() detects change in B6
        ▼
3. APPS SCRIPT
   └─ refreshDnoLookup() executes
        ├─ Read MPAN from B6
        ├─ Validate range (10-23)
        └─ Build BigQuery query
             ▼
4. API CALL
   └─ POST to Vercel proxy
        ├─ Query: SELECT * FROM neso_dno_reference WHERE mpan_id = '14'
        └─ Authentication headers
             ▼
5. BIGQUERY
   └─ Execute query in uk_energy_prod dataset
        ├─ Table: neso_dno_reference
        └─ Return: {mpan_id: "14", dno_key: "WMID", dno_name: "NGED-WM", ...}
             ▼
6. RESPONSE
   └─ Vercel proxy returns JSON
        ├─ Parse response data
        └─ Extract DNO fields
             ▼
7. WRITE TO SHEET
   └─ Update B6:H6
        ├─ B6: "14"
        ├─ C6: "WMID"
        ├─ D6: "NGED-WM"
        ├─ E6: "NGED"
        ├─ F6: "10T"
        ├─ G6: "14"
        └─ H6: "West Midlands"
             ▼
8. AUTO-UPDATE DUOS
   └─ updateDuosRates("NGED")
        ├─ Read voltage from A10: "HV"
        ├─ Lookup rates: [1.764, 0.205, 0.011]
        └─ Update B10:D10
             ▼
9. STATUS UPDATE
   └─ A4: "✅ DNO data updated successfully | Updated: 14:32:15"
```

### Flow 2: PPA Arbitrage Analysis

```
1. USER ACTION
   └─ Terminal: python3 calculate_ppa_arbitrage.py
        ▼
2. SCRIPT INITIALIZATION
   └─ Import libraries (gspread, bigquery, pandas)
        ├─ Load credentials
        ├─ Connect to Dashboard V2
        └─ Read configuration
             ├─ PPA price from B21: £150/MWh
             ├─ Time period from L6: "1 Year"
             └─ DUoS rates from B10:D10
                  ▼
3. CALCULATE DATE RANGE
   └─ Time period: "1 Year"
        ├─ Start: 2024-12-01
        ├─ End: 2025-11-30
        └─ Expected SPs: 365 days × 48 SPs = 17,520
             ▼
4. FETCH SSP DATA
   └─ BigQuery query:
        SELECT settlement_date, settlement_period, ssp
        FROM balancing_prices
        WHERE settlement_date BETWEEN '2024-12-01' AND '2025-11-30'
        ORDER BY settlement_date, settlement_period
             ├─ Query execution time: ~5 seconds
             ├─ Rows returned: 17,520
             └─ Data size: ~1.2 MB
                  ▼
5. PROCESS DATA
   └─ For each settlement period (17,520 iterations):
        ├─ Determine time band (RED/AMBER/GREEN)
        │    └─ Based on settlement_period (1-48)
        ├─ Calculate DUoS cost
        │    ├─ RED: £17.64/MWh
        │    ├─ AMBER: £2.05/MWh
        │    └─ GREEN: £0.11/MWh
        ├─ Add fixed levies
        │    ├─ RO: £61.90/MWh
        │    ├─ CCL: £7.75/MWh
        │    ├─ FiT: £11.50/MWh
        │    ├─ BSUoS: £4.50/MWh
        │    └─ TNUoS: £12.50/MWh
        ├─ Calculate total cost
        │    └─ SSP + DUoS + Fixed levies
        └─ Compare vs PPA price
             └─ Profitable if: total_cost < ppa_price
                  ▼
6. AGGREGATE RESULTS
   └─ Calculate statistics:
        ├─ Overall profitability: 51.2% (8,970 / 17,520 SPs)
        ├─ By time band:
        │    ├─ GREEN: 93.5% profitable (+£19.33/MWh avg)
        │    ├─ AMBER: 29.3% profitable (-£7.43/MWh avg)
        │    └─ RED: 0.0% profitable (-£38.01/MWh avg)
        └─ By month:
             ├─ Best: June 73.1%
             ├─ Worst: Feb 31.8%
             └─ Variation: 41.3 percentage points
                  ▼
7. GENERATE OUTPUT
   └─ Create summary tables:
        ├─ Overall summary (10 rows)
        ├─ Time band analysis (15 rows)
        ├─ Monthly trends (12 rows)
        └─ Top 30 opportunities (30 rows)
             ▼
8. WRITE TO SHEET
   └─ Update Dashboard V2:
        ├─ Clear rows 90-162
        ├─ Write headers (row 90)
        ├─ Write summary (rows 92-102)
        ├─ Write time band stats (rows 104-119)
        ├─ Write monthly data (rows 121-133)
        ├─ Write top opportunities (rows 135-165)
        └─ Apply formatting
             ├─ Headers: Bold, background color
             ├─ Numbers: Currency format
             └─ Percentages: Percentage format
                  ▼
9. COMPLETION
   └─ Print summary:
        ├─ "✅ Analysis complete"
        ├─ "   Periods analyzed: 17,520"
        ├─ "   Profitable: 8,970 (51.2%)"
        ├─ "   Results written to rows 90-162"
        └─ "   Execution time: 58.3 seconds"
```

### Flow 3: Chart Generation

```
1. SCRIPT EXECUTION
   └─ python3 visualize_ppa_costs.py
        ▼
2. DATA COLLECTION
   └─ Fetch 30 days of SSP data (1,440 SPs)
        ├─ BigQuery query
        └─ Calculate cost components for each SP
             ├─ SSP (variable)
             ├─ DUoS (time-band variable)
             ├─ RO (£61.90 fixed)
             ├─ CCL (£7.75 fixed)
             ├─ FiT (£11.50 fixed)
             ├─ BSUoS (£4.50 fixed)
             └─ TNUoS (£12.50 fixed)
                  ▼
3. CREATE MAIN CHART
   └─ matplotlib.pyplot.figure(figsize=(24, 10))
        ├─ 2 subplots (main + daily avg)
        ├─ Stacked bar chart (1,440 bars)
        ├─ Color scheme:
        │    ├─ SSP: #3498db (blue)
        │    ├─ DUoS: #9b59b6 (purple)
        │    ├─ RO: #e67e22 (orange)
        │    ├─ CCL: #e74c3c (red)
        │    ├─ FiT: #2ecc71 (green)
        │    ├─ BSUoS: #e74c3c (red)
        │    └─ TNUoS: #8b4513 (brown)
        └─ Time-band backgrounds:
             ├─ RED: Light red overlay
             ├─ AMBER: Light yellow overlay
             └─ GREEN: Light green overlay
                  ▼
4. CREATE SUMMARY CHARTS
   └─ 2×2 grid (4 charts)
        ├─ Time band comparison (stacked bars)
        ├─ Component pie chart
        ├─ Hourly cost profile (line chart)
        └─ Cost distribution (histogram)
             ▼
5. EXPORT TO PNG
   └─ Save files:
        ├─ ppa_cost_analysis.png (664 KB)
        │    └─ DPI: 300, format: PNG
        └─ ppa_cost_summary.png (477 KB)
             └─ DPI: 300, format: PNG
                  ▼
6. WRITE STATISTICS
   └─ Update rows 210-245:
        ├─ Cost statistics
        ├─ Time-band averages
        ├─ Component breakdown
        └─ Optimization recommendations
```

---

## 🔌 Integration Points

### 1. Elexon BMRS (via BigQuery)
- **Endpoint:** BigQuery table `balancing_prices`
- **Update Frequency:** Real-time (5-minute delay)
- **Data Fields:** settlement_date, settlement_period, ssp, sbp, ssp_volume
- **Usage:** PPA arbitrage analysis, revenue calculations

### 2. NESO DNO Reference
- **Endpoint:** BigQuery table `neso_dno_reference`
- **Update Frequency:** Quarterly
- **Data Fields:** mpan_id, dno_key, dno_name, gsp_group_id
- **Usage:** DNO lookup, MPAN validation

### 3. DUoS Tariff Rates
- **Endpoint:** BigQuery table `duos_tariff_rates`
- **Update Frequency:** Annually (April)
- **Data Fields:** dno_code, voltage_level, time_band, rate_p_per_kwh
- **Usage:** Cost calculations, time-band optimization

### 4. Google Sheets API
- **Version:** v4
- **Library:** gspread 6.2.1
- **Rate Limits:** 100 requests/100 seconds/user
- **Batch Operations:** Update up to 5000 cells in single request

### 5. Vercel Edge Functions
- **Purpose:** CORS proxy for BigQuery from Apps Script
- **Endpoint:** `https://gb-power-market-jj.vercel.app/api/proxy-v2`
- **Method:** POST
- **Authentication:** Header-based token

---

## 💾 Storage Architecture

### BigQuery Schema

```sql
-- balancing_prices table
CREATE TABLE uk_energy_prod.balancing_prices (
  settlement_date DATE NOT NULL,
  settlement_period INT64 NOT NULL,
  ssp FLOAT64,              -- System Sell Price (£/MWh)
  sbp FLOAT64,              -- System Buy Price (£/MWh)
  ssp_volume FLOAT64,       -- Volume (MWh)
  import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY settlement_date
CLUSTER BY settlement_period;

-- duos_tariff_rates table
CREATE TABLE uk_energy_prod.duos_tariff_rates (
  dno_code STRING NOT NULL,
  voltage_level STRING NOT NULL,  -- LV, HV, EHV
  time_band STRING NOT NULL,      -- RED, AMBER, GREEN
  rate_p_per_kwh FLOAT64,
  effective_from DATE,
  effective_to DATE
);

-- neso_dno_reference table
CREATE TABLE uk_energy_prod.neso_dno_reference (
  mpan_id STRING PRIMARY KEY,
  dno_key STRING,
  dno_name STRING,
  dno_short_code STRING,
  market_participant_id STRING,
  gsp_group_id STRING,
  gsp_group_name STRING
);
```

### Google Sheets Schema

```
BESS Sheet Structure:
Row 1-3:    Headers & metadata
Row 4:      Status indicator
Row 5:      Blank
Row 6:      DNO data (A6:H6)
Row 7-9:    Blank
Row 10:     DUoS rates (A10:D10)
Row 11-12:  Blank
Row 13-14:  Time band definitions
Row 15-16:  Blank
Row 17-19:  Battery parameters (Min/Avg/Max kW)
Row 20:     Blank
Row 21:     PPA price
Row 22-69:  HH Profile (48 half-hourly periods)
Row 70-89:  Reserved
Row 90-162: PPA Arbitrage results (73 rows)
Row 163-169: Reserved
Row 170-205: Revenue breakdown (36 rows)
Row 206-209: Reserved
Row 210-245: Cost visualization stats (36 rows)
Row 246-249: Reserved
Row 250-285: Cost breakdown table (36 rows)
```

---

## 🔐 Security Architecture

### Authentication Flow

```
1. SERVICE ACCOUNT CREDENTIALS
   └─ File: inner-cinema-credentials.json
        ├─ Type: service_account
        ├─ Project: inner-cinema-476211-u9
        ├─ Email: bess-dashboard@inner-cinema-476211-u9.iam.gserviceaccount.com
        └─ Private Key: RSA 2048-bit
             ▼
2. OAUTH2 TOKEN GENERATION
   └─ google-auth library
        ├─ Scopes requested:
        │    ├─ https://www.googleapis.com/auth/spreadsheets
        │    ├─ https://www.googleapis.com/auth/drive
        │    └─ https://www.googleapis.com/auth/bigquery
        ├─ Token lifetime: 1 hour
        └─ Auto-refresh: Enabled
             ▼
3. API REQUEST
   └─ Include token in Authorization header
        ├─ Header: "Authorization: Bearer <token>"
        ├─ Request validation by Google
        └─ Permission check against IAM roles
             ▼
4. RESOURCE ACCESS
   └─ IAM roles:
        ├─ BigQuery Data Viewer
        ├─ BigQuery Job User
        └─ (Spreadsheet shared directly with service account email)
```

### Security Best Practices

1. **Credentials Storage**
   - ✅ Local file (not in git)
   - ✅ Added to .gitignore
   - ✅ Restricted file permissions (600)
   - ❌ Never commit to version control
   - ❌ Never share via email/Slack

2. **API Access**
   - ✅ Service account with minimal permissions
   - ✅ Separate service accounts per environment
   - ✅ Regular credential rotation (90 days)
   - ✅ API key restrictions (HTTP referrers, IP addresses)

3. **Data Protection**
   - ✅ BigQuery dataset encrypted at rest
   - ✅ HTTPS/TLS for all API calls
   - ✅ No PII in logs
   - ✅ Audit logging enabled

---

## ⚡ Performance Considerations

### Optimization Strategies

1. **BigQuery Queries**
   ```sql
   -- ✅ GOOD: Uses partition pruning
   SELECT * FROM balancing_prices
   WHERE settlement_date BETWEEN '2024-01-01' AND '2024-12-31'
   
   -- ❌ BAD: Full table scan
   SELECT * FROM balancing_prices
   WHERE EXTRACT(YEAR FROM settlement_date) = 2024
   ```

2. **Google Sheets Updates**
   ```python
   # ✅ GOOD: Batch update (1 API call)
   sheet.update('A1:Z100', values_2d_array, value_input_option='USER_ENTERED')
   
   # ❌ BAD: Individual updates (100 API calls)
   for row in range(1, 101):
       sheet.update_cell(row, 1, value)
   ```

3. **Pandas Operations**
   ```python
   # ✅ GOOD: Vectorized operations
   df['total_cost'] = df['ssp'] + df['duos'] + df['fixed_levies'].sum(axis=1)
   
   # ❌ BAD: Row-by-row iteration
   for idx, row in df.iterrows():
       df.at[idx, 'total_cost'] = row['ssp'] + row['duos'] + row['fixed_levies']
   ```

### Performance Metrics

| Operation | Current | Target | Notes |
|-----------|---------|--------|-------|
| BigQuery fetch (1Y) | 5.2s | <3s | Use clustering |
| Pandas processing | 12.8s | <10s | Optimize loops |
| Chart generation | 8.4s | <5s | Reduce DPI for draft |
| Sheets update | 3.6s | <2s | Batch operations |
| **Total (PPA Arbitrage)** | **58s** | **<45s** | **23% improvement target** |

---

## 📈 Scalability

### Current Limits

- **BigQuery:** 1TB data scanned/month (free tier)
- **Google Sheets:** 5M cells/spreadsheet
- **Apps Script:** 6 min execution time/trigger
- **Python Scripts:** Memory: 4GB, single-threaded

### Scaling Strategies

1. **Horizontal Scaling**
   - Multiple service accounts for parallel requests
   - Separate sheets for different battery systems
   - Distributed processing with multiprocessing

2. **Vertical Scaling**
   - Upgrade to BigQuery on-demand pricing
   - Use Google Sheets Add-on for larger datasets
   - Increase Python process memory allocation

3. **Caching**
   ```python
   # Cache BigQuery results locally
   cache_file = f'cache/ssp_data_{start}_{end}.pkl'
   if os.path.exists(cache_file):
       df = pd.read_pickle(cache_file)
   else:
       df = fetch_from_bigquery()
       df.to_pickle(cache_file)
   ```

---

**For implementation details, see:**
- [Installation Guide](INSTALLATION.md)
- [Apps Script Guide](APPS_SCRIPT_GUIDE.md)
- [API Reference](API_REFERENCE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
