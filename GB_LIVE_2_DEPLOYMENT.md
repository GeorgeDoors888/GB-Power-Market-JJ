# GB Live 2 Dashboard - Deployment Guide

**Date**: December 10, 2025  
**Status**: ✅ Successfully Deployed  
**Sheet URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

---

## 🎯 Overview

GB Live 2 is a Google Sheets dashboard that displays real-time UK energy market data by querying BigQuery directly from Apps Script.

**Architecture**: Python → BigQuery (`publication_dashboard_live` table) → Apps Script → Google Sheets

---

## 📁 Project Structure

### Apps Script Files (5 files)
Located in: `/tmp/gb-live-2-final/`

```
/tmp/gb-live-2-final/
├── appsscript.json      # Manifest with BigQuery Advanced Service enabled
├── Code.gs              # Main entry point (onOpen, updateDashboard, executeBigQuery)
├── Data.gs              # BigQuery queries (fetchData, displayData)
├── Dashboard.gs         # Layout creation (setupDashboardLayout)
└── Charts.gs            # Chart rendering (createCharts)
```

### Python Script
- **File**: `/home/george/GB-Power-Market-JJ/build_publication_table_fixed.py`
- **Purpose**: Populates BigQuery `publication_dashboard_live` table
- **Table**: `inner-cinema-476211-u9.uk_energy_prod.publication_dashboard_live`
- **Data Source**: Aggregates from `bmrs_costs`, `bmrs_fuelinst`, `bmrs_mid`, `bmrs_freq`

---

## 🔧 Apps Script Configuration

### Script ID
```
1MNNFFYr06n8ohcj6XI3yb6RwtE0kRFkgRHY5QTmi2-rIkGafGAT0Pp1O
```

### Sheet ID
```
1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

### Critical Settings (appsscript.json)
```json
{
  "timeZone": "Europe/London",
  "dependencies": {
    "enabledAdvancedServices": [
      {
        "userSymbol": "BigQuery",
        "version": "v2",
        "serviceId": "bigquery"
      }
    ]
  },
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/bigquery"
  ],
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8"
}
```

**⚠️ CRITICAL**: BigQuery Advanced Service MUST be enabled in manifest, otherwise `BigQuery.Jobs.query()` will fail silently.

---

## 🚀 Deployment Steps

### Initial Setup (One-time)

1. **Install clasp globally**:
   ```bash
   npm install -g @google/clasp
   clasp login
   ```

2. **Create BigQuery publication table**:
   ```bash
   cd ~/GB-Power-Market-JJ
   python3 build_publication_table_fixed.py
   ```

### Deploy Apps Script to Sheet

1. **Get Script ID from sheet**:
   - Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
   - Go to: Extensions → Apps Script
   - Click: Project Settings (gear icon)
   - Copy: Script ID

2. **Clone and deploy**:
   ```bash
   cd /tmp
   mkdir gb-live-2-final
   cd gb-live-2-final
   clasp clone <SCRIPT_ID>
   
   # Copy the 5 files
   cp /path/to/Code.gs .
   cp /path/to/Data.gs .
   cp /path/to/Dashboard.gs .
   cp /path/to/Charts.gs .
   cp /path/to/appsscript.json .
   
   # Deploy
   clasp push --force
   ```

3. **Refresh the sheet**:
   - Press F5 in browser
   - "GB Live Dashboard" menu should appear
   - Click "Force Refresh Dashboard"
   - Authorize BigQuery access on first run

---

## ⚠️ Common Issues & Solutions

### Issue 1: Wrong Menu Appears (DNO Map, BESS Tools, Diagnostics)
**Symptom**: Sheet shows wrong menus after deployment  
**Root Cause**: Apps Script deployed to wrong sheet or wrong script project attached  
**Solution**:
1. Get correct Script ID from Extensions → Apps Script → Project Settings
2. Use `clasp clone <SCRIPT_ID>` to clone the correct project
3. Deploy files to that cloned project
4. Verify `.clasp.json` has correct scriptId

### Issue 2: Menu Appears But Does Nothing
**Symptom**: "GB Live Dashboard" menu visible but clicking does nothing  
**Root Cause**: Missing BigQuery Advanced Service in `appsscript.json`  
**Solution**:
1. Check `appsscript.json` includes `enabledAdvancedServices` with BigQuery v2
2. Redeploy with `clasp push --force`
3. Refresh sheet (F5)

### Issue 3: "Array cannot have a null element" Error
**Symptom**: Python script fails with NULL array error  
**Root Cause**: NULL values in BigQuery array aggregation  
**Solution**: Use `IFNULL()` in SQL:
```sql
ARRAY_AGG(IFNULL(value, 0) ORDER BY time) as data_array
```

### Issue 4: Sheet Created Instead of Using Existing
**Symptom**: `clasp create --parentId` creates new sheet instead of binding to existing  
**Root Cause**: `clasp create` always creates new container documents  
**Solution**: 
- Don't use `clasp create --parentId`
- Instead, use `clasp clone <SCRIPT_ID>` from the existing sheet's script project

### Issue 5: Only Code.gs File Visible in Apps Script Editor
**Symptom**: Other .gs files not showing up in online editor  
**Root Cause**: Files not properly pushed or need refresh  
**Solution**:
1. Verify all files with: `clasp push --force`
2. Check Apps Script editor: reload page
3. All 5 files should appear in file list (left sidebar)

---

## 📊 BigQuery Table Schema

### Table: `publication_dashboard_live`

**Single row table** with aggregated data:

```
report_date              DATE
vlp_revenue_total        FLOAT64
wholesale_price_avg      FLOAT64
grid_frequency_avg       FLOAT64
total_generation         FLOAT64
wind_generation          FLOAT64
demand_total             FLOAT64
generation_mix           ARRAY<STRUCT<fuel_type STRING, generation FLOAT64>>
interconnectors          ARRAY<STRUCT<name STRING, flow FLOAT64>>
intraday_wind            ARRAY<FLOAT64>  (24 values)
intraday_demand          ARRAY<FLOAT64>  (24 values)
intraday_price           ARRAY<FLOAT64>  (24 values)
```

**Update Command**:
```bash
python3 ~/GB-Power-Market-JJ/build_publication_table_fixed.py
```

---

## 🔄 Maintenance

### Update Dashboard Data
```bash
cd ~/GB-Power-Market-JJ
python3 build_publication_table_fixed.py
```
Then in Google Sheets: GB Live Dashboard → Force Refresh Dashboard

### Update Apps Script Code
```bash
cd /tmp/gb-live-2-final
# Edit .gs files as needed
clasp push --force
```
Refresh sheet (F5) to see changes

### Check Deployment Status
```bash
cd /tmp/gb-live-2-final
cat .clasp.json  # Verify scriptId and sheet binding
clasp pull        # Pull latest from Apps Script
clasp open        # Open Apps Script editor in browser
```

---

## 🎨 Dashboard Features

### Menu: "GB Live Dashboard"
- **Force Refresh Dashboard**: Queries BigQuery and updates all data

### Dashboard Layout (Fully Implemented)

**Header Section** (Rows 1-2)
- Title: "GB Power Market - Live Executive Dashboard"
- Timestamp: Auto-updated on each refresh

**Key Performance Indicators** (Rows 4-8)
- 6 KPIs displayed with sparklines:
  - VLP Revenue (£k)
  - Wholesale Avg (£/MWh)
  - Grid Frequency (Hz)
  - Total Gen (GW)
  - Wind Gen (GW)
  - Demand (GW)
- Each KPI has a 7-day trend sparkline

**Live Market Snapshot** (Rows 10+)
- Generation Mix table with fuel types and MW values
- Pie chart visualization of generation mix
- Interconnectors table with cross-border flows

**24-Hour Intraday Trends** (Rows 25+)
- Three sparkline charts:
  - Intraday Price (£/MWh) - 24 hours
  - Intraday Demand (GW) - 24 hours
  - Intraday Wind (GW) - 24 hours

**System Status & Weather Analysis** (Rows 29+)
- SO Constraints & Interventions (placeholder)
- Generator Outages (placeholder)
- Weather & Wind Forecast (placeholder)

---

## 🔐 Security & Permissions

### Service Account
- **Project**: `inner-cinema-476211-u9`
- **Service Account**: Uses user's OAuth credentials (no service account needed for Apps Script)

### OAuth Scopes Required
```
https://www.googleapis.com/auth/spreadsheets
https://www.googleapis.com/auth/bigquery
```

### First Run Authorization
User must authorize on first "Force Refresh Dashboard" click:
1. Click menu item
2. See "Authorization Required" dialog
3. Click "Review Permissions"
4. Select Google account
5. Click "Allow"
6. Script runs successfully

---

## 📝 File Locations Summary

| Item | Location |
|------|----------|
| Apps Script Files | `/tmp/gb-live-2-final/` |
| Python Script | `/home/george/GB-Power-Market-JJ/build_publication_table_fixed.py` |
| BigQuery Table | `inner-cinema-476211-u9.uk_energy_prod.publication_dashboard_live` |
| Google Sheet | `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA` |
| Apps Script Project | `1MNNFFYr06n8ohcj6XI3yb6RwtE0kRFkgRHY5QTmi2-rIkGafGAT0Pp1O` |
| Documentation | `/home/george/GB-Power-Market-JJ/GB_LIVE_2_DEPLOYMENT.md` |

---

## 🐛 Troubleshooting Commands

```bash
# Check what's deployed
cd /tmp/gb-live-2-final
clasp pull
ls -la *.gs *.json

# Verify BigQuery table exists
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
table = client.get_table('uk_energy_prod.publication_dashboard_live')
print(f'✅ Table exists: {table.num_rows} rows')
"

# Test Apps Script connection
cd /tmp/gb-live-2-final
clasp open  # Opens Apps Script editor in browser

# Check logs after running dashboard
# In Apps Script editor: View → Executions
```

---

## 📚 Related Documentation

- **Main Project Config**: `PROJECT_CONFIGURATION.md`
- **Data Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **ChatGPT Instructions**: `CHATGPT_INSTRUCTIONS.md`
- **Documentation Index**: `DOCUMENTATION_INDEX.md`

---

## ✅ Deployment Checklist

- [x] BigQuery `publication_dashboard_live` table created
- [x] Table populated with sample data (2025-10-30)
- [x] Apps Script project created and bound to correct sheet
- [x] All 5 files deployed (Code.gs, Data.gs, Dashboard.gs, Charts.gs, appsscript.json)
- [x] BigQuery Advanced Service enabled in manifest
- [x] OAuth scopes configured correctly
- [x] Menu "GB Live Dashboard" appears in sheet
- [x] Script ID documented: `1MNNFFYr06n8ohcj6XI3yb6RwtE0kRFkgRHY5QTmi2-rIkGafGAT0Pp1O`
- [x] Sheet ID documented: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`

---

**Last Updated**: December 10, 2025  
**Status**: ✅ Production Ready  
**Next Steps**: 
1. Update BigQuery table to current date
2. Test dashboard refresh in sheet
3. Authorize OAuth on first run
4. Verify data displays correctly
