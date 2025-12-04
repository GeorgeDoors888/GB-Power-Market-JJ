# GB Power Market JJ - Complete Project Index

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Project**: UK Energy Market Data Platform with BESS Revenue Optimization  
**Last Updated**: December 1, 2025

---

## 📋 Table of Contents

1. [Documentation Files](#documentation-files)
2. [Python Scripts](#python-scripts)
3. [Google Apps Script](#google-apps-script)
4. [Configuration Files](#configuration-files)
5. [Deployment Guides](#deployment-guides)
6. [Data Architecture](#data-architecture)

---

## 📚 Documentation Files

### Core Documentation
- **[BESS_ENGINE_DEPLOYMENT.md](BESS_ENGINE_DEPLOYMENT.md)** - TODAY'S WORK: Complete BESS revenue optimization engine deployment (Dec 1, 2025)
- **[PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md)** - ⭐ Master configuration reference (read first!)
- **[STOP_DATA_ARCHITECTURE_REFERENCE.md](STOP_DATA_ARCHITECTURE_REFERENCE.md)** - ⭐ Data schema reference (prevents common mistakes)
- **[README.md](README.md)** - Project overview and quick start
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Categorized documentation list (22 files)

### Architecture & Design
- **[UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md)** - Dual-pipeline architecture (batch + streaming)
- **[DATA_PIPELINE_ARCHITECTURE.md](DATA_PIPELINE_ARCHITECTURE.md)** - Pipeline design and data flow

### Analysis Guides
- **[STATISTICAL_ANALYSIS_GUIDE.md](STATISTICAL_ANALYSIS_GUIDE.md)** - Statistical analysis suite documentation
- **[ENHANCED_BI_ANALYSIS_README.md](ENHANCED_BI_ANALYSIS_README.md)** - Business intelligence dashboard guide
- **[BATTERY_TRADING_STRATEGY_ANALYSIS.md](BATTERY_TRADING_STRATEGY_ANALYSIS.md)** - VLP battery trading strategy analysis

### Deployment Guides
- **[DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md)** - Overall deployment status
- **[IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md](IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md)** - IRIS real-time pipeline deployment
- **[SHEETS_API_COMPLETE.md](SHEETS_API_COMPLETE.md)** - Google Sheets API deployment (Railway)
- **[codex-server/SHEETS_API_RAILWAY.md](codex-server/SHEETS_API_RAILWAY.md)** - Railway Sheets API reference

### BESS-Specific Documentation
- **[BESS_INSTALLATION_GUIDE.md](BESS_INSTALLATION_GUIDE.md)** - BESS web app installation
- **[BESS_REVENUE_GUIDE.md](BESS_REVENUE_GUIDE.md)** - BESS revenue tracking guide
- **[BESS_SHEET_INVENTORY.md](BESS_SHEET_INVENTORY.md)** - BESS Google Sheets inventory
- **[BESS_UPCLOUD_DEPLOYMENT.md](BESS_UPCLOUD_DEPLOYMENT.md)** - UpCloud server deployment
- **[BESS_UPCLOUD_QUICKSTART.md](BESS_UPCLOUD_QUICKSTART.md)** - Quick start guide
- **[BESS_V2_DEPLOYMENT_COMPLETE.md](BESS_V2_DEPLOYMENT_COMPLETE.md)** - BESS V2 deployment
- **[BESS_DEPLOYMENT_SUCCESS.md](BESS_DEPLOYMENT_SUCCESS.md)** - BESS deployment checklist
- **[BESS_DROPDOWNS_COMPLETE.md](BESS_DROPDOWNS_COMPLETE.md)** - BESS dropdown functionality
- **[BESS_ENHANCEMENTS_COMPLETE.md](BESS_ENHANCEMENTS_COMPLETE.md)** - BESS enhancement summary
- **[BESS_RATE_FIX_SUMMARY.md](BESS_RATE_FIX_SUMMARY.md)** - DUoS rate fix documentation
- **[BESS_TODO.md](BESS_TODO.md)** - BESS task list

### ChatGPT Integration
- **[CHATGPT_INSTRUCTIONS.md](CHATGPT_INSTRUCTIONS.md)** - ChatGPT configuration guide
- **[CHATGPT_ACTUAL_ACCESS.md](CHATGPT_ACTUAL_ACCESS.md)** - ChatGPT access verification

---

## 🐍 Python Scripts

### BESS Revenue Optimization (NEW - Dec 1, 2025)
- **[bess_revenue_engine.py](bess_revenue_engine.py)** - ✨ Complete BESS revenue optimization engine (1030 lines)
  * Multi-revenue stream optimization (FR, Arbitrage, CM, VLP)
  * BigQuery integration (FR prices, system prices, BOAs)
  * Google Sheets dashboard updates
  * SoC (State of Charge) tracking
  * KPI calculations and projections
  * **Status**: ✅ Production Ready
  * **Usage**: `python3 bess_revenue_engine.py 2025-01-01 2025-01-31`

- **[chatgptnextsteps.py](chatgptnextsteps.py)** - Original template (1025 lines, used as basis for bess_revenue_engine.py)

### Frequency Response Analysis
- **[fr_revenue_optimiser.py](fr_revenue_optimiser.py)** - Original FR optimizer (£105k/year projection)
- **[fr_revenue_optimiser_enhanced.py](fr_revenue_optimiser_enhanced.py)** - Enhanced FR optimizer with additional metrics
- **[advanced_fr_optimizer.py](advanced_fr_optimizer.py)** - Advanced FR optimization with constraints

### Dashboard & Reporting
- **[update_analysis_bi_enhanced.py](update_analysis_bi_enhanced.py)** - Main dashboard refresh script
- **[realtime_dashboard_updater.py](realtime_dashboard_updater.py)** - Auto-refresh dashboard (runs every 5 min via cron)
- **[enhance_dashboard_layout.py](enhance_dashboard_layout.py)** - Professional dashboard layout
- **[format_dashboard.py](format_dashboard.py)** - Dashboard formatting
- **[add_dashboard_charts.py](add_dashboard_charts.py)** - Chart creation
- **[bigquery_to_sheets_updater.py](bigquery_to_sheets_updater.py)** - BigQuery → Sheets sync

### Statistical Analysis
- **[advanced_statistical_analysis_enhanced.py](advanced_statistical_analysis_enhanced.py)** - Comprehensive stats suite
- **[advanced_statistical_analysis.py](advanced_statistical_analysis.py)** - Original stats analysis
- **[advanced_stats_bigquery.py](advanced_stats_bigquery.py)** - BigQuery-based stats
- **[advanced_stats_simple.py](advanced_stats_simple.py)** - Simplified stats

### Battery Analysis
- **[analyze_battery_vlp_final.py](analyze_battery_vlp_final.py)** - VLP battery analysis
- **[analyze_vlp_simple.py](analyze_vlp_simple.py)** - Simplified VLP analysis
- **[battery_arbitrage.py](battery_arbitrage.py)** - Battery arbitrage calculator
- **[battery_charging_cost_analysis.py](battery_charging_cost_analysis.py)** - Charging cost analysis
- **[battery_profit_analysis.py](battery_profit_analysis.py)** - Profit analysis

### BESS Web App & Monitoring
- **[bess_auto_monitor.py](bess_auto_monitor.py)** - BESS monitoring script
- **[bess_auto_monitor_upcloud.py](bess_auto_monitor_upcloud.py)** - UpCloud monitoring
- **[bess_export_reports.py](bess_export_reports.py)** - BESS report generator
- **[auto_refresh_outages.py](auto_refresh_outages.py)** - Outage data refresh

### DNO Lookup System
- **[dno_lookup_python.py](dno_lookup_python.py)** - DNO lookup with BigQuery + postcodes.io
- **[dno_webhook_server.py](dno_webhook_server.py)** - Flask webhook for Google Sheets buttons
- **[duos_rates.py](duos_rates.py)** - DUoS rates processing

### Map Generation
- **[auto_generate_map.py](auto_generate_map.py)** - Generator map generator (macOS)
- **[auto_generate_map_linux.py](auto_generate_map_linux.py)** - Generator map (Linux)
- **[auto_update_maps.py](auto_update_maps.py)** - Map auto-updater
- **[add_map_to_dashboard.py](add_map_to_dashboard.py)** - Embed map in Sheets
- **[add_cva_to_map.py](add_cva_to_map.py)** - CVA layer addition

### Data Ingestion (IRIS Pipeline)
- **[iris_to_bigquery_unified.py](iris_to_bigquery_unified.py)** - IRIS → BigQuery uploader
- **[iris-clients/python/client.py](iris-clients/python/client.py)** - IRIS message downloader
- **[ingest_elexon_fixed.py](ingest_elexon_fixed.py)** - Elexon API ingestion
- **[backfill_indo_daily.py](backfill_indo_daily.py)** - INDO data backfill

### Dashboard Enhancements
- **[add_bess_dropdowns_v4.py](add_bess_dropdowns_v4.py)** - BESS dropdown menus (v4)
- **[add_bess_dropdowns.py](add_bess_dropdowns.py)** - Original BESS dropdowns
- **[add_voltage_dropdown.py](add_voltage_dropdown.py)** - Voltage selector
- **[add_dashboard_analysis.py](add_dashboard_analysis.py)** - Analysis panels
- **[add_enhanced_charts_and_flags.py](add_enhanced_charts_and_flags.py)** - Charts + flags
- **[add_flags_manual.py](add_flags_manual.py)** - Manual flag insertion
- **[add_freshness_indicator.py](add_freshness_indicator.py)** - Data freshness badge
- **[add_gsp_to_dashboard.py](add_gsp_to_dashboard.py)** - GSP integration
- **[add_iris_insights_to_dashboard.py](add_iris_insights_to_dashboard.py)** - IRIS insights
- **[add_unavailability_to_dashboard.py](add_unavailability_to_dashboard.py)** - Unavailability tracking
- **[add_validation_and_formatting.py](add_validation_and_formatting.py)** - Data validation
- **[apply_dashboard_design.py](apply_dashboard_design.py)** - Design application
- **[apply_orange_redesign.py](apply_orange_redesign.py)** - Orange theme

### Generator Analysis
- **[analyze_generator_sizes.py](analyze_generator_sizes.py)** - Generator size analysis
- **[analyze_duplicate_types.py](analyze_duplicate_types.py)** - Duplicate detection
- **[analyze_user_concern.py](analyze_user_concern.py)** - User concern analysis

### API & Servers
- **[api_gateway.py](api_gateway.py)** - API gateway
- **[bridge.py](bridge.py)** - Bridge service
- **[codex-server/codex_server_secure.py](codex-server/codex_server_secure.py)** - FastAPI server with Sheets API (Railway)

### Utilities
- **[check_iris_data.py](check_iris_data.py)** - IRIS data freshness checker
- **[check_table_coverage.sh](check_table_coverage.sh)** - BigQuery table date coverage
- **[ask_gemini_analysis.py](ask_gemini_analysis.py)** - Gemini AI integration

---

## 📜 Google Apps Script Files

### BESS Web App
- **[bess_auto_trigger.gs](bess_auto_trigger.gs)** - Auto-trigger functions for BESS sheet
- **[bess_dno_lookup.gs](bess_dno_lookup.gs)** - DNO lookup integration
- **[bess_custom_menu.gs](bess_custom_menu.gs)** - Custom menu for BESS sheet
- **[bess_webapp_api.gs](bess_webapp_api.gs)** - Web app backend API

### Dashboard
- **[apps_script_code.gs](apps_script_code.gs)** - Main dashboard Apps Script
- **[apps_script_map_updater.gs](apps_script_map_updater.gs)** - Map update automation
- **[dashboard_charts.gs](dashboard_charts.gs)** - Chart creation script

### Setup Guides
- **[APPS_SCRIPT_MANUAL_STEPS.md](APPS_SCRIPT_MANUAL_STEPS.md)** - Manual setup steps
- **[APPS_SCRIPT_SETUP_GUIDE.txt](APPS_SCRIPT_SETUP_GUIDE.txt)** - Setup guide

---

## ⚙️ Configuration Files

### Service Accounts & Credentials
- **[inner-cinema-credentials.json](inner-cinema-credentials.json)** - GCP service account (inner-cinema-476211-u9)
- **[arbitrage-bq-key.json](arbitrage-bq-key.json)** - Arbitrage service account

### Systemd Services (Linux)
- **[arbitrage.service](arbitrage.service)** - Arbitrage systemd service
- **[arbitrage.timer](arbitrage.timer)** - Arbitrage timer
- **[bigquery-sheets-updater.service](bigquery-sheets-updater.service)** - BQ→Sheets updater
- **[bess-webhook.service](bess-webhook.service)** - BESS webhook service
- **[bess-monitor.service](bess-monitor.service)** - BESS monitor service
- **[arbitrage.logrotate](arbitrage.logrotate)** - Log rotation config

### Scripts
- **[apply_memory_fix.sh](apply_memory_fix.sh)** - Memory optimization
- **[apply-chat-history-to-repo.sh](apply-chat-history-to-repo.sh)** - Chat history sync

---

## 🗄️ Data Architecture

### BigQuery Project
**Project ID**: `inner-cinema-476211-u9`  
**Dataset**: `uk_energy_prod`  
**Location**: `US`

### Key Tables

#### Historical Pipeline (2020-present)
- `bmrs_bod` - Bid-offer data (391M+ rows)
- `bmrs_fuelinst` - Fuel mix data
- `bmrs_freq` - Frequency data
- `bmrs_mid` - Market index data
- `bmrs_costs` - System prices (SSP/SBP) ⭐ Used by BESS engine
- `fr_clearing_prices` - FR auction results ⭐ Used by BESS engine
- `bmrs_boalf` - BOA acceptances ⭐ Used by BESS engine
- `neso_dno_reference` - DNO lookup table
- `gb_power.duos_unit_rates` - DUoS rates
- `gb_power.duos_time_bands` - Time band definitions

#### Real-Time Pipeline (Last 24-48h)
- `bmrs_fuelinst_iris` - Real-time fuel mix
- `bmrs_freq_iris` - Real-time frequency
- `bmrs_mid_iris` - Real-time market data
- All historical tables have `*_iris` variants

### SQL Query Patterns

#### Complete Timeline Query (Historical + Real-time)
```sql
WITH combined AS (
  SELECT CAST(settlementDate AS DATE) as date, ...
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE settlementDate < '2025-10-30'
  UNION ALL
  SELECT CAST(settlementDate AS DATE) as date, ...
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE settlementDate >= '2025-10-30'
)
SELECT * FROM combined
```

---

## 🚀 External Services

### Live Deployments
- **Google Sheets Dashboard**: [12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/)
- **BESS Dashboard**: [1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc](https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/)
- **ChatGPT Proxy**: https://gb-power-market-jj.vercel.app/api/proxy-v2
- **Railway Sheets API**: https://jibber-jabber-production.up.railway.app
- **IRIS Pipeline Server**: 94.237.55.234 (AlmaLinux)
- **Generator Map**: http://94.237.55.15/gb_power_comprehensive_map.html

### API Endpoints (Railway)
- `GET /sheets_health` - Health check
- `GET /sheets_list` - List all sheets
- `POST /sheets_read` - Read data
- `POST /sheets_write` - Write data
- `POST /query_bigquery` - Execute BigQuery queries

---

## 📊 Key Use Cases

### 1. BESS Revenue Optimization
**Script**: `bess_revenue_engine.py`
```bash
python3 bess_revenue_engine.py 2025-01-01 2025-01-31
```
**Output**: Multi-revenue stream analysis with FR, arbitrage, CM, VLP projections

### 2. Dashboard Refresh
**Auto**: `realtime_dashboard_updater.py` (cron: every 5 min)
**Manual**: `update_analysis_bi_enhanced.py`

### 3. FR Revenue Analysis
**Script**: `fr_revenue_optimiser.py`
```bash
python3 fr_revenue_optimiser.py
```
**Output**: £105k/year FR revenue projection

### 4. DNO Lookup
**Server**: `dno_webhook_server.py` (port 5001)
**Script**: `dno_lookup_python.py`
```bash
python3 dno_lookup_python.py 14 HV
```
**Output**: NGED West Midlands, Red: 1.764 p/kWh

### 5. Statistical Analysis
**Script**: `advanced_statistical_analysis_enhanced.py`
**Output**: Comprehensive market statistics

---

## 🔧 Development Commands

### BigQuery Testing
```bash
# Test connection
python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("✅ Connected")'

# Check table date range
./check_table_coverage.sh bmrs_bod
```

### Google Sheets Testing
```bash
# Test read
curl -X POST https://jibber-jabber-production.up.railway.app/sheets_read \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -d '{"sheet":"Dashboard","range":"A1:C5"}'
```

### IRIS Pipeline
```bash
# Check status
ssh root@94.237.55.234 'ps aux | grep iris'

# Monitor logs
ssh root@94.237.55.234 'tail -f /opt/iris-pipeline/logs/iris_uploader.log'
```

---

## 📝 SQL Query Files

### Analysis Queries
- **[bod_vwap_hh.sql](bod_vwap_hh.sql)** - Half-hourly VWAP from bid-offer data
- **[boalf_counts_hh.sql](boalf_counts_hh.sql)** - BOA acceptance counts

---

## 📦 Data Export Files

### BESS Exports (Nov 24, 2024)
- **[bess_export_20251124_172111.csv](bess_export_20251124_172111.csv)** - BESS data CSV
- **[bess_export_20251124_172111.json](bess_export_20251124_172111.json)** - BESS data JSON
- **[bess_export_20251124_172142.csv](bess_export_20251124_172142.csv)** - BESS data CSV (2)
- **[bess_export_20251124_172142.json](bess_export_20251124_172142.json)** - BESS data JSON (2)
- **[bess_report_20251124_172142.txt](bess_report_20251124_172142.txt)** - BESS report

---

## 🆘 Troubleshooting

### Common Issues

1. **"Table not found in europe-west2"**
   - Fix: Always use `location="US"` for BigQuery client

2. **"Access Denied: jibber-jabber-knowledge"**
   - Fix: Use `inner-cinema-476211-u9` project ID

3. **"Unrecognized name" errors**
   - Fix: Check `STOP_DATA_ARCHITECTURE_REFERENCE.md` for correct schema

4. **Missing recent data**
   - Fix: UNION with `*_iris` tables for real-time data

5. **gspread API errors**
   - Fix: Use named arguments: `ws.update(range_name="A1", values=[[data]])`

---

## 📞 Contact & Support

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production (December 2025)

---

*Last Updated: December 1, 2025*  
*Total Files Indexed: 150+*  
*Documentation Files: 30+*  
*Python Scripts: 80+*  
*Apps Script Files: 8*
