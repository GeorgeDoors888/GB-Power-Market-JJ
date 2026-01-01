# 🔍 Search Functionality Diagnostics Report

**Generated**: 1 January 2026  
**Issue**: User cannot find search functionality in Google Sheets  
**Status**: ✅ DIAGNOSED - Deployment issue likely

---

## Executive Summary

The search code **exists and is fully functional** in your repository, but may not be **deployed** to your Google Sheets. The search interface is a custom Google Apps Script menu that needs to be installed in your spreadsheet.

---

## What Was Found

### ✅ Search Code File
- **Location**: `/home/george/GB-Power-Market-JJ/search_interface.gs`
- **Size**: 901 lines
- **Status**: Optimized (batch operations implemented)
- **Last Modified**: Recently updated with performance improvements

### ✅ Menu Definition
```javascript
// Line 18-30 in search_interface.gs
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🔍 Search Tools')
      .addItem('🔍 Run Search', 'onSearchButtonClick')
      .addItem('🧹 Clear Search', 'onClearButtonClick')
      .addItem('ℹ️ Help', 'onHelpButtonClick')
      .addSeparator()
      .addItem('📋 View Party Details', 'viewSelectedPartyDetails')
      .addItem('📊 Generate Report', 'generateReportFromSearch')
      .addSeparator()
      .addItem('🔧 Test API Connection', 'testAPIConnection')
      .addToUi();
}
```

### ✅ Google Sheets Structure
Your spreadsheet (`1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`) contains:
- **Search** tab (where search interface lives)
- **SearchDropdowns** tab (dropdown data source)
- **Dropdowns** tab (populated by `populate_search_dropdowns.py`)
- **BM Units Detail**, **BSC Parties Detail** (search results)
- 30+ other tabs verified accessible

### ⚠️ Permission Issues Found
11 scripts use `ScriptApp.getProjectTriggers()` which requires OAuth scope:
- ❌ `clasp-gb-live-2/src/KPISparklines.gs`
- ❌ `bg-sparklines-clasp/Code.gs`
- ❌ `gsp_dno_linking.gs`
- ❌ `threshold_alerts_apps_script.gs`
- ✅ `search_interface.gs` does NOT use this (safe!)

---

## Where Should the Menu Appear?

The `🔍 Search Tools` menu should appear in your Google Sheets menu bar:

```
File | Edit | View | Insert | Format | Data | Tools | Extensions | 🔍 Search Tools | Help
                                                                    ^^^^^^^^^^^^^^^
                                                                    YOUR MENU HERE
```

**Menu Items**:
1. 🔍 Run Search - Execute search query
2. 🧹 Clear Search - Reset all search fields
3. ℹ️ Help - Show usage instructions
4. 📋 View Party Details - Show details for selected row
5. 📊 Generate Report - Export search results
6. 🔧 Test API Connection - Verify backend connectivity

---

## Why You Can't Find It - 3 Possible Reasons

### Reason 1: Apps Script Not Deployed ⚠️ MOST LIKELY
**Problem**: The `search_interface.gs` file exists in your local repository but is not uploaded to your Google Sheets bound script.

**How to Check**:
1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
2. Click: `Extensions` → `Apps Script`
3. Look at left sidebar - do you see `search_interface.gs`?

**If NO**: Follow Solution 1 below  
**If YES**: The file is deployed, try Solution 2

### Reason 2: Sheet Needs Refresh
**Problem**: Google Sheets hasn't run the `onOpen()` function yet.

**Solution**:
- Close and reopen the spreadsheet
- Or manually run: `Extensions` → `Apps Script` → Select `onOpen` function → Click Run

### Reason 3: Wrong Spreadsheet
**Problem**: You're looking at a different spreadsheet.

**Verify URL**:
```
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

---

## Solution 1: Deploy via Web Interface (EASIEST)

### Step-by-Step Instructions

**1. Open Your Spreadsheet**
```
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

**2. Open Apps Script Editor**
- Click: `Extensions` → `Apps Script`
- A new tab will open showing the Apps Script project

**3. Check for Existing File**

**IF you see `search_interface.gs` in left panel**:
- ✅ File is already deployed
- Go to Solution 2 (refresh issue)

**IF you DON'T see `search_interface.gs`**:
- Need to upload the file (continue below)

**4. Create New Script File**
- Click the `+` button next to "Files"
- Select "Script"
- Name it: `search_interface.gs`

**5. Copy Code**
Open terminal on your Linux machine:
```bash
cat /home/george/GB-Power-Market-JJ/search_interface.gs
```

Copy ALL 901 lines and paste into the Apps Script editor.

**6. Save**
- Click the disk icon (Save)
- Or press `Ctrl+S`

**7. Test Deployment**
- Close Apps Script editor tab
- Go back to your spreadsheet
- Refresh the page (`F5`)
- Look for `🔍 Search Tools` menu at top

**8. Authorize (First Time Only)**
- Click `🔍 Search Tools` → `🔍 Run Search`
- You'll see "Authorization required" dialog
- Click "Review Permissions"
- Select your Google account
- Click "Advanced" → "Go to [Your Project]"
- Click "Allow"

**9. Use Search!**
- Menu should now work
- Fill in search criteria in "Search" tab
- Click `🔍 Search Tools` → `🔍 Run Search`

---

## Solution 2: Deploy via CLASP (Command Line)

### Prerequisites
```bash
# Install CLASP (if not already installed)
npm install -g @google/clasp

# Login to Google
clasp login
```

### Deployment Steps

**1. Clone Spreadsheet Project**
```bash
cd /home/george/GB-Power-Market-JJ
clasp clone 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

**2. Copy Search File**
```bash
# File should already be here, but verify:
ls -lh search_interface.gs
```

**3. Push to Google**
```bash
clasp push
```

**4. Verify Deployment**
```bash
clasp open
# Opens your Apps Script project in browser
# Verify search_interface.gs appears in file list
```

**5. Refresh Spreadsheet**
- Open spreadsheet in browser
- Press `F5` to refresh
- Menu should appear!

---

## Solution 3: Manual Trigger (If Menu Still Missing)

If the menu doesn't appear after deployment:

**1. Open Apps Script**
- `Extensions` → `Apps Script`

**2. Run onOpen Manually**
- Select `onOpen` function from dropdown
- Click "Run" button (▶️)

**3. Authorize**
- First time: Grant permissions as prompted

**4. Check Spreadsheet**
- Go back to spreadsheet tab
- Menu should now appear

---

## Troubleshooting

### Issue: "Authorization required" won't go away
**Fix**: Add required OAuth scopes to `appsscript.json`:
```json
{
  "timeZone": "Europe/London",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/script.external_request"
  ]
}
```

### Issue: Menu appears but "Run Search" doesn't work
**Check**:
1. API endpoint URL in `search_interface.gs` line 12:
   ```javascript
   var API_ENDPOINT = 'https://a92f6deceb5e.ngrok-free.app/search';
   ```
2. Verify backend is running:
   ```bash
   ps aux | grep "search_api_server\|fast_search_api"
   ```

### Issue: "TypeError: Cannot read property 'getValue' of null"
**Fix**: Ensure you're on the "Search" tab when running the search.

---

## Backend Architecture (Reference)

The search system has 3 components:

### 1. Frontend (Google Sheets)
- **File**: `search_interface.gs` (Apps Script)
- **Purpose**: Menu UI + form validation
- **Optimized**: Batch operations (17 calls → 1)

### 2. Backend API
- **File**: `search_api_server.py` or `fast_search_api.py`
- **Purpose**: Query BigQuery, return results
- **Endpoint**: Configured in line 12 of `search_interface.gs`

### 3. Dropdown Population
- **File**: `populate_search_dropdowns.py`
- **Purpose**: Pre-populate dropdown lists from BigQuery
- **Optimized**: Batch update (9 calls → 1)
- **Tables**: `Dropdowns` sheet with 1,403 BMU IDs, 64 orgs, etc.

---

## Related Python Scripts

Found 8 search-related Python files:
```
/home/george/GB-Power-Market-JJ/
├── populate_search_dropdowns.py        ← Populate dropdown lists
├── fast_search_api.py                  ← FastAPI search backend
├── search_api_server.py                ← Alternative Flask backend
├── create_search_interface.py          ← Interface builder
├── advanced_search_tool_enhanced.py    ← Enhanced search logic
├── bigquery_document_search.py         ← Document search
├── research_vlp_aggregators.py         ← VLP search
└── search_pdfs_recursive.py            ← PDF search
```

---

## Quick Reference

### Spreadsheet URL
```
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

### Search Tab Location
- Bottom tab bar → Click "Search"
- Or: All Sheets menu (⋯) → "Search"

### Expected Search Form Fields
Row 4: From Date (`B4`), To Date (`D4`)  
Row 5: BMU ID (`B5`)  
Row 6: Organization (`B6`)  
Row 7: Fuel Type (`B7`)  
Row 8: GSP Group (`B8`)  
Row 9: DNO Operator (`B9`)  
Row 10-17: Additional filters

### Test Backend Connectivity
Menu: `🔍 Search Tools` → `🔧 Test API Connection`

---

## Next Steps

1. ✅ **Verify Deployment**
   - Open spreadsheet
   - Check for `🔍 Search Tools` menu
   - If missing, follow Solution 1 above

2. ✅ **Test Search**
   - Go to "Search" tab
   - Fill in at least one search field
   - Click `🔍 Search Tools` → `🔍 Run Search`
   - Results should appear below row 20

3. ✅ **Verify Backend**
   ```bash
   # Check if search API is running
   ps aux | grep search_api
   
   # If not running, start it:
   cd /home/george/GB-Power-Market-JJ
   python3 search_api_server.py &
   ```

4. ✅ **Update Dropdowns** (if needed)
   ```bash
   python3 populate_search_dropdowns.py
   ```

---

## Support Files Created

This diagnostics generated the following reference files:

1. **SEARCH_DIAGNOSTICS_REPORT.md** ← This file
2. **FIX_APPS_SCRIPT_PERMISSIONS.md** ← OAuth scope fixes
3. **PERFORMANCE_OPTIMIZATION_COMPLETE.md** ← Performance details

---

## Summary

| Component | Status | Action Required |
|-----------|--------|----------------|
| Search code file | ✅ EXISTS | None - file is complete |
| Search sheet tab | ✅ EXISTS | None - tab is present |
| Menu code | ✅ COMPLETE | None - onOpen() is correct |
| Apps Script deployment | ❓ UNKNOWN | Check/deploy (Solution 1) |
| Backend API | ❓ UNKNOWN | Verify running |

**Most Likely Issue**: Search code not deployed to Google Sheets bound script.

**Resolution Time**: 5-10 minutes (follow Solution 1)

---

**Questions? Check**:
- FIX_APPS_SCRIPT_PERMISSIONS.md (OAuth issues)
- FINAL_TODOS_AND_STATUS.md (optimization status)
- PROJECT_CONFIGURATION.md (system architecture)

**Last Updated**: 1 January 2026
