#!/usr/bin/env python3
"""
GSP Flow Visualization - Generation vs Import/Export
Shows which GSP areas are net exporters or importers
"""

from google.cloud import bigquery
import json

def main():
    print("="*70)
    print("⚡ GSP FLOW MAP - GENERATION VS IMPORT/EXPORT")
    print("="*70)
    
    client = bigquery.Client(project="inner-cinema-476211-u9")
    
    # Direct join query - simpler and more reliable
    query = """
    WITH gsp_flows AS (
        SELECT 
            g.boundary as gsp,
            SUM(g.generation) as gen_mw,
            SUM(d.demand) as dem_mw
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen` g
        INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem` d 
            ON g.boundary = d.boundary 
            AND DATE(g.settlementDate) = DATE(d.settlementDate)
            AND g.settlementPeriod = d.settlementPeriod
        WHERE DATE(g.settlementDate) = '2025-10-30'
          AND g.settlementPeriod = 48
        GROUP BY gsp
    ),
    gsp_info AS (
        SELECT gsp, AVG(lat) as lat, AVG(lng) as lng,
               COUNT(*) as gens, SUM(capacity_mw) as cap
        FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators`
        WHERE gsp IS NOT NULL AND lat IS NOT NULL
        GROUP BY gsp
    )
    SELECT 
        i.gsp, i.lat, i.lng, i.gens, ROUND(i.cap,2) as cap,
        ROUND(f.gen_mw,2) as gen, ROUND(f.dem_mw,2) as dem,
        ROUND(f.gen_mw - f.dem_mw, 2) as net,
        IF(f.gen_mw > f.dem_mw, 'EXPORTING', 'IMPORTING') as status
    FROM gsp_info i
    INNER JOIN gsp_flows f ON i.gsp = f.gsp
    ORDER BY ABS(f.gen_mw - f.dem_mw) DESC
    """
    
    print("🔍 Querying GSP data...")
    results = list(client.query(query).result())
    
    if not results:
        print("❌ No data found")
        return
    
    data = []
    for r in results:
        data.append({
            'gsp': r.gsp, 'lat': r.lat, 'lng': r.lng,
            'gens': r.gens, 'cap': r.cap,
            'gen': r.gen, 'dem': r.dem, 'net': r.net,
            'status': r.status
        })
    
    print(f"✅ Found {len(data)} GSP areas with data\n")
    
    exp = [d for d in data if d['status'] == 'EXPORTING']
    imp = [d for d in data if d['status'] == 'IMPORTING']
    
    print(f"📊 Summary:")
    print(f"   🟦 Exporting: {len(exp)} areas")
    print(f"   🟧 Importing: {len(imp)} areas\n")
    
    print("🔝 Top 5 Exporters (Gen > Dem):")
    for i, g in enumerate(sorted(exp, key=lambda x: x['net'], reverse=True)[:5], 1):
        print(f"   {i}. {g['gsp']:8s} +{g['net']:8,.0f} MW  (Gen: {g['gen']:7,.0f} | Dem: {g['dem']:7,.0f})")
    
    print("\n🔝 Top 5 Importers (Dem > Gen):")
    for i, g in enumerate(sorted(imp, key=lambda x: x['net'])[:5], 1):
        print(f"   {i}. {g['gsp']:8s} {g['net']:9,.0f} MW  (Gen: {g['gen']:7,.0f} | Dem: {g['dem']:7,.0f})")
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html><head><title>GSP Flow Map</title>
<style>
body{{margin:0;font-family:Arial;background:#1a1a1a;color:#fff}}
#map{{height:100vh;width:100%}}
.info{{position:absolute;top:20px;left:20px;background:rgba(0,0,0,0.9);padding:20px;border-radius:10px;border:2px solid #4CAF50;max-width:350px}}
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
<h2 style="margin:0 0 15px 0;color:#4CAF50">⚡ GSP Flow Status</h2>
<p style="font-size:12px;color:#aaa">30 Oct 2025, SP48 (23:30)</p>
<div>Total: <strong>{len(data)}</strong> GSP areas</div>
<div class="stat exp"><strong>🟦 Exporting:</strong> {len(exp)} areas<br><small>Generation &gt; Demand</small></div>
<div class="stat imp"><strong>🟧 Importing:</strong> {len(imp)} areas<br><small>Demand &gt; Generation</small></div>
</div>
<div class="legend">
<div style="font-weight:bold;margin-bottom:10px">Legend</div>
<div class="legend-item"><div class="circle" style="background:rgba(0,188,212,0.7)"></div><span>Exporting</span></div>
<div class="legend-item"><div class="circle" style="background:rgba(255,152,0,0.7)"></div><span>Importing</span></div>
</div>
<script>
const data={json.dumps(data)};
function initMap(){{
const map=new google.maps.Map(document.getElementById('map'),{{
center:{{lat:54.5,lng:-3.5}},zoom:6,mapTypeId:'roadmap',
styles:[
{{"elementType":"geometry","stylers":[{{"color":"#212121"}}]}},
{{"elementType":"labels.text.fill","stylers":[{{"color":"#757575"}}]}},
{{"featureType":"water","elementType":"geometry","stylers":[{{"color":"#000000"}}]}}
]
}});
data.forEach(gsp=>{{
const isExp=gsp.status==='EXPORTING';
const sz=Math.min(Math.max(Math.abs(gsp.net)/200,3),15);
const m=new google.maps.Marker({{
position:{{lat:gsp.lat,lng:gsp.lng}},map:map,title:gsp.gsp,
icon:{{path:google.maps.SymbolPath.CIRCLE,fillColor:isExp?'#00bcd4':'#ff9800',
fillOpacity:0.7,strokeColor:'#fff',strokeWeight:2,scale:sz}}
}});
const info=new google.maps.InfoWindow({{content:`
<div style="color:#000;padding:10px;max-width:300px">
<h3 style="margin:0 0 10px 0;color:${{isExp?'#00bcd4':'#ff9800'}}">GSP: ${{gsp.gsp}}</h3>
<div style="background:#f5f5f5;padding:10px;border-radius:5px;margin:10px 0">
<strong>Status:</strong> <span style="font-weight:bold;color:${{isExp?'#00bcd4':'#ff9800'}}">
${{isExp?'🟦 EXPORTING':'🟧 IMPORTING'}}</span>
</div>
<table style="width:100%;border-collapse:collapse">
<tr style="border-bottom:1px solid #ddd"><td style="padding:5px"><strong>Generation:</strong></td>
<td style="text-align:right;padding:5px">${{gsp.gen.toLocaleString()}} MW</td></tr>
<tr style="border-bottom:1px solid #ddd"><td style="padding:5px"><strong>Demand:</strong></td>
<td style="text-align:right;padding:5px">${{gsp.dem.toLocaleString()}} MW</td></tr>
<tr style="background:${{isExp?'#e0f7fa':'#fff3e0'}}"><td style="padding:5px"><strong>Net Flow:</strong></td>
<td style="text-align:right;padding:5px;font-weight:bold">${{isExp?'+':''}}${{gsp.net.toLocaleString()}} MW</td></tr>
</table>
<div style="margin-top:10px;padding-top:10px;border-top:1px solid #ddd;font-size:12px;color:#666">
<strong>Capacity:</strong> ${{gsp.cap.toLocaleString()}} MW<br>
<strong>Generators:</strong> ${{gsp.gens}}
</div>
</div>
`}});
m.addListener('click',()=>info.open(map,m));
}});
}}
google.maps.event.addDomListener(window,'load',initMap);
</script>
</body></html>"""
    
    with open('gsp_live_flow_map.html','w') as f:
        f.write(html)
    
    print("\n✅ Map created: gsp_live_flow_map.html")
    print("🌐 To view: open gsp_live_flow_map.html")
    print("💡 Blue = Exporting | Orange = Importing | Size = Flow magnitude")

if __name__=="__main__":
    main()
