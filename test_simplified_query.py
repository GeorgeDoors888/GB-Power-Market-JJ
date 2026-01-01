#!/usr/bin/env python3
"""Test if the simplified table queries work and are fast."""

from google.cloud import bigquery
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT_ID, location="US")

print("=" * 80)
print("TESTING SIMPLIFIED TABLE QUERIES")
print("=" * 80)

# Test DNO query (exactly as in map_sidebar.gs)
print("\n[1/2] Testing DNO query...")
dno_query = f"""
SELECT 
  dno_id,
  dno_full_name as dno_name,
  dno_code as dno_short_code,
  gsp_group as gsp_group_id,
  area_name as region_name,
  geojson_string as geometry_json
FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries_simplified`
"""

start = time.time()
try:
    result = client.query(dno_query).result()
    elapsed = time.time() - start
    
    rows = list(result)
    print(f"✅ DNO query successful")
    print(f"   Rows: {len(rows)}")
    print(f"   Time: {elapsed:.2f} seconds")
    
    if rows:
        # Check first row structure
        row = rows[0]
        print(f"   Sample row keys: {list(row.keys())}")
        print(f"   GeoJSON length: {len(row.geometry_json)} characters")
        print(f"   GeoJSON starts: {row.geometry_json[:100]}...")
        
except Exception as e:
    print(f"❌ DNO Error: {e}")

# Test GSP query
print("\n[2/2] Testing GSP query...")
gsp_query = f"""
SELECT 
  gsp_id,
  gsp_name,
  gsp_group,
  region_name,
  area_sqkm,
  geojson_string as geometry_json
FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries_simplified`
LIMIT 10
"""

start = time.time()
try:
    result = client.query(gsp_query).result()
    elapsed = time.time() - start
    
    rows = list(result)
    print(f"✅ GSP query successful")
    print(f"   Rows: {len(rows)}")
    print(f"   Time: {elapsed:.2f} seconds")
    
    if rows:
        row = rows[0]
        print(f"   Sample row keys: {list(row.keys())}")
        print(f"   GeoJSON length: {len(row.geometry_json)} characters")
        
except Exception as e:
    print(f"❌ GSP Error: {e}")

print("\n" + "=" * 80)
print("If both queries succeed in <5 seconds, the problem is NOT BigQuery.")
print("The issue must be in Apps Script's BigQuery service configuration.")
print("=" * 80)
