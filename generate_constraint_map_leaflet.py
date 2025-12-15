#!/usr/bin/env python3
"""
Generate Constraint Map with Leaflet (OpenStreetMap)
NO API KEY REQUIRED - Uses free OpenStreetMap tiles
"""

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
DASHBOARD_SHEET = "Dashboard"
DATA_RANGE = "A116:H126"

# Coordinate lookup
BOUNDARY_COORDS = {
    'BRASIZEX': {'lat': 51.8, 'lng': -2.0},
    'ERROEX': {'lat': 53.5, 'lng': -2.5},
    'ESTEX': {'lat': 51.5, 'lng': 0.5},
    'FLOWSTH': {'lat': 52.0, 'lng': -1.5},
    'GALLEX': {'lat': 53.0, 'lng': -3.0},
    'GETEX': {'lat': 52.5, 'lng': -1.0},
    'GM+SNOW5A': {'lat': 53.5, 'lng': -2.2},
    'HARSPNBLY': {'lat': 55.0, 'lng': -3.5},
    'NKILGRMO': {'lat': 56.5, 'lng': -5.0},
    'SCOTEX': {'lat': 55.5, 'lng': -3.0}
}

def fetch_constraint_data():
    """Fetch constraint data from Google Sheets"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    
    sheets_service = build('sheets', 'v4', credentials=credentials)
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{DASHBOARD_SHEET}!{DATA_RANGE}"
    ).execute()
    
    values = result.get('values', [])
    
    constraints = []
    for i, row in enumerate(values[1:], start=1):
        if len(row) > 0 and row[0]:
            boundary_id = str(row[0])
            coords = BOUNDARY_COORDS.get(boundary_id, {})
            
            constraint = {
                'boundary_id': boundary_id,
                'name': str(row[1] if len(row) > 1 else 'Unknown'),
                'flow_mw': float(row[2]) if len(row) > 2 and row[2] else 0,
                'limit_mw': float(row[3]) if len(row) > 3 and row[3] else 0,
                'util_pct': parse_percent(row[4]) if len(row) > 4 else 0,
                'margin_mw': float(row[5]) if len(row) > 5 and row[5] else 0,
                'status': str(row[6] if len(row) > 6 else 'Unknown'),
                'direction': str(row[7] if len(row) > 7 else 'N/A'),
                'lat': coords.get('lat', 54.5),
                'lng': coords.get('lng', -2.5)
            }
            constraints.append(constraint)
    
    return constraints

def parse_percent(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.replace('%', '')) if value else 0
    return 0

def generate_leaflet_html(constraints):
    """Generate HTML with Leaflet (no API key needed)"""
    
    constraints_json = json.dumps(constraints, indent=2)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GB Transmission Constraints Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            height: 100vh;
            overflow: hidden;
        }}
        #map {{
            height: 100%;
            width: 100%;
        }}
        .legend {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            z-index: 1000;
            font-size: 12px;
        }}
        .legend h4 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #333;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 8px;
            border: 2px solid #fff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }}
        .update-time {{
            position: absolute;
            bottom: 30px;
            left: 10px;
            background: white;
            padding: 8px 12px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            font-size: 11px;
            color: #666;
            z-index: 1000;
        }}
        .leaflet-popup-content {{
            font-size: 13px;
            line-height: 1.6;
        }}
        .leaflet-popup-content h3 {{
            margin: 0 0 10px 0;
            color: #1a73e8;
            font-size: 15px;
        }}
        .leaflet-popup-content table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .leaflet-popup-content td {{
            padding: 3px 6px;
        }}
        .leaflet-popup-content td:first-child {{
            font-weight: 600;
            color: #666;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="legend">
        <h4>🗺️ GB Transmission Constraints</h4>
        <div class="legend-item">
            <span class="legend-color" style="background: #4CAF50;"></span>
            <span>&lt;50% Normal</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #FFC107;"></span>
            <span>50-75% Moderate</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #FF9800;"></span>
            <span>75-90% High</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #F44336;"></span>
            <span>&gt;90% Critical</span>
        </div>
    </div>
    
    <div class="update-time">
        Updated: {timestamp}<br>
        <small>Powered by OpenStreetMap</small>
    </div>
    
    <script>
        // Embedded constraint data
        const constraints = {constraints_json};
        
        // Create map centered on UK
        const map = L.map('map').setView([54.5, -3.5], 6);
        
        // Add OpenStreetMap tiles (no API key needed!)
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19
        }}).addTo(map);
        
        // Create markers for each constraint
        constraints.forEach(constraint => {{
            createMarker(constraint);
        }});
        
        console.log('✅ Map loaded with ' + constraints.length + ' constraints');
        
        function createMarker(c) {{
            const color = getMarkerColor(c.util_pct);
            
            // Create circle marker
            const marker = L.circleMarker([c.lat, c.lng], {{
                radius: 10,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            }}).addTo(map);
            
            // Create popup content
            const popupContent = `
                <h3>${{c.boundary_id}} - ${{c.name}}</h3>
                <table>
                    <tr><td>Flow:</td><td>${{c.flow_mw.toFixed(0)}} MW</td></tr>
                    <tr><td>Limit:</td><td>${{c.limit_mw.toFixed(0)}} MW</td></tr>
                    <tr><td>Utilization:</td><td>${{c.util_pct.toFixed(1)}}%</td></tr>
                    <tr><td>Margin:</td><td>${{c.margin_mw.toFixed(0)}} MW</td></tr>
                    <tr><td>Status:</td><td>${{c.status}}</td></tr>
                    <tr><td>Direction:</td><td>${{c.direction}}</td></tr>
                </table>
            `;
            
            marker.bindPopup(popupContent);
        }}
        
        function getMarkerColor(utilization) {{
            if (utilization < 50) return '#4CAF50';  // Green
            if (utilization < 75) return '#FFC107';  // Yellow
            if (utilization < 90) return '#FF9800';  // Orange
            return '#F44336';  // Red
        }}
    </script>
</body>
</html>'''
    
    return html

def main():
    print("=" * 80)
    print("GENERATING LEAFLET MAP (NO API KEY NEEDED)")
    print("=" * 80)
    
    # Fetch data
    print("\n📊 Fetching constraint data...")
    try:
        constraints = fetch_constraint_data()
        print(f"✅ Retrieved {len(constraints)} constraints")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    # Generate HTML
    print("\n🗺️ Generating Leaflet map...")
    html = generate_leaflet_html(constraints)
    
    # Save files
    output_file = "constraint_map_leaflet.html"
    with open(output_file, 'w') as f:
        f.write(html)
    print(f"✅ Saved: {output_file}")
    
    # Also save for Apps Script
    dashboard_file = "dashboard/apps-script/ConstraintMap_Leaflet.html"
    with open(dashboard_file, 'w') as f:
        f.write(html)
    print(f"✅ Saved: {dashboard_file}")
    
    print("\n" + "=" * 80)
    print("SUCCESS - NO API KEY REQUIRED!")
    print("=" * 80)
    print("\n✅ Advantages of Leaflet:")
    print("   - No API key needed")
    print("   - No billing required")
    print("   - No usage limits")
    print("   - Open source (OpenStreetMap)")
    print("   - Works offline with cached tiles")
    
    print("\n📋 Open the map:")
    print(f"   open {output_file}")
    
    print("\n🔄 For Apps Script:")
    print(f"   - Upload: {dashboard_file}")
    print("   - Use with: constraint_map_minimal.gs")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
