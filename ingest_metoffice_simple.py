#!/usr/bin/env python3
"""
Simple Met Office Marine Stations to BigQuery Ingestion
Uploads station metadata without complex distance calculations
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "metoffice_marine_stations"
CSV_FILE = "metoffice_marine_station_locations.csv"

print("="*80)
print("Met Office Marine Stations - Simple BigQuery Upload")
print("="*80)

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID, location="US")

# Load CSV
print(f"\n1. Loading data from {CSV_FILE}...")
df = pd.read_csv(CSV_FILE, dtype={'station_id': str})  # Force station_id as string
print(f"   Loaded {len(df)} stations")

# Add metadata columns
print("\n2. Adding metadata...")
df['data_source'] = 'Met Office UK Coastal Observations'
df['data_type'] = 'marine_weather_observations'
df['ingested_at'] = datetime.utcnow()

# Classify station types
def classify_station(name):
    name_lower = name.lower()
    if 'buoy' in name_lower:
        return 'ocean_buoy'
    elif 'light' in name_lower or 'lightship' in name_lower:
        return 'light_vessel'
    else:
        return 'coastal_station'

df['station_type'] = df['name_from_index'].apply(classify_station)

# Add region classification
def get_region(lat, lon):
    if lat >= 58:
        return 'Scotland_North'
    elif lat >= 55:
        return 'Scotland_South'
    elif lat >= 53:
        return 'North_England'
    elif lon < -4:
        return 'Irish_Sea_Wales'
    elif lat >= 51:
        return 'Central_England'
    else:
        return 'South_England'

df['region'] = df.apply(lambda r: get_region(r['latitude'], r['longitude']), axis=1)

# Rename columns for clarity
df = df.rename(columns={
    'name_from_index': 'station_name_short',
    'page_title': 'station_name_full'
})

print(f"   Station types: {df['station_type'].value_counts().to_dict()}")
print(f"   Regions: {df['region'].value_counts().to_dict()}")

# Define BigQuery schema
schema = [
    bigquery.SchemaField("station_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("station_name_short", "STRING"),
    bigquery.SchemaField("station_name_full", "STRING"),
    bigquery.SchemaField("latitude", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("longitude", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("url", "STRING"),
    bigquery.SchemaField("station_type", "STRING"),
    bigquery.SchemaField("region", "STRING"),
    bigquery.SchemaField("data_source", "STRING"),
    bigquery.SchemaField("data_type", "STRING"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
]

# Upload to BigQuery
print(f"\n3. Uploading to BigQuery...")
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition="WRITE_TRUNCATE",  # Replace table
)

job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()  # Wait for completion

print(f"   ✅ Uploaded {len(df)} rows to {table_id}")

# Verify upload
query = f"""
SELECT 
    COUNT(*) as total_stations,
    COUNT(DISTINCT station_type) as station_types,
    COUNT(DISTINCT region) as regions,
    COUNTIF(station_type = 'ocean_buoy') as buoys,
    COUNTIF(station_type = 'coastal_station') as coastal,
    COUNTIF(station_type = 'light_vessel') as light_vessels
FROM `{table_id}`
"""

print(f"\n4. Verification:")
result = client.query(query).to_dataframe()
print(result.to_string(index=False))

# Create view linking to wind farms (spatial join)
print(f"\n5. Creating spatial join view...")

view_sql = f"""
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.metoffice_stations_to_wind_farms` AS
WITH station_farm_distances AS (
  SELECT 
    s.station_id,
    s.station_name_short,
    s.station_type,
    s.latitude as station_lat,
    s.longitude as station_lon,
    w.name as wind_farm_name,
    w.latitude as farm_lat,
    w.longitude as farm_lon,
    w.capacity_mw,
    -- Haversine distance calculation (using ST_DISTANCE for simplicity)
    ST_DISTANCE(
      ST_GEOGPOINT(s.longitude, s.latitude),
      ST_GEOGPOINT(w.longitude, w.latitude)
    ) / 1000 as distance_km  -- Convert meters to km
  FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}` s
  CROSS JOIN `{PROJECT_ID}.{DATASET}.offshore_wind_farms` w
  WHERE w.latitude IS NOT NULL
    AND w.longitude IS NOT NULL
),
ranked_distances AS (
  SELECT 
    *,
    ROW_NUMBER() OVER (PARTITION BY station_id ORDER BY distance_km) as rank
  FROM station_farm_distances
  WHERE distance_km < 500  -- Only consider farms within 500km
)
SELECT 
  station_id,
  station_name_short,
  station_type,
  station_lat,
  station_lon,
  wind_farm_name,
  farm_lat,
  farm_lon,
  capacity_mw,
  ROUND(distance_km, 2) as distance_km,
  CASE 
    WHEN distance_km < 50 THEN 'adjacent'
    WHEN distance_km < 150 THEN 'near'
    WHEN distance_km < 300 THEN 'regional'
    ELSE 'distant'
  END as proximity_category,
  -- Estimate time lag for weather systems moving at 30 km/h
  ROUND(distance_km / 30, 1) as estimated_lag_hours
FROM ranked_distances
WHERE rank <= 5  -- Top 5 nearest farms per station
ORDER BY station_id, distance_km
"""

client.query(view_sql).result()
print(f"   ✅ Created view: metoffice_stations_to_wind_farms")

# Test the view
test_query = f"""
SELECT station_id, station_name_short, wind_farm_name, distance_km, proximity_category
FROM `{PROJECT_ID}.{DATASET}.metoffice_stations_to_wind_farms`
WHERE station_type = 'ocean_buoy'
ORDER BY distance_km
LIMIT 10
"""
print(f"\n6. Sample spatial joins (ocean buoys to nearest farms):")
sample = client.query(test_query).to_dataframe()
print(sample.to_string(index=False))

print("\n" + "="*80)
print("✅ INGESTION COMPLETE")
print("="*80)
print(f"\nTable created: {PROJECT_ID}.{DATASET}.{TABLE_NAME}")
print(f"View created: {PROJECT_ID}.{DATASET}.metoffice_stations_to_wind_farms")
print(f"\nQuery example:")
print(f"  SELECT * FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}` WHERE station_type = 'ocean_buoy'")
