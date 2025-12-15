# Enable Apps Script API - Quick Guide

## Problem
The service account `jibber-jabber-knowledge@appspot.gserviceaccount.com` needs Apps Script API access to deploy and run verification scripts remotely.

## Solution (2 minutes)

### Step 1: Enable Apps Script API
1. Visit: https://console.cloud.google.com/apis/library/script.googleapis.com?project=jibber-jabber-knowledge
2. Click **"ENABLE"**
3. Wait 30 seconds for activation

### Step 2: Grant Service Account Permission
The service account also needs to be added as an editor to the Apps Script project:

1. Open your sheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. Go to **Extensions → Apps Script**
3. Click **Project Settings** (gear icon ⚙️)
4. Scroll to **"Google Cloud Project (GCP) Project number"**
5. Click **"Change project"**
6. Enter: `jibber-jabber-knowledge`
7. Click **"Set project"**

### Step 3: Run Automated Verification
Once the API is enabled and project linked:

```bash
python3 deploy_and_run_verification.py 10SiYn4qQ5rSRZlG9EzbWy4Ot6weV_jZr7SfBm_O0qsElewf9FzGeK98z
```

This will:
- ✅ Deploy the verification functions
- ✅ Run all 4 tests automatically
- ✅ Show results in terminal

---

## Alternative: Manual Method (No API needed)

If you prefer not to enable the API:

1. Open your sheet → **Extensions → Apps Script**
2. Copy code from `verify_sheets_access.gs`
3. Paste into Apps Script editor
4. Save (Ctrl+S / Cmd+S)
5. Run function: **`runAllVerificationTests`**
6. View logs: **View → Logs** (Ctrl+Enter)

---

## What This Verifies

The tests check:
1. ✅ Can list all sheet tabs
2. ✅ Can read cell data (A1)
3. ✅ Can write data (timestamp)
4. ✅ Service account has proper permissions

---

## After Verification

Once tests pass, you'll know the service account can:
- Read/write Google Sheets
- Support automation scripts
- Work with ChatGPT Drive connector

---

**Choose your method:**
- **Automated (via API):** Follow Steps 1-3 above
- **Manual (2 minutes):** Use Alternative method

Both work equally well! 🎯
