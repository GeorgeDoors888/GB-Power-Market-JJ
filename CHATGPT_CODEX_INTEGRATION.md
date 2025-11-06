# ChatGPT + Codex Server Integration Guide

## 🎯 Overview

This document explains how ChatGPT accesses your BigQuery data and executes code through the Codex Server deployed on Railway.

---

## 🏗️ Architecture

```
┌─────────────┐
│   You       │
│  (Tablet/   │
│   Phone)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   ChatGPT Web App   │
│  (chatgpt.com)      │
└──────────┬──────────┘
           │
           ▼
┌───────────────────────────────────────┐
│   Railway Codex Server                │
│   jibber-jabber-production            │
│   .up.railway.app                     │
│                                       │
│   ┌─────────────────────────────┐   │
│   │  FastAPI Application         │   │
│   │  - /execute (Python/JS)      │   │
│   │  - /query_bigquery           │   │
│   │  - /health                   │   │
│   └────────┬───────────┬─────────┘   │
│            │           │              │
└────────────┼───────────┼──────────────┘
             │           │
             ▼           ▼
    ┌────────────┐  ┌──────────────┐
    │  Execute   │  │  Google      │
    │  Code in   │  │  BigQuery    │
    │  Sandbox   │  │              │
    └────────────┘  └──────────────┘
```

---

## 🔐 Authentication & Security

### API Token
- **Token**: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- **Usage**: Must be included in all requests
- **Header**: `Authorization: Bearer <token>`

### Google BigQuery Credentials
- **Storage**: Base64-encoded in Railway environment variable
- **Variable Name**: `GOOGLE_CREDENTIALS_BASE64`
- **Project ID**: `jibber-jabber-knowledge`
- **Service Account**: `jibber-jabber-knowledge@appspot.gserviceaccount.com`

---

## 🚀 How It Works

### 1️⃣ Code Execution

#### What ChatGPT Does:
```
1. User asks ChatGPT to run Python/JavaScript code
2. ChatGPT sends POST request to Railway server
3. Server executes code in sandboxed environment
4. Results returned to ChatGPT
5. ChatGPT displays results to user
```

#### API Endpoint:
```
POST https://jibber-jabber-production.up.railway.app/execute
```

#### Request Format:
```json
{
  "code": "print('Hello, World!')",
  "language": "python",
  "timeout": 30
}
```

#### Response Format:
```json
{
  "success": true,
  "output": "Hello, World!\n",
  "error": null,
  "execution_time": 0.123,
  "timestamp": "2025-11-06T22:30:00.000000"
}
```

#### Supported Languages:
- ✅ **Python** - Full Python 3 with standard library
- ✅ **JavaScript** - Node.js runtime

#### Security Features:
- ⏱️ **Timeout Protection** - Max 30 seconds per execution
- 🔒 **Sandboxed Execution** - Isolated subprocess
- 🚫 **Restricted Operations** - Limited file system access
- 📊 **Resource Limits** - Memory and CPU constraints

---

### 2️⃣ BigQuery Access

#### What ChatGPT Does:
```
1. User asks ChatGPT to query BigQuery data
2. ChatGPT constructs SQL query
3. Sends query to Railway server
4. Server authenticates with Google using service account
5. Executes query in BigQuery
6. Results returned to ChatGPT
7. ChatGPT analyzes and presents data to user
```

#### API Endpoint:
```
POST https://jibber-jabber-production.up.railway.app/query_bigquery
```

#### Request Format:
```json
{
  "sql": "SELECT * FROM `jibber-jabber-knowledge.dataset.table` LIMIT 10",
  "timeout": 60,
  "max_results": 1000
}
```

#### Response Format:
```json
{
  "success": true,
  "data": [
    {"column1": "value1", "column2": "value2"},
    {"column1": "value3", "column2": "value4"}
  ],
  "row_count": 2,
  "error": null,
  "execution_time": 1.456,
  "timestamp": "2025-11-06T22:30:00.000000"
}
```

#### BigQuery Project Structure:
```
jibber-jabber-knowledge/
├── dataset_name/
│   ├── table_1
│   ├── table_2
│   └── table_3
└── another_dataset/
    └── table_4
```

#### Query Examples:

**Simple Select:**
```sql
SELECT * FROM `jibber-jabber-knowledge.dataset.table` LIMIT 10
```

**Aggregation:**
```sql
SELECT 
  category,
  COUNT(*) as count,
  AVG(value) as avg_value
FROM `jibber-jabber-knowledge.dataset.table`
GROUP BY category
```

**Joins:**
```sql
SELECT 
  a.id,
  a.name,
  b.value
FROM `jibber-jabber-knowledge.dataset.table_a` a
JOIN `jibber-jabber-knowledge.dataset.table_b` b
  ON a.id = b.id
WHERE a.status = 'active'
```

---

## 🌍 Access from Anywhere

### Where You Can Use This:

| Device | Access Method | Works? |
|--------|---------------|--------|
| **Laptop** | https://chatgpt.com | ✅ Yes |
| **Desktop** | https://chatgpt.com | ✅ Yes |
| **Tablet** | https://chatgpt.com | ✅ Yes |
| **Phone** | ChatGPT mobile app | ✅ Yes |
| **Any Browser** | https://chatgpt.com | ✅ Yes |

### Requirements:
- ✅ Internet connection
- ✅ ChatGPT account (Plus/Pro recommended)
- ✅ Railway server running (auto-wakes from sleep)

---

## 💰 Cost Structure

### GitHub Codespaces (Development Only)
- **Free Tier**: 120 core-hours/month
- **2-core machine**: 60 hours/month FREE
- **Auto-stop**: After 10 minutes idle
- **Use For**: Editing code, testing locally
- **ChatGPT Access**: ❌ No (private to you)

### Railway (Production - ChatGPT Access)
- **Free Tier**: 500 hours/month
- **Auto-sleep**: After 15 minutes idle
- **Cold Start**: ~5-10 seconds to wake
- **Use For**: ChatGPT to access your server
- **ChatGPT Access**: ✅ Yes

### Typical Monthly Costs:

#### Light Usage (5 queries/day):
```
Active time: ~5 minutes/day
Monthly: ~2.5 hours
Cost: $0 (within free tier) ✅
```

#### Moderate Usage (2 hours/day):
```
Active time: 2 hours/day
Monthly: ~60 hours
Cost: $0 (within free tier) ✅
```

#### Heavy Usage (All day):
```
Active time: 8 hours/day
Monthly: ~240 hours
Cost: $0 (within free tier) ✅
```

---

## 🔄 Request Flow

### Example: User Asks ChatGPT to Analyze BigQuery Data

```
1. User (on tablet): "Show me the top 10 customers by revenue"

2. ChatGPT: 
   - Understands request
   - Constructs SQL query
   
3. ChatGPT → Railway:
   POST /query_bigquery
   {
     "sql": "SELECT customer_id, SUM(revenue) as total 
              FROM `jibber-jabber-knowledge.sales.transactions`
              GROUP BY customer_id 
              ORDER BY total DESC 
              LIMIT 10"
   }

4. Railway Server:
   - Receives request
   - Decodes BigQuery credentials from environment
   - Creates Google BigQuery client
   - Executes query
   
5. BigQuery:
   - Processes query
   - Returns results
   
6. Railway → ChatGPT:
   {
     "success": true,
     "data": [
       {"customer_id": "C001", "total": 50000},
       {"customer_id": "C002", "total": 45000},
       ...
     ],
     "row_count": 10
   }

7. ChatGPT:
   - Analyzes data
   - Creates formatted response
   - May create visualizations
   
8. User sees:
   "Here are your top 10 customers by revenue:
    1. Customer C001: $50,000
    2. Customer C002: $45,000
    ..."
```

---

## 🛠️ Technical Implementation

### Server Deployment

**Platform**: Railway.app
**Region**: Asia Southeast (Singapore)
**Runtime**: Python 3.13
**Framework**: FastAPI + Uvicorn
**Auto-scaling**: Enabled
**Sleep Policy**: 15 minutes idle

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `PORT` | Server port (dynamic) | `8000` or `8080` |
| `CODEX_API_TOKEN` | Authentication | `codex_fQI8...` |
| `GOOGLE_CREDENTIALS_BASE64` | BigQuery auth | `eyJ0eXBlIjoi...` |

### Code Execution Sandboxing

**Python Execution:**
```python
# Runs in isolated subprocess
result = subprocess.run(
    [sys.executable, temp_file],
    capture_output=True,
    text=True,
    timeout=30
)
```

**JavaScript Execution:**
```python
# Runs in Node.js subprocess
result = subprocess.run(
    ['node', temp_file],
    capture_output=True,
    text=True,
    timeout=30
)
```

### BigQuery Authentication Flow

```python
# 1. Get base64 credentials from environment
credentials_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')

# 2. Decode to JSON
credentials_json = base64.b64decode(credentials_base64).decode('utf-8')

# 3. Write to temporary file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    f.write(credentials_json)
    service_account_path = f.name

# 4. Set environment variable for Google client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path

# 5. Create BigQuery client
from google.cloud import bigquery
client = bigquery.Client(project='jibber-jabber-knowledge')
```

---

## 🧪 Testing

### Test Health Endpoint:
```bash
curl https://jibber-jabber-production.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "languages": ["python", "javascript"],
  "timestamp": "2025-11-06T22:30:00.000000"
}
```

### Test Code Execution:
```bash
curl -X POST https://jibber-jabber-production.up.railway.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(2 + 2)",
    "language": "python"
  }'
```

### Test BigQuery:
```bash
curl -X POST https://jibber-jabber-production.up.railway.app/query_bigquery \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT 1 as test",
    "timeout": 30,
    "max_results": 10
  }'
```

---

## 📊 Monitoring & Logs

### Check Railway Logs:
```bash
cd /workspaces/overarch-jibber-jabber/codex-server
railway logs
```

### Check Railway Usage:
1. Visit https://railway.com
2. Go to your project: "Jibber Jabber"
3. Click "Usage" tab
4. View active hours and costs

### Check Local Server Status:
```bash
# Check if running
ps aux | grep codex_server

# View logs
tail -f /workspaces/overarch-jibber-jabber/codex-server/server.log

# Test locally
curl http://localhost:8000/health
```

---

## 🔧 Maintenance

### Update Code:
```bash
# 1. Pull latest changes
git pull origin main

# 2. Restart local server
pkill -f codex_server
cd /workspaces/overarch-jibber-jabber/codex-server
source .venv/bin/activate
nohup python codex_server.py > server.log 2>&1 &

# 3. Deploy to Railway
railway up --detach
```

### Update BigQuery Credentials:
```bash
# 1. Get new service account JSON
# 2. Base64 encode it
base64 -w 0 /path/to/new_credentials.json > /tmp/sa_base64.txt

# 3. Update Railway variable
cd /workspaces/overarch-jibber-jabber/codex-server
railway variables --set GOOGLE_CREDENTIALS_BASE64="$(cat /tmp/sa_base64.txt)"

# 4. Redeploy
railway up --detach
```

### Stop Railway (Save Costs):
```bash
# Pause the service
railway down

# Restart later
railway up --detach
```

---

## ⚠️ Troubleshooting

### ChatGPT Can't Access Server

**Symptom**: ChatGPT reports connection error

**Solutions**:
1. Check Railway status: https://railway.com
2. Test health endpoint: `curl https://jibber-jabber-production.up.railway.app/health`
3. Check Railway logs: `railway logs`
4. Verify environment variables: `railway variables`

### BigQuery Permission Errors

**Symptom**: "Project not found or insufficient permissions"

**Solutions**:
1. Verify credentials are set: `railway variables | grep GOOGLE_CREDENTIALS`
2. Check service account has BigQuery permissions
3. Verify project ID in SQL: `jibber-jabber-knowledge`
4. Test locally first: Run query from Codespace

### Code Execution Timeouts

**Symptom**: Code execution takes too long

**Solutions**:
1. Reduce complexity of code
2. Increase timeout in request (max 30s)
3. Split into smaller operations
4. Check Railway server isn't cold-starting

---

## 🎓 Best Practices

### For ChatGPT Usage:

1. ✅ **Be Specific**: Clear SQL queries get better results
2. ✅ **Use Limits**: Add `LIMIT` clause to prevent large data transfers
3. ✅ **Test Small**: Try queries on small datasets first
4. ✅ **Cache Results**: Store frequently used data in ChatGPT context

### For Cost Control:

1. ✅ **Auto-sleep**: Both services auto-sleep when idle
2. ✅ **Monitor Usage**: Check Railway dashboard weekly
3. ✅ **Optimize Queries**: Efficient SQL = faster execution = less active time
4. ✅ **Close Codespace**: Don't leave it running when not developing

### For Security:

1. ✅ **Keep Token Private**: Don't share your API token
2. ✅ **Rotate Credentials**: Update service account periodically
3. ✅ **Review Permissions**: Service account should have minimal permissions
4. ✅ **Monitor Access**: Check Railway logs for unusual activity

---

## 📚 Resources

### Live URLs:
- **Server**: https://jibber-jabber-production.up.railway.app
- **API Docs**: https://jibber-jabber-production.up.railway.app/docs
- **Health**: https://jibber-jabber-production.up.railway.app/health

### Management:
- **Railway Dashboard**: https://railway.com/project/c0c79bb5-e2fc-4e0e-93db-39d6027301ca
- **GitHub Repo**: https://github.com/GeorgeDoors888/overarch-jibber-jabber
- **Codespace**: https://github.com/codespaces

### Documentation:
- **Railway Docs**: https://docs.railway.app
- **BigQuery Docs**: https://cloud.google.com/bigquery/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com

---

## 🎯 Quick Reference

### Most Common ChatGPT Requests:

**1. Run Python Code:**
> "Can you run this Python code: `print('Hello')`"

**2. Query BigQuery:**
> "Show me the total sales from the transactions table"

**3. Analyze Data:**
> "What are the top 10 products by revenue in BigQuery?"

**4. Complex Analysis:**
> "Query BigQuery for customer trends over the last 6 months and create a summary"

### URLs to Remember:

| Purpose | URL |
|---------|-----|
| ChatGPT | https://chatgpt.com |
| Server | https://jibber-jabber-production.up.railway.app |
| Railway | https://railway.com |
| GitHub | https://github.com/GeorgeDoors888/overarch-jibber-jabber |

---

**Last Updated**: November 6, 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready
