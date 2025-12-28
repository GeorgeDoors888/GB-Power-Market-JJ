#!/usr/bin/env python3
"""
Convert DNO GeoJSON to KML for Google My Maps import
Handles coordinate conversion and feature simplification
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

def geojson_to_kml(geojson_file, kml_file):
    """Convert GeoJSON to KML with DNO styling"""
    print(f'📍 Converting {geojson_file} to KML...')
    
    # Load GeoJSON
    with open(geojson_file, 'r') as f:
        geojson = json.load(f)
    
    # Create KML structure
    kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = ET.SubElement(kml, 'Document')
    
    # Metadata
    ET.SubElement(document, 'name').text = 'UK DNO Constraint Costs'
    ET.SubElement(document, 'description').text = '''
Distribution Network Operator boundaries with December 2025 constraint costs.
Data source: NESO + BigQuery uk_energy_prod dataset.
Total: £130.5M across 14 DNO regions.
'''
    
    # Define color scale (blue gradient based on cost)
    cost_brackets = [
        (5000000, 'ff0000ff', 'Very Low'),    # Dark blue
        (7000000, 'ffff0000', 'Low'),         # Blue
        (9000000, 'ffffff00', 'Medium'),      # Cyan
        (11000000, 'ff00ffff', 'High'),       # Yellow
        (float('inf'), 'ff00ff00', 'Very High') # Green
    ]
    
    # Add styles
    for i, (threshold, color, label) in enumerate(cost_brackets):
        style = ET.SubElement(document, 'Style', id=f'cost_{i}')
        line_style = ET.SubElement(style, 'LineStyle')
        ET.SubElement(line_style, 'color').text = 'ff000000'  # Black border
        ET.SubElement(line_style, 'width').text = '2'
        poly_style = ET.SubElement(style, 'PolyStyle')
        ET.SubElement(poly_style, 'color').text = color
        ET.SubElement(poly_style, 'fill').text = '1'
        ET.SubElement(poly_style, 'outline').text = '1'
    
    # Process features
    features_processed = 0
    for feature in geojson['features']:
        props = feature['properties']
        geom = feature['geometry']
        
        # Create placemark
        placemark = ET.SubElement(document, 'Placemark')
        ET.SubElement(placemark, 'name').text = f"{props['dno_code']} - {props['area_name']}"
        
        # Choose style based on cost
        cost = props['total_cost_gbp']
        style_id = 0
        for i, (threshold, _, _) in enumerate(cost_brackets):
            if cost < threshold:
                style_id = i
                break
        ET.SubElement(placemark, 'styleUrl').text = f'#cost_{style_id}'
        
        # Description with full details
        description = f"""
<![CDATA[
<h3>{props['dno_name']}</h3>
<table border="1" cellpadding="5">
<tr><th>DNO Code</th><td>{props['dno_code']}</td></tr>
<tr><th>Region</th><td>{props['area_name']}</td></tr>
<tr><th>Area</th><td>{props['area_sq_km']:,} km²</td></tr>
<tr><th colspan="2" style="background:#f0f0f0"><b>Constraint Costs</b></th></tr>
<tr><th>Total</th><td style="color:red"><b>£{props['cost_millions']:.2f}M</b></td></tr>
<tr><th>Voltage</th><td>£{props['voltage_cost_gbp']/1e6:.2f}M</td></tr>
<tr><th>Thermal</th><td>£{props['thermal_cost_gbp']/1e6:.2f}M</td></tr>
<tr><th>Cost/km²</th><td>£{props['cost_per_sq_km']:.2f}</td></tr>
</table>
<p><small>Data: December 2025</small></p>
]]>
"""
        ET.SubElement(placemark, 'description').text = description.strip()
        
        # Convert geometry (GeoJSON → KML coordinates)
        if geom['type'] == 'Polygon':
            polygon = ET.SubElement(placemark, 'Polygon')
            ET.SubElement(polygon, 'extrude').text = '1'
            ET.SubElement(polygon, 'altitudeMode').text = 'clampToGround'
            
            # Outer boundary
            outer_boundary = ET.SubElement(polygon, 'outerBoundaryIs')
            linear_ring = ET.SubElement(outer_boundary, 'LinearRing')
            
            # Convert coordinates: GeoJSON is [lng, lat], KML is "lng,lat,0"
            coords = geom['coordinates'][0]
            coord_str = ' '.join([f"{c[0]},{c[1]},0" for c in coords])
            ET.SubElement(linear_ring, 'coordinates').text = coord_str
            
        elif geom['type'] == 'MultiPolygon':
            multi_geometry = ET.SubElement(placemark, 'MultiGeometry')
            
            for poly_coords in geom['coordinates']:
                polygon = ET.SubElement(multi_geometry, 'Polygon')
                ET.SubElement(polygon, 'extrude').text = '1'
                ET.SubElement(polygon, 'altitudeMode').text = 'clampToGround'
                
                outer_boundary = ET.SubElement(polygon, 'outerBoundaryIs')
                linear_ring = ET.SubElement(outer_boundary, 'LinearRing')
                
                coords = poly_coords[0]
                coord_str = ' '.join([f"{c[0]},{c[1]},0" for c in coords])
                ET.SubElement(linear_ring, 'coordinates').text = coord_str
        
        features_processed += 1
    
    # Pretty print XML
    xml_str = ET.tostring(kml, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ')
    
    # Remove extra blank lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    # Save KML
    with open(kml_file, 'w') as f:
        f.write(pretty_xml)
    
    print(f'✅ KML created: {kml_file}')
    print(f'   Features: {features_processed} DNO regions')
    print(f'\n💡 Next steps:')
    print(f'   1. Go to: https://www.google.com/mymaps')
    print(f'   2. Create New Map')
    print(f'   3. Import → Upload {kml_file}')
    print(f'   4. Choose "area_name" as the feature label')

if __name__ == '__main__':
    geojson_to_kml('dno_boundaries.geojson', 'dno_boundaries.kml')
