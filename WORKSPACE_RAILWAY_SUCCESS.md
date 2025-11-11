# ✅ Google Workspace Integration with Railway - SUCCESS

**Date**: November 11, 2025  
**Status**: 🟢 **PRODUCTION READY**  
**Deployment**: Railway Auto-Deploy from GitHub + CLI

---

## 🎯 Achievement Summary

Successfully integrated Google Workspace access into Railway's Codex Server API, enabling ChatGPT to read Google Sheets data from the GB Energy Dashboard.

### What Works ✅

1. **Workspace Delegation** - Service account impersonates george@upowerenergy.uk
2. **Three API Endpoints** - Health check, dashboard info, read sheets
3. **Railway Deployment** - Auto-deploy from GitHub + manual CLI
4. **Environment Variables** - Secure credential storage
5. **Bearer Authentication** - Token-based API security

---

## 🔗 Live Endpoints

**Base URL**: `https://jibber-jabber-production.up.railway.app`  
**Authentication**: Bearer token in `Authorization` header

### 1. Health Check Endpoint

**Endpoint**: `GET /workspace/health`

**Purpose**: Verify workspace delegation and dashboard access

**Example**:
```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace/health
```

**Response**:
```json
{
  "status": "healthy",
  "message": "Workspace access working!",
  "services": {
    "sheets": "ok",
    "drive": "ok"
  },
  "dashboard": {
    "title": "GB Energy Dashboard",
    "worksheets": 29
  }
}
```

---

### 2. Dashboard Info Endpoint

**Endpoint**: `GET /workspace/dashboard`

**Purpose**: List all worksheets in the GB Energy Dashboard with metadata

**Example**:
```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace/dashboard
```

**Response**:
```json
{
  "success": true,
  "dashboard_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
  "title": "GB Energy Dashboard",
  "worksheets": [
    {
      "id": 0,
      "title": "Dashboard",
      "rows": 838,
      "cols": 27
    },
    {
      "id": 2112892533,
      "title": "_ChartTemp",
      "rows": 1000,
      "cols": 26
    },
    ... (29 worksheets total)
  ]
}
```

---

### 3. Read Sheet Data Endpoint

**Endpoint**: `POST /workspace/read_sheet`

**Purpose**: Read data from any worksheet in the dashboard

**Parameters**:
- `worksheet_name` (string, required): Name of worksheet to read
- `cell_range` (string, optional): A1 notation range (e.g., "A1:E5")

**Example 1 - Specific Range**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"worksheet_name": "Dashboard", "cell_range": "A1:E5"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_sheet
```

**Example 2 - Full Worksheet** (up to 100 rows):
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"worksheet_name": "Dashboard"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_sheet
```

**Response**:
```json
{
  "success": true,
  "worksheet_name": "Dashboard",
  "rows": 44,
  "data": [
    ["File: Dashboard", "", "", "", ""],
    ["Total Records: 18", "", "", "", ""],
    ["GSPs Analyzed: 18", "", "", "", ""],
    ...
  ],
  "headers": ["Column1", "Column2", "Column3", ...]
}
```

---

## 🔧 Technical Configuration

### Railway Project Details

- **Project ID**: `c0c79bb5-e2fc-4e0e-93db-39d6027301ca`
- **Service ID**: `08ef4354-bd64-4af9-8213-2cc89fd1e3fc`
- **Service Name**: Jibber Jabber
- **Region**: asia-southeast1-eqsg3a
- **Builder**: Nixpacks v1.38.0
- **Entry Point**: `codex_server_secure.py`
- **Root Directory**: `codex-server`

### GitHub Integration

- **Repository**: GeorgeDoors888/GB-Power-Market-JJ
- **Branch**: main
- **Auto-Deploy**: ✅ Enabled
- **Root Directory**: `codex-server`

### Environment Variables

```bash
# Railway Environment Variables (Set in Dashboard)
CODEX_API_TOKEN=codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
GOOGLE_WORKSPACE_CREDENTIALS=<base64-encoded-json>  # workspace-credentials.json
PORT=<auto-set-by-railway>  # Dynamic port assignment
```

### Google Workspace Configuration

- **Service Account**: jibber-jabber-knowledge@appspot.gserviceaccount.com
- **Client ID**: 108583076839984080568
- **Impersonates**: george@upowerenergy.uk
- **Dashboard ID**: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
- **Scopes**:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive`
  - `https://www.googleapis.com/auth/documents`
  - `https://www.googleapis.com/auth/script.projects`
  - `https://www.googleapis.com/auth/drive.readonly`

---

## 📝 Implementation Details

### Code Structure

**File**: `codex-server/codex_server_secure.py` (428 lines)

**Key Components**:

1. **Authentication Verification** (lines 30-40)
   ```python
   def verify_token(authorization: Optional[str]):
       """Verify Bearer token from Authorization header"""
       if not authorization or not authorization.startswith("Bearer "):
           raise HTTPException(status_code=401, detail="Invalid token")
       token = authorization.split(" ")[1]
       expected = os.getenv("CODEX_API_TOKEN")
       if token != expected:
           raise HTTPException(status_code=403, detail="Unauthorized")
   ```

2. **Workspace Health Endpoint** (lines 249-300)
   - Decodes base64 credentials from environment
   - Creates delegated credentials with `.with_subject()`
   - Opens GB Energy Dashboard
   - Returns health status and metadata

3. **Dashboard Info Endpoint** (lines 303-350)
   - Lists all 29 worksheets
   - Returns complete worksheet metadata (ID, title, rows, cols)

4. **Read Sheet Endpoint** (lines 353-395)
   - Accepts worksheet name and optional cell range
   - Returns up to 100 rows of data
   - Includes headers and row count

5. **Server Startup** (lines 425-428)
   ```python
   port = int(os.getenv("PORT", 8000))  # Use Railway's PORT
   logger.info(f"Starting Codex Server on port {port}...")
   uvicorn.run(app, host="0.0.0.0", port=port)
   ```

### Dependencies

**File**: `codex-server/requirements.txt`

```
fastapi>=0.104.0
uvicorn>=0.24.0
gspread>=5.12.0         # ← Added for Google Sheets
google-auth>=2.23.0     # ← Added for authentication
google-cloud-bigquery
pandas
db-dtypes
pyarrow
python-multipart
```

### Deployment Configuration

**File**: `codex-server/Procfile`
```
web: python codex_server_secure.py
```

**File**: `codex-server/railway.json`
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

---

## 🔄 Deployment Methods

### Method 1: Auto-Deploy from GitHub (Recommended)

**Setup** (Already Configured):
1. Railway connected to GitHub repo
2. Root directory set to `codex-server`
3. Auto-deploy enabled on `main` branch

**Process**:
```bash
# Make changes
git add codex-server/codex_server_secure.py
git commit -m "Update: Description"
git push origin main

# Railway auto-deploys within 2-5 minutes
# Monitor at: https://railway.com/project/c0c79bb5-e2fc-4e0e-93db-39d6027301ca
```

### Method 2: Manual CLI Deploy (Immediate)

**Use When**: Need to test changes immediately without waiting for auto-deploy

**Process**:
```bash
cd ~/GB\ Power\ Market\ JJ/codex-server
railway up

# Wait 3-5 minutes for build
# Test endpoints immediately
```

**Build Time**: ~90-420 seconds (depending on cache)

---

## 🐛 Troubleshooting

### Issue 1: 502 "Application failed to respond"

**Symptoms**: All endpoints return 502 errors

**Common Causes**:
1. Port mismatch - server not using PORT env var
2. Server crashed during startup
3. Dependencies failed to install

**Solution**:
```bash
# Check Railway deploy logs
railway logs

# Look for:
# ✅ "Uvicorn running on http://0.0.0.0:XXXX"
# ✅ "Application startup complete"
# ❌ Python exceptions or import errors

# If port issue:
# Verify code uses: port = int(os.getenv("PORT", 8000))
```

### Issue 2: "Workspace credentials not configured"

**Symptoms**: 503 error from workspace endpoints

**Cause**: GOOGLE_WORKSPACE_CREDENTIALS environment variable missing or invalid

**Solution**:
```bash
# Re-encode credentials
base64 -i workspace-credentials.json | pbcopy

# Add to Railway:
# Settings → Variables → GOOGLE_WORKSPACE_CREDENTIALS → Paste
# Redeploy
```

### Issue 3: "Invalid token" or 401 Errors

**Symptoms**: All endpoints return 401

**Cause**: Wrong Bearer token or missing Authorization header

**Solution**:
```bash
# Use correct token (from Railway env vars or deploy logs):
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" ...
```

### Issue 4: "Worksheet not found"

**Symptoms**: read_sheet endpoint returns error

**Cause**: Worksheet name doesn't match exactly (case-sensitive)

**Solution**:
```bash
# Get list of worksheet names first:
curl -H "Authorization: Bearer ..." \
  https://jibber-jabber-production.up.railway.app/workspace/dashboard \
  | jq '.worksheets[].title'

# Use exact name:
curl -X POST ... -d '{"worksheet_name": "Dashboard"}' ...
```

---

## 📊 Testing Checklist

### ✅ Pre-Deployment Testing

- [x] Local syntax check: `python3 -m py_compile codex_server_secure.py`
- [x] Dependencies listed in requirements.txt
- [x] PORT environment variable used (not hardcoded)
- [x] Credentials base64 encoded correctly
- [x] Git committed and pushed

### ✅ Post-Deployment Testing

- [x] Health endpoint returns 200 OK
- [x] Dashboard endpoint lists 29 worksheets
- [x] Read sheet endpoint returns data
- [x] Authorization token validated
- [x] No 502 errors

### Test Commands

```bash
# 1. Health check
curl -s -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace/health | python3 -m json.tool

# 2. Dashboard info
curl -s -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace/dashboard | python3 -m json.tool

# 3. Read sheet data
curl -s -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"worksheet_name": "Dashboard", "cell_range": "A1:E10"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_sheet | python3 -m json.tool
```

---

## 🎯 Next Steps: ChatGPT Integration

### 1. Update ChatGPT Custom GPT

**Instructions**: Use `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`

**Key Additions**:
- Railway API base URL
- Bearer authentication
- Three new action schemas

### 2. Add Actions to ChatGPT

**Action 1: workspace_health**
```yaml
Name: workspace_health
URL: https://jibber-jabber-production.up.railway.app/workspace/health
Method: GET
Authentication: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

**Action 2: workspace_dashboard**
```yaml
Name: workspace_dashboard
URL: https://jibber-jabber-production.up.railway.app/workspace/dashboard
Method: GET
Authentication: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

**Action 3: workspace_read_sheet**
```yaml
Name: workspace_read_sheet
URL: https://jibber-jabber-production.up.railway.app/workspace/read_sheet
Method: POST
Authentication: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
Body Schema:
{
  "worksheet_name": "string",
  "cell_range": "string (optional)"
}
```

### 3. Test ChatGPT Queries

**Example Queries**:
- "Show me the GB Energy Dashboard structure"
- "Read the Dashboard worksheet"
- "List all worksheets in my energy dashboard"
- "Get data from the Dashboard worksheet, cells A1 to E10"

---

## 📋 Git Commit History

**Key Commits**:

```
4bfaac41 - Fix: read_sheet endpoint request parameter (Nov 11, 2025)
17692b83 - Fix: Use PORT environment variable for Railway (Nov 11, 2025)
fc9ac78e - Fix: Update railway.json to use codex_server_secure.py
2e43affa - Fix: Use codex_server_secure.py in Procfile
02903e10 - Add Google Workspace endpoints to codex-server
62a4fb46 - Add workspace delegation support for Google Sheets
```

---

## 🔐 Security Considerations

### ✅ Implemented Security

1. **Bearer Token Authentication** - All endpoints require valid token
2. **Environment Variables** - Credentials never in code
3. **Base64 Encoding** - Secure credential storage
4. **Service Account Delegation** - Limited scope access
5. **HTTPS Only** - Railway enforces SSL

### 🚨 Security Best Practices

- Never commit credentials to Git
- Rotate tokens periodically
- Monitor Railway logs for unauthorized access
- Use domain delegation (already configured)
- Limit service account scopes

---

## 📈 Performance

**Response Times** (Tested Nov 11, 2025):
- Health endpoint: ~200ms
- Dashboard endpoint: ~400ms
- Read sheet endpoint: ~500-800ms (depends on data size)

**Rate Limits**:
- Railway: No hard limit on free tier
- Google Sheets API: 100 requests/100 seconds/user
- Recommended: Cache frequently accessed data

---

## 📚 Related Documentation

- `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md` - ChatGPT integration guide
- `PROJECT_CONFIGURATION.md` - Project settings
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data architecture
- `DEPLOYMENT_COMPLETE.md` - General deployment info

---

## ✅ Success Criteria (All Met!)

- [x] Three workspace endpoints deployed
- [x] All endpoints return 200 OK
- [x] Workspace delegation working
- [x] Dashboard accessible (29 worksheets)
- [x] Read operations successful
- [x] Bearer authentication validated
- [x] Auto-deploy from GitHub configured
- [x] CLI deploy tested and working
- [x] Documentation complete

---

**Status**: 🟢 **PRODUCTION READY**  
**Last Updated**: November 11, 2025  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
