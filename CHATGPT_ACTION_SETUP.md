# 🤖 ChatGPT Action Setup Guide

**Time Required**: 15-30 minutes  
**Difficulty**: Easy  

---

## What You'll Enable

After setup, you'll be able to ask ChatGPT:

- 💰 **"What were UK electricity prices yesterday?"**
- ⚡ **"Show me generation mix for the past week"**
- 📊 **"Update my Google Sheet with today's summary"**
- 🖥️ **"Check the status of my UpCloud server"**
- 🔄 **"Run the daily arbitrage script"**

And ChatGPT will execute these commands **directly** using your API Gateway!

---

## Prerequisites

✅ API Gateway running (local: `localhost:8000` OR remote: `94.237.55.15:8000`)  
✅ API Key ready: `33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af`  
✅ ChatGPT Plus or Enterprise subscription  

---

## Step 1: Export OpenAPI Schema

### **Option A: From Running Server (Recommended)**

```bash
# If running locally
curl http://localhost:8000/openapi.json > chatgpt-action-schema.json

# If deployed to UpCloud
curl http://94.237.55.15:8000/openapi.json > chatgpt-action-schema.json

# View the schema
cat chatgpt-action-schema.json | python3 -m json.tool | head -50
```

### **Option B: Manual Schema File (If Server Not Running)**

I can create the schema file for you - see `chatgpt-action-schema.json` created below.

---

## Step 2: Configure ChatGPT Action

### **Navigate to Actions**:

1. Go to: https://chatgpt.com/
2. Click your profile (bottom left)
3. Click **"Customize ChatGPT"**
4. Click **"Actions"** tab
5. Click **"Create new action"**

### **Configure Action Details**:

**Name**: `GB Power Market API`

**Description**:
```
Access UK electricity market data, prices, generation mix, Google Sheets dashboard, and UpCloud server management for the GB Power Market analysis project.
```

**Schema**: Copy and paste contents of `chatgpt-action-schema.json`

**Authentication**: Select **"API Key"**

---

## Step 3: Set Up Authentication

### **In the Authentication section**:

**Auth Type**: `API Key`

**API Key**: `33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af`

**Custom Header Name**: `Authorization`

**Custom Header Format**: `Bearer {api_key}`

---

## Step 4: Configure Server URL

### **Base URL**:

**For Local Testing**:
```
http://localhost:8000
```

**For Production (UpCloud)**:
```
http://94.237.55.15:8000
```

⚠️ **Note**: If using localhost, ChatGPT won't be able to reach it. You'll need to either:
- Deploy to UpCloud first (see `UPCLOUD_API_GATEWAY_DEPLOY.md`)
- Use a tunnel service like ngrok (see below)

---

## Step 5: Test the Action

### **Click "Test" in the Action editor**:

**Test Query 1: Health Check**
```
GET /health
```
Expected: Returns status of all components (BigQuery, Sheets, SSH)

**Test Query 2: Recent Prices**
```
GET /bigquery/prices?days=7
```
Expected: Returns price data for last 7 days

**Test Query 3: Generation Mix**
```
GET /bigquery/generation?days=7&fuel_type=WIND
```
Expected: Returns wind generation data

---

## Step 6: Save and Enable

1. Click **"Save"** (top right)
2. Toggle the action **ON**
3. Close the Actions panel

---

## Step 7: Test in ChatGPT Conversation

Start a new chat and try these prompts:

### **Test 1: Simple Data Query**
```
What were UK electricity prices over the past 7 days?
```

ChatGPT should:
1. Call `/bigquery/prices?days=7`
2. Parse the results
3. Present formatted summary with insights

### **Test 2: Generation Analysis**
```
Show me wind generation patterns for the last week
```

ChatGPT should:
1. Call `/bigquery/generation?days=7&fuel_type=WIND`
2. Analyze the data
3. Provide insights about wind generation

### **Test 3: Server Status**
```
Check the status of my UpCloud server
```

ChatGPT should:
1. Call `/upcloud/status`
2. Report server health, disk usage, memory, service status

---

## Alternative: Use ngrok for Local Testing

If you want to test with localhost before deploying:

### **Install ngrok**:
```bash
brew install ngrok
```

### **Start ngrok tunnel**:
```bash
# Start your local server first
./start_gateway.sh

# In another terminal, create tunnel
ngrok http 8000
```

### **Use ngrok URL in ChatGPT**:

ngrok will show:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

Use `https://abc123.ngrok.io` as your Base URL in ChatGPT Action.

⚠️ **Note**: Free ngrok URLs change each restart. Paid plans get persistent URLs.

---

## Advanced: Multiple Actions

You can create separate actions for different security levels:

### **Action 1: "Read-Only Power Data"**
- Only exposes: `/bigquery/prices`, `/bigquery/generation`, `/sheets/read`
- No authentication required (if you make a read-only key)
- Safe for experimenting

### **Action 2: "Full Power Market Control"**
- Exposes all endpoints
- Requires full API key
- Can write to Sheets, run SSH commands, execute BigQuery writes

### **Action 3: "Server Management"**
- Only exposes: `/upcloud/status`, `/upcloud/ssh`, `/upcloud/run-script`
- Separate API key for infrastructure control
- Isolated from data operations

---

## Troubleshooting

### **"Action failed to call endpoint"**

1. **Check server is running**:
   ```bash
   curl http://localhost:8000/health
   # OR
   curl http://94.237.55.15:8000/health
   ```

2. **Verify API key**:
   ```bash
   curl -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
     http://localhost:8000/health
   ```

3. **Check ChatGPT can reach server**:
   - localhost won't work unless using ngrok
   - UpCloud IP must be accessible from internet
   - Firewall must allow port 8000

### **"Authentication failed"**

- Verify API key in Action settings matches `.env.ai-gateway`
- Check header format is exactly: `Bearer {api_key}` (with space)
- Ensure Custom Header Name is `Authorization`

### **"Rate limit exceeded"**

- Default limit: 20 requests/minute, 200/hour
- Wait a bit and try again
- Or increase limits in `.env.ai-gateway`:
  ```bash
  RATE_LIMIT_PER_MINUTE=100
  RATE_LIMIT_PER_HOUR=1000
  ```

### **Schema validation errors**

- Re-export schema: `curl http://localhost:8000/openapi.json > chatgpt-action-schema.json`
- Ensure JSON is valid: `python3 -m json.tool chatgpt-action-schema.json`
- Check for any custom modifications that broke the schema

---

## Example Conversations

### **Price Analysis**:

**You**: "What were the cheapest electricity hours yesterday?"

**ChatGPT**: 
```
Let me check the prices for you...

Yesterday (November 5, 2025), the UK electricity market had:
- Lowest price: -£15.55/MWh at 3:00 AM
- 12 periods with negative prices (great for arbitrage!)
- Average price: £27.63/MWh
- Peak price: £111.96/MWh at 6:00 PM

The negative prices indicate excess renewable generation, 
particularly during the early morning hours when wind was high.
```

### **Generation Monitoring**:

**You**: "How much solar generation was there last week?"

**ChatGPT**:
```
Analyzing solar generation data...

Last week's solar generation summary:
- Total: 847 GWh
- Peak: 8.2 GW (Nov 1, 1:00 PM)
- Average: 5.1 GW during daylight hours
- Trend: 15% higher than previous week

Best days: Tuesday and Wednesday with clear skies.
Generation dropped 40% on Thursday due to cloud cover.
```

### **Server Management**:

**You**: "Is my arbitrage script running on the UpCloud server?"

**ChatGPT**:
```
Checking server status...

Server: 94.237.55.15
Status: ✅ Online
Service: arbitrage.service
State: Active (running)
Uptime: 2 days 4 hours
Last run: Today at 02:00 UTC
Memory: 234 MB / 1 GB (23%)
Disk: 4.2 GB / 25 GB (17%)

Everything looks healthy! The daily arbitrage analysis 
is running as scheduled.
```

---

## Security Best Practices

### **1. Use Environment-Specific Keys**

```bash
# Development key (localhost)
DEV_API_KEY=abc123...

# Production key (UpCloud)
PROD_API_KEY=xyz789...
```

### **2. Monitor Action Usage**

Check audit logs regularly:
```bash
tail -100 /tmp/ai-gateway-audit.log | grep "action.*API_REQUEST"
```

### **3. Rotate Keys After Sharing**

If you share your ChatGPT conversation:
```bash
# Generate new key
openssl rand -hex 32

# Update .env.ai-gateway
# Update ChatGPT Action
# Restart server
```

### **4. Set Up Approval for Dangerous Operations**

In your conversations, use phrases like:
- "Check with me before writing to BigQuery"
- "Show me the command before running it"
- "Dry-run first, then ask for approval"

---

## Next Steps

After setup:

1. ✅ Test all read operations (prices, generation, health)
2. ✅ Try a monitored write (update Google Sheets)
3. ✅ Review audit logs: `tail -f /tmp/ai-gateway-audit.log`
4. ✅ Share with team (optional)
5. ✅ Set up Slack alerts (see `SLACK_SETUP.md`)

---

## Quick Reference

**Action Name**: `GB Power Market API`  
**Base URL (local)**: `http://localhost:8000`  
**Base URL (production)**: `http://94.237.55.15:8000`  
**API Key**: `33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af`  
**Schema**: `chatgpt-action-schema.json`  
**Docs**: http://localhost:8000/docs (interactive API docs)

---

**Status**: Ready to configure!  
**Next**: Follow Step 1 to export OpenAPI schema, then Step 2 to create the Action.
