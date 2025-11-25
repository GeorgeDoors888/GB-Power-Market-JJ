# Authorization Error Fix

## ❌ Error Message
```
Exception: Specified permissions are not sufficient to call Ui.showSidebar. 
Required permissions: https://www.googleapis.com/auth/script.container.ui
```

## ✅ Solution: Add OAuth Scopes

### Option 1: Add appsscript.json (Recommended)

1. In Apps Script Editor, click **Project Settings** (⚙️ icon on left)
2. Check "Show 'appsscript.json' manifest file in editor"
3. Go back to **Editor** view
4. You should see `appsscript.json` file
5. Replace its contents with:

```json
{
  "timeZone": "Europe/London",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets.currentonly",
    "https://www.googleapis.com/auth/script.container.ui"
  ]
}
```

6. Click **Save** (💾)

### Option 2: Re-authorize with Updated Scopes

1. In Apps Script Editor, click **Run** → **onOpen**
2. You'll see authorization dialog
3. Click **Review Permissions**
4. Choose your Google account
5. Click **Advanced** → **Go to [Project Name] (unsafe)**
6. Click **Allow**

### What These Scopes Do:

- **spreadsheets.currentonly**: Read/write access to THIS spreadsheet only
- **script.container.ui**: Display custom UI elements (sidebar, dialogs, menus)

## 🔄 After Authorization:

1. Close Apps Script editor
2. **Refresh** your Dashboard spreadsheet
3. Menu **🗺️ Constraint Map** should appear
4. Click **📍 Show Interactive Map**
5. Sidebar should open with map

## 🆘 If Still Not Working:

### Clear Previous Authorization:
1. Go to: https://myaccount.google.com/permissions
2. Find your Apps Script project
3. Click **Remove Access**
4. Go back to Apps Script editor
5. Run **onOpen** again
6. Re-authorize with new permissions

### Check Project Settings:
1. Apps Script Editor → **Project Settings** (⚙️)
2. Verify "Show 'appsscript.json'" is checked
3. Verify manifest file exists with correct scopes

### Verify Execution:
1. Click **Executions** (⏱️ icon on left)
2. Check recent executions for errors
3. Look for "Authorization Required" or "Permission Denied"

## ✅ Success Indicators:

- [ ] No authorization errors in Executions log
- [ ] Menu "🗺️ Constraint Map" visible in spreadsheet
- [ ] Clicking menu items doesn't show permission errors
- [ ] Sidebar opens when clicking "Show Interactive Map"
- [ ] Map displays with UK boundaries

## 📝 Files to Update:

1. **constraint_map.gs** - Add `@OnlyCurrentDoc` comment at top
2. **appsscript.json** - Add OAuth scopes (create if doesn't exist)

## 🔐 Security Note:

The `@OnlyCurrentDoc` directive limits script access to ONLY the current spreadsheet, not all your Google Drive files. This is the most restrictive permission level.

---

**Once authorized, the map should work perfectly!** The authorization is one-time only.
