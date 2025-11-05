# 🤖 Apps Script API Remote Execution Guide

**Purpose:** Run Apps Script verification tests remotely without opening Google Sheets

---

## 🚀 Quick Start

### Step 1: Get Your Script ID

1. **Open your Google Sheet:**
   ```
   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
   ```

2. **Go to Extensions → Apps Script**

3. **Click Project Settings** (gear icon, left sidebar)

4. **Copy the Script ID** (looks like: `AKfycbx...`)

### Step 2: Enable Apps Script API

1. **Go to Google Cloud Console:**
   ```
   https://console.cloud.google.com/apis/library/script.googleapis.com?project=inner-cinema-476211-u9
   ```

2. **Click "ENABLE"**

3. **Wait 1-2 minutes** for API to activate

### Step 3: Run the Tests

```bash
# Install dependencies (if needed)
pip install google-api-python-client google-auth

# Run tests (replace with your Script ID)
python run_apps_script_tests.py AKfycbx...
```

### Expected Output:

```
🔍 Remote Apps Script Verification Tests
============================================================
Sheet ID: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
Script ID: AKfycbx...

✅ Connected to Apps Script API

Running: List all sheet tabs...
  ✅ PASS
  Result: ["Live Dashboard", "Analysis", "Raw Data", ...]

Running: Read Live Dashboard A1...
  ✅ PASS
  Result: GB Power Market Dashboard

Running: Write to Audit_Log...
  ✅ PASS

Running: Check service account permissions...
  ✅ PASS

============================================================
📊 Test Summary
============================================================
Passed: 4/4

🎉 All tests passed! Service account access is working!
```

---

## 📋 What It Does

The script remotely executes these Apps Script functions:

1. **debugListTabs()** - Lists all sheet tabs
2. **debugReadA1()** - Reads cell A1 from Live Dashboard
3. **debugWriteStamp()** - Writes timestamp to Audit_Log
4. **checkPermissions()** - Verifies service account access

---

## 🔧 Prerequisites

### 1. Apps Script Must Be Deployed

The verification script (`verify_sheets_access.gs`) must be in your Apps Script project:

**Method A: Manual (Recommended)**
1. Open Sheet → Extensions → Apps Script
2. Copy contents of `verify_sheets_access.gs`
3. Paste into Apps Script editor
4. Save (Ctrl+S / Cmd+S)

**Method B: Automated (Advanced)**
```python
# Use deploy_verification_script() function in run_apps_script_tests.py
# Requires additional permissions
```

### 2. Apps Script API Enabled

- Go to: https://console.cloud.google.com/apis/library/script.googleapis.com
- Project: `inner-cinema-476211-u9`
- Status: **ENABLED** ✅

### 3. Service Account Permissions

Your service account needs:
- **Apps Script API** access (enabled above)
- **Editor** role on the spreadsheet

---

## 🐛 Troubleshooting

### "API has not been used" or "not enabled"

**Solution:**
```
1. Go to: https://console.cloud.google.com/apis/library/script.googleapis.com?project=inner-cinema-476211-u9
2. Click ENABLE
3. Wait 1-2 minutes
4. Try again
```

### "Script not found" or "404"

**Problem:** Wrong Script ID

**Solution:**
```
1. Extensions → Apps Script
2. Project Settings → Copy Script ID
3. Verify it starts with "AKfycb" or similar
```

### "Permission denied" or "403"

**Problem:** Service account not authorized

**Solution:**
```
1. Extensions → Apps Script → Project Settings
2. Scroll to "Google Cloud Platform (GCP) Project"
3. Change project → Enter: inner-cinema-476211-u9
4. Save
```

### "Function not found"

**Problem:** Verification script not deployed

**Solution:**
```
1. Extensions → Apps Script
2. Paste code from verify_sheets_access.gs
3. Save (Ctrl+S)
4. Try again
```

---

## 🔐 Security Notes

### Service Account Scopes Required:

```python
SCOPES = [
    "https://www.googleapis.com/auth/script.projects",      # Run Apps Script
    "https://www.googleapis.com/auth/spreadsheets",         # Read/write sheets
    "https://www.googleapis.com/auth/drive"                 # Access Drive files
]
```

### OAuth vs Service Account:

| Feature | OAuth (Personal) | Service Account |
|---------|-----------------|-----------------|
| **Interactive** | Yes (ChatGPT Drive) | No |
| **Automated** | No | Yes ✅ |
| **API Access** | Limited | Full |
| **Best For** | In-chat browsing | Scripts, automations |

---

## 📊 Use Cases

### 1. CI/CD Pipeline

```yaml
# .github/workflows/verify-sheets.yml
name: Verify Sheets Access
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install google-api-python-client google-auth
      
      - name: Run verification
        env:
          SCRIPT_ID: ${{ secrets.APPS_SCRIPT_ID }}
        run: python run_apps_script_tests.py $SCRIPT_ID
```

### 2. Pre-Deployment Check

```bash
# Before deploying new code
python run_apps_script_tests.py AKfycbx...

# If all tests pass, deploy
if [ $? -eq 0 ]; then
    echo "✅ Verification passed, deploying..."
    ./deploy.sh
else
    echo "❌ Verification failed, aborting"
    exit 1
fi
```

### 3. Scheduled Health Check

```bash
# Add to crontab (run every hour)
0 * * * * cd /path/to/project && python run_apps_script_tests.py AKfycbx... >> /var/log/sheets-verify.log 2>&1
```

---

## 🆚 Comparison: Manual vs API

| Method | Speed | Automation | Logs | Exit Code |
|--------|-------|------------|------|-----------|
| **Manual** (Extensions → Apps Script → Run) | Slow | ❌ No | View → Logs | N/A |
| **API** (run_apps_script_tests.py) | Fast | ✅ Yes | Terminal | 0 or 1 |

---

## 🔗 Related Files

- **Script:** `run_apps_script_tests.py` (this tool)
- **Apps Script:** `verify_sheets_access.gs` (functions to run)
- **Guide:** `SHEETS_ACCESS_VERIFICATION_GUIDE.md` (full guide)
- **Quick Start:** `SHEETS_VERIFICATION_QUICK_START.md` (quick reference)

---

## 💡 Advanced: Deploy Script Programmatically

The `run_apps_script_tests.py` includes a `deploy_verification_script()` function that can upload the Apps Script code remotely.

**Requirements:**
- Apps Script API enabled
- Service account with `script.projects` scope
- Bound Apps Script project exists

**Usage:**
```python
from run_apps_script_tests import deploy_verification_script
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file("secrets/sa.json", scopes=SCOPES)
script_service = build("script", "v1", credentials=creds)

deploy_verification_script(script_service, "YOUR_SCRIPT_ID")
```

---

## ✅ Success Checklist

- [ ] Apps Script API enabled in GCP Console
- [ ] Script ID copied from Project Settings
- [ ] `verify_sheets_access.gs` code pasted into Apps Script editor
- [ ] Service account has Editor access to sheet
- [ ] `run_apps_script_tests.py` executes successfully
- [ ] All 4 tests pass (debugListTabs, debugReadA1, debugWriteStamp, checkPermissions)
- [ ] Exit code 0 (success)

---

## 🎯 Next Steps

Once verification passes:

1. **Add to CI/CD** (optional) - Auto-verify on every deploy
2. **Schedule Health Checks** (optional) - Hourly or daily cron job
3. **Monitor Logs** - Check for permission changes
4. **Update Documentation** - Note Script ID for team

---

**Last Updated:** November 5, 2025  
**Script:** run_apps_script_tests.py  
**Sheet ID:** 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8  
**Project:** inner-cinema-476211-u9
