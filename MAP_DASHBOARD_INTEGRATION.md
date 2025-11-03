# Adding GB Power Map to Google Sheets Dashboard

**Date**: 2 November 2025  
**Status**: ✅ Map uploaded to Google Drive

---

## ✅ What's Done

### Map Uploaded to Google Drive
- **File**: `gb_power_complete_map.html` (3.7 MB)
- **Google Drive Link**: https://drive.google.com/file/d/11GUMs_sEZ3i5LBjS21ebssV9PtqXNofQ/view
- **File ID**: `11GUMs_sEZ3i5LBjS21ebssV9PtqXNofQ`
- **Permissions**: Anyone with the link can view
- **Auto-updates**: Re-run `python3 add_map_to_dashboard.py` to upload latest version

---

## 📝 How to Add to Your Google Sheets Dashboard

### Option 1: Add Hyperlink (Recommended)

1. **Open your Google Sheet**
   - Go to your UK Power Market dashboard

2. **Find a good location** (e.g., below your existing data, row 40+)

3. **Add a section header**:
   ```
   === 🗺️ POWER SYSTEM MAPS ===
   ```

4. **Add the map link**:
   - In column A: `GB Power Complete Map`
   - In column B: Add this as a hyperlink or formula:
   ```
   =HYPERLINK("https://drive.google.com/file/d/11GUMs_sEZ3i5LBjS21ebssV9PtqXNofQ/view", "Click to View Map")
   ```

5. **Add description**:
   ```
   Row 1: Map Name | Link
   Row 2: GB Power Complete Map | [link]
   Row 3: Description: | Interactive map showing:
   Row 4:              | • 14 DNO boundaries
   Row 5:              | • 18 GSP flow points (live)
   Row 6:              | • 35 offshore wind farms (14.3 GW)
   Row 7:              | • 8,653 power stations (CVA + SVA)
   Row 8: Last Updated: | 2 November 2025
   ```

---

### Option 2: Create Dedicated "Maps" Sheet

1. **Create new sheet** in your Google Sheets workbook
   - Click the + button at bottom
   - Name it: `Power Maps`

2. **Add this content**:

```
A1: GB POWER SYSTEM MAPS
(Format: Bold, Large, Blue background)

A3: 📊 Available Maps

A5: Map Name | Description | Link | Last Updated
A6: GB Power Complete Map | Complete view with all layers | [hyperlink] | 2 Nov 2025

A8: 📈 Map Details

A10: Layer | Count | Data Source
A11: DNO Boundaries | 14 regions | dno_regions.geojson  
A12: GSP Flow Points | 18 points | bmrs_indgen + bmrs_inddem (live)
A13: Offshore Wind | 35 farms (14.3 GW) | offshore_wind_farms table
A14: CVA Plants | 1,581 sites | cva_plants table
A15: SVA Generators | 7,072 sites | sva_generators_with_coords table

A17: 🎯 Features
A18: • Interactive toggle controls for each layer
A19: • Click any element for detailed information
A20: • Real-time GSP generation vs demand data
A21: • Color-coded by fuel type and flow status
A22: • Marker clustering for performance

A24: 🔄 To Update Map
A25: 1. Run: python3 create_complete_gb_power_map.py
A26: 2. Run: python3 add_map_to_dashboard.py (uploads to Drive)
```

3. **Insert the hyperlink** in cell C6:
   ```
   =HYPERLINK("https://drive.google.com/file/d/11GUMs_sEZ3i5LBjS21ebssV9PtqXNofQ/view", "View Map")
   ```

---

### Option 3: Embed via Google Sites (Advanced)

If you want to embed the interactive map directly:

1. **Create a Google Site** (sites.google.com)
2. **Add an Embed block**
3. **Upload the HTML file** or embed via Google Drive
4. **Link to the Google Site** from your sheet

*Note: Google Sheets can't directly embed interactive HTML/JavaScript*

---

## 🔄 Update Workflow

### When GSP Data Changes (Every 30 Minutes)

The map automatically queries the latest settlement period from BigQuery, so:
- **No action needed** for GSP flow updates
- Just refresh the map page in browser

### When You Want Latest Generator Data

1. Regenerate the map:
   ```bash
   python3 create_complete_gb_power_map.py
   ```

2. Upload to Google Drive:
   ```bash
   python3 add_map_to_dashboard.py
   ```

3. The link stays the same, so no need to update your sheet!

---

## 📊 What's in the Map

| Layer | Count | Update Frequency |
|-------|-------|------------------|
| **DNO Boundaries** | 14 | Static (manual update) |
| **GSP Flow Points** | 18 | Live (every 30 mins from BMRS) |
| **Offshore Wind** | 35 | Static (manual update) |
| **CVA Plants** | 1,581 | Static (quarterly update) |
| **SVA Generators** | 7,072 | Static (quarterly update) |

**Total Elements**: 8,720 data points on one map!

---

## 🎮 How to Use the Map

### Controls (Top Left Panel)
- ☑️ Toggle each layer on/off
- See live statistics

### Interaction
- **Zoom**: Mouse wheel or +/- buttons
- **Pan**: Click and drag
- **Click any element**: See detailed popup
  - GSP circles → Generation, demand, net flow
  - Generators → Name, type, fuel, capacity
  - DNO boundaries → Region name and details
  - Offshore wind → Capacity, location, GSP zone

### Legend (Bottom Right)
- Color coding for all elements
- GSP: Blue (exporter) / Orange (importer)
- Fuels: Wind, Solar, Gas, Biomass, Nuclear, etc.

---

## 📁 Files Reference

### On Your Computer
```
gb_power_complete_map.html              # The map (3.7 MB)
create_complete_gb_power_map.py         # Generator script (15 KB)
add_map_to_dashboard.py                 # Upload script (new!)
GB_POWER_COMPLETE_MAP_DOCS.md           # Full documentation (15 KB)
GB_POWER_MAP_QUICK_REF.md              # Quick reference (4 KB)
MAP_DASHBOARD_INTEGRATION.md           # This file
```

### On Google Drive
```
gb_power_complete_map.html              # Shareable link version
File ID: 11GUMs_sEZ3i5LBjS21ebssV9PtqXNofQ
```

---

## 🐛 Troubleshooting

### Map Link Doesn't Work
- Check the link is correct
- Ensure file permissions set to "Anyone with link can view"
- Try opening the link in a new incognito window

### Map Shows Old Data
1. Regenerate: `python3 create_complete_gb_power_map.py`
2. Upload: `python3 add_map_to_dashboard.py`
3. Hard refresh in browser (Cmd+Shift+R on Mac)

### Can't See Map in Google Sheets
- Google Sheets can't embed interactive HTML directly
- Use hyperlinks to open map in new tab/window
- Consider using Google Sites for embedding

### File Size Too Large
- Current file: 3.7 MB (acceptable for Google Drive)
- If issues, reduce generator limit in script
- Or create multiple smaller maps by region

---

## ✅ Next Steps

1. **Add the link to your Google Sheet** using Option 1 or 2 above
2. **Share the Google Drive link** with colleagues who need access
3. **Bookmark the link** for quick access
4. **Update regularly** using the workflow above

---

## 📞 Support

### Quick Commands
```bash
# Regenerate map with latest data
python3 create_complete_gb_power_map.py

# Upload to Google Drive
python3 add_map_to_dashboard.py

# Open map locally
open gb_power_complete_map.html
```

### Documentation
- Full docs: `GB_POWER_COMPLETE_MAP_DOCS.md`
- Quick ref: `GB_POWER_MAP_QUICK_REF.md`
- Integration: `MAP_DASHBOARD_INTEGRATION.md` (this file)

---

**Last Updated**: 2 November 2025  
**Map Link**: https://drive.google.com/file/d/11GUMs_sEZ3i5LBjS21ebssV9PtqXNofQ/view  
**Status**: ✅ Ready to add to dashboard
