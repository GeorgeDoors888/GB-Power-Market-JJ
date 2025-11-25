
# Interactive Constraint Map Installation Guide

## 📍 What This Provides

An **embedded interactive map** inside the Dashboard sheet that displays:
- ✅ Transmission boundary constraints with live utilization data
- ✅ Color-coded by status (🟢🟡🟠🔴)
- ✅ DNO license areas, TNUoS zones, GSP regions
- ✅ Interactive popups with flow/limit/margin details
- ✅ Auto-refreshes every 5 minutes from BigQuery
- ✅ Opens in sidebar (stays within Google Sheets)

## 🚀 Installation Steps

### Step 1: Open Apps Script Editor
1. Open your Dashboard spreadsheet
2. Click: **Extensions → Apps Script**
3. This opens the script editor

### Step 2: Add Main Script
1. In Apps Script editor, delete any existing code
2. Copy entire contents from: `dashboard/apps-script/constraint_map.gs`
3. Paste into the editor
4. File name: `Code.gs` (default)

### Step 3: Add HTML Template
1. Click: **File → New → HTML file**
2. Name it: `ConstraintMap`
3. Copy entire contents from: `dashboard/apps-script/constraint_map.html`
4. Paste and save

### Step 4: Save & Authorize
1. Click the **Save** icon (💾)
2. Click: **Run → onOpen**
3. Authorize the script (first time only)
   - Click "Review Permissions"
   - Choose your Google account
   - Click "Advanced" → "Go to [Project Name] (unsafe)"
   - Click "Allow"

### Step 5: Test the Map
1. Close Apps Script editor
2. Refresh your spreadsheet
3. You'll see new menu: **🗺️ Constraint Map**
4. Click: **🗺️ Constraint Map → 📍 Show Interactive Map**
5. Map opens in right sidebar!

## 🎨 Map Features

### Color Coding
- 🟢 **Green**: <50% utilization (Normal)
- 🟡 **Yellow**: 50-75% utilization (Moderate)
- 🟠 **Orange**: 75-90% utilization (High)
- 🔴 **Red**: >90% utilization (Critical)

### Layer Controls
- ☑️ **Boundaries**: Transmission constraint boundaries
- ☑️ **DNO**: Distribution Network Operator areas
- ☑️ **TNUoS**: Transmission Network Use of System zones
- ☐ **GSP**: Grid Supply Point regions

### Data Updates
- Reads constraint data from Dashboard rows 116-126
- Updates automatically when `update_constraints_dashboard_v2.py` runs
- Manual refresh: Click **🔄 Refresh Map Data** in menu

## 🔧 Troubleshooting

### Map doesn't show
- Ensure both `Code.gs` and `ConstraintMap.html` are saved
- Refresh the spreadsheet
- Check that menu item appears: **🗺️ Constraint Map**

### No data displayed
- Run: `python3 update_constraints_dashboard_v2.py`
- Check Dashboard rows 116-126 have constraint data
- Wait 30 seconds and refresh map

### Authorization error
- Re-run: **Run → onOpen** in Apps Script
- Complete authorization flow again

## 📝 Notes

- Map reads live data from Dashboard sheet (no external APIs needed)
- Works offline once cached
- GeoJSON files embedded in HTML (no external loading)
- Google Maps API key required (free tier sufficient)

## 🆘 Support

If issues persist:
1. Check Dashboard rows 116-126 contain data
2. Verify `update_constraints_dashboard_v2.py` runs successfully
3. Check Apps Script execution logs: **View → Logs**
