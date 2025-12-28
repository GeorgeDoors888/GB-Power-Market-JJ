#!/usr/bin/env python3
"""
Export DNO boundaries to formats compatible with Google Maps/My Maps
Options:
1. KML/KMZ for Google My Maps import
2. GeoJSON for Google Maps JavaScript API
3. CSV with postcode→DNO mapping for My Maps
"""

from google.cloud import bigquery
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def export_dno_to_geojson():
    """Export DNO boundaries as GeoJSON for Google Maps API"""
    print('📍 Exporting DNO boundaries to GeoJSON...')
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    query = f"""
    SELECT 
        d.dno_id,
        d.dno_full_name,
        d.area_name,
        d.dno_code,
        c.total_cost_gbp,
        c.voltage_cost_gbp,
        c.thermal_cost_gbp,
        c.cost_per_sq_km,
        ST_ASGEOJSON(d.boundary) as geometry,
        CAST(ST_AREA(d.boundary) / 1000000 AS INT64) as area_sq_km
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries` d
    JOIN `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno_latest` c
        ON d.dno_id = c.dno_id
    ORDER BY c.total_cost_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    
    # Build GeoJSON
    features = []
    for _, row in df.iterrows():
        geometry = json.loads(row['geometry'])
        
        features.append({
            'type': 'Feature',
            'geometry': geometry,
            'properties': {
                'dno_id': int(row['dno_id']),
                'dno_code': row['dno_code'],
                'dno_name': row['dno_full_name'],
                'area_name': row['area_name'],
                'total_cost_gbp': float(row['total_cost_gbp']),
                'voltage_cost_gbp': float(row['voltage_cost_gbp']),
                'thermal_cost_gbp': float(row['thermal_cost_gbp']),
                'cost_per_sq_km': float(row['cost_per_sq_km']),
                'area_sq_km': int(row['area_sq_km']),
                'cost_millions': round(row['total_cost_gbp'] / 1_000_000, 2),
                'description': f"{row['dno_full_name']}<br>Total Cost: £{row['total_cost_gbp']/1e6:.2f}M<br>Cost/km²: £{row['cost_per_sq_km']:.2f}"
            }
        })
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'title': 'UK DNO Constraint Costs',
            'description': 'Distribution Network Operator boundaries with constraint costs',
            'source': 'NESO + BigQuery',
            'date': '2025-12-28'
        }
    }
    
    # Save GeoJSON
    output_file = 'dno_boundaries.geojson'
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f'✅ GeoJSON exported: {output_file} ({len(features)} DNO regions)')
    return output_file

def export_dno_to_kml():
    """Export DNO boundaries as KML for Google My Maps"""
    print('\n📍 Exporting DNO boundaries to KML...')
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    query = f"""
    SELECT 
        d.dno_id,
        d.dno_full_name,
        d.area_name,
        d.dno_code,
        c.total_cost_gbp,
        ST_ASKML(d.boundary) as kml_geometry
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries` d
    JOIN `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno_latest` c
        ON d.dno_id = c.dno_id
    ORDER BY c.total_cost_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    
    # Build KML
    kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = ET.SubElement(kml, 'Document')
    
    # Add name and description
    ET.SubElement(document, 'name').text = 'UK DNO Constraint Costs'
    ET.SubElement(document, 'description').text = 'Distribution Network Operator boundaries with constraint costs (Dec 2025)'
    
    # Add style for polygons
    style = ET.SubElement(document, 'Style', id='dnoStyle')
    line_style = ET.SubElement(style, 'LineStyle')
    ET.SubElement(line_style, 'color').text = 'ff0000ff'  # Red
    ET.SubElement(line_style, 'width').text = '2'
    poly_style = ET.SubElement(style, 'PolyStyle')
    ET.SubElement(poly_style, 'color').text = '4d0000ff'  # Semi-transparent red
    
    # Add placemarks for each DNO
    for _, row in df.iterrows():
        placemark = ET.SubElement(document, 'Placemark')
        ET.SubElement(placemark, 'name').text = f"{row['dno_code']} - {row['area_name']}"
        ET.SubElement(placemark, 'styleUrl').text = '#dnoStyle'
        
        # Description with costs
        description = f"""
        <![CDATA[
        <b>{row['dno_full_name']}</b><br/>
        Area: {row['area_name']}<br/>
        DNO Code: {row['dno_code']}<br/>
        Total Constraint Cost: £{row['total_cost_gbp']/1e6:.2f}M
        ]]>
        """
        ET.SubElement(placemark, 'description').text = description.strip()
        
        # Parse KML geometry
        kml_geom = ET.fromstring(row['kml_geometry'])
        placemark.append(kml_geom)
    
    # Pretty print
    xml_str = ET.tostring(kml, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ')
    
    # Save KML
    output_file = 'dno_boundaries.kml'
    with open(output_file, 'w') as f:
        f.write(pretty_xml)
    
    print(f'✅ KML exported: {output_file} ({len(df)} DNO regions)')
    print(f'\n💡 Import to Google My Maps:')
    print(f'   1. Go to: https://www.google.com/mymaps')
    print(f'   2. Create New Map')
    print(f'   3. Click "Import" → Upload {output_file}')
    return output_file

def create_google_maps_html():
    """Create Google Maps JavaScript API demo"""
    print('\n📍 Creating Google Maps API demo...')
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>UK DNO Constraint Costs - Google Maps</title>
    <style>
        #map { height: 100%; }
        html, body { height: 100%; margin: 0; padding: 0; }
        .info-window {
            font-family: Arial, sans-serif;
            max-width: 300px;
        }
        .info-window h3 { margin: 0 0 10px 0; color: #1a73e8; }
        .info-window p { margin: 5px 0; }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <script>
        let map;
        let infoWindow;

        function initMap() {
            // Center on UK
            map = new google.maps.Map(document.getElementById('map'), {
                center: { lat: 54.5, lng: -3.5 },
                zoom: 6,
                mapTypeId: 'terrain'
            });

            infoWindow = new google.maps.InfoWindow();

            // Load GeoJSON from file
            map.data.loadGeoJson('dno_boundaries.geojson');

            // Style features based on cost
            map.data.setStyle(function(feature) {
                const cost = feature.getProperty('total_cost_gbp');
                const maxCost = 10000000; // £10M
                const opacity = Math.min(cost / maxCost, 0.8);
                
                return {
                    fillColor: '#2196F3',
                    fillOpacity: opacity,
                    strokeColor: '#1565C0',
                    strokeWeight: 2,
                    strokeOpacity: 0.8
                };
            });

            // Add click listener
            map.data.addListener('click', function(event) {
                const feature = event.feature;
                const dnoName = feature.getProperty('dno_name');
                const areaName = feature.getProperty('area_name');
                const costM = feature.getProperty('cost_millions');
                const costPerKm = feature.getProperty('cost_per_sq_km');
                const voltageCost = (feature.getProperty('voltage_cost_gbp') / 1e6).toFixed(2);
                const thermalCost = (feature.getProperty('thermal_cost_gbp') / 1e6).toFixed(2);
                
                const content = `
                    <div class="info-window">
                        <h3>${areaName}</h3>
                        <p><strong>DNO:</strong> ${dnoName}</p>
                        <p><strong>Total Cost:</strong> £${costM}M</p>
                        <p><strong>Voltage:</strong> £${voltageCost}M</p>
                        <p><strong>Thermal:</strong> £${thermalCost}M</p>
                        <p><strong>Cost/km²:</strong> £${costPerKm.toFixed(2)}</p>
                    </div>
                `;
                
                infoWindow.setContent(content);
                infoWindow.setPosition(event.latLng);
                infoWindow.open(map);
            });
        }
    </script>
    
    <!-- Replace YOUR_API_KEY with actual Google Maps API key -->
    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap" async defer></script>
</body>
</html>"""
    
    output_file = 'dno_google_maps.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f'✅ Google Maps demo: {output_file}')
    print(f'\n⚠️  Requires Google Maps API key!')
    print(f'   Get one at: https://developers.google.com/maps/documentation/javascript/get-api-key')
    return output_file

def main():
    print('🗺️  Exporting DNO Boundaries for Google Maps/My Maps')
    print('='*80)
    
    # Export all formats
    geojson_file = export_dno_to_geojson()
    kml_file = export_dno_to_kml()
    html_file = create_google_maps_html()
    
    print('\n' + '='*80)
    print('✅ SUCCESS: DNO boundaries exported to Google-compatible formats')
    print('='*80)
    print(f'\nFiles created:')
    print(f'  1. {geojson_file} - For Google Maps JavaScript API')
    print(f'  2. {kml_file} - For Google My Maps import')
    print(f'  3. {html_file} - Demo HTML (needs API key)')
    
    print(f'\n🎯 RECOMMENDED APPROACH:')
    print(f'  1. Google My Maps (easiest):')
    print(f'     - Import {kml_file} to https://www.google.com/mymaps')
    print(f'     - Free, no API key needed')
    print(f'     - Can share/embed the map')
    print(f'     - Limited styling options')
    print(f'  ')
    print(f'  2. Google Maps JavaScript API (most powerful):')
    print(f'     - Load {geojson_file} in custom HTML')
    print(f'     - Requires API key (free tier: 28,000 map loads/month)')
    print(f'     - Full control over styling')
    print(f'     - Can integrate with your dashboard')

if __name__ == '__main__':
    main()
