# Fix Apps Script Permissions Error

## Error Message
```
Exception: Specified permissions are not sufficient to call ScriptApp.getProjectTriggers. 
Required permissions: https://www.googleapis.com/auth/script.scriptapp
```

## Root Cause
The Apps Script project needs additional OAuth scopes to access `ScriptApp.getProjectTriggers()`.

## Fix 1: Add OAuth Scopes via Apps Script Editor (EASIEST)

1. **Open Apps Script Editor**:
   - Go to your [Google Sheet](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)
   - Click: **Extensions → Apps Script**

2. **Add Manifest File** (if not visible):
   - Click gear icon ⚙️ (Project Settings)
   - Check: **"Show "appsscript.json" manifest file in editor"**

3. **Edit `appsscript.json`**:
   ```json
   {
     "timeZone": "Europe/London",
     "dependencies": {},
     "exceptionLogging": "STACKDRIVER",
     "runtimeVersion": "V8",
     "oauthScopes": [
       "https://www.googleapis.com/auth/spreadsheets",
       "https://www.googleapis.com/auth/script.scriptapp"
     ]
   }
   ```

4. **Save and Re-authorize**:
   - Click: **Save** (Ctrl+S)
   - Run any function from menu: **🔍 Search Tools → 🔍 Run Search**
   - Click: **Review Permissions** → **Advanced** → **Go to [Project Name]** → **Allow**

## Fix 2: Remove Trigger Code (ALTERNATIVE - If you don't need triggers)

If you don't actually need `ScriptApp.getProjectTriggers()`, remove those lines:

**Find and remove/comment out**:
```javascript
// Remove these lines if not needed:
var triggers = ScriptApp.getProjectTriggers();
ScriptApp.deleteTrigger(trigger);
```

## Fix 3: Via CLASP (Command Line)

If using CLASP for deployment:

1. **Edit appsscript.json**:
   ```bash
   cd /home/george/GB-Power-Market-JJ/clasp-gb-live-2/src
   nano appsscript.json
   ```

2. **Add oauthScopes**:
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
     "exceptionLogging": "STACKDRIVER",
     "runtimeVersion": "V8",
     "oauthScopes": [
       "https://www.googleapis.com/auth/spreadsheets",
       "https://www.googleapis.com/auth/script.scriptapp",
       "https://www.googleapis.com/auth/script.external_request"
     ]
   }
   ```

3. **Push to Apps Script**:
   ```bash
   cd /home/george/GB-Power-Market-JJ/clasp-gb-live-2
   clasp push
   ```

4. **Re-authorize in browser**:
   - Open Google Sheets
   - Run any menu function
   - Grant new permissions

## Common OAuth Scopes for Apps Script

```json
"oauthScopes": [
  "https://www.googleapis.com/auth/spreadsheets",           // Read/write sheets
  "https://www.googleapis.com/auth/script.scriptapp",       // Manage triggers
  "https://www.googleapis.com/auth/script.external_request", // UrlFetchApp
  "https://www.googleapis.com/auth/bigquery.readonly",      // BigQuery (if needed)
  "https://www.googleapis.com/auth/drive.readonly"          // Drive access (if needed)
]
```

## Verification

After fixing, test by running:
```javascript
function testPermissions() {
  var triggers = ScriptApp.getProjectTriggers();
  Logger.log('✅ Triggers accessible: ' + triggers.length + ' triggers found');
}
```

Run from Apps Script editor: **Select `testPermissions` → Click Run ▶️**

Should show: `✅ Triggers accessible: X triggers found`

---

## Related: Where is the Search Function?

The search interface is in:
- **File**: `search_interface.gs` 
- **Location**: Apps Script editor (Extensions → Apps Script)
- **Menu**: 🔍 Search Tools (appears in Google Sheets top menu after `onOpen()` runs)

If menu not visible:
1. Refresh Google Sheets
2. Or manually run: **Apps Script Editor → Select `onOpen` → Run ▶️**

---

*Last Updated: January 1, 2026*
