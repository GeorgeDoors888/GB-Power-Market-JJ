# GSP Auto-Refresh Setup Guide
**Last Updated**: November 10, 2025

## 🎯 Overview

The **GSP Auto-Updater** refreshes Grid Supply Point (GSP) import/export data on the Dashboard every 10 minutes, providing live tracking of regional power flows across the UK grid.

### Data Update Frequency
- **BigQuery IRIS data**: Updates every **~30 minutes** (some 60-min gaps)
- **Recommended refresh**: Every **10 minutes** (catches new data quickly)
- **Current snapshot**: 2025-11-10 09:16 UTC (18 GSPs, 0 exporters, 17 importers, 1 balanced)

---

## 📊 What Gets Updated

### Dashboard Location: Row 55+

**Header (Row 55)**:
```
📊 GSP ANALYSIS | Wind: 13,323 MW | Updated: 2025-11-10 09:16:00 UTC
```

**Generation Table (Columns A-D, Row 57+)**:
- Shows GSPs **exporting** power to the grid
- Columns: Emoji | GSP | Region | Export (MW)
- Green header background
- Currently: "No exporters at this time" (morning demand peak)

**Demand Table (Columns H-K, Row 57+)**:
- Shows GSPs **importing** power from the grid
- Columns: Emoji | GSP | Region | Import (MW)  
- Red header background
- Currently: 17 importers + 1 balanced = 18 total

### Status Emojis
- 🟢 **Exporting** (net flow > 100 MW)
- 🔴 **Importing** (net flow < -100 MW)
- ⚪ **Balanced** (-100 to +100 MW)

---

## ⚙️ Auto-Update Setup

### Option 1: Cron (macOS/Linux) - RECOMMENDED

**Step 1**: Open crontab editor
```bash
crontab -e
```

**Step 2**: Add this line (updates every 10 minutes)
```bash
*/10 * * * * cd ~/GB\ Power\ Market\ JJ && .venv/bin/python gsp_auto_updater.py >> logs/gsp_auto_updater.log 2>&1
```

**Step 3**: Save and verify
```bash
crontab -l  # List current cron jobs
```

**Step 4**: Create logs directory
```bash
mkdir -p ~/GB\ Power\ Market\ JJ/logs
```

### Option 2: Systemd Timer (Linux Server)

**Create timer file**: `/etc/systemd/system/gsp-updater.timer`
```ini
[Unit]
Description=GSP Auto-Updater Timer (every 10 min)

[Timer]
OnBootSec=5min
OnUnitActiveSec=10min
Unit=gsp-updater.service

[Install]
WantedBy=timers.target
```

**Create service file**: `/etc/systemd/system/gsp-updater.service`
```ini
[Unit]
Description=GSP Auto-Updater Service

[Service]
Type=oneshot
WorkingDirectory=/root/GB Power Market JJ
ExecStart=/root/GB Power Market JJ/.venv/bin/python gsp_auto_updater.py
StandardOutput=append:/root/GB Power Market JJ/logs/gsp_auto_updater.log
StandardError=append:/root/GB Power Market JJ/logs/gsp_auto_updater.log
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gsp-updater.timer
sudo systemctl start gsp-updater.timer
sudo systemctl status gsp-updater.timer
```

---

## 🔧 Manual Update

Anytime you want to refresh GSP data manually:

```bash
cd ~/GB\ Power\ Market\ JJ
.venv/bin/python gsp_auto_updater.py
```

**Expected output**:
```
================================================================================
🔄 GSP AUTO-UPDATER
================================================================================
🔒 Locking Dashboard formatting...
✅ Formatting locked
📡 Fetching latest GSP data from BigQuery...
✅ Retrieved 18 GSPs
   Data timestamp: 2025-11-10 09:16:00+00:00
   Wind timestamp: 2025-11-10 08:55:00+00:00
   National wind: 13,323.0 MW

📊 GSP SUMMARY:
   Exporters: 0
   Importers: 17
   Balanced: 1

✍️ Updating Dashboard...
   ℹ️ No exporters currently
   ✅ Demand table: 18 importers/balanced

✅ UPDATE COMPLETE
   🔗 https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
================================================================================
```

---

## 📋 GSP Reference

### All 18 Grid Supply Points

| GSP ID | Region Name | Current Status (09:16 UTC) |
|--------|-------------|----------------------------|
| N | London Core | 🔴 Major Import (-19,147.8 MW) |
| B1 | Scottish Hydro | 🔴 Import (-71.0 MW) |
| B2 | Southern Scotland | 🔴 Import (-2,062.5 MW) |
| B3 | Yorkshire | 🔴 Import (-3,006.2 MW) |
| B4 | North Wales | 🔴 Import (-1,459.8 MW) |
| B5 | Midlands | 🔴 Import (-3,823.8 MW) |
| B6 | Eastern | 🔴 Import (-7,009.7 MW) |
| B7 | East Midlands | 🔴 Import (-2,967.2 MW) |
| B8 | North West | 🔴 Import (-2,808.5 MW) |
| B9 | East Anglia | 🔴 Import (-7,554.7 MW) |
| B10 | South Wales | 🔴 Import (-1,135.0 MW) |
| B11 | South West | 🔴 Import (-2,269.0 MW) |
| B12 | Southern | 🔴 Import (-5,447.0 MW) |
| B13 | London | 🔴 Import (-5,961.7 MW) |
| B14 | South East | 🔴 Import (-6,127.8 MW) |
| B15 | South Coast | 🔴 Import (-1,943.8 MW) |
| B16 | Humber | 🔴 Import (-1,792.0 MW) |
| B17 | North Scotland | ⚪ Balanced (+57.5 MW) |

**Total Import**: ~74,588 MW (across 17 GSPs)  
**National Wind**: 13,323 MW (~18% of demand)

---

## 🎨 Formatting Lock

The script **preserves Dashboard formatting** during updates:

### Colors
- **Row 2**: Light blue (#D9EBF7) - Last updated timestamp
- **Row 3**: Yellow (#FFEFCC) - Data freshness legend
- **Row 4**: Blue (#3399D9) - System metrics header
- **Row 7 (A-C)**: Green (#66D966) - Fuel breakdown
- **Row 7 (D-F)**: Blue (#66B3E6) - Interconnectors
- **Row 32**: Red (#F26666) - Outages header
- **Row 55**: Blue - GSP Analysis header
- **Row 57 (A-D)**: Green (#66D966) - Generation table header
- **Row 57 (H-K)**: Red (#F26666) - Demand table header

### Column Widths
- **A**: 220px (section headers)
- **B**: 120px (data values)
- **C**: 120px (data values)
- **D**: 220px (right section headers)
- **E**: 150px (right data values)
- **F**: 180px (right data values)

---

## 🐛 Troubleshooting

### Check Cron is Running
```bash
# View cron logs (macOS)
tail -f ~/GB\ Power\ Market\ JJ/logs/gsp_auto_updater.log

# Check last update time in Dashboard (Row 2)
# Should update every 10 minutes
```

### Check BigQuery Data Freshness
```bash
cd ~/GB\ Power\ Market\ JJ
.venv/bin/python << 'EOF'
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
client = bigquery.Client(credentials=creds, project='inner-cinema-476211-u9')

query = """
SELECT MAX(publishTime) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem_iris`
"""

df = client.query(query).to_dataframe()
latest = df.iloc[0]['latest']
age = (datetime.now(latest.tzinfo) - latest).total_seconds() / 60

print(f"Latest GSP data: {latest}")
print(f"Age: {age:.1f} minutes")
print(f"Status: {'✅ Fresh' if age < 60 else '⚠️ Stale'}")
EOF
```

### Common Issues

**1. "ModuleNotFoundError: gspread"**
```bash
cd ~/GB\ Power\ Market\ JJ
.venv/bin/pip install gspread google-cloud-bigquery pandas
```

**2. "Permission denied: inner-cinema-credentials.json"**
```bash
chmod 600 ~/GB\ Power\ Market\ JJ/inner-cinema-credentials.json
```

**3. "Cron not running"**
- Check crontab: `crontab -l`
- Verify cron service: `sudo systemctl status cron` (Linux)
- Check logs: `tail -f ~/GB\ Power\ Market\ JJ/logs/gsp_auto_updater.log`

**4. "Data not updating in Dashboard"**
- Manually run: `.venv/bin/python gsp_auto_updater.py`
- Check Google Sheets permissions
- Verify service account has access to Dashboard

---

## 📈 Expected Behavior

### Typical Daily Pattern

**Morning (06:00-09:00)**: 
- All GSPs importing (demand peak)
- Wind: Variable (5-15 GW)
- London Core: Highest import (~20 GW)

**Midday (12:00-15:00)**:
- Some GSPs may export (solar peak)
- Wind: Variable
- Scotland often exports

**Evening (17:00-20:00)**:
- All GSPs importing (evening peak)
- Wind: Variable
- Highest system stress

**Night (22:00-04:00)**:
- Reduced imports
- Wind often high
- Scotland/North may export

### When to Expect Exporters

- **High wind days** (>15 GW national wind)
- **Scottish GSPs** (B1, B2, B17) most likely
- **East Anglia** (B9) during high offshore wind
- **Midday solar peaks** (summer only)

---

## 🔗 Integration

### Dashboard Auto-Refresh
GSP updater works alongside **realtime_dashboard_updater.py** (runs every 5 min):

```bash
# View both cron jobs
crontab -l

# Should see:
*/5 * * * * cd ~/GB\ Power\ Market\ JJ && .venv/bin/python realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1
*/10 * * * * cd ~/GB\ Power\ Market\ JJ && .venv/bin/python gsp_auto_updater.py >> logs/gsp_auto_updater.log 2>&1
```

### Future Enhancements

**Phase 2**: VLP Battery Integration
- Map battery BMUs to GSPs
- Show battery contribution to export/import
- Correlate with market prices

**Phase 3**: Historical Trends
- Show 24-hour sparklines
- Identify peak import/export times
- Predict next hour's flow direction

**Phase 4**: Alerts
- Notify when GSP flips (import → export)
- High import warnings
- Grid stress indicators

---

## 📚 Related Documentation

- **DASHBOARD_STRUCTURE_LOCKED.md** - Complete Dashboard reference
- **GSP_WIND_ANALYSIS_COMPLETE.md** - Technical implementation details
- **AUTO_REFRESH_COMPLETE.md** - Dashboard auto-refresh guide
- **PROJECT_CONFIGURATION.md** - BigQuery and API settings

---

## ✅ Setup Checklist

- [ ] Script tested manually (`python gsp_auto_updater.py`)
- [ ] Logs directory created (`mkdir -p logs`)
- [ ] Cron job added (`crontab -e`)
- [ ] Cron job verified (`crontab -l`)
- [ ] Wait 10 minutes, check Dashboard updates
- [ ] Check logs (`tail -f logs/gsp_auto_updater.log`)
- [ ] Verify formatting preserved (colors, widths intact)
- [ ] Bookmark Dashboard: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

---

**🎉 Status**: GSP auto-refresh is production-ready!  
**📊 Dashboard**: Live tracking every 10 minutes  
**⚡ Next Step**: Schedule the cron job and monitor for 1 hour
