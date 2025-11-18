# GB Energy Dashboard - Google Workspace Delegation Guide

**Project**: GB Power Market JJ  
**Dashboard**: GB Energy Dashboard (12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8)  
**Status**: ✅ Workspace Delegation Active  
**Date**: November 11, 2025

---

## 🎯 Overview

This guide shows how to use **domain-wide delegation** for the GB Energy Dashboard project, replacing the old OAuth `token.pickle` method with permanent service account authentication.

### What Changed

**BEFORE (Old Method)**:
```python
# Used OAuth token.pickle - expires every 7 days
gc = gspread.oauth()  # ❌ Requires manual re-authentication
```

**AFTER (New Method)**:
```python
# Uses service account with domain-wide delegation - never expires
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')
gc = gspread.authorize(creds)  # ✅ Works forever, no re-auth needed
```

---

## 🔑 Credentials Setup

### Service Account Details

**Service Account Email**: `jibber-jabber-knowledge@appspot.gserviceaccount.com`  
**Client ID**: `108583076839984080568`  
**Domain**: upowerenergy.uk  
**Impersonates**: george@upowerenergy.uk

### Credentials File Locations

**Original File**:
```bash
~/Overarch Jibber Jabber/gridsmart_service_account.json
```

**Project Copy** (use this in your scripts):
```bash
~/GB Power Market JJ/workspace-credentials.json
```

**Permissions**: `chmod 600` (already set)

### Active Scopes (Verified Working ✅)

1. `https://www.googleapis.com/auth/spreadsheets` - Read/write Sheets
2. `https://www.googleapis.com/auth/drive.readonly` - List Drive files
3. `https://www.googleapis.com/auth/drive` - Full Drive access
4. `https://www.googleapis.com/auth/documents` - Read/write Docs
5. `https://www.googleapis.com/auth/script.projects` - Apps Script access

**Verification**: Run `python3 test_all_google_services.py` (all pass ✅)

---

## 📊 GB Energy Dashboard Details

**Spreadsheet ID**: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`  
**Title**: GB Energy Dashboard  
**Worksheets**: 29 total  
**Owner**: george@upowerenergy.uk  
**URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

### Key Worksheets

- **Dashboard** - Main summary view
- **Real-time Data** - Live IRIS feeds
- **Historical Analysis** - Long-term trends
- **Battery VLP** - Virtual Lead Party analysis
- **Frequency** - Grid frequency monitoring
- **Prices** - Market price data
- *(23 more worksheets)*

---

## 🔄 Migrating Dashboard Scripts

### Script: `realtime_dashboard_updater.py`

**Current Status**: Uses token.pickle (expires)  
**Migration Status**: ✅ Ready to migrate  
**Priority**: HIGH (runs every 5 minutes via cron)

#### Current Code (Lines to Replace)

**OLD (expires)**:
```python
# Current authentication - uses OAuth token
gc = gspread.oauth()
```

**NEW (permanent)**:
```python
from google.oauth2 import service_account

# Workspace authentication (uPower Energy)
sheets_creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(sheets_creds)
```

#### BigQuery Authentication (Keep Separate!)

**IMPORTANT**: BigQuery uses a **different credentials file** (Smart Grid company):

```python
from google.cloud import bigquery

# BigQuery authentication (Smart Grid) - KEEP THIS UNCHANGED
bq_client = bigquery.Client(
    project='inner-cinema-476211-u9',
    credentials=service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json'
    )
)
```

#### Complete Updated Pattern

```python
#!/usr/bin/env python3
"""
GB Energy Dashboard - Real-time Updater
Uses workspace delegation for Sheets + separate BigQuery auth
"""

from google.oauth2 import service_account
from google.cloud import bigquery
import gspread
import pandas as pd

# 1. BigQuery authentication (Smart Grid company)
bq_creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
bq_client = bigquery.Client(
    project='inner-cinema-476211-u9',
    credentials=bq_creds
)

# 2. Sheets authentication (uPower Energy company)
sheets_creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(sheets_creds)

# 3. Query BigQuery (Smart Grid data)
query = """
SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    frequency
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
WHERE settlementDate >= CURRENT_DATE() - 7
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 1000
"""

df = bq_client.query(query).to_dataframe()

# 4. Update Sheets (uPower Energy dashboard)
spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
worksheet = spreadsheet.worksheet('Real-time Data')

# Clear and update
worksheet.clear()
worksheet.update([df.columns.values.tolist()] + df.values.tolist())

print(f"✅ Updated {len(df)} rows at {pd.Timestamp.now()}")
```

---

## 🛠️ Migration Steps for Dashboard Scripts

### Step 1: Backup Current Script

```bash
cd ~/GB\ Power\ Market\ JJ
cp realtime_dashboard_updater.py realtime_dashboard_updater.py.backup
```

### Step 2: Update Authentication Code

**Find this pattern**:
```python
gc = gspread.oauth()
```

**Replace with**:
```python
from google.oauth2 import service_account

sheets_creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(sheets_creds)
```

### Step 3: Verify BigQuery Auth (Don't Change!)

**Make sure this stays the same**:
```python
from google.cloud import bigquery

bq_client = bigquery.Client(
    project='inner-cinema-476211-u9',
    credentials=service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json'
    )
)
```

### Step 4: Test Manually

```bash
cd ~/GB\ Power\ Market\ JJ
python3 realtime_dashboard_updater.py
```

**Expected Output**:
```
✅ Updated 1000 rows at 2025-11-11 14:30:00
```

### Step 5: Check Dashboard

Open dashboard: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

Verify:
- ✅ Data updated successfully
- ✅ Timestamps are recent
- ✅ No authentication errors

### Step 6: Monitor Cron Job

```bash
# Check cron is still running
tail -f logs/dashboard_updater.log

# Should see updates every 5 minutes
# ✅ 14:30:00 - Updated 1000 rows
# ✅ 14:35:00 - Updated 1000 rows
# ✅ 14:40:00 - Updated 1000 rows
```

---

## 📝 Other Dashboard Scripts to Migrate

### Priority List

**HIGH PRIORITY** (migrate first):
1. ✅ `realtime_dashboard_updater.py` - Runs every 5 min (cron)
2. `update_analysis_bi_enhanced.py` - Manual dashboard refresh
3. `enhance_dashboard_layout.py` - Dashboard formatting
4. `format_dashboard.py` - Apply formatting

**MEDIUM PRIORITY**:
5. `add_dashboard_charts.py` - Chart creation
6. `add_map_to_dashboard.py` - Map embedding
7. Any script that reads/writes to GB Energy Dashboard

**LOW PRIORITY**:
- Scripts that only query BigQuery (no Sheets access)
- One-off analysis scripts
- Historical data exports

### Migration Helper Script

Use this tool to auto-migrate scripts:

```bash
python3 migrate_dashboard_to_delegation.py
```

**What it does**:
1. Creates backup (`.backup` extension)
2. Updates authentication code
3. Preserves BigQuery auth (unchanged)
4. Runs syntax check
5. Shows diff of changes

---

## 🔒 Security Best Practices

### Credentials Protection

**DO**:
- ✅ Keep `workspace-credentials.json` at `chmod 600`
- ✅ Keep `inner-cinema-credentials.json` at `chmod 600`
- ✅ Add both to `.gitignore` (already done)
- ✅ Use separate credentials for separate companies

**DON'T**:
- ❌ Commit credentials to git
- ❌ Share credentials in Slack/email
- ❌ Mix BigQuery and Workspace credentials
- ❌ Change file permissions to 644 or 777

### Audit Logging

All Sheets access is logged:
- **URL**: https://admin.google.com/ac/reporting/audit/user
- **Filter**: Service = "Google Sheets"
- **User**: jibber-jabber-knowledge@appspot.gserviceaccount.com
- **Shows**: All read/write operations with timestamps

### Access Scope

**What service account CAN access**:
- ✅ Any file george@upowerenergy.uk can access
- ✅ Any Sheet in the domain
- ✅ Any Drive file george@ has permission for

**What service account CANNOT access**:
- ❌ Files owned by other users (unless shared with george@)
- ❌ Files in other Google Workspace domains
- ❌ BigQuery in Smart Grid project (uses different credentials)

---

## 🧪 Testing & Verification

### Test 1: Basic Sheets Access

```bash
cd ~/GB\ Power\ Market\ JJ
python3 << 'EOF'
from google.oauth2 import service_account
import gspread

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')

print(f"✅ SUCCESS")
print(f"Title: {spreadsheet.title}")
print(f"Worksheets: {len(spreadsheet.worksheets())}")
EOF
```

**Expected Output**:
```
✅ SUCCESS
Title: GB Energy Dashboard
Worksheets: 29
```

### Test 2: Read Dashboard Worksheet

```bash
python3 << 'EOF'
from google.oauth2 import service_account
import gspread

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
worksheet = spreadsheet.worksheet('Dashboard')

# Read first 5 rows
data = worksheet.get('A1:E5')

print(f"✅ Read {len(data)} rows from Dashboard")
for row in data[:3]:
    print(f"  {row}")
EOF
```

### Test 3: Complete Dashboard Update

```bash
python3 << 'EOF'
from google.oauth2 import service_account
from google.cloud import bigquery
import gspread
import pandas as pd

# BigQuery (Smart Grid)
bq_creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
bq_client = bigquery.Client(project='inner-cinema-476211-u9', credentials=bq_creds)

# Sheets (uPower Energy)
sheets_creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')
gc = gspread.authorize(sheets_creds)

# Query
df = bq_client.query("""
    SELECT CAST(settlementDate AS DATE) as date, frequency
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
    WHERE settlementDate >= CURRENT_DATE() - 1
    ORDER BY settlementDate DESC
    LIMIT 10
""").to_dataframe()

print(f"✅ Retrieved {len(df)} rows from BigQuery")
print(f"✅ Ready to update dashboard")
print(f"   Spreadsheet: GB Energy Dashboard")
print(f"   Worksheet: Real-time Data")
EOF
```

---

## 📊 Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              GB Energy Dashboard (Google Sheets)            │
│         12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8       │
│                                                             │
│  Owner: george@upowerenergy.uk                              │
│  Company: uPower Energy                                     │
│  Worksheets: 29                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ (writes data every 5 min)
                         │
┌────────────────────────▼────────────────────────────────────┐
│         realtime_dashboard_updater.py (cron job)            │
│                                                             │
│  Authentication:                                            │
│  • Sheets: workspace-credentials.json (uPower Energy)       │
│  • BigQuery: inner-cinema-credentials.json (Smart Grid)     │
│                                                             │
│  Process:                                                   │
│  1. Query BigQuery (IRIS + historical data)                 │
│  2. Transform data (pandas)                                 │
│  3. Update Sheets (gspread)                                 │
└──────────────┬────────────────────┬─────────────────────────┘
               │                    │
               │                    │
       ┌───────▼──────┐     ┌──────▼──────────┐
       │   BigQuery   │     │  Google Sheets   │
       │ (Smart Grid) │     │  (uPower Energy) │
       │              │     │                  │
       │ Project:     │     │  Domain:         │
       │ inner-cinema │     │  upowerenergy.uk │
       │              │     │                  │
       │ Tables:      │     │  Dashboard:      │
       │ • bmrs_freq  │     │  • Real-time     │
       │ • bmrs_bod   │     │  • Historical    │
       │ • bmrs_mid   │     │  • Battery VLP   │
       │ • (182 more) │     │  • (26 more)     │
       └──────────────┘     └──────────────────┘
```

---

## 🚨 Troubleshooting

### Error: "unauthorized_client"

**Symptom**:
```
google.auth.exceptions.RefreshError: unauthorized_client: 
Client is unauthorized to retrieve access tokens
```

**Cause**: Scope not added in Workspace Admin

**Fix**:
1. Go to: https://admin.google.com/ac/owl/domainwidedelegation
2. Find Client ID: 108583076839984080568
3. Add missing scope (e.g., `https://www.googleapis.com/auth/spreadsheets`)
4. Click "Authorize"
5. Wait 10 minutes
6. Retry

### Error: "Credentials file not found"

**Symptom**:
```
FileNotFoundError: workspace-credentials.json
```

**Cause**: Running script from wrong directory

**Fix**:
```bash
# Always run from project root
cd ~/GB\ Power\ Market\ JJ
python3 realtime_dashboard_updater.py

# Or use absolute path in script
creds = service_account.Credentials.from_service_account_file(
    '/Users/georgemajor/GB Power Market JJ/workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')
```

### Error: "Spreadsheet not found"

**Symptom**:
```
gspread.exceptions.SpreadsheetNotFound
```

**Cause**: Service account trying to access file george@ doesn't have permission for

**Fix**:
1. Open spreadsheet in browser (as george@upowerenergy.uk)
2. Check if file exists
3. Verify spreadsheet ID is correct
4. Check george@ has access (Owner/Editor)

### Error: "BigQuery permission denied"

**Symptom**:
```
google.api_core.exceptions.Forbidden: 403 Access Denied
```

**Cause**: Using wrong credentials file for BigQuery

**Fix**: Make sure BigQuery uses `inner-cinema-credentials.json`:

```python
# CORRECT - BigQuery uses Smart Grid credentials
bq_client = bigquery.Client(
    project='inner-cinema-476211-u9',
    credentials=service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json'  # ✅ Correct file
    )
)

# WRONG - Don't use workspace credentials for BigQuery
bq_client = bigquery.Client(
    credentials=sheets_creds  # ❌ Wrong! This is uPower Energy
)
```

---

## 📚 Related Documentation

**Setup & Configuration**:
- `WORKSPACE_DELEGATION_COMPLETE.md` - Current status summary
- `COMPLETE_GOOGLE_SERVICES_SETUP.md` - Full setup guide
- `TWO_COMPANIES_CLARIFICATION.md` - BigQuery vs Workspace separation

**Testing & Verification**:
- `test_all_google_services.py` - Test all 4 services
- `test_workspace_credentials.py` - Sheets-specific test

**Migration Tools**:
- `migrate_dashboard_to_delegation.py` - Auto-migration script
- `google_auth_utils.py` - Drop-in authentication helper

**Railway + ChatGPT Integration**:
- `railway_google_workspace_endpoints.py` - API endpoints
- `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md` - ChatGPT setup
- `RAILWAY_DEPLOYMENT_GUIDE.md` - Deployment steps

**Reference**:
- `GOOGLE_AUTH_FILES_REFERENCE.md` - All 98 scripts documented
- `PROJECT_CONFIGURATION.md` - All project settings

---

## ✅ Quick Reference

### Authentication Pattern (Copy This!)

```python
#!/usr/bin/env python3
"""
GB Energy Dashboard Update Script
Two separate authentications: BigQuery (Smart Grid) + Sheets (uPower Energy)
"""

from google.oauth2 import service_account
from google.cloud import bigquery
import gspread
import pandas as pd

def main():
    # 1. BigQuery authentication (Smart Grid company)
    bq_creds = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json'
    )
    bq_client = bigquery.Client(
        project='inner-cinema-476211-u9',
        credentials=bq_creds
    )
    
    # 2. Sheets authentication (uPower Energy company)
    sheets_creds = service_account.Credentials.from_service_account_file(
        'workspace-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    ).with_subject('george@upowerenergy.uk')
    
    gc = gspread.authorize(sheets_creds)
    
    # 3. Query BigQuery
    query = """
        SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
        WHERE settlementDate >= CURRENT_DATE() - 7
        LIMIT 1000
    """
    df = bq_client.query(query).to_dataframe()
    
    # 4. Update Sheets
    spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
    worksheet = spreadsheet.worksheet('Real-time Data')
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    
    print(f"✅ Updated {len(df)} rows at {pd.Timestamp.now()}")

if __name__ == '__main__':
    main()
```

### Key Files & IDs

**Dashboard**:
- Spreadsheet ID: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`
- Title: GB Energy Dashboard
- Worksheets: 29

**Credentials**:
- Workspace (uPower Energy): `workspace-credentials.json`
- BigQuery (Smart Grid): `inner-cinema-credentials.json`

**Service Account**:
- Email: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- Client ID: `108583076839984080568`
- Impersonates: `george@upowerenergy.uk`

**BigQuery**:
- Project: `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod`
- Location: `US`

---

*Last Updated: November 11, 2025*  
*Status: ✅ Active and Working*  
*Next: Deploy to Railway + ChatGPT Integration*
