#!/usr/bin/env python3
"""
Simplified GSP Live Flow Map
Shows which GSP areas are net exporting vs importing
"""

from google.cloud import bigquery
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def get_gsp_flows():
    """Get GSP generation and demand for latest available period"""
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Simplified query - get latest data and join with generator locations
    query = f"""
    WITH latest_period AS (
        SELECT DATE '2025-10-30' as date, 48 as period  -- Use last known good data
    ),
    gen AS (
        SELECT boundary as gsp, SUM(generation) as gen_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen`
        WHERE DATE(settlementDate) = (SELECT date FROM latest_period)
          AND settlementPeriod = (SELECT period FROM latest_period)
        GROUP BY gsp
    ),
    dem AS (
        SELECT boundary as gsp, SUM(demand) as dem_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem`
        WHERE DATE(settlementDate) = (SELECT date FROM latest_period)
          AND settlementPeriod = (SELECT period FROM latest_period)
        GROUP BY gsp
    ),
    gsp_loc AS (
        SELECT gsp, AVG(lat) as lat, AVG(lng) as lng,
               COUNT(*) as gen_count, SUM(capacity_mw) as capacity
        FROM `{PROJECT_ID}.{DATASET}.sva_generators`
        WHERE gsp IS NOT NULL AND lat IS NOT NULL
        GROUP BY gsp
    )
    SELECT 
        l.gsp,
        l.lat,
        l.lng,
        l.gen_count,
        ROUND(l.capacity, 2) as capacity,
        ROUND(COALESCE(g.gen_mw, 0), 2) as gen_mw,
        ROUND(COALESCE(d.dem_mw, 0), 2) as dem_mw,
        ROUND(COALESCE(g.gen_mw, 0) - COALESCE(d.dem_mw, 0), 2) as net_mw,
        CASE WHEN COALESCE(g.gen_mw, 0) > COALESCE(d.dem_mw, 0) 
             THEN 'EXPORTING' ELSE 'IMPORTING' END as status
    FROM gsp_loc l
    LEFT JOIN gen g ON l.gsp = g.gsp
    LEFT JOIN dem d ON l.gsp = d.gsp
    ORDER BY ABS(COALESCE(g.gen_mw, 0) - COALESCE(d.dem_mw, 0)) DESC
    """
    
    print("🔍 Querying GSP flows...")
    results = list(client.query(query).result())
    
    if not results:
        return []
    
    data = []
    for row in results:
        data.append({
            'gsp': row.gsp,
            'lat': row.lat,
            'lng': row.lng,
            'gen_count': row.gen_count,
            'capacity': row.capacity,
            'gen_mw': row.gen_mw,
            'dem_mw': row.dem_mw,
            'net_mw': row.net_mw,
            'status': row.status
        })
    
    return data

def create_map(data):
    """Create HTML map"""
    
    exp = [d for d in data if d['status'] == 'EXPORTING']
    imp = [d for d in data if d['status'] == 'IMPORTING']
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>GSP Flow Map - Live Generation vs Import/Export</title>
    <style>
        body {{ margin: 0; font-family: Arial; background: #1a1a1a; color: #fff; }}
        #map {{ height: 100vh; width: 100%; }}
        .info {{
            position: absolute; top: 20px; left: 20px;
            background: rgba(0,0,0,0.9); padding: 20px;
            border-radius: 10px; max-width: 350px;
            border: 2px solid #4CAF50;
        }}
        .stat {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .export {{ background: rgba(0,188,212,0.3); border-left: 4px solid #00bcd4; }}
        .import {{ background: rgba(255,152,0,0.3); border-left: 4px solid #ff9800; }}
        .legend {{
            position: absolute; bottom: 30px; right: 20px;
            background: rgba(0,0,0,0.9); padding: 15px;
            border-radius: 10px; border: 2px solid #4CAF50;
        }}
        .legend-item {{ display: flex; align-items: center; margin: 8px 0; }}
        .circle {{ width: 20px; height: 20px; border-radius: 50%; margin-right: 10px; border: 2px solid #fff; }}
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDjw_YjobTs0DCbZwl6p1vXbPSxG6YQNCE"></script>
</head>
<body>
    <div id="map"></div>
    <div class="info">
        <h2 style="margin:0 0 15px 0; color:#4CAF50;">⚡ GSP Flow Status</h2>
        <div>Total GSP Areas: <strong>{len(data)}</strong></div>
        <div class="stat export">
            <strong>🟦 Exporting:</strong> {len(exp)} areas<br>
            <small>Generation > Demand</small>
        </div>
        <div class="stat import">
            <strong>🟧 Importing:</strong> {len(imp)} areas<br>
            <small>Demand > Generation</small>
        </div>
    </div>
    <div class="legend">
        <div style="font-weight: bold; margin-bottom: 10px;">Legend</div>
        <div class="legend-item">
            <div class="circle" style="background: rgba(0,188,212,0.7);"></div>
            <span>Exporting</span>
        </div>
        <div class="legend-item">
            <div class="circle" style="background: rgba(255,152,0,0.7);"></div>
            <span>Importing</span>
        </div>
    </div>
    <script>
        const data = {json.dumps(data)};
        let map;
        
        function initMap() {{
            map = new google.maps.Map(document.getElementById('map'), {{
                center: {{lat: 54.5, lng: -3.5}},
                zoom: 6,
                mapTypeId: 'roadmap',
                styles: [
                    {{"elementType": "geometry", "stylers": [{{"color": "#212121"}}]}},
                    {{"elementType": "labels.text.fill", "stylers": [{{"color": "#757575"}}]}},
                    {{"featureType": "water", "elementType": "geometry", "stylers": [{{"color": "#000000"}}]}}
                ]
            }});
            
            data.forEach(gsp => {{
                const isExp = gsp.status === 'EXPORTING';
                const size = Math.min(Math.max(Math.abs(gsp.net_mw) / 200, 3), 15);
                
                const marker = new google.maps.Marker({{
                    position: {{lat: gsp.lat, lng: gsp.lng}},
                    map: map,
                    title: gsp.gsp,
                    icon: {{
                        path: google.maps.SymbolPath.CIRCLE,
                        fillColor: isExp ? '#00bcd4' : '#ff9800',
                        fillOpacity: 0.7,
                        strokeColor: '#fff',
                        strokeWeight: 2,
                        scale: size
                    }}
                }});
                
                const info = new google.maps.InfoWindow({{
                    content: `
                        <div style="color:#000; padding:10px; max-width:300px;">
                            <h3 style="margin:0 0 10px 0; color:${{isExp ? '#00bcd4' : '#ff9800'}};">
                                GSP: ${{gsp.gsp}}
                            </h3>
                            <div style="background:#f5f5f5; padding:10px; border-radius:5px; margin:10px 0;">
                                <strong>Status:</strong> <span style="font-weight:bold; color:${{isExp ? '#00bcd4' : '#ff9800'}};">
                                    ${{isExp ? '🟦 EXPORTING' : '🟧 IMPORTING'}}
                                </span>
                            </div>
                            <table style="width:100%; border-collapse:collapse;">
                                <tr style="border-bottom:1px solid #ddd;">
                                    <td style="padding:5px;"><strong>Generation:</strong></td>
                                    <td style="text-align:right; padding:5px;">${{gsp.gen_mw.toLocaleString()}} MW</td>
                                </tr>
                                <tr style="border-bottom:1px solid #ddd;">
                                    <td style="padding:5px;"><strong>Demand:</strong></td>
                                    <td style="text-align:right; padding:5px;">${{gsp.dem_mw.toLocaleString()}} MW</td>
                                </tr>
                                <tr style="background:${{isExp ? '#e0f7fa' : '#fff3e0'}};">
                                    <td style="padding:5px;"><strong>Net Flow:</strong></td>
                                    <td style="text-align:right; padding:5px; font-weight:bold;">
                                        ${{isExp ? '+' : ''}}${{gsp.net_mw.toLocaleString()}} MW
                                    </td>
                                </tr>
                            </table>
                            <div style="margin-top:10px; padding-top:10px; border-top:1px solid #ddd; font-size:12px; color:#666;">
                                <strong>Capacity:</strong> ${{gsp.capacity.toLocaleString()}} MW<br>
                                <strong>Generators:</strong> ${{gsp.gen_count}}
                            </div>
                        </div>
                    `
                }});
                
                marker.addListener('click', () => info.open(map, marker));
            }});
        }}
        
        google.maps.event.addDomListener(window, 'load', initMap);
    </script>
</body>
</html>
"""
    
    with open('gsp_live_flow_map.html', 'w') as f:
        f.write(html)
    
    print(f"✅ Map created: gsp_live_flow_map.html")

def main():
    print("=" * 70)
    print("⚡ GSP LIVE FLOW MAP - GENERATION VS IMPORT/EXPORT")
    print("=" * 70)
    
    data = get_gsp_flows()
    
    if not data:
        print("❌ No data available")
        return
    
    print(f"\n✅ Loaded {len(data)} GSP areas")
    
    exp = [d for d in data if d['status'] == 'EXPORTING']
    imp = [d for d in data if d['status'] == 'IMPORTING']
    
    print(f"\n📊 Summary:")
    print(f"   🟦 Exporting: {len(exp)} areas")
    print(f"   🟧 Importing: {len(imp)} areas")
    
    print(f"\n🔝 Top 5 Exporters:")
    for i, g in enumerate(sorted(exp, key=lambda x: x['net_mw'], reverse=True)[:5], 1):
        print(f"   {i}. {g['gsp']:8s} +{g['net_mw']:8,.0f} MW (Gen: {g['gen_mw']:7,.0f} | Dem: {g['dem_mw']:7,.0f})")
    
    print(f"\n🔝 Top 5 Importers:")
    for i, g in enumerate(sorted(imp, key=lambda x: x['net_mw'])[:5], 1):
        print(f"   {i}. {g['gsp']:8s} {g['net_mw']:8,.0f} MW (Gen: {g['gen_mw']:7,.0f} | Dem: {g['dem_mw']:7,.0f})")
    
    create_map(data)
    
    print(f"\n🌐 To view: open gsp_live_flow_map.html")
    print(f"💡 Blue circles = Exporting | Orange circles = Importing")

if __name__ == "__main__":
    main()
