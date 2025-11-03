"""
Automated GB Power Map Generator for Windows UpCloud Server
Queries BigQuery for latest data and generates the complete power system map
Designed to run on Windows Task Scheduler every 30 minutes
"""

import os
import sys
from datetime import datetime
from google.cloud import bigquery
import json

def log_message(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
    # Also write to log file
    log_dir = r"C:\maps\logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"map_generation_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def get_latest_gsp_flows():
    """Query BigQuery for latest GSP flows"""
    log_message("Querying latest GSP flows from BigQuery...")
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    query = """
    WITH latest_period AS (
        SELECT MAX(settlementDate) as max_date
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
    ),
    latest_sp AS (
        SELECT MAX(settlementPeriod) as max_sp
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
    ),
    generation AS (
        SELECT 
            nationalGridBmUnit as gsp,
            SUM(generation) as total_generation
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
        AND settlementPeriod = (SELECT max_sp FROM latest_sp)
        GROUP BY nationalGridBmUnit
    ),
    demand AS (
        SELECT 
            nationalGridBmUnit as gsp,
            SUM(ABS(demand)) as total_demand
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
        AND settlementPeriod = (SELECT max_sp FROM latest_sp)
        GROUP BY nationalGridBmUnit
    )
    SELECT 
        COALESCE(g.gsp, d.gsp) as gsp,
        COALESCE(g.total_generation, 0) as generation,
        COALESCE(d.total_demand, 0) as demand,
        COALESCE(g.total_generation, 0) - COALESCE(d.total_demand, 0) as net_flow,
        (SELECT max_date FROM latest_period) as settlement_date,
        (SELECT max_sp FROM latest_sp) as settlement_period
    FROM generation g
    FULL OUTER JOIN demand d ON g.gsp = d.gsp
    ORDER BY ABS(COALESCE(g.total_generation, 0) - COALESCE(d.total_demand, 0)) DESC
    """
    
    results = client.query(query).result()
    gsp_data = list(results)
    log_message(f"Retrieved {len(gsp_data)} GSP records")
    return gsp_data

def get_offshore_wind_farms():
    """Query offshore wind farms from BigQuery"""
    log_message("Querying offshore wind farms...")
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    query = """
    SELECT 
        name,
        capacity_mw,
        latitude as lat,
        longitude as lon,
        gsp_zone,
        gsp_region
    FROM `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms`
    WHERE status = 'Operational'
    ORDER BY capacity_mw DESC
    """
    
    results = client.query(query).result()
    wind_farms = list(results)
    log_message(f"Retrieved {len(wind_farms)} offshore wind farms")
    return wind_farms

def get_all_generators():
    """Query all CVA and SVA generators from BigQuery"""
    log_message("Querying all generators (CVA + SVA)...")
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    # SVA generators
    sva_query = """
    SELECT 
        'SVA' as type,
        generator_name as name,
        fuel_type,
        installed_capacity_mw as capacity,
        lat,
        lon,
        dno,
        gsp_zone
    FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords`
    WHERE lat IS NOT NULL AND lon IS NOT NULL
    """
    
    # CVA generators
    cva_query = """
    SELECT 
        'CVA' as type,
        name,
        primary_fuel as fuel_type,
        installed_capacity_mw as capacity,
        lat,
        lon,
        dno,
        gsp_zone
    FROM `inner-cinema-476211-u9.uk_energy_prod.cva_plants`
    WHERE lat IS NOT NULL AND lon IS NOT NULL
    """
    
    sva_results = client.query(sva_query).result()
    cva_results = client.query(cva_query).result()
    
    all_generators = list(sva_results) + list(cva_results)
    log_message(f"Retrieved {len(all_generators)} total generators")
    return all_generators

def load_dno_geojson():
    """Load DNO boundaries GeoJSON"""
    log_message("Loading DNO boundaries...")
    
    geojson_path = r"C:\maps\data\dno_regions.geojson"
    if not os.path.exists(geojson_path):
        log_message(f"WARNING: DNO GeoJSON not found at {geojson_path}")
        return None
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        dno_data = json.load(f)
    
    log_message(f"Loaded {len(dno_data['features'])} DNO regions")
    return dno_data

def get_fuel_color(fuel_type):
    """Return color for fuel type"""
    fuel_colors = {
        'Wind': '#00ff00',
        'Solar': '#ffff00',
        'Gas': '#ff8c00',
        'Coal': '#8b4513',
        'Nuclear': '#ff00ff',
        'Hydro': '#00bfff',
        'Biomass': '#32cd32',
        'Oil': '#696969',
        'Other': '#a9a9a9',
        'Storage': '#9370db'
    }
    
    fuel_upper = str(fuel_type).upper()
    for key in fuel_colors:
        if key.upper() in fuel_upper:
            return fuel_colors[key]
    
    return fuel_colors['Other']

def generate_html_map(gsp_data, offshore_farms, generators, dno_geojson):
    """Generate the complete HTML map"""
    log_message("Generating HTML map...")
    
    # Get settlement info from first GSP record
    settlement_date = gsp_data[0].settlement_date if gsp_data else 'Unknown'
    settlement_period = gsp_data[0].settlement_period if gsp_data else 'Unknown'
    
    # GSP coordinates (approximate center of each GSP)
    gsp_coords = {
        'PEMB_M': (51.68, -4.92),
        'INDQ_M': (53.44, -2.94),
        'PYAS_M': (52.76, -1.78),
        'SOUT_M': (50.91, -1.40),
        'STEW_M': (55.93, -4.40),
        'LAGA_M': (51.64, 0.15),
        'STAY_M': (51.11, 1.32),
        'HUTB_M': (53.45, -0.40),
        'FOYE_M': (52.60, 1.50),
        'BRIG_M': (52.43, -1.90),
        'HARW_M': (51.59, -0.32),
        'TORN_M': (57.47, -4.23),
        'COTL_M': (52.02, 0.80),
        'EGGB_M': (53.86, -1.77),
        'IRON_M': (52.92, -1.27),
        'SANT_M': (53.55, -0.95),
        'ABHA_M': (57.45, -2.07),
        'NORT_M': (55.11, -1.61)
    }
    
    # Count exporters/importers
    exporters = [g for g in gsp_data if g.net_flow > 0]
    importers = [g for g in gsp_data if g.net_flow < 0]
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>GB Power System Map - Live</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        #map {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 100%;
        }}
        .info-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            z-index: 1000;
            max-width: 300px;
        }}
        .info-panel h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .info-panel p {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .legend {{
            position: absolute;
            bottom: 30px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        .legend-item {{
            margin: 5px 0;
            font-size: 12px;
        }}
        .legend-circle {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info-panel">
        <h3>GB Power System</h3>
        <p><strong>Data:</strong> {settlement_date} SP{settlement_period}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p><strong>GSPs:</strong> {len(gsp_data)} total</p>
        <p>Exporters: {len(exporters)} | Importers: {len(importers)}</p>
        <p><strong>Offshore Wind:</strong> {len(offshore_farms)} farms</p>
        <p><strong>Generators:</strong> {len(generators)} total</p>
    </div>
    
    <div class="legend">
        <strong>Legend</strong>
        <div class="legend-item">
            <span class="legend-circle" style="background: #4169E1;"></span> GSP Exporter
        </div>
        <div class="legend-item">
            <span class="legend-circle" style="background: #FF8C00;"></span> GSP Importer
        </div>
        <div class="legend-item">
            <span class="legend-circle" style="background: #00FFFF;"></span> Offshore Wind
        </div>
        <div class="legend-item">
            <span class="legend-circle" style="background: #00FF00;"></span> Wind
        </div>
        <div class="legend-item">
            <span class="legend-circle" style="background: #FFFF00;"></span> Solar
        </div>
        <div class="legend-item">
            <span class="legend-circle" style="background: #FF8C00;"></span> Gas
        </div>
        <div class="legend-item">
            <span class="legend-circle" style="background: #FF00FF;"></span> Nuclear
        </div>
    </div>

    <script>
        // Initialize map
        var map = L.map('map').setView([54.5, -3.0], 6);
        
        // Add dark theme tile layer
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap contributors &copy; CartoDB',
            subdomains: 'abcd',
            maxZoom: 20
        }}).addTo(map);
        
        // Layer groups
        var dnoLayer = L.layerGroup().addTo(map);
        var gspLayer = L.layerGroup().addTo(map);
        var offshoreLayer = L.layerGroup().addTo(map);
        var generatorsClusters = L.markerClusterGroup({{
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false
        }}).addTo(map);
"""

    # Add DNO boundaries
    if dno_geojson:
        html += """
        // Add DNO boundaries
        var dnoData = """ + json.dumps(dno_geojson) + """;
        L.geoJSON(dnoData, {
            style: {
                color: '#00ff00',
                weight: 2,
                fillOpacity: 0.1,
                fillColor: '#00ff00'
            },
            onEachFeature: function(feature, layer) {
                if (feature.properties && feature.properties.DNO_NAME) {
                    layer.bindPopup('<strong>' + feature.properties.DNO_NAME + '</strong>');
                }
            }
        }).addTo(dnoLayer);
"""

    # Add GSP points
    for gsp in gsp_data:
        if gsp.gsp in gsp_coords:
            lat, lon = gsp_coords[gsp.gsp]
            color = '#4169E1' if gsp.net_flow > 0 else '#FF8C00'
            radius = min(max(abs(gsp.net_flow) / 50, 5), 30)
            
            html += f"""
        L.circleMarker([{lat}, {lon}], {{
            color: '{color}',
            fillColor: '{color}',
            fillOpacity: 0.7,
            radius: {radius},
            weight: 2
        }}).bindPopup(`
            <strong>{gsp.gsp}</strong><br>
            Generation: {gsp.generation:.1f} MW<br>
            Demand: {gsp.demand:.1f} MW<br>
            Net Flow: {gsp.net_flow:.1f} MW<br>
            Status: {'Exporter' if gsp.net_flow > 0 else 'Importer'}
        `).addTo(gspLayer);
"""

    # Add offshore wind farms
    for farm in offshore_farms:
        if farm.lat and farm.lon:
            html += f"""
        L.circleMarker([{farm.lat}, {farm.lon}], {{
            color: '#00FFFF',
            fillColor: '#00FFFF',
            fillOpacity: 0.6,
            radius: {min(farm.capacity_mw / 100, 20)},
            weight: 2
        }}).bindPopup(`
            <strong>{farm.name}</strong><br>
            Capacity: {farm.capacity_mw:.1f} MW<br>
            GSP: {farm.gsp_zone or 'N/A'}
        `).addTo(offshoreLayer);
"""

    # Add generators (with clustering)
    for gen in generators:
        if gen.lat and gen.lon:
            color = get_fuel_color(gen.fuel_type)
            html += f"""
        L.circleMarker([{gen.lat}, {gen.lon}], {{
            color: '{color}',
            fillColor: '{color}',
            fillOpacity: 0.6,
            radius: 4,
            weight: 1
        }}).bindPopup(`
            <strong>{gen.name or 'Unknown'}</strong><br>
            Type: {gen.type}<br>
            Fuel: {gen.fuel_type or 'Unknown'}<br>
            Capacity: {gen.capacity or 0:.2f} MW<br>
            DNO: {gen.dno or 'N/A'}<br>
            GSP: {gen.gsp_zone or 'N/A'}
        `).addTo(generatorsClusters);
"""

    # Add layer control
    html += """
        // Layer control
        var overlays = {
            "DNO Boundaries": dnoLayer,
            "GSP Flow Points": gspLayer,
            "Offshore Wind": offshoreLayer,
            "Generators": generatorsClusters
        };
        L.control.layers(null, overlays, {collapsed: false}).addTo(map);
    </script>
</body>
</html>
"""
    
    return html

def main():
    """Main execution function"""
    try:
        log_message("=== Starting GB Power Map Generation ===")
        
        # Query all data
        gsp_data = get_latest_gsp_flows()
        offshore_farms = get_offshore_wind_farms()
        generators = get_all_generators()
        dno_geojson = load_dno_geojson()
        
        # Generate HTML
        html_content = generate_html_map(gsp_data, offshore_farms, generators, dno_geojson)
        
        # Save to web server directory
        output_path = r"C:\inetpub\wwwroot\gb_power_complete_map.html"
        output_dir = os.path.dirname(output_path)
        
        if not os.path.exists(output_dir):
            log_message(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        file_size = os.path.getsize(output_path)
        log_message(f"Map generated successfully: {output_path} ({file_size:,} bytes)")
        log_message("=== Map Generation Complete ===")
        
        return 0
        
    except Exception as e:
        log_message(f"ERROR: {str(e)}")
        import traceback
        log_message(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
