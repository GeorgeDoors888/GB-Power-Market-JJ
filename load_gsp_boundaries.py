#!/usr/bin/env python3
"""
Load GSP (Grid Supply Point) boundaries to BigQuery
Transforms coordinates from British National Grid (EPSG:27700) to WGS84 (EPSG:4326)
"""

import json
from google.cloud import bigquery
from pyproj import Transformer
import sys

# BigQuery configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "neso_gsp_boundaries"

# GSP GeoJSON file path
GSP_GEOJSON_PATH = "/Users/georgemajor/Jibber Jabber ChatGPT/gis-boundaries-for-gb-grid-supply-points_08534dae-5408-4e31-8639-b579c8f1c50b_20220505_160129.461187.geojson"

# Create transformer from British National Grid to WGS84
transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

def transform_coordinates(coords):
    """Transform a single coordinate pair from BNG to WGS84"""
    lon, lat = transformer.transform(coords[0], coords[1])
    return [lon, lat]

def transform_polygon(polygon_coords):
    """Transform all coordinates in a polygon"""
    return [[transform_coordinates(coord) for coord in ring] for ring in polygon_coords]

def transform_multipolygon(multipolygon_coords):
    """Transform all polygons in a MultiPolygon"""
    return [transform_polygon(polygon) for polygon in multipolygon_coords]

def load_gsp_geojson():
    """Load and parse the GSP GeoJSON file"""
    print(f"🗺️  Loading GSP boundaries from GeoJSON...")
    
    with open(GSP_GEOJSON_PATH, 'r') as f:
        data = json.load(f)
    
    features = data['features']
    print(f"✅ Found {len(features)} GSP zones")
    
    return features

def create_bigquery_table():
    """Create BigQuery table for GSP boundaries"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Define schema
    schema = [
        bigquery.SchemaField("gsp_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gsp_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gsp_group", "STRING"),
        bigquery.SchemaField("region_name", "STRING"),
        bigquery.SchemaField("boundary", "GEOGRAPHY", mode="REQUIRED"),
        bigquery.SchemaField("area_sqkm", "FLOAT64"),
    ]
    
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    table = bigquery.Table(table_ref, schema=schema)
    
    try:
        client.delete_table(table_ref)
        print(f"🗑️  Deleted existing table")
    except:
        pass
    
    table = client.create_table(table)
    print(f"✅ Created table: {table_ref}")
    
    return client

def load_gsp_to_bigquery(features):
    """Transform coordinates and load GSP features to BigQuery"""
    client = create_bigquery_table()
    
    print(f"\n🔄 Converting from British National Grid (EPSG:27700) to WGS84 (EPSG:4326)...")
    
    rows_to_insert = []
    
    for i, feature in enumerate(features, 1):
        properties = feature['properties']
        geometry = feature['geometry']
        
        # Extract properties
        gsp_id = properties.get('gsp_id', properties.get('GSP_ID', properties.get('ID', f'GSP_{i}')))
        gsp_name = properties.get('gsp_name', properties.get('GSP_Name', properties.get('Name', f'GSP {i}')))
        gsp_group = properties.get('gsp_group', properties.get('GSP_Group', ''))
        region_name = properties.get('region_name', properties.get('Region', ''))
        
        # Transform coordinates
        if geometry['type'] == 'Polygon':
            transformed_coords = transform_polygon(geometry['coordinates'])
            geojson_str = json.dumps({
                'type': 'Polygon',
                'coordinates': transformed_coords
            })
        elif geometry['type'] == 'MultiPolygon':
            transformed_coords = transform_multipolygon(geometry['coordinates'])
            geojson_str = json.dumps({
                'type': 'MultiPolygon',
                'coordinates': transformed_coords
            })
        else:
            print(f"⚠️  Skipping unsupported geometry type: {geometry['type']}")
            continue
        
        # Calculate area (approximate)
        # BigQuery will calculate the actual area
        
        # Insert using raw query
        query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` 
        (gsp_id, gsp_name, gsp_group, region_name, boundary, area_sqkm)
        VALUES (
            @gsp_id,
            @gsp_name,
            @gsp_group,
            @region_name,
            ST_GEOGFROMGEOJSON(@geojson),
            ST_AREA(ST_GEOGFROMGEOJSON(@geojson)) / 1000000
        )
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("gsp_id", "STRING", str(gsp_id)),
                bigquery.ScalarQueryParameter("gsp_name", "STRING", str(gsp_name)),
                bigquery.ScalarQueryParameter("gsp_group", "STRING", str(gsp_group)),
                bigquery.ScalarQueryParameter("region_name", "STRING", str(region_name)),
                bigquery.ScalarQueryParameter("geojson", "STRING", geojson_str),
            ]
        )
        
        try:
            client.query(query, job_config=job_config).result()
            print(f"✅ {i:3d}/{len(features)}: {gsp_name:40s} | {gsp_group:10s}")
        except Exception as e:
            print(f"❌ Failed to load {gsp_name}: {e}")
            continue
    
    print(f"\n📊 Verifying loaded GSP boundaries...")
    
    # Verify
    query = f"""
    SELECT 
        gsp_id,
        gsp_name,
        gsp_group,
        region_name,
        ROUND(area_sqkm, 0) as area_km2
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    ORDER BY gsp_name
    """
    
    results = client.query(query).result()
    
    print(f"\n✅ SUCCESS! Loaded GSP boundaries to BigQuery")
    print(f"\n🗺️  GSP Zones:")
    print(f"{'GSP ID':20s} | {'GSP Name':40s} | {'Group':10s} | {'Area (km²)':>12s}")
    print("-" * 90)
    
    for row in results:
        print(f"{row.gsp_id:20s} | {row.gsp_name:40s} | {row.gsp_group:10s} | {row.area_km2:>12,.0f}")

if __name__ == '__main__':
    try:
        features = load_gsp_geojson()
        load_gsp_to_bigquery(features)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
