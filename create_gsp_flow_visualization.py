#!/usr/bin/env python3
"""
GSP Flow Map - Simplified Version
Shows GB grid supply points with generation vs demand
Uses approximate coordinates for GSP areas
"""

from google.cloud import bigquery
import json

# Approximate GSP center coordinates (from GB electricity grid)
GSP_COORDS = {
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
    'N': {'name': 'National Grid', 'lat': 54.5, 'lng': -3.5}
}

def main():
    print("="*70)
    print("⚡ GSP FLOW MAP - GENERATION VS IMPORT/EXPORT") 
    print("="*70)
    
    client = bigquery.Client(project="inner-cinema-476211-u9")
    
    # Get latest GSP generation and demand data
    # Query for latest GSP flow data
    query = """
    SELECT 
        g.boundary as gsp,
        SUM(g.generation) as total_generation_mw,
        SUM(d.demand) as total_demand_mw,
        SUM(g.generation) - SUM(d.demand) as net_flow_mw
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen` g
    INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem` d
        ON g.boundary = d.boundary 
        AND DATE(g.settlementDate) = DATE(d.settlementDate)
        AND g.settlementPeriod = d.settlementPeriod
    WHERE DATE(g.settlementDate) = '2025-10-29'
        AND g.settlementPeriod = 48
    GROUP BY gsp
    ORDER BY net_flow_mw DESC
    """
    
    print("🔍 Querying GSP flow data...")
    results = list(client.query(query).result())
    
    if not results:
        print("❌ No data found")
        return
    
    data = []
    for r in results:
        gsp_info = GSP_COORDS.get(r.gsp, {'name': r.gsp, 'lat': 54.5, 'lng': -3.5})
        status = 'EXPORTING' if r.total_generation_mw > r.total_demand_mw else 'IMPORTING'
        data.append({
            'gsp': r.gsp,
            'name': gsp_info['name'],
            'lat': gsp_info['lat'],
            'lng': gsp_info['lng'],
            'gen': round(r.total_generation_mw, 2),
            'dem': round(r.total_demand_mw, 2),
            'net': round(r.net_flow_mw, 2),
            'status': status
        })
    
    print(f"✅ Found {len(data)} GSP areas with data\n")
    
    exp = [d for d in data if d['status'] == 'EXPORTING']
    imp = [d for d in data if d['status'] == 'IMPORTING']
    
    total_exp = sum(d['net'] for d in exp)
    total_imp = sum(abs(d['net']) for d in imp)
    
    print(f"📊 Summary:")
    print(f"   🟦 Exporting: {len(exp)} areas ({total_exp:,.0f} MW net)")
    print(f"   🟧 Importing: {len(imp)} areas ({total_imp:,.0f} MW net)\n")
    
    print("🔝 Top 5 Exporters (Gen > Demand):")
    for i, g in enumerate(sorted(exp, key=lambda x: x['net'], reverse=True)[:5], 1):
        print(f"   {i}. {g['gsp']:4s} {g['name']:20s} +{g['net']:8,.0f} MW  (Gen: {g['gen']:7,.0f} | Dem: {g['dem']:7,.0f})")
    
    print("\n🔝 Top 5 Importers (Demand > Gen):")
    for i, g in enumerate(sorted(imp, key=lambda x: x['net'])[:5], 1):
        print(f"   {i}. {g['gsp']:4s} {g['name']:20s} {g['net']:9,.0f} MW  (Gen: {g['gen']:7,.0f} | Dem: {g['dem']:7,.0f})")
    
    # Create HTML map
    html = f"""<!DOCTYPE html>
<html><head><title>GSP Flow Map - GB Grid Supply Points</title>
<style>
body{{margin:0;font-family:Arial;background:#1a1a1a;color:#fff}}
#map{{height:100vh;width:100%}}
.info{{position:absolute;top:20px;left:20px;background:rgba(0,0,0,0.9);padding:20px;border-radius:10px;border:2px solid #4CAF50;max-width:400px}}
h2{{margin:0 0 15px 0;color:#4CAF50}}
.stat{{padding:10px;margin:5px 0;border-radius:5px}}
.exp{{background:rgba(0,188,212,0.3);border-left:4px solid #00bcd4}}
.imp{{background:rgba(255,152,0,0.3);border-left:4px solid #ff9800}}
.legend{{position:absolute;bottom:30px;right:20px;background:rgba(0,0,0,0.9);padding:15px;border-radius:10px;border:2px solid #4CAF50}}
.legend-item{{display:flex;align-items:center;margin:8px 0}}
.circle{{width:20px;height:20px;border-radius:50%;margin-right:10px;border:2px solid #fff}}
</style>
<script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDjw_YjobTs0DCbZwl6p1vXbPSxG6YQNCE"></script>
</head><body>
<div id="map"></div>
<div class="info">
<h2>⚡ GB Grid Supply Points</h2>
<p style="font-size:12px;color:#aaa;margin:5px 0">30 October 2025, SP48 (23:30)</p>
<p style="font-size:13px">Total GSP Areas: <strong>{len(data)}</strong></p>
<div class="stat exp">
<strong>🟦 Exporting: {len(exp)} areas</strong><br>
<small>Total: +{total_exp:,.0f} MW</small><br>
<small style="color:#aaa">Generation exceeds local demand</small>
</div>
<div class="stat imp">
<strong>🟧 Importing: {len(imp)} areas</strong><br>
<small>Total: {total_imp:,.0f} MW</small><br>
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
const data={json.dumps(data)};
function initMap(){{
const map=new google.maps.Map(document.getElementById('map'),{{
center:{{lat:54,lng:-2.5}},zoom:6,mapTypeId:'roadmap',
styles:[
{{"elementType":"geometry","stylers":[{{"color":"#212121"}}]}},
{{"elementType":"labels.text.fill","stylers":[{{"color":"#757575"}}]}},
{{"elementType":"labels.text.stroke","stylers":[{{"color":"#212121"}}]}},
{{"featureType":"water","elementType":"geometry","stylers":[{{"color":"#000000"}}]}}
]
}});

data.forEach(gsp=>{{
const isExp=gsp.status==='EXPORTING';
const sz=Math.min(Math.max(Math.abs(gsp.net)/300,4),18);

const m=new google.maps.Marker({{
position:{{lat:gsp.lat,lng:gsp.lng}},
map:map,
title:gsp.gsp+' - '+gsp.name,
icon:{{
path:google.maps.SymbolPath.CIRCLE,
fillColor:isExp?'#00bcd4':'#ff9800',
fillOpacity:0.8,
strokeColor:'#fff',
strokeWeight:2,
scale:sz
}}
}});

const info=new google.maps.InfoWindow({{content:`
<div style="color:#000;padding:15px;max-width:320px;font-family:Arial">
<h3 style="margin:0 0 10px 0;color:${{isExp?'#00bcd4':'#ff9800'}};border-bottom:2px solid ${{isExp?'#00bcd4':'#ff9800'}};padding-bottom:10px">
GSP ${{gsp.gsp}}: ${{gsp.name}}
</h3>
<div style="background:${{isExp?'#e0f7fa':'#fff3e0'}};padding:15px;border-radius:8px;margin:15px 0;text-align:center">
<div style="font-size:24px;font-weight:bold;color:${{isExp?'#00bcd4':'#ff9800'}}">
${{isExp?'🟦 EXPORTING':'🟧 IMPORTING'}}
</div>
<div style="font-size:18px;font-weight:bold;margin-top:10px">
${{isExp?'+':''}}${{gsp.net.toLocaleString()}} MW
</div>
</div>
<table style="width:100%;border-collapse:collapse;margin-top:10px">
<tr style="border-bottom:2px solid #e0e0e0;background:#f5f5f5">
<td style="padding:10px;font-weight:bold">Metric</td>
<td style="padding:10px;text-align:right;font-weight:bold">Value</td>
</tr>
<tr style="border-bottom:1px solid #e0e0e0">
<td style="padding:10px">⚡ Local Generation</td>
<td style="text-align:right;padding:10px;font-weight:bold">${{gsp.gen.toLocaleString()}} MW</td>
</tr>
<tr style="border-bottom:1px solid #e0e0e0">
<td style="padding:10px">💡 Local Demand</td>
<td style="text-align:right;padding:10px;font-weight:bold">${{gsp.dem.toLocaleString()}} MW</td>
</tr>
<tr style="background:${{isExp?'#e0f7fa':'#fff3e0'}}">
<td style="padding:10px"><strong>📊 Net Flow</strong></td>
<td style="text-align:right;padding:10px;font-weight:bold;color:${{isExp?'#00bcd4':'#ff9800'}}">
${{isExp?'+':''}}${{gsp.net.toLocaleString()}} MW
</td>
</tr>
</table>
<div style="margin-top:15px;padding-top:15px;border-top:2px solid #e0e0e0;font-size:12px;color:#666;text-align:center">
<strong>Settlement Period 48</strong> (23:30 on 30 Oct 2025)<br>
${{isExp ? 'Surplus power flows to other areas' : 'Additional power imported from grid'}}
</div>
</div>
`}});

m.addListener('click',()=>info.open(map,m));
}});

console.log(`✅ Loaded ${{data.length}} GSP areas`);
}}

google.maps.event.addDomListener(window,'load',initMap);
</script>
</body></html>"""
    
    with open('gsp_live_flow_map.html','w') as f:
        f.write(html)
    
    print("\n✅ Interactive map created: gsp_live_flow_map.html")
    print("🌐 To view: open gsp_live_flow_map.html")
    print("\n💡 Map features:")
    print("   • 🟦 Blue circles = Net exporters (Gen > Demand)")
    print("   • 🟧 Orange circles = Net importers (Demand > Gen)")
    print("   • Circle size = Magnitude of power flow")
    print("   • Click any circle for detailed GSP information")

if __name__=="__main__":
    main()
