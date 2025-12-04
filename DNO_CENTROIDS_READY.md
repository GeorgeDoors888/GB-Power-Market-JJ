# DNO Centroids Generated - Ready for Google Sheets

**Date**: December 4, 2025  
**Machine**: Dell localhost-0 (100.119.237.107) via Tailscale  
**Status**: ✅ COMPLETE

---

## What Was Done

Ran **Option B (DNO Centroids)** from the DNO GeoChart Mapping Guide on the Dell machine.

### Step 1: Export DNO Boundaries from BigQuery ✅

**Script**: `export_dno_geojson.py`  
**Output**: `dno_boundaries_export.geojson` (5.7 MB)  
**Records**: 14 DNO regions

```
ENWL  - North West England
NGED  - East Midlands
NGED  - West Midlands
NGED  - South Wales
NGED  - South West England
NPG   - North East England
NPG   - Yorkshire
SPEN  - North Wales, Merseyside and Cheshire
SPEN  - South and Central Scotland
SSEN  - North Scotland
SSEN  - Southern England
UKPN  - East England
UKPN  - London
UKPN  - South East England
```

### Step 2: Calculate Centroids ✅

**Script**: `generate_dno_centroids.py`  
**Output**: `dno_centroids.csv` (897 bytes)  
**Method**: GeoPandas centroid calculation

### Step 3: Download to Local Machine ✅

**File**: `dno_centroids.csv` in project root

---

## CSV Contents

```csv
dno_id,dno_name,lat,lon,size
ENWL,North West England,54.21,-2.70,1
NGED,East Midlands,52.77,-0.89,1
NGED,West Midlands,52.33,-2.32,1
NGED,South Wales,51.89,-3.84,1
NGED,South West England,50.77,-3.83,1
NPG,North East England,54.68,-1.64,1
NPG,Yorkshire,53.70,-0.99,1
SPEN,"North Wales, Merseyside and Cheshire",52.98,-3.45,1
SPEN,South and Central Scotland,55.53,-3.65,1
SSEN,North Scotland,57.36,-4.41,1
SSEN,Southern England,51.23,-1.52,1
UKPN,East England,52.22,0.50,1
UKPN,London,51.50,-0.03,1
UKPN,South East England,51.14,0.32,1
```

---

## Next Steps: Google Sheets Setup

### 1. Import CSV to Google Sheets

1. Open Dashboard: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
2. Create new tab: **DNO_CENTROIDS**
3. File → Import → Upload `dno_centroids.csv`
4. Import to DNO_CENTROIDS tab

### 2. Add "Value to Color" Column

In column F (or next available), add header: **value**

In F2, add formula:
```
=IF('Dashboard V3'!$B$10="", 0, IF(B2='Dashboard V3'!$B$10, 1, 0))
```

Fill formula down to F15.

**What this does**: 
- When user selects DNO in Dashboard V3 cell B10
- Value = 1 for selected DNO's centroid
- Value = 0 for all other DNOs
- GeoChart highlights the selected DNO marker

### 3. Create GeoChart

1. **Select data**: DNO_CENTROIDS!A:F (all columns)
2. **Insert → Chart**
3. **Chart Editor**:
   - Chart type: **Geo chart**
   - Region: **World** (or United Kingdom)
   - Display mode: **Markers**
   - Latitude: Column C (lat)
   - Longitude: Column D (lon)
   - Color: Column F (value)
   - Size: Column E (size) - optional

4. **Style**:
   - Min value color (0): Light grey #CCCCCC
   - Max value color (1): Bright highlight #FF6B35 or #4285F4
   - Show tooltips: ✅
   - Marker size: Medium or Large

### 4. Test Interactivity

1. Go to Dashboard V3
2. Change cell B10 to a DNO ID (e.g., "ENWL", "NPG", "UKPN")
3. GeoChart should highlight that DNO's marker
4. Hover over markers to see DNO name

---

## Comparison: Centroids vs Full Boundaries

| Feature | Centroids (Done) | Postcode Districts (Future) |
|---------|------------------|---------------------------|
| Setup Time | ✅ 30 min | ⏳ 2-3 hours |
| Visual | Markers/Points | Filled regions |
| Accuracy | Approximate center | ~95% accurate boundaries |
| Interactivity | ✅ Full | ✅ Full |
| Ready Now | ✅ YES | ❌ Need UK postcode data |

---

## Files on Dell Machine

**Location**: `/home/george/dno-mapping/`

```
dno_boundaries_export.geojson  (5.7 MB) - Full polygon boundaries
dno_centroids.csv              (897 B)  - Lat/lon centroids
export_dno_geojson.py                   - BigQuery export script
generate_dno_centroids.py               - Centroid calculator
```

---

## Future Enhancement: Full Postcode District Mapping

To implement **Option A (Full Boundaries)** later:

1. **Download UK Postcode Districts**:
   - ONS Open Geography Portal
   - Postcode Districts (polygons)
   - ~2,500 districts covering UK

2. **Run Spatial Join**:
   ```bash
   ssh george@100.119.237.107
   cd ~/dno-mapping
   python3 map_dno_to_postcodes.py
   ```

3. **Import to Sheets**:
   - New tab: DNO_PCD_MAP
   - ~2,500 rows of postcode → DNO mappings
   - GeoChart displays filled regions

**Benefit**: Full shaded DNO regions instead of points  
**Effort**: Additional 2-3 hours for postcode data acquisition

---

## Technical Notes

- **Python**: 3.9.23 (Dell machine)
- **GeoPandas**: 1.0.1 (installed)
- **Shapely**: 2.0.7 (installed)
- **BigQuery**: inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries
- **CRS**: EPSG:4326 (WGS84 lat/lon)

---

## Support

**Documentation**: See `DNO_GEOCHART_MAPPING_GUIDE.md` for full details  
**Contact**: george@upowerenergy.uk  
**Status**: Ready to import to Google Sheets ✅

---

*Generated: December 4, 2025*
