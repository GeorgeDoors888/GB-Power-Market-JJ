# API SETUP STATUS - 30 October 2025

## ✅ Current API Configuration

### Google Sheets API
- **Status**: ✅ WORKING
- **User**: george@upowerenergy.uk
- **Credentials**: `credentials.json`, `token.pickle`
- **Access**: Read/Write to all spreadsheets
- **Target Spreadsheet**: 
  - ID: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`
  - Name: **GB Energy Dashboard**
  - Sheets: 10 (Sheet1, Calculations BHM, HH Profile, Sheet7, DNO_ID, DNUoS 2, DNUoS, Map, DNO_Data, Chart Data)

### Google Drive API
- **Status**: ✅ WORKING
- **User**: george@upowerenergy.uk
- **Credentials**: `token.pickle`
- **Access**: Full drive access for file management

### BigQuery API
- **Status**: ⚠️ PARTIAL - Permission Issue
- **Project ID**: `jibber-jabber-knowledge` (service account project)
- **Target Project**: `inner-cinema-476211-u9` (Grid Smart - actual data project)
- **Service Account**: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- **Credentials**: `jibber_jabber_key.json`
- **Issue**: Service account needs permissions on `inner-cinema-476211-u9` project
- **Dataset**: `gb_power`

**Fix Required:**
```bash
# Grant service account access to inner-cinema-476211-u9
# In Google Cloud Console:
1. Go to https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9
2. Add member: jibber-jabber-knowledge@appspot.gserviceaccount.com
3. Grant roles:
   - BigQuery Data Editor
   - BigQuery Job User
```

### Google Apps Script
- **Status**: ✅ AVAILABLE (needs manual setup in Sheets UI)
- **Location**: Extensions > Apps Script in Google Sheets
- **Current Scripts**: Preserved in GB Energy Dashboard
- **Setup**: 
  1. Open https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
  2. Go to Extensions > Apps Script
  3. Scripts are bound to the spreadsheet

---

## 📊 GB Energy Dashboard Integration

### Current Data in Spreadsheet

**DNUoS Sheet** (100 rows):
- Year, DNO_Code, DNO_Name, Tariff_Name
- LLFCs, PCs
- Red_Rate_p_kWh, Amber_Rate_p_kWh, Green_Rate_p_kWh
- Fixed_Charge_p_day, Capacity_Charge_p_kVA_day
- Document, Document_Reference

**Available to Upload**:
- ✅ All 14 DNOs - 2,108 comprehensive tariffs
- File: `all_14_dnos_comprehensive_tariffs.csv`
- Years: 2020-2026
- Full LLFC and PC documentation

### Upload Options

**Option 1: Replace DNUoS Sheet**
```python
# Upload all 2,108 tariffs to replace current 100 rows
python upload_all_14_to_dashboard.py
```

**Option 2: Add New Sheet**
```python
# Add "DNUoS_Complete" sheet with full dataset
python add_complete_tariffs_sheet.py
```

**Option 3: Update via BigQuery** (requires permission fix)
```python
# Load to BigQuery then link to Sheets
python load_tariffs_to_bigquery.py
```

---

## 🔧 APIs Enabled in Google Cloud Projects

### jibber-jabber-knowledge (Service Account Project)
- ✅ BigQuery API
- ✅ Cloud Storage API
- Service Account can create jobs in this project

### inner-cinema-476211-u9 (Grid Smart - Data Project)
- ✅ BigQuery API
- ✅ BigQuery Data Transfer API
- ✅ Cloud Storage API
- ⚠️ Service account needs IAM permissions

### george@upowerenergy.uk (User Account)
- ✅ Google Sheets API
- ✅ Google Drive API
- ✅ Apps Script API (via Sheets UI)

---

## 📝 Credential Files

### credentials.json
- **Type**: OAuth 2.0 Client ID
- **Project**: jibber-jabber-knowledge
- **Scopes**: 
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive`
  - `https://www.googleapis.com/auth/documents`

### token.pickle
- **Type**: OAuth 2.0 Access Token
- **User**: george@upowerenergy.uk
- **Status**: Active and refreshable
- **Scopes**: Sheets, Drive, Docs

### jibber_jabber_key.json
- **Type**: Service Account Key
- **Project**: jibber-jabber-knowledge
- **Email**: jibber-jabber-knowledge@appspot.gserviceaccount.com
- **Use**: BigQuery operations

### oauth_credentials.json
- **Type**: OAuth credentials backup
- **Status**: Redundant (same as credentials.json)

---

## 🚀 Quick Commands

### Re-authenticate Google Sheets/Drive
```bash
cd "/Users/georgemajor/GB Power Market JJ"
rm -f token.pickle
.venv/bin/python authorize_google_docs.py
```

### Test API Access
```bash
.venv/bin/python verify_api_setup.py
```

### Read Dashboard Spreadsheet
```bash
.venv/bin/python read_user_spreadsheet.py
```

### Upload 2,108 Tariffs to Dashboard
```bash
# Coming soon - need your preference on which sheet to update
```

---

## 📚 Related Documentation

- `COMPREHENSIVE_TARIFFS_COMPLETE.md` - NGED tariff extraction (640 tariffs)
- `ALL_14_DNOS_COMPLETE.md` - All 14 DNOs extraction (2,108 tariffs)
- `OAUTH_SETUP_INSTRUCTIONS.md` - OAuth setup guide
- `QUICK_REFERENCE.md` - Quick command reference

---

## ✅ Verification Results

**Date**: 30 October 2025  
**Google Sheets**: ✅ Working  
**Google Drive**: ✅ Working  
**BigQuery**: ⚠️ Needs Permission  
**Apps Script**: ✅ Available  
**Spreadsheet Access**: ✅ Confirmed  

**Next Steps**:
1. ✅ APIs verified
2. ✅ Spreadsheet read successfully
3. ⏳ Grant BigQuery permissions (optional)
4. ⏳ Upload complete tariff dataset to dashboard
5. ⏳ Update documentation files

---

**Report Generated**: 30 October 2025  
**System**: GB Power Market JJ  
**User**: george@upowerenergy.uk
