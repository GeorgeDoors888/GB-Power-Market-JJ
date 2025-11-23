# 🗺️ GeoJSON Boundary Maps - Complete

## ✅ What Was Created

### New Boundary-Based Maps (Using GeoJSON Files)

**1. DNO Boundary Map** (`map_dno_boundaries.html`)
- **Features**: 14 colored regions showing Distribution Network Operator zones
- **Data Source**: `official_dno_boundaries.geojson` + BigQuery capacity data
- **Shows**: 
  - Regional boundaries with different colors per DNO company
  - Click regions for capacity breakdown (total MW, wind, solar, gas, nuclear)
  - Generator counts per region
  - Company names and license areas
- **Colors**: UK Power Networks (red), Scottish Power (blue), National Grid (green), etc.

**2. GSP Capacity Choropleth** (`map_gsp_capacity.html`)
- **Features**: 333 GSP zones colored by generation capacity
- **Data Source**: `gsp_zones.geojson` + BigQuery capacity aggregation
- **Shows**:
  - Heat map where darker = higher capacity
  - Individual GSP catchment areas
  - Capacity in MW per zone
  - GSP group mapping (_A through _P)
- **Color Gradient**: Yellow (low) → Red (high) capacity

**3. Combined Infrastructure Map** (`map_combined_boundaries.html`)
- **Features**: DNO boundaries + 1,000 generator locations
- **Data Source**: `official_dno_boundaries.geojson` + `sva_generators_with_coords`
- **Shows**:
  - Gray boundary overlays for regional context
  - Colored dots for generators (Wind=green, Solar=gold, etc.)
  - Toggleable layers by fuel type
  - Click generators for details (name, capacity, technology)

### Updated Dashboard Maps

**Now showing in Google Sheets Dashboard**:
- **Row 20 (J20)**: 🗺️ Generators Map (dots only)
- **Row 36 (J36)**: 🗺️ GSP Regions (aggregated data)
- **Row 52 (J52)**: ⚡ Transmission Zones (data table)
- **Row 68 (J68)**: ⚡ DNO Boundaries (NEW - colored regions)
- **Row 84 (J84)**: 🗺️ Combined Infrastructure (NEW - boundaries + generators)

**View Live**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

---

## 📊 GeoJSON Files Used

### Source Files
```
official_dno_boundaries.geojson    - 14 DNO regions (MultiPolygon)
official_gsp_boundaries.geojson    - 333 GSP zones (MultiPolygon)
gsp_zones.geojson                  - 333 GSP detailed (Polygon)
dno_regions.geojson                - 14 DNO alternate (MultiPolygon)
uk_dno_license_areas.geojson       - 14 license areas (Polygon)
```

### BigQuery Tables with Geography
```sql
-- DNO boundaries with GEOGRAPHY type
neso_dno_boundaries (14 rows, ST_Polygon)

-- GSP boundaries with GEOGRAPHY type  
neso_gsp_boundaries (333 rows, ST_MultiPolygon)

-- License areas with GEOGRAPHY type
dno_license_areas (14 rows, ST_Polygon)
```

---

## 🎨 How It Works

### Map Generation Pipeline

**Step 1: Load GeoJSON**
```python
with open('official_dno_boundaries.geojson') as f:
    dno_data = json.load(f)
# Returns: 14 features with MultiPolygon geometries
```

**Step 2: Query BigQuery for Data**
```sql
SELECT 
    gspgroupid,
    COUNT(*) as num_generators,
    SUM(generationcapacity) as total_capacity_mw
FROM bmu_registration_data
GROUP BY gspgroupid
```

**Step 3: Combine GeoJSON + Data**
```python
for feature in dno_data['features']:
    # Match boundary to capacity data
    capacity = capacity_lookup[feature['properties']['gsp_group']]
    
    # Add to map with color based on capacity/DNO
    folium.GeoJson(feature, style_function=...).add_to(map)
```

**Step 4: Convert to PNG + Upload**
```bash
# Chrome headless screenshot
chrome --headless --screenshot=map.png map.html

# Upload to Google Drive
drive.files().create(body={'name': 'map.png'}, media=...)

# Update Dashboard IMAGE formula
=IMAGE("https://drive.google.com/uc?id=...", 4, 500, 350)
```

---

## 🔄 Automatic Updates

### What Gets Updated

**Every time you run** `python3 auto_update_maps.py`:

1. **Regenerates all 5 maps** with latest BigQuery data:
   - Queries current generator capacity
   - Queries real-time transmission data
   - Overlays on GeoJSON boundaries
   
2. **Creates PNG images** (for Sheets embedding)

3. **Uploads to Google Drive** (updates existing files by ID)

4. **Updates Dashboard cells** (IMAGE formulas stay same, images update)

### Schedule Options

**Manual**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 auto_update_maps.py
```

**Cron (every 6 hours)**:
```bash
0 */6 * * * /Users/georgemajor/GB\ Power\ Market\ JJ/cron_update_maps.sh
```

---

## 🗺️ Map Features Explained

### Interactive Features

**DNO Boundary Map**:
- ✅ Click any region → See capacity breakdown by fuel type
- ✅ Hover → Region name appears
- ✅ Fullscreen mode available
- ✅ Color-coded by DNO company
- ✅ Legend shows which color = which company

**GSP Capacity Map**:
- ✅ Click any GSP zone → See capacity + area
- ✅ Color intensity = generation capacity
- ✅ 333 individual zones visible
- ✅ Gradient legend (low → high)
- ✅ Hover for quick capacity tooltip

**Combined Map**:
- ✅ Toggle generator layers by fuel type
- ✅ Click generators → Name, capacity, technology
- ✅ DNO boundaries as background context
- ✅ Layer control in top right
- ✅ 1,000 generators shown (SVA data with coordinates)

### Why GeoJSON Instead of Dots?

**Before** (dots only):
- ❌ No regional context
- ❌ Hard to see DNO/GSP boundaries
- ❌ Just points on a map

**After** (GeoJSON boundaries):
- ✅ Actual regional polygons
- ✅ See exact catchment areas
- ✅ Color-coded regions
- ✅ Click for aggregated data
- ✅ Professional cartographic visualization

---

## 📁 Files Created

### Map Scripts
```
create_boundary_maps.py          - Main boundary map generator
create_maps_for_sheets.py        - Simple dot maps (original)
auto_update_maps.py              - Unified updater (both types)
```

### HTML Maps (Interactive)
```
map_dno_boundaries.html          - DNO regions (colored)
map_gsp_capacity.html            - GSP choropleth (capacity heat map)
map_combined_boundaries.html     - Boundaries + generators
sheets_generators_map.html       - Simple generator dots
sheets_gsp_regions_map.html      - Simple GSP circles
sheets_transmission_map.html     - Transmission data
```

### PNG Images (Sheets)
```
map_dno_boundaries.png           - For Dashboard J68
map_combined_boundaries.png      - For Dashboard J84
sheets_generators_map.png        - For Dashboard J20
sheets_gsp_regions_map.png       - For Dashboard J36
sheets_transmission_map.png      - For Dashboard J52
```

### Drive URLs
```
DNO Boundaries:     https://drive.google.com/uc?id=17yUhaYI0Jq4usBaMEgG8GS-SihOwpVVC
Combined Map:       https://drive.google.com/uc?id=1pvJrXugHXvr5OqbFSwWyCdJvQX5VwHzs
Generators:         https://drive.google.com/uc?id=1z2_U9xm_kOG7wnQibZybtrq5akWwkgko
GSP Regions:        https://drive.google.com/uc?id=17TKRWnL_6e7gWu6d27O4XFVbe8K8HEmj
Transmission:       https://drive.google.com/uc?id=1nAOV9B-kxSqCWsuBaXOWPGteBVAVz7jm
```

---

## 🎯 Usage Examples

### View All Maps Locally
```bash
# Open all interactive HTML maps
open map_dno_boundaries.html
open map_gsp_capacity.html
open map_combined_boundaries.html
```

### Regenerate Everything
```bash
# Generate boundary maps only
python3 create_boundary_maps.py

# Generate all maps + update Dashboard
python3 auto_update_maps.py
```

### Check What's Available
```bash
# List all GeoJSON files
ls -lh *.geojson

# Check BigQuery geography tables
python3 -c "from google.cloud import bigquery; ..."
```

---

## 📈 Data Sources Summary

| Map Type | GeoJSON File | BigQuery Table | Rows | Update Frequency |
|----------|-------------|----------------|------|------------------|
| DNO Boundaries | official_dno_boundaries.geojson | bmu_registration_data | 14 | Daily |
| GSP Capacity | gsp_zones.geojson | bmu_registration_data | 333 | Daily |
| Generators | N/A (dots) | sva_generators_with_coords | 7,065 | Weekly |
| Transmission | N/A (data) | bmrs_indgen_iris | 1.06M | 30 min |

---

## 💡 Next Steps

### Immediate
- [x] GeoJSON boundary maps created
- [x] All 5 maps embedded in Dashboard
- [x] Auto-update script working
- [ ] Set up cron for automatic daily updates

### Enhancements
- [ ] Add transmission boundaries to map (B1-B17 zones)
- [ ] Overlay real-time generation heatmap on GSP zones
- [ ] Add time slider for historical capacity changes
- [ ] Export maps as high-res PDFs for reports
- [ ] Create map API endpoint for external embedding

### Integration
- [ ] Add map URLs to ChatGPT custom instructions
- [ ] Embed in Railway dashboard
- [ ] Create map viewer page on Vercel
- [ ] Add to project README

---

**Status**: ✅ Complete  
**Created**: November 21, 2025  
**Maps Generated**: 5 (3 boundary + 2 simple)  
**Dashboard Embedded**: 5 maps (rows 20, 36, 52, 68, 84)
