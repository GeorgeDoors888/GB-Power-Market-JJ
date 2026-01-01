#!/usr/bin/env python3
"""
Create ultra-simplified boundary tables for fast Apps Script loading.
This pre-computes simplified geometries to avoid timeout issues.
"""

from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT_ID, location="US")

print("=" * 80)
print("CREATING SIMPLIFIED BOUNDARY TABLES FOR APPS SCRIPT")
print("=" * 80)

# DNO simplified table (10km tolerance - very coarse but fast)
print("\n[1/2] Creating simplified DNO boundaries...")
dno_query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.neso_dno_boundaries_simplified` AS
SELECT 
  dno_id,
  dno_full_name,
  dno_code,
  gsp_group,
  area_name,
  -- Ultra-simplified for Apps Script (10km tolerance)
  ST_SIMPLIFY(boundary, 10000) as boundary_simplified,
  -- Pre-compute GeoJSON string to avoid serialization time
  ST_AsGeoJSON(ST_SIMPLIFY(boundary, 10000)) as geojson_string
FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
WHERE boundary IS NOT NULL
"""

try:
    job = client.query(dno_query)
    job.result()
    print("✅ DNO simplified table created")
    
    # Count rows
    count = client.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries_simplified`").result()
    for row in count:
        print(f"   Rows: {row.cnt}")
        
except Exception as e:
    print(f"❌ DNO Error: {e}")

# GSP simplified table (5km tolerance)
print("\n[2/2] Creating simplified GSP boundaries...")
gsp_query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries_simplified` AS
SELECT 
  gsp_id,
  gsp_name,
  gsp_group,
  region_name,
  area_sqkm,
  -- Moderately simplified for Apps Script (5km tolerance)
  ST_SIMPLIFY(boundary, 5000) as boundary_simplified,
  -- Pre-compute GeoJSON string
  ST_AsGeoJSON(ST_SIMPLIFY(boundary, 5000)) as geojson_string
FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries`
WHERE boundary IS NOT NULL
"""

try:
    job = client.query(gsp_query)
    job.result()
    print("✅ GSP simplified table created")
    
    # Count rows
    count = client.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries_simplified`").result()
    for row in count:
        print(f"   Rows: {row.cnt}")
        
except Exception as e:
    print(f"❌ GSP Error: {e}")

print("\n" + "=" * 80)
print("✅ SIMPLIFIED TABLES CREATED")
print("=" * 80)
print("\nNow update map_sidebar.gs to query these tables:")
print("  - neso_dno_boundaries_simplified (geojson_string column)")
print("  - neso_gsp_boundaries_simplified (geojson_string column)")
print("\nThis should be MUCH faster (pre-computed GeoJSON strings)!")
