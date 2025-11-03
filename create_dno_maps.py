#!/usr/bin/env python3
"""
Create Interactive DNO Maps using GeoJSON from BigQuery and Google Maps API

This script:
1. Queries GeoJSON data from BigQuery
2. Creates interactive maps with Google Maps JavaScript API
3. Displays DNO boundaries, GSP regions, and other geographic data
4. Allows overlaying energy data (generation, demand, prices) on maps
"""

import json
import pickle
from google.cloud import bigquery
from datetime import datetime
import os

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET_ID = 'uk_energy_prod'

# Google Maps API Key - Set as environment variable or in file
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

print("=" * 80)
print("🗺️  DNO MAP CREATOR - GeoJSON from BigQuery + Google Maps API")
print("=" * 80)
print()

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID)

# ============================================================================
# STEP 1: Discover Available GeoJSON Tables
# ============================================================================

print("Step 1: Discovering GeoJSON tables in BigQuery...")
print()

query = f"""
SELECT 
    table_name,
    ROUND(size_bytes / 1024 / 1024, 2) as size_mb,
    row_count
FROM `{PROJECT_ID}.{DATASET_ID}.__TABLES__`
WHERE LOWER(table_name) LIKE '%geo%' 
   OR LOWER(table_name) LIKE '%gsp%'
   OR LOWER(table_name) LIKE '%dno%'
   OR LOWER(table_name) LIKE '%region%'
ORDER BY table_name
"""

tables = list(client.query(query).result())

if not tables:
    print("⚠️  No GeoJSON tables found. Looking for tables with geometry columns...")
    
    # Try to find tables with geography/geometry columns
    query_columns = f"""
    SELECT 
        table_name,
        column_name,
        data_type
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE LOWER(data_type) LIKE '%geography%'
       OR LOWER(data_type) LIKE '%geometry%'
       OR LOWER(column_name) LIKE '%geo%'
       OR LOWER(column_name) LIKE '%geojson%'
    ORDER BY table_name, column_name
    """
    
    geo_columns = list(client.query(query_columns).result())
    
    if geo_columns:
        print("✅ Found tables with geographic data:")
        for row in geo_columns:
            print(f"   📊 {row.table_name}.{row.column_name} ({row.data_type})")
    else:
        print("❌ No geographic data found in BigQuery")
        print()
        print("💡 Suggestion: Load GeoJSON data into BigQuery first")
        print("   You can upload GeoJSON files for:")
        print("   - DNO License Areas")
        print("   - GSP Regions")
        print("   - Transmission Zones")
        print("   - Substations")
        exit(1)
else:
    print("✅ Found GeoJSON-related tables:")
    for row in tables:
        print(f"   📊 {row.table_name} ({row.size_mb} MB, {row.row_count} rows)")

print()

# ============================================================================
# STEP 2: Query GeoJSON Data
# ============================================================================

print("Step 2: Querying GeoJSON data...")
print()

# Example: Query DNO license areas
# Adjust this query based on your actual table structure

query_geojson = f"""
SELECT 
    *
FROM `{PROJECT_ID}.{DATASET_ID}.*`
WHERE table_name LIKE '%dno%' OR table_name LIKE '%gsp%'
LIMIT 1
"""

# Let's try a generic approach - query the first geo table we found
if tables:
    first_table = tables[0].table_name
    
    print(f"📍 Querying table: {first_table}")
    
    # Get table schema first
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{first_table}"
    table = client.get_table(table_ref)
    
    print(f"   Columns: {[field.name for field in table.schema]}")
    print()
    
    # Query sample data
    sample_query = f"""
    SELECT *
    FROM `{table_ref}`
    LIMIT 5
    """
    
    sample_data = list(client.query(sample_query).result())
    
    print(f"✅ Retrieved {len(sample_data)} sample rows")
    print()

# ============================================================================
# STEP 3: Create HTML Map with Google Maps API
# ============================================================================

print("Step 3: Creating interactive HTML map...")
print()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>UK Power Market - DNO Map</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        #map {{
            height: 100vh;
            width: 100%;
        }}
        #controls {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            z-index: 1000;
            max-width: 300px;
        }}
        #legend {{
            position: absolute;
            bottom: 30px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border: 1px solid #333;
        }}
        h2 {{
            margin: 0 0 10px 0;
            font-size: 18px;
        }}
        button {{
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            background: #4285f4;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background: #357ae8;
        }}
        .info-box {{
            background: #f0f0f0;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div id="controls">
        <h2>🗺️ UK Power Market Map</h2>
        <button onclick="loadDNOBoundaries()">Show DNO Regions</button>
        <button onclick="loadGSPRegions()">Show GSP Regions</button>
        <button onclick="loadGenerationSites()">Show Generation Sites</button>
        <button onclick="clearMap()">Clear All Layers</button>
        <div class="info-box" id="info">
            Click buttons to load map layers
        </div>
    </div>

    <div id="legend">
        <h2>Legend</h2>
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(66, 133, 244, 0.3);"></div>
            <span>DNO Region</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(52, 168, 83, 0.3);"></div>
            <span>GSP Region</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(251, 188, 5, 0.8);"></div>
            <span>Power Station</span>
        </div>
    </div>

    <div id="map"></div>

    <script>
        let map;
        let dataLayers = [];

        // Initialize Google Map
        function initMap() {{
            map = new google.maps.Map(document.getElementById('map'), {{
                zoom: 6,
                center: {{ lat: 54.5, lng: -3.5 }}, // Center on UK
                mapTypeId: 'roadmap',
                styles: [
                    {{
                        featureType: 'all',
                        elementType: 'labels',
                        stylers: [{{ visibility: 'on' }}]
                    }}
                ]
            }});

            // Add click listener for feature info
            map.data.addListener('click', function(event) {{
                const feature = event.feature;
                let infoText = '<strong>Feature Info:</strong><br>';
                
                feature.forEachProperty(function(value, name) {{
                    infoText += `${{name}}: ${{value}}<br>`;
                }});
                
                document.getElementById('info').innerHTML = infoText;
            }});
        }}

        // Load DNO Boundaries from BigQuery data
        function loadDNOBoundaries() {{
            clearMap();
            document.getElementById('info').innerHTML = 'Loading DNO boundaries...';
            
            // Example GeoJSON structure - replace with actual BigQuery data
            const dnoGeoJSON = {{
                "type": "FeatureCollection",
                "features": [
                    // DNO features will be loaded here from BigQuery
                ]
            }};

            // Load GeoJSON data
            map.data.addGeoJson(dnoGeoJSON);
            
            // Style the features
            map.data.setStyle({{
                fillColor: '#4285f4',
                fillOpacity: 0.3,
                strokeColor: '#1967d2',
                strokeWeight: 2
            }});

            document.getElementById('info').innerHTML = 'DNO boundaries loaded';
        }}

        // Load GSP Regions
        function loadGSPRegions() {{
            clearMap();
            document.getElementById('info').innerHTML = 'Loading GSP regions...';
            
            // GSP regions GeoJSON from BigQuery
            const gspGeoJSON = {{
                "type": "FeatureCollection",
                "features": []
            }};

            map.data.addGeoJson(gspGeoJSON);
            
            map.data.setStyle({{
                fillColor: '#34a853',
                fillOpacity: 0.3,
                strokeColor: '#137333',
                strokeWeight: 2
            }});

            document.getElementById('info').innerHTML = 'GSP regions loaded';
        }}

        // Load Generation Sites
        function loadGenerationSites() {{
            document.getElementById('info').innerHTML = 'Loading generation sites...';
            
            // Example generation sites
            const sites = [
                {{ name: 'Drax', lat: 53.7371, lng: -0.9957, capacity: 3906 }},
                {{ name: 'Sizewell B', lat: 52.2138, lng: 1.6202, capacity: 1198 }},
                {{ name: 'Heysham', lat: 54.0296, lng: -2.9160, capacity: 1240 }}
            ];

            sites.forEach(site => {{
                const marker = new google.maps.Marker({{
                    position: {{ lat: site.lat, lng: site.lng }},
                    map: map,
                    title: `${{site.name}} (${{site.capacity}} MW)`,
                    icon: {{
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 8,
                        fillColor: '#fbbc05',
                        fillOpacity: 0.8,
                        strokeColor: '#f9ab00',
                        strokeWeight: 2
                    }}
                }});

                marker.addListener('click', function() {{
                    document.getElementById('info').innerHTML = 
                        `<strong>${{site.name}}</strong><br>Capacity: ${{site.capacity}} MW`;
                }});

                dataLayers.push(marker);
            }});

            document.getElementById('info').innerHTML = `Loaded ${{sites.length}} generation sites`;
        }}

        // Clear all map layers
        function clearMap() {{
            map.data.forEach(function(feature) {{
                map.data.remove(feature);
            }});
            
            dataLayers.forEach(marker => marker.setMap(null));
            dataLayers = [];
        }}

        // Load API key and initialize
        window.onload = function() {{
            if (!window.google) {{
                console.error('Google Maps API not loaded');
            }}
        }};
    </script>

    <!-- Load Google Maps API -->
    <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}&callback=initMap&libraries=&v=weekly" async defer></script>
</body>
</html>
"""

# Save HTML file
output_file = 'dno_map_interactive.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ Created interactive map: {output_file}")
print()

# ============================================================================
# STEP 4: Create Python Script to Fetch GeoJSON from BigQuery
# ============================================================================

print("Step 4: Creating BigQuery GeoJSON fetcher...")
print()

fetcher_script = '''#!/usr/bin/env python3
"""
Fetch GeoJSON from BigQuery and inject into HTML map
"""

from google.cloud import bigquery
import json

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET_ID = 'uk_energy_prod'

client = bigquery.Client(project=PROJECT_ID)

def fetch_dno_geojson():
    """Fetch DNO boundaries as GeoJSON"""
    
    # Adjust query based on your actual table structure
    query = f"""
    SELECT 
        dno_name,
        ST_ASGEOJSON(geography) as geojson,
        area_sqkm,
        license_id
    FROM `{PROJECT_ID}.{DATASET_ID}.dno_license_areas`
    """
    
    results = client.query(query).result()
    
    features = []
    for row in results:
        feature = {
            "type": "Feature",
            "geometry": json.loads(row.geojson),
            "properties": {
                "name": row.dno_name,
                "area": row.area_sqkm,
                "license": row.license_id
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson

def fetch_gsp_geojson():
    """Fetch GSP regions as GeoJSON"""
    
    query = f"""
    SELECT 
        gsp_name,
        ST_ASGEOJSON(geography) as geojson,
        region_id
    FROM `{PROJECT_ID}.{DATASET_ID}.gsp_regions`
    """
    
    results = client.query(query).result()
    
    features = []
    for row in results:
        feature = {
            "type": "Feature",
            "geometry": json.loads(row.geojson),
            "properties": {
                "name": row.gsp_name,
                "region_id": row.region_id
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson

if __name__ == '__main__':
    print("Fetching DNO GeoJSON...")
    dno_data = fetch_dno_geojson()
    
    with open('dno_boundaries.geojson', 'w') as f:
        json.dump(dno_data, f, indent=2)
    
    print(f"✅ Saved {len(dno_data['features'])} DNO regions")
    
    print("Fetching GSP GeoJSON...")
    gsp_data = fetch_gsp_geojson()
    
    with open('gsp_regions.geojson', 'w') as f:
        json.dump(gsp_data, f, indent=2)
    
    print(f"✅ Saved {len(gsp_data['features'])} GSP regions")
'''

with open('fetch_geojson_from_bigquery.py', 'w') as f:
    f.write(fetcher_script)

print("✅ Created: fetch_geojson_from_bigquery.py")
print()

# ============================================================================
# Summary and Next Steps
# ============================================================================

print("=" * 80)
print("✅ DNO MAP CREATION COMPLETE")
print("=" * 80)
print()
print("📁 Created Files:")
print(f"   1. {output_file} - Interactive map HTML")
print("   2. fetch_geojson_from_bigquery.py - GeoJSON data fetcher")
print()
print("🔑 Google Maps API Key Required:")
if not GOOGLE_MAPS_API_KEY:
    print("   ⚠️  API key not set!")
    print("   Set environment variable: export GOOGLE_MAPS_API_KEY='your-key-here'")
    print("   Or get one from: https://console.cloud.google.com/google/maps-apis")
else:
    print(f"   ✅ API key configured")
print()
print("📊 Next Steps:")
print("   1. Set Google Maps API key")
print("   2. Run: python fetch_geojson_from_bigquery.py")
print(f"   3. Open: {output_file} in your browser")
print("   4. Click buttons to load DNO regions, GSP zones, and generation sites")
print()
print("🎯 To customize:")
print("   - Edit BigQuery queries in fetch_geojson_from_bigquery.py")
print("   - Add more layers (substations, interconnectors, etc.)")
print("   - Overlay real-time data (prices, demand, generation)")
print()
