"""
Load OFFICIAL NESO DNO Boundaries using BigQuery SQL with ST_GEOGFROMGEOJSON
"""

from google.cloud import bigquery
import json

client = bigquery.Client(project='inner-cinema-476211-u9')

# Load the GeoJSON
with open('official_dno_boundaries.geojson', 'r') as f:
    geojson = json.load(f)

print(f"🗺️  Loading {len(geojson['features'])} DNO boundaries...")

# Create table with SQL
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

# Insert each record using ST_GEOGFROMGEOJSON
for i, feature in enumerate(geojson['features']):
    props = feature['properties']
    geom_json = json.dumps(feature['geometry'])
    
    # Escape single quotes in the JSON
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
        print(f"✅ Loaded {i+1}/{len(geojson['features'])}: {props['DNO']} - {props['Area']}")
    except Exception as e:
        print(f"❌ Failed to load {props['DNO']}: {e}")
        break

# Verify
count_query = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`"
result = list(client.query(count_query).result())[0]
print(f"\n✅ Successfully loaded {result.count} DNO boundaries!")

# Show them
query = """
SELECT 
  gsp_group,
  dno_code,
  dno_full_name,
  area_name
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`
ORDER BY gsp_group
"""

print("\n📊 DNO Boundaries:")
for row in client.query(query).result():
    print(f"GSP {row.gsp_group:3s} | {row.dno_code:8s} | {row.dno_full_name:35s} | {row.area_name}")
