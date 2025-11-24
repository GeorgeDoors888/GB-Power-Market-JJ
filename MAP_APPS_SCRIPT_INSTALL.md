# 🗺️ Apps Script Installation Guide

**Final Step**: Install the interactive map code in Google Sheets

---

## 📋 Prerequisites (Already Complete ✅)

- [x] Python script tested successfully
- [x] Map data sheets populated (Map_Data_GSP, Map_Data_IC, Map_Data_DNO)
- [x] All dependencies installed
- [x] BigQuery and Sheets API working

---

## 🚀 Installation Steps (5 minutes)

### Step 1: Open Apps Script Editor

1. Open your dashboard:
   ```
   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
   ```

2. Click **Extensions → Apps Script**

3. You'll see the Apps Script editor with existing code

### Step 2: Create map_integration.gs

1. In the left sidebar, click **+** next to "Files"

2. Select **Script** (not HTML)

3. Name it: `map_integration`

4. **Copy the entire content** from your local file:
   ```
   /Users/georgemajor/GB Power Market JJ/map_integration.gs
   ```

5. **Paste** into the Apps Script editor

6. Click **Save** (💾 icon or Ctrl+S / Cmd+S)

### Step 3: Create dynamicMapView.html

1. In the left sidebar, click **+** next to "Files" again

2. This time select **HTML**

3. Name it: `dynamicMapView`

4. **Copy the entire content** from your local file:
   ```
   /Users/georgemajor/GB Power Market JJ/dynamicMapView.html
   ```

5. **Paste** into the HTML editor (replace default content)

6. Click **Save** (💾 icon)

### Step 4: Test the Installation

1. Go back to your Google Sheets tab

2. **Refresh the page** (F5 or Cmd+R)

3. You should see a new menu: **🗺️ Map Tools**

4. If you don't see it:
   - Go back to Apps Script editor
   - Click **Run** → Select `onOpen` function
   - Click **Run** button
   - Authorize the script (first time only)
   - Refresh spreadsheet again

### Step 5: Open the Map

1. Click **🗺️ Map Tools → 🌍 Open Interactive Map**

2. The map should load in a sidebar (1300x900px)

3. You should see:
   - ✅ Dark map centered on GB (lat: 54.5, lng: -3.5)
   - ✅ 3 dropdown controls at the top
   - ✅ 9 green circles (GSPs)
   - ✅ 8 interconnector lines (green/red)
   - ✅ 6 DNO boundary regions (colored polygons)
   - ✅ Legend in bottom-right corner

---

## 🧪 Verification Checklist

After opening the map, verify:

- [ ] Map loads in sidebar (not full screen)
- [ ] Map is dark themed (blue tones, not standard Google Maps)
- [ ] DNO dropdown works (try "UKPN" - should filter to London area)
- [ ] Overlay dropdown works (try "Demand Heatmap" - circles change color)
- [ ] Interconnector dropdown works (try "Imports" - only green lines show)
- [ ] Click on a GSP circle - tooltip appears with data
- [ ] Click on an IC line - tooltip shows flow details
- [ ] Click on a DNO region - tooltip shows region info
- [ ] Legend updates when changing overlays
- [ ] No JavaScript errors in browser console (F12)

---

## 🎮 Quick Feature Test

### Test 1: DNO Filtering
1. Select **DNO Region: UKPN**
2. Result: Map should zoom to London/East Anglia area
3. Result: Only GSPs N and B9 visible

### Test 2: Demand Heatmap
1. Select **Overlay: Demand Heatmap**
2. Result: GSP circles change color based on load
3. Result: Legend updates to show color scale

### Test 3: Interconnector Filtering
1. Select **Interconnectors: Imports**
2. Result: Only green lines visible (IFA, NSL, ElecLink)
3. Result: Red export lines hidden

### Test 4: Interactive Tooltips
1. Click on London Core GSP (big circle in center)
2. Result: Tooltip shows:
   ```
   London Core
   GSP ID: N
   Load: 1,235.0 MW
   Generation: 27,867.0 MW
   Frequency: 50.00 Hz
   Region: UKPN
   ```

---

## 🐛 Troubleshooting

### Problem: Menu "🗺️ Map Tools" doesn't appear

**Solution 1**: Manually run onOpen()
```
1. Apps Script editor
2. Select "onOpen" function from dropdown
3. Click "Run" button
4. Refresh spreadsheet
```

**Solution 2**: Check authorization
```
1. Apps Script editor → Run onOpen
2. Click "Review permissions"
3. Choose your Google account
4. Click "Advanced" → "Go to [project name] (unsafe)"
5. Click "Allow"
```

### Problem: Map shows blank/white screen

**Solution**: Check browser console
```
1. Press F12 (or Cmd+Option+I on Mac)
2. Click "Console" tab
3. Look for error messages
4. Common issues:
   - "google.script.run is not defined" → Map opened outside sidebar
   - "Map_Data_GSP not found" → Run refresh_map_data.py first
```

### Problem: No data on map (empty circles)

**Solution**: Re-run data refresh
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 refresh_map_data.py
```

Then refresh the map:
```
🗺️ Map Tools → 📊 Refresh Map Data
```

### Problem: Dropdowns don't filter data

**Solution**: Check Apps Script logs
```
1. Apps Script editor
2. Click "Executions" (⏱️ icon in left sidebar)
3. Look for errors in getRegionalMapData function
4. Check that Map_Data_* sheets have data
```

---

## 📊 Expected Data in Sheets

After successful installation, your sheets should have:

### Map_Data_GSP
```
9 rows + header
Columns: GSP_ID | Name | Latitude | Longitude | DNO_Region | Load_MW | etc.
Example: N | London Core | 51.51 | -0.13 | UKPN | 1,235.0 | ...
```

### Map_Data_IC
```
8 rows + header
Columns: IC_Name | Country | Flow_MW | Start_Lat | End_Lat | etc.
Example: IFA | France | 1,509 | 50.85 | 49.8 | ...
```

### Map_Data_DNO
```
6 rows + header
Columns: DNO_Name | Boundary_Coordinates_JSON | Color_Hex | etc.
Example: UKPN | [{"lat":51.3,"lng":-0.5},...] | #29B6F6 | ...
```

---

## ⚙️ Optional: Add to Menu Permanently

To make the map available to all users:

1. Apps Script editor
2. Click "Deploy" → "New deployment"
3. Select type: "Add-on"
4. Set name: "GB Energy Map"
5. Click "Deploy"

Note: This makes the menu persistent across all sessions.

---

## 🔄 Data Refresh Schedule

### Manual Refresh (Anytime)
```
Option 1: From menu
🗺️ Map Tools → 📊 Refresh Map Data

Option 2: From terminal
python3 refresh_map_data.py
```

### Auto-Refresh (Optional)
Set up cron on server (94.237.55.234):
```bash
# Every 15 minutes
*/15 * * * * cd /opt/map-data && python3 refresh_map_data.py
```

---

## 📚 Next Steps After Installation

1. ✅ Test all dropdown combinations
2. ✅ Verify tooltips show correct data
3. ✅ Check legend updates properly
4. 📖 Read full docs: `ENERGY_DASHBOARD_MAPS_INTEGRATION.md`
5. 📖 Share user guide: `MAP_QUICK_REFERENCE.md`
6. 🔄 Set up auto-refresh (optional)
7. 🎨 Customize DNO colors (optional)
8. 📈 Add more GSPs (optional)

---

## ✅ Success!

When everything works, you'll have:

- 🗺️ Interactive map in Google Sheets sidebar
- 🎮 3 dropdown controls for filtering
- 📍 9 GSPs with real-time data
- 🔌 8 interconnectors with flow visualization
- 🏢 6 DNO regions with boundaries
- 🎨 5 overlay types (demand, generation, constraints, frequency)
- 📊 Live tooltips on click
- 🎯 Legend that updates dynamically

---

**Installation Time**: ~5 minutes  
**Difficulty**: Easy (copy-paste)  
**Support**: george@upowerenergy.uk

**Last Updated**: 24 November 2025
