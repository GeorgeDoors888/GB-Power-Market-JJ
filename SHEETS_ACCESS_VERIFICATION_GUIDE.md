# 🔍 Google Sheets Access Verification Guide

**Date:** November 5, 2025  
**Purpose:** Verify service account access to Google Sheets from multiple angles

---

## 🎯 Overview

This guide helps you verify that your service account (`jibber-jabber-knowledge@appspot.gserviceaccount.com`) has proper access to your Google Sheet for automation.

**Three verification methods:**
1. **Apps Script** (in-sheet testing)
2. **FastAPI Server** (server-side testing from UpCloud)
3. **ChatGPT Drive Connector** (optional, for in-chat browsing)

---

## Method 1: Apps Script Verification (Recommended First)

### Step 1: Open Apps Script Editor

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
2. Click **Extensions → Apps Script**
3. Copy the contents of `verify_sheets_access.gs` into the editor

### Step 2: Run Individual Tests

**Test A: List Tabs**
```javascript
// Run: debugListTabs()
// Expected: Lists all sheet tabs (Live Dashboard, Analysis, Audit_Log, etc.)
// Status: ✅ if tabs are listed, ❌ if error
```

**Test B: Read Cell A1**
```javascript
// Run: debugReadA1()
// Expected: Shows value from Live Dashboard A1
// Status: ✅ if value displayed, ❌ if "sheet not found"
```

**Test C: Write Timestamp**
```javascript
// Run: debugWriteStamp()
// Expected: Adds row to Audit_Log with timestamp
// Status: ✅ if row appears, ❌ if permission denied
```

### Step 3: Run All Tests at Once

```javascript
// Run: runAllVerificationTests()
// Expected: All three tests PASS
// Check View → Logs for detailed output
```

### Step 4: Check Permissions

```javascript
// Run: checkPermissions()
// Expected: Shows all editors/viewers
// Look for: jibber-jabber-knowledge@appspot.gserviceaccount.com in Editors list
```

### ✅ Success Criteria

- All tabs listed (Live Dashboard, Analysis, etc.)
- A1 value read successfully
- Timestamp written to Audit_Log
- Service account email appears in Editors list

### ❌ Troubleshooting

**"Live Dashboard sheet not found"**
- Check sheet name spelling (case-sensitive)
- Verify sheet exists in spreadsheet

**"Permission denied"**
- Service account not added as Editor
- Go to Share → Add: `jibber-jabber-knowledge@appspot.gserviceaccount.com` (Editor)

**"No logs appear"**
- Click View → Logs
- Wait 5-10 seconds after running function

---

## Method 2: FastAPI Server Verification

### Step 1: Add Endpoints to FastAPI

**Option A: Merge into existing FastAPI**

If you already have FastAPI running on 94.237.55.15:

```bash
# SSH to server
ssh root@94.237.55.15

# Copy the new endpoints
nano /path/to/fastapi/main.py
# Add the functions from fastapi_sheets_verify.py
```

**Option B: Test locally first**

```bash
# Install dependencies
pip install fastapi uvicorn google-api-python-client google-auth

# Run test server
python fastapi_sheets_verify.py

# Test locally
curl "http://localhost:8080/sheets/verifyAccess"
```

### Step 2: Test Endpoints

**Test 1: Health Check**
```bash
curl http://94.237.55.15:8080/health
# Expected: {"ok": true}
```

**Test 2: Read A1**
```bash
curl "http://94.237.55.15:8080/sheets/readA1?sheet_id=12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
# Expected: {"value": "some text", "status": "ok"}
```

**Test 3: List Tabs**
```bash
curl "http://94.237.55.15:8080/sheets/listTabs?sheet_id=12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
# Expected: {"tabs": ["Live Dashboard", "Analysis", ...], "count": 5}
```

**Test 4: Read Range**
```bash
curl "http://94.237.55.15:8080/sheets/readRange?sheet_id=12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8&range=Live%20Dashboard!A1:B10"
# Expected: {"values": [["row1col1", "row1col2"], ...], "rows": 10}
```

**Test 5: Comprehensive Verification**
```bash
curl "http://94.237.55.15:8080/sheets/verifyAccess"
# Expected: {"overall_status": "✅ ALL TESTS PASSED", "tests": {...}}
```

### ✅ Success Criteria

- `/health` returns `{"ok": true}`
- `/sheets/readA1` returns cell value
- `/sheets/listTabs` returns all sheet names
- `/sheets/verifyAccess` returns "✅ ALL TESTS PASSED"

### ❌ Troubleshooting

**"Service account file not found"**
```bash
# Check if file exists
ssh root@94.237.55.15 "ls -la /secrets/sa.json"

# Verify it's readable
ssh root@94.237.55.15 "cat /secrets/sa.json | jq .client_email"
```

**"403 Permission denied"**
- Service account not added as Editor to sheet
- Add: `jibber-jabber-knowledge@appspot.gserviceaccount.com`

**"404 Sheet not found"**
- Verify sheet ID: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`
- Check sheet name: `Live Dashboard` (case-sensitive)

---

## Method 3: ChatGPT Drive Connector (Optional)

### Purpose
Allows ChatGPT to read your Google Sheets directly in chat (like "list my Drive files").

### Setup Steps

1. **Open ChatGPT Settings**
   - Click your profile (bottom left)
   - Go to **Settings**

2. **Connect Google Drive**
   - Navigate to **Connectors**
   - Find **Google Drive**
   - Click **Connect** (or **Reconnect** if already connected)

3. **Authorize**
   - Select account: `george@upowerenergy.uk`
   - Click **Allow** on permissions screen
   - Scopes needed:
     - See and download all Google Drive files
     - View your Google Sheets

4. **Test Connection**
   ```
   Ask ChatGPT: "List my recent Google Drive files"
   Ask ChatGPT: "Open sheet 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
   Ask ChatGPT: "Read cell A1 from Live Dashboard in sheet 12jY0..."
   ```

### ⚠️ Important Notes

- This is **OAuth-based** (your personal account)
- **NOT required** for automations (service account handles those)
- Only needed if you want ChatGPT to read sheets in conversation
- Different from service account access

### When to Use

✅ **Use Drive Connector when:**
- You want ChatGPT to read sheets interactively
- Asking questions like "what's in my dashboard?"
- Quick data exploration in chat

❌ **Don't use Drive Connector for:**
- Automated updates (use service account)
- GitHub Actions (use service account)
- Python scripts (use service account)

---

## 🔐 Permissions & Security Checklist

### Current Setup (Recommended)

- ✅ **Service Account as Editor**
  - Email: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
  - Role: Editor (needed for read/write automation)
  - Used by: GitHub Actions, FastAPI, Python scripts

- ✅ **Your Personal Account as Owner**
  - Email: `george@upowerenergy.uk`
  - Role: Owner
  - Used by: Manual edits, ChatGPT Drive connector

### Security Recommendations

**1. Restrict General Access**

Current setting (likely):
```
General access: "Anyone with the link can edit"
```

Recommended:
```
General access: "Restricted" (only specific people)
OR
General access: "Anyone with the link can VIEW" (not edit)
```

To change:
1. Open Sheet → Click **Share** (top right)
2. Under "General access" → Change to **Restricted**
3. Keep service account + your account as explicit Editors

**2. Service Account File Security**

✅ **On UpCloud server:**
```bash
# Verify file permissions (should be 600)
ssh root@94.237.55.15 "ls -la /secrets/sa.json"
# Expected: -rw------- (only root can read)

# Verify not in public directory
ssh root@94.237.55.15 "find /var/www -name sa.json"
# Expected: (empty result)
```

✅ **In repository:**
```bash
# Verify gitignore
cat .gitignore | grep -E "(sa\.json|credentials)"
# Expected: Multiple matches (sa.json excluded)
```

**3. Audit Access Regularly**

```javascript
// Run in Apps Script: checkPermissions()
// Review list of Editors and Viewers
// Remove any unknown accounts
```

---

## 📊 Verification Matrix

| Method | What It Tests | When to Use | Auth Type |
|--------|--------------|-------------|-----------|
| **Apps Script** | In-sheet script access | First check | Bound script (inherit sheet permissions) |
| **FastAPI** | Server-side API access | Automation testing | Service account |
| **ChatGPT Drive** | Interactive chat access | In-conversation reading | OAuth (personal account) |

---

## 🚀 Quick Start (Choose Your Path)

### Path A: Just Want to Verify It Works

1. Run Apps Script: `runAllVerificationTests()`
2. Check logs: View → Logs
3. If all ✅ PASS → **Done!**

### Path B: Need Server-Side Testing

1. Add endpoints to FastAPI (from `fastapi_sheets_verify.py`)
2. Run: `curl "http://94.237.55.15:8080/sheets/verifyAccess"`
3. If returns ✅ ALL TESTS PASSED → **Done!**

### Path C: Want ChatGPT to Read Sheets

1. ChatGPT Settings → Connectors → Google Drive → Connect
2. Authorize `george@upowerenergy.uk`
3. Ask: "list my Drive files"
4. If lists files → **Done!**

---

## 🐛 Common Issues & Solutions

### Issue: "Service account not found in Editors list"

**Solution:**
```
1. Open Sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
2. Click Share (top right)
3. Add: jibber-jabber-knowledge@appspot.gserviceaccount.com
4. Role: Editor
5. Uncheck "Notify people"
6. Click Send
```

### Issue: "Apps Script can read but FastAPI can't"

**Diagnosis:** Service account file issue

**Solution:**
```bash
# Verify service account file
ssh root@94.237.55.15 "cat /secrets/sa.json | jq .client_email"

# Should show: jibber-jabber-knowledge@appspot.gserviceaccount.com
# If different email → wrong service account file
```

### Issue: "ChatGPT says 'I cannot access Drive'"

**Solution:**
```
1. Settings → Connectors → Google Drive
2. Click "Disconnect" then "Connect" again
3. Select george@upowerenergy.uk
4. Allow all permissions
5. Test: "list my Drive files"
```

---

## 📚 Related Files

- **Apps Script Test:** `verify_sheets_access.gs`
- **FastAPI Test:** `fastapi_sheets_verify.py`
- **This Guide:** `SHEETS_ACCESS_VERIFICATION_GUIDE.md`
- **API Docs:** `drive-bq-indexer/API.md`

---

## ✅ Final Checklist

- [ ] Apps Script tests all pass (runAllVerificationTests)
- [ ] Service account in Editors list (checkPermissions)
- [ ] FastAPI /sheets/verifyAccess returns ✅ ALL TESTS PASSED
- [ ] Sheet general access changed to Restricted (recommended)
- [ ] Service account file secure (not in public directory)
- [ ] ChatGPT Drive connector working (optional)

---

**Last Updated:** November 5, 2025  
**Sheet ID:** 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8  
**Service Account:** jibber-jabber-knowledge@appspot.gserviceaccount.com  
**FastAPI Server:** http://94.237.55.15:8080
