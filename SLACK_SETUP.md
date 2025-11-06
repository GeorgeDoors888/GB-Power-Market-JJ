# 📱 Slack Notifications Setup Guide

**Time Required**: 10 minutes  
**Difficulty**: Easy  

---

## Step 1: Create Slack Webhook

### **Option A: Use Existing Workspace**

1. Go to: https://api.slack.com/messaging/webhooks
2. Click **"Create your Slack app"**
3. Choose **"From scratch"**
4. App Name: `AI Gateway Alerts`
5. Select your workspace
6. Click **"Create App"**

### **Option B: If You Already Have an App**

1. Go to: https://api.slack.com/apps
2. Select your app
3. Click **"Incoming Webhooks"** in sidebar
4. Toggle **"Activate Incoming Webhooks"** to ON

---

## Step 2: Generate Webhook URL

1. Scroll down to **"Webhook URLs for Your Workspace"**
2. Click **"Add New Webhook to Workspace"**
3. Select channel (e.g., `#power-market-alerts` or `#general`)
4. Click **"Allow"**
5. **Copy the Webhook URL** - looks like:
   ```
   https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
   ```

---

## Step 3: Update Configuration

Edit your `.env.ai-gateway` file:

```bash
# Replace this line:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# With your actual webhook:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

---

## Step 4: Restart Server

```bash
cd "/Users/georgemajor/GB Power Market JJ"

# Stop existing server
pkill -f 'python.*api_gateway.py'

# Start with new config
./start_gateway.sh
```

---

## Step 5: Test Slack Notifications

### **Test 1: Trigger a Write Operation**

```bash
curl -X POST \
  -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  -H "Content-Type: application/json" \
  -d '{"tab": "Raw Data", "range": "Z1", "values": [["Test from API"]]}' \
  "http://localhost:8000/sheets/update"
```

**Expected**: Slack message appears: ⚠️ Google Sheet Update: Raw Data range Z1

### **Test 2: Trigger Dangerous Command Block**

```bash
curl -X POST \
  -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  "http://localhost:8000/upcloud/ssh?command=rm%20-rf%20/tmp/test&require_approval=false"
```

**Expected**: Slack message appears: 🚨 BLOCKED DANGEROUS COMMAND!

### **Test 3: Server Startup**

Restart server - you should see:
✅ AI Gateway Server Started

---

## What You'll Get Alerted On

### **🚨 Critical Alerts**:
- SSH command execution
- BigQuery write operations
- Dangerous commands blocked
- Server startup/shutdown
- Script execution failures

### **⚠️ Warning Alerts**:
- Google Sheets updates
- Approved script runs
- Write operation approvals

### **✅ Success Alerts**:
- Script completions
- Successful deployments

---

## Customize Alert Channel

Want different channels for different alert types? Edit `api_gateway.py`:

```python
# Around line 90-110
def send_slack_alert(message: str, level: str = "info", details: Dict = None):
    """Send alert to Slack with optional details"""
    
    # Add channel routing
    if level == "critical":
        webhook_url = os.environ.get("SLACK_CRITICAL_WEBHOOK")
    elif level == "warning":
        webhook_url = os.environ.get("SLACK_WARNING_WEBHOOK")
    else:
        webhook_url = SLACK_WEBHOOK
    
    # ... rest of function
```

Then add to `.env.ai-gateway`:
```bash
SLACK_CRITICAL_WEBHOOK=https://hooks.slack.com/services/.../critical-channel
SLACK_WARNING_WEBHOOK=https://hooks.slack.com/services/.../warnings-channel
```

---

## Troubleshooting

### **"No alerts appearing"**

1. Check webhook URL is correct:
   ```bash
   grep SLACK_WEBHOOK_URL .env.ai-gateway
   ```

2. Test webhook manually:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test from terminal"}' \
     YOUR_WEBHOOK_URL
   ```

3. Check server logs:
   ```bash
   tail -20 /tmp/ai-gateway.log | grep -i slack
   ```

### **"Failed to send Slack alert"**

- Check internet connectivity
- Verify webhook hasn't been revoked
- Check Slack API status: https://status.slack.com/

---

## Example Slack Messages

### **Write Operation Alert**:
```
⚠️ Action: Google Sheet Update

• rows: 1
• timestamp: 2025-11-06T11:30:45
```

### **Critical Alert**:
```
🚨 EXECUTING SSH COMMAND on 94.237.55.15

• command: systemctl restart arbitrage.service
```

### **Server Startup**:
```
✅ AI Gateway Server Started

• version: 3.0.0
• security: Level 3
```

---

**Status**: Ready to configure!  
**Next**: Update `.env.ai-gateway` with your webhook URL and restart server.
