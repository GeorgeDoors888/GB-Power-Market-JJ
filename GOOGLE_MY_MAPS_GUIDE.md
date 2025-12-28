# Google My Maps - DNO Boundary Import Guide

## Quick Start (5 minutes)

### Step 1: Convert GeoJSON to KML
Google My Maps requires KML format. Convert using one of these methods:

**Option A: Online Converter (Easiest)**
1. Go to: https://mygeodata.cloud/converter/geojson-to-kml
2. Upload: `dno_boundaries.geojson`
3. Click "Convert"
4. Download: `dno_boundaries.kml`

**Option B: Using ogr2ogr (if GDAL installed)**
```bash
ogr2ogr -f KML dno_boundaries.kml dno_boundaries.geojson
```

**Option C: Python script (provided below)**
```bash
python3 convert_geojson_to_kml.py
```

### Step 2: Import to Google My Maps
1. Go to: https://www.google.com/mymaps
2. Click "**+ CREATE A NEW MAP**"
3. Click "**Import**" (under the search box)
4. Select/drag `dno_boundaries.kml`
5. Choose columns for labels:
   - **Name**: `area_name` or `dno_name`
   - **Description**: Check "Include data from this column"
6. Click "**Finish**"

### Step 3: Style the Map
1. Click on the layer name → "**Individual styles**"
2. For each DNO region:
   - Click the paint bucket icon
   - Set fill color based on cost (darker = higher cost)
   - Adjust opacity to 50-70%
3. Or use "**Uniform style**" for consistent coloring

### Step 4: Share/Embed
- **Share**: Click "Share" → Copy link
- **Embed**: Click ⋮ menu → "Embed on my site" → Copy iframe code
- **Permissions**: Set to "Public" or "Anyone with the link"

---

## Alternative: Google Maps JavaScript API

If you need more control (custom colors, interactive features), use the JavaScript API:

### Setup (One-time)
1. Get API key: https://console.cloud.google.com/apis/credentials
2. Enable "Maps JavaScript API"
3. Free tier: 28,000 map loads/month

### Implementation
```html
<!DOCTYPE html>
<html>
<head>
    <title>UK DNO Constraint Costs</title>
    <style>
        #map { height: 100vh; width: 100%; }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <script>
        function initMap() {
            const map = new google.maps.Map(document.getElementById('map'), {
                center: { lat: 54.5, lng: -3.5 },
                zoom: 6
            });

            // Load GeoJSON (must be on same domain or CORS-enabled)
            map.data.loadGeoJson('dno_boundaries.geojson');

            // Style by cost
            map.data.setStyle(function(feature) {
                const cost = feature.getProperty('total_cost_gbp');
                const opacity = Math.min(cost / 10000000, 0.7);
                return {
                    fillColor: '#2196F3',
                    fillOpacity: opacity,
                    strokeColor: '#1565C0',
                    strokeWeight: 2
                };
            });

            // Click handler
            map.data.addListener('click', function(event) {
                const name = event.feature.getProperty('dno_name');
                const cost = (event.feature.getProperty('cost_millions')).toFixed(2);
                alert(name + ': £' + cost + 'M');
            });
        }
    </script>
    
    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap" async defer></script>
</body>
</html>
```

---

## Troubleshooting

### "Upload failed" on My Maps
- **File too large**: GeoJSON is 5.6MB, which may exceed limit
- **Solution**: Simplify geometries using `mapshaper`:
  ```bash
  npm install -g mapshaper
  mapshaper dno_boundaries.geojson -simplify 20% -o dno_boundaries_simple.geojson
  ```

### "No features found" error
- GeoJSON has nested FeatureCollection
- Use the conversion script below (handles nesting)

### Polygons not showing
- Check coordinate order: GeoJSON uses [lng, lat], KML uses lat,lng
- Conversion script handles this automatically

---

## Files in This Project

| File | Size | Purpose |
|------|------|---------|
| `dno_boundaries.geojson` | 5.6MB | Source data (14 DNO regions) |
| `dno_boundaries.kml` | TBD | Google My Maps import file |
| `dno_constraint_map.html` | 500KB | Standalone interactive map (Folium/Leaflet) |
| `convert_geojson_to_kml.py` | 3KB | Conversion utility script |
| `export_dno_for_google_maps.py` | 10KB | Original export script |

---

## Comparison: My Maps vs JavaScript API

| Feature | Google My Maps | Maps JavaScript API |
|---------|----------------|---------------------|
| **Setup** | No coding required | Requires HTML/JS coding |
| **API Key** | Not needed | Required (free tier available) |
| **Styling** | Basic (manual per-feature) | Full control (programmatic) |
| **Sharing** | Built-in share/embed | Self-hosted or embed iframe |
| **Data Limit** | ~10MB KML, 2000 features | No hard limit (performance-based) |
| **Interactive** | Click for info popups | Custom interactivity |
| **Best For** | Quick visualization, sharing | Custom dashboards, integration |

---

## Next Steps

1. **Test**: Convert and import `dno_boundaries.geojson` to My Maps
2. **Integrate**: Embed map in Google Sheets dashboard (Insert → Drawing → Import from URL)
3. **Automate**: Schedule daily updates to refresh constraint cost data
4. **Enhance**: Add time-series animation showing monthly cost trends

---

**Generated**: 2025-12-28  
**Data Source**: NESO DNO boundaries + BigQuery constraint costs  
**Total DNOs**: 14 regions covering England, Scotland, Wales
