# Apps Script Deployment - Constraint Map

## 📋 Files in this package:

1. **Code.gs** - Main Apps Script file (30 lines)
2. **ConstraintMap_Leaflet.html** - Map with embedded data

## 🚀 Deployment Steps:

### Step 1: Open Apps Script
1. Open your Google Sheet: GB Energy Dashboard
2. Menu: **Extensions** → **Apps Script**

### Step 2: Clean Up Old Files
Delete these if they exist:
- `constraint_map.gs` (old version)
- `ConstraintMap.html` (old version)  
- `Code.gs` (if exists - we'll replace it)

### Step 3: Upload Code.gs
1. In Apps Script editor, click ➕ next to "Files"
2. Select "Script" (.gs file)
3. Name it: `Code`
4. Copy ALL content from `Code.gs` in this package
5. Paste into the Apps Script editor
6. Save (Ctrl+S / Cmd+S)

### Step 4: Upload ConstraintMap_Leaflet.html
1. In Apps Script editor, click ➕ next to "Files"
2. Select "HTML" (.html file)
3. Name it: `ConstraintMap_Leaflet` (exact name!)
4. Copy ALL content from `ConstraintMap_Leaflet.html` 
5. Paste into the Apps Script editor
6. Save (Ctrl+S / Cmd+S)

### Step 5: Deploy
1. Click **Deploy** (top right)
2. Select **New deployment**
3. Type: **Web app**
4. Description: "Constraint Map v16"
5. Execute as: **Me**
6. Who has access: **Anyone with Google account**
7. Click **Deploy**
8. Authorize if prompted

### Step 6: Test
1. **Close** your Google Sheet tab
2. **Reopen** the sheet (important!)
3. Look for menu: **🗺️ Constraint Map**
4. Click: **📍 Show Map (Leaflet - No API Key)**
5. Sidebar should show map with 10 colored markers

## ✅ Expected Result:
- Menu "🗺️ Constraint Map" appears in sheet
- Clicking menu opens sidebar
- Map displays with UK centered
- 10 colored markers visible (7 green, 3 yellow)
- Click markers to see constraint details

## ❌ Troubleshooting:

**Menu doesn't appear:**
- Close and reopen Google Sheets
- Check Apps Script: Run → onOpen function
- Look for errors in execution log

**Sidebar is blank:**
- Check HTML filename: Must be "ConstraintMap_Leaflet" exactly
- Check browser console (F12) for errors
- Verify HTML file was uploaded correctly

**"ConstraintMap_Leaflet not found":**
- HTML file not uploaded
- Wrong filename (check spelling, case-sensitive)

## 📞 Support:
If still not working, provide:
1. Screenshot of Apps Script files list
2. Browser console errors (F12 → Console tab)
3. Apps Script execution log (View → Executions)
