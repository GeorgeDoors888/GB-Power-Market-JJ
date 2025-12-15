# Apps Script Deployment Guide

## ❌ Common Error: "Sorry, unable to open the file"

**This happens when accessing the Web App URL directly in a browser.**

### Why It Fails:
The map uses `google.script.run.getConstraintData()` which **only works inside Google Sheets**, not as a standalone web page.

## ✅ Correct Way to Access the Map

### Method 1: From Google Sheets (RECOMMENDED)

1. Open your **Dashboard spreadsheet**: 
   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

2. Look for menu: **🗺️ Constraint Map**
   
3. Click: **📍 Show Interactive Map**

4. Map opens in **right sidebar** with live data

### Method 2: If Menu Doesn't Appear

1. Open Dashboard spreadsheet
2. Go to: **Extensions** → **Apps Script**
3. In the script editor, click: **Run** → **onOpen**
4. Authorize when prompted
5. Close Apps Script editor
6. Refresh spreadsheet
7. Menu should now appear

## 🔧 Installation Steps (If Not Already Installed)

### Step 1: Open Apps Script Editor
1. Open your Dashboard spreadsheet
2. Click: **Extensions** → **Apps Script**

### Step 2: Add Main Script
1. Rename `Code.gs` (if default file exists)
2. Copy all code from: `dashboard/apps-script/constraint_map.gs`
3. Paste into the editor

### Step 3: Add HTML File
1. Click: **+** (Add a file) → **HTML**
2. Name it: **ConstraintMap** (exact name, no spaces)
3. Copy all code from: `dashboard/apps-script/constraint_map.html`
4. Paste into the HTML file

### Step 4: Save and Authorize
1. Click: **Save** (💾 icon)
2. Click: **Run** → **onOpen**
3. Review permissions when prompted
4. Click: **Allow**

### Step 5: Test
1. Close Apps Script editor
2. Refresh your Dashboard spreadsheet
3. Look for menu: **🗺️ Constraint Map**
4. Click: **📍 Show Interactive Map**
5. Map should open in sidebar

## 🎯 What You Should See

When working correctly:
- ✅ Menu "🗺️ Constraint Map" appears in menu bar
- ✅ Clicking "Show Interactive Map" opens sidebar
- ✅ Map displays UK with constraint boundaries
- ✅ Circles are color-coded (🟢🟡🟠🔴)
- ✅ Clicking circles shows popup with flow/limit data
- ✅ "Updated: [time]" shows in top right

## 🚫 Web App URL (Don't Use Directly)

The deployment URLs are for Apps Script infrastructure only:
- Version 7: `AKfycbyq7s0Ga37EV8HY1nrsV0Zt2bNgBIPClTbrt7kL0W1k_tqhCMeEodZvZIRNqiLOzTCA`
- Version 8: `AKfycbw5DSYuky8TrsgMPOsl-arEdQ96gnYHd19f9W6KdUIdbsXJpfH5zlYu8mWNPh1OmcY9`

**These URLs will show an error when opened directly** because they need to run within Google Sheets context.

## 🔄 To Deploy as Standalone Web App (Advanced)

If you want a standalone version, you need to modify `doGet()` function:

```javascript
function doGet() {
  return HtmlService.createHtmlOutputFromFile('ConstraintMap')
    .setTitle('GB Transmission Constraints')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
```

Then data needs to come from a different source (not `google.script.run`).

## 📊 Current Data Flow

```
BigQuery
  ↓
update_constraints_dashboard_v2.py (every 5 min)
  ↓
Dashboard Sheet Rows 116-126
  ↓
Apps Script getConstraintData() ← REQUIRES SHEETS CONTEXT
  ↓
constraint_map.html (displays in sidebar)
```

## 🆘 Troubleshooting

### "Menu doesn't appear"
- Run `onOpen()` in Apps Script editor
- Refresh spreadsheet
- Check authorization permissions

### "Map shows error message"
- Verify Dashboard rows 116-126 contain data
- Run: `python3 update_constraints_dashboard_v2.py`
- Wait 30 seconds, refresh map

### "Authorization error"
- Apps Script needs permission to read spreadsheet
- Click "Review permissions" → "Allow"
- Don't use incognito mode

### "Map is blank"
- Check browser console (F12) for errors
- Verify Google Maps API key is valid
- Check API key has "Maps JavaScript API" enabled

## ✅ Success Checklist

- [ ] Apps Script files installed (constraint_map.gs + ConstraintMap.html)
- [ ] onOpen() function executed
- [ ] Permissions authorized
- [ ] Menu "🗺️ Constraint Map" visible
- [ ] Map opens in sidebar (not new window)
- [ ] Constraint circles visible on map
- [ ] Clicking circles shows data popup
- [ ] Data updates from Dashboard rows 116-126

---

**Remember**: Access from **Dashboard → Menu → Show Interactive Map**, not from the deployment URL!
