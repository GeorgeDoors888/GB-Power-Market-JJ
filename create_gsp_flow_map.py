#!/usr/bin/env python3
"""
Create GSP Flow Map - Shows Grid Supply Points as Net Exporters or Importers
Queries latest BMRS data from BigQuery and generates interactive HTML map
"""

from google.cloud import bigquery
from datetime import datetime
import json

# Initialize BigQuery client
client = bigquery.Client(project="inner-cinema-476211-u9")

# GSP coordinates (approximate central points)
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

# Query latest GSP flow data
query = """
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

print("🔍 Querying latest GSP flow data from BigQuery...")
results = client.query(query).result()

# Process results
gsp_data = []
latest_date = None
latest_period = None
exporters = 0
importers = 0
total_export = 0
total_import = 0

for row in results:
    gsp_code = row.gsp
    if gsp_code not in GSP_COORDS:
        continue
    
    coords = GSP_COORDS[gsp_code]
    net_flow = row.net_flow_mw
    is_exporter = net_flow > 0
    
    if is_exporter:
        exporters += 1
        total_export += net_flow
    else:
        importers += 1
        total_import += abs(net_flow)
    
    gsp_data.append({
        'gsp': gsp_code,
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

print(f"✅ Found {len(gsp_data)} GSP areas")
print(f"📅 Data from: {latest_date}, Settlement Period {latest_period}")
print(f"🟦 Exporters: {exporters} ({total_export:,.0f} MW)")
print(f"🟧 Importers: {importers} ({total_import:,.0f} MW)")

# Generate HTML map
html = f"""<!DOCTYPE html>
<html><head><title>GSP Flow Map - GB Grid Supply Points</title>
<style>
body{{margin:0;font-family:Arial;background:#1a1a1a;color:#fff}}
#map{{height:100vh;width:100%}}
.info{{position:absolute;top:20px;left:20px;background:rgba(0,0,0,0.9);padding:20px;border-radius:10px;border:2px solid #4CAF50;max-width:400px;z-index:1000}}
h2{{margin:0 0 15px 0;color:#4CAF50}}
.stat{{padding:10px;margin:5px 0;border-radius:5px}}
.exp{{background:rgba(0,188,212,0.3);border-left:4px solid #00bcd4}}
.imp{{background:rgba(255,152,0,0.3);border-left:4px solid #ff9800}}
.legend{{position:absolute;bottom:30px;right:20px;background:rgba(0,0,0,0.9);padding:15px;border-radius:10px;border:2px solid #4CAF50;z-index:1000}}
.legend-item{{display:flex;align-items:center;margin:8px 0}}
.circle{{width:20px;height:20px;border-radius:50%;margin-right:10px;border:2px solid #fff}}
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head><body>
<div id="map"></div>
<div class="info">
<h2>⚡ GB Grid Supply Points</h2>
<p style="font-size:12px;color:#aaa;margin:5px 0">{latest_date}, SP{latest_period} ({(latest_period-1)*0.5:.1f}h - {latest_period*0.5:.1f}h)</p>
<p style="font-size:13px">Total GSP Areas: <strong>{len(gsp_data)}</strong></p>
<div class="stat exp">
<strong>🟦 Exporting: {exporters} areas</strong><br>
<small>Total: +{total_export:,.0f} MW</small><br>
<small style="color:#aaa">Generation exceeds local demand</small>
</div>
<div class="stat imp">
<strong>🟧 Importing: {importers} areas</strong><br>
<small>Total: -{total_import:,.0f} MW</small><br>
<small style="color:#aaa">Demand exceeds local generation</small>
</div>
</div>
<div class="legend">
<div style="font-weight:bold;margin-bottom:10px">Legend</div>
<div class="legend-item"><div class="circle" style="background:rgba(0,188,212,0.7)"></div><span>Net Exporter</span></div>
<div class="legend-item"><div class="circle" style="background:rgba(255,152,0,0.7)"></div><span>Net Importer</span></div>
<div style="font-size:11px;color:#aaa;margin-top:10px">Circle size = flow magnitude</div>
</div>
<script>
const data={json.dumps(gsp_data)};

// Initialize map
const map = L.map('map', {{
  center: [54, -2.5],
  zoom: 6,
  zoomControl: true
}});

// Dark tiles
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
  maxZoom: 19
}}).addTo(map);

// Calculate max absolute flow for sizing
const maxFlow = Math.max(...data.map(d => Math.abs(d.net)));

// Add markers
data.forEach(gsp => {{
  const isExporter = gsp.status === 'EXPORTING';
  const color = isExporter ? '#00bcd4' : '#ff9800';
  const radius = 10 + (Math.abs(gsp.net) / maxFlow) * 30;
  
  const circle = L.circleMarker([gsp.lat, gsp.lng], {{
    radius: radius,
    fillColor: color,
    fillOpacity: 0.7,
    color: '#fff',
    weight: 2
  }}).addTo(map);
  
  const popupContent = `
    <div style="color:#000;font-family:Arial;min-width:200px">
      <h3 style="margin:0 0 10px 0;color:${{color}}">${{gsp.gsp}} - ${{gsp.name}}</h3>
      <table style="width:100%;font-size:12px">
        <tr><td>Generation:</td><td style="text-align:right"><strong>${{gsp.gen.toLocaleString()}} MW</strong></td></tr>
        <tr><td>Demand:</td><td style="text-align:right"><strong>${{gsp.dem.toLocaleString()}} MW</strong></td></tr>
        <tr><td colspan="2" style="padding-top:5px;border-top:1px solid #ccc"></td></tr>
        <tr><td><strong>Net Flow:</strong></td><td style="text-align:right;color:${{color}}"><strong>${{gsp.net > 0 ? '+' : ''}}${{gsp.net.toLocaleString()}} MW</strong></td></tr>
        <tr><td colspan="2" style="padding-top:5px"><span style="background:${{color}};color:#fff;padding:2px 8px;border-radius:3px;font-size:11px">${{gsp.status}}</span></td></tr>
      </table>
    </div>
  `;
  
  circle.bindPopup(popupContent);
}});

console.log('✅ GSP Flow Map loaded successfully');
console.log(`📊 Exporters: {exporters}, Importers: {importers}`);
</script>
</body></html>"""

# Save to file
output_file = 'gsp_live_flow_map.html'
with open(output_file, 'w') as f:
    f.write(html)

print(f"\n✅ Map created: {output_file}")
print(f"🌐 Open in browser to view GSP flows")
