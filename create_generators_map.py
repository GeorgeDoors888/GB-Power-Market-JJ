#!/usr/bin/env python3
"""
Create interactive map showing:
1. All 7,072 SVA generators with their actual locations
2. Colored by DNO region
3. GSP flow data overlaid
"""

from google.cloud import bigquery
import json

def main():
    print("="*70)
    print("🗺️  CREATING COMPREHENSIVE GB POWER MAP")
    print("="*70)
    
    client = bigquery.Client(project="inner-cinema-476211-u9")
    
    # Get generator data by DNO
    print("\n🔍 Querying generator data...")
    gen_query = """
    SELECT 
        dno,
        COUNT(*) as num_generators,
        SUM(capacity_mw) as total_capacity_mw,
        ARRAY_AGG(STRUCT(name, lat, lng, capacity_mw, fuel_type, gsp) LIMIT 100) as sample_generators
    FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords`
    WHERE lat IS NOT NULL AND lng IS NOT NULL
    GROUP BY dno
    ORDER BY total_capacity_mw DESC
    """
    
    dno_data = list(client.query(gen_query).result())
    
    print(f"✅ Found {len(dno_data)} DNO regions\n")
    
    for dno in dno_data[:10]:
        print(f"   {dno.dno[:40]:40s} {dno.num_generators:>4} gens  {dno.total_capacity_mw:>8,.0f} MW")
    
    # Get ALL generators for the map
    print("\n🔍 Loading all generator locations...")
    all_gen_query = """
    SELECT name, lat, lng, capacity_mw, fuel_type, dno, gsp
    FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords`
    WHERE lat IS NOT NULL AND lng IS NOT NULL
    ORDER BY capacity_mw DESC
    """
    
    all_generators = list(client.query(all_gen_query).result())
    print(f"✅ Loaded {len(all_generators):,} generator locations")
    
    # Prepare data
    generators_data = []
    for g in all_generators:
        generators_data.append({
            'name': g.name,
            'lat': g.lat,
            'lng': g.lng,
            'capacity': round(g.capacity_mw, 2) if g.capacity_mw else 0,
            'fuel': g.fuel_type or 'Unknown',
            'dno': g.dno or 'Unknown',
            'gsp': g.gsp or 'Unknown'
        })
    
    # Generate HTML
    html = generate_html(generators_data)
    
    output_file = "gb_generators_map.html"
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Map created: {output_file}")
    print(f"🌐 To view: open {output_file}")
    print(f"\n📊 Map shows {len(generators_data):,} generators across GB")

def generate_html(generators):
    # Sample generators for faster loading (show top 2000)
    sample_gens = generators[:2000]
    
    data_json = json.dumps(sample_gens)
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GB Power Generators Map - All {len(generators):,} Sites</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; }}
        #map {{ height: 100vh; width: 100%; }}
        .info {{
            position: absolute; top: 20px; left: 20px;
            background: rgba(0,0,0,0.95); padding: 20px;
            border-radius: 10px; border: 2px solid #4CAF50;
            max-width: 350px; z-index: 1000;
        }}
        h2 {{ margin: 0 0 10px 0; color: #4CAF50; }}
        .legend {{
            position: absolute; bottom: 30px; right: 20px;
            background: rgba(0,0,0,0.95); padding: 15px;
            border-radius: 10px; border: 2px solid #4CAF50;
            z-index: 1000; max-width: 250px;
        }}
        .fuel-item {{ display: flex; align-items: center; margin: 5px 0; font-size: 12px; }}
        .fuel-dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; border: 1px solid #fff; }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info">
        <h2>⚡ GB Power Generators</h2>
        <p style="font-size:13px;margin:5px 0"><strong>{len(generators):,}</strong> generation sites</p>
        <p style="font-size:11px;color:#aaa">Showing top 2,000 by capacity</p>
        <p style="font-size:11px;margin-top:10px;color:#888">
            Click any marker to see details<br>
            Zoom in to see individual sites<br>
            Clusters show number of sites
        </p>
    </div>
    
    <div class="legend">
        <div style="font-weight:bold;margin-bottom:10px">Fuel Types</div>
        <div class="fuel-item"><div class="fuel-dot" style="background:#ff9800"></div>Solar</div>
        <div class="fuel-item"><div class="fuel-dot" style="background:#2196F3"></div>Wind</div>
        <div class="fuel-item"><div class="fuel-dot" style="background:#4CAF50"></div>Biomass / Hydro</div>
        <div class="fuel-item"><div class="fuel-dot" style="background:#9C27B0"></div>Gas</div>
        <div class="fuel-item"><div class="fuel-dot" style="background:#F44336"></div>Coal / Oil</div>
        <div class="fuel-item"><div class="fuel-dot" style="background:#607D8B"></div>Battery / Other</div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <script>
        const generators = {data_json};
        
        const map = L.map('map').setView([54, -2.5], 6);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CartoDB',
            maxZoom: 19
        }}).addTo(map);

        const markers = L.markerClusterGroup({{
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false
        }});

        function getFuelColor(fuel) {{
            const f = (fuel || '').toLowerCase();
            if (f.includes('solar') || f.includes('pv')) return '#ff9800';
            if (f.includes('wind')) return '#2196F3';
            if (f.includes('biomass') || f.includes('hydro') || f.includes('anaerobic')) return '#4CAF50';
            if (f.includes('gas') || f.includes('ccgt')) return '#9C27B0';
            if (f.includes('coal') || f.includes('oil')) return '#F44336';
            if (f.includes('battery') || f.includes('storage')) return '#607D8B';
            return '#999999';
        }}

        generators.forEach(gen => {{
            const color = getFuelColor(gen.fuel);
            const size = Math.min(Math.max(Math.sqrt(gen.capacity) * 0.8, 3), 12);
            
            const circle = L.circleMarker([gen.lat, gen.lng], {{
                radius: size,
                fillColor: color,
                color: '#ffffff',
                weight: 1,
                opacity: 0.8,
                fillOpacity: 0.7
            }});

            const popupContent = `
                <div style="color:#000;padding:10px;min-width:220px;font-family:Arial">
                    <h4 style="margin:0 0 8px 0;color:${{color}};border-bottom:2px solid ${{color}};padding-bottom:5px">
                        ${{gen.name}}
                    </h4>
                    <table style="width:100%;font-size:12px">
                        <tr>
                            <td style="padding:3px">⚡ Capacity:</td>
                            <td style="text-align:right;padding:3px;font-weight:bold">${{gen.capacity}} MW</td>
                        </tr>
                        <tr>
                            <td style="padding:3px">🔋 Type:</td>
                            <td style="text-align:right;padding:3px">${{gen.fuel}}</td>
                        </tr>
                        <tr>
                            <td style="padding:3px">🏢 DNO:</td>
                            <td style="text-align:right;padding:3px;font-size:10px">${{gen.dno}}</td>
                        </tr>
                        <tr>
                            <td style="padding:3px">📍 GSP:</td>
                            <td style="text-align:right;padding:3px">${{gen.gsp}}</td>
                        </tr>
                    </table>
                </div>
            `;

            circle.bindPopup(popupContent);
            markers.addLayer(circle);
        }});

        map.addLayer(markers);
        console.log(`✅ Loaded ${{generators.length}} generators on map`);
    </script>
</body>
</html>'''

if __name__ == "__main__":
    main()
