# Map Sidebar Fix & Deployment Guide

## 🚨 Critical Update: Manual Action Required

Due to network restrictions on the deployment server, the Google Apps Script code must be updated manually to fix the "No HTML file named map_sidebarh" error.

### 1. The Issue
The Apps Script was looking for an old HTML file (`map_sidebarh.html`) that no longer existed or was named incorrectly. The code has been updated to reference the correct file (`map_sidebar_v2.html`), but these changes need to be applied to the live Apps Script project.

### 2. The Fix (3-Step Process)

You have two helper files in your repository root that contain the exact code you need.

#### Step 1: Update Server Code (`map_sidebar.gs`)
1. Open the file **`PASTE_THIS_INTO_APPS_SCRIPT_GS.js`** in this repository.
2. Copy **ALL** the content.
3. Go to the [Apps Script Editor](https://script.google.com/d/1KlgBiFBGXfub87ACCfx7y9QugHbT46Mv3bgWtpQ38FvroSTsl8CEiXUz/edit).
4. Open the file named **`map_sidebar.gs`**.
5. **Delete everything** in that file and paste the new code.
6. Save (Ctrl+S / Cmd+S).

#### Step 2: Update Client Code (`map_sidebar_v2.html`)
1. Open the file **`PASTE_THIS_INTO_APPS_SCRIPT_HTML.html`** in this repository.
2. Copy **ALL** the content.
3. Go to the Apps Script Editor.
4. Look for a file named **`map_sidebar_v2.html`**.
   - *If it doesn't exist:* Click `+` > `HTML` > Name it `map_sidebar_v2`.
5. **Delete everything** in that file and paste the new code.
6. Save.

#### Step 3: Update Manifest (`appsscript.json`)
1. In the Apps Script Editor, click the **Project Settings** (gear icon) on the left.
2. Check the box: **"Show 'appsscript.json' manifest file in editor"**.
3. Go back to the **Editor** tab.
4. Open **`appsscript.json`**.
5. Replace its content with:
   ```json
   {
     "timeZone": "Europe/London",
     "dependencies": {
       "enabledAdvancedServices": [{
         "userSymbol": "BigQuery",
         "version": "v2",
         "serviceId": "bigquery"
       }]
     },
     "exceptionLogging": "STACKDRIVER",
     "runtimeVersion": "V8"
   }
   ```
6. Save.

### 3. Verification
1. Refresh your Google Sheet.
2. Click **GB Power > Geographic Map > Show DNO & GSP Boundaries**.
3. The map sidebar should load correctly without errors.

---

## Repository Information
**Repository:** [https://github.com/GeorgeDoors888/GB-Power-Market-JJ](https://github.com/GeorgeDoors888/GB-Power-Market-JJ)
**Branch:** main
