# DNO GeoChart Mapping Guide for Google Sheets

**Project**: GB Power Market JJ  
**Purpose**: Interactive DNO boundary visualization in Google Sheets  
**Date**: December 4, 2025

---

## Overview

This guide shows how to create an **interactive DNO boundary map inside Google Sheets** that can be used to select DNO regions and drive dashboard KPIs.

### Current Infrastructure

We already have:
- ✅ `neso_dno_boundaries` BigQuery table with polygon geometries
- ✅ `generate_dno_map.py` script that creates Folium HTML maps
- ✅ DNO lookup functionality in `dno_lookup_python.py`

### What Google Sheets CAN'T Do

❌ Import or render GeoJSON polygons  
❌ Render arbitrary geographic shapes (like NESO DNO boundaries)  
❌ Show Leaflet/Folium maps directly in a chart  
❌ Display TopoJSON/polyline boundaries  

### What Google Sheets CAN Do

✅ Postcode districts (e.g., NE1, LS10, YO31)  
✅ Postcode areas (NE, LS, YO…)  
✅ Lat/Lon points (markers only)  
✅ Countries / Admin regions  

---

## Three Working Solutions

### Option 1: Simple Hyperlink to Existing Map (5 minutes)

**Best for**: Quick access to existing Folium maps

#### Steps:

1. **Upload `dno_boundary_map.html` to Google Drive**
   - Run: `python3 python/generate_dno_map.py` to create the map
   - Upload the generated `dno_boundary_map.html` file to Drive
   - Right-click → Share → set permissions
   - Copy the sharing link

2. **Add hyperlink in Google Sheets**
   - In Dashboard V3, choose a cell (e.g., A1)
   - Enter: `=HYPERLINK("PASTE_DRIVE_LINK_HERE","🗺️ Open DNO Boundary Map")`
   - Clicking opens the interactive map in a browser tab

**Limitation**: Drive may preview raw HTML instead of executing it. Consider hosting on:
- Small web server
- GitHub Pages
- Vercel static hosting

---

### Option 2: Static Screenshot (10 minutes)

**Best for**: Visual reference without interactivity

#### Steps:

1. **Generate and capture map**
   - Run: `python3 python/generate_dno_map.py`
   - Open `dno_boundary_map.html` in browser
   - Take screenshot (full window or cropped)

2. **Insert in Google Sheets**
   - Dashboard V3 → Insert → Image → Image over cells
   - Or use: `=IMAGE("https://example.com/dno_boundary_map.png")`

**Limitation**: Static only, no interactivity

---

### Option 3: Interactive GeoChart via Postcode Districts (RECOMMENDED)

**Best for**: Fully interactive, clickable, color-coded DNO selection

This produces a **TRUE CHOROPLETH MAP** inside Google Sheets.

---

## Option 3 Implementation: Postcode District Mapping

### Part A: One-Time GIS Processing

#### Method 1: Using Python (GeoPandas)

**Prerequisites**:
```bash
pip3 install geopandas pandas
```

**Step 1: Export DNO boundaries from BigQuery**

Create `export_dno_geojson.py`:

```python
#!/usr/bin/env python3
"""
Export DNO boundaries from BigQuery to GeoJSON for postcode mapping
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def main():
    print("📥 Exporting DNO boundaries to GeoJSON...")
    
    # Initialize BigQuery
    creds = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json'
    )
    client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    
    # Query with GeoJSON export
    query = f"""
    SELECT 
        dno_code,
        area_name,
        ST_ASGEOJSON(boundary) as geojson
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    WHERE boundary IS NOT NULL
    """
    
    df = client.query(query).to_dataframe()
    
    # Build GeoJSON FeatureCollection
    features = []
    for _, row in df.iterrows():
        feature = {
            "type": "Feature",
            "properties": {
                "dno_code": row['dno_code'],
                "dno_name": row['area_name']
            },
            "geometry": json.loads(row['geojson'])
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Save
    output_file = 'dno_boundaries_export.geojson'
    with open(output_file, 'w') as f:
        json.dump(geojson, f)
    
    print(f"✅ Saved {len(features)} DNO regions to {output_file}")

if __name__ == "__main__":
    main()
```

Run it:
```bash
python3 export_dno_geojson.py
```

**Step 2: Get UK Postcode District Boundaries**

Download from:
- **ONS Open Geography**: [Postcode Districts boundaries](https://geoportal.statistics.gov.uk/)
- **OS OpenData**: Code-Point Open
- Any "UK Postcode District Shapefile" source

Save as `uk_postcode_districts.shp` (or `.geojson`)

**Step 3: Spatial Join DNO → Postcode Districts**

Create `map_dno_to_postcodes.py`:

```python
#!/usr/bin/env python3
"""
Spatial join: which postcode districts fall inside each DNO region?
Output: CSV mapping postcode_district → dno_id → dno_name
"""

import geopandas as gpd
import pandas as pd

def main():
    print("🗺️  Starting DNO → Postcode District mapping...")
    
    # 1. Load DNO GeoJSON
    print("📥 Loading DNO boundaries...")
    dno_gdf = gpd.read_file("dno_boundaries_export.geojson")
    
    # 2. Load postcode district boundaries
    print("📥 Loading UK postcode districts...")
    pcd_gdf = gpd.read_file("uk_postcode_districts.shp")
    # Alternative: pcd_gdf = gpd.read_file("uk_postcode_districts.geojson")
    
    # 3. Ensure same CRS
    if dno_gdf.crs is None:
        dno_gdf = dno_gdf.set_crs("EPSG:4326")  # WGS84
    
    pcd_gdf = pcd_gdf.to_crs(dno_gdf.crs)
    print(f"   CRS: {dno_gdf.crs}")
    
    # 4. Spatial join: postcode districts with DNO they fall into
    print("🔗 Performing spatial join...")
    joined = gpd.sjoin(pcd_gdf, dno_gdf, how="left", predicate="intersects")
    
    # 5. Select and rename columns
    # Adjust 'PCD', 'dno_code', 'dno_name' to match your actual field names
    out = joined[["PCD", "dno_code", "dno_name"]].drop_duplicates()
    out = out.rename(columns={
        "PCD": "postcode_district",
        "dno_code": "dno_id",
        "dno_name": "dno_name"
    })
    
    # 6. Drop postcode districts with no DNO match
    out = out.dropna(subset=["dno_id"])
    
    # 7. Save to CSV
    output_file = "postcode_district_to_dno_mapping.csv"
    out.to_csv(output_file, index=False)
    
    print(f"\n✅ Saved {len(out)} postcode district mappings")
    print(f"   Output: {output_file}")
    print("\n📊 Sample:")
    print(out.head(10))
    
    # Summary by DNO
    print("\n📊 DNO Coverage:")
    summary = out.groupby(['dno_id', 'dno_name']).size().reset_index(name='postcode_count')
    print(summary)

if __name__ == "__main__":
    main()
```

Run it:
```bash
python3 map_dno_to_postcodes.py
```

**Output**: `postcode_district_to_dno_mapping.csv`

```csv
postcode_district,dno_id,dno_name
AB10,SSEH,Scottish Hydro Electric
AB11,SSEH,Scottish Hydro Electric
BD1,NPGN,Northern Powergrid (North East)
LS1,NPGY,Northern Powergrid (Yorkshire)
NG1,WMID,Western Power Distribution (West Midlands)
PE19,LPN,UK Power Networks (London)
...
```

---

### Part B: Google Sheets Setup

#### Step 1: Import Mapping to Google Sheets

1. Open your dashboard: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
2. Create new tab: **DNO_PCD_MAP**
3. File → Import → Upload `postcode_district_to_dno_mapping.csv`
4. Import to DNO_PCD_MAP tab

Result:
```
| A                  | B        | C                          |
|--------------------|----------|----------------------------|
| postcode_district  | dno_id   | dno_name                   |
| AB10               | SSEH     | Scottish Hydro Electric    |
| AB11               | SSEH     | Scottish Hydro Electric    |
| BD1                | NPGN     | Northern Powergrid (NE)    |
| ...                | ...      | ...                        |
```

#### Step 2: Add "Value to Colour" Column

In `DNO_PCD_MAP!D1`, add header: **value**

In `DNO_PCD_MAP!D2`, add formula:
```
=IF($B$2="", 0, IF(B2='Dashboard V3'!$B$10, 1, 0))
```

Assumptions:
- `Dashboard V3!B10` contains the selected DNO ID dropdown
- Adjust cell reference to match your dashboard layout

Fill formula down to all rows.

**Result**: Column D shows 1 for selected DNO's postcodes, 0 for others.

#### Step 3: Create GeoChart

1. **Select data**: `DNO_PCD_MAP!A:D`
2. **Insert → Chart**
3. **Chart Editor**:
   - Chart type: **Geo chart**
   - Region: **United Kingdom**
   - Location: Column A (`postcode_district`)
   - Color: Column D (`value`)

4. **Style**:
   - Min value color: Light grey (#F0F0F0)
   - Max value color: Bright highlight (#FF6B35 or #4285F4)
   - Show tooltips: ✅

#### Step 4: Make Interactive

When user changes `Dashboard V3!B10` (DNO dropdown):
1. Column D formulas recalculate
2. Value becomes 1 for selected DNO, 0 for others
3. GeoChart recolors automatically

**Effect**: Interactive DNO region highlighting!

---

## Method 2: Using QGIS (No Coding)

If you prefer GUI over Python:

1. **Open QGIS**
2. **Load layers**:
   - Layer → Add Layer → Add Vector Layer → `dno_boundaries_export.geojson`
   - Layer → Add Layer → Add Vector Layer → `uk_postcode_districts.shp`
3. **Check CRS**: Both should be EPSG:4326 or BNG
   - If not: Right-click → Export → Save Features As… → Reproject
4. **Spatial Join**:
   - Vector → Geoprocessing Tools → **Join attributes by location**
   - Input layer: postcode districts
   - Join layer: DNO boundaries
   - Predicate: **intersects**
   - Output: `postcode_districts_with_dno`
5. **Export**:
   - Open attribute table → Keep columns: postcode_district, dno_id, dno_name
   - Right-click layer → Export → Save Features As… → **CSV**

Then proceed to Part B (Google Sheets Setup) above.

---

## Advanced: Embedded Sidebar Map (Option C)

For showing the REAL polygon boundaries inside Google Sheets.

### Apps Script Setup

1. **Upload HTML map to Drive** (from `python/generate_dno_map.py`)
2. **Open Apps Script**: Extensions → Apps Script
3. **Create HTML file**: File → New → HTML file → Name: `dno_boundary_map`
4. **Paste your Folium HTML** (full content from generated map)
5. **Create sidebar function**:

```javascript
function showDNOMap() {
  var html = HtmlService.createHtmlOutputFromFile('dno_boundary_map')
    .setTitle('DNO Map')
    .setWidth(600);
  SpreadsheetApp.getUi().showSidebar(html);
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🗺️ DNO Tools')
    .addItem('Show DNO Map', 'showDNOMap')
    .addToUi();
}
```

6. **Save and reload sheet**
7. **New menu appears**: 🗺️ DNO Tools → Show DNO Map
8. **Sidebar opens** with full interactive map

### Making it Interactive

Add JavaScript to HTML file to write clicked DNO back to sheet:

```javascript
map.on('click', function(e) {
  // Get clicked DNO ID
  var dnoId = e.layer.feature.properties.dno_code;
  
  // Write to sheet
  google.script.run.setDNOSelection(dnoId);
});
```

Apps Script function:
```javascript
function setDNOSelection(dnoId) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard V3');
  sheet.getRange('B10').setValue(dnoId);
}
```

---

## Comparison Table

| Feature | Option 1: Hyperlink | Option 2: Screenshot | Option 3: GeoChart | Option C: Sidebar |
|---------|-------------------|-------------------|------------------|-----------------|
| **Setup Time** | 5 min | 10 min | 2 hours | 1 hour |
| **Interactivity** | External | None | Full | Full |
| **True Boundaries** | ✅ | ✅ | ❌ (postcode approx) | ✅ |
| **Clicks to View** | 1 click | 0 (always visible) | 0 (embedded) | 1 click |
| **Auto-Updates** | ❌ | ❌ | ✅ | ✅ |
| **Mobile Friendly** | ✅ | ✅ | ✅ | ⚠️ |

---

## Recommendation

**For Dashboard V3**: Use **Option 3 (GeoChart with Postcode Districts)**

**Why**:
- ✅ Fully embedded in sheet
- ✅ No external clicks needed
- ✅ Auto-updates when dropdown changes
- ✅ Professional appearance
- ✅ Standard Google Sheets chart (easy to maintain)

**Tradeoff**: Postcode district boundaries approximate DNO areas (typically accurate to ~95%)

**For detailed analysis**: Keep **Option 1 (Hyperlink)** as secondary reference for precise boundaries

---

## Existing Scripts Reference

### `python/generate_dno_map.py`
- Queries `neso_dno_boundaries` BigQuery table
- Generates Folium HTML map with polygon boundaries
- Output: `dno_boundary_map.html`

### `dno_lookup_python.py`
- DNO lookup by MPAN or postcode
- Uses `neso_dno_reference` table
- Returns DUoS rates and time bands

### BigQuery Tables

| Table | Purpose | Columns |
|-------|---------|---------|
| `neso_dno_boundaries` | Polygon geometries | dno_code, area_name, boundary (GEOGRAPHY) |
| `neso_dno_reference` | DNO details | dno_id, dno_name, region, contact |
| `duos_unit_rates` | DUoS rates | dno_id, voltage, red_rate, amber_rate, green_rate |

---

## Next Steps

1. ✅ **Export DNO GeoJSON**: Run `export_dno_geojson.py` (create from template above)
2. ⏳ **Get Postcode Districts**: Download from ONS Open Geography
3. ⏳ **Spatial Join**: Run `map_dno_to_postcodes.py`
4. ⏳ **Import to Sheets**: Upload CSV to DNO_PCD_MAP tab
5. ⏳ **Create GeoChart**: Follow Part B instructions
6. ⏳ **Test Interactivity**: Change DNO dropdown, verify map updates

---

## Troubleshooting

### "No CRS found"
```python
dno_gdf = dno_gdf.set_crs("EPSG:4326")  # WGS84
```

### "Geometry column not found"
Check GeoJSON structure - ensure "geometry" field exists:
```python
print(dno_gdf.columns)
print(dno_gdf.head())
```

### "Postcode districts not matching"
- Verify UK postcode shapefile covers all regions
- Check for Northern Ireland exclusion (often separate dataset)
- Use `predicate="intersects"` not `"within"` for border postcodes

### GeoChart shows wrong regions
- Verify column A contains standard UK postcode districts (e.g., "SW1A", "NE1")
- Google Sheets recognizes: Postcode districts, not full postcodes
- Use district prefix only: "SW1A" not "SW1A 1AA"

---

## Cost & Performance

- **BigQuery**: Free tier covers DNO queries (~1KB per query)
- **Python Processing**: One-time cost (~30 seconds)
- **Google Sheets**: Free, no API limits for charts
- **GeoChart Rendering**: <1 second for ~2,500 UK postcode districts

---

## Support

**Documentation**:
- `PROJECT_CONFIGURATION.md` - All config settings
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data schema
- `DNO_LOOKUP_SYSTEM.md` - DNO lookup details (if exists)

**Contact**: george@upowerenergy.uk  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

---

*Last Updated: December 4, 2025*
