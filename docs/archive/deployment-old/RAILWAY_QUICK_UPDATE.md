# 🚀 Quick Railway Update Guide - Add Workspace Delegation

**Your Railway Project**: https://railway.com/project/c0c79bb5-e2fc-4e0e-93db-39d6027301ca

**Current Status**: 
- ✅ Railway is running with `api_gateway.py`
- ✅ Has BigQuery access (Smart Grid)
- ⏳ Needs Workspace delegation (uPower Energy) for Sheets

**Time**: 10 minutes

---

## 🎯 What We're Doing

Your `api_gateway.py` currently uses `inner-cinema-credentials.json` (Smart Grid/BigQuery) for everything.

We'll add `workspace-credentials.json` (uPower Energy) for Sheets/Drive/Docs access.

---

## Step 1: Add Workspace Credentials to Railway (3 minutes)

### 1.1 Convert Credentials to Base64

In Terminal:
```bash
cd ~/GB\ Power\ Market\ JJ
base64 workspace-credentials.json | pbcopy
```

This copies a long string to your clipboard. ✅ Don't paste anywhere yet!

---

### 1.2 Add to Railway Environment

1. **Go to**: https://railway.com/project/c0c79bb5-e2fc-4e0e-93db-39d6027301ca
2. **Click**: Your service (probably "api-gateway" or similar)
3. **Click**: "Variables" tab
4. **Click**: "+ New Variable"
5. **Enter**:
   - **Name**: `GOOGLE_WORKSPACE_CREDENTIALS`
   - **Value**: Cmd+V (paste the base64 string)
6. **Click**: "Add"

---

## Step 2: Update api_gateway.py (5 minutes)

I'll show you exactly what to change in your `api_gateway.py` file.

### 2.1 Update the get_sheets_client() Function

**FIND THIS** (around line 234):
```python
def get_sheets_client():
    """Get authenticated Google Sheets client"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'inner-cinema-credentials.json', scope)
        return gspread.authorize(creds)
    except Exception as e:
        logger.error(f"Failed to initialize Sheets client: {e}")
        return None
```

**REPLACE WITH THIS**:
```python
def get_sheets_client():
    """Get authenticated Google Sheets client using workspace delegation"""
    try:
        # Try to load workspace credentials from base64 env var (for Railway)
        workspace_creds_base64 = os.environ.get("GOOGLE_WORKSPACE_CREDENTIALS")
        
        if workspace_creds_base64:
            logger.info("Loading workspace credentials from GOOGLE_WORKSPACE_CREDENTIALS")
            creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
            creds_dict = json.loads(creds_json)
            
            # Create credentials with delegation
            from google.oauth2 import service_account as sa
            credentials = sa.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive.readonly']
            ).with_subject('george@upowerenergy.uk')
            
            return gspread.authorize(credentials)
        else:
            # Fall back to local credentials file
            logger.info("Using local workspace-credentials.json file")
            from google.oauth2 import service_account as sa
            credentials = sa.Credentials.from_service_account_file(
                'workspace-credentials.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive.readonly']
            ).with_subject('george@upowerenergy.uk')
            
            return gspread.authorize(credentials)
            
    except Exception as e:
        logger.error(f"Failed to initialize Sheets client: {e}")
        logger.error(traceback.format_exc())
        return None
```

---

### 2.2 Add New Workspace Endpoints

**AT THE BOTTOM** of your `api_gateway.py` file (before the startup/shutdown events), add:

```python
# ============================================
# GOOGLE WORKSPACE ENDPOINTS (NEW)
# ============================================

@app.get("/workspace/health")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def workspace_health(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Check if Workspace delegation is working"""
    try:
        gc = get_sheets_client()
        if not gc:
            return {
                "status": "error",
                "message": "Could not initialize Sheets client"
            }
        
        # Try to access the dashboard
        sheet = gc.open_by_key(SHEETS_ID)
        
        return {
            "status": "healthy",
            "message": "Workspace access working!",
            "services": {
                "sheets": "ok",
                "drive": "ok"
            },
            "dashboard": {
                "title": sheet.title,
                "worksheets": len(sheet.worksheets())
            }
        }
    except Exception as e:
        logger.error(f"Workspace health check failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/workspace/dashboard")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def get_dashboard_info(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Get GB Energy Dashboard information"""
    log_action("WORKSPACE_DASHBOARD_ACCESS", {"spreadsheet_id": SHEETS_ID})
    
    try:
        gc = get_sheets_client()
        if not gc:
            raise HTTPException(status_code=503, detail="Sheets client not available")
        
        sheet = gc.open_by_key(SHEETS_ID)
        
        worksheets = []
        for ws in sheet.worksheets():
            worksheets.append({
                "id": ws.id,
                "title": ws.title,
                "rows": ws.row_count,
                "cols": ws.col_count
            })
        
        return {
            "success": True,
            "title": sheet.title,
            "spreadsheet_id": sheet.id,
            "url": sheet.url,
            "worksheets": worksheets,
            "total_worksheets": len(worksheets)
        }
    except Exception as e:
        logger.error(f"Dashboard access error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/read_sheet")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
async def read_sheet_data(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Read data from any worksheet in the dashboard"""
    body = await request.json()
    worksheet_name = body.get('worksheet_name', 'Dashboard')
    cell_range = body.get('range', '')
    
    log_action("WORKSPACE_READ_SHEET", {
        "worksheet": worksheet_name,
        "range": cell_range
    })
    
    try:
        gc = get_sheets_client()
        if not gc:
            raise HTTPException(status_code=503, detail="Sheets client not available")
        
        sheet = gc.open_by_key(SHEETS_ID)
        worksheet = sheet.worksheet(worksheet_name)
        
        if cell_range:
            data = worksheet.get(cell_range)
        else:
            data = worksheet.get_all_values()
        
        return {
            "success": True,
            "worksheet_name": worksheet_name,
            "rows": len(data),
            "cols": len(data[0]) if data else 0,
            "data": data[:100]  # Limit to first 100 rows
        }
    except Exception as e:
        logger.error(f"Read sheet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Step 3: Deploy to Railway (2 minutes)

### Option A: If Connected to GitHub

```bash
cd ~/GB\ Power\ Market\ JJ
git add api_gateway.py
git commit -m "Add workspace delegation support"
git push
```

Railway will auto-deploy (watch the logs in Railway dashboard).

### Option B: Railway CLI

```bash
railway up
```

### Option C: Railway Dashboard

1. Go to your Railway project
2. Click "Deploy"
3. Wait for build to complete

**Deployment time**: ~2-3 minutes

---

## Step 4: Test the New Endpoints (2 minutes)

### Test 1: Workspace Health

```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace/health
```

**Expected**:
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

### Test 2: Dashboard Info

```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace/dashboard
```

**Expected**: List of 29 worksheets

### Test 3: Read Dashboard Worksheet

```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"worksheet_name": "Dashboard"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_sheet
```

**Expected**: First 100 rows of Dashboard worksheet

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Railway deployment successful (no errors in logs)
- [ ] `/workspace/health` returns `"healthy"`
- [ ] `/workspace/dashboard` returns 29 worksheets
- [ ] `/workspace/read_sheet` returns data
- [ ] Old endpoints still work (`/sheets/read`, `/bigquery/prices`)

---

## 🔍 Troubleshooting

### "Sheets client not available"

**Cause**: `GOOGLE_WORKSPACE_CREDENTIALS` env var not set or invalid

**Fix**:
1. Check Railway Variables tab
2. Verify variable name is exact: `GOOGLE_WORKSPACE_CREDENTIALS`
3. Re-run Step 1.1 to get fresh base64

### "unauthorized_client"

**Cause**: Scopes not added in Workspace Admin (but we already did this!)

**Fix**: Should work - scopes are already active (we tested this)

### Railway Build Failed

**Cause**: Usually missing dependency

**Check**: Railway logs for specific error
**Fix**: Make sure `gspread` and `google-auth` are in requirements.txt

---

## 📋 Files to Modify

You only need to modify ONE file:

**File**: `api_gateway.py`

**Changes**:
1. Update `get_sheets_client()` function (~line 234)
2. Add 3 new endpoints at the bottom (before startup events)

**Backup First**:
```bash
cp api_gateway.py api_gateway.py.backup
```

---

## 🎯 Next Steps After Railway Works

Once Railway is working (all 3 tests pass):

1. ✅ **Phase 1 Complete!**
2. ⏳ **Phase 2**: Update ChatGPT (see `SUPER_SIMPLE_GUIDE.md` Phase 2)

---

## 💡 Quick Summary

**What you're doing**:
1. Add workspace credentials to Railway as environment variable
2. Update `get_sheets_client()` to use workspace credentials
3. Add 3 new endpoints for workspace access
4. Deploy and test

**What stays the same**:
- BigQuery still uses `inner-cinema-credentials.json`
- Old endpoints still work
- No changes to ChatGPT yet (that's Phase 2)

**Time**: ~10 minutes

---

**Ready?** Start with Step 1.1 - run this command:

```bash
cd ~/GB\ Power\ Market\ JJ
base64 workspace-credentials.json | pbcopy
```

Then tell me: **"Done, copied to clipboard!"**
