#!/usr/bin/env python3
"""
Comprehensive GB Power Map - Shows:
1. GSP Flow circles (export/import status)
2. All power stations (CVA + SVA)
3. Offshore wind farms
4. DNO boundaries
"""

from google.cloud import bigquery
from datetime import datetime
import json

# Initialize BigQuery client
client = bigquery.Client(project="inner-cinema-476211-u9")

# GSP coordinates
GSP_COORDS = {
    'N': {'name': 'National Grid', 'lat': 54.5, 'lng': -3.5},
    'B1': {'name': 'Barking', 'lat': 51.5362, 'lng': 0.0810},
    'B2': {'name': 'Ealing', 'lat': 51.5154, 'lng': -0.2994},
    'B3': {'name': 'Wimbledon', 'lat': 51.4214, 'lng': -0.2072},
    'B4': {'name': 'Brixton', 'lat': 51.4615, 'lng': -0.1125},
    'B5': {'name': 'City Road', 'lat': 51.5319, 'lng': -0.0966},
    'B6': {'name': 'Willesden', 'lat': 51.5489, 'lng': -0.2356},
    'B7': {'name': 'Hurst', 'lat': 51.4459, 'lng': -0.4815},
    'B8': {'name': 'Sundon', 'lat': 51.9476, 'lng': -0.4682},
    'B9': {'name': 'Pelham', 'lat': 51.7422, 'lng': -0.0475},
    'B10': {'name': 'Bramley', 'lat': 51.3244, 'lng': -0.9947},
    'B11': {'name': 'Melksham', 'lat': 51.3687, 'lng': -2.1413},
    'B12': {'name': 'Exeter', 'lat': 50.7184, 'lng': -3.5339},
    'B13': {'name': 'Bristol', 'lat': 51.4545, 'lng': -2.5879},
    'B14': {'name': 'Indian Queens', 'lat': 50.4019, 'lng': -4.9378},
    'B15': {'name': 'Landulph', 'lat': 50.4464, 'lng': -4.2124},
    'B16': {'name': 'Pembroke', 'lat': 51.6750, 'lng': -4.9392},
    'B17': {'name': 'Swansea North', 'lat': 51.6563, 'lng': -3.9436},
}

print("🔍 Step 1: Querying GSP flow data...")
gsp_query = """
WITH latest_data AS (
  SELECT 
    MAX(CONCAT(settlementDate, '-', settlementPeriod)) as latest_timestamp,
    MAX(settlementDate) as latest_date,
    MAX(settlementPeriod) as latest_period
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
),
generation AS (
  SELECT 
    boundary,
    SUM(generation) as total_generation
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
  WHERE CONCAT(settlementDate, '-', settlementPeriod) = (
    SELECT latest_timestamp FROM latest_data
  )
  GROUP BY boundary
),
demand AS (
  SELECT 
    boundary,
    SUM(demand) as total_demand
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem`
  WHERE CONCAT(settlementDate, '-', settlementPeriod) = (
    SELECT latest_timestamp FROM latest_data
  )
  GROUP BY boundary
)
SELECT 
  COALESCE(g.boundary, d.boundary) as gsp,
  COALESCE(g.total_generation, 0) as generation_mw,
  COALESCE(d.total_demand, 0) as demand_mw,
  COALESCE(g.total_generation, 0) + COALESCE(d.total_demand, 0) as net_flow_mw,
  (SELECT latest_date FROM latest_data) as date,
  (SELECT latest_period FROM latest_data) as period
FROM generation g
FULL OUTER JOIN demand d ON g.boundary = d.boundary
ORDER BY net_flow_mw DESC
"""

gsp_results = client.query(gsp_query).result()
gsp_data = []
latest_date = None
latest_period = None
exporters = 0
importers = 0

for row in gsp_results:
    if row.gsp not in GSP_COORDS:
        continue
    coords = GSP_COORDS[row.gsp]
    net_flow = row.net_flow_mw
    is_exporter = net_flow > 0
    
    if is_exporter:
        exporters += 1
    else:
        importers += 1
    
    gsp_data.append({
        'gsp': row.gsp,
        'name': coords['name'],
        'lat': coords['lat'],
        'lng': coords['lng'],
        'gen': round(row.generation_mw, 1),
        'dem': round(row.demand_mw, 1),
        'net': round(net_flow, 1),
        'status': 'EXPORTING' if is_exporter else 'IMPORTING'
    })
    
    if latest_date is None:
        latest_date = row.date
        latest_period = row.period

print(f"✅ Found {len(gsp_data)} GSPs ({exporters} exporters, {importers} importers)")

print("\n🔍 Step 2: Querying offshore wind farms...")
offshore_query = """
SELECT 
  name,
  capacity_mw,
  latitude as lat,
  longitude as lng,
  gsp_zone,
  gsp_region
FROM `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms`
WHERE status = 'Operational'
ORDER BY capacity_mw DESC
"""

offshore_results = client.query(offshore_query).result()
offshore_data = []
total_offshore_capacity = 0

for row in offshore_results:
    offshore_data.append({
        'name': row.name,
        'capacity': row.capacity_mw,
        'lat': row.lat,
        'lng': row.lng,
        'gsp': row.gsp_zone,
        'region': row.gsp_region
    })
    total_offshore_capacity += row.capacity_mw

print(f"✅ Found {len(offshore_data)} offshore wind farms ({total_offshore_capacity:,.0f} MW)")

print("\n🔍 Step 3: Querying onshore generators (SVA + CVA)...")
generators_query = """
SELECT 
  'SVA' as type,
  name,
  lat,
  lng,
  capacity_mw,
  fuel_type,
  dno
FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords`
WHERE lat IS NOT NULL
  AND capacity_mw > 5

UNION ALL

SELECT 
  'CVA' as type,
  name,
  lat,
  lng,
  NULL as capacity_mw,
  fuel_type,
  NULL as dno
FROM `inner-cinema-476211-u9.uk_energy_prod.cva_plants`
WHERE lat IS NOT NULL

ORDER BY capacity_mw DESC
LIMIT 1000
"""

gen_results = client.query(generators_query).result()
generators = []
cva_count = 0
sva_count = 0

for row in gen_results:
    if row.type == 'CVA':
        cva_count += 1
    else:
        sva_count += 1
    
    generators.append({
        'name': row.name,
        'type': row.type,
        'lat': row.lat,
        'lng': row.lng,
        'capacity': row.capacity_mw if row.capacity_mw else 0,
        'fuel': row.fuel_type if row.fuel_type else 'Unknown',
        'dno': row.dno if row.dno else ''
    })

print(f"✅ Found {len(generators)} generators ({cva_count} CVA, {sva_count} SVA)")

# Generate comprehensive HTML
html = f"""<!DOCTYPE html>
<html><head><title>GB Power System - Comprehensive View</title>
<style>
body{{margin:0;font-family:Arial;background:#1a1a1a;color:#fff}}
#map{{height:100vh;width:100%}}
.controls{{position:absolute;top:20px;left:20px;background:rgba(0,0,0,0.95);padding:20px;border-radius:10px;border:2px solid #4CAF50;max-width:350px;z-index:1000}}
h2{{margin:0 0 15px 0;color:#4CAF50;font-size:18px}}
h3{{margin:15px 0 10px 0;color:#4CAF50;font-size:14px}}
.toggle{{margin:10px 0;padding:10px;background:rgba(76,175,80,0.2);border-radius:5px;cursor:pointer;user-select:none}}
.toggle:hover{{background:rgba(76,175,80,0.3)}}
.toggle input{{margin-right:10px}}
.stat{{font-size:12px;color:#aaa;margin:5px 0;padding:5px;border-left:3px solid #4CAF50}}
.legend{{position:absolute;bottom:30px;right:20px;background:rgba(0,0,0,0.95);padding:15px;border-radius:10px;border:2px solid #4CAF50;z-index:1000;max-width:250px}}
.legend-item{{display:flex;align-items:center;margin:8px 0;font-size:12px}}
.circle{{width:16px;height:16px;border-radius:50%;margin-right:8px;border:2px solid #fff}}
.marker{{width:10px;height:10px;margin-right:8px}}
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
</head><body>
<div id="map"></div>
<div class="controls">
<h2>⚡ GB Power System</h2>
<p style="font-size:11px;color:#aaa;margin:5px 0">{latest_date}, SP{latest_period}</p>

<h3>Layers</h3>
<div class="toggle" onclick="toggleLayer('gsp')">
<input type="checkbox" id="gsp-check" checked> GSP Flow Points ({len(gsp_data)})
</div>
<div class="toggle" onclick="toggleLayer('offshore')">
<input type="checkbox" id="offshore-check" checked> Offshore Wind ({len(offshore_data)})
</div>
<div class="toggle" onclick="toggleLayer('cva')">
<input type="checkbox" id="cva-check" checked> CVA Generators ({cva_count})
</div>
<div class="toggle" onclick="toggleLayer('sva')">
<input type="checkbox" id="sva-check" checked> SVA Generators ({sva_count})
</div>

<h3>Statistics</h3>
<div class="stat">🟦 Exporters: {exporters} GSPs</div>
<div class="stat">🟧 Importers: {importers} GSPs</div>
<div class="stat">🌊 Offshore: {total_offshore_capacity:,.0f} MW</div>
<div class="stat">⚡ Generators: {len(generators)}</div>
</div>

<div class="legend">
<div style="font-weight:bold;margin-bottom:10px;font-size:13px">Legend</div>
<div style="border-bottom:1px solid #444;margin:10px 0;padding-bottom:5px">
<div style="font-size:11px;color:#aaa;margin-bottom:5px">GSP Flow</div>
<div class="legend-item"><div class="circle" style="background:rgba(0,188,212,0.7)"></div><span>Net Exporter</span></div>
<div class="legend-item"><div class="circle" style="background:rgba(255,152,0,0.7)"></div><span>Net Importer</span></div>
</div>
<div style="border-bottom:1px solid #444;margin:10px 0;padding-bottom:5px">
<div style="font-size:11px;color:#aaa;margin-bottom:5px">Wind</div>
<div class="legend-item"><div class="marker" style="background:#00ffff;border-radius:50%"></div><span>Offshore</span></div>
<div class="legend-item"><div class="marker" style="background:#00bfff;border-radius:50%"></div><span>Onshore</span></div>
</div>
<div>
<div style="font-size:11px;color:#aaa;margin-bottom:5px">Other Fuels</div>
<div class="legend-item"><div class="marker" style="background:#ff6b6b"></div><span>Gas/Fossil</span></div>
<div class="legend-item"><div class="marker" style="background:#ffa500"></div><span>Solar</span></div>
<div class="legend-item"><div class="marker" style="background:#32cd32"></div><span>Biomass</span></div>
<div class="legend-item"><div class="marker" style="background:#9b59b6"></div><span>Nuclear</span></div>
</div>
</div>

<script>
const gspData = {json.dumps(gsp_data)};
const offshoreData = {json.dumps(offshore_data)};
const generatorsData = {json.dumps(generators)};

// Initialize map
const map = L.map('map', {{
  center: [54.5, -2.5],
  zoom: 6,
  zoomControl: true
}});

// Dark tiles
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19
}}).addTo(map);

// Layer groups
const layers = {{
  gsp: L.layerGroup().addTo(map),
  offshore: L.layerGroup().addTo(map),
  cva: L.markerClusterGroup({{maxClusterRadius: 50}}),
  sva: L.markerClusterGroup({{maxClusterRadius: 30}})
}};

layers.cva.addTo(map);
layers.sva.addTo(map);

// Toggle function
function toggleLayer(name) {{
  const checkbox = document.getElementById(name + '-check');
  if (layers[name].hasLayer ? Object.keys(layers[name]._layers).length > 0 : map.hasLayer(layers[name])) {{
    map.removeLayer(layers[name]);
    checkbox.checked = false;
  }} else {{
    map.addLayer(layers[name]);
    checkbox.checked = true;
  }}
}}

// Add GSP circles
const maxFlow = Math.max(...gspData.map(d => Math.abs(d.net)));
gspData.forEach(gsp => {{
  const isExporter = gsp.status === 'EXPORTING';
  const color = isExporter ? '#00bcd4' : '#ff9800';
  const radius = 15 + (Math.abs(gsp.net) / maxFlow) * 35;
  
  const circle = L.circleMarker([gsp.lat, gsp.lng], {{
    radius: radius,
    fillColor: color,
    fillOpacity: 0.6,
    color: '#fff',
    weight: 3
  }});
  
  circle.bindPopup(`
    <div style="color:#000;font-family:Arial;min-width:220px">
      <h3 style="margin:0 0 10px 0;color:${{color}};font-size:16px">${{gsp.gsp}} - ${{gsp.name}}</h3>
      <div style="font-size:13px">
        <div style="margin:5px 0">Generation: <strong>${{gsp.gen.toLocaleString()}} MW</strong></div>
        <div style="margin:5px 0">Demand: <strong>${{gsp.dem.toLocaleString()}} MW</strong></div>
        <div style="margin:10px 0;padding-top:8px;border-top:2px solid #ddd">
          <strong style="color:${{color}}">Net Flow: ${{gsp.net > 0 ? '+' : ''}}${{gsp.net.toLocaleString()}} MW</strong>
        </div>
        <div style="margin-top:8px">
          <span style="background:${{color}};color:#fff;padding:4px 10px;border-radius:4px;font-size:12px;font-weight:bold">${{gsp.status}}</span>
        </div>
      </div>
    </div>
  `);
  
  layers.gsp.addLayer(circle);
}});

// Add offshore wind
offshoreData.forEach(wind => {{
  const marker = L.circleMarker([wind.lat, wind.lng], {{
    radius: 6 + Math.sqrt(wind.capacity) / 3,
    fillColor: '#00ffff',
    fillOpacity: 0.8,
    color: '#fff',
    weight: 2
  }});
  
  marker.bindPopup(`
    <div style="color:#000;font-family:Arial">
      <h4 style="margin:0 0 8px 0;color:#00ffff">🌊 ${{wind.name}}</h4>
      <div style="font-size:12px">
        <div>Capacity: <strong>${{wind.capacity}} MW</strong></div>
        <div>Type: <strong>Offshore Wind</strong></div>
        <div>GSP: <strong>${{wind.gsp}}</strong></div>
        <div>Region: <strong>${{wind.region}}</strong></div>
      </div>
    </div>
  `);
  
  layers.offshore.addLayer(marker);
}});

// Fuel colors
const fuelColors = {{
  'WIND': '#00bfff',
  'SOLAR': '#ffa500', 
  'BIOMASS': '#32cd32',
  'GAS': '#ff6b6b',
  'CCGT': '#ff6b6b',
  'OCGT': '#ff6b6b',
  'COAL': '#8b4513',
  'NUCLEAR': '#9b59b6',
  'HYDRO': '#1e90ff',
  'OTHER': '#999'
}};

function getFuelColor(fuel) {{
  const f = fuel.toUpperCase();
  for (let key in fuelColors) {{
    if (f.includes(key)) return fuelColors[key];
  }}
  return '#999';
}}

// Add generators
generatorsData.forEach(gen => {{
  const color = getFuelColor(gen.fuel);
  const radius = gen.capacity > 0 ? 3 + Math.sqrt(gen.capacity) / 5 : 4;
  
  const marker = L.circleMarker([gen.lat, gen.lng], {{
    radius: radius,
    fillColor: color,
    fillOpacity: 0.7,
    color: '#fff',
    weight: 1
  }});
  
  marker.bindPopup(`
    <div style="color:#000;font-family:Arial">
      <h4 style="margin:0 0 8px 0;color:${{color}}">${{gen.name}}</h4>
      <div style="font-size:12px">
        <div>Type: <strong>${{gen.type}}</strong></div>
        <div>Fuel: <strong>${{gen.fuel}}</strong></div>
        ${{gen.capacity > 0 ? '<div>Capacity: <strong>' + gen.capacity + ' MW</strong></div>' : ''}}
        ${{gen.dno ? '<div>DNO: <strong>' + gen.dno + '</strong></div>' : ''}}
      </div>
    </div>
  `);
  
  if (gen.type === 'CVA') {{
    layers.cva.addLayer(marker);
  }} else {{
    layers.sva.addLayer(marker);
  }}
}});

console.log('✅ Comprehensive GB Power Map loaded');
console.log(`📊 GSPs: ${{gspData.length}}, Offshore: ${{offshoreData.length}}, Generators: ${{generatorsData.length}}`);
</script>
</body></html>"""

output_file = 'gb_power_comprehensive_map.html'
with open(output_file, 'w') as f:
    f.write(html)

print(f"\n✅ Comprehensive map created: {output_file}")
print(f"🌐 Map includes:")
print(f"   • {len(gsp_data)} GSP flow points")
print(f"   • {len(offshore_data)} offshore wind farms")
print(f"   • {len(generators)} power stations")
print(f"\n📊 Total offshore wind capacity: {total_offshore_capacity:,.0f} MW")
