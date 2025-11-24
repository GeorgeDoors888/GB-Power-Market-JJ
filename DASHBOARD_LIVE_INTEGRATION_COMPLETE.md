# Dashboard Live Integration - Complete Deployment Guide

**Status**: ✅ Integrated and ready for auto-refresh  
**Date**: 24 November 2025  
**Author**: George Major

## 🎯 What's Been Integrated

The Dashboard sheet now includes:

### 1. **Live Analytics Section** (Rows 44-60)
- Row 44: `📊 LIVE ANALYTICS & VISUALIZATION` header
- Row 46: `🗺️ GB ENERGY MAP (Live)` header
- Rows 47-60: Map placeholder (will be interactive via Apps Script)

### 2. **Intraday Charts Section** (Rows 62+)
- Row 62: `📈 INTRADAY GENERATION (Today)` header
- Rows 64+: Live chart data (Settlement Period × Fuel Type matrix)
- Updates every 5 minutes with today's generation

### 3. **Live Timestamp** (Cell B2)
- Format: `⏰ Last Updated: 2025-11-24 00:38:41 | ✅ LIVE AUTO-REFRESH (5 min)`
- Updates every refresh cycle

### 4. **Map Data Sheets**
- `Map_Data_GSP`: 9 GSP locations with demand/generation
- `Map_Data_IC`: 8 interconnectors with flow data
- `Map_Data_DNO`: 10 DNO boundaries with real GeoJSON coordinates

## 📋 Files Created

| File | Purpose | Status |
|------|---------|--------|
| `integrate_dashboard_complete.py` | Initial integration script | ✅ Complete |
| `enhanced_dashboard_updater.py` | Auto-refresh script (replaces old version) | ✅ Complete |
| `dashboard_integration.gs` | Apps Script menu & map functions | ✅ Ready to install |
| `dynamicMapView.html` | Interactive map HTML (already exists) | ✅ Ready to use |

## 🚀 Quick Start

### Step 1: View Your Dashboard
```bash
open "https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/"
```

You should see:
- Rows 1-42: Existing data (fuel breakdown, outages)
- Row 44: New analytics section header (red background)
- Rows 47-60: Map placeholder (gray background)
- Row 62: Charts header
- Rows 64+: Today's intraday generation data

### Step 2: Install Apps Script (Interactive Map)

1. Open the spreadsheet
2. Go to: `Extensions → Apps Script`
3. Delete any existing code in the editor
4. **Copy entire contents** of `dashboard_integration.gs`
5. Paste into Apps Script editor
6. Click `File → New → HTML` → name it `dynamicMapView`
7. **Copy entire contents** of `dynamicMapView.html`
8. Paste into the HTML editor
9. Click **Save** (💾 icon)
10. Close Apps Script tab
11. **Refresh the spreadsheet**

You should now see: `🔄 Live Dashboard` menu in the menu bar

### Step 3: Enable Auto-Refresh

```bash
# Option A: Test manual refresh first
cd "/Users/georgemajor/GB Power Market JJ"
python3 enhanced_dashboard_updater.py

# Option B: Enable auto-refresh (every 5 minutes)
# Edit crontab on server
ssh root@94.237.55.234

# Add this line:
*/5 * * * * cd /opt/dashboard && /usr/bin/python3 enhanced_dashboard_updater.py >> logs/updater.log 2>&1

# Save and exit
```

## 🗺️ Using the Interactive Map

### From Spreadsheet Menu
1. Click: `🔄 Live Dashboard → 🗺️ Show Interactive Map`
2. Map modal opens with 3 controls:
   - **DNO Region**: Select area to focus on
   - **Overlay Type**: Generation/Demand/Constraints
   - **IC Mode**: All/Imports/Exports
3. Map updates in real-time as you change selections

### Map Features
- **10 DNO regions** with colored boundaries
- **9 GSP points** showing demand/generation
- **8 Interconnectors** with flow arrows
- **7,072 generator sites** (optional overlay)

## 📊 Dashboard Layout Reference

```
┌─────────────────────────────────────────────────────┐
│ Row 1-5:   Headers, Status Bar, System Metrics      │
│ Row 7-17:  Fuel Breakdown (A-B) + ICs (D-E)         │
│ Row 28-42: Live Outages Table (A-H)                 │
├─────────────────────────────────────────────────────┤
│ Row 44:    📊 LIVE ANALYTICS HEADER                  │
│ Row 46:    🗺️ GB ENERGY MAP HEADER                   │
│ Row 47-60: Interactive Map Area (click menu)        │
│ Row 62:    📈 INTRADAY GENERATION HEADER             │
│ Row 64+:   Live Chart Data (SP × Fuel Type)         │
└─────────────────────────────────────────────────────┘
```

## 🔄 Auto-Refresh Behavior

### What Updates Every 5 Minutes
1. **Timestamp** (B2): Current date/time
2. **Chart Data** (A64+): Today's intraday generation by settlement period
3. **Map Data Sheets**: GSP demand, IC flows
4. **Status**: "✅ FRESH" indicator

### What Updates Less Frequently
- **DNO Boundaries**: Static (only refresh when schema changes)
- **Generator Coordinates**: Updated daily
- **Outages Table**: Updates via main dashboard script

## 🎮 Manual Controls

### Refresh Dashboard Data
```bash
# Method 1: From spreadsheet
Click: 🔄 Live Dashboard → 📊 Refresh All Data

# Method 2: From terminal
python3 enhanced_dashboard_updater.py
```

### View Auto-Refresh Status
```bash
# Method 1: From spreadsheet
Click: 🔄 Live Dashboard → ⚙️ Auto-Refresh: ON (5 min)

# Method 2: Check logs
tail -f logs/updater.log  # On server
```

### Update Charts Only
```bash
# From spreadsheet
Click: 🔄 Live Dashboard → 📈 Update Charts
```

## 🐛 Troubleshooting

### Map Doesn't Show
**Problem**: Rows 47-60 show placeholder text  
**Solution**: Install Apps Script code (see Step 2 above)

### Chart Data Empty
**Problem**: Rows 64+ are blank  
**Cause**: No data for today yet (early morning)  
**Solution**: Wait until first settlement period (00:30), then refresh

### Timestamp Not Updating
**Problem**: B2 shows old timestamp  
**Cause**: Auto-refresh not enabled  
**Solution**: Check cron job on server: `ssh root@94.237.55.234 'crontab -l'`

### "Unrecognized name" Error
**Problem**: BigQuery query fails  
**Cause**: Column name mismatch  
**Solution**: Check `STOP_DATA_ARCHITECTURE_REFERENCE.md` for correct schema

## 📈 Chart Configuration

The chart data (rows 64+) is formatted as:

```
A64: Settlement Period | B64: BIOMASS | C64: CCGT | ... | K64: WIND
A65: SP 1              | B65: 123.45  | C65: 5678 | ... | K65: 1234
A66: SP 2              | B66: 125.67  | C66: 5690 | ... | K66: 1245
...
```

To create charts in Google Sheets:
1. Select range A64:K150 (or current max period)
2. Insert → Chart
3. Chart type: Stacked column chart
4. X-axis: Settlement Period
5. Series: Each fuel type
6. Move chart to desired location in Dashboard sheet

## 🔐 Security & Access

### Service Account
- File: `inner-cinema-credentials.json`
- Permissions: Sheets write, BigQuery read
- Scope: This spreadsheet only (`12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`)

### API Keys
- Google Maps API: Required for interactive map (in Apps Script)
- BigQuery: Service account (no API key needed)

## 📊 Data Sources

### BigQuery Tables Used
- `bmrs_fuelinst` + `bmrs_fuelinst_iris`: Generation by fuel type
- `neso_gsp_boundaries`: 333 GSP areas with GEOGRAPHY boundaries
- `neso_dno_boundaries`: 14 DNO regions with GEOGRAPHY polygons
- `sva_generators_with_coords`: 7,072 generator locations
- `bmrs_indgen_iris`: Generation by boundary code

### Update Frequency
- **Historical tables** (`bmrs_*`): Updated every 15 minutes
- **Real-time tables** (`bmrs_*_iris`): Updated every 30 seconds
- **Dashboard refresh**: Every 5 minutes
- **Map data**: Every 5 minutes (GSPs, ICs), daily (DNO boundaries)

## 🎨 Styling

### Color Scheme (Dark Theme)
- Background: `#111111` (17, 17, 17)
- Text: `#ffffff` (255, 255, 255)
- Headers: `#e43835` (228, 56, 53) - Red accent
- Status bar: `#d8eaf6` (216, 234, 246) - Light blue

### Emoji Indicators
- 🔥 CCGT (gas)
- ⚛️ Nuclear
- 💨 Wind
- ☀️ Solar
- 🌱 Biomass
- 🇫🇷 France IC
- 🇳🇱 Netherlands IC
- 🇧🇪 Belgium IC

## 📞 Support

**Issues**: Check logs first
```bash
# Dashboard updater logs
tail -f logs/updater.log

# IRIS pipeline logs (if map data stale)
ssh root@94.237.55.234 'tail -f /opt/iris-pipeline/logs/iris_uploader.log'
```

**Questions**: See documentation
- `PROJECT_CONFIGURATION.md` - All settings
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data schema
- `MAP_INTEGRATION_COMPLETE.md` - Map technical details

## ✅ Verification Checklist

After deployment, verify:

- [ ] Dashboard sheet has rows 44, 46, 62 headers
- [ ] Map placeholder visible in rows 47-60
- [ ] Chart data visible in rows 64+ (after 00:30)
- [ ] Timestamp (B2) shows "LIVE AUTO-REFRESH"
- [ ] Apps Script menu shows "🔄 Live Dashboard"
- [ ] Map modal opens when clicking menu item
- [ ] Map shows 10 DNO regions, 9 GSPs, 8 ICs
- [ ] Auto-refresh updates B2 every 5 minutes
- [ ] Chart data updates with new settlement periods

---

**Next Steps**: See `DEPLOYMENT_NEXT_STEPS.md` for advanced features (real-time DNO generation, enhanced charts, mobile view)
