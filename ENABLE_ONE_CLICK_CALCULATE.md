# 🚀 ONE-CLICK CALCULATE BUTTON SETUP

**Status**: ✅ Ready to deploy
**What it does**: Click button → Report automatically generates → Results appear in sheet

---

## 📋 Quick Setup (5 minutes)

### Step 1: Start Webhook Server

Open a terminal and run:
```bash
cd /home/george/GB-Power-Market-JJ
python3 report_webhook_server.py
```

**Expected output:**
```
🚀 Starting Analysis Report Webhook Server...
📁 Script directory: /home/george/GB-Power-Market-JJ
🌐 Endpoint: http://localhost:5000/generate-report
💡 Trigger from Google Sheets CALCULATE button

⏸️  Press Ctrl+C to stop

 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

**Keep this terminal open!** The server must run for the button to work.

---

### Step 2: Update Apps Script

1. **Open Apps Script:**
   - Google Sheets → Extensions → Apps Script

2. **Update webhook URL in ANALYSIS_DROPDOWNS.gs:**

   Find line ~136:
   ```javascript
   var webhookUrl = 'http://localhost:5000/generate-report';
   ```

   **If accessing from another computer**, change to:
   ```javascript
   var webhookUrl = 'http://YOUR_SERVER_IP:5000/generate-report';
   ```

3. **Save** (Ctrl+S) and close Apps Script

---

### Step 3: Test the Button

1. Go to Analysis sheet
2. Set your selections (dates, category, type, graph)
3. Click **CALCULATE** button
4. ✅ Should see: "✅ Report Generated! Check row 18+ for results"
5. ✅ Data appears automatically in row 18+

---

## 🔧 Troubleshooting

### Button shows "Automatic execution unavailable"

**Problem**: Webhook server not running or wrong URL

**Fix**:
1. Check webhook server is running: `curl http://localhost:5000/health`
2. Should return: `{"status":"healthy"...}`
3. If not, restart: `python3 report_webhook_server.py`

### "Failed to fetch" error

**Problem**: Google Sheets can't reach localhost

**Solutions**:

**Option A: Use ngrok tunnel (Recommended for local dev)**
```bash
# Terminal 1: Start webhook
python3 report_webhook_server.py

# Terminal 2: Start ngrok
ngrok http 5000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok.io`) and update Apps Script:
```javascript
var webhookUrl = 'https://abc123.ngrok.io/generate-report';
```

**Option B: Deploy to cloud server**
- Use a VPS, Google Cloud Run, or Railway
- Update webhookUrl to public endpoint

---

## 🎯 How It Works

```
┌─────────────────┐
│  Google Sheets  │
│  CALCULATE btn  │ ──── 1. Click button
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Apps Script    │ ──── 2. POST to webhook
│  CALCULATE()    │      (selections as JSON)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Webhook Server  │ ──── 3. Receive request
│ Flask (port 5000)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Python Script   │ ──── 4. Query BigQuery
│ generate_...py  │      Write to Sheets
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Google Sheets  │ ──── 5. Results appear!
│  Row 18+        │
└─────────────────┘
```

---

## 🔄 Background Service (Optional)

To keep webhook running permanently:

### Option 1: systemd service
```bash
# Create service file
sudo nano /etc/systemd/system/analysis-webhook.service
```

```ini
[Unit]
Description=Analysis Report Webhook Server
After=network.target

[Service]
Type=simple
User=george
WorkingDirectory=/home/george/GB-Power-Market-JJ
ExecStart=/usr/bin/python3 /home/george/GB-Power-Market-JJ/report_webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable analysis-webhook
sudo systemctl start analysis-webhook

# Check status
sudo systemctl status analysis-webhook
```

### Option 2: screen/tmux session
```bash
# Start in background
screen -dmS webhook python3 report_webhook_server.py

# Attach to view
screen -r webhook

# Detach: Ctrl+A, D
```

### Option 3: nohup
```bash
nohup python3 report_webhook_server.py > webhook.log 2>&1 &
```

---

## 📊 Test Commands

### Test webhook server
```bash
curl http://localhost:5000/health
# Should return: {"status":"healthy"...}
```

### Test report generation
```bash
curl -X POST http://localhost:5000/generate-report \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
    "from_date": "2025-12-15",
    "to_date": "2025-12-22",
    "report_category": "⚡ Generation & Fuel Mix",
    "report_type": "Time Series Chart",
    "graph_type": "Line Chart"
  }'
```

---

## 📝 Current Status

✅ **Files Created:**
- `report_webhook_server.py` - Flask webhook server
- `ANALYSIS_DROPDOWNS.gs` - Updated with webhook call
- `ENABLE_ONE_CLICK_CALCULATE.md` - This guide

✅ **Dependencies Installed:**
- Flask 3.1.2
- Flask-CORS 6.0.2

⏳ **Next Steps:**
1. Start webhook server: `python3 report_webhook_server.py`
2. Update Apps Script with this file
3. Click CALCULATE button
4. ✅ Automatic report generation!

---

## 🎉 Success Indicators

**When it's working:**
- ✅ Webhook server shows: "🔔 Webhook triggered!"
- ✅ Button shows: "✅ Report Generated!"
- ✅ Data appears in row 18+ within 10 seconds
- ✅ No manual terminal commands needed

**When it's NOT working:**
- ❌ Button shows: "⚠️ Automatic execution unavailable"
- ❌ Webhook server shows no activity
- ❌ Manual command still required

---

*Last Updated: December 22, 2025*
*Version: 1.0 - One-Click Automation*
