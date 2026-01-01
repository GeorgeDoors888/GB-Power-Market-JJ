# 🌐 ngrok Setup Guide - Automatic Search Execution

This guide enables **automatic search execution** from Google Sheets by exposing your local API server via ngrok public tunnel.

## ✅ Prerequisites

- ✅ ngrok installed at `/usr/local/bin/ngrok`
- ✅ API server running on port 5002 (PIDs: 3172149, 3172151)
- ⏳ ngrok authtoken (get from https://dashboard.ngrok.com)

---

## 🔐 Step 1: Authenticate ngrok (One-Time Setup)

### A. Create Free ngrok Account

1. Visit: https://dashboard.ngrok.com/signup
2. Sign up with email (Google/GitHub login available)
3. Verify email

### B. Get Your Authtoken

1. Visit: https://dashboard.ngrok.com/get-started/your-authtoken
2. Copy the token (looks like: `2abc123def456ghi789jkl`)

### C. Configure ngrok

```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

**Example:**
```bash
ngrok config add-authtoken 2abc123def456ghi789jkl
```

**Verify:**
```bash
cat ~/.config/ngrok/ngrok.yml
# Should show your authtoken
```

---

## 🚀 Step 2: Start ngrok Tunnel

### Quick Start (Automated)

```bash
./start_ngrok_tunnel.sh
```

**Expected Output:**
```
🌐 Starting ngrok tunnel to port 5002...
✅ ngrok started (PID: 1234567)
⏳ Waiting 5 seconds for tunnel to establish...

✅ ngrok tunnel active!
🌐 Public URL: https://abc123def456.ngrok-free.app

📝 Next step: Update Apps Script API_ENDPOINT to:
   https://abc123def456.ngrok-free.app/search
```

### Manual Start (Alternative)

```bash
# Start ngrok in background
nohup ngrok http 5002 > logs/ngrok.log 2>&1 &

# Wait 5 seconds
sleep 5

# Get public URL
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['tunnels'][0]['public_url'])
"
```

---

## 📝 Step 3: Update Apps Script

### Option A: Automatic Update (Recommended)

```bash
# Replace YOUR_NGROK_URL with actual URL from Step 2
python3 update_apps_script_endpoint.py https://abc123def456.ngrok-free.app
```

**Output:**
```
✅ Updated API_ENDPOINT to: https://abc123def456.ngrok-free.app/search

📋 Next steps:
1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
2. Go to Extensions > Apps Script
3. Replace Code.gs with updated search_interface.gs
4. Save (Ctrl+S) and refresh spreadsheet
5. Click Search button → Should auto-execute! ✨
```

### Option B: Manual Update

1. Open `search_interface.gs` in editor
2. Find line 12:
   ```javascript
   var API_ENDPOINT = 'http://localhost:5002/search';
   ```
3. Replace with your ngrok URL:
   ```javascript
   var API_ENDPOINT = 'https://abc123def456.ngrok-free.app/search';
   ```
4. Save file

---

## 📊 Step 4: Install in Google Sheets

1. **Open spreadsheet**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

2. **Go to Apps Script**:
   - Extensions > Apps Script

3. **Replace code**:
   - Delete existing `Code.gs` content
   - Copy entire contents of `search_interface.gs`
   - Paste into editor

4. **Save**:
   - Ctrl+S or File > Save
   - Name project: "Search Interface"

5. **Refresh spreadsheet**:
   - Close Apps Script tab
   - Refresh Google Sheets tab
   - Verify "🔍 Search Tools" menu appears

---

## 🧪 Step 5: Test Automatic Execution

### Test Case 1: Simple Organization Search

1. In Google Sheets, go to "Search" tab
2. Fill in:
   - **Organization** (B10): `Flexitricity Limited`
   - **Record Type** (B6): `Supplier`
3. Click **Search** button (or menu: 🔍 Search Tools > 🔍 Run Search)

**Expected Result:**
- ✅ Brief "Executing search..." alert
- ✅ Results appear automatically in rows 25+
- ✅ Timestamp updates in E22
- ✅ Result count shows in J22

**If command dialog appears instead:**
- ❌ API not accessible (check ngrok tunnel)
- ❌ Apps Script has old endpoint (check line 12)
- ❌ API server not running (check PIDs)

### Test Case 2: Regional Filter

1. Fill in:
   - **GSP Region** (B15): `_A - Eastern (EPN)`
   - **DNO Operator** (B16): `EPN - UK Power Networks Eastern`
2. Click Search

**Expected:**
- ✅ Automatic execution
- ✅ Results filtered by region

---

## 🔧 Troubleshooting

### Issue: "Authentication failed" when starting ngrok

**Cause:** Authtoken not configured

**Fix:**
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### Issue: Command dialog still appearing

**Check 1:** ngrok tunnel running?
```bash
ps aux | grep ngrok
# Should show running process
```

**Check 2:** Get current public URL
```bash
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['tunnels'][0]['public_url'] if data.get('tunnels') else 'No tunnels')
"
```

**Check 3:** Verify Apps Script endpoint
```bash
grep "API_ENDPOINT" search_interface.gs
# Should show: var API_ENDPOINT = 'https://...ngrok...';
```

**Check 4:** Test API accessibility from browser
- Open: `https://YOUR_NGROK_URL.ngrok-free.app/health` (note: `/health` not `/search`)
- Should see: `{"status": "ok", "service": "Search API Server", ...}`

### Issue: ngrok tunnel disconnected

**Cause:** Free ngrok tunnels expire after 2 hours or on inactivity

**Fix:**
```bash
# Restart tunnel
./start_ngrok_tunnel.sh

# Get new URL and update Apps Script
python3 update_apps_script_endpoint.py https://NEW_URL.ngrok-free.app
```

### Issue: API server not responding

**Check status:**
```bash
curl -s http://localhost:5002/health
# Should return JSON with "status": "ok"
```

**Restart if needed:**
```bash
# Kill old processes
pkill -f search_api_server

# Start new
./start_search_api.sh
```

---

## 📊 Status Monitoring

### Check All Services

```bash
# API Server
ps aux | grep search_api_server | grep -v grep
curl -s http://localhost:5002/health

# ngrok Tunnel
ps aux | grep ngrok | grep -v grep
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Public URL:', data['tunnels'][0]['public_url'] if data.get('tunnels') else 'No tunnel')
print('Connections:', data['tunnels'][0]['connections'] if data.get('tunnels') else 0)
"

# View ngrok web interface
# Open in browser: http://localhost:4040
```

### Monitor Logs

```bash
# API server logs
tail -f logs/search_api.log

# ngrok logs
tail -f logs/ngrok.log

# Combined
tail -f logs/search_api.log logs/ngrok.log
```

---

## 🚀 Production Deployment

### Option 1: ngrok Paid Plan ($8-25/month)

**Benefits:**
- Static URLs (no need to update Apps Script)
- No 2-hour timeout
- Custom domain support
- Reserved domains

**Setup:**
```bash
# Reserve domain at: https://dashboard.ngrok.com/domains
# Update API_ENDPOINT once to static URL
var API_ENDPOINT = 'https://search-api.yourdomain.com/search';
```

### Option 2: Deploy to Cloud (Recommended for Production)

**Options:**
- AlmaLinux VPS (like IRIS pipeline server 94.237.55.234)
- Google Cloud Run
- Railway.app (free tier)
- Heroku

**Benefits:**
- No ngrok dependency
- Always online
- Better performance
- Static URLs

---

## 📋 Quick Reference

### Start Everything

```bash
# 1. Start API server (if not running)
./start_search_api.sh

# 2. Authenticate ngrok (one-time)
ngrok config add-authtoken YOUR_TOKEN

# 3. Start ngrok tunnel
./start_ngrok_tunnel.sh

# 4. Update Apps Script endpoint
python3 update_apps_script_endpoint.py $(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])")

# 5. Install Apps Script in Google Sheets (manual step)
```

### Stop Everything

```bash
# Stop ngrok
pkill ngrok

# Stop API server
pkill -f search_api_server
```

### Restart After Reboot

```bash
cd ~/GB-Power-Market-JJ
./start_search_api.sh
./start_ngrok_tunnel.sh
# Copy new URL from output
python3 update_apps_script_endpoint.py https://NEW_URL.ngrok-free.app
# Reinstall Apps Script in Google Sheets
```

---

## 🎯 Success Criteria

✅ **Setup Complete When:**
- ngrok authenticated (`ngrok config add-authtoken` successful)
- Tunnel running (public URL visible)
- Apps Script updated with ngrok URL
- Apps Script installed in Google Sheets
- Search button triggers automatic execution (no command dialog)
- Results populate automatically in rows 25+

---

## 📚 Related Documentation

- **Search Interface**: `SEARCH_SHEET_ENHANCEMENT_TODOS.md`
- **Integration Roadmap**: `SEARCH_ANALYSIS_INTEGRATION_TODOS.md`
- **API Server**: `search_api_server.py`
- **Apps Script**: `search_interface.gs`

---

**Last Updated:** December 31, 2025  
**Status:** ✅ Ready for authentication and deployment
