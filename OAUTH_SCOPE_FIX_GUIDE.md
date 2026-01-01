# OAuth Scope Fix Guide - Apps Script Permissions

## 🔴 ISSUE IDENTIFIED

**Error Message:**
```
Specified permissions are not sufficient to call UrlFetchApp.fetch. 
Required permissions: https://www.googleapis.com/auth/script.external_request
```

**Root Cause:** The `appsscript.json` manifest is missing required OAuth scopes for external API calls and BigQuery access.

---

## 📋 Current vs Required Scopes

### ❌ Current Scopes (INCOMPLETE)
```json
{
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets.currentonly",
    "https://www.googleapis.com/auth/script.container.ui"
  ]
}
```

**Problems:**
1. ❌ `spreadsheets.currentonly` - Too restrictive (only active sheet)
2. ❌ Missing `script.external_request` - Can't call external APIs
3. ❌ Missing `bigquery` - Can't query BigQuery

### ✅ Required Scopes (COMPLETE)
```json
{
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/script.container.ui",
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/script.external_request"
  ]
}
```

**Each scope enables:**
1. ✅ `spreadsheets` - Full read/write access to all sheets in workbook
2. ✅ `script.container.ui` - Show dialogs, sidebars, custom menus
3. ✅ `bigquery` - Execute BigQuery queries (for map sidebar GeoJSON)
4. ✅ `script.external_request` - Call external APIs via UrlFetchApp.fetch()

---

## 🛠️ FIX INSTRUCTIONS

### Method 1: Manual Update (Recommended for Google Sheets Editor)

**Step 1: Open Apps Script Manifest**
```
1. In Google Sheets: Extensions → Apps Script
2. View → Show manifest file (if not already visible)
3. Click on appsscript.json in left sidebar
```

**Step 2: Replace OAuth Scopes**
```json
// Find the "oauthScopes" array and replace with:
"oauthScopes": [
  "https://www.googleapis.com/auth/spreadsheets",
  "https://www.googleapis.com/auth/script.container.ui",
  "https://www.googleapis.com/auth/bigquery",
  "https://www.googleapis.com/auth/script.external_request"
]
```

**Step 3: Save and Reauthorize**
```
1. Save manifest (Command+S on Mac)
2. Select ANY function from dropdown (e.g., onOpen or showMapSidebar)
3. Click Run (▶️)
4. Click "Review Permissions"
5. Select your Google account
6. Click "Advanced" → "Go to [project name] (unsafe)"
7. Review new permissions:
   - See, edit, create, delete all spreadsheets
   - Display and run third-party web content
   - Connect to external service (BigQuery)
   - Connect to external service (APIs)
8. Click "Allow"
```

**Step 4: Test**
```
1. Close Apps Script editor
2. In Google Sheets, refresh (Command+R)
3. Try the search interface again
4. Should work without "API Connection Failed" error
```

---

### Method 2: Automated Deploy via Clasp (For Terminal Users)

**Step 1: Copy Fixed Manifest**
```bash
cd /home/george/GB-Power-Market-JJ
cp appsscript_v3/appsscript_FIXED.json appsscript_v3/appsscript.json
```

**Step 2: Deploy via Clasp**
```bash
cd appsscript_v3
clasp push
```

**Step 3: Reauthorize in Google Sheets**
```
Extensions → Apps Script → Run any function → Review Permissions → Allow
```

---

## 🔍 WHY EACH SCOPE IS NEEDED

### 1. `spreadsheets` (NOT `spreadsheets.currentonly`)
**Used by:** All scripts that read/write multiple sheets
**Example:**
- `populate_search_dropdowns.py` writes to Dropdowns sheet
- Dashboard scripts update multiple tabs
- Search interface reads from various sheets

**Why not currentonly?** It only allows access to the active sheet, blocking multi-sheet operations.

---

### 2. `script.container.ui`
**Used by:** Custom menus, sidebars, dialogs
**Example:**
```javascript
// MASTER_onOpen.gs
ui.createMenu('🗺️ Geographic Map')
  .addItem('Show DNO & GSP Boundaries', 'showMapSidebar')

// map_sidebar.gs
var html = HtmlService.createHtmlOutputFromFile('map_sidebarh')
  .setTitle('GB Power Geographic Map')
  .setWidth(400);
SpreadsheetApp.getUi().showSidebar(html);
```

**Error without it:** "Specified permissions are not sufficient to call Ui.showSidebar"

---

### 3. `bigquery`
**Used by:** BigQuery API queries in Apps Script
**Example:**
```javascript
// map_sidebar.gs - getGeoJson()
var request = {
  query: `SELECT dno_id, ST_AsGeoJSON(boundary) 
          FROM \`inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries\``,
  useLegacySql: false,
  location: 'US'
};
var queryResults = BigQuery.Jobs.query(request, PROJECT_ID);
```

**Error without it:** "BigQuery is not defined" or "Insufficient permissions"

---

### 4. `script.external_request`
**Used by:** UrlFetchApp.fetch() calls to external APIs
**Example:**
```javascript
// search_interface.gs
var API_ENDPOINT = 'https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/search_bigquery';
var response = UrlFetchApp.fetch(API_ENDPOINT, {
  method: 'POST',
  contentType: 'application/json',
  payload: JSON.stringify({ filters: searchCriteria })
});
```

**Error without it:** "Specified permissions are not sufficient to call UrlFetchApp.fetch"

**Also used by:**
- `analysis_report_generator.gs` - Webhook calls
- `btm_hh_generator.gs` - Export API calls
- `dynamic_dropdowns.gs` - Vercel proxy queries

---

## 📊 SCOPE USAGE BY FILE

| File | spreadsheets | container.ui | bigquery | external_request |
|------|--------------|--------------|----------|------------------|
| `map_sidebar.gs` | ✅ | ✅ | ✅ | ❌ |
| `search_interface.gs` | ✅ | ✅ | ❌ | ✅ |
| `MASTER_onOpen.gs` | ✅ | ✅ | ❌ | ❌ |
| `analysis_report_generator.gs` | ✅ | ✅ | ❌ | ✅ |
| `btm_hh_generator.gs` | ✅ | ✅ | ❌ | ✅ |
| `dynamic_dropdowns.gs` | ✅ | ❌ | ❌ | ✅ |

**Conclusion:** All 4 scopes are required for full functionality.

---

## 🚨 COMMON MISTAKES

### ❌ Mistake 1: Using `spreadsheets.currentonly`
```json
"https://www.googleapis.com/auth/spreadsheets.currentonly"  // TOO RESTRICTIVE
```
**Problem:** Can only access the currently active sheet, not other sheets in workbook.
**Fix:** Use `https://www.googleapis.com/auth/spreadsheets` (no .currentonly)

### ❌ Mistake 2: Forgetting to Reauthorize
After adding new scopes, you MUST reauthorize the script:
1. Run any function manually
2. Click "Review Permissions"
3. Allow new permissions

**Symptom:** Old permissions still active, new scopes not recognized.

### ❌ Mistake 3: Missing BigQuery API Enable
Even with the OAuth scope, you must enable BigQuery API:
```
Services (+) → BigQuery API → v2 → Add
```

### ❌ Mistake 4: Wrong Script Property Name
API key must be exactly: `GOOGLE_MAPS_API_KEY` (not MAPS_API_KEY or similar)

---

## ✅ VERIFICATION CHECKLIST

After applying the fix, verify each scope works:

**Test 1: Spreadsheets Scope**
```javascript
function testSpreadsheetsScope() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  Logger.log('✅ Can access ' + sheets.length + ' sheets');
}
```
Expected: Logs number of sheets without permission error.

**Test 2: Container UI Scope**
```javascript
function testUiScope() {
  SpreadsheetApp.getUi().alert('✅ UI scope works!');
}
```
Expected: Alert dialog appears.

**Test 3: BigQuery Scope**
```javascript
function testBigQueryScope() {
  var request = {
    query: 'SELECT 1 as test',
    useLegacySql: false
  };
  var result = BigQuery.Jobs.query(request, 'inner-cinema-476211-u9');
  Logger.log('✅ BigQuery scope works');
}
```
Expected: Query executes without error.

**Test 4: External Request Scope**
```javascript
function testExternalRequestScope() {
  var response = UrlFetchApp.fetch('https://www.google.com');
  Logger.log('✅ External request scope works');
}
```
Expected: HTTP request completes without permission error.

---

## 📝 SUMMARY

**The Fix (Single Line Change):**
Replace `appsscript.json` OAuth scopes with:
```json
[
  "https://www.googleapis.com/auth/spreadsheets",
  "https://www.googleapis.com/auth/script.container.ui",
  "https://www.googleapis.com/auth/bigquery",
  "https://www.googleapis.com/auth/script.external_request"
]
```

**Then reauthorize:** Run any function → Review Permissions → Allow

**Time Required:** 2-3 minutes

**Bottom Line:** Missing OAuth scope is causing the "API Connection Failed" error. Adding `script.external_request` scope will fix search interface API calls. All other scopes are needed for map sidebar and BigQuery queries.

---

*Last Updated: January 1, 2026*
*Issue: UrlFetchApp.fetch permission error in search_interface.gs*
