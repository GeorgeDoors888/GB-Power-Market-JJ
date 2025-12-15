# 🎯 Complete Action Plan - Google Services + Delegation

**Date**: November 11, 2025  
**Status**: ✅ Sheets Working | ⏳ Drive/Docs/Apps Script Need Authorization

---

## 📊 Quick Status

| Service | Current Status | What It Enables |
|---------|----------------|-----------------|
| **Google Sheets** | ✅ **WORKING NOW** | Dashboard updates (98 scripts ready) |
| **Google Drive** | ❌ Blocked | File indexing, Drive Indexer enhancement |
| **Google Docs** | ❌ Blocked | Automated report generation |
| **Apps Script** | ❌ Blocked | Custom automation, scheduled tasks |

---

## 🚀 Complete 3-Step Plan (20 minutes total)

### ✅ STEP 1: Add All Google Service Scopes (5 minutes)

**Where**: https://admin.google.com/ac/owl/domainwidedelegation  
**Client ID**: 108583076839984080568

**Scopes to Add** (copy-paste this entire line):
```
https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/script.projects,https://www.googleapis.com/auth/bigquery
```

**Instructions**:
1. Find Client ID 108583076839984080568
2. Click "Edit" or "Add new"
3. Paste all scopes above
4. Click "Authorize"
5. Wait 5-10 minutes for propagation

---

### ✅ STEP 2: Test All Services (2 minutes)

```bash
cd ~/GB\ Power\ Market\ JJ
python3 test_all_google_services.py
```

**Expected Result After Scopes Added**:
```
✅ SUCCESS - Can access Sheets!
✅ SUCCESS - Can access Drive!
✅ SUCCESS - Can access Docs!
✅ SUCCESS - Can access Apps Script!
```

---

### ✅ STEP 3: Migrate Dashboard Script (5 minutes)

```bash
# Backup and update main dashboard script
python3 migrate_dashboard_to_delegation.py

# Test it works
python3 realtime_dashboard_updater.py

# Monitor logs
tail -f logs/dashboard_updater.log
```

**Expected Log Output**:
```
✅ Using workspace delegation (permanent auth)
✅ Connected successfully
📊 Wrote 1,234 rows to Dashboard
```

---

## 📚 What Each Service Does

### 1. Google Sheets ✅ (Working Now!)
**Current Use**:
- Update GB Energy Dashboard (29 worksheets)
- Write BigQuery query results
- Format cells and create charts
- Auto-refresh every 5 minutes

**Your Scripts Using This**: 98 Python scripts

**Code Pattern**:
```python
from google.oauth2 import service_account
import gspread

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
```

---

### 2. Google Drive 📁 (After Authorization)
**Use Cases**:
- **Index all your files** (Drive Indexer does this - 139K+ files)
- Find documents by name or content
- List folder contents
- Track file changes
- Monitor shared folders

**Code Pattern**:
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
).with_subject('george@upowerenergy.uk')

drive = build('drive', 'v3', credentials=creds)

# List files
results = drive.files().list(
    q="name contains 'battery'",
    pageSize=10,
    fields="files(id, name, mimeType, modifiedTime)"
).execute()

for file in results.get('files', []):
    print(f"{file['name']} - {file['mimeType']}")
```

**Practical Examples**:
```python
# Find all CSV files
results = drive.files().list(
    q="mimeType='text/csv'",
    fields="files(name, webViewLink)"
).execute()

# Find files modified this week
from datetime import datetime, timedelta
week_ago = (datetime.now() - timedelta(days=7)).isoformat()
results = drive.files().list(
    q=f"modifiedTime > '{week_ago}'",
    orderBy="modifiedTime desc"
).execute()

# Search in specific folder
results = drive.files().list(
    q="'FOLDER_ID' in parents and name contains 'VLP'"
).execute()
```

---

### 3. Google Docs 📝 (After Authorization)
**Use Cases**:
- **Generate automated reports** from BigQuery data
- Create weekly battery revenue summaries
- Document VLP analysis findings
- Format markdown as Google Docs
- Extract text for natural language analysis

**Code Pattern**:
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/documents']
).with_subject('george@upowerenergy.uk')

docs = build('docs', 'v1', credentials=creds)

# Create a new document
doc = docs.documents().create(body={'title': 'Weekly Battery Report'}).execute()
doc_id = doc['documentId']

# Add content
requests = [
    {
        'insertText': {
            'location': {'index': 1},
            'text': 'Battery Revenue Analysis\n\nWeek of Nov 11, 2025\n'
        }
    }
]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

**Practical Example - Weekly Report**:
```python
def create_weekly_battery_report(revenue_data):
    """Generate automated battery revenue report as Google Doc"""
    docs = build('docs', 'v1', credentials=creds)
    
    # Create document
    doc = docs.documents().create(body={
        'title': f'Battery Revenue Report - Week {datetime.now().strftime("%Y-%m-%d")}'
    }).execute()
    
    # Build content
    content = f"""
    Battery Revenue Analysis
    
    Total Revenue: £{revenue_data['total']:,.2f}
    Top Performing Unit: {revenue_data['top_unit']}
    Average Price: £{revenue_data['avg_price']:.2f}/MWh
    
    High-Value Periods:
    {revenue_data['peak_periods']}
    """
    
    # Insert content
    requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
    docs.documents().batchUpdate(documentId=doc['documentId'], body={'requests': requests}).execute()
    
    return doc['documentId']
```

---

### 4. Apps Script 🔧 (After Authorization)
**Use Cases**:
- **Deploy custom Sheets functions** for calculations
- Create scheduled triggers (hourly/daily data updates)
- Build custom menus and sidebars in Sheets
- Web apps and REST APIs
- Email automation (send reports)

**Code Pattern**:
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/script.projects']
).with_subject('george@upowerenergy.uk')

script = build('script', 'v1', credentials=creds)

# Create new Apps Script project
project = script.projects().create(body={'title': 'Battery Calculator'}).execute()

# Add code files
script_content = """
function calculateArbitrage(chargePrice, dischargePrice, capacity) {
  var efficiency = 0.85;
  var revenue = (dischargePrice - chargePrice) * capacity * efficiency;
  return revenue;
}
"""

# Update project with code
script.projects().updateContent(
    scriptId=project['scriptId'],
    body={'files': [{'name': 'Code', 'type': 'SERVER_JS', 'source': script_content}]}
).execute()
```

**Practical Example - Custom Sheet Function**:
```javascript
// Apps Script code to deploy
function BATTERY_ARBITRAGE(chargePrice, dischargePrice, capacityMWh) {
  var efficiency = 0.85;  // 85% round-trip efficiency
  var revenue = (dischargePrice - chargePrice) * capacityMWh * efficiency;
  return revenue;
}

// Use in Sheets: =BATTERY_ARBITRAGE(A2, B2, C2)
```

---

## 🔐 Security & Permissions

### What the Service Account Can Do

**Scope**: Only what george@upowerenergy.uk can access

- ✅ Read/write files george@ owns or has access to
- ✅ Access Sheets explicitly shared with george@
- ✅ Create new documents as george@
- ❌ Cannot access other users' private files
- ❌ Cannot change Workspace settings
- ❌ Cannot manage other users

### Audit & Control

**Monitor Activity**:
- Google Workspace Admin Console → Reports → Drive
- Filter by: jibber-jabber-knowledge@appspot.gserviceaccount.com

**Revoke Access**:
- Go to: https://admin.google.com/ac/owl/domainwidedelegation
- Find Client ID: 108583076839984080568
- Click "Delete" or "Edit" to remove scopes

**Best Practices**:
- ✅ Keep credentials secure (chmod 600)
- ✅ Only grant minimum needed scopes
- ✅ Regularly review audit logs
- ✅ Use `.gitignore` to exclude credentials from git
- ✅ Rotate credentials periodically (yearly)

---

## 📁 Files Reference

### Created During This Session

| File | Purpose | Status |
|------|---------|--------|
| `workspace-credentials.json` | Delegation credentials | ✅ Ready |
| `test_workspace_credentials.py` | Test Sheets access | ✅ Passing |
| `test_all_google_services.py` | Test all services | ⏳ Run after scope auth |
| `migrate_dashboard_to_delegation.py` | Auto-migrate scripts | ✅ Ready to use |
| `COMPLETE_GOOGLE_SERVICES_SETUP.md` | Detailed setup guide | ✅ Complete |
| `READY_TO_USE_DELEGATION_GUIDE.md` | Quick start guide | ✅ Complete |
| `WORKSPACE_DELEGATION_SUCCESS.md` | Success summary | ✅ Complete |
| `ACTION_PLAN.md` | This file | ✅ Complete |

### Original Credentials

| File | Purpose | Keep/Change |
|------|---------|-------------|
| `inner-cinema-credentials.json` | BigQuery only | ✅ **KEEP** (no changes) |
| `token.pickle` | OAuth (expires) | ⏳ Replace with delegation |
| `gridsmart_service_account.json` | Drive Indexer | ✅ **KEEP** (source of workspace creds) |

---

## 🧪 Testing Commands

```bash
# Test Sheets (should work now)
python3 test_workspace_credentials.py

# Test all services (after adding scopes)
python3 test_all_google_services.py

# Test Drive specifically
python3 << 'EOF'
from google.oauth2 import service_account
from googleapiclient.discovery import build
creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
).with_subject('george@upowerenergy.uk')
drive = build('drive', 'v3', credentials=creds)
results = drive.files().list(pageSize=5, fields="files(name)").execute()
print("✅ Files:", [f['name'] for f in results['files']])
EOF

# Migrate main dashboard script
python3 migrate_dashboard_to_delegation.py

# Test migrated script
python3 realtime_dashboard_updater.py

# Monitor dashboard logs
tail -f logs/dashboard_updater.log
```

---

## 📊 Migration Roadmap

### Phase 1: Authorization (Today - 10 minutes)
- ✅ Add scopes in Workspace Admin
- ✅ Wait for propagation
- ✅ Test all services

### Phase 2: Critical Scripts (This Week - 2 hours)
- ✅ Migrate `realtime_dashboard_updater.py` (auto-refresh)
- ✅ Migrate `update_analysis_bi_enhanced.py` (main dashboard)
- ✅ Migrate `advanced_statistical_analysis_enhanced.py` (stats)
- ✅ Test for 48 hours

### Phase 3: Bulk Migration (Next Week - 4 hours)
- ✅ Update remaining ~95 scripts
- ✅ Test each batch (10 scripts at a time)
- ✅ Monitor logs for issues

### Phase 4: Cleanup (After Stable - 1 hour)
- ✅ Remove `token.pickle` (OAuth token)
- ✅ Remove OAuth authentication code
- ✅ Update documentation
- ✅ Create migration summary

---

## 💡 Future Capabilities Unlocked

### With Full Google Services Access

**Automated Reporting**:
- Weekly battery revenue reports (generated as Docs)
- Monthly VLP analysis summaries
- Daily market condition updates
- Automated email distribution

**Enhanced Drive Indexer**:
- Full file type support (not just Sheets)
- Content search across documents
- Version tracking and history
- File organization automation

**Apps Script Integration**:
- Custom Sheets functions for calculations
- Scheduled data refreshes (beyond cron)
- Interactive dashboards with custom menus
- ChatGPT integration via Apps Script

**Document Generation**:
- Query BigQuery → Generate formatted Docs
- Create presentation-ready reports
- Markdown to Google Docs conversion
- Template-based document creation

---

## 🎯 Success Metrics

### How to Know It's Working

**Immediate (After Authorization)**:
```bash
python3 test_all_google_services.py
# Should show: ✅ SUCCESS for all 4 services
```

**Short-term (After Script Migration)**:
```bash
grep "workspace delegation" logs/dashboard_updater.log
# Should show: "✅ Using workspace delegation (permanent auth)"
```

**Long-term (After Full Migration)**:
- ✅ No more "token expired" errors
- ✅ Cron jobs run reliably 24/7
- ✅ No manual re-authentication needed
- ✅ All 98 scripts using permanent auth

---

## 🔗 Quick Links

**Workspace Admin Console**:  
https://admin.google.com/ac/owl/domainwidedelegation

**Service Account Details**:
- Email: jibber-jabber-knowledge@appspot.gserviceaccount.com
- Client ID: 108583076839984080568

**Documentation**:
- Full Guide: `COMPLETE_GOOGLE_SERVICES_SETUP.md`
- Quick Start: `READY_TO_USE_DELEGATION_GUIDE.md`
- Success Log: `WORKSPACE_DELEGATION_SUCCESS.md`

---

## 🎊 Summary

**Before**:
- ✅ Sheets working (delegation)
- ❌ Drive blocked (needs scope)
- ❌ Docs blocked (needs scope)
- ❌ Apps Script blocked (needs scope)

**After** (5 minutes of work):
- ✅ Full Google Workspace access
- ✅ All automation capabilities unlocked
- ✅ Permanent authentication (no expiration)
- ✅ 98 scripts ready to migrate

**Time Investment**:
- 5 min: Add scopes
- 10 min: Wait for propagation
- 5 min: Test and verify
- **Total: 20 minutes**

**Next Action**: Add scopes in Workspace Admin Console now! 🚀

---

*Last Updated: November 11, 2025*
