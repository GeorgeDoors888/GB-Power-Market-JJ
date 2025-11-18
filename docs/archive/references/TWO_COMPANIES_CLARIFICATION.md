# ⚠️ CRITICAL CORRECTION - Two Separate Companies

**Date**: November 11, 2025  
**Issue**: BigQuery scope should NOT be added to Workspace delegation

---

## 🚨 IMPORTANT CLARIFICATION

You have **TWO COMPLETELY SEPARATE COMPANIES** with different credentials:

### Company 1: Smart Grid (BigQuery Owner)
```
Project: inner-cinema-476211-u9
Credentials: inner-cinema-credentials.json
Service Account: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com
Purpose: Query BigQuery energy data
Auth Type: Standard service account (NO delegation needed)
Status: ✅ WORKING - DO NOT CHANGE!
```

### Company 2: uPower Energy (Workspace Owner)
```
Domain: upowerenergy.uk
Credentials: workspace-credentials.json
Service Account: jibber-jabber-knowledge@appspot.gserviceaccount.com
Purpose: Google Workspace (Sheets, Drive, Docs, Apps Script)
Auth Type: Domain-wide delegation
Status: ⏳ Add Sheets/Drive/Docs/Apps Script scopes only
```

---

## ✅ CORRECTED SCOPE LIST

When adding scopes for Client ID **108583076839984080568**, use **ONLY** these:

```
https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/script.projects
```

### ❌ DO NOT ADD:
- `https://www.googleapis.com/auth/bigquery` ← **WRONG!** This belongs to Smart Grid company

---

## 📊 What Each Credential File Does

### `inner-cinema-credentials.json` (Smart Grid Company)
**Purpose**: BigQuery ONLY  
**Used by**: 98 Python scripts for data queries  
**Keep unchanged**: ✅ Already working perfectly

**Example usage**:
```python
from google.cloud import bigquery
from google.oauth2 import service_account

# BigQuery - uses Smart Grid credentials
bq_credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',  # Smart Grid company
    scopes=["https://www.googleapis.com/auth/bigquery"]
)
bq_client = bigquery.Client(project='inner-cinema-476211-u9', credentials=bq_credentials)
```

### `workspace-credentials.json` (uPower Energy Company)
**Purpose**: Google Workspace (Sheets, Drive, Docs, Apps Script)  
**Used by**: Dashboard updates, Drive Indexer, automation  
**Needs**: Delegation scopes added (NOT BigQuery!)

**Example usage**:
```python
from google.oauth2 import service_account
import gspread

# Sheets - uses uPower Energy credentials
sheets_credentials = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',  # uPower Energy company
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(sheets_credentials)
```

---

## 🎯 Correct Implementation Pattern

Many of your scripts need **BOTH** credentials for different purposes:

```python
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# 1. BigQuery (Smart Grid) - for data queries
bq_creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
bq_client = bigquery.Client(project='inner-cinema-476211-u9', credentials=bq_creds)

# 2. Sheets (uPower Energy) - for dashboard updates
sheets_creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')
gc = gspread.authorize(sheets_creds)

# Query BigQuery with Smart Grid credentials
query = "SELECT * FROM uk_energy_prod.bmrs_fuelinst LIMIT 100"
df = bq_client.query(query).to_dataframe()

# Write to Sheets with uPower Energy credentials
spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
worksheet = spreadsheet.worksheet('Dashboard')
worksheet.update([df.columns.values.tolist()] + df.values.tolist())
```

---

## 📝 Updated Script Template

Your `realtime_dashboard_updater.py` correctly uses BOTH:

```python
#!/usr/bin/env python3
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from pathlib import Path

# Credentials paths
BIGQUERY_CREDS = Path(__file__).parent / 'inner-cinema-credentials.json'  # Smart Grid
WORKSPACE_CREDS = Path(__file__).parent / 'workspace-credentials.json'    # uPower Energy

# 1. BigQuery connection (Smart Grid company)
bq_credentials = service_account.Credentials.from_service_account_file(
    str(BIGQUERY_CREDS),
    scopes=['https://www.googleapis.com/auth/bigquery']
)
bq_client = bigquery.Client(project='inner-cinema-476211-u9', credentials=bq_credentials)

# 2. Google Sheets connection (uPower Energy company)
sheets_credentials = service_account.Credentials.from_service_account_file(
    str(WORKSPACE_CREDS),
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')
gc = gspread.authorize(sheets_credentials)

# Now use both services...
```

---

## 🔒 Why Keep Them Separate?

### Security & Billing
1. **Different companies** = Different billing accounts
2. **Smart Grid** pays for BigQuery usage
3. **uPower Energy** manages Workspace access
4. **Mixing them** = billing/access confusion

### Access Control
1. **Smart Grid credentials** = BigQuery access only (no Workspace)
2. **Workspace credentials** = Sheets/Drive/Docs only (no BigQuery)
3. **Separation** = principle of least privilege

### Auditing
1. **Smart Grid audit logs** = BigQuery queries tracked separately
2. **Workspace audit logs** = File access tracked separately
3. **Clear accountability** for each system

---

## ✅ Corrected Documentation Files

Updated these files to remove BigQuery scope:

1. ✅ `COMPLETE_GOOGLE_SERVICES_SETUP.md` - Removed bigquery from scope list
2. ✅ `test_all_google_services.py` - Removed bigquery from test
3. ✅ `TWO_COMPANIES_CLARIFICATION.md` - This file (new)

---

## 🎯 Summary

**What to add in Workspace Admin** (Client ID 108583076839984080568):
```
spreadsheets ✅
drive.readonly ✅
drive ✅
documents ✅
script.projects ✅
```

**What NOT to add**:
```
bigquery ❌ (belongs to Smart Grid company)
```

**Keep these completely separate**:
- `inner-cinema-credentials.json` → BigQuery (Smart Grid)
- `workspace-credentials.json` → Sheets/Drive/Docs (uPower Energy)

---

**Next Action**: Add the 5 Workspace scopes (without bigquery) in Workspace Admin Console.
