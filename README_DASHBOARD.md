# 📊 GB Power Market Dashboard - Complete Solution

**Real-time UK power market monitoring with automated charts**

[![Status](https://img.shields.io/badge/Status-Operational-success)](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Google Sheets](https://img.shields.io/badge/Google-Sheets-green)](https://sheets.google.com/)
[![BigQuery](https://img.shields.io/badge/BigQuery-Powered-orange)](https://cloud.google.com/bigquery)

---

## 🚀 Quick Start

### For End Users (Just View Dashboard)
➡️ **Open Dashboard**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

### For Dashboard Maintainers (Add Charts)
1. Read **[QUICK_START_CHARTS.md](QUICK_START_CHARTS.md)** (5 minutes)
2. Install Google Apps Script charts
3. **Done!** Charts auto-update

### For Developers (Run Updates)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python dashboard_clean_design.py
```

---

## ✨ Features

### 📊 Data Tracking
- ✅ **10 Fuel Types**: Gas (CCGT), Nuclear, Wind, Biomass, Hydro (Run-of-River), Pumped Storage, Coal, Gas Peaking (OCGT), Oil, Other
- ✅ **10 Interconnectors**: NSL (Norway), IFA, IFA2, ElecLink (France), Nemo (Belgium), Viking Link (Denmark), BritNed (Netherlands), Moyle, East-West, Greenlink (Ireland)
- ✅ **REMIT Outages**: Power station unavailability tracking
- ✅ **Price Impact Analysis**: Market price changes from outages
- ✅ **Settlement Periods**: Generation, Frequency, and Price tracking (48 periods/day)

### 📈 Visualizations
- ✅ **Generation Chart**: Line graph showing power generation trends (blue)
- ✅ **Frequency Chart**: System frequency monitoring 49.8-50.2 Hz (red)
- ✅ **Price Chart**: Market price column chart (yellow)
- ✅ **Combined Overview**: All metrics on one chart with dual Y-axes

### 🔄 Automation
- ✅ **Auto-updating**: Python script fetches latest data from BigQuery
- ✅ **Chart Auto-refresh**: Charts update when data changes
- ✅ **Layout Preserved**: Your custom 27-column formatting maintained
- ✅ **Fixed Positions**: REMIT section stays at row 29

---

## 📖 Documentation

| Document | Purpose | Time |
|----------|---------|------|
| **[QUICK_START_CHARTS.md](QUICK_START_CHARTS.md)** | Add charts in 5 minutes | ⏱️ 5 min |
| **[COMPLETE_SOLUTION_SUMMARY.md](COMPLETE_SOLUTION_SUMMARY.md)** | Overall solution overview | ⏱️ 10 min |
| **[APPS_SCRIPT_INSTALLATION.md](APPS_SCRIPT_INSTALLATION.md)** | Detailed chart installation | ⏱️ 15 min |
| **[DASHBOARD_UPDATE_SUMMARY.md](DASHBOARD_UPDATE_SUMMARY.md)** | Python script details | ⏱️ 10 min |
| **[DASHBOARD_LAYOUT_DIAGRAM.md](DASHBOARD_LAYOUT_DIAGRAM.md)** | Visual layout reference | ⏱️ 5 min |
| **[DOCUMENTATION_INDEX_NEW.md](DOCUMENTATION_INDEX_NEW.md)** | Complete documentation index | ⏱️ 5 min |

---

## 🏗️ Architecture

```
┌─────────────────┐
│   BigQuery      │  • bmrs_fuelinst (Generation)
│   Data Sources  │  • bmrs_mid (Market prices)
│                 │  • bmrs_freq (Frequency)
│                 │  • bmrs_remit_unavailability (Outages)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Python Script  │  dashboard_clean_design.py
│  Updates Data   │  • Fetches from BigQuery
│                 │  • Updates Google Sheet (batch_update)
│                 │  • Preserves formatting
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Google Sheets   │  • 27-column layout preserved
│ Dashboard       │  • Graph data: A18:H28
│                 │  • REMIT section: Row 29+
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Apps Script    │  google_apps_script_charts.js
│  Auto Charts    │  • 4 charts (Gen, Freq, Price, Combined)
│                 │  • Auto-update on data change
└─────────────────┘
```

---

## 🛠️ Setup

### Prerequisites
- Python 3.11+ with virtual environment
- Google Cloud Platform project with BigQuery access
- Google Sheets API credentials
- Google Apps Script access

### Installation

#### 1. Python Environment
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 -m venv .venv
source .venv/bin/activate  # or .venv/bin/activate on Windows
pip install -r requirements.txt
```

#### 2. Install Charts
See **[QUICK_START_CHARTS.md](QUICK_START_CHARTS.md)** for 5-minute setup

#### 3. Run Dashboard Update
```bash
./.venv/bin/python dashboard_clean_design.py
```

---

## 📊 Dashboard Layout

```
Row 1-5:    Title, Timestamp, System Metrics
Row 7-17:   Generation (10 fuel types) | Interconnectors (10)
Row 18-28:  📈 Settlement Period Graph Data (A18:H28)
Row 29+:    🔴 REMIT Outages & Price Impacts
Col J+:     📊 4 Auto-updating Charts
```

Full layout diagram: **[DASHBOARD_LAYOUT_DIAGRAM.md](DASHBOARD_LAYOUT_DIAGRAM.md)**

---

## 🔄 Usage

### Manual Update
```bash
./.venv/bin/python dashboard_clean_design.py
```

### Automated Updates (Cron)
```bash
# Edit crontab
crontab -e

# Add line (every 30 minutes)
*/30 * * * * cd "/Users/georgemajor/GB Power Market JJ" && ./.venv/bin/python dashboard_clean_design.py >> dashboard_updates.log 2>&1
```

### Apps Script Auto-Update
1. In Apps Script editor: Click ⏰ Clock icon
2. Add Trigger: `updateCharts`, Time-driven, Every 30 minutes

---

## 📈 Current Status

**Last Update**: 2025-10-30 16:13:00

**Metrics**:
- Total Generation: 27.8 GW
- Renewables: 44.1%
- Active Outages: 4 of 5 events
- Settlement Periods Tracked: 29
- Charts: 4 (Auto-updating)

**View Dashboard**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

---

## 🎨 Charts

### 1. Generation Chart (📊)
- **Type**: Line chart with smooth curves
- **Color**: Google Blue (#4285F4)
- **Location**: Row 35, Column J
- **Data**: Settlement periods vs Generation (GW)

### 2. Frequency Chart (⚡)
- **Type**: Line chart
- **Color**: Google Red (#EA4335)
- **Location**: Row 35, Column Q
- **Data**: Settlement periods vs Frequency (Hz)
- **Range**: 49.8 - 50.2 Hz

### 3. Price Chart (💷)
- **Type**: Column chart
- **Color**: Google Yellow (#FBBC04)
- **Location**: Row 50, Column J
- **Data**: Settlement periods vs Price (£/MWh)

### 4. Combined Chart (📈)
- **Type**: Combo chart (lines + bars)
- **Colors**: Blue (Gen), Red (Freq), Yellow (Price)
- **Location**: Row 50, Column Q
- **Features**: Dual Y-axes, all metrics visible

---

## 🔧 Troubleshooting

### Python Script Issues
```bash
# Check BigQuery access
bq query "SELECT COUNT(*) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\` LIMIT 1"

# Reinstall dependencies
./.venv/bin/pip install -r requirements.txt

# Check db-dtypes (for graph data)
./.venv/bin/pip install db-dtypes
```

### Chart Issues
- **Charts don't appear**: Run `createAllCharts` in Apps Script
- **Wrong data**: Run Python script first to populate A18:H28
- **Overlapping**: Edit `CHART_START_ROW` in Apps Script

Full troubleshooting: **[COMPLETE_SOLUTION_SUMMARY.md](COMPLETE_SOLUTION_SUMMARY.md#troubleshooting)**

---

## 📝 Files

### Python Scripts
- `dashboard_clean_design.py` - Main dashboard updater
- `update_graph_data.py` - Standalone graph data updater
- `read_sheet_api.py` - Layout verification tool

### Google Apps Script
- `google_apps_script_charts.js` - Chart automation

### Documentation
- 6 comprehensive markdown guides (see Documentation section above)

---

## 🎯 Key Features

### Data Accuracy
- ✅ Real-time BigQuery data
- ✅ All fuel types and interconnectors tracked
- ✅ Hydro separated (Run-of-River vs Pumped Storage)
- ✅ 48 settlement periods per day

### Layout Protection
- ✅ 27-column layout preserved
- ✅ Fixed row positions
- ✅ Formatting intact
- ✅ Only data updated, not structure

### Visualization
- ✅ 4 professional charts
- ✅ Auto-updating
- ✅ Google color scheme
- ✅ Responsive design

---

## 🚀 Next Steps

1. **Add Charts**: Follow [QUICK_START_CHARTS.md](QUICK_START_CHARTS.md)
2. **Automate**: Set up cron job for Python + Apps Script trigger
3. **Customize**: Adjust chart colors, positions, or add new charts
4. **Enhance**: Add demand data, historical comparisons, or alerts

---

## 📞 Support

**Documentation**: See [DOCUMENTATION_INDEX_NEW.md](DOCUMENTATION_INDEX_NEW.md)  
**Dashboard URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

---

## 📄 License

This project is for internal use with UK power market data.

---

## ✅ Quick Checklist

### First Time Setup:
- [ ] Python environment configured
- [ ] BigQuery access working
- [ ] Google Sheets API credentials set up
- [ ] Dashboard script runs successfully
- [ ] Charts installed via Apps Script
- [ ] All 4 charts appear in spreadsheet
- [ ] Data updates correctly
- [ ] Charts auto-update on data change

### Regular Maintenance:
- [ ] Run Python script (manual or automated)
- [ ] Verify data freshness
- [ ] Check charts display correctly
- [ ] Monitor for errors in logs

---

**Built with ❤️ for GB Power Market Analysis**

Last Updated: 2025-10-30  
Version: 1.0  
Status: ✅ Fully Operational
