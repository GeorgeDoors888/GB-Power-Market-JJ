# Interactive Geographic Map Sidebar - Deployment Guide

## Overview
Adds an interactive Google Maps sidebar to Google Sheets showing:
- **DNO Boundaries** (14 regions) - Blue polygons
- **GSP Boundaries** (333 regions) - Green polygons
- Click any region to see details (name, ID, area, etc.)

## Files Created
1. `map_sidebar.html` - Frontend (Google Maps interface)
2. `map_sidebar.gs` - Backend (BigQuery data fetcher)
3. `MASTER_onOpen.gs` - Updated to include map menu

## Prerequisites

### 1. Enable BigQuery API in Apps Script
1. Open Apps Script editor
2. Click ⚙️ Services (left sidebar)
3. Click "+ Add a service"
4. Select "BigQuery API"
5. Click "Add"

### 2. Get Google Maps API Key
1. Go to https://console.cloud.google.com/apis/credentials
2. Select project: `inner-cinema-476211-u9`
3. Click "Create Credentials" → "API Key"
4. Restrict key to "Maps JavaScript API"
5. Copy the API key

### 3. Add API Key to Script Properties
1. In Apps Script editor: File → Project Settings
2. Scroll to "Script Properties"
3. Click "Add script property"
4. Property name: `GOOGLE_MAPS_API_KEY`
5. Property value: [paste your API key]
6. Click "Save"

## Deployment Steps

### Step 1: Upload Files to Apps Script
1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
2. Extensions → Apps Script
3. Create `map_sidebar.html`:
   - Click + button → HTML
   - Name: `map_sidebar`
   - Paste contents from `/home/george/GB-Power-Market-JJ/map_sidebar.html`
   - Save (Ctrl+S)

4. Create `map_sidebar.gs`:
   - Click + button → Script
   - Name: `map_sidebar`
   - Paste contents from `/home/george/GB-Power-Market-JJ/map_sidebar.gs`
   - Save (Ctrl+S)

5. Update `MASTER_onOpen.gs`:
   - Find existing file
   - Replace contents with updated version from `/home/george/GB-Power-Market-JJ/MASTER_onOpen.gs`
   - Save (Ctrl+S)

### Step 2: Test BigQuery Connection
1. In Apps Script editor, select `map_sidebar.gs`
2. Select function: `testGeoJsonFetch`
3. Click "Run" ▶️
4. Check Execution log (View → Logs)
5. Should see:
   ```
   Testing DNO GeoJSON fetch...
   DNO features: 14
   Testing GSP GeoJSON fetch...
   GSP features: 333
   ✅ Test complete
   ```

### Step 3: Deploy Menu
1. Close Apps Script editor
2. Refresh Google Sheets (F5)
3. New menu should appear: **🗺️ Geographic Map**
4. Click: **Show DNO & GSP Boundaries**
5. Sidebar opens on right side

### Step 4: Use the Map
**Buttons:**
- **🗺️ Show DNO Regions** - Display 14 DNO licence areas (blue)
- **📍 Show GSP Regions** - Display 333 GSP substations (green)
- **🌍 Show Both Layers** - Display both DNO + GSP overlayed
- **🧹 Clear Map** - Remove all layers

**Interactions:**
- Click any polygon to see details in info box
- Zoom/pan map as normal
- Map auto-fits bounds when layer loads

## Data Sources

### DNO Boundaries
**Table**: `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`  
**Columns**:
- `dno_id` - DNO identifier
- `dno_name` - Full DNO name (e.g., "UK Power Networks (London)")
- `dno_short_code` - Short code (e.g., "LPN")
- `gsp_group_id` - GSP Group code (_A to _P)
- `region_name` - Geographic region name
- `boundary` - GEOGRAPHY polygon

**Sample**: 14 DNO licence areas covering all of GB

### GSP Boundaries
**Table**: `inner-cinema-476211-u9.uk_energy_prod.neso_gsp_boundaries`  
**Columns**:
- `gsp_id` - GSP identifier (e.g., "GSP_133")
- `gsp_name` - GSP name (e.g., "GSP 133")
- `gsp_group` - Parent GSP Group code
- `region_name` - Geographic region
- `area_sqkm` - Area in square kilometers
- `boundary` - GEOGRAPHY polygon

**Sample**: 333 individual Grid Supply Point boundaries

## Troubleshooting

### "No Maps API key set in Script Properties"
**Solution**: Follow step "3. Add API Key to Script Properties" above

### "BigQuery error: Access Denied"
**Solution**: 
1. Check BigQuery API is enabled in Apps Script Services
2. Verify project ID is correct: `inner-cinema-476211-u9`
3. Ensure tables exist: `neso_dno_boundaries`, `neso_gsp_boundaries`

### "No data returned"
**Solution**: Check if BigQuery tables have GEOGRAPHY data:
```sql
SELECT COUNT(*) 
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`
WHERE boundary IS NOT NULL
```

### Map doesn't load
**Solution**:
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify Maps API key has "Maps JavaScript API" enabled
4. Check API key restrictions don't block domain

### Polygons don't appear
**Solution**:
1. Click "Clear Map" then reload layer
2. Check Execution log in Apps Script for errors
3. Verify GeoJSON format is valid (run `testGeoJsonFetch()`)

## Customization

### Change Map Colors
Edit `map_sidebar.html`, find:
```javascript
map.data.setStyle((feature) => {
  const type = feature.getProperty('layer_type');
  
  if (type === 'dno') {
    return {
      fillColor: '#4285f4',  // Change DNO color
      fillOpacity: 0.25,
      strokeColor: '#1a73e8',
      strokeWeight: 2
    };
  }
```

### Add More Layers
1. Add button to HTML:
   ```html
   <button onclick="loadLayer('generators')">⚡ Show Generators</button>
   ```

2. Add query to `map_sidebar.gs`:
   ```javascript
   } else if (layer === 'generators') {
     query = `
       SELECT 
         bmu_id,
         lead_party_name,
         fuel_type_category,
         ST_AsGeoJSON(ST_GEOGPOINT(longitude, latitude)) as geometry_json
       FROM \`${PROJECT_ID}.${DATASET}.ref_bmu_generators\`
       WHERE longitude IS NOT NULL AND latitude IS NOT NULL
     `;
   }
   ```

### Change Default Center/Zoom
Edit `map_sidebar.html`:
```javascript
map = new google.maps.Map(document.getElementById('map'), {
  zoom: 6,              // Adjust zoom level
  center: { lat: 54.5, lng: -3.5 },  // Adjust center point
```

## Performance Notes
- **DNO Layer**: Fast (~14 polygons, loads <1 second)
- **GSP Layer**: Moderate (~333 polygons, loads 2-3 seconds)
- **Both Layers**: Moderate (loads sequentially, 3-5 seconds total)

## Future Enhancements
1. Add generator locations as markers (colored by fuel type)
2. Add TEC projects from Connections 360 (once ingested)
3. Add search/filter for specific regions
4. Add legend showing layer colors
5. Export selected region data to sheet
6. Add heat maps for capacity/generation

## Related Files
- `SEARCH_DROPDOWN_FIXES_SUMMARY.md` - Dropdown enhancement docs
- `PROJECT_CONFIGURATION.md` - BigQuery configuration
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Table schemas

---

**Status**: ✅ Ready for deployment  
**Last Updated**: January 1, 2026
