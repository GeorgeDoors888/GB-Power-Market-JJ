# 🚀 Railway + ChatGPT Deployment - Phase by Phase

**Project**: GB Power Market JJ  
**Goal**: Add Google Workspace capabilities to ChatGPT Custom GPT  
**Time**: ~25 minutes total (15 min Phase 1 + 10 min Phase 2)  
**Status**: Ready to start

---

## 📋 Prerequisites (Already Complete ✅)

- ✅ Workspace delegation active (all 5 scopes working)
- ✅ `workspace-credentials.json` file exists and tested
- ✅ All test scripts passing (Sheets, Drive, Docs, Apps Script)
- ✅ Railway API endpoints code ready (`railway_google_workspace_endpoints.py`)
- ✅ Updated ChatGPT instructions ready (`CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`)

---

# 🎯 PHASE 1: Railway Deployment (15 minutes)

**Goal**: Add Workspace capabilities to your Railway API  
**Current Railway**: https://jibber-jabber-production.up.railway.app  
**Current Endpoints**: `/query_bigquery`, `/health`  
**Adding**: 11 new endpoints for Sheets/Drive/Docs

---

## Step 1.1: Add Credentials to Railway (5 minutes)

You have **two options** - pick one:

### Option A: Environment Variable (Recommended - More Secure)

1. **Convert credentials to base64**:
   ```bash
   cd ~/GB\ Power\ Market\ JJ
   base64 workspace-credentials.json | pbcopy
   ```
   This copies the base64 string to your clipboard.

2. **Add to Railway**:
   - Go to: https://railway.app/project/[YOUR_PROJECT]
   - Click: **Variables** tab
   - Click: **New Variable**
   - Name: `GOOGLE_WORKSPACE_CREDENTIALS`
   - Value: Paste the base64 string (Cmd+V)
   - Click: **Add**

3. **Update your Railway code to decode it**:
   ```python
   import os
   import base64
   import json
   import tempfile
   
   # Decode base64 credentials from environment
   creds_base64 = os.environ.get('GOOGLE_WORKSPACE_CREDENTIALS')
   creds_json = base64.b64decode(creds_base64).decode('utf-8')
   
   # Write to temporary file
   with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
       f.write(creds_json)
       WORKSPACE_CREDS_PATH = f.name
   ```

### Option B: Direct File Upload (Easier - Less Secure)

1. **Copy file to Railway repo**:
   ```bash
   # If you have Railway CLI installed
   railway login
   railway link [YOUR_PROJECT_ID]
   
   # Copy credentials
   cp ~/GB\ Power\ Market\ JJ/workspace-credentials.json ./workspace-credentials.json
   
   # Add to .gitignore (if not already)
   echo "workspace-credentials.json" >> .gitignore
   
   # Deploy
   git add workspace-credentials.json
   git commit -m "Add workspace credentials"
   railway up
   ```

2. **Use in code**:
   ```python
   WORKSPACE_CREDS_PATH = 'workspace-credentials.json'
   ```

**⚠️ Security Note**: Option A is more secure (credentials encrypted in Railway), but Option B is simpler for testing.

---

## Step 1.2: Add New Endpoints to Railway (5 minutes)

### Option A: Merge Full File (Easier)

1. **Copy the complete endpoint file**:
   ```bash
   cd ~/GB\ Power\ Market\ JJ
   cat railway_google_workspace_endpoints.py
   ```

2. **Add to your Railway `main.py`**:
   - Open your Railway project code editor
   - Find `main.py` (or whatever your FastAPI file is called)
   - **Copy ALL the endpoints** from `railway_google_workspace_endpoints.py`
   - **Paste at the bottom** of your `main.py` (after existing endpoints)

### Option B: Copy Individual Endpoints (More Control)

Pick which endpoints you want:

**Essential Endpoints** (copy these):
```python
@app.get("/workspace_health")          # Health check
@app.get("/gb_energy_dashboard")       # Quick dashboard access
@app.post("/read_sheet")               # Read any sheet
@app.post("/write_sheet")              # Write to sheet
```

**Optional Endpoints** (add later if needed):
```python
@app.get("/list_worksheets")           # List all worksheets
@app.get("/search_drive")              # Search Drive
@app.get("/list_drive_files")          # List Drive files
@app.get("/read_doc")                  # Read Google Doc
@app.post("/create_doc")               # Create Google Doc
```

---

## Step 1.3: Update requirements.txt (2 minutes)

Add these dependencies to your Railway `requirements.txt`:

```bash
# Add to requirements.txt
gspread>=5.12.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=1.0.0
```

**Full example `requirements.txt`**:
```
fastapi>=0.104.0
uvicorn>=0.24.0
google-cloud-bigquery>=3.11.0
db-dtypes>=1.1.1
pandas>=2.1.0
gspread>=5.12.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=1.0.0
```

---

## Step 1.4: Deploy to Railway (1 minute)

```bash
# If using Railway CLI
railway up

# Or just git push (if connected to GitHub)
git add main.py requirements.txt
git commit -m "Add Google Workspace endpoints"
git push origin main

# Railway will auto-deploy
```

**Wait for deployment** (~2-3 minutes):
- Railway will install new dependencies
- Restart the service
- Show "✅ Deployed" when ready

---

## Step 1.5: Test Railway Endpoints (2 minutes)

### Test 1: Health Check

```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace_health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "services": {
    "sheets": "ok",
    "drive": "ok",
    "docs": "ok"
  },
  "timestamp": "2025-11-11T14:30:00Z"
}
```

### Test 2: Read Dashboard

```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/gb_energy_dashboard
```

**Expected Response**:
```json
{
  "title": "GB Energy Dashboard",
  "spreadsheet_id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
  "worksheets": [
    {"id": 0, "title": "Dashboard"},
    {"id": 1, "title": "Real-time Data"},
    ...
  ],
  "total_worksheets": 29
}
```

### Test 3: Search Drive

```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  "https://jibber-jabber-production.up.railway.app/search_drive?name=battery"
```

**Expected Response**:
```json
{
  "files": [
    {
      "id": "...",
      "name": "battery_revenue_analysis.csv",
      "mimeType": "text/csv",
      "modifiedTime": "2025-11-06T15:10:39.000Z"
    },
    ...
  ],
  "total": 5
}
```

---

## ✅ Phase 1 Complete Checklist

Before moving to Phase 2, verify:

- ✅ Railway deployment successful (no errors in logs)
- ✅ `/workspace_health` returns `{"status": "healthy"}`
- ✅ `/gb_energy_dashboard` returns 29 worksheets
- ✅ `/search_drive` returns file list
- ✅ Old endpoints still work (`/query_bigquery`, `/health`)

**If all tests pass**, proceed to Phase 2!

---

# 🎯 PHASE 2: ChatGPT Custom GPT Update (10 minutes)

**Goal**: Add Workspace capabilities to your ChatGPT Custom GPT  
**Current GPT**: Jibber Jabber Knowledge (BigQuery + docs only)  
**Adding**: Sheets, Drive, Docs access via new Railway endpoints

---

## Step 2.1: Open ChatGPT GPT Editor (1 minute)

1. **Go to your ChatGPT Custom GPT**:
   - URL: https://chat.openai.com/gpts
   - Find: "Jibber Jabber Knowledge" (or your GPT name)
   - Click: **Edit** button

2. **Click "Configure" tab** (top of editor)

---

## Step 2.2: Update Instructions (5 minutes)

### What to Do

1. **Open the new instructions file**:
   ```bash
   cd ~/GB\ Power\ Market\ JJ
   cat CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md
   ```

2. **In ChatGPT Editor**:
   - Find: **"Instructions"** text box (big box at top)
   - **Select ALL** current text (Cmd+A)
   - **Delete** (or just start typing to replace)

3. **Paste new instructions**:
   - Copy ALL content from `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`
   - Paste into Instructions box (Cmd+V)
   - Make sure it pastes completely (scroll to bottom to verify)

### What Changed

**BEFORE (old instructions)** had:
- Capability 1: Query BigQuery
- Capability 2: Read documentation (15 files)
- Capability 3: Health check

**AFTER (new instructions)** has:
- Capability 1: Query BigQuery ✅ (unchanged)
- Capability 2: Read documentation (15 files) ✅ (unchanged)
- Capability 3: Health check ✅ (unchanged)
- **Capability 4: Access Google Sheets** 🆕
- **Capability 5: Search Google Drive** 🆕
- **Capability 6: Read/Create Google Docs** 🆕

---

## Step 2.3: Add New Actions (3 minutes)

### Option A: Let ChatGPT Auto-Configure (Recommended)

The new instructions include endpoint documentation. ChatGPT will likely suggest adding the actions automatically:

1. Look for **"Actions"** section (below Instructions)
2. Click: **"Create new action"** or **"Import from URL"**
3. If it suggests importing from your Railway URL, click **"Import"**

### Option B: Manual Action Configuration

If auto-import doesn't work, add manually:

1. **Click "Actions" section**
2. **Click "Create new action"**
3. **Add these endpoints one by one**:

**Action 1: Read Sheet**
- Method: `POST`
- URL: `https://jibber-jabber-production.up.railway.app/read_sheet`
- Auth: Bearer token (use existing token)
- Body: `{"spreadsheet_id": "string", "worksheet_name": "string"}`

**Action 2: GB Energy Dashboard**
- Method: `GET`
- URL: `https://jibber-jabber-production.up.railway.app/gb_energy_dashboard`
- Auth: Bearer token

**Action 3: Search Drive**
- Method: `GET`
- URL: `https://jibber-jabber-production.up.railway.app/search_drive?name={query}`
- Auth: Bearer token

**Action 4: Workspace Health**
- Method: `GET`
- URL: `https://jibber-jabber-production.up.railway.app/workspace_health`
- Auth: Bearer token

*(Add more actions as needed - see full list in instructions)*

---

## Step 2.4: Keep Knowledge Files (0 minutes)

**DO NOTHING** with the Knowledge section!

- ✅ Keep all 15 MD files as-is
- ✅ Don't delete any files
- ✅ Don't upload new files

The Knowledge base still works for documentation queries.

---

## Step 2.5: Save and Test (1 minute)

1. **Click "Save"** (top right)
2. **Wait for save confirmation** (~5 seconds)
3. **Click "View GPT"** to test

---

## Step 2.6: Test ChatGPT Queries (5 minutes)

### Test 1: Dashboard Access

**Query**: "Show me the GB Energy Dashboard"

**Expected Response**:
```
I can see your GB Energy Dashboard has 29 worksheets:

1. Dashboard - Main summary view
2. Real-time Data - Live IRIS feeds
3. Historical Analysis - Long-term trends
4. Battery VLP - Virtual Lead Party analysis
...

Which worksheet would you like to explore?
```

### Test 2: Read Dashboard Data

**Query**: "Read the Dashboard worksheet and show me the first 10 rows"

**Expected Response**:
```
Here's the data from the Dashboard worksheet:

| Date       | Frequency | Price | ... |
|------------|-----------|-------|-----|
| 2025-11-11 | 49.98     | 45.23 | ... |
| 2025-11-10 | 50.01     | 43.87 | ... |
...
```

### Test 3: Drive Search

**Query**: "Find all CSV files containing 'battery' in Drive"

**Expected Response**:
```
I found 5 CSV files related to batteries:

1. battery_revenue_analysis_20251106.csv (Modified: Nov 6, 2025)
2. battery_bmus_complete_20251106.csv (Modified: Nov 6, 2025)
3. battery_generators_20251106.csv (Modified: Nov 6, 2025)
...

Would you like me to read any of these files?
```

### Test 4: Combined Workflow

**Query**: "Query BigQuery for today's frequency data and update the Dashboard worksheet"

**Expected Response**:
```
I've completed the update:

1. Queried BigQuery:
   - Retrieved 48 settlement periods of frequency data
   - Date range: 2025-11-11 00:00 to 23:30
   - Average frequency: 49.97 Hz

2. Updated Dashboard worksheet:
   - Cleared existing data
   - Wrote 48 rows of new data
   - Added timestamp: 2025-11-11 14:30:00

✅ Dashboard is now up to date!
```

---

## ✅ Phase 2 Complete Checklist

Verify all tests pass:

- ✅ ChatGPT can list dashboard worksheets
- ✅ ChatGPT can read worksheet data
- ✅ ChatGPT can search Drive files
- ✅ ChatGPT can query BigQuery (old capability still works)
- ✅ ChatGPT can read documentation files (old capability still works)
- ✅ Combined workflows work (BigQuery → Sheets)

---

# 🎉 BOTH PHASES COMPLETE!

## What You've Accomplished

✅ **Phase 1 (Railway)**:
- Added workspace-credentials.json to Railway
- Deployed 11 new API endpoints
- Verified all endpoints working
- Old BigQuery endpoints still working

✅ **Phase 2 (ChatGPT)**:
- Updated GPT instructions (6 capabilities instead of 3)
- Added new Actions for Workspace
- Kept Knowledge files intact
- Verified all queries working

---

## 🚀 New Capabilities

Your ChatGPT can now:

1. **Query BigQuery** (Smart Grid energy data) ✅
2. **Read Documentation** (15 MD files) ✅
3. **Access Sheets** (read/write dashboard) 🆕
4. **Search Drive** (find CSV/analysis files) 🆕
5. **Create Docs** (generate reports) 🆕
6. **Combined Workflows** (query → analyze → update) 🆕

---

## 📊 Example Workflows You Can Now Do

### Workflow 1: Real-time Dashboard Update
```
You: "Update the dashboard with latest battery VLP data"

ChatGPT:
1. Queries BigQuery for VLP data (last 7 days)
2. Calculates revenue and cycles
3. Updates Dashboard worksheet
4. Confirms: "✅ Updated with 168 rows of VLP data"
```

### Workflow 2: Weekly Report Generation
```
You: "Create a weekly battery revenue report"

ChatGPT:
1. Queries BigQuery for week's data
2. Calculates metrics (revenue, cycles, ROI)
3. Creates Google Doc with formatted analysis
4. Returns: "✅ Report created: [Google Doc link]"
```

### Workflow 3: File Analysis
```
You: "Find all battery CSV files and summarize the latest one"

ChatGPT:
1. Searches Drive for "battery" CSV files
2. Identifies most recent file
3. Reads file content
4. Summarizes: "Latest analysis shows £12,450 revenue..."
```

### Workflow 4: Dashboard vs BigQuery Comparison
```
You: "Compare dashboard frequency data with BigQuery"

ChatGPT:
1. Reads Dashboard worksheet (frequency column)
2. Queries BigQuery bmrs_freq table
3. Compares timestamps and values
4. Reports: "Dashboard is 5 minutes behind, updating..."
```

---

## 📚 What's Next?

### Immediate (Optional)
- Migrate `realtime_dashboard_updater.py` to use delegation (see `DASHBOARD_WORKSPACE_DELEGATION_GUIDE.md`)
- Test more complex ChatGPT queries
- Create custom reports

### Short-term (1 week)
- Migrate other 97 scripts to delegation
- Remove `token.pickle` OAuth files
- Update cron jobs

### Long-term (1 month)
- Add more Drive/Docs automation
- Create Apps Script functions via API
- Build custom dashboard charts

---

## 🆘 Need Help?

**Documentation**:
- `DASHBOARD_WORKSPACE_DELEGATION_GUIDE.md` - Dashboard migration guide
- `RAILWAY_DEPLOYMENT_GUIDE.md` - Full Railway setup
- `WORKSPACE_DELEGATION_COMPLETE.md` - Status summary
- `TWO_COMPANIES_CLARIFICATION.md` - BigQuery vs Workspace

**Testing**:
```bash
cd ~/GB\ Power\ Market\ JJ

# Test local Workspace access
python3 test_all_google_services.py

# Test Railway health
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace_health
```

**Troubleshooting**:
- Check Railway logs for errors
- Verify credentials file uploaded correctly
- Test endpoints individually with curl
- Check ChatGPT Actions configuration

---

## 📋 Quick Reference Card

**Railway API**: https://jibber-jabber-production.up.railway.app  
**Auth Token**: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`  
**Dashboard ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`

**Key Endpoints**:
- `/workspace_health` - Health check
- `/gb_energy_dashboard` - List worksheets
- `/read_sheet` - Read worksheet data
- `/write_sheet` - Update worksheet
- `/search_drive` - Find files
- `/query_bigquery` - Query data (existing)

**Credentials**:
- Workspace: `workspace-credentials.json` (uPower Energy)
- BigQuery: `inner-cinema-credentials.json` (Smart Grid)

---

*Deployment Guide Created: November 11, 2025*  
*Status: Ready to Deploy*  
*Estimated Time: 25 minutes*
