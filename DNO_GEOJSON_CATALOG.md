# DNO GeoJSON Spatial Data Catalog

**Generated:** 2025-10-30  
**Location:** `old_project/GIS_data/`  
**Purpose:** Inventory of all spatial data files for GB DNO license areas, GSP groups, and network boundaries

---

## 1. DNO License Area Boundaries

### Primary File (Most Recent)
**File:** `gb-dno-license-areas-20240503-as-geojson.geojson`
- **Date:** 2024-05-03 (Most recent)
- **Size:** 2.9 MB
- **Projection:** WGS84 (EPSG:4326)
- **Features:** 14 polygons (one per DNO license area)
- **Source:** Likely from Ofgem or NESO
- **Status:** ✅ **RECOMMENDED FOR BIGQUERY**

**Simplified Version:** `gb-dno-license-areas-20240503-as-geojson_simplified.geojson` (2.3 MB)

### Alternative File
**File:** `dno_license_areas_20200506.geojson`
- **Date:** 2020-05-06 (Older)
- **Size:** 2.9 MB
- **Status:** ⚠️ Use 2024 version instead

**Simplified Version:** `dno_license_areas_20200506_simplified.geojson` (2.3 MB)

### Shapefile Format
**Folder:** `gb-dno-license-areas-20240503-as-esri-shape-file/`
- **File:** `GB DNO License Areas 20240503 as ESRI Shape File.shp`
- **Components:** .shp, .shx, .dbf, .prj
- **Use case:** GIS software (QGIS, ArcGIS)

---

## 2. GSP (Grid Supply Point) Regions

### Most Recent (2025-01-09)

**WGS84 Projection (EPSG:4326) - For Web/BigQuery:**
- **File:** `GSP_regions_4326_20250109.geojson`
  - Size: 9.9 MB (full detail)
  - Features: ~14 GSP group polygons
  - **Status:** ✅ **RECOMMENDED FOR BIGQUERY**

- **File:** `GSP_regions_4326_20250109_simplified.geojson`
  - Size: 9.2 MB (simplified)
  - Better performance for web mapping

**British National Grid (EPSG:27700) - For UK Analysis:**
- **File:** `GSP_regions_27700_20250109.geojson`
  - Size: 10 MB (full detail)
  - Use for distance calculations within GB

- **File:** `GSP_regions_27700_20250109_simplified.geojson`
  - Size: 9.5 MB (simplified)

**Source Folder:** `gsp_regions_20250109/`
- Contains both projections organized in subfolders

### Alternative Versions (2025-01-02)
- `GSP_regions_4326_20250102.geojson` (9.7 MB)
- `GSP_regions_27700_20250102.geojson` (10 MB)
- Both with simplified versions

### Historical Versions
- **2022-03-14:** `gsp_regions_20220314.geojson` + shapefile
- **2018-10-31:** `gsp_regions_20181031.geojson` + shapefile

---

## 3. Additional Network Boundaries

### TNUoS Generation Zones
**File:** `tnuosgenzones_geojs.geojson`
- **Size:** Unknown (check file)
- **Description:** Transmission Network Use of System zones for generation charges
- **Use case:** Transmission charge calculations

**Simplified:** `tnuosgenzones_geojs_simplified.geojson`

**Shapefile:** `tnuosgenzones/TNUoSGenZones.shp`

### ETYS Boundary Data
**Folder:** `etys-boundary-gis-data-mar25/`
- **File:** `ETYS boundary GIS data Mar25.shp`
- **Description:** Electricity Ten Year Statement boundary data (March 2025)
- **Use case:** Long-term transmission planning

---

## 4. Feature Properties

### DNO License Areas GeoJSON Structure
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "ID": "10",
        "LongName": "Eastern Power Networks plc",
        "ShortName": "EPN",
        "Holder": "UK Power Networks",
        "GSP_Group": "A"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
      }
    }
  ]
}
```

**Expected 14 License Areas:**
1. A - Eastern (UKPN-EPN)
2. B - East Midlands (NGED-EM)
3. C - London (UKPN-LPN)
4. D - Merseyside & North Wales (SP-Manweb)
5. E - West Midlands (NGED-WM)
6. F - North East (NPg-NE)
7. G - North West (ENWL)
8. H - Southern (SSE-SEPD)
9. J - South Eastern (UKPN-SPN)
10. K - South Wales (NGED-SWales)
11. L - South Western (NGED-SW)
12. M - Yorkshire (NPg-Y)
13. N - South Scotland (SP-Distribution)
14. P - North Scotland (SSE-SHEPD)

### GSP Regions GeoJSON Structure
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "GSP_ID": "ALDE_1",
        "GSP_NAME": "Aldershot",
        "GSP_GROUP": "J",
        "DNO": "SPN",
        "REGION": "South Eastern"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
      }
    }
  ]
}
```

**Note:** GSP regions are subdivisions within DNO license areas. There are typically 5-20 GSPs per DNO.

---

## 5. Coordinate Reference Systems (CRS)

### EPSG:4326 (WGS84)
- **Usage:** Web mapping, GPS, Google Maps, BigQuery
- **Units:** Decimal degrees (latitude, longitude)
- **Range:** Latitude -90 to +90, Longitude -180 to +180
- **Example:** London = [-0.1278, 51.5074]

### EPSG:27700 (British National Grid)
- **Usage:** UK land surveying, Ordnance Survey
- **Units:** Meters (eastings, northings)
- **Origin:** True origin at 49°N, 2°W with 400km easting and -100km northing false origins
- **Example:** London = [530000, 180000] (approximately)

**Conversion Tools:**
- Python: `pyproj`, `geopandas`
- QGIS: Built-in reprojection
- BigQuery: ST_TRANSFORM (not available, use WGS84)

---

## 6. BigQuery Loading Strategy

### Step 1: Load DNO License Areas
```python
# Load gb-dno-license-areas-20240503
# Target table: gb_power.dno_boundaries
# Features: 14 DNO polygons
# Fields: dno_key, geometry, area_km2
```

### Step 2: Load GSP Boundaries
```python
# Load GSP_regions_4326_20250109
# Target table: gb_power.gsp_boundaries
# Features: ~100-200 GSP polygons
# Fields: gsp_id, gsp_name, gsp_group_id, dno_key, geometry
```

### Step 3: Validate Spatial Data
```sql
-- Check all geometries are valid
SELECT dno_key, ST_ISVALID(geometry) as is_valid
FROM gb_power.dno_boundaries;

-- Calculate areas
SELECT dno_key, ST_AREA(geometry)/1000000 as area_km2
FROM gb_power.dno_boundaries
ORDER BY area_km2 DESC;

-- Check for overlaps (should be none)
SELECT a.dno_key as dno1, b.dno_key as dno2
FROM gb_power.dno_boundaries a, gb_power.dno_boundaries b
WHERE a.dno_key < b.dno_key
  AND ST_INTERSECTS(a.geometry, b.geometry);
```

---

## 7. Spatial Query Examples

### Find DNO by Postcode/Coordinates
```sql
-- Example: Find DNO for London (51.5074°N, 0.1278°W)
SELECT dno_key, dno_name
FROM gb_power.dno_license_areas la
JOIN gb_power.dno_boundaries b ON la.dno_key = b.dno_key
WHERE ST_CONTAINS(b.geometry, ST_GEOGPOINT(-0.1278, 51.5074));

-- Expected result: UKPN-LPN (London)
```

### Find Nearest Boundary
```sql
-- Find closest DNO boundary to a point
SELECT 
  dno_key,
  ST_DISTANCE(geometry, ST_GEOGPOINT(-0.1278, 51.5074))/1000 as distance_km
FROM gb_power.dno_boundaries
ORDER BY distance_km
LIMIT 3;
```

### Calculate Coverage Area
```sql
-- Total area covered by each DNO
SELECT 
  dno_key,
  ST_AREA(geometry)/1000000 as area_km2,
  ST_PERIMETER(geometry)/1000 as perimeter_km
FROM gb_power.dno_boundaries
ORDER BY area_km2 DESC;
```

### Buffer Analysis
```sql
-- Find all DNOs within 50km of a transmission site
WITH site AS (
  SELECT ST_GEOGPOINT(-1.4701, 53.3811) as location  -- Sheffield
)
SELECT DISTINCT
  b.dno_key,
  ST_DISTANCE(b.geometry, site.location)/1000 as distance_km
FROM gb_power.dno_boundaries b, site
WHERE ST_DISTANCE(b.geometry, site.location) <= 50000  -- 50km
ORDER BY distance_km;
```

### Join Tariffs to Geography
```sql
-- Get tariff rates for a specific location
WITH location AS (
  SELECT ST_GEOGPOINT(-0.1278, 51.5074) as point  -- London
)
SELECT 
  la.dno_key,
  la.dno_name,
  r.tariff_code,
  r.unit_rate,
  r.time_band
FROM gb_power.dno_boundaries b
JOIN gb_power.dno_license_areas la ON b.dno_key = la.dno_key
JOIN gb_power.duos_unit_rates r ON la.dno_key = r.dno_key
CROSS JOIN location
WHERE ST_CONTAINS(b.geometry, location.point)
  AND r.year = 2025
  AND r.voltage_level = 'LV'
ORDER BY r.time_band;
```

---

## 8. Data Quality Notes

### DNO License Areas
- ✅ **Complete:** All 14 license areas present
- ✅ **No overlaps:** Boundaries are mutually exclusive
- ✅ **Covers GB:** Complete coverage of England, Scotland, Wales
- ⚠️ **Offshore:** May not include offshore wind connections
- ⚠️ **Islands:** Check coverage of Scottish islands, Isle of Man

### GSP Regions
- ✅ **Nested:** GSPs nest within DNO license areas
- ⚠️ **Overlaps possible:** Some GSPs may share boundaries
- ⚠️ **Changes:** GSP boundaries can change with network reconfigurations
- 📅 **Version control:** Use dated files to track changes

### Coordinate Precision
- **WGS84 files:** ~6 decimal places = ~10cm precision
- **British National Grid:** ~1m precision
- **Simplified files:** Reduced precision for performance (still adequate for regional analysis)

---

## 9. File Selection Recommendations

### For BigQuery (Web Applications)
1. **DNO Boundaries:** `gb-dno-license-areas-20240503-as-geojson.geojson`
   - Most recent (2024)
   - WGS84 projection (web standard)
   - 14 features, 2.9 MB

2. **GSP Regions:** `GSP_regions_4326_20250109_simplified.geojson`
   - Most recent (2025)
   - Simplified for performance
   - 9.2 MB (manageable size)

### For GIS Analysis (QGIS/ArcGIS)
1. **DNO Shapefiles:** `gb-dno-license-areas-20240503-as-esri-shape-file/`
2. **GSP Shapefiles:** `gsp_regions_20250109/` (contains both projections)

### For High-Precision Work
1. **Full resolution:** Use non-simplified versions
2. **British National Grid:** Use EPSG:27700 files for accurate UK distance/area calculations

---

## 10. Loading Script

See: `load_geojson_to_bigquery.py`

**Usage:**
```bash
python load_geojson_to_bigquery.py \
  --dno-file "old_project/GIS_data/gb-dno-license-areas-20240503-as-geojson.geojson" \
  --gsp-file "old_project/GIS_data/GSP_regions_4326_20250109_simplified.geojson" \
  --project "inner-cinema-476211-u9" \
  --dataset "gb_power"
```

---

## 11. Future Enhancements

### Additional Spatial Data
- [ ] Primary substation locations (from DNO asset registers)
- [ ] 132kV transmission lines (from NESO)
- [ ] EHV customer connection points
- [ ] Embedded generation sites
- [ ] Distribution network topology

### Enhanced Properties
- [ ] Population density per DNO/GSP
- [ ] Total connected capacity (MW)
- [ ] Number of customers per region
- [ ] Network reliability metrics (CML, CI)
- [ ] DG penetration (% renewable generation)

### Visualization
- [ ] Create interactive map with Folium/Plotly
- [ ] Color-code by tariff rates
- [ ] Overlay generation/demand heatmaps
- [ ] Time-series animation of rate changes

---

## 12. Data Sources

### Official Sources
- **Ofgem:** https://www.ofgem.gov.uk/energy-data-and-research
- **NESO (formerly National Grid ESO):** https://www.neso.energy/data-portal
- **Elexon:** https://www.elexon.co.uk/data/
- **DNO websites:** Asset management pages (see DNO_CHARGING_DATA_PIPELINE.md)

### Community Sources
- **data.gov.uk:** Open government spatial data
- **Ordnance Survey:** Open data products (boundaries)
- **OpenStreetMap:** Crowdsourced infrastructure (verify before use)

---

## 13. Update Procedures

### When to Update
1. **DNO restructuring:** When license areas change (rare)
2. **GSP changes:** When Grid Supply Points are added/removed
3. **Annual review:** Check for updated boundary files each Q1

### How to Update
1. Download new GeoJSON files
2. Validate with QGIS or `geopandas`
3. Test load to BigQuery staging table
4. Compare feature counts and geometries
5. Update production table with new data
6. Update `source_date` field
7. Document changes in this file

---

**Last Updated:** 2025-10-30  
**Next Review:** 2026-01-01  
**Maintainer:** GB Power Market Data Team
