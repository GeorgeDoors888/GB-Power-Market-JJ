# 🚀 Start Codex Server with BigQuery in GitHub Codespaces

**Date: November 6, 2025**

## ✅ **What's Ready:**

1. ✅ `codex_server.py` updated with `/query_bigquery` endpoint
2. ✅ `requirements.txt` updated with `google-cloud-bigquery`
3. ✅ Service account JSON ready: `gridsmart_service_account.json`

---

## 📋 **Step-by-Step Setup (15 minutes)**

### Step 1: Open GitHub Codespaces (3 min)

**Option A: From GitHub Website**
1. Go to: https://github.com/GeorgeDoors888/overarch-jibber-jabber
2. Click the green **"Code"** button
3. Click **"Codespaces"** tab
4. Click **"Create codespace on main"** (or open existing one)
5. Wait for Codespace to load (~1-2 minutes)

**Option B: From VS Code (if you have GitHub extension)**
1. Press `Cmd+Shift+P`
2. Type: "Codespaces: Create New Codespace"
3. Select: `GeorgeDoors888/overarch-jibber-jabber`
4. Wait for Codespace to load

---

### Step 2: Upload Service Account to Codespace (2 min)

Once Codespace is open:

**Option A: Drag & Drop**
1. In Codespace file explorer, right-click root folder
2. Click **"Upload..."**
3. Select: `gridsmart_service_account.json` from your Mac
4. Upload to `/workspace/` directory

**Option B: Via Terminal**
In Codespace terminal:
```bash
# Create a secure upload (run this in Codespace terminal)
cat > /workspace/gridsmart_service_account.json << 'EOF'
# Then paste the contents of your service account JSON
# Press Ctrl+D when done
EOF
```

**Option C: Use GitHub CLI (from your Mac)**
```bash
# First, get your codespace name
gh codespace list

# Then copy the file
gh codespace cp gridsmart_service_account.json remote:/workspace/ -c YOUR_CODESPACE_NAME
```

✅ **Verify Upload:**
```bash
ls -la /workspace/gridsmart_service_account.json
```
You should see the file listed.

---

### Step 3: Install Dependencies (2 min)

In Codespace terminal:
```bash
cd /workspace/codex-server
pip install -r requirements.txt
```

Wait for packages to install (~1-2 minutes).

✅ **Expected output:**
```
Successfully installed fastapi-0.115.0 uvicorn-0.30.0 google-cloud-bigquery-3.11.0 ...
```

---

### Step 4: Start the Codex Server (1 min)

In Codespace terminal:
```bash
cd /workspace/codex-server
python codex_server.py
```

✅ **Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

🎉 **Server is now running!**

---

### Step 5: Make Port Public (3 min)

This is the **critical step** that lets ChatGPT access your server!

1. **In Codespace**, look for the **"PORTS"** tab (bottom panel)
   - If you don't see it, click **"View"** → **"Terminal"** → **"Ports"**

2. **You should see port 8000** listed

3. **Right-click on port 8000** → Select **"Port Visibility: Public"**

4. **Copy the URL** (looks like: `https://redesigned-space-gibbon-xxxxxxxx-8000.app.github.dev`)
   - Hover over port 8000
   - Click the 🌐 globe icon to copy URL
   - OR right-click → **"Copy Local Address"**

5. **Save this URL!** You'll give it to ChatGPT.

---

### Step 6: Test the Server (2 min)

**Test 1: Health Check**

In Codespace terminal (open a new terminal tab):
```bash
curl http://localhost:8000/health
```

✅ **Expected output:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "languages": ["python", "javascript"],
  "timestamp": "2025-11-06T..."
}
```

**Test 2: BigQuery Query**

```bash
curl -X POST http://localhost:8000/query_bigquery \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT fuelType, SUM(generation) as total FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` WHERE DATE(settlementDate) = CURRENT_DATE() GROUP BY fuelType ORDER BY total DESC LIMIT 5",
    "max_results": 5
  }'
```

✅ **Expected output:**
```json
{
  "success": true,
  "data": [
    {"fuelType": "gas", "total": 12450},
    {"fuelType": "wind", "total": 8200},
    ...
  ],
  "row_count": 5,
  "execution_time": 1.23,
  "timestamp": "2025-11-06T..."
}
```

---

### Step 7: Give ChatGPT the URL (2 min)

Copy your **public URL** from Step 5 (e.g., `https://redesigned-space-gibbon-xxxxxxxx-8000.app.github.dev`)

Then tell ChatGPT:

```
ChatGPT, I have a BigQuery API server running that you can use to query my UK energy data.

Server URL: https://redesigned-space-gibbon-xxxxxxxx-8000.app.github.dev

Available endpoints:
- GET  /health - Health check
- POST /query_bigquery - Execute BigQuery SQL queries

Project: inner-cinema-476211-u9
Dataset: uk_energy_prod

Available tables:
- bmrs_fuelinst_iris (fuel generation)
- bmrs_imbalprices_iris (imbalance prices)
- bmrs_detsysprices_iris (system prices)
- bmrs_freq_iris (frequency)
- bmrs_temp_iris (temperature)
- bmrs_indod_iris (demand)
- bmrs_melimbalngc_iris (MEL imbalance)
- bmrs_netbsad_iris (net BSAD)
- bmrs_rolsysdem_iris (rolling system demand)
- bmrs_syswarn_iris (system warnings)
- bmrs_sysfreq_iris (system frequency)

You can now query this data directly by making POST requests to /query_bigquery with SQL queries.

Example:
POST /query_bigquery
{
  "sql": "SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` WHERE DATE(settlementDate) = CURRENT_DATE() LIMIT 10"
}
```

---

## 🎉 **Done! ChatGPT Can Now Query BigQuery!**

### **What ChatGPT Can Do Now:**

✅ Run **ANY** SQL query against your BigQuery tables  
✅ Get real-time energy data  
✅ Analyze trends, calculate percentages, filter data  
✅ Return results in JSON format  

### **Example Conversation:**

**You:** "What's the current renewable percentage?"

**ChatGPT:** 
```
[Makes POST request to your server]
POST https://your-url/query_bigquery
{
  "sql": "SELECT SUM(CASE WHEN fuelType IN ('wind','solar','hydro','biomass') THEN generation ELSE 0 END) / SUM(generation) * 100 as renewable_pct FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` WHERE DATE(settlementDate) = CURRENT_DATE()"
}

Response: {"success": true, "data": [{"renewable_pct": 68.4}], ...}
```

**ChatGPT:** "The current renewable percentage is 68.4%"

---

## 🔧 **Troubleshooting**

### **Problem: Port 8000 not showing up**
**Solution:**
```bash
# Restart the server with explicit port
python codex_server.py
```
Wait 10 seconds and check PORTS tab again.

### **Problem: Service account not found**
**Solution:**
```bash
# Check if file exists
ls -la /workspace/gridsmart_service_account.json

# If not, re-upload it
```

### **Problem: "google.cloud.bigquery not found"**
**Solution:**
```bash
cd /workspace/codex-server
pip install --upgrade google-cloud-bigquery
```

### **Problem: BigQuery query returns "Access Denied"**
**Solution:**
- Verify service account JSON is correct
- Check that service account has BigQuery Data Viewer role in project `inner-cinema-476211-u9`

### **Problem: Codespace stops/sleeps**
**Solution:**
- Free Codespaces auto-stop after 30 min of inactivity
- Just restart the Codespace and re-run Step 4 (start server)
- Consider upgrading to paid Codespaces for always-on

---

## 📊 **API Reference**

### **POST /query_bigquery**

**Request Body:**
```json
{
  "sql": "SELECT * FROM `project.dataset.table` LIMIT 10",
  "timeout": 60,
  "max_results": 1000
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"column1": "value1", "column2": "value2"},
    ...
  ],
  "row_count": 10,
  "execution_time": 1.23,
  "timestamp": "2025-11-06T12:00:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message here",
  "execution_time": 0.1,
  "timestamp": "2025-11-06T12:00:00Z"
}
```

---

## 💰 **Cost Information**

### **GitHub Codespaces:**
- **Free tier**: 60 hours/month (2 core, 8 GB RAM)
- **After free tier**: ~$0.18/hour
- **Auto-stop**: After 30 minutes of inactivity

### **BigQuery Queries:**
- **First 1 TB/month**: FREE
- **After 1 TB**: $5 per TB
- **Your usage**: Very minimal (queries are small)

### **Cost Estimate:**
- Codespaces: **$0** (within free tier)
- BigQuery: **$0** (way under 1 TB)
- **Total: $0/month** 🎉

---

## 🎯 **Next Steps**

1. ✅ Start Codespace
2. ✅ Upload service account
3. ✅ Install dependencies
4. ✅ Start server
5. ✅ Make port public
6. ✅ Test endpoints
7. ✅ Give URL to ChatGPT

**Time to complete: ~15 minutes**

---

## 📚 **Related Docs**

- Full Codex Server code: `codex-server/codex_server.py`
- Original setup guide: `CODEX_SERVER_SETUP.md`
- ChatGPT integration: `codex-server/CHATGPT_INTEGRATION.md`
- Methods comparison: `METHODS_2_AND_3_EXPLAINED.md`

---

**Ready to start? Open GitHub Codespaces and let's go! 🚀**
