# 🚀 BESS UpCloud Setup - Quick Start

## What Was Created

### ✅ Python Scripts (3 files)
1. **`bess_auto_monitor_upcloud.py`** (320 lines)
   - Monitors cells: **A6, B6, I6, J6**
   - Auto-triggers DNO lookup on changes
   - 30-second check interval
   - 1-hour cache TTL

2. **`dno_webhook_server_upcloud.py`** (290 lines)
   - Flask server on port 5001
   - Endpoints: `/trigger-dno-lookup`, `/generate-hh-profile`, `/health`, `/status`
   - Request logging to `/var/log/bess/webhook_requests.log`

3. **`bess_custom_menu.gs`** (Updated)
   - Webhook URL changed to: `http://94.237.55.234:5001/trigger-dno-lookup`
   - Ready to use from Google Sheets

### ✅ Systemd Services (2 files)
1. **`bess-monitor.service`**
   - Auto-monitor daemon
   - Logs: `/var/log/bess/monitor.log`
   - Auto-restart on failure

2. **`bess-webhook.service`**
   - Webhook server daemon
   - Logs: `/var/log/bess/webhook.log`
   - Auto-restart on failure

### ✅ Deployment Script
**`deploy_bess_to_upcloud.sh`** (executable)
- One-command deployment
- Copies all files to UpCloud
- Installs dependencies
- Starts services
- Shows status

### ✅ Documentation
**`BESS_UPCLOUD_DEPLOYMENT.md`**
- Complete deployment guide
- Testing procedures
- Troubleshooting steps
- Management commands

---

## 🎯 Deploy Now (3 Steps)

### Step 1: Test SSH Connection
```bash
ssh root@94.237.55.234 "echo 'Connected!'"
```

### Step 2: Run Deployment
```bash
cd ~/GB\ Power\ Market\ JJ
./deploy_bess_to_upcloud.sh
```

**Takes ~2-3 minutes**

### Step 3: Verify
```bash
# Check services are running
ssh root@94.237.55.234 'systemctl status bess-monitor bess-webhook'

# Test webhook
curl http://94.237.55.234:5001/health
```

---

## 📋 What Cells Are Monitored?

The auto-monitor watches these 4 cells:

| Cell | Purpose | Example Value |
|------|---------|---------------|
| **A6** | Postcode | `RH19 4LX` |
| **B6** | MPAN ID | `14` |
| **I6** | Additional field 1 | TBD |
| **J6** | Additional field 2 | TBD |

**When any cell changes** → Auto-triggers DNO lookup (30-second polling)

---

## 🧪 Quick Test After Deployment

### Test 1: Check Services
```bash
ssh root@94.237.55.234 'systemctl is-active bess-monitor && echo "✅ Monitor running"'
ssh root@94.237.55.234 'systemctl is-active bess-webhook && echo "✅ Webhook running"'
```

### Test 2: Check Logs
```bash
ssh root@94.237.55.234 'tail -20 /var/log/bess/monitor.log'
```

You should see:
```
🔋 BESS AUTO-MONITOR STARTING
==================================================
📍 Monitoring cells: A6, B6, I6, J6
⏰ Check interval: 30 seconds
💾 Cache TTL: 3600 seconds
==================================================
✅ Connected to BESS sheet
👀 Monitoring started.
```

### Test 3: Edit Sheet
1. Open BESS sheet
2. Edit cell A6 (postcode) or B6 (MPAN)
3. Wait 30 seconds
4. Check logs:
```bash
ssh root@94.237.55.234 'tail -30 /var/log/bess/monitor.log'
```

You should see:
```
🔔 CHANGE DETECTED at 17:45:30
   Previous: ('old_value', '14', '', '')
   Current:  ('new_value', '14', '', '')
🔄 Cache miss - triggering lookup
🔄 Triggering DNO lookup...
   A6 (Postcode): new_value
   B6 (MPAN): 14
✅ DNO lookup completed successfully
```

---

## 🔄 Apps Script Integration

Your custom menu now uses the UpCloud webhook:

```javascript
// In bess_custom_menu.gs
const webhookUrl = 'http://94.237.55.234:5001/trigger-dno-lookup';
```

**To install menu** (if not done yet):
1. Open BESS sheet → Extensions → Apps Script
2. Paste contents of `bess_custom_menu.gs`
3. Save and refresh sheet
4. See **🔋 BESS Tools** menu

**To trigger manually**:
1. Click **🔋 BESS Tools** → **🔄 Refresh DNO Data**
2. Menu calls webhook on UpCloud
3. DNO lookup runs
4. Results update in sheet

---

## 📊 Monitoring Commands

### View Live Logs
```bash
# Monitor auto-detection
ssh root@94.237.55.234 'tail -f /var/log/bess/monitor.log'

# Webhook requests
ssh root@94.237.55.234 'tail -f /var/log/bess/webhook.log'
```

### Check Status
```bash
# Service status
ssh root@94.237.55.234 'systemctl status bess-monitor bess-webhook'

# Webhook health
curl http://94.237.55.234:5001/health | python3 -m json.tool

# System status
curl http://94.237.55.234:5001/status | python3 -m json.tool
```

### Restart Services
```bash
# Restart monitor
ssh root@94.237.55.234 'systemctl restart bess-monitor'

# Restart webhook
ssh root@94.237.55.234 'systemctl restart bess-webhook'

# Restart both
ssh root@94.237.55.234 'systemctl restart bess-monitor bess-webhook'
```

---

## 🛠️ Troubleshooting

### Issue: Can't SSH to UpCloud
```bash
# Test connectivity
ping 94.237.55.234

# Check SSH key
ssh -v root@94.237.55.234
```

### Issue: Services Not Starting
```bash
# Check logs
ssh root@94.237.55.234 'journalctl -u bess-monitor -n 50'
ssh root@94.237.55.234 'tail -50 /var/log/bess/monitor-error.log'

# Re-deploy
./deploy_bess_to_upcloud.sh
```

### Issue: Webhook Not Responding
```bash
# Check if listening
ssh root@94.237.55.234 'netstat -tlnp | grep 5001'

# Test from server
ssh root@94.237.55.234 'curl http://localhost:5001/health'

# Open firewall
ssh root@94.237.55.234 'firewall-cmd --add-port=5001/tcp --permanent && firewall-cmd --reload'
```

---

## 🎉 Summary

**Files Created:**
- ✅ `bess_auto_monitor_upcloud.py` - Monitors A6, B6, I6, J6
- ✅ `dno_webhook_server_upcloud.py` - Webhook on port 5001
- ✅ `bess-monitor.service` - Systemd service for monitor
- ✅ `bess-webhook.service` - Systemd service for webhook
- ✅ `deploy_bess_to_upcloud.sh` - One-command deployment
- ✅ `bess_custom_menu.gs` - Updated with UpCloud webhook URL
- ✅ `BESS_UPCLOUD_DEPLOYMENT.md` - Full documentation

**What It Does:**
1. Monitors 4 cells (A6, B6, I6, J6) every 30 seconds
2. Auto-triggers DNO lookup when any cell changes
3. Caches results for 1 hour (reduces API calls)
4. Updates BESS sheet status bar in real-time
5. Provides webhook endpoint for Apps Script

**Deploy Command:**
```bash
./deploy_bess_to_upcloud.sh
```

**That's it!** 🚀

---

Last Updated: 2025-11-24 17:50:00
