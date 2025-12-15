# Dashboard V2 - Quick Reference

## 🚀 Current Status

✅ **Webhook Server**: Running on http://localhost:5001  
✅ **ngrok Tunnel**: https://5893b8404ab5.ngrok-free.app  
✅ **Apps Script**: Deployed (3 files)  
✅ **Google Sheets**: Created  

⚠️ **PENDING**: Share spreadsheet with service account

---

## 📋 URLs

| Resource | URL |
|----------|-----|
| **New Dashboard** | https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc |
| **Apps Script Editor** | https://script.google.com/d/1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz/edit |
| **Old Dashboard** | https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA |
| **Webhook (public)** | https://5893b8404ab5.ngrok-free.app |
| **Webhook (local)** | http://localhost:5001 |

---

## 🔧 Commands

### Start Services
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ/new-dashboard

# Start webhook server
nohup python3 webhook_server.py > webhook.log 2>&1 & echo $! > webhook.pid

# Start ngrok tunnel
nohup ngrok http 5001 > ngrok.log 2>&1 & echo $! > ngrok.pid

# Check status
./check_status.sh
```

### Update & Deploy
```bash
# Edit Code.gs, then push to Apps Script
clasp push

# Update webhook URL after ngrok restart
# 1. Get new URL: curl -s http://localhost:4040/api/tunnels
# 2. Edit Code.gs CONFIG.WEBHOOK_URL
# 3. clasp push
```

### Monitor
```bash
# Webhook logs
tail -f webhook.log

# ngrok dashboard
open http://localhost:4040

# Check health
curl -s http://localhost:5001/health | python3 -m json.tool
```

### Stop Services
```bash
pkill -f webhook_server
pkill -f ngrok
```

---

## 🎯 Next Action Required

**Share spreadsheet with service account:**

1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
2. Click **Share** button (top right)
3. Add email: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`
4. Set role: **Editor**
5. Uncheck "Notify people"
6. Click **Share**

---

## ✅ Testing Flow

After sharing spreadsheet:

1. **Refresh Google Sheets** (F5 or reload)
2. **Test Menu**: Data → Copy from Old Dashboard
   - Should copy KPIs (rows 1-10) and constraints (rows 116-126)
3. **Test Map**: Maps → Constraint Map
   - Should show sidebar with 10 markers
4. **Check Logs**: `tail -f webhook.log`
   - Should see POST /copy-dashboard-data requests

---

## 📊 Webhook Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (returns `{"status": "ok"}`) |
| POST | `/copy-dashboard-data` | Copy KPIs & constraints from old sheet |
| POST | `/copy-bess-data` | Copy BESS sheet structure |
| GET | `/get-constraints` | Get current constraint data for map |
| POST | `/refresh-dashboard` | Query BigQuery, update sheet |

---

## 🔑 Service Account

**Email**: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`

**Required Access**:
- ✅ Old Dashboard (already has)
- ⚠️ **New Dashboard V2** (MUST ADD)
- ✅ BESS Sheet (already has)

---

## 🐛 Troubleshooting

**Webhook not responding:**
```bash
ps aux | grep webhook_server  # Check if running
curl http://localhost:5001/health  # Test locally
```

**ngrok URL changed:**
- Get new URL: `curl -s http://localhost:4040/api/tunnels`
- Update `Code.gs` CONFIG.WEBHOOK_URL
- Run `clasp push`

**Permission errors:**
- Verify service account has Editor access
- Check webhook.log for error details
- Manually share spreadsheet if needed

**Apps Script not seeing menu:**
- Refresh spreadsheet (F5)
- Check: Extensions → Apps Script → Executions
- Verify `clasp push` succeeded

---

## 📁 Files

```
new-dashboard/
├── Code.gs                    # Main Apps Script (menus, maps)
├── CopyData.gs                # Legacy copy functions (unused)
├── webhook_server.py          # Flask webhook server
├── check_status.sh            # Status checker script
├── share_with_service_account.py  # Helper to share spreadsheet
├── .clasp.json                # clasp configuration
├── appsscript.json            # Apps Script manifest
├── config.env                 # Environment variables
├── webhook.log                # Server logs
├── ngrok.log                  # Tunnel logs
├── webhook.pid                # Process ID
└── ngrok.pid                  # Process ID
```

---

**Created**: 2025-11-25  
**Status**: ✅ Ready for testing (after sharing spreadsheet)
