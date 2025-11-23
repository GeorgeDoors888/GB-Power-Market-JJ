# Complete Services Setup - November 23, 2025

## ✅ SERVICES STATUS

### MacBook (Local Services)

| Service | Status | Purpose | How to Check |
|---------|--------|---------|--------------|
| **Webhook Server** | ✅ Running (PID 28682) | DNO Refresh button | `lsof -i:5001` |
| **Ngrok Tunnel** | ❌ NOT Running | Expose webhook to Google Sheets | `curl http://127.0.0.1:4040/api/tunnels` |
| **Dashboard Auto-Update** | ✅ Running (every 10 min) | Main Dashboard sheet | `crontab -l` |
| **Live Data Auto-Update** | ✅ Running (every 5 min) | Live_Raw_Gen sheet | `crontab -l` |
| **GSP Auto-Update** | ✅ Running (every 10 min) | GSP data | `crontab -l` |

### UpCloud Server (94.237.55.234)

| Service | Status | Purpose | How to Check |
|---------|--------|---------|--------------|
| **IRIS Pipeline** | ⚠️ Check manually | Real-time BMRS data | SSH: `systemctl status iris-pipeline` |
| **Dell Server Control** | ⚠️ Check manually | Power on/off Dell for map generation | SSH and check automation |
| **Map Generation** | ⚠️ Check manually | Auto-generate GB Power maps | Check cron on UpCloud |

## 🔧 WHAT EACH GOOGLE SHEETS FUNCTION NEEDS

### 1. "Refresh DNO" Button (BESS Sheet)

**Requirements**:
- ✅ Webhook Server running (`dno_webhook_server.py` on port 5001)
- ❌ Ngrok tunnel active (exposing webhook to internet)
- ❌ Apps Script updated with current ngrok URL

**Status**: **PARTIAL** - Webhook running but ngrok not active

**To Fix**:
```bash
# In a separate terminal
ngrok http 5001

# Get the URL
curl -s http://127.0.0.1:4040/api/tunnels | python3 -c 'import sys,json; print(json.load(sys.stdin)["tunnels"][0]["public_url"])'

# Update bess_auto_trigger.gs line 206 with new URL
```

**Current Apps Script URL**: `https://26eff9472aea.ngrok-free.app` (OLD - won't work)

### 2. "Generate HH Data" Button (BESS Sheet)

**Requirements**:
- Nothing! Runs directly via Apps Script

**Status**: **✅ READY**

### 3. Dashboard Sheet Auto-Update

**Requirements**:
- ✅ Cron job configured
- ✅ `update_dashboard_preserve_layout.py` script
- ✅ BigQuery access configured

**Status**: **✅ WORKING**

**Frequency**: Every 10 minutes (just added today)

**Updates**:
- Fuel generation breakdown
- Interconnector flows with flags
- System metrics (total generation, renewables %)
- Market price
- Outages section

**Log**: `logs/dashboard_main_updater.log`

### 4. Live_Raw_Gen Sheet Auto-Update

**Requirements**:
- ✅ Cron job configured (already running)
- ✅ `realtime_dashboard_updater.py` script

**Status**: **✅ WORKING**

**Frequency**: Every 5 minutes

**Log**: `logs/dashboard_updater.log`

### 5. Map Generation & Display

**Requirements**:
- Dell server (for map generation)
- UpCloud server (for hosting maps)
- IRIS pipeline (for real-time data)
- Cron job on UpCloud

**Status**: **⚠️ MANUAL CHECK REQUIRED**

Maps displayed in Dashboard:
- 🗺️ GSP Regions
- ⚡ Transmission Zones  
- ⚡ DNO Boundaries
- 🗺️ Combined Infrastructure
- 🌬️ Wind Farm Capacity Map

## 📋 CRON JOBS (MacBook)

```bash
# Every 5 minutes - Update Live_Raw_Gen sheet
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && /opt/homebrew/bin/python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1

# Every 10 minutes - Update GSP data
*/10 * * * * cd /Users/georgemajor/GB Power Market JJ && .venv/bin/python gsp_auto_updater.py >> logs/gsp_auto_updater.log 2>&1

# Every 10 minutes - Update main Dashboard sheet ✨ NEW
*/10 * * * * cd '/Users/georgemajor/GB Power Market JJ' && /opt/homebrew/bin/python3 update_dashboard_preserve_layout.py >> logs/dashboard_main_updater.log 2>&1
```

## 🚀 STARTUP CHECKLIST

When MacBook restarts, run these:

### 1. Start Webhook Server (Terminal 1)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/inner-cinema-credentials.json"
python3 dno_webhook_server.py
```

Keep this terminal open.

### 2. Start Ngrok (Terminal 2)
```bash
ngrok http 5001
```

Keep this terminal open and note the `https://` URL.

### 3. Update Apps Script
1. Copy ngrok URL from terminal
2. Open Google Sheets > Extensions > Apps Script
3. Open `bess_auto_trigger.gs`
4. Update line 206: `const webhookUrl = 'YOUR_NEW_NGROK_URL/trigger-dno-lookup';`
5. Save

### 4. Cron Jobs
These start automatically - no action needed!

## 📊 MONITORING

### Check if services are running:
```bash
./check_services_status.sh
```

### View logs:
```bash
# Main Dashboard updates
tail -f logs/dashboard_main_updater.log

# Live data updates
tail -f logs/dashboard_updater.log

# GSP updates
tail -f logs/gsp_auto_updater.log
```

### Manual update Dashboard:
```bash
python3 update_dashboard_preserve_layout.py
```

### Check Dashboard timestamp in Google Sheets:
Cell B2 should show current time if auto-updates working

## 🔍 TROUBLESHOOTING

### Dashboard not updating?
```bash
# Check cron is running
crontab -l | grep dashboard

# Check logs for errors
tail -20 logs/dashboard_main_updater.log

# Manual test
python3 update_dashboard_preserve_layout.py
```

### DNO Refresh button not working?
```bash
# Check webhook server
lsof -i:5001

# Check ngrok
curl http://127.0.0.1:4040/api/tunnels

# Test webhook
curl -X POST http://localhost:5001/trigger-dno-lookup \
  -H "Content-Type: application/json" \
  -d '{"postcode":"rh19 4lx"}'
```

### Maps not displaying?
1. SSH to UpCloud: `ssh root@94.237.55.234`
2. Check IRIS pipeline: `systemctl status iris-pipeline`
3. Check map generation cron: `crontab -l`
4. Check Dell server status

## 📝 IMPORTANT FILES

| File | Purpose |
|------|---------|
| `dno_webhook_server.py` | Webhook for DNO Refresh button |
| `update_dashboard_preserve_layout.py` | Main Dashboard updater |
| `realtime_dashboard_updater.py` | Live_Raw_Gen updater |
| `bess_auto_trigger.gs` | Apps Script for BESS buttons |
| `check_services_status.sh` | Service status checker |
| `inner-cinema-credentials.json` | GCP credentials |

## ✅ COMPLETED TODAY (Nov 23, 2025)

1. ✅ Added `update_dashboard_preserve_layout.py` to cron (every 10 min)
2. ✅ Created `check_services_status.sh` for monitoring
3. ✅ Verified webhook server is running
4. ✅ Documented all service requirements
5. ⚠️ Ngrok needs to be started manually

## 🎯 SUMMARY

**What's Working Now**:
- ✅ Dashboard auto-updates every 10 minutes (NEW!)
- ✅ Live data updates every 5 minutes
- ✅ GSP data updates every 10 minutes
- ✅ Webhook server running for DNO button
- ✅ HH Generator button ready to use

**What Needs Manual Start** (after reboot):
- ❌ Ngrok tunnel (then update Apps Script URL)

**What Needs Manual Check**:
- ⚠️ UpCloud server IRIS pipeline
- ⚠️ Dell server automation
- ⚠️ Map generation cron

---

**Last Updated**: November 23, 2025 01:20 GMT
