# ✅ ChatGPT Google Sheets Integration - COMPLETE GUIDE

**Date**: November 23, 2025  
**Status**: ✅ Ready to Deploy to ChatGPT

---

## 🎯 What Was Accomplished

### Phase 1: Railway Credentials ✅ COMPLETE
- ✅ Workspace credentials encoded to base64
- ✅ Added `GOOGLE_WORKSPACE_CREDENTIALS` to Railway environment
- ✅ Railway automatically redeployed

### Phase 2: API Endpoints ✅ ALREADY DEPLOYED
Your `api_gateway.py` already has Google Workspace endpoints:
- ✅ `/workspace/health` - Check workspace access
- ✅ `/workspace/dashboard` - List all worksheets
- ✅ `/workspace/read_sheet` - Read sheet data

### Phase 3: ChatGPT Configuration ⏳ NEXT STEP
Update your ChatGPT Custom GPT to use the workspace endpoints.

---

## 📊 Available Railway Endpoints

### Currently Working in api_gateway.py

#### 1. `/workspace/health` (GET)
Check if workspace delegation is working.

**Request:**
```bash
curl -X GET "https://jibber-jabber-production.up.railway.app/workspace/health" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"
```

**Response:**
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
    "worksheets": 48
  }
}
```

#### 2. `/workspace/dashboard` (GET)
Get GB Energy Dashboard information with all worksheets.

**Request:**
```bash
curl -X GET "https://jibber-jabber-production.up.railway.app/workspace/dashboard" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"
```

**Response:**
```json
{
  "success": true,
  "spreadsheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
  "title": "GB Energy Dashboard",
  "url": "https://docs.google.com/spreadsheets/d/...",
  "worksheets": [
    {"id": 0, "title": "Notes", "rows": 1000, "cols": 26},
    {"id": 1, "title": "Dashboard", "rows": 1000, "cols": 26},
    {"id": 2, "title": "Chart_Prices", "rows": 1000, "cols": 26},
    ...
  ],
  "total_worksheets": 48
}
```

#### 3. `/workspace/read_sheet` (POST)
Read data from any worksheet.

**Request:**
```bash
curl -X POST "https://jibber-jabber-production.up.railway.app/workspace/read_sheet" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{
    "worksheet_name": "Dashboard",
    "range": "A1:E10"
  }'
```

**Response:**
```json
{
  "success": true,
  "worksheet_name": "Dashboard",
  "rows": 10,
  "cols": 5,
  "data": [
    ["Date", "Frequency", "Price", "Demand", "Generation"],
    ["2025-11-23", "49.98", "68.39", "42500", "43200"],
    ...
  ]
}
```

---

## 🆕 Additional Endpoints Available (from railway_google_workspace_endpoints.py)

These endpoints are ready to add to `api_gateway.py` if needed:

### Google Sheets

#### `/write_sheet` (POST)
Write data to Google Sheets.

```json
POST /write_sheet
{
  "sheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
  "worksheet": "Dashboard",
  "data": [["Header1", "Header2"], ["Value1", "Value2"]],
  "range_name": "A1"
}
```

#### `/list_worksheets` (GET)
List all worksheets with metadata (rows, cols, IDs).

```
GET /list_worksheets?sheet_id=12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
```

### Google Drive

#### `/search_drive` (GET)
Search Google Drive by name/type/date.

```
GET /search_drive?name=battery&mime_type=csv
```

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "files": [
    {
      "id": "1ABC...",
      "name": "battery_revenue_analysis.csv",
      "mimeType": "text/csv",
      "modifiedTime": "2025-11-06T15:10:39.000Z",
      "webViewLink": "https://drive.google.com/..."
    }
  ]
}
```

#### `/list_drive_files` (GET)
List Drive files with custom query.

```
GET /list_drive_files?query=name contains 'battery'&page_size=20
```

### Google Docs

#### `/read_doc` (GET)
Read Google Doc content.

```
GET /read_doc?document_id=1ABC...
```

#### `/create_doc` (POST)
Create new Google Doc.

```json
POST /create_doc
{
  "title": "Weekly Battery Revenue Report",
  "content": "# Report\n\nRevenue: £12,450..."
}
```

---

## 🔧 How to Update ChatGPT Custom GPT

### Step 1: Open ChatGPT GPT Editor (2 min)

1. Go to: https://chat.openai.com/gpts
2. Find: "Jibber Jabber Knowledge" (or your GPT name)
3. Click: **Edit** button
4. Click: **Configure** tab

### Step 2: Update Instructions (5 min)

1. **Open the instruction file:**
   ```bash
   open CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md
   ```

2. **In ChatGPT Editor:**
   - Find the **"Instructions"** text box (large box at top)
   - Select ALL current text (Cmd+A)
   - Delete

3. **Paste new instructions:**
   - Copy ALL content from `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`
   - Paste into Instructions box (Cmd+V)
   - Scroll to bottom to verify it pasted completely

**What Changed:**
- **Before**: 3 capabilities (BigQuery, Docs, Health)
- **After**: 6 capabilities (+ Sheets, Drive, Docs creation)

### Step 3: Verify Actions (2 min)

Check the **"Actions"** section below Instructions:

**Existing actions** (keep these):
- `query_bigquery` - Execute SQL queries
- `health` - API health check

**NEW actions to verify** (should auto-configure):
- `workspace_health` - Check workspace access
- `workspace_dashboard` - List all worksheets
- `workspace_read_sheet` - Read sheet data

If they don't appear automatically, add manually:

**Action 1: Workspace Health**
- Method: `GET`
- URL: `https://jibber-jabber-production.up.railway.app/workspace/health`
- Auth: Bearer `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`

**Action 2: Workspace Dashboard**
- Method: `GET`
- URL: `https://jibber-jabber-production.up.railway.app/workspace/dashboard`
- Auth: Bearer token (same)

**Action 3: Read Sheet**
- Method: `POST`
- URL: `https://jibber-jabber-production.up.railway.app/workspace/read_sheet`
- Auth: Bearer token (same)
- Body: `{"worksheet_name": "string", "range": "string"}`

### Step 4: Keep Knowledge Files (0 min)

**DO NOTHING** with the Knowledge section!
- ✅ Keep all 15 MD files as-is
- ✅ Don't delete any files
- ✅ Don't upload new files

### Step 5: Save and Test (1 min)

1. Click **"Save"** (top right)
2. Wait for save confirmation (~5 seconds)
3. Click **"View GPT"** to test

---

## 🧪 Test Queries for ChatGPT

### Test 1: Check Workspace Access

**Query**: "Can you access the GB Energy Dashboard?"

**Expected Response:**
```
Yes! I can access the GB Energy Dashboard. It has 48 worksheets including:
- Dashboard (main summary)
- BESS (battery storage)
- HH Data (half-hourly data)
- Daily_Chart_Data (chart data)
- REMIT Unavailability (outages)
...

Which worksheet would you like to explore?
```

### Test 2: List Worksheets

**Query**: "Show me all worksheets in the GB Energy Dashboard"

**Expected Response:**
```
The GB Energy Dashboard contains 48 worksheets:

1. Notes - Documentation and notes
2. Dashboard - Main summary view
3. Chart_Prices - Price chart data
4. Chart_Demand_Gen - Demand and generation charts
5. BESS - Battery storage analysis
...

Would you like to read data from any of these?
```

### Test 3: Read Dashboard Data

**Query**: "Read the Dashboard worksheet, show me the first 10 rows"

**Expected Response:**
```
Here's the data from the Dashboard worksheet:

| Date       | Frequency | Price  | Demand | Generation |
|------------|-----------|--------|--------|------------|
| 2025-11-23 | 49.98 Hz  | £68.39 | 42500  | 43200      |
| 2025-11-22 | 50.01 Hz  | £71.23 | 43200  | 44100      |
...

This shows today's market data including frequency, pricing, and demand/generation balance.
```

### Test 4: Combined Workflow

**Query**: "Query BigQuery for today's average frequency, then show me the frequency data in the Dashboard"

**Expected Response:**
```
I've analyzed today's frequency data:

**From BigQuery:**
- Average frequency: 49.98 Hz
- Max: 50.12 Hz
- Min: 49.85 Hz
- Settlement periods: 34 (so far today)

**From Dashboard worksheet:**
The Dashboard shows matching data with similar frequency ranges. The real-time data is being updated every 5 minutes via the UpCloud cron jobs.

Would you like me to compare this to historical averages?
```

---

## 📋 What ChatGPT Can Now Do

### ✅ NEW Capabilities

1. **Read Google Sheets**
   - Access any worksheet in GB Energy Dashboard
   - Read specific cell ranges
   - Get live dashboard data

2. **List Worksheets**
   - See all 48 worksheets
   - Get worksheet metadata (rows, columns, IDs)

3. **Check Workspace Health**
   - Verify delegation is working
   - Confirm access to Sheets/Drive

### ✅ Existing Capabilities (Unchanged)

1. **Query BigQuery** (391M+ rows)
2. **Read Documentation** (15 MD files)
3. **Health Checks** (API status)

### 🔄 Future Capabilities (Ready to Add)

1. **Write to Sheets** - Update dashboard data
2. **Search Drive** - Find CSV/analysis files
3. **Create Docs** - Generate automated reports

---

## 🔒 Security & Permissions

### What ChatGPT Has Access To

**✅ CAN DO:**
- Read all worksheets in GB Energy Dashboard
- Query BigQuery (read/write)
- List Drive files
- Check system health

**❌ CANNOT DO:**
- Write to Sheets (not configured yet)
- Delete files
- Access other Google Workspace users' data
- Execute Python/shell commands directly

### How It Works

```
ChatGPT
  ↓
Railway API (jibber-jabber-production.up.railway.app)
  ↓
Domain-Wide Delegation (george@upowerenergy.uk)
  ↓
Google Sheets/Drive/Docs
```

**Authentication:**
- ChatGPT → Railway: Bearer token
- Railway → Google: Service account with delegation
- Impersonates: george@upowerenergy.uk only

---

## 🐛 Troubleshooting

### Problem: ChatGPT says "Can't access sheets"

**Fix:**
1. Test Railway endpoint directly:
```bash
curl "https://jibber-jabber-production.up.railway.app/workspace/health" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"
```

2. Check Railway variables:
```bash
railway variables | grep WORKSPACE
```

3. Check Railway logs:
```bash
railway logs
```

### Problem: Railway endpoint returns error

**Possible causes:**
- Workspace credentials not properly decoded
- Domain-wide delegation not configured
- Service account email not authorized

**Fix:**
1. Verify delegation: https://admin.google.com/ac/owl/domainwidedelegation
2. Check service account email: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
3. Verify scopes:
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/drive.readonly`

### Problem: ChatGPT doesn't show new capabilities

**Fix:**
1. Verify you saved the new instructions
2. Check Actions are configured
3. Try in a new chat (context refresh)
4. Re-save the GPT configuration

---

## 📁 Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `api_gateway.py` | Railway API with workspace endpoints | ✅ Deployed |
| `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md` | Updated GPT instructions | ✅ Ready |
| `workspace-credentials.json` | Service account credentials | ✅ On Railway |
| `WORKSPACE_DELEGATION_COMPLETE.md` | Delegation setup summary | ✅ Complete |
| `RAILWAY_CHATGPT_PHASE_BY_PHASE.md` | Deployment guide | ✅ Followed |

---

## 🎯 Summary: What to Do Next

1. **Update ChatGPT Custom GPT** (10 minutes)
   - Open GPT editor
   - Replace instructions with `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`
   - Verify Actions are configured
   - Save

2. **Test in ChatGPT** (5 minutes)
   - Ask: "Can you access the GB Energy Dashboard?"
   - Ask: "Show me all worksheets"
   - Ask: "Read the Dashboard worksheet"

3. **Optionally Add More Endpoints** (later)
   - `/write_sheet` for updating dashboards
   - `/search_drive` for finding files
   - `/create_doc` for automated reports

---

**Status**: ✅ Phases 1 & 2 COMPLETE - Ready for Phase 3 (ChatGPT update)  
**Time Required**: 10 minutes to update ChatGPT  
**Documentation**: Complete  
**Next Review**: After testing in ChatGPT

*Last Updated: November 23, 2025*
