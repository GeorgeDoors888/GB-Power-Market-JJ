# 🚂 Railway Deployment - Complete Guide

*Last Updated: November 13, 2025*

## 📋 Overview

Railway hosts your **FastAPI backend server** that serves as the central API gateway for the GB Power Market JJ project, providing secure access to BigQuery data and Google Workspace integration.

## 🏗️ Project Configuration

### **Basic Details**
- **URL**: `https://jibber-jabber-production.up.railway.app`
- **Project Name**: Jibber Jabber (production environment)
- **Project ID**: `c0c79bb5-e2fc-4e0e-93db-39d6027301ca`
- **Service ID**: `08ef4354-bd64-4af9-8213-2cc89fd1e3fc`
- **Region**: `asia-southeast1-eqsg3a`
- **Runtime**: Python 3.9+ with FastAPI
- **Builder**: Nixpacks v1.38.0
- **Root Directory**: `codex-server`

### **GitHub Integration**
- **Repository**: `GeorgeDoors888/GB-Power-Market-JJ`
- **Branch**: `main`
- **Auto-Deploy**: ✅ Enabled
- **Deployment Trigger**: Push to main branch

---

## 📁 What Railway Contains

### **File Structure**
```
codex-server/
├── codex_server_secure.py     # Main FastAPI application (840 lines)
├── requirements.txt           # Python dependencies
├── railway.json              # Railway configuration
├── Procfile                  # Process definition
├── start.sh                  # Startup script
├── test_client.py            # Testing utilities
└── __pycache__/              # Python cache
```

### **Core Components**

#### 🔧 **Main Application** (`codex_server_secure.py`)
- **Framework**: FastAPI with Pydantic models
- **Security**: Bearer token authentication
- **Logging**: Structured logging with timestamps
- **Error Handling**: Comprehensive exception handling
- **Code Execution**: Sandboxed Python/JS execution
- **Timeout Management**: 10-30 second timeouts per operation

#### ⚙️ **Configuration Files**

**`railway.json`**:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python codex_server_secure.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**`Procfile`**:
```
web: python codex_server_secure.py
```

---

## 🌐 API Endpoints

### **BigQuery Interface**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/query_bigquery` | POST | Execute SQL queries on UK energy data |
| `/query_bigquery_get` | GET | Simple SQL queries via URL parameters |
| `/debug/env` | GET | Environment variable debugging |

### **Google Workspace Integration**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/workspace/health` | GET | Check workspace connection status |
| `/workspace/dashboard` | GET | List all accessible spreadsheets |
| `/workspace/read_sheet` | POST | Read data from specific sheet |
| `/workspace/write_sheet` | POST | Write data to sheets |
| `/workspace/create_sheet` | POST | Create new spreadsheet |
| `/workspace/list_files` | GET | List Google Drive files |
| `/workspace/read_doc` | POST | Read Google Docs content |
| `/workspace/create_doc` | POST | Create new Google Doc |
| `/workspace/list_spreadsheets` | GET | List Google Sheets only |
| `/workspace/get_sheet_metadata` | POST | Get sheet structure info |
| `/workspace/batch_read` | POST | Read multiple sheets at once |

### **Utility Endpoints**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Server health check |
| `/execute` | POST | Simple Python/JS code execution |

---

## 🔐 Environment Variables

### **Authentication**
```bash
CODEX_API_TOKEN=codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```
*Used for bearer token authentication on all endpoints*

### **BigQuery Configuration**
```bash
BQ_PROJECT_ID=inner-cinema-476211-u9
BQ_DATASET=uk_energy_prod
GOOGLE_APPLICATION_CREDENTIALS=<base64-encoded-bigquery-credentials>
```

### **Google Workspace**
```bash
GOOGLE_WORKSPACE_CREDENTIALS=<base64-encoded-workspace-credentials>
```
*Base64 encoded `workspace-credentials.json` (3160 characters)*

### **Service Account Details**
- **BigQuery SA**: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`
- **Workspace SA**: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- **Impersonates**: `george@upowerenergy.uk`

---

## 📊 Data Access

### **BigQuery Integration**
- **Project**: `inner-cinema-476211-u9` (Smart Grid)
- **Dataset**: `uk_energy_prod` (185+ tables)
- **Region**: US
- **Main Tables**:
  - `bmrs_mid` - Market Index Data (155,405+ rows)
  - `bmrs_fuelinst` - Fuel Instance data
  - `bmrs_freq` - Frequency data
  - `bmrs_bod` - Bid-Offer Data (391M+ rows)
  - `bmrs_*_iris` - Real-time data tables

### **Google Workspace Access**
- **Primary Sheet**: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`
- **Scopes**:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive`
  - `https://www.googleapis.com/auth/documents`
- **Domain-Wide Delegation**: ✅ Enabled

---

## 🚀 Deployment Methods

### **Method 1: Auto-Deploy (Recommended)**
```bash
# Connected to GitHub - deploys automatically
git add .
git commit -m "Update railway deployment"
git push origin main
# Railway detects changes and auto-deploys
```

### **Method 2: Manual CLI Deploy**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link  # Select: Jibber Jabber (production)

# Deploy from codex-server directory
cd "codex-server"
railway up

# Monitor deployment
railway logs
```

### **Method 3: Environment Variables Update**
```bash
# Set workspace credentials
python3 set_railway_workspace_credentials.py

# Or manually via CLI
railway variables set GOOGLE_WORKSPACE_CREDENTIALS="$(base64 -i workspace-credentials.json | tr -d '\n')"
```

---

## 📦 Dependencies

### **Production Requirements** (`requirements.txt`)
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
python-multipart>=0.0.6
requests>=2.31.0
google-cloud-bigquery>=3.11.0
gspread>=5.12.0                    # Google Sheets API
google-auth>=2.23.0                # Authentication
google-api-python-client>=2.100.0  # Google APIs suite
```

### **Build Process**
1. **Detection**: Nixpacks detects Python project
2. **Environment**: Creates Python virtual environment
3. **Dependencies**: Installs from `requirements.txt`
4. **Build Time**: ~29 seconds average
5. **Start Command**: `python codex_server_secure.py`
6. **Port**: Auto-assigned by Railway (usually 8080)

---

## 🔗 Integration Architecture

```
ChatGPT Custom GPT ──Bearer Auth──→ Railway Backend
Google Sheets Apps Script ──Via Vercel Proxy──→ Railway Backend
Direct API Calls ──Bearer Auth──→ Railway Backend

Railway Backend ──Query──→ BigQuery inner-cinema-476211-u9
Railway Backend ──API Calls──→ Google Workspace APIs

BigQuery → UK Energy Data (185+ Tables)
Google Workspace APIs → Google Sheets/Docs/Drive
```

### **Data Flow Examples**

**ChatGPT Query:**
```
ChatGPT → Railway /query_bigquery → BigQuery → UK Energy Data → Response
```

**Apps Script Dashboard:**
```
Google Sheets → Apps Script → Vercel Proxy → Railway → BigQuery → Dashboard Data
```

**Workspace Integration:**
```
ChatGPT → Railway /workspace/read_sheet → Google Sheets API → Sheet Data
```

---

## ⚡ Performance Metrics

### **Response Times**
- **Cold Start**: 2-5 seconds (first request after idle)
- **Average Response**: 2-4 seconds
- **BigQuery Queries**: 1-10 seconds (depending on complexity)
- **Workspace Operations**: 1-3 seconds
- **Maximum Timeout**: 30 seconds

### **Reliability**
- **Uptime**: 100% (containerized with auto-restart)
- **Auto-Restart**: On failure (max 10 retries)
- **Health Monitoring**: `/health` endpoint
- **Error Handling**: Comprehensive exception catching

### **Scaling**
- **Concurrent Requests**: Handles multiple simultaneous requests
- **Rate Limiting**: Managed by Railway platform
- **Resource Limits**: Railway free tier limits apply
- **Memory Usage**: ~100-200MB typical

---

## 🧪 Testing & Debugging

### **Health Checks**
```bash
# Basic health check
curl "https://jibber-jabber-production.up.railway.app/health"

# Environment debug (requires auth)
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  "https://jibber-jabber-production.up.railway.app/debug/env"

# Workspace health
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  "https://jibber-jabber-production.up.railway.app/workspace/health"
```

### **BigQuery Test**
```bash
# Simple query test
curl -X POST "https://jibber-jabber-production.up.railway.app/query_bigquery" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`"}'
```

### **Monitoring Commands**
```bash
# View deployment logs
railway logs

# Check deployment status
railway status

# List environment variables
railway variables

# Connect to deployment shell
railway shell
```

---

## 🔧 Troubleshooting

### **Common Issues**

#### 1. **401 Unauthorized**
- **Cause**: Missing or invalid bearer token
- **Fix**: Include `Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`

#### 2. **BigQuery Access Denied**
- **Cause**: Wrong project ID or credentials
- **Fix**: Verify `BQ_PROJECT_ID=inner-cinema-476211-u9`

#### 3. **Workspace API Errors**
- **Cause**: Invalid workspace credentials or delegation
- **Fix**: Check `GOOGLE_WORKSPACE_CREDENTIALS` and domain delegation

#### 4. **Cold Start Delays**
- **Cause**: Railway container sleeping after inactivity
- **Solution**: Expected behavior, first request takes 2-5 seconds

### **Debug Endpoints**
```bash
# Check environment configuration
GET /debug/env

# Verify BigQuery connection
POST /query_bigquery {"sql": "SELECT 1"}

# Test workspace access
GET /workspace/health
```

---

## 🎯 Use Cases

### **Primary Functions**

1. **ChatGPT Custom GPT Backend**
   - Powers natural language queries to UK energy data
   - Provides secure API access with authentication
   - Handles complex BigQuery operations

2. **Google Sheets Dashboard Backend**
   - Supplies real-time energy market data
   - Updates dashboard via Apps Script integration
   - Manages workspace operations

3. **Direct API Access**
   - Allows programmatic access to energy datasets
   - Supports both simple and complex SQL queries
   - Provides workspace automation capabilities

### **Business Applications**
- **Battery VLP Analysis**: Query bid-offer data for arbitrage opportunities
- **Market Price Tracking**: Access system buy/sell prices and volumes
- **Generation Mix Analysis**: Monitor fuel types and generation capacity
- **Grid Frequency Monitoring**: Track system stability metrics
- **Interconnector Analysis**: Monitor cross-border electricity flows

---

## 📚 Related Documentation

- **Configuration**: `PROJECT_CONFIGURATION.md`
- **Authentication**: `WORKSPACE_RAILWAY_SUCCESS.md`
- **BigQuery Setup**: `RAILWAY_BIGQUERY_FIX_STATUS.md`
- **ChatGPT Integration**: `CHATGPT_RAILWAY_SETUP.md`
- **API Reference**: `WORKSPACE_API_MASTER_REFERENCE.md`
- **Data Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`

---

## 🔒 Security Notes

### **Authentication**
- All endpoints require bearer token authentication
- Tokens are validated server-side
- No public endpoints (except `/health`)

### **Data Access**
- Service accounts use least-privilege access
- BigQuery access limited to specific datasets
- Workspace delegation properly configured

### **Best Practices**
- Keep bearer tokens secure
- Rotate credentials periodically  
- Monitor access logs via Railway dashboard
- Use HTTPS for all communications

---

## ✅ Success Criteria

Railway deployment is successful when:

- [x] Health endpoint returns 200 OK
- [x] BigQuery queries return data (155,405+ rows in `bmrs_mid`)
- [x] Workspace endpoints access Google Sheets
- [x] Bearer authentication works correctly
- [x] Auto-deploy from GitHub functions
- [x] All 11 endpoints respond properly
- [x] ChatGPT integration working
- [x] Apps Script dashboard updating

---

**Status**: 🟢 **PRODUCTION READY**  
**Last Deployment**: Latest commit auto-deployed  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

---

*This guide provides complete Railway deployment information for the GB Power Market JJ project. For updates, see commit history and related documentation files.*
# - /gb_energy_dashboard
# - /workspace_health
```

---

### Step 3: Update Requirements.txt (2 min)

Add to your Railway project's `requirements.txt`:

```txt
gspread>=5.12.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-httplib2>=0.1.1
```

Then commit and push:
```bash
git add requirements.txt
git commit -m "Add Google Workspace dependencies"
git push origin main
```

---

### Step 4: Test Railway Endpoints (3 min)

After Railway deploys (watch the logs):

```bash
# Test workspace health
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace_health

# Should return:
{
  "status": "healthy",
  "services": {
    "sheets": "ok",
    "drive": "ok",
    "docs": "ok"
  }
}

# Test reading GB Energy Dashboard
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/gb_energy_dashboard

# Should return list of 29 worksheets
```

---

### Step 5: Update ChatGPT Instructions (5 min)

1. Go to your ChatGPT Custom GPT settings
2. Replace instructions with content from: `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`
3. Save and test

**Test ChatGPT**:
- "Show me the GB Energy Dashboard worksheets"
- "Read the Dashboard worksheet"
- "Find all battery-related files in Drive"
- "Create a test report document"

---

## 🧪 Testing Commands

### Local Testing (Before Railway Deploy)

```bash
# Start Railway endpoints locally
cd /path/to/railway/project
python3 main.py

# In another terminal, test:
curl -X POST http://localhost:8000/read_sheet \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{
    "sheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
    "worksheet": "Dashboard"
  }'
```

### Railway Testing (After Deploy)

```bash
# Replace localhost:8000 with your Railway URL
export RAILWAY_URL="https://jibber-jabber-production.up.railway.app"
export AUTH_TOKEN="Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

# Test health
curl -H "Authorization: $AUTH_TOKEN" "$RAILWAY_URL/workspace_health"

# Test sheets
curl -H "Authorization: $AUTH_TOKEN" "$RAILWAY_URL/gb_energy_dashboard"

# Test drive search
curl -H "Authorization: $AUTH_TOKEN" "$RAILWAY_URL/search_drive?name=battery"
```

---

## 📊 What ChatGPT Can Now Do

### Before (Current)
```
User: "Show me battery revenue"
ChatGPT: [Queries BigQuery] → Returns data as text/table
```

### After (With Workspace Access)
```
User: "Show me battery revenue"
ChatGPT: 
  1. [Queries BigQuery] → Gets data
  2. [Reads Dashboard] → Gets current dashboard state
  3. [Compares] → Shows differences
  4. [Offers] → "Would you like me to update the dashboard?"
```

### New Capabilities

**Dashboard Management**:
- "Show me the current dashboard"
- "Update dashboard with latest battery data"
- "List all worksheets in GB Energy Dashboard"

**File Discovery**:
- "Find all CSV files containing 'VLP'"
- "Show me files modified this week"
- "List all battery analysis spreadsheets"

**Report Generation**:
- "Create a weekly battery revenue report"
- "Generate VLP arbitrage analysis document"
- "Write findings to a new Google Doc"

**Data Synchronization**:
- "Query BigQuery and update the dashboard"
- "Refresh all dashboard metrics"
- "Write analysis results to a new worksheet"

---

## 🔒 Security Notes

### Credential Safety
- ✅ Store in environment variable (base64 encoded)
- ✅ Never commit raw JSON to public repos
- ✅ Railway environment variables are encrypted
- ✅ Credentials only accessible within Railway container

### Access Control
- ✅ Bearer token authentication required for all endpoints
- ✅ Workspace credentials impersonate george@upowerenergy.uk only
- ✅ Can only access files george@ can access
- ✅ Audit logs available in Google Workspace Admin

### Best Practices
- ✅ Use read-only scopes where possible
- ✅ Monitor Railway logs for suspicious activity
- ✅ Rotate bearer token periodically
- ✅ Review Workspace audit logs monthly

---

## 🐛 Troubleshooting

### "Credentials file not found"
```python
# In Railway startup, add debug:
import os
print("Current directory:", os.getcwd())
print("Files:", os.listdir("."))
print("Workspace creds exists:", os.path.exists("workspace-credentials.json"))
```

### "unauthorized_client" error
- Wait 10 minutes after adding scopes in Workspace Admin
- Verify scopes were added to correct Client ID: 108583076839984080568
- Check `/workspace_health` endpoint for specific error

### "Permission denied"
- Verify george@upowerenergy.uk can access the file/sheet
- Check file is shared with george@ or in a shared Drive
- Test with a file you definitely own

### ChatGPT can't call endpoints
- Verify Railway URL is correct in instructions
- Test endpoints manually with curl first
- Check Railway logs for errors
- Verify bearer token matches

---

## 📈 Monitoring

### Railway Logs
```bash
# View real-time logs
railway logs --follow

# Filter for Workspace calls
railway logs | grep "workspace"

# Check for errors
railway logs | grep "ERROR"
```

### Key Metrics to Watch
- Endpoint response times (should be <2 seconds)
- Error rates (should be <1%)
- Workspace API quota (Google limits apply)
- Railway memory usage

### Google Workspace Audit
1. Go to: https://admin.google.com/ac/reporting/audit/drive
2. Filter by: jibber-jabber-knowledge@appspot.gserviceaccount.com
3. Review: File access, modifications, creations

---

## 🎯 Success Criteria

✅ **Railway Health Check Passes**
```json
{
  "status": "healthy",
  "services": {
    "sheets": "ok",
    "drive": "ok", 
    "docs": "ok"
  }
}
```

✅ **ChatGPT Can Access Dashboard**
- "Show me GB Energy Dashboard" → Lists 29 worksheets
- "Read Dashboard worksheet" → Returns data

✅ **ChatGPT Can Search Drive**
- "Find battery files" → Returns file list with links

✅ **ChatGPT Can Create Docs**
- "Create test report" → Returns document link

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `workspace-credentials.json` | Service account with delegation |
| `railway_google_workspace_endpoints.py` | New API endpoints code |
| `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md` | Updated ChatGPT instructions |
| `RAILWAY_DEPLOYMENT_GUIDE.md` | This file |
| `test_all_google_services.py` | Local testing script |

---

## 🎊 What's Next

After successful deployment:

1. **Test all endpoints** with ChatGPT
2. **Create example reports** to verify Docs creation
3. **Set up monitoring** for Railway endpoints
4. **Document common queries** for team reference
5. **Add more endpoints** as needed (e.g., batch operations)

---

**Deployment Time**: 15 minutes  
**Testing Time**: 5 minutes  
**Total**: 20 minutes from start to ChatGPT having full Workspace access! 🚀
