# DNO Map Implementation - Complete Documentation

**Status**: ✅ Nearly Working - Real NESO data loaded, map displays functional
**Last Updated**: 1 November 2025

## Overview

This system displays GB Distribution Network Operator (DNO) license areas on an interactive Google Maps interface using official NESO (National Energy System Operator) data.

## System Architecture

### Data Flow
```
NESO GeoJSON Files (EPSG:27700)
    ↓
Coordinate Transformation (pyproj)
    ↓
BigQuery Tables (EPSG:4326)
    ↓
Static GeoJSON File
    ↓
Google Maps Display
```

## Data Sources

### Official NESO Data Files

**Location**: `/Users/georgemajor/Jibber Jabber ChatGPT/`

1. **DNO Boundaries GeoJSON**:
   - File: `gis-boundaries-for-gb-dno-license-areas_*.geojson`
   - Contains: 14 DNO license area polygons
   - Coordinate System: British National Grid (EPSG:27700)
   - Format: MultiPolygon geometries

2. **GSP Boundaries GeoJSON**:
   - File: `gis-boundaries-for-gb-grid-supply-points_*.geojson`
   - Contains: Grid Supply Point boundaries
   - Coordinate System: British National Grid (EPSG:27700)

3. **DNO Reference Data**:
   - File: `/Users/georgemajor/Jibber-Jabber-Work/DNO_Master_Reference.csv`
   - Contains: Metadata for all 14 DNOs
   - Fields: MPAN IDs, GSP groups, contact info, coverage areas

## BigQuery Schema

### Project Configuration
- **Project ID**: `inner-cinema-476211-u9`
- **Dataset**: `uk_energy_prod`

### Table 1: `neso_dno_reference`
```sql
CREATE TABLE uk_energy_prod.neso_dno_reference (
    dno_id STRING,
    dno_full_name STRING,
    dno_code STRING,
    gsp_group_id STRING,
    gsp_group_name STRING,
    mpan_distributor_id INT64,
    market_participant_id STRING,
    primary_coverage_area STRING,
    website_url STRING,
    contact_email STRING,
    emergency_phone STRING
);
```

**Records**: 14 DNO operators with MPAN IDs 10-23

### Table 2: `neso_gsp_groups`
```sql
CREATE TABLE uk_energy_prod.neso_gsp_groups (
    gsp_group_id STRING,
    gsp_group_name STRING,
    dno_operator STRING,
    geographic_area STRING
);
```

**Records**: 14 GSP groups (A-P, excluding I and O)

### Table 3: `neso_dno_boundaries`
```sql
CREATE TABLE uk_energy_prod.neso_dno_boundaries (
    dno_id STRING,
    gsp_group STRING,
    dno_code STRING,
    area_name STRING,
    dno_full_name STRING,
    boundary GEOGRAPHY,  -- WGS84 (EPSG:4326) coordinates
    area_sqkm FLOAT64
);
```

**Records**: 14 DNO boundary polygons with transformed WGS84 coordinates

**Coverage**:
- Smallest: London (684 km²)
- Largest: North Scotland (64,024 km²)
- Total: ~237,000 km² (England, Wales, Scotland)

## The 14 DNO License Areas

| MPAN ID | GSP Group | DNO Code | DNO Name | Coverage Area |
|---------|-----------|----------|----------|---------------|
| 10 | A | UKPN | UK Power Networks | East England |
| 11 | B | NGED | National Grid ED | East Midlands |
| 12 | C | UKPN | UK Power Networks | London |
| 13 | D | SPEN | SP Energy Networks | North Wales, Merseyside, Cheshire |
| 14 | E | NGED | National Grid ED | West Midlands |
| 15 | F | NPG | Northern Powergrid | North East England |
| 16 | G | ENWL | Electricity North West | North West England |
| 20 | H | SSEN | SSE Networks | Southern England |
| 19 | J | UKPN | UK Power Networks | South East England |
| 21 | K | NGED | National Grid ED | South Wales |
| 22 | L | NGED | National Grid ED | South West England |
| 23 | M | NPG | Northern Powergrid | Yorkshire |
| 18 | N | SPEN | SP Energy Networks | South and Central Scotland |
| 17 | P | SSEN | SSE Networks | North Scotland |

**Note**: GSP groups I and O are not used (reserved for Ireland/offshore).

## Coordinate System Transformation

### The Problem
NESO provides data in **British National Grid (EPSG:27700)**:
- Units: Meters (easting/northing)
- Example: [599568.1474, 183256.9999]
- Used for UK mapping accuracy

BigQuery GEOGRAPHY type requires **WGS84 (EPSG:4326)**:
- Units: Degrees (longitude/latitude)
- Example: [0.2651, 52.8119]
- Standard global coordinate system

### The Solution
Using the `pyproj` library to transform coordinates:

```python
from pyproj import Transformer

# Create transformer
transformer = Transformer.from_crs(
    "EPSG:27700",  # British National Grid
    "EPSG:4326",   # WGS84 lat/long
    always_xy=True
)

def transform_coordinates(coords):
    """Transform [easting, northing] to [longitude, latitude]"""
    lon, lat = transformer.transform(coords[0], coords[1])
    return [lon, lat]
```

## Python Scripts

### 1. `load_neso_dno_reference.py`
**Purpose**: Load DNO metadata from CSV to BigQuery

**Status**: ✅ Successfully executed

**Key Functions**:
```python
def load_neso_dno_data():
    """Load the official NESO DNO Master Reference data"""
    csv_path = "/Users/georgemajor/Jibber-Jabber-Work/DNO_Master_Reference.csv"
    df = pd.read_csv(csv_path)
    return df

def create_bigquery_table(df):
    """Create BigQuery table with real NESO DNO data"""
    # Creates neso_dno_reference table
    
def create_gsp_groups_table():
    """Create separate GSP groups table"""
    # Creates neso_gsp_groups table
```

**Output**:
- ✅ 14 DNO records loaded to `neso_dno_reference`
- ✅ 14 GSP group records loaded to `neso_gsp_groups`

### 2. `load_dno_transformed.py`
**Purpose**: Transform coordinates and load DNO boundaries to BigQuery

**Status**: ✅ Successfully executed

**Key Functions**:
```python
def transform_coordinates(coords):
    """Transform British National Grid to WGS84"""
    lon, lat = transformer.transform(coords[0], coords[1])
    return [lon, lat]

def transform_polygon(polygon_coords):
    """Transform all coordinates in a polygon"""
    return [[transform_coordinates(coord) for coord in ring] 
            for ring in polygon_coords]

def transform_multipolygon(multipolygon_coords):
    """Transform all polygons in a MultiPolygon"""
    return [transform_polygon(polygon) 
            for polygon in multipolygon_coords]

def load_dno_to_bigquery(features):
    """Load transformed features to BigQuery"""
    for feature in features:
        # Extract properties and geometry
        # Transform coordinates
        # Insert as GEOGRAPHY type
```

**Output**:
```
✅  1/14: GSP _A  | UKPN | East England      | 20,429 km²
✅  2/14: GSP _B  | NGED | East Midlands     | 16,242 km²
✅  3/14: GSP _C  | UKPN | London            |    684 km²
...
✅ 14/14: GSP _P  | SSEN | North Scotland    | 64,024 km²

✅ SUCCESS! Loaded all 14 DNO boundaries to BigQuery
```

### 3. `generate_dno_geojson.py`
**Purpose**: Export BigQuery data to static GeoJSON file for web display

**Status**: ✅ Successfully executed

**Key Query**:
```python
query = """
SELECT 
    b.dno_id,
    b.gsp_group,
    b.dno_code,
    b.area_name,
    b.dno_full_name,
    r.mpan_distributor_id,
    r.gsp_group_name,
    r.website_url,
    r.primary_coverage_area,
    ST_ASGEOJSON(b.boundary) as geojson,
    ST_AREA(b.boundary) / 1000000 as area_sqkm
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries` b
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` r
    ON REPLACE(b.gsp_group, '_', '') = r.gsp_group_id
ORDER BY b.gsp_group
"""
```

**Output File**: `dno_regions.geojson`
- Format: GeoJSON FeatureCollection
- Features: 14 DNO license areas
- Geometry: MultiPolygon with WGS84 coordinates
- Properties: MPAN IDs, DNO names, areas, contact info
- Total Coordinates: 3,552+ points

### 4. Verification Script
```python
# Check GeoJSON contents
import json

with open('dno_regions.geojson', 'r') as f:
    data = json.load(f)

print(f"Features: {len(data['features'])}")
print(f"Total coordinate points: {sum(len(f['geometry']['coordinates'][0][0]) for f in data['features'])}")

for feature in data['features']:
    props = feature['properties']
    print(f"GSP {props['gsp_group']} | MPAN {props['mpan_id']} | {props['dno_code']} | {props['area']}")
```

## Web Interface

### File: `dno_energy_map_advanced.html`

**Google Maps API Key**: `AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0`

### Key Features

1. **DNO Region Display**
   - Loads real NESO boundaries from `dno_regions.geojson`
   - Color-coded by DNO operator
   - Interactive polygons with click events

2. **Info Windows**
   - Shows DNO details on click
   - Displays: Name, Code, MPAN ID, GSP Group, Coverage Area, Website

3. **Color Scheme**
   ```javascript
   const colors = {
       'UKPN': '#667eea',  // Purple
       'SSEN': '#34a853',  // Green
       'NGED': '#fbbc05',  // Yellow
       'ENWL': '#ea4335',  // Red
       'NPG':  '#4285f4',  // Blue
       'SPEN': '#764ba2'   // Dark Purple
   };
   ```

### Critical JavaScript Functions

#### Load DNO Regions
```javascript
function loadDNORegions() {
    console.log('🗺️ Loading DNO regions...');
    
    fetch('dno_regions.geojson')
        .then(response => {
            console.log('📥 Fetch response:', response.status);
            if (!response.ok) {
                throw new Error('GeoJSON file not found');
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ GeoJSON loaded:', data.features.length, 'features');
            console.log('First feature:', data.features[0]);
            
            // Clear existing layers
            map.data.forEach(feature => {
                map.data.remove(feature);
            });
            
            // Add GeoJSON to map
            const addedFeatures = map.data.addGeoJson(data);
            console.log('✅ Added to map:', addedFeatures.length, 'features');
            
            // Style the polygons
            map.data.setStyle(function(feature) {
                const dnoCode = feature.getProperty('dno_code');
                return {
                    fillColor: getDNOColorByCode(dnoCode),
                    fillOpacity: 0.35,
                    strokeColor: getDNOColorByCode(dnoCode),
                    strokeWeight: 2.5
                };
            });
            
            // Fit map bounds to data
            const bounds = new google.maps.LatLngBounds();
            addedFeatures.forEach(feature => {
                feature.getGeometry().forEachLatLng(function(latLng) {
                    bounds.extend(latLng);
                });
            });
            map.fitBounds(bounds);
            console.log('✅ Map bounds fitted to data');
        })
        .catch(err => {
            console.error('❌ Error loading DNO data:', err);
            console.error('❌ Error message:', err.message);
            console.error('❌ Error stack:', err.stack);
            console.log('⚠️ Falling back to sample rectangles');
            loadSampleDNOData();
        });
}
```

#### Fallback Function (Sample Data)
```javascript
function loadSampleDNOData() {
    // This function draws rectangular approximations
    // Only used if GeoJSON fetch fails
    const dnoRegions = [
        { name: 'UKPN - London', bounds: [[51.28, -0.51], [51.69, 0.33]], color: '#667eea' },
        // ... more rectangles
    ];
}
```

## Running the System

### Step 1: Load Data to BigQuery (One-time setup)

```bash
cd "/Users/georgemajor/GB Power Market JJ"
source .venv/bin/activate

# Load DNO reference data
python load_neso_dno_reference.py

# Transform coordinates and load boundaries
python load_dno_transformed.py
```

### Step 2: Generate GeoJSON

```bash
# Generate static GeoJSON file
python generate_dno_geojson.py
```

This creates `dno_regions.geojson` with 14 DNO license areas.

### Step 3: Start HTTP Server

```bash
# Start local web server on port 8765
python -m http.server 8765
```

Keep this terminal running.

### Step 4: Open Map

```bash
# Open in browser
open "http://localhost:8765/dno_energy_map_advanced.html"
```

### Step 5: View DNO Regions

1. Click the **"Load DNO Regions"** button
2. Open Developer Console (`Cmd+Option+I`)
3. Look for console messages:
   - 🗺️ Loading DNO regions...
   - 📥 Fetch response: 200
   - ✅ GeoJSON loaded: 14 features
   - ✅ Added to map: 14 features
   - ✅ Map bounds fitted to data

## Debugging

### Console Logging
The map includes comprehensive logging:

```javascript
console.log('🗺️ Loading DNO regions...');        // Start
console.log('📥 Fetch response:', response.status); // HTTP status
console.log('✅ GeoJSON loaded:', data.features.length); // Success
console.log('✅ Added to map:', addedFeatures.length);  // Features added
console.log('✅ Map bounds fitted to data');      // Bounds calculated
console.error('❌ Error loading DNO data:', err); // Errors
```

### Common Issues

**Issue 1: Rectangles displayed instead of real boundaries**
- **Symptom**: Map shows rectangular boxes
- **Cause**: Fetch failing, falling back to `loadSampleDNOData()`
- **Solution**: Check browser console for error messages
- **Verify**: 
  ```bash
  curl http://localhost:8765/dno_regions.geojson | head -20
  ```

**Issue 2: "File not found" error**
- **Symptom**: Console shows "GeoJSON file not found"
- **Cause**: HTTP server not running or wrong URL
- **Solution**: 
  ```bash
  # Verify server is running
  lsof -i :8765
  
  # Restart server if needed
  python -m http.server 8765
  ```

**Issue 3: Coordinates out of range**
- **Symptom**: "Latitude must be between -90 and 90"
- **Cause**: Using British National Grid coordinates without transformation
- **Solution**: Use `load_dno_transformed.py` (already done)

**Issue 4: Empty map**
- **Symptom**: Map loads but no polygons visible
- **Cause**: Bounds calculation error or geometry issue
- **Solution**: Check console for JavaScript errors
- **Verify**: 
  ```javascript
  // In browser console
  map.data.forEach(f => console.log(f.getGeometry().getType()));
  ```

### Verification Commands

```bash
# Check GeoJSON file exists and has correct format
python -c "
import json
with open('dno_regions.geojson') as f:
    data = json.load(f)
    print(f'Features: {len(data[\"features\"])}')
    print(f'First MPAN ID: {data[\"features\"][0][\"properties\"][\"mpan_id\"]}')
"

# Verify HTTP server is serving files
curl -s http://localhost:8765/dno_regions.geojson | head -20

# Check BigQuery table
bq query --use_legacy_sql=false "
SELECT gsp_group, dno_code, area_name, area_sqkm 
FROM \`inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries\`
ORDER BY gsp_group
"
```

## File Structure

```
/Users/georgemajor/GB Power Market JJ/
├── dno_energy_map_advanced.html       # Main map interface
├── dno_regions.geojson                 # Generated GeoJSON (14 DNOs)
├── load_neso_dno_reference.py         # Load metadata to BigQuery
├── load_dno_transformed.py            # Transform coords & load boundaries
├── generate_dno_geojson.py            # Export BigQuery to GeoJSON
└── DNO_MAP_IMPLEMENTATION.md          # This documentation

/Users/georgemajor/Jibber-Jabber-Work/
└── DNO_Master_Reference.csv           # NESO reference data

/Users/georgemajor/Jibber Jabber ChatGPT/
├── gis-boundaries-for-gb-dno-license-areas_*.geojson
└── gis-boundaries-for-gb-grid-supply-points_*.geojson
```

## Data Validation

### Verify GeoJSON Contents
```python
import json

with open('dno_regions.geojson', 'r') as f:
    data = json.load(f)

print(f"Total Features: {len(data['features'])}")
print(f"\nDNO License Areas:")

for i, feature in enumerate(data['features'], 1):
    props = feature['properties']
    geom = feature['geometry']
    
    # Count coordinates
    coord_count = len(geom['coordinates'][0][0])
    
    print(f"{i:2d}. GSP {props['gsp_group']:3s} | "
          f"MPAN {props.get('mpan_id', 'N/A'):3} | "
          f"{props['dno_code']:8s} | "
          f"{props['area']:30s} | "
          f"{props.get('area_sqkm', 0):>8,.1f} km² | "
          f"{coord_count:>4d} coords")
```

**Expected Output**:
```
Total Features: 14

DNO License Areas:
 1. GSP _A  | MPAN  10 | UKPN     | East England                   | 20,429.1 km² |  234 coords
 2. GSP _B  | MPAN  11 | NGED     | East Midlands                  | 16,242.5 km² |  198 coords
 3. GSP _C  | MPAN  12 | UKPN     | London                         |    684.0 km² |   89 coords
...
14. GSP _P  | MPAN  17 | SSEN     | North Scotland                 | 64,024.0 km² |  567 coords
```

### Verify BigQuery Data
```sql
-- Check record count
SELECT COUNT(*) as dno_count 
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`;
-- Expected: 14

-- Verify MPAN IDs
SELECT 
    b.gsp_group,
    r.mpan_distributor_id,
    b.dno_code,
    b.area_name
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries` b
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` r
    ON REPLACE(b.gsp_group, '_', '') = r.gsp_group_id
ORDER BY r.mpan_distributor_id;
-- Expected: MPANs 10-23 (excluding 24-27)

-- Check coordinate ranges (should be UK bounds)
SELECT 
    MIN(ST_X(ST_CENTROID(boundary))) as min_lon,
    MAX(ST_X(ST_CENTROID(boundary))) as max_lon,
    MIN(ST_Y(ST_CENTROID(boundary))) as min_lat,
    MAX(ST_Y(ST_CENTROID(boundary))) as max_lat
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`;
-- Expected: lon ≈ -6 to 2, lat ≈ 50 to 61
```

## Current Status

### ✅ Completed
- [x] Found and loaded real NESO data files
- [x] Loaded 14 DNO metadata records to `neso_dno_reference`
- [x] Loaded 14 GSP group records to `neso_gsp_groups`
- [x] Solved coordinate system transformation (EPSG:27700 → EPSG:4326)
- [x] Loaded 14 DNO boundaries to `neso_dno_boundaries`
- [x] Generated correct GeoJSON with real boundaries (3,552+ coordinate points)
- [x] Started HTTP server for local testing
- [x] Added comprehensive console logging for debugging
- [x] Fixed bounds calculation for MultiPolygon geometries

### ⚠️ In Progress
- [ ] Verifying map displays real DNO boundaries (not rectangles)
- [ ] Confirming all 14 MPAN IDs (10-23) are visible
- [ ] Testing click interactions and info windows

### 🎯 Next Steps
1. Verify map displays correctly in browser
2. Test info window popups for each DNO region
3. Add power station overlay functionality
4. Implement search/filter by MPAN ID
5. Add legend showing all DNOs
6. Export functionality for analysis

## Future Enhancements

### Phase 2: Power Stations
- Load power station locations from BigQuery
- Display as markers on map
- Show which DNO region each station is in
- Filter by fuel type/capacity

### Phase 3: Interactive Analysis
- Click DNO region to see stations within it
- Filter by date/time for demand analysis
- Show real-time generation by region
- Compare regional statistics

### Phase 4: Data Export
- Export selected DNO data as CSV
- Generate reports by region
- API endpoints for programmatic access

## Technical Notes

### Why MultiPolygon?
DNO regions are MultiPolygon geometries because:
- Some areas include islands (e.g., Scottish islands)
- Some regions have geographic discontinuities
- Accurate representation of complex boundaries

### Why Static GeoJSON?
Using a static file instead of API because:
- **Performance**: Faster load times (no database query)
- **Simplicity**: No backend server needed
- **Caching**: Browser can cache the file
- **Reliability**: Works even if BigQuery is down

For real-time updates, could implement:
```python
# Flask API endpoint (future enhancement)
@app.route('/api/dno-regions')
def get_dno_regions():
    query = "SELECT ... FROM neso_dno_boundaries"
    results = bigquery_client.query(query)
    return jsonify(results)
```

### Coordinate Precision
- BigQuery: Full precision maintained
- GeoJSON: 6-8 decimal places sufficient
- Display: More precision = larger file size
- Trade-off: Accuracy vs performance

## References

- **NESO Data Portal**: https://www.neso.energy/
- **DNO License Areas**: Official GB distribution network boundaries
- **GSP Groups**: Grid Supply Point groupings A-P (excluding I, O)
- **EPSG:27700**: British National Grid (Ordnance Survey)
- **EPSG:4326**: WGS84 (GPS coordinates)
- **BigQuery Geography**: https://cloud.google.com/bigquery/docs/geospatial-data
- **Google Maps API**: https://developers.google.com/maps/documentation

## Support

For issues or questions:
1. Check browser console for error messages
2. Verify HTTP server is running: `lsof -i :8765`
3. Verify GeoJSON file exists and is valid
4. Check BigQuery tables have 14 records each
5. Review this documentation for troubleshooting steps

---

**Document Version**: 1.0
**Last Tested**: 1 November 2025
**Status**: ✅ Data pipeline complete, ⚠️ Map display being verified
