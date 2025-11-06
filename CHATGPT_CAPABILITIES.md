# 🤖 ChatGPT GB Power Market API - Full Capabilities

**GPT URL**: https://chatgpt.com/g/g-690c89d2e338819180a9ab96a71e082f-gb-power-market-api  
**Server**: https://94.237.55.15  
**Status**: ✅ **ALL SYSTEMS OPERATIONAL**

---

## ✅ What Your ChatGPT Can Do Now

### 📊 **1. BigQuery Data Access (Read-Only)**

**Available Endpoints:**
- `/bigquery/prices?days=N` - Get UK electricity prices
- `/bigquery/generation?days=N&fuel_type=TYPE` - Get generation mix data
- `/bigquery/execute?query=SQL&dry_run=true` - Execute custom SQL queries (dry-run mode safe)

**Example Prompts:**
```
"What were electricity prices in the UK last week?"
"Show me wind generation data for the past 3 days"
"What's the generation mix for solar vs gas?"
"Run a BigQuery query to show price averages by hour"
```

**What It Can Do:**
- ✅ Query historical electricity prices
- ✅ Analyze generation by fuel type (wind, solar, gas, nuclear, etc.)
- ✅ Run custom SQL queries against your uk_energy_prod dataset
- ✅ Filter by date ranges
- ✅ Aggregate and summarize data

**Security:**
- Read-only access to BigQuery
- All queries logged in audit log
- Rate limited (20/min, 200/hour)
- Requires authentication (handled automatically by GPT)

---

### 📑 **2. Google Sheets Integration**

**Available Endpoints:**
- `/sheets/read?tab=NAME&range=A1:Z100` - Read from any tab
- `/sheets/update?tab=NAME&range=A1:Z100` - Write to sheets (with logging)

**Default Sheet**: `Analysis BI Enhanced` tab

**Example Prompts:**
```
"Read row 10 from the Analysis BI Enhanced sheet"
"Show me the data in cells A1:C10"
"Update cell B5 with the value 42.5"
"Write this data to the Summary tab: [[1,2,3],[4,5,6]]"
```

**What It Can Do:**
- ✅ Read any range from any tab in your Google Sheet
- ✅ Write/update cells with new data
- ✅ Create summaries and reports
- ✅ Update analysis results automatically

**Security:**
- All write operations logged
- Can send Slack alerts (if configured)
- Full audit trail of changes

---

### 🖥️ **3. Server Management & Monitoring**

**Available Endpoints:**
- `/upcloud/status` - Check server health (CPU, memory, disk, uptime)
- `/upcloud/ssh?command=CMD` - Execute SSH commands (requires approval)
- `/upcloud/run-script?script_name=NAME` - Run pre-approved scripts

**Example Prompts:**
```
"What's the server status?"
"Check CPU and memory usage on UpCloud"
"Show me disk space available"
"Run system updates" (if script is whitelisted)
```

**What It Can Do:**
- ✅ Monitor server health (CPU, RAM, disk)
- ✅ Check service status (nginx, API gateway)
- ✅ View system logs
- ✅ Execute approved maintenance commands
- 🔒 Run dangerous commands (requires your approval first)

**Security:**
- SSH commands require approval by default
- Dangerous commands detected and flagged
- All commands logged
- Whitelisted scripts can run without approval

---

### 🔧 **4. Advanced Operations**

**High-Risk Endpoints** (Protected):
- `/bigquery/execute?query=SQL&dry_run=false&require_approval=true` - Write to BigQuery
- `/upcloud/ssh?command=CMD&require_approval=true` - Arbitrary SSH commands
- `/emergency/shutdown` - Emergency kill switch (requires special token)

**What It Can Do (With Your Approval):**
- 🔒 Modify BigQuery data (INSERT, UPDATE, DELETE)
- 🔒 Execute system administration commands
- 🔒 Deploy code changes
- 🔒 Restart services
- 🔒 Emergency shutdown

**Security:**
- All dangerous operations require explicit approval
- Dry-run mode available for testing
- Approval prompts show exactly what will happen
- Emergency token prevents accidental shutdowns

---

## 🔐 Authentication & Security

### **How API Key Works:**

**Storage**: 
- API key is stored in your GPT's configuration
- Sent automatically with every request as `Authorization: Bearer TOKEN`

**Token Refresh**:
- ❌ **Token does NOT auto-update**
- The API key is fixed: `33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af`
- If you change it on the server, you must manually update the GPT configuration

**To Update API Key:**
1. Go to GPT settings: https://chatgpt.com/gpts/editor/g-690c89d2e338819180a9ab96a71e082f
2. Configure → Authentication
3. Update the API Key field
4. Save

### **Rate Limits:**
- **20 requests per minute**
- **200 requests per hour**
- Exceeding limits returns HTTP 429 error
- Resets automatically

### **Audit Logging:**
Every API call is logged with:
- Timestamp
- Action type (READ/WRITE/DANGEROUS)
- Client IP
- Endpoint called
- Parameters
- Success/failure
- Duration

**Log Location**: `/tmp/ai-gateway-audit.log` on server

---

## 🚀 Example Use Cases

### **1. Daily Price Report**
**Prompt**: *"Create a summary of UK electricity prices for the last 7 days, including min, max, and average prices per day"*

ChatGPT will:
1. Call `/bigquery/prices?days=7`
2. Process the data
3. Calculate statistics
4. Format a nice summary

---

### **2. Generation Analysis**
**Prompt**: *"Compare wind vs solar generation over the last month. Show me which days had the highest renewable generation."*

ChatGPT will:
1. Query generation data for wind and solar
2. Analyze daily totals
3. Identify peak days
4. Create a comparison report

---

### **3. Sheet Update Automation**
**Prompt**: *"Get the latest electricity prices and update the 'Summary' tab in cells B2:B8"*

ChatGPT will:
1. Query BigQuery for latest prices
2. Format the data
3. Call `/sheets/update` to write to the sheet
4. Confirm the update

---

### **4. Server Health Monitoring**
**Prompt**: *"Check if the server is healthy and tell me if anything needs attention"*

ChatGPT will:
1. Call `/health` endpoint
2. Check BigQuery, Sheets, SSH status
3. Report any issues
4. Suggest fixes if needed

---

### **5. Custom Analysis with Code**
**Prompt**: *"Analyze electricity price trends and create a forecast for next week using Python"*

ChatGPT can:
1. Fetch historical data from BigQuery
2. **Write Python code** in its environment to analyze trends
3. Use libraries like pandas, numpy, scikit-learn
4. Generate forecasts
5. Format results

**Note**: ChatGPT has its own Python environment for analysis. The API provides data; ChatGPT processes it with code.

---

## 💻 Can ChatGPT Create & Run Code?

### **YES! Here's How:**

**ChatGPT's Code Execution:**
- ✅ ChatGPT has a **built-in Python environment**
- ✅ Can run code **internally** without touching your server
- ✅ Has access to: pandas, numpy, matplotlib, scikit-learn, etc.
- ✅ Can create visualizations, perform analysis, build models

**Workflow:**
```
1. ChatGPT calls your API to get data
   └─> /bigquery/prices returns JSON data
   
2. ChatGPT writes Python code internally
   └─> import pandas as pd
   └─> df = pd.DataFrame(data)
   └─> df.plot()
   
3. ChatGPT runs the code in its sandbox
   └─> Generates charts, analysis, predictions
   
4. ChatGPT shows you the results
   └─> Images, tables, insights
```

**Example Flow:**
```
User: "Analyze price volatility and create a chart"

ChatGPT:
1. Calls /bigquery/prices?days=30
2. Receives data: [{date: "2025-11-01", price: 42.5}, ...]
3. Creates Python code:
   ```python
   import pandas as pd
   import matplotlib.pyplot as plt
   
   df = pd.DataFrame(api_data)
   df['date'] = pd.to_datetime(df['date'])
   df['rolling_std'] = df['price'].rolling(7).std()
   
   plt.figure(figsize=(12,6))
   plt.plot(df['date'], df['price'], label='Price')
   plt.plot(df['date'], df['rolling_std'], label='7-day volatility')
   plt.show()
   ```
4. Runs the code internally
5. Shows you the chart and analysis
```

**What Code Can It Run:**
- ✅ Data analysis (pandas, numpy)
- ✅ Statistical analysis (scipy, statsmodels)
- ✅ Machine learning (scikit-learn)
- ✅ Visualization (matplotlib, seaborn)
- ✅ Time series forecasting
- ✅ Custom calculations and transformations

**What It CANNOT Do:**
- ❌ Install new Python packages on YOUR server
- ❌ Modify files on your server (without /upcloud/ssh endpoint)
- ❌ Access your local filesystem directly
- ❌ Run code persistently (each session is isolated)

---

## 🔄 Token/API Key Management

### **Current API Key:**
```
33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af
```

### **Does It Auto-Update?**
**NO** - You must manually update in two places if you change it:

**If you change the API key:**

1. **Update on Server:**
   ```bash
   ssh root@94.237.55.15
   nano /etc/systemd/system/ai-gateway.service
   # Change Environment="AI_GATEWAY_API_KEY=NEW_KEY"
   systemctl daemon-reload
   systemctl restart ai-gateway.service
   ```

2. **Update in GPT:**
   - Go to https://chatgpt.com/gpts/editor/g-690c89d2e338819180a9ab96a71e082f
   - Configure → Authentication
   - Update API Key field
   - Save

**Best Practice:**
- Don't change the key unless compromised
- If you must change it, update both locations simultaneously
- Test with a simple query after updating

---

## 📊 Current System Status

```
✅ BigQuery:      HEALTHY - Connected to inner-cinema-476211-u9
✅ Google Sheets: HEALTHY - Connected to Analysis BI Enhanced
✅ UpCloud SSH:   HEALTHY - Connected to 94.237.55.15
⚠️  Slack:        NOT CONFIGURED (optional)

📡 Server:        https://94.237.55.15
🔒 Security:      Level 3 - Full Automation
⏱️  Rate Limits:   20/min, 200/hour
📝 Audit Log:     /tmp/ai-gateway-audit.log
```

---

## 🧪 Test Your GPT Now!

### **Try These Prompts:**

1. **"What's your status?"** → Should show healthy components
2. **"Get electricity prices for yesterday"** → Should query BigQuery
3. **"Read cell A1 from Analysis BI Enhanced"** → Should read from Sheets
4. **"Analyze price trends and create a chart"** → Should fetch data + run Python code
5. **"Check server health"** → Should show CPU/memory/disk

---

## 🚨 Emergency Procedures

### **If Something Goes Wrong:**

**Stop the API:**
```bash
ssh root@94.237.55.15
systemctl stop ai-gateway.service
```

**Emergency Shutdown (from GPT):**
```
Use /emergency/shutdown endpoint with emergency token
(You set this token separately from the API key)
```

**View Logs:**
```bash
ssh root@94.237.55.15
tail -f /var/log/ai-gateway-error.log
tail -f /tmp/ai-gateway-audit.log
```

**Restart Everything:**
```bash
ssh root@94.237.55.15
systemctl restart nginx.service
systemctl restart ai-gateway.service
```

---

## 📚 Additional Documentation

- `DEPLOYMENT_SUCCESS_CHATGPT_SETUP.md` - Initial setup guide
- `HTTPS_SETUP_COMPLETE.md` - SSL/TLS configuration
- `CHATGPT_QUICK_CONFIG.md` - Quick reference card
- `api_gateway.py` - Full API source code (850 lines)

---

## 🎯 Summary

**Your ChatGPT can now:**
- ✅ Query BigQuery for UK electricity data
- ✅ Read & write Google Sheets
- ✅ Monitor server health
- ✅ Execute approved server commands
- ✅ **Write and run Python code** for analysis
- ✅ Create charts and visualizations
- ✅ Perform statistical analysis
- ✅ Build forecasting models
- 🔒 All with authentication, rate limiting, and audit logging

**API Key Management:**
- ❌ Does NOT auto-update
- ✅ Stored securely in GPT configuration
- ✅ Sent automatically with each request
- ⚠️  Must manually update in both GPT and server if changed

**Next Steps:**
1. Test with the example prompts above
2. Monitor logs: `ssh root@94.237.55.15 tail -f /tmp/ai-gateway-audit.log`
3. Ask ChatGPT to analyze your data!

---

**🎉 Deployment Complete - Total Time: ~60 minutes**
