#!/usr/bin/env python3
"""
Create ACCURATE GSP Flow Map with REAL data from BMRS
Uses latest available data and correct GSP-level aggregation
"""

from google.cloud import bigquery
import json

# Approximate GSP center coordinates (these are the grid supply point locations)
GSP_COORDS = {
    'B1': {'name': 'Barking (London East)', 'lat': 51.5362, 'lng': 0.0810},
    'B2': {'name': 'Ealing (London West)', 'lat': 51.5154, 'lng': -0.2994},
    'B3': {'name': 'Wimbledon (London South)', 'lat': 51.4214, 'lng': -0.2072},
    'B4': {'name': 'Brixton (London Central)', 'lat': 51.4615, 'lng': -0.1125},
    'B5': {'name': 'City Road (London North)', 'lat': 51.5319, 'lng': -0.0966},
    'B6': {'name': 'Willesden (London NW)', 'lat': 51.5489, 'lng': -0.2356},
    'B7': {'name': 'Hurst (South East)', 'lat': 51.4459, 'lng': -0.4815},
    'B8': {'name': 'Sundon (East Midlands)', 'lat': 51.9476, 'lng': -0.4682},
    'B9': {'name': 'Pelham (East Anglia)', 'lat': 51.7422, 'lng': -0.0475},
    'B10': {'name': 'Bramley (South Central)', 'lat': 51.3244, 'lng': -0.9947},
    'B11': {'name': 'Melksham (South West)', 'lat': 51.3687, 'lng': -2.1413},
    'B12': {'name': 'Exeter (Devon)', 'lat': 50.7184, 'lng': -3.5339},
    'B13': {'name': 'Bristol (Severnside)', 'lat': 51.4545, 'lng': -2.5879},
    'B14': {'name': 'Indian Queens (Cornwall)', 'lat': 50.4019, 'lng': -4.9378},
    'B15': {'name': 'Landulph (Plymouth)', 'lat': 50.4464, 'lng': -4.2124},
    'B16': {'name': 'Pembroke (West Wales)', 'lat': 51.6750, 'lng': -4.9392},
    'B17': {'name': 'Swansea North (South Wales)', 'lat': 51.6563, 'lng': -3.9436},
    'N': {'name': 'National Grid', 'lat': 54.5, 'lng': -3.5}
}

def main():
    print("=" * 70)
    print("⚡ GSP FLOW MAP - ACCURATE DATA FROM BMRS")
    print("=" * 70)
    
    client = bigquery.Client(project="inner-cinema-476211-u9")
    
    # Get latest date
    date_query = """
    SELECT MAX(DATE(settlementDate)) as latest_date,
           MAX(settlementPeriod) as max_period
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
    WHERE DATE(settlementDate) = (
        SELECT MAX(DATE(settlementDate))
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
    )
    """
    date_info = list(client.query(date_query).result())[0]
    latest_date = date_info.latest_date
    latest_period = date_info.max_period
    
    print(f"📅 Using data from: {latest_date}, Settlement Period {latest_period}")
    
    # Query GSP flow data
    query = f"""
    WITH gen_data AS (
        SELECT 
            boundary,
            SUM(generation) as total_generation
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
        WHERE DATE(settlementDate) = '{latest_date}'
          AND settlementPeriod = {latest_period}
        GROUP BY boundary
    ),
    dem_data AS (
        SELECT 
            boundary,
            SUM(demand) as total_demand
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem`
        WHERE DATE(settlementDate) = '{latest_date}'
          AND settlementPeriod = {latest_period}
        GROUP BY boundary
    )
    SELECT 
        g.boundary as gsp,
        g.total_generation as gen_mw,
        d.total_demand as dem_mw,
        (g.total_generation + d.total_demand) as net_flow_mw
    FROM gen_data g
    INNER JOIN dem_data d ON g.boundary = d.boundary
    ORDER BY net_flow_mw DESC
    """
    
    results = list(client.query(query).result())
    
    if not results:
        print("❌ No data found")
        return
    
    # Prepare data for map
    map_data = []
    exporters = 0
    importers = 0
    
    for r in results:
        gsp_info = GSP_COORDS.get(r.gsp, {'name': r.gsp, 'lat': 54.5, 'lng': -3.5})
        is_exporting = r.net_flow_mw > 0
        
        if is_exporting:
            exporters += 1
        else:
            importers += 1
            
        map_data.append({
            'gsp': r.gsp,
            'name': gsp_info['name'],
            'lat': gsp_info['lat'],
            'lng': gsp_info['lng'],
            'gen': round(r.gen_mw, 2),
            'dem': round(r.dem_mw, 2),
            'net': round(r.net_flow_mw, 2),
            'status': 'EXPORTING' if is_exporting else 'IMPORTING'
        })
    
    print(f"✅ Found {len(map_data)} GSP areas")
    print(f"📊 {exporters} exporters, {importers} importers\n")
    
    # Show top exporters/importers
    exp_data = [d for d in map_data if d['status'] == 'EXPORTING']
    imp_data = [d for d in map_data if d['status'] == 'IMPORTING']
    
    print("🔝 Top 5 Exporters:")
    for i, g in enumerate(sorted(exp_data, key=lambda x: x['net'], reverse=True)[:5], 1):
        print(f"   {i}. {g['gsp']:4s} {g['name']:30s} +{g['net']:8,.0f} MW")
    
    print("\n🔝 Top Importers:")
    for i, g in enumerate(sorted(imp_data, key=lambda x: x['net'])[:5], 1):
        print(f"   {i}. {g['gsp']:4s} {g['name']:30s} {g['net']:9,.0f} MW")
    
    # Generate HTML map
    html = generate_html(map_data, exporters, importers, latest_date, latest_period)
    
    output_file = "gsp_flow_accurate.html"
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Map created: {output_file}")
    print(f"🌐 To view: open {output_file}")

def generate_html(data, exp_count, imp_count, date, period):
    data_json = json.dumps(data)
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GSP Flow Map - Accurate BMRS Data</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }}
        #map {{ height: 100vh; width: 100%; }}
        .info {{
            position: absolute; top: 20px; left: 20px;
            background: rgba(0,0,0,0.95); padding: 20px;
            border-radius: 10px; border: 2px solid #4CAF50;
            max-width: 400px; z-index: 1000;
        }}
        h2 {{ margin: 0 0 15px 0; color: #4CAF50; }}
        .stat {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .exp {{ background: rgba(0,188,212,0.3); border-left: 4px solid #00bcd4; }}
        .imp {{ background: rgba(255,152,0,0.3); border-left: 4px solid #ff9800; }}
        .legend {{
            position: absolute; bottom: 30px; right: 20px;
            background: rgba(0,0,0,0.95); padding: 15px;
            border-radius: 10px; border: 2px solid #4CAF50; z-index: 1000;
        }}
        .legend-item {{ display: flex; align-items: center; margin: 8px 0; }}
        .circle {{ width: 20px; height: 20px; border-radius: 50%; margin-right: 10px; border: 2px solid #fff; }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info">
        <h2>⚡ GB Grid Supply Points</h2>
        <p style="font-size:12px;color:#aaa;margin:5px 0">{date}, SP{period}</p>
        <p style="font-size:13px">Total GSP Areas: <strong>18</strong></p>
        <div class="stat exp">
            <strong>🟦 Net Exporters: {exp_count} areas</strong><br>
            <small style="color:#aaa">Generation exceeds demand in area</small>
        </div>
        <div class="stat imp">
            <strong>🟧 Net Importers: {imp_count} areas</strong><br>
            <small style="color:#aaa">Demand exceeds local generation</small>
        </div>
        <p style="font-size:11px;color:#888;margin-top:10px">
            ℹ️ Data from BMRS (Balancing Mechanism Reporting Service)<br>
            Shows grid supply point level aggregation, not individual generators
        </p>
    </div>
    
    <div class="legend">
        <div style="font-weight:bold;margin-bottom:10px">Legend</div>
        <div class="legend-item">
            <div class="circle" style="background:rgba(0,188,212,0.7)"></div>
            <span>Net Exporter</span>
        </div>
        <div class="legend-item">
            <div class="circle" style="background:rgba(255,152,0,0.7)"></div>
            <span>Net Importer</span>
        </div>
        <div style="font-size:11px;color:#aaa;margin-top:10px">Circle size = flow magnitude</div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const gspData = {data_json};
        
        const map = L.map('map').setView([54, -2.5], 6);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CartoDB',
            maxZoom: 19
        }}).addTo(map);

        gspData.forEach(gsp => {{
            const isExporting = gsp.status === 'EXPORTING';
            const circleSize = Math.min(Math.max(Math.abs(gsp.net) / 30000, 5), 25);
            
            const circle = L.circleMarker([gsp.lat, gsp.lng], {{
                radius: circleSize,
                fillColor: isExporting ? '#00bcd4' : '#ff9800',
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }}).addTo(map);

            const popupContent = `
                <div style="color:#000;padding:12px;min-width:280px;font-family:Arial">
                    <h3 style="margin:0 0 10px 0;color:${{isExporting?'#00bcd4':'#ff9800'}};border-bottom:2px solid ${{isExporting?'#00bcd4':'#ff9800'}};padding-bottom:8px">
                        GSP ${{gsp.gsp}}: ${{gsp.name}}
                    </h3>
                    <div style="background:${{isExporting?'#e0f7fa':'#fff3e0'}};padding:12px;border-radius:5px;text-align:center;margin:10px 0">
                        <div style="font-size:18px;font-weight:bold;color:${{isExporting?'#00bcd4':'#ff9800'}}">
                            ${{isExporting?'🟦 NET EXPORTER':'🟧 NET IMPORTER'}}
                        </div>
                        <div style="font-size:16px;font-weight:bold;margin-top:8px">
                            ${{isExporting?'+':''}}${{gsp.net.toLocaleString()}} MW
                        </div>
                    </div>
                    <table style="width:100%;border-collapse:collapse">
                        <tr style="border-bottom:1px solid #ddd">
                            <td style="padding:8px">⚡ Total Generation</td>
                            <td style="text-align:right;padding:8px;font-weight:bold">${{gsp.gen.toLocaleString()}} MW</td>
                        </tr>
                        <tr style="border-bottom:1px solid #ddd">
                            <td style="padding:8px">💡 Total Demand</td>
                            <td style="text-align:right;padding:8px;font-weight:bold">${{Math.abs(gsp.dem).toLocaleString()}} MW</td>
                        </tr>
                        <tr>
                            <td style="padding:8px"><strong>📊 Net Flow</strong></td>
                            <td style="text-align:right;padding:8px;font-weight:bold;color:${{isExporting?'#00bcd4':'#ff9800'}}">
                                ${{isExporting?'+':''}}${{gsp.net.toLocaleString()}} MW
                            </td>
                        </tr>
                    </table>
                    <div style="margin-top:10px;padding-top:10px;border-top:1px solid #ddd;font-size:11px;color:#666">
                        ${{isExporting ? 'Area generates more than it consumes - exports surplus to grid' : 'Area consumes more than it generates - imports from grid'}}
                    </div>
                </div>
            `;

            circle.bindPopup(popupContent, {{ maxWidth: 350 }});
        }});

        console.log(`✅ Loaded ${{gspData.length}} GSP areas`);
    </script>
</body>
</html>'''

if __name__ == "__main__":
    main()
