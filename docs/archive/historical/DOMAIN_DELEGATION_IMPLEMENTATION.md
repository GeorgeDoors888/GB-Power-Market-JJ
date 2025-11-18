# 🚀 Domain-Wide Delegation Implementation Guide

**Date**: November 11, 2025  
**Project**: GB Power Market JJ  
**Purpose**: Enable automatic access to all Google Sheets, Docs, and Apps Script projects

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Why Enable Delegation](#why-enable-delegation)
3. [Setup Instructions](#setup-instructions)
4. [How to Update Your Scripts](#how-to-update-your-scripts)
5. [ChatGPT Integration](#chatgpt-integration)
6. [Testing](#testing)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

### **What Is Domain-Wide Delegation?**

Domain-wide delegation allows a service account to **impersonate a user** and access all resources that user can access, without manual sharing.

### **Current Setup (Standard Auth):**
```
❌ Must manually share each Sheet with service account
❌ New dashboards require manual sharing
❌ Limited to explicitly shared files
✅ More secure, tighter control
```

### **With Domain-Wide Delegation:**
```
✅ Access ALL Sheets/Docs george@ can access
✅ No manual sharing needed
✅ Automatically discover new files
✅ Works with Apps Script APIs
⚠️ More powerful (requires careful use)
```

---

## 🌟 Why Enable Delegation

### **Benefits for Your Project:**

1. **Automatic Dashboard Access**
   - Create new Sheets → immediately accessible
   - No manual sharing step
   - ChatGPT can find dashboards automatically

2. **Apps Script Integration**
   - Read/modify Apps Script projects
   - Automate script deployments
   - Monitor script executions

3. **Document Discovery**
   - Find all energy market documents
   - Index Docs for search
   - Automated reporting

4. **Simplified Workflow**
   - One-time setup
   - All future files automatically accessible
   - Less maintenance

---

## 🔧 Setup Instructions

### **Prerequisites:**
- ✅ Google Workspace account (upowerenergy.uk)
- ✅ Workspace Admin access
- ✅ Service account: `all-jibber@inner-cinema-476211-u9`

---

### **STEP 1: Get Your Client ID (1 minute)**

Run the setup script:
```bash
cd ~/GB\ Power\ Market\ JJ
python3 setup_delegation.py
```

**Output will show:**
```
✅ Credentials file found
   Email: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com
   Client ID: 123456789012345678901  ← SAVE THIS!
```

**Save the Client ID** - you'll need it in Step 3!

---

### **STEP 2: Enable in GCP Console (2 minutes)**

1. **Go to**: https://console.cloud.google.com/iam-admin/serviceaccounts?project=inner-cinema-476211-u9

2. **Click on**: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`

3. **Find** "Domain-wide delegation" section (may need to expand "Show Advanced Settings")

4. **Check the box**: "Enable Google Workspace Domain-wide Delegation"

5. **Click** "Save"

**Screenshot reference**: You should see something like:
```
☑ Enable Google Workspace Domain-wide Delegation
  Domain-wide delegation enabled
  Client ID: 123456789012345678901
```

---

### **STEP 3: Authorize in Google Workspace Admin (3 minutes)**

1. **Go to**: https://admin.google.com/ac/owl/domainwidedelegation

2. **Click** "Add new" (or "Edit" if already exists)

3. **Enter Client ID**:
   ```
   123456789012345678901  ← From Step 1
   ```

4. **OAuth Scopes** (copy-paste ALL):
   ```
   https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/script.projects,https://www.googleapis.com/auth/bigquery
   ```

5. **Click** "Authorize"

**What each scope does:**
- `spreadsheets` - Read/write Google Sheets
- `documents` - Read/write Google Docs
- `drive.readonly` - Read Drive files (discover/list)
- `script.projects` - Access Apps Script
- `bigquery` - Access BigQuery (already working)

---

### **STEP 4: Configure Environment (30 seconds)**

Add to your environment:

**Option A: Permanent (recommended)**
```bash
echo 'export GOOGLE_WORKSPACE_ADMIN_EMAIL="george@upowerenergy.uk"' >> ~/.zshrc
source ~/.zshrc
```

**Option B: Temporary (current session only)**
```bash
export GOOGLE_WORKSPACE_ADMIN_EMAIL="george@upowerenergy.uk"
```

**Option C: In Python scripts**
```python
os.environ['GOOGLE_WORKSPACE_ADMIN_EMAIL'] = 'george@upowerenergy.uk'
```

---

### **STEP 5: Wait and Verify (5-10 minutes)**

Changes can take 5-20 minutes to propagate.

**Verify setup:**
```bash
cd ~/GB\ Power\ Market\ JJ
python3 setup_delegation.py
```

**Success looks like:**
```
✅ Delegated Sheets working: 15 sheets accessible
✅ Domain-wide delegation is WORKING!
```

**If not working yet:**
```
⚠️ Domain-wide delegation NOT YET configured
   Wait 5-10 minutes for propagation
```

---

## 🔄 How to Update Your Scripts

### **Method 1: Use the Utility Module (Easiest)**

Replace your existing auth code with the utility:

**Before:**
```python
from google.oauth2 import service_account
import gspread

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

gc = gspread.authorize(creds)
bq_client = bigquery.Client(project='inner-cinema-476211-u9', credentials=creds)
```

**After:**
```python
from google_auth_utils import get_sheets_client, get_bigquery_client

# Automatically uses delegation if GOOGLE_WORKSPACE_ADMIN_EMAIL is set
gc = get_sheets_client()
bq_client = get_bigquery_client()
```

**That's it!** The utility automatically:
- ✅ Detects if delegation is configured
- ✅ Uses delegation when available
- ✅ Falls back to standard auth if not
- ✅ Prints status messages

---

### **Method 2: Manual Update (More Control)**

If you want more control, update manually:

**Add at top of script:**
```python
import os

# Check if delegation is enabled
ADMIN_EMAIL = os.environ.get('GOOGLE_WORKSPACE_ADMIN_EMAIL')
USE_DELEGATION = ADMIN_EMAIL is not None
```

**Update credential creation:**
```python
from google.oauth2 import service_account

# Load base credentials
creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

# Apply delegation if configured
if USE_DELEGATION and ADMIN_EMAIL:
    print(f"🔐 Using domain-wide delegation (impersonating: {ADMIN_EMAIL})")
    creds = creds.with_subject(ADMIN_EMAIL)
else:
    print(f"🔒 Using standard authentication")

# Use credentials normally
gc = gspread.authorize(creds)
```

---

### **Example: Updated realtime_dashboard_updater.py**

```python
#!/usr/bin/env python3
"""Real-Time Dashboard Updater with Domain-Wide Delegation Support"""

import os
from google_auth_utils import get_sheets_client, get_bigquery_client

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
PROJECT_ID = 'inner-cinema-476211-u9'

def update_dashboard():
    # Get clients (automatically uses delegation if configured)
    gc = get_sheets_client()
    bq_client = get_bigquery_client()
    
    # Open spreadsheet
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # ... rest of your code ...
```

---

## 🤖 ChatGPT Integration

### **How Domain-Wide Delegation Helps ChatGPT:**

**Current Limitation:**
- ChatGPT can only access Sheets you explicitly share
- Must manually share new dashboards
- Limited discovery

**With Delegation:**
- ✅ ChatGPT automatically sees all your Sheets
- ✅ Can find dashboards by name
- ✅ Access new files immediately
- ✅ No manual sharing needed

---

### **ChatGPT Setup (After Delegation Enabled):**

1. **Update ChatGPT Instructions**:
   ```
   You can now access all Google Sheets in the upowerenergy.uk domain
   that george@upowerenergy.uk can access. No manual sharing needed.
   
   To query a sheet:
   1. Use: gc = get_sheets_client()
   2. Find sheets: gc.openall() or gc.open('Dashboard Name')
   3. Read/write normally
   ```

2. **Update Vercel Proxy** (if using):
   ```bash
   cd ~/GB\ Power\ Market\ JJ/vercel-proxy
   
   # Add to .env:
   echo 'GOOGLE_WORKSPACE_ADMIN_EMAIL=george@upowerenergy.uk' >> .env
   
   # Deploy:
   vercel --prod
   ```

3. **Test ChatGPT Access**:
   ```
   Ask ChatGPT:
   "List all Google Sheets I can access"
   "Open the Enhanced BI Analysis dashboard"
   "Create a new dashboard called 'Battery VLP Summary'"
   ```

---

### **Example ChatGPT Queries:**

**Before (with explicit sharing):**
```
User: "Update my dashboard"
ChatGPT: "Which dashboard? Please provide the Sheet ID or share it with the service account"
```

**After (with delegation):**
```
User: "Update my dashboard"  
ChatGPT: "Found 3 dashboards:
  1. Enhanced BI Analysis
  2. Battery VLP Tracking  
  3. GSP Wind Analysis
  Which one would you like to update?"
```

**Discovery:**
```
User: "What dashboards do I have?"
ChatGPT: "Scanning your Google Drive...
  Found 8 Sheets:
  - Enhanced BI Analysis (12jY0d...)
  - Battery Revenue Tracking (15aB3...)
  - GSP Wind by Region (18xC9...)
  ..."
```

---

## 🧪 Testing

### **Test 1: Check Setup**
```bash
cd ~/GB\ Power\ Market\ JJ
python3 setup_delegation.py
```

**Expected output:**
```
✅ Credentials file found
✅ Standard auth working
✅ Delegated Sheets working: 15 sheets accessible
🎉 DOMAIN-WIDE DELEGATION IS WORKING!
```

---

### **Test 2: Test Utility Module**
```bash
python3 google_auth_utils.py
```

**Expected output:**
```
Domain-Wide Delegation:
  Enabled: ✅ YES
  Admin Email: george@upowerenergy.uk

✅ Credentials loaded successfully
✅ BigQuery working: 2 datasets accessible
✅ Sheets working: 15 sheets accessible

🎉 Domain-wide delegation is ACTIVE!
```

---

### **Test 3: Test Script Access**
```python
# test_delegation_access.py
from google_auth_utils import get_sheets_client

gc = get_sheets_client()

# List all accessible sheets
sheets = gc.openall()
print(f"📊 Accessible sheets: {len(sheets)}")

for sheet in sheets:
    print(f"  - {sheet.title} ({sheet.id})")

# Try to open a specific sheet (without manual sharing)
try:
    dashboard = gc.open('Enhanced BI Analysis')
    print(f"✅ Successfully opened: {dashboard.title}")
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 🔒 Security Considerations

### **What Changes:**

**Standard Auth (Before):**
- ✅ Only accesses explicitly shared files
- ✅ Clear audit trail (see what's shared)
- ✅ Easy to revoke (unshare file)
- ✅ Least privilege

**Domain Delegation (After):**
- ⚠️ Accesses ALL files george@ can access
- ⚠️ Powerful - use carefully
- ⚠️ Requires Workspace admin approval
- ✅ Easier automation
- ✅ No manual sharing needed

---

### **Best Practices:**

1. **Keep credentials secure**:
   ```bash
   chmod 600 inner-cinema-credentials.json
   ```

2. **Use read-only scopes where possible**:
   ```python
   # For read-only access:
   scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
   ```

3. **Log all operations**:
   ```python
   logging.info(f"Accessing sheet: {sheet_id} as {ADMIN_EMAIL}")
   ```

4. **Disable delegation when not needed**:
   ```bash
   unset GOOGLE_WORKSPACE_ADMIN_EMAIL
   ```

5. **Monitor service account activity**:
   - Check Google Workspace audit logs
   - Review BigQuery job history
   - Monitor Sheet access patterns

---

### **Audit Logging:**

Add to your scripts:
```python
import logging

# Log delegation usage
if USE_DELEGATION:
    logging.info(f"🔓 Using delegation: {ADMIN_EMAIL}")
    logging.info(f"   Accessing: {spreadsheet.title}")
    logging.info(f"   Operation: {operation_type}")
    logging.info(f"   Timestamp: {datetime.now()}")
```

---

## 🐛 Troubleshooting

### **Problem: "unauthorized_client"**

**Cause**: Delegation not authorized in Workspace Admin

**Solution**:
1. Go to: https://admin.google.com/ac/owl/domainwidedelegation
2. Verify Client ID matches your service account
3. Verify OAuth scopes are correct
4. Wait 10-20 minutes for propagation

---

### **Problem: "403 Forbidden"**

**Cause**: Service account doesn't have permission to impersonate user

**Solution**:
1. Verify you enabled delegation in GCP Console
2. Check that GOOGLE_WORKSPACE_ADMIN_EMAIL is set correctly
3. Ensure the email is a valid Workspace user

---

### **Problem: "Delegation works but can't see files"**

**Cause**: The admin user doesn't have access to those files

**Solution**:
- Delegation gives service account same access as admin user
- If george@ can't access a file, delegation won't help
- Share files with george@ or use a different admin user

---

### **Problem: "Works locally but not in cron"**

**Cause**: Environment variable not set in cron context

**Solution**:
```bash
# In crontab:
*/5 * * * * export GOOGLE_WORKSPACE_ADMIN_EMAIL="george@upowerenergy.uk" && cd ~/GB\ Power\ Market\ JJ && python3 realtime_dashboard_updater.py
```

Or add to script:
```python
os.environ['GOOGLE_WORKSPACE_ADMIN_EMAIL'] = 'george@upowerenergy.uk'
```

---

### **Problem: "Still showing as standard auth"**

**Check environment variable:**
```bash
echo $GOOGLE_WORKSPACE_ADMIN_EMAIL
# Should output: george@upowerenergy.uk
```

**Check in Python:**
```python
import os
print(os.environ.get('GOOGLE_WORKSPACE_ADMIN_EMAIL'))
```

---

## 📚 Files Created

### **New Files:**
1. **`setup_delegation.py`** - Setup and verification script
2. **`google_auth_utils.py`** - Authentication utility module
3. **`DOMAIN_DELEGATION_IMPLEMENTATION.md`** - This documentation
4. **`test_delegation_access.py`** - Test script (to be created)

### **Documentation Updated:**
1. `GOOGLE_AUTH_FILES_REFERENCE.md` - Added delegation info
2. `GOOGLE_AUTH_QUICK_START.md` - Added delegation option
3. `DOMAIN_DELEGATION_CORRECTION.md` - Comparison with Drive Indexer

---

## 🎯 Summary

### **To Enable Delegation:**
```bash
# 1. Run setup script
python3 setup_delegation.py

# 2. Follow instructions:
#    - Enable in GCP Console
#    - Authorize in Workspace Admin
#    - Set environment variable

# 3. Wait 5-10 minutes

# 4. Verify
python3 setup_delegation.py
```

### **To Update Scripts:**
```python
# Replace existing auth with:
from google_auth_utils import get_sheets_client, get_bigquery_client

gc = get_sheets_client()
bq = get_bigquery_client()
```

### **To Use with ChatGPT:**
- Update Vercel proxy with GOOGLE_WORKSPACE_ADMIN_EMAIL
- ChatGPT automatically gets access to all sheets
- No manual sharing needed

---

## ✅ Next Steps

1. **Run setup script**: `python3 setup_delegation.py`
2. **Follow setup instructions** (Steps 1-5 above)
3. **Update 1-2 scripts as test** (use `google_auth_utils.py`)
4. **Verify working**: Check logs, test manually
5. **Update remaining scripts gradually**
6. **Update ChatGPT integration** (if using)

---

**Questions?** See `GOOGLE_AUTH_FILES_REFERENCE.md` or run:
```bash
python3 google_auth_utils.py --help
python3 setup_delegation.py
```

---

*Created: November 11, 2025*  
*For: GB Power Market JJ Project*  
*Status: Ready for implementation*
