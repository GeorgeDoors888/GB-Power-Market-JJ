# BESS UpCloud Deployment Guide

## 🎯 Overview

This guide will help you deploy the BESS auto-monitor and webhook server to your UpCloud server (94.237.55.234).

## 📋 What Gets Deployed

### 1. **BESS Auto-Monitor** (`bess-monitor.service`)
- **Monitors cells**: A6 (Postcode), B6 (MPAN), I6, J6
- **Check interval**: 30 seconds
- **Auto-triggers**: DNO lookup when any cell changes
- **Caching**: 1-hour TTL to reduce API calls
- **Logs**: `/var/log/bess/monitor.log`

### 2. **DNO Webhook Server** (`bess-webhook.service`)
- **Port**: 5001
- **Endpoints**:
  - `POST /trigger-dno-lookup` - Trigger DNO lookup
  - `POST /generate-hh-profile` - Generate HH profile
  - `GET /health` - Health check
  - `GET /status` - System status
- **Logs**: `/var/log/bess/webhook.log`

### 3. **Supporting Files**
- `dno_lookup_python.py` - Main DNO lookup script
- `generate_hh_profile.py` - HH profile generator
- `mpan_generator_validator.py` - MPAN validation
- `inner-cinema-credentials.json` - BigQuery credentials

## 🚀 Deployment Steps

### Step 1: Prepare Deployment

Ensure you're in the project directory and have the credentials file:

```bash
cd ~/GB\ Power\ Market\ JJ

# Check credentials file exists
ls -l inner-cinema-credentials.json
```

### Step 2: Run Deployment Script

```bash
./deploy_bess_to_upcloud.sh
```

**What the script does:**
1. ✅ Tests SSH connection to UpCloud server
2. 📁 Creates directories: `/opt/bess`, `/var/log/bess`, `/root/.google-credentials`
3. 🔑 Copies credentials file securely
4. 📄 Copies all Python scripts
5. ⚙️ Copies systemd service files
6. 📦 Installs Python dependencies
7. 🔄 Enables and starts services
8. 📊 Shows service status

**Expected output:**
```
==========================================
🚀 BESS DEPLOYMENT TO UPCLOUD
==========================================
Target: root@94.237.55.234
Project Dir: /opt/bess

✅ Credentials file found locally
🔍 Testing SSH connection...
✅ SSH connection successful
📁 Creating directories on server...
✅ Directories created
🔑 Copying credentials file...
✅ Credentials copied
📄 Copying Python scripts...
✅ Python scripts copied
⚙️  Copying systemd service files...
✅ Service files copied
📦 Installing dependencies and setting up services...
✅ Services configured and started
🔍 Checking service status...

📊 BESS Monitor Status:
● bess-monitor.service - BESS Auto-Monitor Service
   Active: active (running)

🌐 BESS Webhook Status:
● bess-webhook.service - BESS DNO Webhook Server
   Active: active (running)

==========================================
✅ DEPLOYMENT COMPLETE!
==========================================
```

### Step 3: Verify Deployment

```bash
# Check monitor status
ssh root@94.237.55.234 'systemctl status bess-monitor'

# Check webhook status
ssh root@94.237.55.234 'systemctl status bess-webhook'

# Test webhook health
curl http://94.237.55.234:5001/health

# Test system status
curl http://94.237.55.234:5001/status
```

### Step 4: View Logs

```bash
# Monitor logs (real-time)
ssh root@94.237.55.234 'tail -f /var/log/bess/monitor.log'

# Webhook logs (real-time)
ssh root@94.237.55.234 'tail -f /var/log/bess/webhook.log'

# Last 50 lines of monitor log
ssh root@94.237.55.234 'tail -50 /var/log/bess/monitor.log'

# Check for errors
ssh root@94.237.55.234 'tail -50 /var/log/bess/monitor-error.log'
ssh root@94.237.55.234 'tail -50 /var/log/bess/webhook-error.log'
```

## 🧪 Testing

### Test 1: Auto-Monitor Detection

1. **Check current values**:
   ```bash
   ssh root@94.237.55.234 'tail -20 /var/log/bess/monitor.log'
   ```

2. **Edit cell in Google Sheets**:
   - Open BESS sheet
   - Change value in A6, B6, I6, or J6
   - Wait 30 seconds

3. **Verify detection**:
   ```bash
   ssh root@94.237.55.234 'tail -20 /var/log/bess/monitor.log'
   ```
   
   You should see:
   ```
   🔔 CHANGE DETECTED at 17:30:45
      Previous: ('old_value', 'old_mpan', '', '')
      Current:  ('new_value', 'new_mpan', '', '')
   🔄 Cache miss - triggering lookup
   ```

### Test 2: Webhook Endpoint

```bash
# Test health endpoint
curl http://94.237.55.234:5001/health

# Expected response:
{
  "status": "ok",
  "message": "DNO Webhook Server running",
  "timestamp": "2025-11-24T17:30:00",
  "project_dir": "/opt/bess",
  "credentials": "configured"
}

# Test status endpoint
curl http://94.237.55.234:5001/status

# Expected response:
{
  "status": "ok",
  "monitor_running": true,
  "scripts": {
    "dno_lookup_python.py": true,
    "generate_hh_profile.py": true,
    "bess_auto_monitor.py": true,
    "credentials": true
  }
}
```

### Test 3: Manual DNO Lookup Trigger

```bash
# Trigger DNO lookup via webhook
curl -X POST http://94.237.55.234:5001/trigger-dno-lookup \
  -H "Content-Type: application/json" \
  -d '{
    "postcode": "RH19 4LX",
    "mpan_id": "14",
    "voltage": "HV"
  }'

# Check logs for execution
ssh root@94.237.55.234 'tail -30 /var/log/bess/webhook.log'
```

## 🔧 Management Commands

### Start/Stop/Restart Services

```bash
# Stop monitor
ssh root@94.237.55.234 'systemctl stop bess-monitor'

# Start monitor
ssh root@94.237.55.234 'systemctl start bess-monitor'

# Restart monitor
ssh root@94.237.55.234 'systemctl restart bess-monitor'

# Stop webhook
ssh root@94.237.55.234 'systemctl stop bess-webhook'

# Start webhook
ssh root@94.237.55.234 'systemctl start bess-webhook'

# Restart webhook
ssh root@94.237.55.234 'systemctl restart bess-webhook'

# Restart both
ssh root@94.237.55.234 'systemctl restart bess-monitor bess-webhook'
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
ssh root@94.237.55.234 'systemctl enable bess-monitor'
ssh root@94.237.55.234 'systemctl enable bess-webhook'

# Disable auto-start
ssh root@94.237.55.234 'systemctl disable bess-monitor'
ssh root@94.237.55.234 'systemctl disable bess-webhook'
```

### View Service Logs

```bash
# View systemd journal for monitor
ssh root@94.237.55.234 'journalctl -u bess-monitor -f'

# View systemd journal for webhook
ssh root@94.237.55.234 'journalctl -u bess-webhook -f'

# View last 100 lines
ssh root@94.237.55.234 'journalctl -u bess-monitor -n 100'
```

## 🔍 Troubleshooting

### Issue: Services Not Starting

**Check status:**
```bash
ssh root@94.237.55.234 'systemctl status bess-monitor bess-webhook'
```

**Check logs:**
```bash
ssh root@94.237.55.234 'journalctl -u bess-monitor -n 50'
ssh root@94.237.55.234 'tail -50 /var/log/bess/monitor-error.log'
```

**Common fixes:**
```bash
# Re-deploy with fresh files
./deploy_bess_to_upcloud.sh

# Check Python dependencies
ssh root@94.237.55.234 'pip3 list | grep -E "gspread|google-cloud|flask"'

# Check credentials
ssh root@94.237.55.234 'ls -la /root/.google-credentials/inner-cinema-credentials.json'

# Test credentials manually
ssh root@94.237.55.234 'cd /opt/bess && python3 -c "from google.cloud import bigquery; client = bigquery.Client(project=\"inner-cinema-476211-u9\"); print(\"OK\")"'
```

### Issue: Monitor Not Detecting Changes

**Check if monitor is running:**
```bash
ssh root@94.237.55.234 'ps aux | grep bess_auto_monitor'
```

**Check monitor logs:**
```bash
ssh root@94.237.55.234 'tail -f /var/log/bess/monitor.log'
```

**Manual test:**
```bash
ssh root@94.237.55.234 'cd /opt/bess && python3 bess_auto_monitor_upcloud.py --stats'
```

### Issue: Webhook Returns Error

**Check webhook is listening:**
```bash
ssh root@94.237.55.234 'netstat -tlnp | grep 5001'
```

**Test from server:**
```bash
ssh root@94.237.55.234 'curl http://localhost:5001/health'
```

**Check firewall:**
```bash
ssh root@94.237.55.234 'firewall-cmd --list-ports'

# If port 5001 not open:
ssh root@94.237.55.234 'firewall-cmd --add-port=5001/tcp --permanent && firewall-cmd --reload'
```

### Issue: "Connection Refused" from Apps Script

**Problem**: Apps Script can't reach webhook

**Solution 1**: Open firewall port
```bash
ssh root@94.237.55.234 'firewall-cmd --add-port=5001/tcp --permanent && firewall-cmd --reload'
```

**Solution 2**: Use ngrok tunnel
```bash
ssh root@94.237.55.234 'ngrok http 5001'
# Update webhook URL in Apps Script to ngrok URL
```

**Solution 3**: Check UpCloud firewall rules in web console

## 📊 Monitoring Dashboard

Create a simple monitoring script:

```bash
# Save as check_bess_status.sh
#!/bin/bash
echo "🔋 BESS System Status"
echo "===================="
ssh root@94.237.55.234 << 'EOF'
  echo "Monitor: $(systemctl is-active bess-monitor)"
  echo "Webhook: $(systemctl is-active bess-webhook)"
  echo ""
  echo "Last 5 monitor log lines:"
  tail -5 /var/log/bess/monitor.log
  echo ""
  echo "Webhook health:"
  curl -s http://localhost:5001/health | python3 -m json.tool
EOF
```

## 🔄 Updates & Redeployment

To update the scripts after making changes:

```bash
# Re-run deployment script
./deploy_bess_to_upcloud.sh

# Or manually copy specific file:
scp bess_auto_monitor_upcloud.py root@94.237.55.234:/opt/bess/
ssh root@94.237.55.234 'systemctl restart bess-monitor'
```

## 📝 File Locations on Server

```
/opt/bess/
├── bess_auto_monitor_upcloud.py    # Monitor script
├── dno_webhook_server_upcloud.py   # Webhook server
├── dno_lookup_python.py            # DNO lookup
├── generate_hh_profile.py          # HH profile generator
└── mpan_generator_validator.py     # MPAN validator

/etc/systemd/system/
├── bess-monitor.service            # Monitor systemd service
└── bess-webhook.service            # Webhook systemd service

/var/log/bess/
├── monitor.log                     # Monitor stdout
├── monitor-error.log               # Monitor stderr
├── webhook.log                     # Webhook stdout
├── webhook-error.log               # Webhook stderr
└── webhook_requests.log            # Webhook request history

/root/.google-credentials/
└── inner-cinema-credentials.json   # BigQuery credentials
```

## ✅ Post-Deployment Checklist

- [ ] Services running: `systemctl status bess-monitor bess-webhook`
- [ ] Health check passes: `curl http://94.237.55.234:5001/health`
- [ ] Monitor detecting changes (edit A6/B6/I6/J6 and check logs)
- [ ] Webhook accessible from Apps Script
- [ ] Logs rotating properly
- [ ] Services enabled for auto-start on boot
- [ ] Firewall port 5001 open (if needed)
- [ ] Apps Script updated with correct webhook URL

## 🎉 Success!

Your BESS system is now running on UpCloud! 

**What happens now:**
1. Monitor checks A6, B6, I6, J6 every 30 seconds
2. When any cell changes, DNO lookup auto-triggers
3. Results cached for 1 hour (reduces API calls)
4. Status bar in BESS sheet updates in real-time
5. Google Apps Script can trigger webhooks directly

**Test it:**
- Edit A6 or B6 in BESS sheet
- Wait 30 seconds
- Check logs: `ssh root@94.237.55.234 'tail -20 /var/log/bess/monitor.log'`
- You should see change detection and lookup execution

---

**Questions?** Check logs first:
```bash
ssh root@94.237.55.234 'tail -f /var/log/bess/monitor.log'
```

Last Updated: 2025-11-24
