# 🚀 Quick Start: AI Direct Access

## TL;DR - 3 Ways to Give ChatGPT Access

### **Option 1: Read-Only (Recommended First)** ⭐ SAFE
**Time**: 30 minutes  
**Risk**: Low  
**What it does**: ChatGPT can query your data but not modify anything

```bash
# 1. Install dependencies
pip install fastapi uvicorn google-cloud-bigquery paramiko

# 2. Download the API gateway
# (Use AI_DIRECT_ACCESS_SETUP.md file)

# 3. Set API key
export AI_GATEWAY_API_KEY=$(openssl rand -hex 32)
echo "Your API key: $AI_GATEWAY_API_KEY"

# 4. Run server
python api_gateway.py

# 5. Test it
curl -H "Authorization: Bearer $AI_GATEWAY_API_KEY" \
  "http://localhost:8000/bigquery/prices?days=7"
```

**What ChatGPT can do**:
- ✅ Query BigQuery (electricity prices, generation data)
- ✅ Read Google Sheets
- ✅ Check UpCloud server status
- ❌ Cannot modify anything

---

### **Option 2: Monitored Write Access** ⚠️ MODERATE RISK
**Time**: 1 hour  
**Risk**: Moderate (all writes logged)  
**What it does**: ChatGPT can update sheets and run approved scripts

**Additional setup**:
```bash
# Enable Slack notifications (optional but recommended)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**What ChatGPT can do**:
- ✅ Everything from Option 1
- ✅ Update Google Sheets
- ✅ Run whitelisted scripts (battery_arbitrage.py, etc.)
- ✅ All actions logged and alerted
- ❌ Cannot run arbitrary commands

---

### **Option 3: Full Automation** 🚨 HIGH RISK
**Time**: 2-3 hours  
**Risk**: High (requires strong security)  
**What it does**: ChatGPT can do almost anything

**Additional requirements**:
- SSL certificate (HTTPS)
- IP whitelisting
- Rate limiting
- Comprehensive monitoring

**What ChatGPT can do**:
- ✅ Everything from Options 1 & 2
- ✅ Execute BigQuery INSERT/UPDATE/DELETE
- ✅ Run any SSH command (with approval workflow)
- ✅ Deploy code changes
- ⚠️ Requires approval for dangerous operations

---

## 🎯 Recommended Approach

### **Week 1: Start with Read-Only**
```bash
# Deploy on your Mac for testing
python api_gateway.py

# ChatGPT conversation:
You: "What were electricity prices yesterday?"
ChatGPT: [Automatically queries BigQuery] 
         "Average: £52.30/MWh, Peak: £120.50/MWh..."
```

### **Week 2: Add ChatGPT Action**
1. Go to ChatGPT → Settings → Actions
2. Create new action
3. Upload OpenAPI schema (see full guide)
4. Test with queries

### **Week 3: Enable Write Access (if needed)**
```bash
# Add Slack alerts first!
export SLACK_WEBHOOK_URL="your-webhook"

# Then enable write endpoints
# ChatGPT can now update your Google Sheet
```

### **Week 4: Move to Production (optional)**
```bash
# Deploy to UpCloud with SSL
scp api_gateway.py root@94.237.55.15:/opt/arbitrage/
# Setup systemd service
# Enable HTTPS
# Add rate limiting
```

---

## 🔒 Security Checklist

Before enabling:
- [ ] Generate strong API key (32+ characters)
- [ ] Store API key in environment variable (not in code)
- [ ] Enable logging to file
- [ ] Set up Slack/email alerts
- [ ] Test all endpoints manually first
- [ ] Start with read-only access
- [ ] Add rate limiting (10-20 requests/min)
- [ ] Use HTTPS in production
- [ ] Whitelist IP addresses if possible
- [ ] Have rollback plan

---

## 📊 Quick Test Commands

```bash
# Set your API key
export API_KEY="your-api-key-here"
export API_URL="http://localhost:8000"

# Test health
curl $API_URL/

# Test prices (read-only)
curl -H "Authorization: Bearer $API_KEY" \
  "$API_URL/bigquery/prices?days=7"

# Test wind generation
curl -H "Authorization: Bearer $API_KEY" \
  "$API_URL/bigquery/generation?days=14&fuel_type=WIND"

# Test server status
curl -H "Authorization: Bearer $API_KEY" \
  "$API_URL/upcloud/status"
```

---

## 💡 Example ChatGPT Conversations

### **With Read-Only Access**:
```
You: "What's the average electricity price this month?"

ChatGPT: [Automatically calls your API]
"Average electricity price for November 2025:
• Mean: £48.20/MWh
• Peak: £156.30/MWh (Nov 4 at 18:30)
• Minimum: -£8.50/MWh (Nov 2 at 03:00)
• Negative price hours: 12"

You: "Compare that to last month"

ChatGPT: [Queries October data]
"October 2025 comparison:
• October avg: £52.80/MWh (9.5% higher)
• November has more negative prices (12 vs 6)
• Peak prices similar
• Likely due to increased wind generation"
```

### **With Write Access**:
```
You: "Update my dashboard with today's data"

ChatGPT: [Calls /upcloud/run-script endpoint]
"✅ Dashboard updated successfully!
• Ran: battery_arbitrage.py
• Processed: 275 rows
• Updated: Google Sheets at 10:45 UTC
• Status: All healthy"
```

---

## ❓ FAQ

**Q: Is this safe?**  
A: Read-only access is very safe. Write access requires proper security measures (API keys, logging, rate limiting).

**Q: What are the costs?**  
A: Minimal - same BigQuery costs you already have. API calls to ChatGPT cost ~$0.01 per conversation.

**Q: Can ChatGPT access this automatically?**  
A: Yes, once you create a ChatGPT Action. It will call your API whenever you ask questions about your data.

**Q: What if something goes wrong?**  
A: All write operations are logged. You can disable the API server instantly, and your data remains unchanged.

**Q: Do I need to keep my computer on?**  
A: For development, yes. For production, deploy to your UpCloud server (runs 24/7).

**Q: Can other people access this?**  
A: No - only you have the API key. Anyone without the key gets HTTP 403 Forbidden.

---

## 📚 Full Documentation

- **AI_DIRECT_ACCESS_SETUP.md** - Complete setup guide (you're reading the summary)
- **AI_INTEGRATION_GUIDE.md** - How ChatGPT currently works
- **MASTER_SYSTEM_DOCUMENTATION.md** - Full system documentation

---

## 🎯 Next Steps

1. **Read the full setup guide**: `AI_DIRECT_ACCESS_SETUP.md`
2. **Start with Option 1** (read-only): Safe and easy
3. **Test thoroughly**: Use curl commands
4. **Create ChatGPT Action**: Enable AI conversation
5. **Add write access** (optional): Only if needed
6. **Deploy to production** (optional): Move to UpCloud

**Remember**: Start simple, test everything, add security! 🚀

---

*Created: 2025-11-06*  
*Status: Ready to implement*
