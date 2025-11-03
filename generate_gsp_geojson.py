#!/usr/bin/env python3
"""
Generate GeoJSON file for GSP zones from BigQuery
"""

import json
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "neso_gsp_boundaries"

def generate_gsp_geojson():
    """Query BigQuery and generate static GeoJSON file"""
    client = bigquery.Client(project=PROJECT_ID)
    
    print(f"🗄️  Fetching GSP boundaries from BigQuery...")
    
    query = f"""
    SELECT 
        gsp_id,
        gsp_name,
        gsp_group,
        region_name,
        ST_ASGEOJSON(boundary) as geojson,
        area_sqkm
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    ORDER BY gsp_id
    """
    
    results = client.query(query).result()
    
    # Build GeoJSON FeatureCollection
    features = []
    
    for row in results:
        # Parse the geometry
        geometry = json.loads(row.geojson)
        
        # Create feature
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "gsp_id": row.gsp_id,
                "gsp_name": row.gsp_name,
                "gsp_group": row.gsp_group or "",
                "region_name": row.region_name or "",
                "area_sqkm": round(row.area_sqkm, 1) if row.area_sqkm else 0
            }
        }
        
        features.append(feature)
    
    # Create FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Write to file
    output_file = "gsp_zones.geojson"
    with open(output_file, 'w') as f:
        json.dump(geojson, f)
    
    print(f"✅ Generated {output_file}")
    print(f"   Contains {len(features)} GSP zones")
    
    # Show summary
    print(f"\n📊 GSP Zones Summary:")
    print(f"   Total zones: {len(features)}")
    total_area = sum(f['properties']['area_sqkm'] for f in features)
    print(f"   Total area: {total_area:,.0f} km²")
    
    # Show first few
    print(f"\n📋 Sample GSP Zones:")
    for feature in features[:10]:
        props = feature['properties']
        print(f"   {props['gsp_id']:20s} | {props['gsp_name']:30s} | {props['area_sqkm']:>8,.0f} km²")

if __name__ == '__main__':
    generate_gsp_geojson()
