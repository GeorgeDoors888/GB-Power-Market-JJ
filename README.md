# 🇬🇧 GB-Power-Market-JJ - Complete Energy Data Platform

**Last Updated**: 15 December 2025  
**Status**: Production - Active Development  
**Purpose**: Comprehensive GB electricity market analysis, real-time monitoring, and forecasting system

⚠️ **DATA DISCLAIMER**: All Balancing Mechanism (BM) revenue figures in this project are **ESTIMATES** derived from Elexon BMRS transparency data (BOALF, BOAV, EBOCF). These are **NOT settlement-grade cashflows**. Actual BOA energy payments are determined through BSC settlement and may vary ±10-20% from our estimates. For details, see [BOA_ENERGY_PAYMENTS_EXPLAINED.md](BOA_ENERGY_PAYMENTS_EXPLAINED.md).

---

## 🚀 Quick Start

### What This Project Does
- **Real-time Monitoring**: Live electricity generation, prices, and grid status (auto-updates every 5 minutes)
- **Historical Analysis**: 22+ months of GB power market data (2023-2025)
- **Forecasting**: Battery arbitrage, wind generation, and price predictions
- **Dashboard**: Google Sheets-based interactive dashboard with auto-updates
- **Outages Tracking**: 15 active power plant outages with complete details (capacity, timing, operator, duration, planned/unplanned status)
- **DNO Integration**: Distribution Network Operator tariffs and MPAN lookup
- **BESS Analysis**: Battery Energy Storage System profit optimization

### Live Dashboard
**Access**: [Live Dashboard v2](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)  
**Auto-Updates**: Every 5 minutes via cron  
**Features**: VLP Revenue, Wholesale Prices, Generation Mix, Interconnectors, Outages, Wind Chart

### Repository Size After Optimization
- **Before**: 3.4GB (879MB Git + 2.5GB working files)
- **After**: 2.2GB (large data moved to `~/GB-Power-Data/`)
- **Performance**: ⚡ 35% faster Git operations

---

## 📚 Complete Documentation

**See [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)** for the full index of 45+ core documentation files.

### 🎯 Essential Documents

#### Start Here
1. **[docs/STOP_DATA_ARCHITECTURE_REFERENCE.md](docs/STOP_DATA_ARCHITECTURE_REFERENCE.md)** - ⚠️ **READ FIRST** - Prevents recurring data issues
2. **[docs/PROJECT_CONFIGURATION.md](docs/PROJECT_CONFIGURATION.md)** - Essential configuration & BigQuery setup
3. **[docs/QUICK_START_ANALYSIS.md](docs/QUICK_START_ANALYSIS.md)** - ⚡ Copy-paste commands to run analysis NOW

#### Latest Updates (Nov 21-23, 2025)
- **[docs/DASHBOARD_FIX_NOV_21_2025.md](docs/DASHBOARD_FIX_NOV_21_2025.md)** - Dashboard MW→GW conversion fix
- **[docs/WIND_FARM_MAPPING_COMPLETE.md](docs/WIND_FARM_MAPPING_COMPLETE.md)** - 43 offshore + 414 onshore wind farms mapped
- **[docs/AUTHENTICATION_ARCHITECTURE.md](docs/AUTHENTICATION_ARCHITECTURE.md)** - Complete auth guide
- **Performance Optimization** - Moved 1.1GB data to external directory

#### For Dashboard Users
1. **[DASHBOARD_AUTO_UPDATE_GUIDE.md](DASHBOARD_AUTO_UPDATE_GUIDE.md)** - ⚡ **NEW** - Auto-update configuration & monitoring
2. **[docs/DASHBOARD_REFRESH_QUICK_REF.md](docs/DASHBOARD_REFRESH_QUICK_REF.md)** - One-page data refresh guide
3. **[docs/ENHANCED_BI_ANALYSIS_README.md](docs/ENHANCED_BI_ANALYSIS_README.md)** - Dashboard features & usage

#### For Developers
1. **[docs/CODE_REVIEW_SUMMARY.md](docs/CODE_REVIEW_SUMMARY.md)** - All analysis functions documented
2. **[docs/AUTO_REFRESH_COMPLETE.md](docs/AUTO_REFRESH_COMPLETE.md)** - Self-refreshing BigQuery pipeline
3. **[docs/GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)** - GitHub Actions deployment guide
4. **[drive-bq-indexer/API.md](drive-bq-indexer/API.md)** - FastAPI endpoints & BigQuery repository

---

## 🏗️ Project Architecture

### Data Sources
- **BMRS (Balancing Mechanism Reporting Service)**: Real-time generation & prices
- **IRIS API**: Historical settlement data via Elexon
- **National Grid ESO**: Outages, capacity, transmission data
- **DNO APIs**: 14 Distribution Network Operators tariff schedules
- **Elexon API**: Market indices, system prices
- **Google Sheets**: Dashboard frontend with Apps Script automation

### Technology Stack
- **Database**: Google BigQuery (40+ tables, 100M+ rows)
- **Backend**: Python 3.14, FastAPI, Railway/UpCloud deployment
- **Frontend**: Google Sheets with Apps Script (GAS)
- **Automation**: GitHub Actions, cron jobs, Cloud Functions
- **Maps**: Leaflet.js with GeoJSON for grid visualization
- **Auth**: Google OAuth 2.0, Service Accounts

### Key Components
1. **Historical Data Pipeline**: IRIS → BigQuery (2023-2025)
2. **Real-time Pipeline**: BMRS → BigQuery (live updates)
3. **Analysis Engine**: Statistical analysis, forecasting models
4. **Dashboard**: Auto-updating Google Sheets with 20+ visualizations
5. **BESS Optimizer**: Battery arbitrage profit calculator
6. **DNO Integration**: MPAN lookup, DUOS tariff calculator

---

## 📁 Repository Structure

```
/GB-Power-Market-JJ/
├── docs/                          # 📚 All documentation (45+ files)
│   ├── DOCUMENTATION_INDEX.md     # Complete documentation index
│   ├── STOP_DATA_ARCHITECTURE_REFERENCE.md  # Critical reference
│   ├── QUICK_START_ANALYSIS.md    # Quick start commands
│   └── ...                        # 40+ more docs
├── output/                        # 📊 Generated outputs
│   ├── maps/                      # HTML/PNG maps
│   └── data/                      # CSV/JSON exports
├── logs/                          # 📝 Application logs
├── chat-history/                  # 💬 Copilot conversation exports
├── drive-bq-indexer/              # 🔌 FastAPI PDF indexer
├── schemas/                       # 📋 BigQuery table schemas
├── *.py                           # 🐍 330+ Python scripts
├── *.gs                           # 📜 15 Google Apps Scripts
├── .vscode/settings.json          # ⚙️ Optimized VS Code config
└── .gitignore                     # 🚫 Performance-optimized exclusions
```

---

## 🎯 Common Tasks

### Run Analysis
```bash
cd "/Users/georgemajor/GB-Power-Market-JJ"
python3 enhanced_statistical_analysis.py
```

### Update Dashboard
```bash
python3 comprehensive_dashboard_update.py
# Or use: python3 realtime_dashboard_updater.py
```

### Check System Status
```bash
./check_services_status.sh
./check_dual_server_status.sh
```

### Generate Maps
```bash
python3 create_boundary_maps.py
python3 create_wind_farm_maps.py
python3 create_gsp_maps.py
```

### MPAN Lookup & Tariff Calculation
```bash
python3 mpan_parser.py
python3 duos_cost_calculator.py
```

---

## 🔐 Authentication & Credentials

### Required Credentials
1. **BigQuery**: Service account JSON (`arbitrage-bq-key.json`)
2. **Google Sheets**: OAuth credentials (`credentials.json`, `token.json`)
3. **IRIS API**: Settings file (`iris_settings.json`) - in `~/GB-Power-Data/`

### Setup Guide
See **[docs/AUTHENTICATION_ARCHITECTURE.md](docs/AUTHENTICATION_ARCHITECTURE.md)** for complete setup instructions.

---

## 📊 BigQuery Tables

### Historical Data (IRIS)
- `bmrs_fuelinst_iris` - Fuel type generation (2023-2025)
- `day_ahead_prices_iris` - Day-ahead auction prices
- `imbalance_prices_iris` - System imbalance prices
- `market_index_data_iris` - Market indices

### Real-time Data (BMRS)
- `bmrs_generation_by_fuel_type` - Live generation
- `bmrs_rolling_system_demand` - System demand
- `bmrs_day_ahead_prices` - Forward prices
- `bmrs_system_prices` - Current prices

### Enhanced Data
- `battery_profit_analysis` - BESS arbitrage calculations
- `generation_forecast_accuracy` - Forecast vs actual
- `wind_capacity_analysis` - Wind farm performance
- `outages_dashboard` - Planned outages

**Full Schema Reference**: [docs/COMPLETE_SCHEMA_REFERENCE.md](docs/COMPLETE_SCHEMA_REFERENCE.md)

---

## 🌐 External Data Location

Large data files moved to **`~/GB-Power-Data/`** for performance:
- `iris_windows_deployment/` (939MB) - IRIS client & historical data
- `overarch-jibber-jabber/` (138MB) - GeoJSON boundaries
- `logs_archive_*.tar.gz` - Archived log files

---

## 🚀 Deployment

### Local Development
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/
```

### Production Deployments
- **Railway**: FastAPI PDF indexer (`drive-bq-indexer/`)
- **UpCloud**: Dashboard backend server
- **GitHub Actions**: Automated testing & deployment
- **Google Apps Script**: Dashboard frontend

See **[docs/DEPLOYMENT_SUMMARY.md](docs/DEPLOYMENT_SUMMARY.md)** for details.

---

## 🛠️ Performance Optimizations (Nov 23, 2025)

### Recent Improvements
1. ✅ Moved 1.1GB data to external directory (`~/GB-Power-Data/`)
2. ✅ Configured VS Code to exclude large directories from indexing
3. ✅ Organized 103+ untracked files into `docs/` and `output/`
4. ✅ Updated `.gitignore` for better performance
5. ✅ Ran `git gc --aggressive` (reduced pack from 806MB → 746MB)
6. ✅ Reduced repo size from 3.4GB → 2.2GB

### VS Code Settings
File watching and search now exclude:
- `iris_windows_deployment/`, `overarch-jibber-jabber/`, `logs/`
- `.venv/`, `__pycache__/`, `chat-history/`
- See `.vscode/settings.json` for complete configuration

---

## 📈 Project Stats

- **Lines of Code**: 50,000+ (Python, JavaScript, SQL)
- **Python Scripts**: 330+
- **Google Apps Scripts**: 15
- **Documentation Files**: 45+ core docs (460+ total .md files)
- **BigQuery Tables**: 40+
- **BigQuery Rows**: 100M+
- **Date Range**: January 2023 - November 2025
- **Wind Farms Mapped**: 457 (43 offshore, 414 onshore)
- **DNO Integrations**: 14 (all GB distribution networks)

---

## 🤝 Contributing

This is a personal research project. For questions or collaboration:
- **Email**: george@upowerenergy.uk
- **GitHub**: GeorgeDoors888

---

## 📝 License

Proprietary - Internal Research Project

---

## 🔗 Quick Links

- **[Full Documentation Index](docs/DOCUMENTATION_INDEX.md)** - All 45+ docs indexed
- **[Latest Changes](CHANGELOG.md)** - Recent updates & fixes
- **[Dashboard Access](docs/CHATGPT_DASHBOARD_ACCESS_STATUS.md)** - Dashboard credentials
- **[API Documentation](drive-bq-indexer/API.md)** - FastAPI endpoints
- **[GitHub Repository](https://github.com/GeorgeDoors888/GB-Power-Market-JJ)**

---

**Need Help?** Start with [docs/QUICK_START_ANALYSIS.md](docs/QUICK_START_ANALYSIS.md) or [docs/STOP_DATA_ARCHITECTURE_REFERENCE.md](docs/STOP_DATA_ARCHITECTURE_REFERENCE.md)
