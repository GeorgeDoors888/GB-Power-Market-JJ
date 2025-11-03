#!/usr/bin/env python3
"""
GSP Live Flow Visualization
Shows which GSP areas are net exporting (generation > demand) 
or net importing (demand > generation) in real-time

Uses:
- bmrs_indgen: Indicative generation by GSP
- bmrs_inddem: Indicative demand by GSP
- sva_generators: Generator locations to calculate GSP positions
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def get_latest_gsp_flows():
    """Get latest generation and demand by GSP area"""
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Query to get latest GSP generation and demand
    query = f"""
    WITH latest_time AS (
        SELECT MAX(DATE(settlementDate)) as max_date,
               MAX(settlementPeriod) as max_period
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen`
    ),
    gen_data AS (
        SELECT 
            boundary as gsp,
            SUM(generation) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen`, latest_time
        WHERE DATE(settlementDate) = latest_time.max_date
          AND settlementPeriod = latest_time.max_period
        GROUP BY gsp
    ),
    dem_data AS (
        SELECT 
            boundary as gsp,
            SUM(demand) as demand_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem`, latest_time
        WHERE DATE(settlementDate) = latest_time.max_date
          AND settlementPeriod = latest_time.max_period
        GROUP BY gsp
    ),
    gsp_locations AS (
        -- Calculate approximate GSP center from generators
        SELECT 
            gsp,
            AVG(lat) as lat,
            AVG(lng) as lng,
            COUNT(*) as generator_count,
            SUM(capacity_mw) as total_capacity
        FROM `{PROJECT_ID}.{DATASET}.sva_generators`
        WHERE gsp IS NOT NULL 
          AND gsp != ''
          AND lat IS NOT NULL
          AND lng IS NOT NULL
        GROUP BY gsp
    )
    SELECT 
        l.gsp,
        l.lat,
        l.lng,
        l.generator_count,
        l.total_capacity,
        COALESCE(g.generation_mw, 0) as generation_mw,
        COALESCE(d.demand_mw, 0) as demand_mw,
        COALESCE(g.generation_mw, 0) - COALESCE(d.demand_mw, 0) as net_flow_mw,
        CASE 
            WHEN COALESCE(g.generation_mw, 0) > COALESCE(d.demand_mw, 0) 
            THEN 'EXPORTING'
            ELSE 'IMPORTING'
        END as flow_status,
        (SELECT max_date FROM latest_time) as data_date,
        (SELECT max_period FROM latest_time) as data_period
    FROM gsp_locations l
    LEFT JOIN gen_data g ON l.gsp = g.gsp
    LEFT JOIN dem_data d ON l.gsp = d.gsp
    WHERE l.lat IS NOT NULL
    ORDER BY ABS(COALESCE(g.generation_mw, 0) - COALESCE(d.demand_mw, 0)) DESC
    """
    
    print("🔍 Querying latest GSP flows...")
    results = client.query(query).result()
    
    gsp_data = []
    for row in results:
        gsp_data.append({
            'gsp': row.gsp,
            'lat': row.lat,
            'lng': row.lng,
            'generator_count': row.generator_count,
            'total_capacity': round(row.total_capacity, 2) if row.total_capacity else 0,
            'generation_mw': round(row.generation_mw, 2),
            'demand_mw': round(row.demand_mw, 2),
            'net_flow_mw': round(row.net_flow_mw, 2),
            'flow_status': row.flow_status,
            'data_date': str(row.data_date),
            'data_period': row.data_period
        })
    
    return gsp_data

def create_html_map(gsp_data):
    """Create interactive HTML map showing GSP flows"""
    
    if not gsp_data:
        print("❌ No GSP data available")
        return
    
    # Get data timestamp
    data_date = gsp_data[0]['data_date']
    data_period = gsp_data[0]['data_period']
    
    # Calculate statistics
    exporting = [g for g in gsp_data if g['flow_status'] == 'EXPORTING']
    importing = [g for g in gsp_data if g['flow_status'] == 'IMPORTING']
    
    total_export = sum(g['net_flow_mw'] for g in exporting)
    total_import = sum(abs(g['net_flow_mw']) for g in importing)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>GSP Live Flow Map - Generation vs Import/Export</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: #1a1a1a;
            color: #fff;
        }}
        #map {{
            height: 100vh;
            width: 100%;
        }}
        .info-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.85);
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #4CAF50;
            max-width: 350px;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        .info-panel h2 {{
            margin: 0 0 15px 0;
            color: #4CAF50;
            font-size: 20px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .info-panel p {{
            margin: 8px 0;
            font-size: 14px;
        }}
        .stat-box {{
            background: rgba(76, 175, 80, 0.2);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #4CAF50;
        }}
        .stat-export {{
            border-left-color: #00bcd4;
            background: rgba(0, 188, 212, 0.2);
        }}
        .stat-import {{
            border-left-color: #ff9800;
            background: rgba(255, 152, 0, 0.2);
        }}
        .legend {{
            position: absolute;
            bottom: 30px;
            right: 20px;
            background: rgba(0, 0, 0, 0.85);
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #4CAF50;
            z-index: 1000;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 14px;
        }}
        .legend-circle {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid #fff;
        }}
        .export-circle {{
            background: rgba(0, 188, 212, 0.7);
        }}
        .import-circle {{
            background: rgba(255, 152, 0, 0.7);
        }}
        .refresh-btn {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
            width: 100%;
        }}
        .refresh-btn:hover {{
            background: #45a049;
        }}
        .timestamp {{
            color: #aaa;
            font-size: 12px;
            font-style: italic;
        }}
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDjw_YjobTs0DCbZwl6p1vXbPSxG6YQNCE"></script>
</head>
<body>
    <div id="map"></div>
    
    <div class="info-panel">
        <h2>⚡ GSP Flow Status</h2>
        <p class="timestamp">Data: {data_date} SP{data_period}</p>
        
        <div class="stat-box">
            <strong>Total GSP Areas:</strong> {len(gsp_data)}<br>
            <strong>Total Capacity:</strong> {sum(g['total_capacity'] for g in gsp_data):,.0f} MW
        </div>
        
        <div class="stat-box stat-export">
            <strong>🟦 Exporting Areas:</strong> {len(exporting)}<br>
            <strong>Net Export:</strong> {total_export:,.0f} MW
        </div>
        
        <div class="stat-box stat-import">
            <strong>🟧 Importing Areas:</strong> {len(importing)}<br>
            <strong>Net Import:</strong> {total_import:,.0f} MW
        </div>
        
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>
    </div>
    
    <div class="legend">
        <div style="color: #4CAF50; font-weight: bold; margin-bottom: 10px;">Legend</div>
        <div class="legend-item">
            <div class="legend-circle export-circle"></div>
            <span>Exporting (Gen > Demand)</span>
        </div>
        <div class="legend-item">
            <div class="legend-circle import-circle"></div>
            <span>Importing (Demand > Gen)</span>
        </div>
    </div>
    
    <script>
        let map;
        let markers = [];
        
        const gspData = {json.dumps(gsp_data)};
        
        function initMap() {{
            // Center on UK
            map = new google.maps.Map(document.getElementById('map'), {{
                center: {{lat: 54.5, lng: -3.5}},
                zoom: 6,
                mapTypeId: 'roadmap',
                styles: [
                    {{
                        "elementType": "geometry",
                        "stylers": [
                            {{"color": "#212121"}}
                        ]
                    }},
                    {{
                        "elementType": "labels.text.fill",
                        "stylers": [
                            {{"color": "#757575"}}
                        ]
                    }},
                    {{
                        "elementType": "labels.text.stroke",
                        "stylers": [
                            {{"color": "#212121"}}
                        ]
                    }},
                    {{
                        "featureType": "water",
                        "elementType": "geometry",
                        "stylers": [
                            {{"color": "#000000"}}
                        ]
                    }}
                ]
            }});
            
            // Add GSP markers
            gspData.forEach(gsp => {{
                const isExporting = gsp.flow_status === 'EXPORTING';
                const netFlow = Math.abs(gsp.net_flow_mw);
                
                // Size based on net flow magnitude
                const scale = Math.min(Math.max(netFlow / 200, 3), 15);
                
                const marker = new google.maps.Marker({{
                    position: {{lat: gsp.lat, lng: gsp.lng}},
                    map: map,
                    title: gsp.gsp,
                    icon: {{
                        path: google.maps.SymbolPath.CIRCLE,
                        fillColor: isExporting ? '#00bcd4' : '#ff9800',
                        fillOpacity: 0.7,
                        strokeColor: '#ffffff',
                        strokeWeight: 2,
                        scale: scale
                    }}
                }});
                
                // Info window
                const infoContent = `
                    <div style="color: #000; font-family: Arial; padding: 10px; max-width: 300px;">
                        <h3 style="margin: 0 0 10px 0; color: ${{isExporting ? '#00bcd4' : '#ff9800'}};">
                            GSP: ${{gsp.gsp}}
                        </h3>
                        <div style="background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
                            <strong>Status:</strong> <span style="color: ${{isExporting ? '#00bcd4' : '#ff9800'}}; font-weight: bold;">
                                ${{isExporting ? '🟦 EXPORTING' : '🟧 IMPORTING'}}
                            </span>
                        </div>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 5px;"><strong>Generation:</strong></td>
                                <td style="text-align: right; padding: 5px;">${{gsp.generation_mw.toLocaleString()}} MW</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 5px;"><strong>Demand:</strong></td>
                                <td style="text-align: right; padding: 5px;">${{gsp.demand_mw.toLocaleString()}} MW</td>
                            </tr>
                            <tr style="background: ${{isExporting ? '#e0f7fa' : '#fff3e0'}};">
                                <td style="padding: 5px;"><strong>Net Flow:</strong></td>
                                <td style="text-align: right; padding: 5px; font-weight: bold;">
                                    ${{isExporting ? '+' : ''}}${{gsp.net_flow_mw.toLocaleString()}} MW
                                </td>
                            </tr>
                        </table>
                        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                            <strong>Installed Capacity:</strong> ${{gsp.total_capacity.toLocaleString()}} MW<br>
                            <strong>Generators:</strong> ${{gsp.generator_count}}
                        </div>
                    </div>
                `;
                
                const infoWindow = new google.maps.InfoWindow({{
                    content: infoContent
                }});
                
                marker.addListener('click', () => {{
                    // Close all other info windows
                    markers.forEach(m => {{
                        if (m.infoWindow) m.infoWindow.close();
                    }});
                    infoWindow.open(map, marker);
                }});
                
                markers.push({{marker: marker, infoWindow: infoWindow}});
            }});
            
            console.log(`✅ Loaded ${{gspData.length}} GSP areas`);
        }}
        
        // Initialize map
        google.maps.event.addDomListener(window, 'load', initMap);
    </script>
</body>
</html>
"""
    
    return html_content

def main():
    """Main execution"""
    print("=" * 70)
    print("⚡ GSP LIVE FLOW MAP - GENERATION VS IMPORT/EXPORT")
    print("=" * 70)
    
    # Get latest GSP flows
    gsp_data = get_latest_gsp_flows()
    
    if not gsp_data:
        print("\n❌ No GSP data available. Ensure bmrs_indgen and bmrs_inddem tables have recent data.")
        return
    
    print(f"\n✅ Loaded {len(gsp_data)} GSP areas")
    
    # Statistics
    exporting = [g for g in gsp_data if g['flow_status'] == 'EXPORTING']
    importing = [g for g in gsp_data if g['flow_status'] == 'IMPORTING']
    
    print(f"\n📊 Summary:")
    print(f"   🟦 Exporting: {len(exporting)} GSP areas")
    print(f"   🟧 Importing: {len(importing)} GSP areas")
    print(f"   📅 Data: {gsp_data[0]['data_date']} SP{gsp_data[0]['data_period']}")
    
    # Top exporters
    print(f"\n🔝 Top 5 Exporters (Gen > Demand):")
    top_exporters = sorted([g for g in gsp_data if g['flow_status'] == 'EXPORTING'], 
                           key=lambda x: x['net_flow_mw'], reverse=True)[:5]
    for i, gsp in enumerate(top_exporters, 1):
        print(f"   {i}. {gsp['gsp']:10s} +{gsp['net_flow_mw']:8,.0f} MW  "
              f"(Gen: {gsp['generation_mw']:7,.0f} | Dem: {gsp['demand_mw']:7,.0f})")
    
    # Top importers
    print(f"\n🔝 Top 5 Importers (Demand > Gen):")
    top_importers = sorted([g for g in gsp_data if g['flow_status'] == 'IMPORTING'], 
                           key=lambda x: x['net_flow_mw'])[:5]
    for i, gsp in enumerate(top_importers, 1):
        print(f"   {i}. {gsp['gsp']:10s} {gsp['net_flow_mw']:8,.0f} MW  "
              f"(Gen: {gsp['generation_mw']:7,.0f} | Dem: {gsp['demand_mw']:7,.0f})")
    
    # Create HTML map
    print(f"\n🗺️  Creating interactive map...")
    html = create_html_map(gsp_data)
    
    output_file = "gsp_live_flow_map.html"
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Map created: {output_file}")
    print(f"\n🌐 To view:")
    print(f"   1. Open {output_file} in your browser")
    print(f"   2. Or run: open {output_file}")
    print(f"\n💡 Map shows:")
    print(f"   • 🟦 Blue circles = Exporting (Generation > Demand)")
    print(f"   • 🟧 Orange circles = Importing (Demand > Generation)")
    print(f"   • Circle size = Magnitude of net flow")
    print(f"   • Click markers for detailed info")

if __name__ == "__main__":
    main()
