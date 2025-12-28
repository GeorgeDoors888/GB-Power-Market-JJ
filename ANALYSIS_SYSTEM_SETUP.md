# Analysis Report System - Complete Setup Guide

**Status**: ✅ Fully Working
**Last Updated**: December 22, 2025
**Google Sheet**: [GB Energy Market Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)

---

## 📊 System Overview

Interactive report generation system for the Analysis sheet. Select data category, date range, and filters via dropdowns, then generate custom reports from BigQuery with one command.

**Key Features**:
- 8 data categories (Generation, Balancing, Pricing, System Ops, etc.)
- 10 report types (Dashboard, Trend Analysis, Time Series, etc.)
- 9 graph types (Line Chart, Bar Chart, Heatmap, etc.)
- Filter by fuel type (CCGT, WIND, NUCLEAR, etc.)
- Date range selection (last 90 days + next 7 days)
- Automatic date format handling (DD/MM/YYYY → YYYY-MM-DD)

---

## 🚀 Quick Start

### 1. Set Your Report Parameters

Open Analysis sheet and configure:

| Row | Field | Example Value |
|-----|-------|---------------|
| **B4** | From Date | 22/12/2025 |
| **D4** | To Date | 22/12/2025 |
| **B8** | Generation Type | CCGT |
| **B11** | Report Category | ⚡ Generation & Fuel Mix |
| **B12** | Report Type | Time Series Chart |
| **B13** | Graph Type | Line Chart (Time Series) |

### 2. Click CALCULATE Button

Located in Analysis sheet cell **B14**

### 3. Run Python Command

```bash
cd /home/george/GB-Power-Market-JJ
python3 generate_analysis_report.py
```

### 4. View Results

Results appear in **Analysis sheet, row 18+**

**Example output (CCGT today)**:
- 254 rows of generation data
- Columns: date, settlementPeriod, fuelType, generation_mw
- Time range: All 48 settlement periods for selected day

---

## 🔧 Installation & Setup

### Prerequisites

```bash
# Python packages
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas google-api-python-client

# Google Cloud credentials
# File: inner-cinema-credentials.json (already configured)
```

### Apps Script Setup

1. **Open Apps Script Editor**:
   - Google Sheets → Extensions → Apps Script

2. **Add CALCULATE Function**:
   - Copy code from: `/home/george/GB-Power-Market-JJ/ANALYSIS_DROPDOWNS.gs`
   - Paste into Apps Script editor
   - Save (Ctrl+S)

3. **Assign Button**:
   - Right-click CALCULATE button in Analysis sheet
   - Click: "Assign script"
   - Type: `CALCULATE`
   - Click OK

4. **Test**:
   - Click CALCULATE button
   - Should show report configuration dialog

---

## 📋 Report Categories

### ⚡ Generation & Fuel Mix
**Data Source**: `bmrs_fuelinst_iris`
**Metrics**: MW output by fuel type
**Filters**: Fuel type (CCGT, WIND, NUCLEAR, etc.)
**Use Case**: Track generation patterns, wind/solar output

**Example Query**:
```sql
SELECT date, settlementPeriod, fuelType, generation_mw
FROM bmrs_fuelinst_iris
WHERE settlementDate = '2025-12-22'
  AND fuelType = 'CCGT'
  AND generation > 0
```

### 💰 Balancing Mechanism (Trading)
**Data Source**: `boalf_with_prices`
**Metrics**: Acceptance prices (£/MWh), volumes (MWh), revenues (£)
**Use Case**: VLP revenue analysis, arbitrage opportunities

### 💷 Pricing & Settlement
**Data Source**: `bmrs_costs`
**Metrics**: SSP/SBP (imbalance prices)
**Use Case**: Identify high-price periods for battery discharge

### 📡 System Operations
**Data Source**: `bmrs_freq_iris`
**Metrics**: Grid frequency (Hz), demand (MW)
**Use Case**: Frequency response opportunities, grid stability

### 🔌 Grid Infrastructure
**Data Source**: `duos_unit_rates`
**Metrics**: DNO charges (Red/Amber/Green p/kWh)
**Use Case**: DUoS cost analysis, optimal charging times

### 📋 Reference Data
**Data Source**: `dim_bmu`
**Metrics**: Unit metadata, capacities, fuel types
**Use Case**: Lookup BMU details, company names

### 📊 Analytics & Derived
**Data Source**: Pre-calculated KPIs
**Metrics**: Revenue summaries, benchmarks
**Use Case**: High-level dashboards

### 🗂️ REMIT & Compliance
**Data Source**: `bmrs_remit_iris`
**Metrics**: Outage notifications, unavailability
**Use Case**: Track plant outages, capacity reductions

---

## 🎯 Common Use Cases

### Use Case 1: CCGT Generation Today

**Goal**: See all CCGT generation for today

**Setup**:
1. From Date: `22/12/2025`
2. To Date: `22/12/2025`
3. Generation Type: `CCGT`
4. Category: ⚡ Generation & Fuel Mix
5. Type: Time Series Chart

**Result**: 254 rows (all CCGT units across 48 settlement periods)

---

### Use Case 2: Battery VLP Revenue (High-Price Week)

**Goal**: Analyze battery earnings during Oct 17-23 event

**Setup**:
1. From Date: `17/10/2025`
2. To Date: `23/10/2025`
3. BMU ID: `FFSEN005` (or leave as "All")
4. Category: 💰 Balancing Mechanism
5. Type: Top 10 Ranking

**Result**: Acceptance prices, volumes, estimated revenues

---

### Use Case 3: Wind Output Last 7 Days

**Goal**: Track wind generation trends

**Setup**:
1. From Date: `15/12/2025`
2. To Date: `22/12/2025`
3. Generation Type: `WIND`
4. Category: ⚡ Generation & Fuel Mix
5. Type: Trend Analysis (7 days)

**Result**: Daily wind output patterns

---

### Use Case 4: Imbalance Price Spikes

**Goal**: Find high-price arbitrage opportunities

**Setup**:
1. From Date: Last 30 days
2. Category: 💷 Pricing & Settlement
3. Type: Time Series Chart
4. Graph: Line Chart

**Result**: SSP/SBP over time, identify £70+ periods

---

## 🔍 Troubleshooting

### Issue: "Script function CALCULATE could not be found"

**Cause**: Apps Script function not deployed

**Fix**:
1. Extensions → Apps Script
2. Copy `ANALYSIS_DROPDOWNS.gs` code
3. Save and close
4. Reload Google Sheets
5. Try button again

---

### Issue: Date format error (400 Could not cast literal)

**Cause**: Google Sheets returns dates as DD/MM/YYYY

**Status**: ✅ **FIXED** in current version
**Solution**: Script auto-converts DD/MM/YYYY → YYYY-MM-DD

---

### Issue: No data returned

**Possible Causes**:
1. **Date range too narrow**: Try wider range
2. **Filter too specific**: Set Generation Type to "All"
3. **No data for period**: Check `bmrs_fuelinst_iris` has data for selected dates
4. **IRIS lag**: Real-time tables only have last 55 days

**Fix**: Run broader query first, then narrow down

---

### Issue: Wrong fuel type data

**Cause**: Filter not applied to query

**Status**: ✅ **FIXED** in current version
**Solution**: Script now reads GenType from B8 and applies to WHERE clause

---

## 📁 File Structure

```
/home/george/GB-Power-Market-JJ/
├── generate_analysis_report.py          # Main report generator ⭐
├── ANALYSIS_DROPDOWNS.gs                # Apps Script code ⭐
├── ANALYSIS_REPORT_SYSTEM_GUIDE.md      # User guide with examples
├── auto_report_watcher.py               # Auto-execution watcher (optional)
├── report_webhook_server.py             # Webhook server (optional)
├── SHEETS_API_SLOWNESS_ANALYSIS.md      # Performance analysis
├── ENABLE_ONE_CLICK_CALCULATE.md        # Webhook setup guide
└── inner-cinema-credentials.json        # GCP credentials
```

---

## 🔑 Key Components

### 1. Apps Script (ANALYSIS_DROPDOWNS.gs)

**Function**: `CALCULATE()`
**Trigger**: Button click in Analysis!B14
**Actions**:
- Reads selections from dropdowns
- Writes trigger marker to B15
- Shows configuration dialog
- Provides command to run

**Location**: Google Sheets → Extensions → Apps Script

---

### 2. Python Script (generate_analysis_report.py)

**Main Functions**:

```python
parse_date(date_str)
# Converts DD/MM/YYYY → YYYY-MM-DD

get_query_with_filters(category, from_dt, to_dt, gen_type)
# Builds SQL with filters applied

# Main execution
1. Read dropdown selections from Analysis sheet
2. Parse dates (handle DD/MM/YYYY format)
3. Build query with filters
4. Execute BigQuery query
5. Convert results to strings
6. Write to Analysis sheet (row 18+)
```

**Configuration**:
```python
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
```

---

### 3. Dropdown Data

**Source**: DropdownData sheet (hidden)

**Columns**:
- A: Party Roles
- B: BMU IDs (1,644 units)
- C: Unit Names (with company names)
- D: Generation Types (10 types)
- E: Lead Parties (258 parties)
- F: Report Categories (9 options)
- G: Report Types (10 options)
- H: Graph Types (9 options)

**Update**: Run `add_full_dropdowns_with_range.py` to refresh

---

## 🚀 Advanced: Auto-Execution

### Option 1: Watcher Script (Simplest)

**Start watcher** (runs in background):
```bash
python3 auto_report_watcher.py &
```

**How it works**:
1. Watches Analysis!B15 for "GENERATE" marker
2. When detected, automatically runs `generate_analysis_report.py`
3. Results appear in sheet without manual command

**Stop watcher**:
```bash
pkill -f auto_report_watcher
```

---

### Option 2: Webhook Server (Full Automation)

**Start webhook**:
```bash
python3 report_webhook_server.py
```

**Update Apps Script**: Change webhook URL in `CALCULATE()` function

**Benefit**: True one-click button → instant results

**See**: `ENABLE_ONE_CLICK_CALCULATE.md` for full setup

---

## 📊 Data Flow Diagram

```
┌─────────────────────┐
│  Google Sheets      │
│  Analysis Sheet     │
│  ┌───────────────┐  │
│  │ B4: From Date │  │
│  │ D4: To Date   │  │
│  │ B8: GenType   │  │ 1. User configures
│  │ B11: Category │  │
│  │ B14: CALCULATE│◄─┘
│  └───────┬────────┘  │
└──────────┼───────────┘
           │
           ▼
    2. Click button
           │
           ▼
┌──────────┴───────────┐
│  Apps Script         │
│  CALCULATE()         │
│  - Reads selections  │
│  - Shows dialog      │
└──────────┬───────────┘
           │
           ▼
    3. Run command
           │
           ▼
┌──────────┴──────────────┐
│  Python Script          │
│  generate_analysis_     │
│  report.py              │
│  ┌─────────────────┐    │
│  │ 1. Parse dates  │    │
│  │ 2. Build query  │    │
│  │ 3. Query BQ     │    │
│  │ 4. Write sheet  │    │
│  └────────┬────────┘    │
└───────────┼─────────────┘
            │
            ▼
     4. Query BigQuery
            │
┌───────────┴────────────┐
│  BigQuery              │
│  inner-cinema-...      │
│  uk_energy_prod        │
│  ┌──────────────────┐  │
│  │ bmrs_fuelinst_   │  │
│  │ iris             │  │
│  │ (10k rows)       │  │
│  └────────┬─────────┘  │
└───────────┼────────────┘
            │
            ▼
     5. Return data
            │
┌───────────┴────────────┐
│  Python processes:     │
│  - Convert dates       │
│  - Limit to 1000 rows  │
│  - Format as strings   │
└───────────┬────────────┘
            │
            ▼
     6. Write to Sheets
            │
┌───────────┴───────────┐
│  Google Sheets        │
│  Analysis!A18+        │
│  ┌─────────────────┐  │
│  │ date | period | │  │
│  │ fuel | MW      │  │
│  │ 254 rows ✅    │  │
│  └─────────────────┘  │
└───────────────────────┘
```

---

## 🎓 Best Practices

### 1. Date Selection
- ✅ Use specific dates for fast queries
- ✅ Test with 1 day first, then expand
- ⚠️ IRIS tables only have last 55 days
- ⚠️ Historical tables lag ~24 hours

### 2. Filters
- ✅ Start with "All" to see full dataset
- ✅ Apply fuel type filter for focused analysis
- ✅ Use BMU ID filter for specific units
- ⚠️ Too many filters = no results

### 3. Performance
- ✅ Queries limited to 10,000 rows (BQ)
- ✅ Display limited to 1,000 rows (Sheets)
- ✅ Fast execution: 5-10 seconds typical
- ⚠️ Large date ranges take longer

### 4. Data Quality
- ✅ Generation data: Very reliable
- ✅ CCGT filter working correctly
- ✅ Date parsing handles both formats
- ✅ Null values handled gracefully

---

## 📈 Performance Stats

**Tested Query**: CCGT generation for 22 Dec 2025

| Metric | Value |
|--------|-------|
| **Rows Retrieved** | 254 |
| **Query Time** | ~3 seconds |
| **Data Transfer** | Minimal |
| **API Calls** | 3 (read dropdowns, clear, write) |
| **Sheet Write Time** | ~2 seconds |
| **Total Time** | 5-10 seconds |

**Optimization Tips**:
- Dropdowns use hardcoded sheet IDs (no metadata fetch)
- BigQuery queries filtered early (WHERE clause)
- Date conversion happens in Python (fast)
- Batch API calls where possible

---

## 🔒 Security & Credentials

**Google Cloud Project**: `inner-cinema-476211-u9`
**Service Account**: inner-cinema-credentials.json
**Permissions Required**:
- ✅ BigQuery Data Viewer
- ✅ BigQuery Job User
- ✅ Sheets Editor

**API Limits**:
- BigQuery: 1TB free per month (well within)
- Sheets API: 60 requests/minute (rarely hit)

---

## 📚 Related Documentation

| Document | Purpose |
|----------|---------|
| `ANALYSIS_REPORT_SYSTEM_GUIDE.md` | User guide with examples |
| `BIGQUERY_DATA_CATEGORIES.md` | All data categories explained |
| `BIGQUERY_DATA_STATUS_DEC22_2025.md` | Current data pipeline status |
| `SHEETS_API_SLOWNESS_ANALYSIS.md` | Performance optimization |
| `PROJECT_CONFIGURATION.md` | BigQuery setup & configuration |
| `ENABLE_ONE_CLICK_CALCULATE.md` | Webhook automation setup |

---

## ✅ System Status

**Last Tested**: December 22, 2025
**Status**: ✅ Fully Operational

**Working Features**:
- ✅ CALCULATE button connected
- ✅ Date parsing (DD/MM/YYYY → YYYY-MM-DD)
- ✅ CCGT filter applied correctly
- ✅ BigQuery queries executing
- ✅ Results writing to sheet
- ✅ 254 rows retrieved for test query

**Known Limitations**:
- ⚠️ Manual command execution required (unless watcher running)
- ⚠️ Chart generation not automated (manual creation needed)
- ⚠️ Display limited to 1,000 rows (full dataset retrieved)

**Future Enhancements**:
- 🔮 Automatic chart creation
- 🔮 Webhook one-click execution
- 🔮 Scheduled report generation
- 🔮 Email/Slack notifications

---

## 🆘 Support

**Issues**: Check `/home/george/GB-Power-Market-JJ/FIX_CALCULATE_BUTTON.md`
**Performance**: See `SHEETS_API_SLOWNESS_ANALYSIS.md`
**Data Questions**: Review `BIGQUERY_DATA_CATEGORIES.md`

**Quick Checks**:
```bash
# Test BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"

# Test Sheets API
python3 -c "from googleapiclient.discovery import build; from google.oauth2.service_account import Credentials; creds = Credentials.from_service_account_file('inner-cinema-credentials.json'); sheets = build('sheets', 'v4', credentials=creds); print('✅ Sheets API ready')"

# Run test report
python3 generate_analysis_report.py
```

---

*Documentation created: December 22, 2025*
*System version: 1.0 - Production Ready*
*Maintainer: George Major (george@upowerenergy.uk)*
