#!/usr/bin/env python3
"""
Generate Standalone Constraint Map HTML
Uses Python to fetch data from Google Sheets and generate a complete HTML map
No Apps Script dependency - pure static HTML with embedded data
"""

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
DASHBOARD_SHEET = "Dashboard"
DATA_RANGE = "A116:H126"
GOOGLE_MAPS_API_KEY = "AIzaSyCsH49dmxEqcX0Hhi_UJGS8VvuGNLuggTQ"

# Coordinate lookup for boundaries
BOUNDARY_COORDS = {
    'BRASIZEX': {'lat': 51.8, 'lng': -2.0, 'desc': 'Bristol area'},
    'ERROEX': {'lat': 53.5, 'lng': -2.5, 'desc': 'North West'},
    'ESTEX': {'lat': 51.5, 'lng': 0.5, 'desc': 'Essex/East'},
    'FLOWSTH': {'lat': 52.0, 'lng': -1.5, 'desc': 'Flow South'},
    'GALLEX': {'lat': 53.0, 'lng': -3.0, 'desc': 'North Wales'},
    'GETEX': {'lat': 52.5, 'lng': -1.0, 'desc': 'Get Export'},
    'GM+SNOW5A': {'lat': 53.5, 'lng': -2.2, 'desc': 'Greater Manchester/Snowdonia'},
    'HARSPNBLY': {'lat': 55.0, 'lng': -3.5, 'desc': 'Harker-Stella/Penwortham-Blyth'},
    'NKILGRMO': {'lat': 56.5, 'lng': -5.0, 'desc': 'North Kilbride-Grudie-Moyle'},
    'SCOTEX': {'lat': 55.5, 'lng': -3.0, 'desc': 'Scotland Export'}
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
                'lng': coords.get('lng', -2.5),
                'description': coords.get('desc', '')
            }
            constraints.append(constraint)
    
    return constraints

def parse_percent(value):
    """Parse percentage value"""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.replace('%', '')) if value else 0
    return 0

def generate_html_map(constraints):
    """Generate standalone HTML map with embedded data"""
    
    constraints_json = json.dumps(constraints, indent=2)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GB Transmission Constraints Map</title>
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
        .info-window {{
            font-size: 14px;
            line-height: 1.6;
        }}
        .info-window h3 {{
            margin: 0 0 10px 0;
            color: #1a73e8;
            font-size: 16px;
        }}
        .info-window table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .info-window td {{
            padding: 4px 8px;
        }}
        .info-window td:first-child {{
            font-weight: 600;
            color: #666;
        }}
        .legend {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
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
            bottom: 10px;
            left: 10px;
            background: white;
            padding: 8px 12px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            font-size: 11px;
            color: #666;
            z-index: 1000;
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
        Updated: {timestamp}
    </div>
    
    <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}"></script>
    <script>
        // Embedded constraint data (from Google Sheets via Python)
        const constraints = {constraints_json};
        
        let map;
        
        function initMap() {{
            // Create map centered on UK
            map = new google.maps.Map(document.getElementById('map'), {{
                center: {{ lat: 54.5, lng: -3.5 }},
                zoom: 6,
                mapTypeId: 'roadmap',
                styles: [
                    {{
                        featureType: 'poi',
                        elementType: 'labels',
                        stylers: [{{ visibility: 'off' }}]
                    }}
                ]
            }});
            
            // Create markers for each constraint
            constraints.forEach(constraint => {{
                createMarker(constraint);
            }});
            
            console.log('✅ Map loaded with ' + constraints.length + ' constraints');
        }}
        
        function createMarker(constraint) {{
            const color = getMarkerColor(constraint.util_pct);
            const icon = {{
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: color,
                fillOpacity: 0.9,
                strokeColor: '#ffffff',
                strokeWeight: 2,
                scale: 10
            }};
            
            const marker = new google.maps.Marker({{
                position: {{ lat: constraint.lat, lng: constraint.lng }},
                map: map,
                title: constraint.boundary_id,
                icon: icon
            }});
            
            const infoContent = createInfoWindow(constraint);
            const infowindow = new google.maps.InfoWindow({{
                content: infoContent
            }});
            
            marker.addListener('click', () => {{
                infowindow.open(map, marker);
            }});
        }}
        
        function getMarkerColor(utilization) {{
            if (utilization < 50) return '#4CAF50';  // Green
            if (utilization < 75) return '#FFC107';  // Yellow
            if (utilization < 90) return '#FF9800';  // Orange
            return '#F44336';  // Red
        }}
        
        function createInfoWindow(c) {{
            return `
                <div class="info-window">
                    <h3>${{c.boundary_id}} - ${{c.name}}</h3>
                    <table>
                        <tr><td>Flow:</td><td>${{c.flow_mw.toFixed(0)}} MW</td></tr>
                        <tr><td>Limit:</td><td>${{c.limit_mw.toFixed(0)}} MW</td></tr>
                        <tr><td>Utilization:</td><td>${{c.util_pct.toFixed(1)}}%</td></tr>
                        <tr><td>Margin:</td><td>${{c.margin_mw.toFixed(0)}} MW</td></tr>
                        <tr><td>Status:</td><td>${{c.status}}</td></tr>
                        <tr><td>Direction:</td><td>${{c.direction}}</td></tr>
                    </table>
                </div>
            `;
        }}
        
        // Initialize map on load
        window.onload = initMap;
    </script>
</body>
</html>'''
    
    return html

def main():
    print("=" * 80)
    print("GENERATING STANDALONE CONSTRAINT MAP")
    print("=" * 80)
    
    # Fetch data from Sheets
    print("\n📊 Fetching constraint data from Google Sheets...")
    try:
        constraints = fetch_constraint_data()
        print(f"✅ Retrieved {len(constraints)} constraints")
        
        for c in constraints:
            print(f"   {c['boundary_id']}: {c['util_pct']:.1f}% ({c['status']})")
    
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return 1
    
    # Generate HTML
    print("\n🗺️ Generating HTML map...")
    html = generate_html_map(constraints)
    
    # Save standalone HTML
    output_file = "constraint_map_standalone.html"
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✅ Saved: {output_file}")
    
    # Also save as dashboard version (can be uploaded to Apps Script)
    dashboard_file = "dashboard/apps-script/ConstraintMap_Python.html"
    with open(dashboard_file, 'w') as f:
        f.write(html)
    
    print(f"✅ Saved: {dashboard_file}")
    
    print("\n" + "=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print("\n📋 Usage Options:")
    print("\n1. STANDALONE (No Apps Script needed):")
    print(f"   Open: {output_file}")
    print("   - Works locally in any browser")
    print("   - Data embedded in HTML")
    print("   - Refresh by re-running this script")
    
    print("\n2. APPS SCRIPT EMBED:")
    print(f"   - Upload {dashboard_file} to Apps Script")
    print("   - Rename to 'ConstraintMap.html'")
    print("   - No getConstraintData() function needed!")
    print("   - Data is pre-embedded from Python")
    
    print("\n3. AUTO-REFRESH (Recommended):")
    print("   - Add to crontab: */5 * * * * python3 generate_constraint_map_html.py")
    print("   - Host on web server (94.237.55.234)")
    print("   - Embed in Sheets via iframe")
    
    print("\n🎯 Next steps:")
    print("   1. Open constraint_map_standalone.html in browser")
    print("   2. Verify all 10 markers display correctly")
    print("   3. Deploy to Apps Script or web server")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
