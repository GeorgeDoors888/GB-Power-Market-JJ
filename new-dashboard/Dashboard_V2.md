# Dashboard V2 - Complete Architecture

**Version:** 2.0  
**Created:** 2025-11-25  
**Status:** ✅ Production Ready

## Overview

Clean rebuild of GB Energy Dashboard with proper version control, automated data refresh, and webhook architecture to avoid permission issues.

### Key Improvements over V1
- ✅ **clasp version control** for Apps Script
- ✅ **Python webhook architecture** (no permission conflicts)
- ✅ **Automated cron refresh** (adapted from realtime_dashboard_updater.py)
- ✅ **Clean data structure** (KPIs, BESS, Maps, Outages)
- ✅ **Working constraint & generator maps**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DASHBOARD V2 STACK                         │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │  Google Sheets   │
                    │   Dashboard V2   │
                    │ (Apps Script UI) │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Python Webhooks │
                    │  (Flask Server)  │
                    │  Port 5001       │
                    └────────┬─────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ BigQuery │  │  Sheets  │  │   BESS   │
         │   IRIS   │  │   API    │  │  Sheet   │
         └──────────┘  └──────────┘  └──────────┘
```

---

## Components

### 1. Google Sheets (UI Layer)

**Spreadsheet ID:** `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`  
**URL:** https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc

**Sheets:**
- `Dashboard` - KPIs, generation types, interconnectors, constraints
- `BESS` - Battery storage analysis, DNO lookup, DUoS rates
- `Generator Map Data` - Generator locations and capacity
- `Outages` - Current and planned outages

**Menus:**
- 🗺️ **Maps** → Constraint Map, Generator Map
- 🔄 **Data** → Copy from Old Dashboard, Copy BESS Sheet, Refresh

### 2. Apps Script (Code.gs)

**Deployed via clasp:**
```bash
cd new-dashboard
clasp push
```

**Key Functions:**
- `onOpen()` - Creates menus
- `showConstraintMap()` - Displays constraint map sidebar
- `getConstraintData()` - Fetches boundary data
- `copyFromOldDashboard()` - Calls webhook to copy data
- `refreshDashboard()` - Triggers data refresh

**Script ID:** `1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz`

### 3. Python Webhook Server (webhook_server.py)

**Flask server that handles all Sheets/BigQuery operations**

**Endpoints:**
```
GET  /health                 - Health check
POST /copy-dashboard-data    - Copy KPIs & constraints from old sheet
POST /copy-bess-data         - Copy BESS sheet structure
GET  /get-constraints        - Get current constraint data for map
POST /refresh-dashboard      - Query BigQuery, update sheet
```

**Start Server:**
```bash
cd new-dashboard
python3 webhook_server.py > webhook.log 2>&1 &
```

**Expose via ngrok:**
```bash
ngrok http 5001
```

### 4. Automated Refresh (auto_refresh_v2.py)

**Cron job that runs every 5 minutes**

```bash
# Add to crontab
*/5 * * * * cd /path/to/new-dashboard && python3 auto_refresh_v2.py >> logs/auto_refresh.log 2>&1
```

---

## Configuration

### Service Account Permissions

**Service Account:** `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`

**Must have Editor access to:**
- New Dashboard: `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`
- Old Dashboard: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`
- BESS Sheet: `1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx`

### Environment Variables

**File:** `config.env`
```bash
SPREADSHEET_ID=1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
SCRIPT_ID=1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz
SPREADSHEET_URL=https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
WEBHOOK_URL=http://localhost:5001  # or ngrok URL
```

---

## Deployment

### Initial Setup

1. **Create spreadsheet** (already done):
```bash
cd new-dashboard
clasp create --type sheets --title "GB Energy Dashboard V2"
```

2. **Deploy Apps Script code**:
```bash
clasp push
```

3. **Start webhook server**:
```bash
python3 webhook_server.py &
ngrok http 5001  # for remote access
```

4. **Share with service account**:
   - Open spreadsheet
   - Click Share
   - Add: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`
   - Give Editor access

5. **Copy data**:
   - Refresh spreadsheet
   - Menu: Data → Copy from Old Dashboard
   - Menu: Data → Copy BESS Sheet

6. **Test maps**:
   - Menu: Maps → Constraint Map
   - Should show 10 markers

### Updating Code

**Apps Script changes:**
```bash
cd new-dashboard
# Edit Code.gs or CopyData.gs
clasp push
```

**Python webhook changes:**
```bash
cd new-dashboard
# Edit webhook_server.py
pkill -f webhook_server.py
python3 webhook_server.py &
```

### Setting Up Cron

```bash
crontab -e

# Add line:
*/5 * * * * cd /Users/georgemajor/GB\ Power\ Market\ JJ/new-dashboard && python3 auto_refresh_v2.py >> logs/auto_refresh.log 2>&1
```

---

## Usage

### Refreshing Data

**Manual (via UI):**
- Menu: Data → Refresh Dashboard

**Manual (via webhook):**
```bash
curl -X POST http://localhost:5001/refresh-dashboard
```

**Automatic:**
- Cron runs every 5 minutes
- Updates all KPIs from BigQuery IRIS tables

### Viewing Maps

**Constraint Map:**
- Menu: Maps → Constraint Map
- Shows 10 GB transmission boundaries
- Color-coded by utilization (green/yellow/orange/red)

**Generator Map:**
- Menu: Maps → Generator Map
- Shows all UK generators with capacity and fuel type

### BESS Analysis

**DNO Lookup:**
- Enter MPAN in BESS sheet
- Click refresh button
- Python webhook queries BigQuery for DNO details
- Updates DUoS rates automatically

---

## Data Sources

### BigQuery Tables

**Project:** `inner-cinema-476211-u9`  
**Dataset:** `uk_energy_prod`

**Key Tables:**
- `bmrs_fuelinst_iris` - Generation by fuel type (real-time)
- `bmrs_inddem_iris` - Demand data (real-time)
- `bmrs_imbalngc` - System prices (real-time)
- `bmrs_boalf_iris` - Bid-offer acceptances
- `bmrs_freq` - Frequency data
- `bmrs_mels_iris` - Generator outages

### Original Dashboard Sections Preserved

**From:** `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`

- Rows 1-10: KPIs (demand, generation, interconnectors, prices)
- Rows 116-126: Transmission constraints
- BESS sheet: Full structure with DNO lookup and DUoS rates

---

## Maintenance

### Logs

```bash
# Webhook server logs
tail -f new-dashboard/webhook.log

# Auto-refresh logs
tail -f new-dashboard/logs/auto_refresh.log

# Apps Script logs
# View in: Extensions → Apps Script → Executions
```

### Troubleshooting

**Maps show blank:**
- Check constraint data exists in Dashboard A116:H126
- Verify coordinate lookup in BOUNDARY_COORDS

**Permission errors:**
- Confirm service account has Editor access
- Check `.clasp.json` has correct scriptId

**Webhook not responding:**
```bash
ps aux | grep webhook_server  # Check if running
curl http://localhost:5001/health  # Test endpoint
```

**Data not updating:**
- Check cron: `crontab -l`
- Check logs: `tail -f logs/auto_refresh.log`
- Verify BigQuery credentials

---

## Files

```
new-dashboard/
├── Code.gs                      # Main Apps Script
├── CopyData.gs                  # Data copy functions
├── webhook_server.py            # Flask webhook server
├── auto_refresh_v2.py           # Cron auto-refresh script
├── config.env                   # Configuration
├── .clasp.json                  # clasp configuration
├── appsscript.json              # Apps Script manifest
└── logs/
    ├── webhook.log              # Webhook server logs
    └── auto_refresh.log         # Cron job logs
```

---

## API Reference

### Webhook Endpoints

#### GET /health
```bash
curl http://localhost:5001/health
# Response: {"status": "ok", "service": "Dashboard V2 Webhook"}
```

#### POST /copy-dashboard-data
```bash
curl -X POST http://localhost:5001/copy-dashboard-data
# Response: {"success": true, "rows_copied": {"kpis": 10, "constraints": 11}}
```

#### POST /copy-bess-data
```bash
curl -X POST http://localhost:5001/copy-bess-data
# Response: {"success": true, "rows_copied": 100}
```

#### GET /get-constraints
```bash
curl http://localhost:5001/get-constraints
# Response: {"success": true, "constraints": [{boundary, flow, limit, ...}]}
```

#### POST /refresh-dashboard
```bash
curl -X POST http://localhost:5001/refresh-dashboard
# Response: {"success": true, "updated": {...}, "timestamp": "..."}
```

---

## Theme & Styling

**Upower Energy Colors:**
- Primary Blue: `#0072ce`
- Accent Orange: `#ff7f0f`
- Success Green: `#7ac943`
- Neutral Grey: `#bdbdbd`

**Applied to:**
- KPI categories (color-coded by system)
- Chart series (generation, demand, interconnectors)
- Map markers (utilization thresholds)

---

## Security

- Service account credentials stored in `inner-cinema-credentials.json`
- Webhook server runs on localhost (or secured ngrok)
- No public API keys in code
- Sheet-level permissions via Google Drive sharing

---

## Support

**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer:** George Major (george@upowerenergy.uk)  
**Documentation:** This file + inline code comments

---

## Changelog

**v2.0 (2025-11-25)**
- Initial Dashboard V2 release
- Implemented webhook architecture
- Set up clasp version control
- Migrated KPIs, constraints, BESS structure
- Created working constraint map
- Configured automated refresh

---

## Next Steps

1. ✅ **Complete data migration** (copy remaining dashboard sections)
2. ✅ **Test all maps** (constraint + generator)
3. ✅ **Set up cron job** (automated refresh)
4. ⏳ **Deploy generator map** with live data
5. ⏳ **Add more charts** (generation mix, price trends)
6. ⏳ **Integrate BESS DNO webhook** (replace manual button)

---

**Last Updated:** 2025-11-25  
**Status:** ✅ Core infrastructure complete, ready for data population
