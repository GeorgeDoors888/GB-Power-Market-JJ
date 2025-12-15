# GB Live Dashboard - Apps Script Deployment

## Overview
Executive-grade Google Sheets dashboard with:
- ⚡ Interactive menu (Refresh Data, Rebuild Layout, Toggle Theme)
- 📊 8 KPI metrics with multiple sparkline visualizations
- 🚦 Wind prediction traffic light system
- 🌓 Light/Dark theme toggle
- 📝 Automatic changelog tracking
- ⏱️ 5-minute data caching

## Quick Deploy

### 1. Deploy Apps Script
```bash
cd /home/george/GB-Power-Market-JJ/apps-script
clasp push
```

### 2. Open Google Sheets
- Go to your spreadsheet: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
- Refresh the page
- You should see "⚡ GB Live Dashboard" menu appear

### 3. Build Layout
- Click: **⚡ GB Live Dashboard** > **✨ Rebuild Layout**
- Creates 4 sheets: `GB Live`, `raw_live_data`, `config_live`, `changelog`
- Sets up 8 KPI rows with headers and formatting

### 4. Configure API URL (IMPORTANT!)
Before refreshing data, update the API URL in the script:

**Option A: iMac (Local)**
```javascript
const API_URL = "http://localhost:5002/query_bigquery";
```

**Option B: Dell UpCloud Server**
```javascript
const API_URL = "http://UPCLOUD_IP:5002/query_bigquery";
```

**Option C: ngrok Tunnel (Public Access)**
```javascript
const API_URL = "https://YOUR_NGROK_URL.ngrok.io/query_bigquery";
```

### 5. Test Refresh
- Click: **⚡ GB Live Dashboard** > **🔄 Refresh Data**
- Select timeframe: Daily / Weekly / Monthly
- Watch KPIs populate with sparklines

## Features

### Dashboard Layout (GB Live Sheet)
| Range | Content | Description |
|-------|---------|-------------|
| A1:H1 | Header | "⚡ GB Live Dashboard — Automated KPI Feed" (blue #1E88E5) |
| A2:H2 | Status Banner | System status with timestamps |
| B3:B4 | Timeframe Selector | Dropdown: Daily / Weekly / Monthly |
| A6:L6 | KPI Headers | 12 columns: Metric, Value, Delta, 5 Sparklines, Traffic, % |
| A7:L14 | 8 KPI Rows | Revenue, Profit, Export, Import, Availability, Arbitrage, Wind Pred/Act |

### 8 KPI Metrics
1. 💷 **Total Revenue (£)** - Sum of export revenue
2. ⚙️ **Net Profit (£)** - Revenue minus import costs
3. ⚡ **Export MWh** - Total energy exported
4. 🔌 **Import MWh** - Total energy imported
5. 🧭 **Availability %** - System availability (placeholder)
6. 🔁 **Arbitrage £/MWh** - Profit per MWh
7. 🌬️ **Wind Predicted MWh** - Forecasted wind generation
8. 🌬️ **Wind Actual MWh** - Real wind generation

### Sparkline Visualizations (Per Row)
| Column | Type | Color | Description |
|--------|------|-------|-------------|
| D | Line | Blue #1976D2 | Trend over time |
| E | Column (Gradient) | Red→Yellow→Green | Heatmap visualization |
| F | Line | Green #43A047 | 7-day rolling average |
| G | Area | Purple #AB47BC | Filled area chart |
| H | Win/Loss | Teal #009688 | Above/below average bars |

### Wind Traffic Light (Row 13)
- **Column I**: 🟩 🟨 🟥 Traffic light icon
- **Column J**: Percentage (Actual / Predicted × 100%)
- **Column K**: Status text
  - 🟩 **On Target** (≥95%) - Green #33CC33
  - 🟨 **Watch** (≥85%) - Yellow #FFCC00
  - 🟥 **Under-Gen** (<85%) - Red #FF3333

### Theme Toggle
- **Light Theme**: White background, blue header
- **Dark Theme**: Dark grey #263238 header, #37474F background, light text
- Persists across sessions using DocumentProperties

## Data Flow

```
BigQuery → Python FastAPI → Apps Script → Google Sheets
  ↓             ↓               ↓              ↓
bmrs_*      gb_live_api.py   UrlFetchApp   Sparklines
tables      (port 5002)      (POST)        Formatting
```

## Configuration

### Update API URL in GBLiveDashboard.gs
```javascript
const API_URL = "http://localhost:5002/query_bigquery";
const BEARER_TOKEN = "Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA";
```

### BigQuery Tables Queried
The script expects these columns in the API response:
- `settlementDate`, `settlementPeriod`
- `marketIndexPrice`, `systemBuyPrice`, `systemSellPrice`
- `exportMWh`, `importMWh`
- `predictedWindMWh`, `actualWindMWh`, `generationGapMWh`

## Troubleshooting

### Menu not appearing
```bash
# Redeploy script
cd /home/george/GB-Power-Market-JJ/apps-script
clasp push

# Refresh spreadsheet
# Clear browser cache
# Check Extensions > Apps Script for errors
```

### "Python API not responding"
```bash
# Check if API is running
curl http://localhost:5002/health

# Start FastAPI server (see gb_live_api.py)
python3 gb_live_api.py
```

### Sparklines not rendering
- Check that raw_live_data sheet has data
- Verify formulas in columns D-H use correct syntax
- Check for NaN or null values in data

### Theme not persisting
- Check DocumentProperties permissions
- Clear script cache: Tools > Script editor > Run > Clear all

## Next Steps
1. Deploy Python FastAPI server (Task 2)
2. Test data refresh (Task 8)
3. Verify sparklines render (Task 9)
4. Test traffic light logic (Task 10)
5. Test theme toggle (Task 11)

## Files
- `GBLiveDashboard.gs` - Main Apps Script (340 lines)
- `.clasp.json` - Clasp configuration
- `appsscript.json` - Apps Script manifest

## Support
See main README: `/home/george/GB-Power-Market-JJ/BG_LIVE_UPDATER_README.md`
