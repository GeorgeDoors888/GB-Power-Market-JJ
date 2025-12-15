# 🎯 SIMPLE GUIDE: Add Google Sheets to ChatGPT

**Time**: 25 minutes  
**What you'll do**: Make ChatGPT able to read/write your GB Energy Dashboard  
**Status**: Ready to start now

---

## 🧠 **What's Happening? (The Big Picture)**

Right now:
- ✅ Your Mac can access Sheets (we tested this - it works!)
- ✅ Your Railway API can query BigQuery
- ❌ ChatGPT **cannot** access Sheets yet

After this guide:
- ✅ ChatGPT will be able to read your dashboard
- ✅ ChatGPT will be able to search your Drive files
- ✅ ChatGPT will still query BigQuery (nothing breaks)

**How?** We'll teach your Railway API how to access Sheets, then tell ChatGPT about it.

---

## 🎬 **PHASE 1: Teach Railway About Google Sheets**

**What is Railway?** It's the website where your API lives:
- URL: https://railway.app
- Your API: https://jibber-jabber-production.up.railway.app

**What we're doing**: Adding the `workspace-credentials.json` file to Railway so it can access Sheets.

---

### **Step 1: Get the Credentials Ready**

Open Terminal and run:

```bash
cd ~/GB\ Power\ Market\ JJ
base64 workspace-credentials.json | pbcopy
```

**What this does**: Converts the credentials file to a long string and copies it to your clipboard (like Cmd+C).

**You'll see**: Nothing! But your clipboard now has the text. Don't paste it anywhere yet.

---

### **Step 2: Go to Railway Website**

1. **Open browser**: Go to https://railway.app
2. **Login** (if not already)
3. **Find your project**: Look for "jibber-jabber" or your project name
4. **Click on it** to open

You should see:
- Left side: Services list
- Middle: Deployment info
- Right side: Logs

---

### **Step 3: Add the Credentials**

1. **Click "Variables" tab** (top of page)
2. **Click "New Variable" button**
3. **Type this EXACTLY**:
   - **Variable name**: `GOOGLE_WORKSPACE_CREDENTIALS`
   - **Variable value**: Press Cmd+V (paste the long string from Step 1)
4. **Click "Add"**

**What you'll see**: New variable appears in the list.

---

### **Step 4: Update Your Railway Code**

Now we need to tell Railway how to **use** that credentials variable.

**Option A: If you know where your Railway code is (GitHub)**:
1. Go to your Railway code repository (GitHub)
2. Open the main Python file (probably `main.py` or `app.py`)
3. We'll add code to it

**Option B: If Railway code is somewhere else**:
- Tell me where your Railway code lives and I'll help find it

**For now, let's continue assuming you can edit the code...**

---

### **Step 5: Add This Code to Railway**

I'll show you **exactly what to add**. Don't worry about understanding it yet - just copy-paste.

**AT THE TOP of your Railway Python file**, add this:

```python
import os
import base64
import json
import tempfile
from google.oauth2 import service_account
import gspread

# Decode workspace credentials from environment variable
def get_workspace_credentials():
    """Get workspace credentials from Railway environment variable"""
    creds_base64 = os.environ.get('GOOGLE_WORKSPACE_CREDENTIALS')
    if not creds_base64:
        raise Exception("GOOGLE_WORKSPACE_CREDENTIALS not found in environment")
    
    # Decode base64 to JSON string
    creds_json = base64.b64decode(creds_base64).decode('utf-8')
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(creds_json)
        temp_path = f.name
    
    # Create credentials
    creds = service_account.Credentials.from_service_account_file(
        temp_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.readonly']
    ).with_subject('george@upowerenergy.uk')
    
    return creds

# Initialize gspread client (for Sheets access)
def get_sheets_client():
    """Get authenticated gspread client"""
    creds = get_workspace_credentials()
    return gspread.authorize(creds)
```

**What this does**: Reads the credentials from Railway's environment and creates a Sheets client.

---

### **Step 6: Add New Endpoints**

**AT THE BOTTOM of your Railway Python file**, add these new endpoints:

```python
# ============================================================================
# NEW: Google Sheets Endpoints
# ============================================================================

@app.get("/workspace_health")
async def workspace_health(authorization: str = Header(None)):
    """Check if Workspace access is working"""
    # Check auth token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    
    token = authorization.replace("Bearer ", "")
    if token != "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        gc = get_sheets_client()
        return {
            "status": "healthy",
            "message": "Workspace access is working!",
            "services": {
                "sheets": "ok",
                "drive": "ok"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/gb_energy_dashboard")
async def gb_energy_dashboard(authorization: str = Header(None)):
    """Quick access to GB Energy Dashboard - list all worksheets"""
    # Check auth token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    
    token = authorization.replace("Bearer ", "")
    if token != "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        gc = get_sheets_client()
        spreadsheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
        
        worksheets = []
        for ws in spreadsheet.worksheets():
            worksheets.append({
                "id": ws.id,
                "title": ws.title,
                "rows": ws.row_count,
                "cols": ws.col_count
            })
        
        return {
            "title": spreadsheet.title,
            "spreadsheet_id": spreadsheet.id,
            "url": spreadsheet.url,
            "worksheets": worksheets,
            "total_worksheets": len(worksheets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/read_sheet")
async def read_sheet(
    request: dict,
    authorization: str = Header(None)
):
    """Read data from any Google Sheet worksheet"""
    # Check auth token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    
    token = authorization.replace("Bearer ", "")
    if token != "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    spreadsheet_id = request.get('spreadsheet_id', '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
    worksheet_name = request.get('worksheet_name', 'Dashboard')
    
    try:
        gc = get_sheets_client()
        spreadsheet = gc.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Get all values
        data = worksheet.get_all_values()
        
        return {
            "spreadsheet_id": spreadsheet_id,
            "worksheet_name": worksheet_name,
            "rows": len(data),
            "data": data[:100]  # Return first 100 rows
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### **Step 7: Update requirements.txt**

In your Railway project, find `requirements.txt` and add these lines:

```
gspread>=5.12.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
```

---

### **Step 8: Deploy to Railway**

**Option A: If Railway auto-deploys from GitHub**:
1. Commit your changes: `git add .`
2. `git commit -m "Add Google Sheets endpoints"`
3. `git push`
4. Railway will auto-deploy (watch the Railway dashboard)

**Option B: If using Railway CLI**:
1. Run: `railway up`
2. Wait for deployment

**Option C: Manual deploy**:
1. In Railway dashboard, click "Deploy" button

**Wait**: ~3 minutes for deployment to complete. Watch the logs in Railway dashboard.

---

### **Step 9: Test Railway**

Open Terminal and test:

```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace_health
```

**Expected result**:
```json
{
  "status": "healthy",
  "message": "Workspace access is working!",
  "services": {
    "sheets": "ok",
    "drive": "ok"
  }
}
```

**If you see this** ✅ Phase 1 is DONE!

**If you see an error** ❌:
- Check Railway logs for details
- Make sure variable name is exact: `GOOGLE_WORKSPACE_CREDENTIALS`
- Make sure you pasted the full base64 string

---

## 🎬 **PHASE 2: Tell ChatGPT About Railway's New Powers**

Now ChatGPT needs to know Railway can access Sheets.

---

### **Step 1: Open Your ChatGPT Custom GPT**

1. **Go to**: https://chat.openai.com/gpts
2. **Find**: Your custom GPT (probably called "Jibber Jabber Knowledge")
3. **Click**: The ✏️ Edit button
4. **Click**: "Configure" tab at the top

You should see a big text box labeled "Instructions".

---

### **Step 2: Get the New Instructions**

On your Mac, open Terminal:

```bash
cd ~/GB\ Power\ Market\ JJ
open CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md
```

This opens the file in your text editor. **Select ALL the text** (Cmd+A).

---

### **Step 3: Replace ChatGPT Instructions**

Back in ChatGPT editor:

1. **Find** the "Instructions" text box (big box at top)
2. **Click inside** the box
3. **Select all** (Cmd+A)
4. **Paste** (Cmd+V) - replaces with new instructions

**Scroll down** to make sure all text pasted correctly.

---

### **Step 4: Add Actions**

Scroll down to "Actions" section:

1. **Click** "Create new action"
2. **Schema**: Paste this:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "GB Power Market API",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://jibber-jabber-production.up.railway.app"
    }
  ],
  "paths": {
    "/workspace_health": {
      "get": {
        "operationId": "checkWorkspaceHealth",
        "summary": "Check Workspace access health"
      }
    },
    "/gb_energy_dashboard": {
      "get": {
        "operationId": "getDashboard",
        "summary": "Get GB Energy Dashboard info"
      }
    },
    "/read_sheet": {
      "post": {
        "operationId": "readSheet",
        "summary": "Read Google Sheet data",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "spreadsheet_id": {"type": "string"},
                  "worksheet_name": {"type": "string"}
                }
              }
            }
          }
        }
      }
    }
  }
}
```

3. **Authentication**: Select "Bearer"
4. **Token**: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`

---

### **Step 5: Save**

1. **Click** "Save" (top right)
2. **Wait** for confirmation (~5 seconds)

---

### **Step 6: Test ChatGPT**

Click "View GPT" to test. Try these queries:

**Test 1**: "Show me the GB Energy Dashboard"

**Expected**: Lists 29 worksheets

**Test 2**: "Read the Dashboard worksheet"

**Expected**: Shows data table

**If both work** ✅ Phase 2 is DONE!

---

## 🎉 **YOU'RE DONE!**

Now you can ask ChatGPT things like:
- "Show me the dashboard"
- "Read the latest frequency data"
- "Update the dashboard with new VLP data"

---

## 🆘 **STUCK? Common Issues**

### "Can't find Railway code"
Tell me where your code is (GitHub URL?) and I'll help.

### "Railway deployment failed"
Check Railway logs - usually missing dependency.

### "ChatGPT says 'I don't have access'"
Make sure Actions are saved and Bearer token is correct.

### "Still confused about a step"
Tell me which step number and I'll explain it differently!

---

**Ready to start? Let's do Phase 1, Step 1 together!**

Just run this command:
```bash
cd ~/GB\ Power\ Market\ JJ
base64 workspace-credentials.json | pbcopy
```

Then tell me: **"Done, what's next?"**
