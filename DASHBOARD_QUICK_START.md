# Dashboard Live Integration - Quick Reference

## ✅ What's Complete

### Dashboard Sheet Updates
```
Row 44:    📊 LIVE ANALYTICS & VISUALIZATION (header)
Row 46:    🗺️ GB ENERGY MAP (Live) (header)
Rows 47-60: Interactive map placeholder (installs via Apps Script)
Row 62:    📈 INTRADAY GENERATION (Today) (header)
Rows 64+:  Live chart data (Settlement Period × Fuel Type)
Cell B2:   ⏰ Timestamp with "LIVE AUTO-REFRESH (5 min)"
```

### Auto-Refresh Status
- **Script**: `enhanced_dashboard_updater.py` (✅ Working)
- **Frequency**: Every 5 minutes (when enabled via cron)
- **Updates**: Timestamp, chart data, map data sheets
- **Last Test**: 2025-11-24 00:41:03 - ✅ SUCCESS

### Map Data Sheets
- **Map_Data_GSP**: 9 GSP locations (✅ Updates live)
- **Map_Data_IC**: 8 interconnectors (✅ Updates live)
- **Map_Data_DNO**: 10 DNO boundaries with GeoJSON (✅ Static)

## 🚀 One-Minute Setup

### 1. View Dashboard (0 seconds)
```bash
open "https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/"
```

### 2. Install Apps Script (30 seconds)
1. Extensions → Apps Script
2. Copy `dashboard_integration.gs` → Paste
3. File → New → HTML → Name: `dynamicMapView`
4. Copy `dynamicMapView.html` → Paste
5. Save → Refresh spreadsheet
6. ✅ Menu appears: "🔄 Live Dashboard"

### 3. Enable Auto-Refresh (30 seconds)
```bash
# Test first
python3 enhanced_dashboard_updater.py

# Enable cron (on server)
ssh root@94.237.55.234
crontab -e
# Add: */5 * * * * cd /opt/dashboard && python3 enhanced_dashboard_updater.py >> logs/updater.log 2>&1
```

## 📊 Using the Dashboard

### Interactive Map
```
Menu: 🔄 Live Dashboard → 🗺️ Show Interactive Map
```
- Select DNO region (dropdown)
- Choose overlay type (Generation/Demand/Constraints)
- Set IC mode (All/Imports/Exports)
- Map updates in real-time

### Manual Refresh
```
Menu: 🔄 Live Dashboard → 📊 Refresh All Data
```
- Updates timestamp
- Refreshes chart data
- Updates map data sheets

### View Status
```
Menu: 🔄 Live Dashboard → ⚙️ Auto-Refresh: ON (5 min)
```
- Shows refresh interval
- Displays last update time
- Lists updated components

## 🔧 Files Reference

| File | Location | Purpose |
|------|----------|---------|
| `integrate_dashboard_complete.py` | Root | Initial setup (run once) |
| `enhanced_dashboard_updater.py` | Root | Auto-refresh (run every 5 min) |
| `dashboard_integration.gs` | Root | Apps Script menu code |
| `dynamicMapView.html` | Root | Interactive map HTML |
| `DASHBOARD_LIVE_INTEGRATION_COMPLETE.md` | Root | Full deployment guide |

## ⚡ Quick Commands

```bash
# Manual refresh
python3 enhanced_dashboard_updater.py

# Check if running
ps aux | grep enhanced_dashboard_updater

# View logs (on server)
tail -f logs/updater.log

# Re-run initial setup
python3 integrate_dashboard_complete.py
```

## 🎯 What's Live

✅ **Timestamp** (B2): Updates every 5 min  
✅ **Chart Data** (A64+): Today's intraday generation  
✅ **Map Data**: GSP locations, IC flows  
✅ **Headers**: Analytics, Map, Charts sections  
✅ **Auto-Refresh**: Ready for cron deployment  

## 📍 Next Actions

1. **Install Apps Script** (30 sec) - Get interactive map working
2. **Enable cron** (30 sec) - Auto-refresh every 5 min
3. **Test map** (10 sec) - Open menu → Show map
4. **Verify refresh** (5 min wait) - Check B2 timestamp updates

## 📞 Troubleshooting

**Map doesn't show**: Install Apps Script code (step 2 above)  
**No chart data**: Too early (before 00:30), wait for first settlement period  
**Timestamp not updating**: Enable cron (step 3 above)  
**"Unrecognized name" error**: Check `STOP_DATA_ARCHITECTURE_REFERENCE.md` for schema  

---

**Full Guide**: `DASHBOARD_LIVE_INTEGRATION_COMPLETE.md`  
**Last Updated**: 2025-11-24 00:41:03  
**Status**: ✅ Production Ready
