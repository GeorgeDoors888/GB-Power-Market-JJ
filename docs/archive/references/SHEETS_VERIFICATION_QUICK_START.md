# ✅ Google Sheets Access Verification - Quick Start

**Created:** November 5, 2025  
**Commit:** 83692c8

---

## 🎯 What Just Got Created

### Three Verification Tools:

1. **📝 verify_sheets_access.gs** - Apps Script tests (run in Google Sheets)
2. **🔌 fastapi_sheets_verify.py** - FastAPI endpoints (test from server)
3. **📚 SHEETS_ACCESS_VERIFICATION_GUIDE.md** - Complete instructions

---

## 🚀 Quick Start - Choose Your Method

### Method 1: Apps Script (Easiest - 2 minutes)

1. **Open your Google Sheet:**
   ```
   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
   ```

2. **Go to Extensions → Apps Script**

3. **Copy the code:**
   - Open `verify_sheets_access.gs` from repo
   - Copy all functions into Apps Script editor

4. **Run the test:**
   ```javascript
   runAllVerificationTests()
   ```

5. **Check View → Logs**
   - Expected: "✅ PASS" for all 3 tests
   - If you see ✅ PASS for all → **Service account access is working!**

---

### Method 2: FastAPI Server (For automation testing)

1. **SSH to UpCloud server:**
   ```bash
   ssh root@94.237.55.15
   ```

2. **Add endpoints to your FastAPI** (or run standalone):
   - Copy functions from `fastapi_sheets_verify.py`
   - Add to your existing FastAPI app

3. **Test from anywhere:**
   ```bash
   curl "http://94.237.55.15:8080/sheets/verifyAccess"
   ```

4. **Expected response:**
   ```json
   {
     "overall_status": "✅ ALL TESTS PASSED",
     "tests": {
       "list_tabs": {"status": "✅ PASS", "count": 5},
       "read_a1": {"status": "✅ PASS", "value": "..."}
     }
   }
   ```

---

### Method 3: ChatGPT Drive Connector (Optional - for in-chat browsing)

1. **Open ChatGPT Settings** (bottom left, click your profile)
2. **Go to Connectors → Google Drive**
3. **Click Connect (or Reconnect)**
4. **Select:** `george@upowerenergy.uk`
5. **Allow permissions**
6. **Test:** Ask ChatGPT "list my Drive files"

**Note:** This is separate from service account automations. Only needed if you want ChatGPT to read sheets interactively.

---

## ❓ Why This Matters

### The Problem:
- Different chat sessions have different OAuth states
- Service account automations ≠ ChatGPT Drive connector
- You asked why it worked in the other chat but not this one

### The Solution:
These tools verify **both** access methods independently:

| Access Method | What Uses It | Verification Tool |
|--------------|--------------|-------------------|
| **Service Account** | GitHub Actions, Python scripts, FastAPI | Apps Script / FastAPI tests |
| **OAuth (Personal)** | ChatGPT in-chat reading | Drive Connector setup |

---

## 🔐 Security Check (Important!)

### 1. Verify Service Account is Editor

**Run in Apps Script:**
```javascript
checkPermissions()
```

**Look for:**
```
✅ Service account found: jibber-jabber-knowledge@appspot.gserviceaccount.com
```

**If NOT found:**
```
1. Open Sheet → Share
2. Add: jibber-jabber-knowledge@appspot.gserviceaccount.com
3. Role: Editor
4. Click Send (uncheck "Notify people")
```

### 2. Change General Access (Recommended)

**Current (likely):**
```
General access: "Anyone with the link can edit" ⚠️ RISKY
```

**Change to:**
```
General access: "Restricted" ✅ SECURE
(Only service account + george@upowerenergy.uk can access)
```

**How:**
1. Click Share → General access dropdown
2. Select **Restricted**
3. Click Done

---

## 📊 Expected Results

### Apps Script Tests:

```
TEST 1: List Tabs
✅ PASS: Found 5 tabs

TEST 2: Read Live Dashboard A1
✅ PASS: Read value 'GB Power Market Dashboard'

TEST 3: Write to Audit_Log
✅ PASS: Write successful

✅ Service account found: jibber-jabber-knowledge@appspot.gserviceaccount.com
```

### FastAPI Tests:

```json
{
  "overall_status": "✅ ALL TESTS PASSED",
  "sheet_id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
  "tests": {
    "list_tabs": {
      "status": "✅ PASS",
      "tabs": ["Live Dashboard", "Analysis", "Raw Data", "Config", "Audit_Log"],
      "count": 5
    },
    "read_a1": {
      "status": "✅ PASS",
      "value": "GB Power Market Dashboard"
    }
  }
}
```

---

## 🐛 Troubleshooting

### "❌ FAIL: Permission denied"

**Problem:** Service account not added as Editor

**Solution:**
```
1. Sheet → Share
2. Add: jibber-jabber-knowledge@appspot.gserviceaccount.com
3. Role: Editor (NOT Viewer)
4. Send
```

### "❌ FAIL: Live Dashboard sheet not found"

**Problem:** Sheet name mismatch

**Solution:**
```javascript
// Check actual sheet names:
debugListTabs()

// Update test if name is different
```

### "Service account file not found" (FastAPI)

**Problem:** `/secrets/sa.json` missing on server

**Solution:**
```bash
ssh root@94.237.55.15 "ls -la /secrets/sa.json"
# If not found, copy from local:
scp path/to/sa.json root@94.237.55.15:/secrets/sa.json
```

---

## 📚 Files Created

| File | Purpose | Size |
|------|---------|------|
| `verify_sheets_access.gs` | Apps Script tests | 5 functions |
| `fastapi_sheets_verify.py` | FastAPI endpoints | 6 endpoints |
| `SHEETS_ACCESS_VERIFICATION_GUIDE.md` | Complete guide | 500+ lines |

**GitHub:** https://github.com/GeorgeDoors888/overarch-jibber-jabber/tree/main

---

## ✅ Next Steps

1. **Run Apps Script test** (2 minutes)
   - If all ✅ → **Done! Service account working**
   - If ❌ → Add service account as Editor

2. **Optional: Test FastAPI** (if you need server-side verification)
   - Add endpoints to your FastAPI
   - Test with curl

3. **Optional: Connect ChatGPT Drive** (if you want in-chat reading)
   - Settings → Connectors → Google Drive → Connect

---

## 🎉 Success Looks Like

- ✅ Apps Script: All 3 tests PASS
- ✅ Service account in Editors list
- ✅ FastAPI: `/sheets/verifyAccess` returns ALL TESTS PASSED
- ✅ Sheet general access set to Restricted (security)
- ✅ ChatGPT Drive connected (optional)

---

**Your service account automations (GitHub Actions, Python scripts) work independently of ChatGPT's OAuth state. The Apps Script test is the quickest way to verify everything is set up correctly!**

---

**Last Updated:** November 5, 2025  
**Commit:** 83692c8  
**Sheet ID:** 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA  
**Service Account:** jibber-jabber-knowledge@appspot.gserviceaccount.com
