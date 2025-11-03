# 🗺️ DNO Energy Maps with Google Maps API

**Created**: 31 October 2025  
**Project**: GB Power Market JJ

---

## Overview

Interactive maps showing UK Distribution Network Operator (DNO) regions with real-time energy data overlay using Google Maps API and BigQuery GeoJSON data.

---

## ✅ Created Files

### 1. **dno_energy_map_advanced.html** (Main Map)
   - Interactive UK energy map with professional UI
   - Multiple data layers (DNO, GSP, generation, demand, prices)
   - Real-time statistics dashboard
   - Click-to-explore features
   - **Size**: ~20 KB
   - **Technology**: HTML + JavaScript + Google Maps API

### 2. **create_dno_maps.py** (Basic Creator)
   - Discovers GeoJSON tables in BigQuery
   - Creates basic interactive map
   - Generates data fetcher script
   - **Size**: ~15 KB

### 3. **create_dno_maps_advanced.py** (Advanced Creator)
   - Creates professional map with full UI
   - Integrates BigQuery real-time data
   - Generates Flask API server
   - **Size**: ~20 KB

### 4. **map_api_server.py** (API Server)
   - Flask API to serve GeoJSON from BigQuery
   - Endpoints for DNO regions, GSP zones, live stats
   - **Size**: ~3 KB

---

## 🚀 Quick Start

### Step 1: Get Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Maps JavaScript API**
3. Create API key
4. Set environment variable:
   ```bash
   export GOOGLE_MAPS_API_KEY='your-key-here'
   ```

### Step 2: Open the Map

```bash
cd "/Users/georgemajor/GB Power Market JJ"

# Open in default browser
open dno_energy_map_advanced.html

# Or with specific browser
open -a "Google Chrome" dno_energy_map_advanced.html
```

### Step 3: (Optional) Start API Server for Live Data

```bash
# Install Flask if needed
pip install flask

# Start server
python map_api_server.py

# Server runs on http://localhost:5000
```

---

## 📊 Map Features

### Geographic Layers

| Layer | Description | Source |
|-------|-------------|--------|
| **DNO Regions** | 14 distribution network operator boundaries | BigQuery GeoJSON |
| **GSP Zones** | Grid Supply Point zones | BigQuery GeoJSON |
| **Transmission Zones** | National Grid transmission boundaries | BigQuery GeoJSON |
| **Substations** | Major substations | BigQuery |

### Energy Data Overlays

| Overlay | Description | Update Frequency |
|---------|-------------|------------------|
| **Generation Sites** | Power stations with capacity | Real-time |
| **Demand Heatmap** | Regional demand visualization | Every 5 min |
| **Price Heatmap** | System prices by region | Every 30 min |
| **Wind Farms** | Offshore/onshore wind installations | Real-time |
| **Power Flows** | Interconnector and grid flows | Real-time |
| **Congestion** | Grid congestion points | Real-time |

### Live Statistics

- **Total Generation**: Current UK generation (GW)
- **Renewables %**: Percentage from renewable sources
- **System Price**: Current wholesale price (£/MWh)
- **Frequency**: Grid frequency (Hz)

---

## 🎯 Usage Guide

### Loading Layers

1. **DNO Regions Button**
   - Shows 14 DNO boundaries
   - Color-coded by operator
   - Click region for details

2. **Generation Sites Button**
   - Displays power stations as markers
   - Size represents capacity
   - Color represents fuel type:
     - 🟢 Green = Wind/Renewable
     - 🟡 Yellow = Gas
     - 🔵 Blue = Nuclear
     - ⚫ Grey = Coal

3. **Price Heatmap Button**
   - Shows regional price variations
   - Gradient: Green (low) → Red (high)

4. **Clear All Layers**
   - Removes all active layers
   - Resets map to default view

### Interacting with Features

- **Click on regions**: View DNO details
- **Click on markers**: See power station info
- **Hover over heatmap**: View price data
- **Zoom/Pan**: Explore different areas

---

## 🔧 Configuration

### Setting Google Maps API Key

**Method 1: Environment Variable**
```bash
export GOOGLE_MAPS_API_KEY='AIza...'
```

**Method 2: Edit HTML File**
```html
<!-- Line 650 in dno_energy_map_advanced.html -->
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_KEY_HERE&callback=initMap"></script>
```

### BigQuery Table Structure

Expected GeoJSON tables in BigQuery:

```sql
-- DNO Regions
CREATE TABLE uk_energy_prod.dno_license_areas (
    dno_name STRING,
    geography GEOGRAPHY,
    license_id STRING,
    area_sqkm FLOAT64
);

-- GSP Zones
CREATE TABLE uk_energy_prod.gsp_regions (
    gsp_name STRING,
    geography GEOGRAPHY,
    region_id STRING
);
```

---

## 📡 API Endpoints (if using map_api_server.py)

### GET /api/geojson/dno-regions
Returns DNO boundaries as GeoJSON
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {...},
      "properties": {
        "dno_name": "UKPN London",
        "license_id": "10"
      }
    }
  ]
}
```

### GET /api/geojson/gsp-zones
Returns GSP zones as GeoJSON

### GET /api/live-stats
Returns real-time energy statistics
```json
{
  "total_generation": 34200,
  "renewables_pct": 45.3,
  "system_price": 76.50,
  "frequency": 49.98
}
```

---

## 🎨 Customization

### Adding New Power Stations

Edit `dno_energy_map_advanced.html`, line ~520:

```javascript
const powerStations = [
    { name: 'Your Station', lat: 51.5, lng: -0.1, capacity: 500, type: 'Gas' },
    // Add more stations...
];
```

### Changing Colors

Edit color schemes, line ~450:

```javascript
function getDNOColor(dnoName) {
    const colors = {
        'UKPN': '#667eea',  // Change to your color
        'SSEN': '#34a853',
        // ...
    };
}
```

### Adding Custom Layers

1. Create button in control panel HTML
2. Add JavaScript function:
```javascript
function loadYourLayer() {
    // Your layer loading code
}
```

---

## 🔍 Data Sources

### BigQuery Tables Used

| Table | Purpose | Update Frequency |
|-------|---------|------------------|
| `bmrs_fuelinst_unified` | Generation by fuel type | Real-time (30s) |
| `bmrs_freq` | System frequency | Real-time (1s) |
| `bmrs_mid` | Market prices | Real-time (5min) |
| `dno_license_areas` | DNO boundaries | Static |
| `gsp_regions` | GSP zones | Static |

### External Data

- **Google Maps API**: Base maps and geocoding
- **GeoJSON Files**: UK geographic boundaries
- **BMRS Data**: Real-time energy data (via IRIS)

---

## 🚨 Troubleshooting

### Map Not Loading

**Issue**: Blank map or "For development purposes only" watermark

**Solution**: 
1. Check API key is set correctly
2. Enable billing on Google Cloud project
3. Enable Maps JavaScript API

### No Data Appearing

**Issue**: Layers don't load or show data

**Solutions**:
1. Check BigQuery tables exist:
   ```sql
   SELECT table_name FROM `inner-cinema-476211-u9.uk_energy_prod.__TABLES__`
   WHERE table_name LIKE '%geo%'
   ```

2. Verify API server is running:
   ```bash
   curl http://localhost:5000/api/live-stats
   ```

3. Check browser console for errors (F12)

### Slow Performance

**Issue**: Map is slow or laggy

**Solutions**:
1. Reduce number of markers
2. Simplify GeoJSON polygons
3. Use clustering for dense markers
4. Limit data query time ranges

---

## 📈 Future Enhancements

### Planned Features

- [ ] Real-time data auto-refresh (every 5 min)
- [ ] Historical playback (time slider)
- [ ] Custom date range selection
- [ ] Export map as image/PDF
- [ ] 3D building overlays
- [ ] Weather layer integration
- [ ] Traffic/transport layer
- [ ] Comparison view (side-by-side)

### Advanced Analytics

- [ ] Power flow animation
- [ ] Congestion heatmap
- [ ] Price forecasting overlay
- [ ] Renewable generation predictions
- [ ] Grid stress indicators
- [ ] Carbon intensity mapping

---

## 🔗 Related Documentation

- `UPCLOUD_DEPLOYMENT_PLAN.md` - IRIS real-time data pipeline
- `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` - Data architecture
- `GOOGLE_SHEET_INFO.md` - Google Sheets integration
- `README.md` - Main project documentation

---

## 📚 Resources

### Google Maps API
- [Maps JavaScript API](https://developers.google.com/maps/documentation/javascript)
- [Data Layer](https://developers.google.com/maps/documentation/javascript/datalayer)
- [GeoJSON Support](https://developers.google.com/maps/documentation/javascript/importing_data)

### BigQuery GIS
- [Working with Geography](https://cloud.google.com/bigquery/docs/gis-data)
- [ST_ASGEOJSON Function](https://cloud.google.com/bigquery/docs/reference/standard-sql/geography_functions#st_asgeojson)
- [Loading GeoJSON](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-json#loading_geojson_data)

### UK Energy Data
- [BMRS Data Portal](https://www.bmrs.co.uk/)
- [Elexon API](https://www.elexon.co.uk/data/)
- [National Grid ESO](https://www.nationalgrideso.com/data-portal)

---

## ✅ Checklist

Before deploying:

- [ ] Google Maps API key obtained and set
- [ ] BigQuery GeoJSON tables loaded
- [ ] API server tested (if using live data)
- [ ] Browser compatibility checked (Chrome, Firefox, Safari)
- [ ] Mobile responsiveness verified
- [ ] Performance tested with full dataset
- [ ] Error handling implemented
- [ ] Documentation updated

---

**Status**: ✅ Ready to use  
**Last Updated**: 31 October 2025  
**Version**: 1.0
