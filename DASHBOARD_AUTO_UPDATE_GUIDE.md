# Live Dashboard v2 - Auto-Update Configuration

**Last Updated**: 12 December 2025  
**Status**: ✅ Active - Updates every 5 minutes  
**Spreadsheet**: [Live Dashboard v2](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)

---

## 📊 What Updates Automatically

### Every 5 Minutes (via cron)
The dashboard refreshes **automatically** with the latest data:

1. **Main Dashboard** (`update_live_dashboard_v2.py`)
   - ⚡ VLP Revenue (7-day average)
   - 💷 Wholesale Price (£/MWh)
   - 📊 Generation Mix (10 fuel types with %)
   - 🔌 Interconnectors (10 connections, MW flows)
   - 📈 48-period sparklines (fuel generation & IC flows)
   - 🕐 Timestamp (current settlement period)

2. **Outages Section** (`update_live_dashboard_v2_outages.py`)
   - 🔴 Active outages (15 units, row 40+)
   - Columns (11 total): Asset Name, Fuel Type, Unavail (MW), Normal (MW), Cause, Type (Planned/Unplanned), Expected Return, Duration, Operator, Area, Zone
   - Includes proper asset names from BMU registration
   - Fuel type emojis (🏭 CCGT, ⚛️ Nuclear, 🇫🇷 Interconnectors, etc.)
   - Duration calculated from start/end times (shows days/hours)
   - Planned/Unplanned indicators (📅 vs ⚡)

3. **Wind Chart** (`update_intraday_wind_chart.py`)
   - 🌬️ Intraday wind generation (A40:C63)
   - Actual wind output by settlement period
   - Updates chart data automatically

---

## ⚙️ Technical Setup

### Cron Job Configuration
```bash
# File: /etc/crontab or crontab -e
*/5 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
```

**Frequency**: Every 5 minutes (00, 05, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55)

### Update Script
**Location**: `/home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh`

**Executes**:
1. `update_live_dashboard_v2.py` - Main dashboard (KPIs, gen mix, sparklines)
2. `update_live_dashboard_v2_outages.py` - Outages section (row 40+, columns G-Q)
3. `update_intraday_wind_chart.py` - Wind chart data

**Log File**: `~/dashboard_v2_updates.log`

---

## 📋 Data Sources

### BigQuery Tables (Real-Time IRIS Data)
- `bmrs_fuelinst_iris` - Fuel generation by type
- `bmrs_mid_iris` - Wholesale market prices
- `bmrs_freq_iris` - Grid frequency
- `bmrs_remit_unavailability` - Power plant outages (with capacity, timing, operator data)
- `bmu_registration_data` - BMU names and details

### Settlement Period Calculation
```python
# Current time → Settlement Period (1-48)
hour = now.hour
minutes = now.minute
current_sp = (hour * 2) + (1 if minutes < 30 else 2)
# SP1 = 00:00-00:30, SP2 = 00:30-01:00, ..., SP48 = 23:30-24:00
```

---

## 🔍 Monitoring Auto-Updates

### Check Update Log
```bash
tail -f ~/dashboard_v2_updates.log
```

### View Recent Updates
```bash
tail -50 ~/dashboard_v2_updates.log | grep "✅\|❌"
```

### Manual Update (Test)
```bash
cd /home/george/GB-Power-Market-JJ
./auto_update_dashboard_v2.sh
```

### Check Cron Status
```bash
crontab -l | grep dashboard
# Should show: */5 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
```

---

## 🎯 Dashboard Layout

### Main Section (Rows 1-39)
- **Row 1**: Title & Timestamp
- **Rows 3-6**: KPIs (VLP Revenue, Wholesale, Frequency, etc.)
- **Rows 13-22**: Generation Mix (WIND, CCGT, NUCLEAR, etc.) with sparklines
- **Rows 13-22, Column J**: Interconnectors (ElecLink, IFA, etc.)

### Outages Section (Rows 40+)
**Headers** (Row 40): BM Unit | Asset Name | Fuel Type | Unavail (MW) | Cause

**Sample Data** (Rows 41-55):
```
I_IEG-FRAN1 | IEG-FRAN1        | 🇫🇷 INTFR  | 750 | DC Cable Fault
I_IED-FRAN1 | IED-FRAN1        | 🇫🇷 INTFR  | 750 | DC Cable Fault
DIDCB6      | Didcot B Unit 6  | 🏭 CCGT    | 666 | Turbine / Generator
T_HEYM27    | Heysham 2 Gen 7  | ⚛️ NUCLEAR | 660 | OPR
```

### Wind Chart (A40:F57)
- Chart displays intraday wind generation
- Data source: A40:C63 (Settlement Period, Actual GW, Forecast GW)
- Auto-updates every 5 minutes

### Hidden Sheet (Data_Hidden)
- **Rows 1-10**: 48-period fuel generation data (for sparklines)
- **Rows 11-20**: 48-period interconnector flows (for sparklines)
- **Columns A-AV**: Settlement Periods 1-48

---

## 🛠️ Troubleshooting

### Updates Not Running
```bash
# Check if cron is running
systemctl status cron

# Verify cron job exists
crontab -l | grep auto_update_dashboard

# Check script permissions
ls -l /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
# Should show: -rwxr-xr-x (executable)

# Make executable if needed
chmod +x /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
```

### Rate Limit Errors (429)
Google Sheets API has a limit of 60 writes/minute. The scripts use **batching** to reduce API calls:
- Before batching: ~30+ API calls per update
- After batching: ~6 API calls per update

**Solution**: Scripts include built-in rate limiting and batching. No action needed.

### Missing Data
```bash
# Check BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"

# Check Google Sheets credentials
ls -l inner-cinema-credentials.json
# Should exist and be readable
```

### Outages Not Updating
```bash
# Manual test
cd /home/george/GB-Power-Market-JJ
python3 update_gb_live_complete.py

# Check for errors
tail -20 ~/dashboard_v2_updates.log | grep -A 5 "Outages"
```

---

## 📊 Performance Metrics

### API Efficiency (After Batching)
- **Total API calls per update**: ~6 (was 30+)
- **KPIs**: 1 batch update (was 6 individual)
- **Generation Mix**: 1 batch update (was 10 individual)
- **Interconnectors**: 1 batch update (was 10 individual)
- **Data_Hidden**: 2 updates (fuel + IC timeseries)

### Update Timing
- **Main dashboard**: ~5-8 seconds
- **Outages**: ~3-5 seconds
- **Wind chart**: ~2-3 seconds
- **Total**: ~10-15 seconds per cycle

### Data Freshness
- Settlement period lag: <1 minute (updates immediately when new data available)
- Maximum age: 5 minutes (cron frequency)

---

## 🔧 Maintenance

### Disable Auto-Updates
```bash
# Comment out cron job
crontab -e
# Add # at start of line:
# */5 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
```

### Re-enable Auto-Updates
```bash
crontab -e
# Remove # from line:
*/5 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
```

### Change Update Frequency
```bash
crontab -e

# Every 10 minutes
*/10 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh

# Every hour
0 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh

# Every 2 minutes (not recommended - rate limits!)
*/2 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
```

---

## 📝 Related Documentation

- [README.md](README.md) - Main project overview
- [STOP_DATA_ARCHITECTURE_REFERENCE.md](STOP_DATA_ARCHITECTURE_REFERENCE.md) - Data architecture
- [PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md) - BigQuery configuration
- [ENHANCED_BI_ANALYSIS_README.md](ENHANCED_BI_ANALYSIS_README.md) - Dashboard features

---

## ✅ Verification Checklist

**Confirm auto-updates are working**:
- [ ] Cron job exists: `crontab -l | grep auto_update_dashboard`
- [ ] Script is executable: `ls -l auto_update_dashboard_v2.sh`
- [ ] Log file shows recent updates: `tail ~/dashboard_v2_updates.log`
- [ ] Dashboard timestamp updates every 5 minutes
- [ ] Outages section shows current data (row 40+)
- [ ] Wind chart shows today's data (A40:C63)
- [ ] No rate limit errors in log (no 429 errors)

---

**Status**: ✅ All auto-updates active and working (12 Dec 2025)
