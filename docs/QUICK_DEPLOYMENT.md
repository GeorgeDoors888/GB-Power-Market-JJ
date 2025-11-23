# Quick Deployment Guide - Dual Server with Failover

## Deploy to UpCloud (94.237.55.234)

### 1. Upload Files
```bash
# From Dell/local machine
scp health_check_server.py root@94.237.55.234:/root/GB-Power-Market-JJ/
scp realtime_dashboard_updater.py root@94.237.55.234:/root/GB-Power-Market-JJ/
scp gsp_auto_updater.py root@94.237.55.234:/root/GB-Power-Market-JJ/
scp update_dashboard_preserve_layout.py root@94.237.55.234:/root/GB-Power-Market-JJ/
scp update_outages_enhanced.py root@94.237.55.234:/root/GB-Power-Market-JJ/
scp inner-cinema-credentials.json root@94.237.55.234:/root/GB-Power-Market-JJ/
```

### 2. Setup Cron Jobs
```bash
ssh root@94.237.55.234

# Edit crontab
crontab -e

# Add these lines:
GOOGLE_APPLICATION_CREDENTIALS=/root/GB-Power-Market-JJ/inner-cinema-credentials.json

*/5 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1
*/10 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 gsp_auto_updater.py >> logs/gsp_updater.log 2>&1
*/10 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 update_dashboard_preserve_layout.py >> logs/dashboard_main_updater.log 2>&1
*/10 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 update_outages_enhanced.py >> logs/outages_updater.log 2>&1
```

### 3. Start Health Check Server
```bash
ssh root@94.237.55.234

cd /root/GB-Power-Market-JJ
pip3 install flask

# Start in background
nohup python3 health_check_server.py >> logs/health_server.log 2>&1 &

# Test it works
curl http://localhost:8080/health
```

### 4. Verify IRIS Service Running
```bash
systemctl status iris-pipeline
systemctl enable iris-pipeline
systemctl start iris-pipeline
```

---

## Setup Dell Failover Monitor

### 1. Install Dependencies
```bash
pip3 install requests flask
```

### 2. Test Monitor (Foreground)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 monitor_and_failover.py
# Should show: ✅ UpCloud healthy
# Press Ctrl+C to stop
```

### 3. Run Monitor in Background
```bash
# Using nohup
nohup python3 monitor_and_failover.py >> failover_monitor.log 2>&1 &

# OR using screen (recommended)
screen -S failover
python3 monitor_and_failover.py
# Press Ctrl+A, then D to detach
# Reattach with: screen -r failover
```

### 4. Check Monitor Status
```bash
# Check if running
ps aux | grep monitor_and_failover

# View log
tail -f failover_monitor.log

# View last 50 lines
tail -50 failover_monitor.log
```

---

## Test Failover

### Simulate UpCloud Failure
```bash
# On UpCloud - stop services
ssh root@94.237.55.234
systemctl stop crond
# OR stop health server
pkill -f health_check_server
```

### Watch Dell Activate Failover
```bash
# On Dell - watch the monitor
tail -f failover_monitor.log

# Should see after 3 minutes:
# 🚨 FAILOVER ACTIVATED
# ✅ Started realtime_dashboard_updater.py (PID: ...)
# ✅ Started gsp_auto_updater.py (PID: ...)
# etc.
```

### Restore UpCloud
```bash
# On UpCloud
systemctl start crond
python3 health_check_server.py &

# On Dell - monitor should show:
# ✅ UPCLOUD RECOVERED
# ✅ Stopped realtime_dashboard_updater.py
# etc.
```

---

## Verification Checklist

### UpCloud Server
- [ ] Health check responds: `curl http://94.237.55.234:8080/health`
- [ ] Cron jobs active: `crontab -l`
- [ ] IRIS service running: `systemctl status iris-pipeline`
- [ ] Logs updating: `tail logs/dashboard_updater.log`
- [ ] Dashboard timestamp updating (check Google Sheets)

### Dell Server
- [ ] Monitor running: `ps aux | grep monitor_and_failover`
- [ ] Monitor log active: `tail -f failover_monitor.log`
- [ ] Shows UpCloud healthy status
- [ ] No failover services running: `ps aux | grep dashboard`

### Dashboard
- [ ] Open: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
- [ ] Check row 2: "Last Updated" timestamp within 10 minutes
- [ ] Fuel data current
- [ ] Outages showing correct count
- [ ] No duplicate TOTAL rows

---

## Troubleshooting

### Health Check Not Responding
```bash
# On UpCloud
ps aux | grep health_check
netstat -tulpn | grep 8080

# Restart if needed
pkill -f health_check_server
nohup python3 health_check_server.py >> logs/health_server.log 2>&1 &
```

### Monitor Shows False Failures
```bash
# Check network connectivity
ping 94.237.55.234

# Test health endpoint
curl http://94.237.55.234:8080/health

# Check firewall allows port 8080
```

### Cron Jobs Not Running
```bash
# On UpCloud
systemctl status crond
crontab -l

# Check logs
tail -f logs/dashboard_main_updater.log

# Run manually to test
cd /root/GB-Power-Market-JJ
python3 update_dashboard_preserve_layout.py
```

---

## Status Commands

### Quick Status Check
```bash
# On Dell - check everything
./check_dual_server_status.sh

# Or manually:
curl -s http://94.237.55.234:8080/health | python3 -m json.tool
ps aux | grep monitor_and_failover
tail -5 failover_monitor.log
```

### Dashboard Status
```bash
python3 -c "
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = sh.worksheet('Dashboard')

row2 = dashboard.get('A2')[0][0]
print(f'Dashboard: {row2}')
"
```

---

## Production Checklist

Before going live with dual-server setup:

- [ ] UpCloud cron jobs configured and tested
- [ ] IRIS service enabled and running
- [ ] Health check server running on port 8080
- [ ] Dell monitor running in background (screen/nohup)
- [ ] Firewall allows port 8080 on UpCloud
- [ ] Credentials file on both servers
- [ ] Test failover manually (stop/start services)
- [ ] Verify recovery works (monitor stops Dell services)
- [ ] Check Dashboard updates within 10 minutes
- [ ] Document current configuration
- [ ] Set up alerts (optional: email/Slack on failover)

---

*Deployment Date: November 23, 2025*  
*Architecture: Dual-Server with Automatic Failover*
