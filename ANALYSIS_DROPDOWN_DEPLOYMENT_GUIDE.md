# Analysis Dropdowns - Deployment Complete ✅

**Date**: December 20, 2025
**Status**: Ready to deploy to Google Sheets

## What Was Done

### 1. BSC Party Roles Reference Data ✅
- **Created**: `bsc_signatories` table in BigQuery (`uk_energy_prod` dataset)
- **Source**: Elexon BSC official party role definitions
- **Records**: 14 party role types
- **Table**: `inner-cinema-476211-u9.uk_energy_prod.bsc_signatories`

### 2. Party Role Definitions

| Code | Description |
|------|-------------|
| BP | BSC Party |
| DSO | Distribution System Operator |
| IA | Interconnector Administrator |
| IE | Interconnector Error Administrator |
| NETSO | National Electricity Transmission System Operator |
| TG | Trading Party – Generator |
| TI | Trading Party – Interconnector User |
| TN | Trading Party – Non Physical |
| TS | Trading Party – Supplier |
| EN | ECVNA |
| MV | MVRNA |
| VP | Virtual Lead Party |
| AV | Asset Metering Virtual Lead Party |
| VT | Virtual Trading Party |

### 3. Google Sheets Script Ready ✅
**File**: `ANALYSIS_DROPDOWNS.gs`

## Deployment Instructions

### Step 1: Open Google Sheets
```
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
```

### Step 2: Open Apps Script Editor
1. Click **Extensions** → **Apps Script**
2. You'll see the script editor

### Step 3: Deploy the Script
1. **Delete any existing code** in the editor
2. **Copy the entire contents** of `ANALYSIS_DROPDOWNS.gs`
3. **Paste** into the Apps Script editor
4. Click **Save** (💾 icon)
5. **Close** the Apps Script tab

### Step 4: Run the Function
1. Back in Google Sheets
2. Refresh the page (F5)
3. You should see a new menu: **🔧 Custom Tools**
4. Click: **🔧 Custom Tools** → **Add Analysis Dropdowns**
5. **Authorize** when prompted (first time only)
6. Wait for confirmation popup

### Step 5: Verify Dropdowns
The script creates **4 dropdowns** in the Analysis sheet:

**Row 4 Headers (Blue background):**
- **Cell B4**: Time Period dropdown
  - Options: LIVE DATA, TODAY, WEEK, MONTH, YEAR, ALL

- **Cell D4**: From Date dropdown
  - Options: Last 90 days + next 7 days (98 total dates)

- **Cell F4**: To Date dropdown
  - Options: Same 98 dates as From Date

- **Cell H4**: Party Role dropdown
  - Options: 14 party roles (BP, DSO, NETSO, VP, etc.)

## How It Works

### Data Flow
```
Elexon BSC Website
    ↓
scrape_and_upload_bsc_signatories.py
    ↓
BigQuery table: bsc_signatories
    ↓
Google Apps Script: ANALYSIS_DROPDOWNS.gs
    ↓
Google Sheets: Analysis sheet dropdowns
```

### Technical Details

**BigQuery Table Schema:**
```sql
CREATE TABLE uk_energy_prod.bsc_signatories (
  party_role_code STRING NOT NULL,
  party_role_description STRING NOT NULL,
  scraped_date TIMESTAMP
);
```

**Apps Script Functions:**
- `addAnalysisDropdowns()` - Main function to create dropdowns
- `onOpen()` - Adds custom menu on sheet open

### Future Enhancements
- **Query Integration**: Use dropdown values to filter BigQuery queries
- **Dynamic Party List**: Fetch actual party names (e.g., "FFSEN005", "FBPGM002")
- **Auto-Refresh**: Update dropdowns automatically when data changes

## Files Created

1. **ANALYSIS_DROPDOWNS.gs** - Google Apps Script (ready to paste)
2. **scrape_and_upload_bsc_signatories.py** - Python uploader script
3. **bsc_signatories** - BigQuery table (14 rows)
4. **ANALYSIS_DROPDOWN_DEPLOYMENT_GUIDE.md** - This file

## Testing

Verify BigQuery data:
```sql
SELECT *
FROM `inner-cinema-476211-u9.uk_energy_prod.bsc_signatories`
ORDER BY party_role_code;
```

Expected output: 14 rows with party role codes and descriptions.

## Troubleshooting

### "Analysis sheet not found"
- Ensure the sheet is named exactly **"Analysis"** (case-sensitive)
- Create the sheet if it doesn't exist

### Authorization Issues
- On first run, Google will ask to authorize the script
- Click **Review Permissions** → select your account → **Allow**

### Dropdown Not Showing
- Refresh the Google Sheets page (F5)
- Check that you clicked "Add Analysis Dropdowns" from the menu
- Check Apps Script logs: Extensions → Apps Script → Executions

## Next Steps

1. **Deploy the script** (5 minutes)
2. Test the dropdowns work correctly
3. Build query logic that uses these dropdown values
4. Integrate with dashboard refresh automation

---

**Status**: ✅ Ready for deployment
**Maintainer**: George Major (george@upowerenergy.uk)
**Last Updated**: December 20, 2025
