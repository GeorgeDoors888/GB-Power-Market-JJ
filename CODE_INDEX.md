# GB Power Market JJ - Code Index

**Last Updated**: December 12, 2025  
**Purpose**: Comprehensive index of all code, scripts, and configurations

---

## 🆕 NEW FILES (December 12, 2025)

### Battery BM Revenue Tracking
- **`update_battery_trading_dashboard.py`** ⭐ NEW
  - **Purpose**: Update Google Sheets with battery BM revenue from BOAV + EBOCF endpoints
  - **Usage**: `python3 update_battery_trading_dashboard.py [YYYY-MM-DD]`
  - **Features**: 
    - Queries 10 batteries across 48 settlement periods
    - Calculates revenue, volume, average price
    - Generates sparkline formulas for trend visualization
    - Updates Live Dashboard v2 rows 38-43
  - **Dependencies**: gspread, requests, config.py
  - **Endpoint**: Settlement-derived BOAV + EBOCF (1-2 day lag)

### Configuration Management
- **`config.py`** ⭐ NEW
  - **Purpose**: Single source of truth for all configuration IDs
  - **Contains**: 
    - `GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_ID']`
    - `validate_spreadsheet_connection()` function
  - **Usage**: `from config import GOOGLE_SHEETS_CONFIG`
  - **Why**: Prevents hardcoded ID sprawl, enables centralized validation

### Documentation
- **`BATTERY_BM_REVENUE_TRACKING.md`** ⭐ NEW
  - Complete guide to battery revenue tracking system
  - Architecture, data flow, dashboard layout
  - Usage examples, error handling, future enhancements

- **`CRITICAL_SPREADSHEET_ID_ISSUE.md`** ⭐ UPDATED
  - Documents wrong spreadsheet ID issue discovered Dec 12
  - Root cause analysis, impact assessment, resolution
  - Status: ✅ RESOLVED

- **`CODE_INDEX.md`** ⭐ NEW (this file)
  - Comprehensive index of all code and scripts
  - Organized by category with descriptions

---

## 📊 Dashboard & Google Sheets Scripts

### Main Dashboard Updaters
- **`update_analysis_bi_enhanced.py`**
  - Main dashboard refresh script
  - Updates generation mix, prices, VLP revenue
  - **Status**: Production (manual run)

- **`realtime_dashboard_updater.py`**
  - Auto-refresh dashboard every 5 minutes
  - Runs via cron job
  - **Logs**: `logs/dashboard_updater.log`

- **`enhance_dashboard_layout.py`**
  - Create professional dashboard layout
  - Apply formatting, colors, borders

- **`format_dashboard.py`**
  - Apply formatting to existing dashboard

- **`update_battery_trading_dashboard.py`** ⭐ NEW
  - Update battery BM revenue section
  - Uses BOAV + EBOCF endpoints

### Dashboard Chart & Visualization Scripts
- **`add_dashboard_charts.py`**
- **`add_chart_only.py`**
- **`add_revenue_stack_charts.py`**
- **`add_enhanced_charts_and_flags.py`**
- **`dashboard_charts.gs`** (Apps Script)

### Dashboard Component Adders
- **`add_dashboard_analysis.py`**
- **`add_dashboard_interactivity.py`**
- **`add_iris_insights_to_dashboard.py`**
- **`add_gsp_to_dashboard.py`**
- **`add_unavailability_to_dashboard.py`**
- **`add_freshness_indicator.py`**
- **`add_validation_and_formatting.py`**

### Map & Geospatial
- **`add_map_to_dashboard.py`**
- **`add_maps_to_dashboard.py`**
- **`add_dno_map_to_sheet.py`**
- **`add_dno_map_chart.py`**
- **`auto_generate_map.py`**
- **`auto_generate_map_linux.py`**

---

## 🔋 BESS (Battery) Management

### BESS Configuration & Setup
- **`add_bess_dropdowns_v4.py`**
- **`add_bess_dropdowns.py`**
- **`add_voltage_dropdown.py`**
- **`apply_bess_formatting.py`**
- **`reset_bess_layout.py`**
- **`show_dashboard_layout.py`**

### BESS Analysis
- **`analyze_bess_costs.py`**
- **`analyze_seasonal_arbitrage.py`**
- **`update_battery_trading_dashboard.py`** ⭐ NEW

---

## 📈 VLP (Virtual Lead Party) Analysis

### VLP Revenue Calculation
- **`analyze_battery_vlp_final.py`**
- **`analyze_vlp_bm_revenue.py`**
- **`analyze_vlp_pricing.py`**
- **`analyze_vlp_simple.py`**
- **`add_vlp_correct_calculation.py`**

### VLP Data Discovery (BREAKTHROUGH)
- **Discovery**: BOAV + EBOCF endpoints provide pair-level cashflows and volumes
- **Issue Resolved**: BOALF has no prices, BOD has submissions only
- **Solution**: Settlement-derived endpoints (1-2 day lag but authoritative)

---

## 🌐 Data Ingestion & BigQuery

### Elexon BMRS Ingestion
- **`ingest_elexon_fixed.py`**
  - Main BMRS data ingestion script
  - Updates 174+ BMRS tables
  - **Schedule**: 15-min cron job

### IRIS Real-Time Pipeline
- **`iris-clients/python/client.py`**
  - Download messages from Azure Service Bus
  - **Deployment**: AlmaLinux server (94.237.55.234)

- **`iris_to_bigquery_unified.py`**
  - Upload IRIS messages to BigQuery
  - Creates `*_iris` tables (24-48h data)

### Backfill Scripts
- **`auto_backfill_costs_daily.py`**
- **`auto_backfill_disbsad_daily.py`**
- **`backfill_boalf_gap.py`**
- **`backfill_constraints_gap.py`**
- **`backfill_costs_gap.py`**
- **`backfill_costs_simple.py`**
- **`backfill_dets_system_prices.py`**
- **`backfill_disbsad_to_present.py`**

---

## 📊 Statistical Analysis

### Advanced Analytics
- **`advanced_statistical_analysis_enhanced.py`**
  - Full statistical suite
  - Correlation, regression, time series

- **`advanced_statistical_analysis.py`**
  - Original stats analysis

- **`advanced_stats_bigquery.py`**
  - Stats directly in BigQuery

- **`advanced_stats_simple.py`**
  - Lightweight stats module

### Specific Analysis Scripts
- **`analyze_constraints_by_geography.py`**
- **`analyze_duplicate_types.py`**
- **`analyze_generator_sizes.py`**
- **`analyze_user_concern.py`**

---

## 🗺️ DNO (Distribution Network Operator) Lookup

### DNO System Components
- **`dno_lookup_python.py`**
  - Main DNO lookup script
  - Queries BigQuery for DNO details and DUoS rates
  - Uses `mpan_generator_validator` for MPAN parsing

- **`dno_webhook_server.py`**
  - Flask webhook receiver (port 5001)
  - Triggered by Apps Script button

- **`bess_auto_trigger.gs`** (Apps Script)
  - Google Sheets button handler
  - Calls webhook via ngrok tunnel

### DNO Data Tables
- **BigQuery Tables**:
  - `uk_energy_prod.neso_dno_reference` - DNO details
  - `gb_power.duos_unit_rates` - DUoS rates by DNO/voltage
  - `gb_power.duos_time_bands` - Time periods (Red/Amber/Green)

---

## 🔧 Utility & Helper Scripts

### Configuration & Setup
- **`config.py`** ⭐ NEW
  - Centralized configuration
  - Spreadsheet IDs, validation functions

### Credentials & Authentication
- **`inner-cinema-credentials.json`**
  - Service account for BigQuery + Sheets
  - Project: inner-cinema-476211-u9

### Testing & Validation
- **`test_mpan_details.py`**
- **`test_workspace_credentials.py`**
- **`check_table_coverage.sh`**
- **`check_iris_data.py`**

### Dashboard Management
- **`quick_dashboard_update.py`**
- **`update_both_dashboards.py`**
- **`flag_fixer.py`**
- **`read_dashboard_structure.py`**

---

## 🚀 Deployment & Automation

### Shell Scripts
- **`refresh_dashboard_full.sh`**
  - Full dashboard refresh
  
- **`setup_constraints.sh`**
  - Setup constraints analysis

- **`verify_vlp_system.sh`**
  - Verify VLP system status

- **`auto_update_dashboard_v2.sh`**
  - Auto-update dashboard v2

- **`apply-chat-history-to-repo.sh`**
  - Apply chat history to repo

### Cron Jobs
```bash
# Dashboard auto-refresh (every 5 min)
*/5 * * * * python3 /path/to/realtime_dashboard_updater.py

# Battery revenue update (daily at 08:00)
0 8 * * * python3 /path/to/update_battery_trading_dashboard.py
```

---

## 📱 API Gateway & Vercel Proxy

### Vercel Edge Functions
- **`vercel-proxy/api/proxy-v2.js`**
  - ChatGPT → BigQuery proxy endpoint
  - SQL validation, rate limiting
  - **URL**: https://gb-power-market-jj.vercel.app/api/proxy-v2

### API Gateway
- **`api_gateway.py`**
  - Local API gateway

---

## 📚 Apps Script Files

### Google Apps Script (Deployed)
- **`apps_script_code.gs`**
- **`apps_script_map_updater.gs`**
- **`dashboard_charts.gs`**
- **`add_date_range_controls.gs`**
- **`add_gb_live_sparklines.gs`**
- **`bess_auto_trigger.gs`** (DNO webhook caller)

### Apps Script HTML
- **`APPS_SCRIPT_DNOMAP.html`**

---

## 🗂️ Data Files & Configurations

### Service Configuration
- **`arbitrage.service`** - Systemd service
- **`arbitrage.timer`** - Systemd timer
- **`arbitrage.logrotate`** - Log rotation config

### JSON Data
- **`arbitrage-bq-key.json`** - BigQuery credentials
- **`dashboard_data_20251031_163623.json`** - Dashboard snapshot

---

## 📖 Documentation Files

### Project Documentation
- **`README.md`** - Main project README
- **`ARCHITECTURE.md`** - System architecture
- **`API_REFERENCE.md`** - API reference
- **`DOCUMENTATION_INDEX.md`** - Index of all docs

### Setup & Deployment Guides
- **`DEPLOYMENT_COMPLETE.md`**
- **`IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`**
- **`APPS_SCRIPT_GUIDE.md`**
- **`APPS_SCRIPT_INSTALLATION.gs`**
- **`APPS_SCRIPT_SETUP_GUIDE.txt`**

### Battery & BESS Guides
- **`BATTERY_BM_REVENUE_TRACKING.md`** ⭐ NEW
- **`BESS_BATTERY_CHP_INVENTORY.md`**
- **`BATTERY_TRADING_STRATEGY_ANALYSIS.md`**
- **`IRIS_DATA_STATUS_AND_BATTERY_MODEL_FINAL.md`**

### VLP Documentation
- **`VLP_SYSTEM_README.md`**
- **`VLP_IMPLEMENTATION_COMPLETE.md`**
- **`VLP_DEPLOYMENT_GUIDE.md`**
- **`VLP_DATA_DISCOVERY_SUMMARY.md`**
- **`VLP_REVENUE_ANALYSIS.md`**
- **`VLP_PYTHON_DASHBOARD_GUIDE.md`**
- **`✅ VLP_Data sheet: 30 days of sample VLP .md`**

### Configuration & Reference
- **`PROJECT_CONFIGURATION.md`** ⭐ READ FIRST
- **`STOP_DATA_ARCHITECTURE_REFERENCE.md`** ⭐ CRITICAL
- **`UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`**
- **`SPREADSHEET_IDS_MASTER_REFERENCE.md`**

### Issue Tracking
- **`CRITICAL_SPREADSHEET_ID_ISSUE.md`** ⭐ RESOLVED
- **`KNOWN_ISSUES_VLP_REVENUE_CALCULATION.md`**
- **`DIAGNOSIS_DATE_CONTROLS_FAILURE.md`**
- **`APPS_SCRIPT_MENU_FIX.md`**

### Analysis Guides
- **`STATISTICAL_ANALYSIS_GUIDE.md`**
- **`ENHANCED_BI_ANALYSIS_README.md`**

### ChatGPT Integration
- **`CHATGPT_INSTRUCTIONS.md`**
- **`CHATGPT_ACTUAL_ACCESS.md`**

---

## 🔑 Critical Configuration Reference

### BigQuery Project
```
Project ID: inner-cinema-476211-u9
Dataset: uk_energy_prod
Location: US
```

### Google Sheets
```
Spreadsheet ID: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
Title: "GB Live 2"
Main Worksheet: "Live Dashboard v2"
URL: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
```

### IRIS Pipeline
```
Server: 94.237.55.234 (AlmaLinux)
Client: /opt/iris-pipeline/client.py
Uploader: /opt/iris-pipeline/iris_to_bigquery_unified.py
Logs: /opt/iris-pipeline/logs/
```

### Python Environment
```bash
python3  # NOT `python` on macOS
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread requests
export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"
```

---

## 📊 Data Tables Reference

### Historical Tables (2020-present)
- `bmrs_bod` - Bid-offer data (391M+ rows, HAS PRICES)
- `bmrs_boalf` - Acceptances (615K rows, NO PRICES)
- `bmrs_costs` - System prices (SSP/SBP merged since Nov 2015)
- `bmrs_fuelinst` - Fuel generation
- `bmrs_freq` - Grid frequency
- `bmrs_mid` - Market index (wholesale prices)

### Real-Time IRIS Tables (24-48h)
- `bmrs_*_iris` suffix
- Examples: `bmrs_fuelinst_iris`, `bmrs_bod_iris`, `bmrs_boalf_iris`

### Reference Tables
- `bmu_registration_data` - 59 batteries, 2,555.8 MW total
- `neso_dno_reference` - DNO details
- `duos_unit_rates` - DUoS rates

---

## 🚨 Common Pitfalls & Solutions

### 1. Wrong Spreadsheet ID
**Problem**: Hardcoded old ID in 20+ files  
**Solution**: Import from `config.py`
```python
from config import GOOGLE_SHEETS_CONFIG
SHEET_ID = GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_ID']
```

### 2. Wrong Worksheet Name
**Problem**: Looking for "Dashboard" (doesn't exist)  
**Solution**: Use "Live Dashboard v2"

### 3. BOALF Has No Prices
**Problem**: Cannot calculate revenue from acceptances  
**Solution**: Use BOAV + EBOCF settlement endpoints (1-2 day lag)

### 4. Wrong BigQuery Location
**Problem**: Queries fail with "table not found in europe-west2"  
**Solution**: Use location="US"
```python
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
```

### 5. MPAN Parsing Error
**Problem**: Using wrong parser, extracting wrong distributor ID  
**Solution**: Import from `mpan_generator_validator`
```python
from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup
```

---

## 🎯 Quick Start Guide

### 1. Update Battery Revenue Dashboard
```bash
python3 update_battery_trading_dashboard.py
```

### 2. Refresh Main Dashboard
```bash
python3 update_analysis_bi_enhanced.py
```

### 3. Check IRIS Data Freshness
```bash
python3 check_iris_data.py
```

### 4. Query BigQuery (Python)
```python
from google.cloud import bigquery
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
query = "SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst` LIMIT 10"
df = client.query(query).to_dataframe()
```

### 5. Update DNO Lookup
```bash
python3 dno_lookup_python.py 14 HV  # MPAN ID, voltage
```

---

## 📞 Support & Contacts

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production (November 2025)

---

## 🔄 Recent Updates (December 12, 2025)

### Critical Fixes
✅ Fixed spreadsheet ID issue (wrong ID in 20+ files)  
✅ Created `config.py` for centralized configuration  
✅ Updated `.github/copilot-instructions.md` with correct ID

### New Features
✅ Battery BM revenue tracking system  
✅ BOAV + EBOCF endpoint integration  
✅ Sparkline trend visualization  
✅ Auto-calculation of revenue metrics

### New Files
✅ `update_battery_trading_dashboard.py`  
✅ `config.py`  
✅ `BATTERY_BM_REVENUE_TRACKING.md`  
✅ `CODE_INDEX.md` (this file)

### Documentation Updates
✅ All markdown files updated with latest changes  
✅ Code index created for easy navigation  
✅ Critical issue resolution documented

---

**Last Updated**: December 12, 2025  
**Version**: 2.0 (Post-Spreadsheet ID Fix)  
**Next Review**: January 2026
