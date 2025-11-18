# 🔧 Complete Google Services Setup Guide

**Date**: November 11, 2025  
**Service Account**: jibber-jabber-knowledge@appspot.gserviceaccount.com  
**Client ID**: 108583076839984080568

---

## ✅ Current Status (Test Results)

| Service | Status | Scope | Action Needed |
|---------|--------|-------|---------------|
| **Google Sheets** | ✅ **WORKING** | `https://www.googleapis.com/auth/spreadsheets` | None - already authorized |
| **Google Drive** | ❌ **BLOCKED** | `https://www.googleapis.com/auth/drive.readonly` | Add scope |
| **Google Docs** | ❓ **UNKNOWN** | `https://www.googleapis.com/auth/documents` | Add scope (to be safe) |
| **Apps Script** | ❌ **BLOCKED** | `https://www.googleapis.com/auth/script.projects` | Add scope |

---

## 🚀 How to Add Missing Scopes (5 minutes)

### Step 1: Go to Workspace Admin Console

**URL**: https://admin.google.com/ac/owl/domainwidedelegation

### Step 2: Find Your Service Account

Look for Client ID: **108583076839984080568**

If it exists:
- Click **"Edit"** next to it

If it doesn't exist:
- Click **"Add new"**
- Enter Client ID: **108583076839984080568**

### Step 3: Add Workspace Scopes (NOT BigQuery!)

Copy and paste these scopes into the "OAuth scopes" field (comma-separated):

```
https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/script.projects
```

**⚠️ CRITICAL**: Do **NOT** add `bigquery` scope here! BigQuery is a separate company (Smart Grid) with its own credentials (`inner-cinema-credentials.json`).

**Breakdown of what each scope does:**

1. **`spreadsheets`** - ✅ Already working
   - Read/write Google Sheets
   - Current status: AUTHORIZED

2. **`drive.readonly`** - ❌ Needs authorization
   - Read files from Drive
   - List folders and files
   - Used by Drive Indexer

3. **`drive`** - ⚠️ Full Drive access
   - Read/write/create files
   - Move/delete files
   - More powerful than readonly

4. **`documents`** - ❌ Needs authorization
   - Read/write Google Docs
   - Create new documents
   - Format and style docs

5. **`script.projects`** - ❌ Needs authorization
   - Manage Apps Script projects
   - Deploy and run scripts
   - Automation capabilities

**❌ NOT INCLUDED**: `bigquery` scope
   - BigQuery is separate company (Smart Grid)
   - Uses different credentials: `inner-cinema-credentials.json`
   - Service account: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`
   - **Keep BigQuery completely separate!**

### Step 4: Authorize

Click the **"Authorize"** button

### Step 5: Wait for Propagation

Changes can take **5-10 minutes** (sometimes up to 20 minutes) to take effect.

### Step 6: Test Again

After waiting, run the test script:

```bash
cd ~/GB\ Power\ Market\ JJ
python3 test_all_google_services.py
```

Should see all **✅ SUCCESS** results!

---

## 📝 Code Examples for Each Service

### Google Sheets (Already Working!)

```python
from google.oauth2 import service_account
import gspread

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('YOUR_SHEET_ID')
worksheet = spreadsheet.sheet1
data = worksheet.get_all_records()
```

### Google Drive (After Authorization)

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
).with_subject('george@upowerenergy.uk')

drive_service = build('drive', 'v3', credentials=creds)

# List files
results = drive_service.files().list(
    pageSize=10,
    fields="files(id, name, mimeType)"
).execute()

files = results.get('files', [])
for file in files:
    print(f"{file['name']} ({file['mimeType']})")
```

### Google Docs (After Authorization)

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/documents']
).with_subject('george@upowerenergy.uk')

docs_service = build('docs', 'v1', credentials=creds)

# Read a document
doc_id = 'YOUR_DOC_ID'
document = docs_service.documents().get(documentId=doc_id).execute()
print(f"Document title: {document.get('title')}")

# Get document content
content = document.get('body').get('content')
for element in content:
    if 'paragraph' in element:
        for text_run in element['paragraph'].get('elements', []):
            if 'textRun' in text_run:
                print(text_run['textRun']['content'])
```

### Apps Script (After Authorization)

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/script.projects']
).with_subject('george@upowerenergy.uk')

script_service = build('script', 'v1', credentials=creds)

# Create a new Apps Script project
request = {
    'title': 'My New Script'
}
response = script_service.projects().create(body=request).execute()
script_id = response['scriptId']
print(f"Created script: {script_id}")

# Run an Apps Script function
request = {
    'function': 'myFunction',
    'parameters': []
}
response = script_service.scripts().run(
    scriptId=script_id,
    body=request
).execute()
```

---

## 🎯 Use Cases

### What You Can Do with Full Access

#### Google Sheets ✅
- Auto-update dashboards (already doing this!)
- Read market data
- Generate reports
- Format cells and charts

#### Google Drive 📁
- **Index all files** (Drive Indexer already does this)
- Find documents by name/content
- Track file changes
- Monitor shared folders
- Create file inventory

#### Google Docs 📝
- **Generate automated reports**
- Create documentation from BigQuery data
- Mail merge with market data
- Format and style documents
- Extract text for analysis

#### Apps Script 🔧
- **Deploy custom functions**
- Automate Sheets workflows
- Create custom menus in Sheets
- Scheduled triggers
- Web apps and APIs

---

## 🔒 Security Considerations

### Scope Permissions (Most → Least Restrictive)

1. **`drive`** - Full read/write/delete access
   - Most powerful, use carefully
   - Can create, modify, delete any file

2. **`drive.readonly`** - Read-only access
   - Safer option for indexing
   - Cannot modify files

3. **`spreadsheets`** - Sheets only
   - Already using this successfully
   - Limited to Sheets files

4. **`documents`** - Docs only
   - Limited to Google Docs
   - Cannot access other file types

5. **`script.projects`** - Apps Script only
   - Manage automation scripts
   - Can't access regular files

### Recommendations

**For Drive Indexer** (current use):
- Use `drive.readonly` ✅ (safer)
- Only need read access to index files

**For Dashboard Automation**:
- Use `spreadsheets` ✅ (already working)
- Don't need full Drive access

**For Future Automation**:
- Add `documents` if generating reports
- Add `script.projects` if deploying automation
- Add `drive` only if need to create/move files

---

## 🧪 Testing Each Service

### Test Drive Access

```bash
# After adding drive scopes, test with:
python3 << 'EOF'
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
).with_subject('george@upowerenergy.uk')

drive = build('drive', 'v3', credentials=creds)
results = drive.files().list(pageSize=5, fields="files(name)").execute()
print("✅ Drive working! Files:", [f['name'] for f in results.get('files', [])])
EOF
```

### Test Docs Access

```bash
# Create a test Google Doc first, then:
python3 << 'EOF'
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/documents']
).with_subject('george@upowerenergy.uk')

docs = build('docs', 'v1', credentials=creds)
print("✅ Docs service created successfully!")
# Would need a doc ID to fully test
EOF
```

---

## 📋 Complete Scope Reference

| Scope | Purpose | Danger Level | Recommendation |
|-------|---------|--------------|----------------|
| `spreadsheets` | Read/write Sheets | 🟢 Low | ✅ Add (already working) |
| `drive.readonly` | Read Drive files | 🟢 Low | ✅ Add (safe for indexing) |
| `drive` | Full Drive access | 🟡 Medium | ⚠️ Only if needed |
| `documents` | Read/write Docs | 🟢 Low | ✅ Add (useful for reports) |
| `script.projects` | Manage Apps Script | 🟡 Medium | ✅ Add (for automation) |
| `bigquery` | Query BigQuery | 🟢 Low | ℹ️ Optional (use inner-cinema SA) |

---

## 🎯 Next Steps

1. ✅ **Add scopes in Workspace Admin** (5 minutes)
   - URL: https://admin.google.com/ac/owl/domainwidedelegation
   - Client ID: 108583076839984080568
   - Add all 6 scopes listed above

2. ⏳ **Wait 5-10 minutes** for propagation

3. ✅ **Test all services**
   ```bash
   python3 test_all_google_services.py
   ```

4. ✅ **Update your scripts** to use new capabilities
   - Drive indexing (already working, will work better)
   - Docs generation (new capability)
   - Apps Script automation (new capability)

---

## 📚 Required Python Packages

Make sure you have these installed:

```bash
pip3 install --user google-api-python-client gspread google-auth google-auth-httplib2
```

---

## 🎊 Summary

**Current State:**
- ✅ Sheets working perfectly
- ❌ Drive blocked (needs scope)
- ❌ Docs untested (needs scope)
- ❌ Apps Script blocked (needs scope)

**After Adding Scopes:**
- ✅ Full Google Workspace access
- ✅ All automation capabilities
- ✅ No more OAuth token expiration
- ✅ 24/7 reliable operation

**Time Investment:** 5 minutes to add scopes, 5-10 minutes propagation

**Next Action:** Add scopes in Workspace Admin Console now! 🚀
