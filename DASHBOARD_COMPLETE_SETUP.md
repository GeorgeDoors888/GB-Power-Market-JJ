# GB Energy Dashboard - Complete Setup Guide

**Status**: ✅ Fully Implemented  
**Date**: 23 November 2025  
**Dashboard**: [View Live Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/)

---

## ✅ What's Been Implemented

### 1. **Professional Dark Theme** (Material Black)
- Background: #121212 (Material Black)
- Text: White (#FFFFFF)
- Enhanced KPI layout with color-coding:
  - 🔴 Red: Demand MW
  - 🔵 Blue: Generation MW
  - 🟢 Green: Wind Share %
  - 🟠 Orange: Margin MW
  - ⚪ Grey: Avg Price £/MWh
  - 🟣 Purple: Constraint MW

### 2. **Enhanced KPI Layout** (A3:F4)
Horizontal 6-metric layout showing:
- Total GB Demand (MW)
- Total Generation (MW)
- Wind Share (%)
- System Margin (MW)
- Average Market Price (£/MWh)
- Constraint Volume (MW)

### 3. **4 Professional Charts** (A6:G60)

#### Chart 1: Market Price & Frequency (A6:G18)
- **Type**: Dual-axis combo chart
- **Data**: 48-hour rolling window
- **Left Y-axis**: Market Price (£/MWh) - Grey line
- **Right Y-axis**: Grid Frequency (Hz) - Green line
- **Purpose**: Correlate price volatility with frequency events

#### Chart 2: Demand & Constraints (A20:G32)
- **Type**: Stacked area chart
- **Data**: 48-hour rolling window
- **Series 1**: GB Demand (MW) - Red area
- **Series 2**: System Constraints (MW) - Purple area
- **Purpose**: Visualize demand patterns and balancing actions

#### Chart 3: Generation Fuel Mix (A34:G46)
- **Type**: Pie chart
- **Data**: TODAY's total generation by fuel type
- **Includes**: CCGT, Wind, Nuclear, Solar, Coal, Biomass, Interconnectors
- **Purpose**: Show current generation portfolio

#### Chart 4: Demand Trend (A48:G60)
- **Type**: Line chart
- **Data**: 48-hour rolling demand
- **Color**: Blue
- **Purpose**: Simple demand trend visualization

### 4. **Interconnector Flags** 🚩
Added country flags to interconnector rows:
- 🇫🇷 France: IFA, IFA2, ElecLink
- 🇧🇪 Belgium: NEMO
- 🇳🇱 Netherlands: BritNed
- 🇮🇪 Ireland: MOYLE, EWIC
- 🇳🇴 Norway: NSL
- 🇩🇰 Denmark: VIKING

### 5. **Auto-Refresh System** 🔄
**Three refresh methods available:**

#### Method A: Apps Script Timer (Google Sheets)
- **File**: `dashboard_auto_refresh.gs`
- **Frequency**: Every 5 minutes
- **Setup**: 
  1. Open Google Sheets
  2. Extensions → Apps Script
  3. Paste contents of `dashboard_auto_refresh.gs`
  4. Click "🔄 Dashboard" menu → "⚙️ Setup Auto-Refresh"

#### Method B: UpCloud Systemd Timer (Server-side)
- **Files**: `dashboard-updater.service`, `dashboard-updater.timer`
- **Frequency**: Every 5 minutes
- **Deployment**:
  ```bash
  cd "/Users/georgemajor/GB Power Market JJ"
  ./deploy_dashboard_updater.sh
  ```
- **Logs**: `/var/log/dashboard-updater.log`

#### Method C: Railway API Endpoint
- **Endpoint**: `POST https://jibber-jabber-production.up.railway.app/api/refresh-dashboard`
- **Trigger**: Called by Apps Script or external systems
- **Purpose**: Cloud-based refresh orchestration

---

## 🗂️ File Structure

### Python Scripts
```
transform_dashboard_complete.py       # Initial transformation (dark theme, KPIs)
add_enhanced_charts_and_flags.py      # Charts + IC flags (runs every 5 min)
```

### Apps Script
```
dashboard_auto_refresh.gs             # Google Sheets auto-refresh menu
```

### Systemd Files (UpCloud)
```
dashboard-updater.service             # Systemd service definition
dashboard-updater.timer               # 5-minute timer trigger
deploy_dashboard_updater.sh           # Deployment script
```

### API Gateway
```
api_gateway.py                        # Railway API (includes /api/refresh-dashboard)
```

---

## 🚀 Quick Start Guide

### Option 1: Manual Refresh (Immediate)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 add_enhanced_charts_and_flags.py
```

### Option 2: Deploy Auto-Refresh (Recommended)
```bash
# Deploy to UpCloud server for 5-min auto-updates
cd "/Users/georgemajor/GB Power Market JJ"
./deploy_dashboard_updater.sh

# Verify deployment
ssh root@94.237.55.15 'sudo systemctl status dashboard-updater.timer'
```

### Option 3: Apps Script Setup
1. Open [Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/)
2. Extensions → Apps Script
3. Paste `dashboard_auto_refresh.gs` code
4. Save as "Dashboard Auto-Refresh"
5. Click "🔄 Dashboard" menu → "⚙️ Setup Auto-Refresh"

---

## 📊 Data Pipeline

```
BigQuery (uk_energy_prod)
    ├── bmrs_mid_iris          → Market Prices
    ├── bmrs_indo_iris         → GB Demand
    ├── bmrs_fuelinst_iris     → Generation by Fuel
    ├── bmrs_freq_iris         → Grid Frequency
    └── bmrs_bod_iris          → Constraints (Bid-Offer)
              ↓
   Python Script (every 5 min)
              ↓
   Daily_Chart_Data Sheet (48h data)
              ↓
   Dashboard Sheet (4 Charts + 6 KPIs)
```

---

## 🔍 Monitoring & Logs

### Check UpCloud Auto-Updater
```bash
# Timer status
ssh root@94.237.55.15 'sudo systemctl status dashboard-updater.timer'

# View logs
ssh root@94.237.55.15 'tail -f /var/log/dashboard-updater.log'

# Manual trigger
ssh root@94.237.55.15 'sudo systemctl start dashboard-updater.service'
```

### Check Apps Script Logs
1. Open Apps Script editor
2. View → Logs (Ctrl/Cmd + Enter)
3. Check "RefreshLog" sheet (hidden) for audit trail

### Check Railway API
```bash
# Health check
curl https://jibber-jabber-production.up.railway.app/workspace/health

# Trigger manual refresh
curl -X POST https://jibber-jabber-production.up.railway.app/api/refresh-dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎨 Theme Colors Reference

| Element | Color | Hex Code |
|---------|-------|----------|
| Background | Material Black | #121212 |
| Text | White | #FFFFFF |
| Gridlines | Dark Grey | #333333 |
| Demand | Red | #E53935 |
| Generation | Blue | #1E88E5 |
| Wind | Green | #43A047 |
| Margin | Orange | #FB8C00 |
| Price | Grey | #9E9E9E |
| Constraints | Purple | #8E24AA |

---

## 🔧 Troubleshooting

### Dashboard Not Updating?

**Check 1**: Verify BigQuery access
```bash
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"
```

**Check 2**: Verify Google Sheets access
```bash
python3 -c "import gspread; from google.oauth2 import service_account; creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json'); gc = gspread.authorize(creds); print('✅ Connected')"
```

**Check 3**: Check UpCloud timer
```bash
ssh root@94.237.55.15 'sudo systemctl list-timers dashboard-updater.timer'
```

### Charts Not Appearing?

**Issue**: Charts require `Daily_Chart_Data` sheet to exist
**Fix**: Run `add_enhanced_charts_and_flags.py` manually once:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 add_enhanced_charts_and_flags.py
```

### Old Charts Still Visible?

**Issue**: Old charts not removed
**Fix**: Run complete transformation:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 transform_dashboard_complete.py
```

---

## 📝 Maintenance

### Update Refresh Frequency
Edit `dashboard-updater.timer`:
```ini
OnUnitActiveSec=5min  # Change to desired interval (e.g., 10min)
```

Then redeploy:
```bash
./deploy_dashboard_updater.sh
```

### Add More KPIs
Edit `add_enhanced_charts_and_flags.py` → `create_enhanced_kpis()` function

### Modify Chart Types
Edit `add_enhanced_charts_and_flags.py` → `create_enhanced_charts()` function

---

## 🎯 Success Metrics

✅ **Dark theme applied** - Material Black (#121212)  
✅ **6 KPIs displayed** - Horizontal layout (A3:F4)  
✅ **4 charts created** - Professional layouts (A6:G60)  
✅ **Interconnector flags** - Country emojis added  
✅ **Auto-refresh enabled** - Every 5 minutes  
✅ **Existing data preserved** - Fuel breakdown + outages intact  
✅ **GSP data removed** - Rows 58-77 cleared  
✅ **Old charts deleted** - 4 charts removed  

---

## 📞 Support

**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/  

---

*Last Updated: 23 November 2025*
