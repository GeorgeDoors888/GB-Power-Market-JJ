#!/usr/bin/env python3
"""
Constraint Geo-Visualization
Creates geographic heat map of constraint costs using BMU locations
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def get_constraint_costs_by_gsp():
    """Get constraint costs aggregated by GSP region"""

    print("\n📊 Querying constraint costs by region...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Use BOALF acceptances with BMU canonical model
    sql = f"""
    WITH recent_constraints AS (
      SELECT
        b.acceptanceTime,
        b.bmUnit,
        ABS(b.levelTo - b.levelFrom) as volume_mw,
        EXTRACT(DATE FROM b.acceptanceTime) as date
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris` b
      WHERE b.acceptanceTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
    ),

    bmu_with_location AS (
      SELECT
        c.bmUnit,
        c.date,
        c.volume_mw,
        r.gsp_group,
        r.fuel_type_category
      FROM recent_constraints c
      JOIN `{PROJECT_ID}.{DATASET}.ref_bmu_canonical` r
        ON c.bmUnit = r.bmu_id
      WHERE r.gsp_group IS NOT NULL
    )

    SELECT
      gsp_group,
      COUNT(DISTINCT bmUnit) as bmu_count,
      COUNT(*) as acceptance_count,
      SUM(volume_mw) as total_volume_mw,
      AVG(volume_mw) as avg_volume_mw
    FROM bmu_with_location
    GROUP BY gsp_group
    ORDER BY total_volume_mw DESC
    """

    df = client.query(sql).to_dataframe()

    print(f"✅ Retrieved {len(df)} GSP regions with constraint data")

    return df

def get_gsp_coordinates():
    """Map GSP regions to approximate coordinates (UK grid)"""

    # Approximate coordinates for UK GSP groups (lat, lon)
    gsp_coords = {
        'Eastern': {'lat': 52.2053, 'lon': 0.1218, 'name': 'Eastern'},
        'East Midlands': {'lat': 52.9548, 'lon': -1.1581, 'name': 'East Midlands'},
        'London': {'lat': 51.5074, 'lon': -0.1278, 'name': 'London'},
        'Merseyside and Northern Wales': {'lat': 53.4084, 'lon': -2.9916, 'name': 'Merseyside & N Wales'},
        'Midlands': {'lat': 52.4862, 'lon': -1.8904, 'name': 'Midlands'},
        'North Eastern': {'lat': 54.9783, 'lon': -1.6178, 'name': 'North Eastern'},
        'North Western': {'lat': 53.4808, 'lon': -2.2426, 'name': 'North Western'},
        'Northern': {'lat': 54.5270, 'lon': -1.5528, 'name': 'Northern'},
        'North Scotland': {'lat': 57.4778, 'lon': -4.2247, 'name': 'North Scotland'},
        'South Eastern': {'lat': 51.2787, 'lon': 1.0789, 'name': 'South Eastern'},
        'Southern': {'lat': 50.9097, 'lon': -1.4044, 'name': 'Southern'},
        'South Wales': {'lat': 51.4816, 'lon': -3.1791, 'name': 'South Wales'},
        'South Western': {'lat': 50.7184, 'lon': -3.5339, 'name': 'South Western'},
        'Yorkshire': {'lat': 53.7960, 'lon': -1.5461, 'name': 'Yorkshire'},
        'South Scotland': {'lat': 55.9533, 'lon': -3.1883, 'name': 'South Scotland'},
    }

    return gsp_coords

def create_html_map(df):
    """Generate Leaflet map HTML with constraint heat markers"""

    print("\n🗺️  Creating geographic heat map...")

    gsp_coords = get_gsp_coordinates()

    # Merge data with coordinates
    map_data = []
    for _, row in df.iterrows():
        gsp = row['gsp_group']
        if gsp in gsp_coords:
            coords = gsp_coords[gsp]
            map_data.append({
                'lat': coords['lat'],
                'lon': coords['lon'],
                'name': coords['name'],
                'volume_mw': row['total_volume_mw'],
                'bmu_count': row['bmu_count'],
                'acceptance_count': row['acceptance_count'],
                'avg_volume': row['avg_volume_mw']
            })

    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GB Constraint Cost Heat Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ height: 100vh; width: 100%; }}
            .info-box {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                z-index: 1000;
                max-width: 300px;
            }}
            .legend {{
                position: absolute;
                bottom: 30px;
                right: 10px;
                background: white;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
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
                border-radius: 50%;
            }}
        </style>
    </head>
    <body>
        <div class="info-box">
            <h3 style="margin-top: 0;">🗺️ GB Constraint Heat Map</h3>
            <p><strong>Period:</strong> Last 7 days</p>
            <p><strong>Data Source:</strong> BOALF acceptances</p>
            <p>Circle size = total volume (MW)<br>
            Color intensity = constraint severity</p>
        </div>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #800026; opacity: 0.7;"></div>
                <span>High (&gt;5,000 MW)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #E31A1C; opacity: 0.7;"></div>
                <span>Medium (2,000-5,000 MW)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FD8D3C; opacity: 0.7;"></div>
                <span>Low (&lt;2,000 MW)</span>
            </div>
        </div>

        <div id="map"></div>

        <script>
            // Initialize map (centered on UK)
            var map = L.map('map').setView([54.5, -2.5], 6);

            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }}).addTo(map);

            // Constraint data
            var constraintData = {json.dumps(map_data)};

            // Get color based on volume
            function getColor(volume) {{
                return volume > 5000 ? '#800026' :
                       volume > 2000 ? '#E31A1C' :
                       volume > 1000 ? '#FD8D3C' :
                       volume > 500  ? '#FEB24C' :
                                       '#FFEDA0';
            }}

            // Get radius based on volume (scaled)
            function getRadius(volume) {{
                return Math.sqrt(volume) * 2;
            }}

            // Add circles for each region
            constraintData.forEach(function(point) {{
                var circle = L.circle([point.lat, point.lon], {{
                    color: getColor(point.volume_mw),
                    fillColor: getColor(point.volume_mw),
                    fillOpacity: 0.6,
                    radius: getRadius(point.volume_mw) * 1000,
                    weight: 2
                }}).addTo(map);

                // Popup
                circle.bindPopup(
                    '<strong>' + point.name + '</strong><br>' +
                    'Total Volume: ' + point.volume_mw.toFixed(0) + ' MW<br>' +
                    'Acceptances: ' + point.acceptance_count + '<br>' +
                    'BMUs Involved: ' + point.bmu_count + '<br>' +
                    'Avg Volume: ' + point.avg_volume.toFixed(1) + ' MW'
                );
            }});
        </script>
    </body>
    </html>
    """

    # Save HTML file
    filename = "constraint_heatmap.html"
    with open(filename, 'w') as f:
        f.write(html)

    print(f"✅ Created interactive map: {filename}")
    print(f"   Open in browser: file://{filename}")

    return filename

def add_map_to_dashboard(df):
    """Add constraint summary to Google Sheets"""

    print("\n📊 Adding constraint summary to dashboard...")

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'inner-cinema-credentials.json', scope)

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet('Live Dashboard v2')

    # Add section header
    header_row = [["", "🗺️ CONSTRAINT COSTS BY REGION (7 Days)"]]
    sheet.update('K47:L47', header_row, value_input_option='USER_ENTERED')

    # Format header
    sheet.format('K47:L47', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
    })

    # Add data rows
    data_rows = [["Region", "Volume (MW)"]]
    for _, row in df.head(10).iterrows():
        data_rows.append([row['gsp_group'], f"{row['total_volume_mw']:.0f}"])

    sheet.update('K48:L58', data_rows, value_input_option='USER_ENTERED')

    # Format data
    sheet.format('K48:L48', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'bold': True}
    })

    print(f"✅ Added {len(data_rows)-1} regions to dashboard")

def main():
    print("="*80)
    print("CONSTRAINT GEO-VISUALIZATION")
    print("="*80)

    # Get data
    df = get_constraint_costs_by_gsp()

    if len(df) == 0:
        print("\n⚠️  No constraint data available for mapping")
        return

    # Show summary
    print("\n📈 Constraint Cost Summary:")
    print("="*80)
    print(f"{'Region':<30} {'Volume (MW)':>15} {'Acceptances':>15}")
    print("-"*80)
    for _, row in df.head(10).iterrows():
        print(f"{row['gsp_group']:<30} {row['total_volume_mw']:>15,.0f} {row['acceptance_count']:>15}")

    # Create map
    map_file = create_html_map(df)

    # Add to dashboard
    add_map_to_dashboard(df)

    print("\n" + "="*80)
    print("✅ GEO-VISUALIZATION COMPLETE")
    print("="*80)
    print(f"Interactive map: {map_file}")
    print(f"Dashboard: https://docs.google.com/spreadsheets/d/{SHEET_ID}")

if __name__ == "__main__":
    main()
