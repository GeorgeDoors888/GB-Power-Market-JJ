"""
Load OFFICIAL NESO DNO Boundaries with coordinate transformation
Converts from British National Grid (EPSG:27700) to WGS84 lat/long (EPSG:4326)
"""

from google.cloud import bigquery
from pyproj import Transformer
import json

# Create transformer from British National Grid to lat/long
transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

def transform_coordinates(coords):
    """Transform British National Grid coordinates to lat/long"""
    lon, lat = transformer.transform(coords[0], coords[1])
    return [lon, lat]

def transform_polygon(polygon_coords):
    """Transform a polygon's coordinates"""
    return [[transform_coordinates(coord) for coord in ring] for ring in polygon_coords]

def transform_multipolygon(multipolygon_coords):
    """Transform a multipolygon's coordinates"""
    return [transform_polygon(polygon) for polygon in multipolygon_coords]

client = bigquery.Client(project='inner-cinema-476211-u9')

# Load the GeoJSON
print("🗺️  Loading DNO boundaries from GeoJSON...")
with open('official_dno_boundaries.geojson', 'r') as f:
    geojson = json.load(f)

print(f"✅ Found {len(geojson['features'])} DNO license areas")
print("🔄 Converting from British National Grid (EPSG:27700) to WGS84 (EPSG:4326)...")

# Create table
create_table_sql = """
CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries` (
  dno_id INT64,
  gsp_group STRING,
  dno_code STRING,
  area_name STRING,
  dno_full_name STRING,
  boundary GEOGRAPHY
)
"""

client.query(create_table_sql).result()
print("✅ Created table")

# Transform and load each boundary
success_count = 0
for i, feature in enumerate(geojson['features']):
    props = feature['properties']
    geom = feature['geometry']
    
    # Transform coordinates
    transformed_geom = {'type': geom['type']}
    if geom['type'] == 'Polygon':
        transformed_geom['coordinates'] = transform_polygon(geom['coordinates'])
    elif geom['type'] == 'MultiPolygon':
        transformed_geom['coordinates'] = transform_multipolygon(geom['coordinates'])
    
    # Convert to GeoJSON string
    geom_json = json.dumps(transformed_geom)
    geom_json_escaped = geom_json.replace("'", "\\'")
    
    insert_sql = f"""
    INSERT INTO `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries` 
    (dno_id, gsp_group, dno_code, area_name, dno_full_name, boundary)
    VALUES (
      {props['ID']},
      '{props['Name']}',
      '{props['DNO']}',
      '{props['Area']}',
      '{props['DNO_Full']}',
      ST_GEOGFROMGEOJSON('{geom_json_escaped}')
    )
    """
    
    try:
        client.query(insert_sql).result()
        success_count += 1
        print(f"✅ {success_count:2d}/14: GSP {props['Name']:3s} | {props['DNO']:8s} | {props['Area']}")
    except Exception as e:
        print(f"❌ Failed to load {props['DNO']}: {e}")
        break

# Verify
print("\n📊 Verifying loaded boundaries...")
count_query = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`"
result = list(client.query(count_query).result())[0]

if result.count == 14:
    print(f"✅ SUCCESS! Loaded all {result.count} DNO boundaries")
    
    # Show summary
    query = """
    SELECT 
      gsp_group,
      dno_code,
      dno_full_name,
      area_name,
      ST_AREA(boundary) / 1000000 as area_km2
    FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`
    ORDER BY gsp_group
    """
    
    print("\n🗺️  DNO License Areas:")
    print("=" * 100)
    for row in client.query(query).result():
        print(f"GSP {row.gsp_group:3s} | {row.dno_code:8s} | {row.dno_full_name:35s} | {row.area_name:25s} | {row.area_km2:8,.0f} km²")
    
    print("\n✅ These are the REAL NESO DNO boundaries!")
    print("   Coordinate system: WGS84 (EPSG:4326) - standard lat/long")
    print("   Source: NESO official GIS data")
    print(f"   Table: inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries")
else:
    print(f"⚠️  Only loaded {result.count} of 14 boundaries")
