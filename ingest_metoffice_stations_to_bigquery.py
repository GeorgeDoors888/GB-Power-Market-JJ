#!/usr/bin/env python3
"""
Ingest Met Office Marine Station Metadata to BigQuery

Creates comprehensive station reference table with:
- Station identifiers and names
- Geographic coordinates
- Station types (Buoy, Land, Light Vessel)
- Data source URLs
- Links to wind farms (spatial proximity)
- Links to weather data sources (ERA5, Open-Meteo, etc.)
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import numpy as np

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "metoffice_marine_stations"

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID, location="US")

print("=" * 80)
print("MET OFFICE MARINE STATIONS → BIGQUERY")
print("=" * 80)

# 1. Load CSV data
print("\n📊 Loading Met Office station data...")
df = pd.read_csv('metoffice_marine_station_locations.csv')

# 2. Clean and enhance data
print(f"   ✅ Loaded {len(df)} stations")

# Extract station type from name
df['station_type'] = df['name_from_index'].str.extract(r'‐\s*(.+)$')[0]
df['station_type'] = df['station_type'].fillna('Unknown')

# Clean station names (remove type suffix)
df['station_name_clean'] = df['name_from_index'].str.replace(r'\s*‐\s*.+$', '', regex=True)

# Add metadata
df['data_source'] = 'Met Office DataPoint API'
df['data_provider'] = 'UK Met Office'
df['ingestion_timestamp'] = datetime.utcnow()
df['is_active'] = True  # Assume all are active

# Add UK region classification
def classify_region(row):
    lat, lon = row['latitude'], row['longitude']
    
    # UK offshore wind regions
    if 50 <= lat <= 52 and -6 <= lon <= 2:
        return 'English Channel / Southwest Approaches'
    elif 52 <= lat <= 54 and -1 <= lon <= 2:
        return 'Southern North Sea'
    elif 54 <= lat <= 56 and -1 <= lon <= 2:
        return 'Central North Sea'
    elif 56 <= lat <= 59 and -4 <= lon <= 0:
        return 'Northern North Sea / Moray Firth'
    elif 53 <= lat <= 55 and -6 <= lon <= -3:
        return 'Irish Sea'
    elif 55 <= lat <= 61 and -8 <= lon <= -4:
        return 'Hebrides / West Scotland'
    elif lat < 50:
        return 'Bay of Biscay / Atlantic (South)'
    elif lon < -8:
        return 'Atlantic (West)'
    else:
        return 'Other'

df['uk_region'] = df.apply(classify_region, axis=1)

# 3. Calculate distances to nearest UK offshore wind farms
print("\n🗺️  Calculating proximity to wind farms...")

# Get wind farm coordinates from BigQuery
wind_farms_query = f"""
SELECT DISTINCT
    name as farm_name,
    latitude as farm_lat,
    longitude as farm_lon
FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
WHERE name IS NOT NULL
  AND latitude IS NOT NULL
  AND longitude IS NOT NULL
"""

try:
    wind_farms = client.query(wind_farms_query).to_dataframe()
    print(f"   Found {len(wind_farms)} wind farms in BigQuery")
    
    # Calculate distance to nearest wind farm using Haversine formula
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance in km between two lat/lon points"""
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
    
    # For each station, find nearest wind farm
    nearest_farms = []
    distances = []
    
    for _, station in df.iterrows():
        min_distance = float('inf')
        nearest_farm = None
        
        for _, farm in wind_farms.iterrows():
            dist = haversine_distance(
                station['latitude'], station['longitude'],
                farm['farm_lat'], farm['farm_lon']
            )
            
            if dist < min_distance:
                min_distance = dist
                nearest_farm = farm['farm_name']
        
        nearest_farms.append(nearest_farm)
        distances.append(min_distance)
    
    df['nearest_wind_farm'] = nearest_farms
    df['distance_to_nearest_farm_km'] = distances
    
    print(f"   ✅ Calculated distances to nearest wind farms")
    
except Exception as e:
    print(f"   ⚠️  Could not calculate wind farm distances: {e}")
    df['nearest_wind_farm'] = None
    df['distance_to_nearest_farm_km'] = None

# 4. Link to existing weather data sources
print("\n🌤️  Linking to weather data sources...")

# Check which stations are near existing ERA5/Open-Meteo data points
df['has_era5_nearby'] = False  # Will be populated by spatial join later
df['has_openmeteo_nearby'] = False

# Mark buoys as priority for data integration
df['priority_for_integration'] = df.apply(
    lambda x: 'HIGH' if x['station_type'] == 'Buoy' and x.get('distance_to_nearest_farm_km', 999) < 200
    else 'MEDIUM' if x['station_type'] in ['Buoy', 'Light Vessel']
    else 'LOW',
    axis=1
)

print(f"   HIGH priority stations: {(df['priority_for_integration'] == 'HIGH').sum()}")
print(f"   MEDIUM priority stations: {(df['priority_for_integration'] == 'MEDIUM').sum()}")
print(f"   LOW priority stations: {(df['priority_for_integration'] == 'LOW').sum()}")

# 5. Reorder columns for BigQuery
columns_ordered = [
    'station_id',
    'station_name_clean',
    'name_from_index',
    'page_title',
    'station_type',
    'latitude',
    'longitude',
    'uk_region',
    'nearest_wind_farm',
    'distance_to_nearest_farm_km',
    'data_source',
    'data_provider',
    'url',
    'has_era5_nearby',
    'has_openmeteo_nearby',
    'priority_for_integration',
    'is_active',
    'ingestion_timestamp'
]

df_upload = df[columns_ordered]

# 6. Create/replace BigQuery table
print(f"\n📤 Uploading to BigQuery...")
print(f"   Table: {PROJECT_ID}.{DATASET}.{TABLE_NAME}")

table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

# Define schema explicitly
schema = [
    bigquery.SchemaField("station_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("station_name_clean", "STRING"),
    bigquery.SchemaField("name_from_index", "STRING"),
    bigquery.SchemaField("page_title", "STRING"),
    bigquery.SchemaField("station_type", "STRING"),
    bigquery.SchemaField("latitude", "FLOAT64"),
    bigquery.SchemaField("longitude", "FLOAT64"),
    bigquery.SchemaField("uk_region", "STRING"),
    bigquery.SchemaField("nearest_wind_farm", "STRING"),
    bigquery.SchemaField("distance_to_nearest_farm_km", "FLOAT64"),
    bigquery.SchemaField("data_source", "STRING"),
    bigquery.SchemaField("data_provider", "STRING"),
    bigquery.SchemaField("url", "STRING"),
    bigquery.SchemaField("has_era5_nearby", "BOOLEAN"),
    bigquery.SchemaField("has_openmeteo_nearby", "BOOLEAN"),
    bigquery.SchemaField("priority_for_integration", "STRING"),
    bigquery.SchemaField("is_active", "BOOLEAN"),
    bigquery.SchemaField("ingestion_timestamp", "TIMESTAMP"),
]

job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)

job = client.load_table_from_dataframe(
    df_upload,
    table_id,
    job_config=job_config
)

job.result()  # Wait for completion

print(f"   ✅ Uploaded {len(df_upload)} stations")

# 7. Create spatial join view linking stations to wind farms
print(f"\n🔗 Creating spatial join view...")

view_sql = f"""
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.metoffice_stations_to_wind_farms` AS
WITH station_farm_pairs AS (
  SELECT
    s.station_id,
    s.station_name_clean,
    s.station_type,
    s.latitude as station_lat,
    s.longitude as station_lon,
    w.farm_name,
    w.latitude as farm_lat,
    w.longitude as farm_lon,
    -- Haversine distance calculation
    6371 * 2 * ASIN(SQRT(
      POW(SIN((RADIANS(w.latitude) - RADIANS(s.latitude)) / 2), 2) +
      COS(RADIANS(s.latitude)) * COS(RADIANS(w.latitude)) *
      POW(SIN((RADIANS(w.longitude) - RADIANS(s.longitude)) / 2), 2)
    )) AS distance_km
  FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}` s
  CROSS JOIN `{PROJECT_ID}.{DATASET}.wind_farm_coordinates` w
)
SELECT
  station_id,
  station_name_clean,
  station_type,
  station_lat,
  station_lon,
  farm_name,
  farm_lat,
  farm_lon,
  distance_km,
  -- Calculate lag time based on typical wind speeds (15 m/s avg)
  -- 1 degree longitude at 55°N ≈ 60 km, so distance/54 km/h ≈ hours
  CASE
    WHEN distance_km < 50 THEN ROUND(distance_km / 54, 1)
    WHEN distance_km < 100 THEN ROUND(distance_km / 54, 1)
    WHEN distance_km < 200 THEN ROUND(distance_km / 54, 1)
    ELSE ROUND(distance_km / 54, 1)
  END as estimated_lag_hours,
  -- Categorize proximity
  CASE
    WHEN distance_km < 50 THEN 'VERY_CLOSE'
    WHEN distance_km < 100 THEN 'CLOSE'
    WHEN distance_km < 200 THEN 'NEARBY'
    WHEN distance_km < 400 THEN 'MODERATE'
    ELSE 'FAR'
  END as proximity_category
FROM station_farm_pairs
WHERE distance_km < 500  -- Only show stations within 500km of wind farms
ORDER BY station_id, distance_km
"""

try:
    client.query(view_sql).result()
    print(f"   ✅ Created view: metoffice_stations_to_wind_farms")
except Exception as e:
    print(f"   ⚠️  View creation failed: {e}")

# 8. Create comprehensive data source registry view
print(f"\n📋 Creating data source registry...")

registry_sql = f"""
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.weather_data_source_registry` AS
WITH metoffice_stations AS (
  SELECT
    'Met Office Marine' as source_type,
    station_id as source_id,
    station_name_clean as source_name,
    latitude,
    longitude,
    station_type as data_type,
    uk_region,
    data_source as api_endpoint,
    TRUE as is_realtime,
    '30 minutes' as update_frequency,
    priority_for_integration,
    is_active
  FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
),

era5_grids AS (
  SELECT DISTINCT
    'ERA5 Reanalysis' as source_type,
    grid_point as source_id,
    grid_point as source_name,
    latitude,
    longitude,
    'Reanalysis Grid' as data_type,
    CASE
      WHEN latitude >= 50 AND latitude <= 61 AND longitude >= -8 AND longitude <= 3 THEN 'UK Waters'
      ELSE 'Extended Region'
    END as uk_region,
    'Copernicus CDS API' as api_endpoint,
    FALSE as is_realtime,
    '1 hour' as update_frequency,
    'HIGH' as priority_for_integration,
    TRUE as is_active
  FROM `{PROJECT_ID}.{DATASET}.era5_wind_upstream`
  LIMIT 1000
),

openmeteo_farms AS (
  SELECT DISTINCT
    'Open-Meteo Wind' as source_type,
    farm_name as source_id,
    farm_name as source_name,
    latitude,
    longitude,
    'Wind Farm Point' as data_type,
    'UK Offshore Wind' as uk_region,
    'Open-Meteo Archive API' as api_endpoint,
    TRUE as is_realtime,
    '1 hour' as update_frequency,
    'HIGH' as priority_for_integration,
    TRUE as is_active
  FROM `{PROJECT_ID}.{DATASET}.wind_farm_coordinates`
)

SELECT * FROM metoffice_stations
UNION ALL
SELECT * FROM era5_grids
UNION ALL
SELECT * FROM openmeteo_farms
ORDER BY source_type, source_name
"""

try:
    client.query(registry_sql).result()
    print(f"   ✅ Created view: weather_data_source_registry")
except Exception as e:
    print(f"   ⚠️  Registry view creation failed: {e}")

# 9. Generate summary statistics
print(f"\n📊 Summary Statistics:")

summary_query = f"""
SELECT
  station_type,
  COUNT(*) as station_count,
  COUNT(CASE WHEN priority_for_integration = 'HIGH' THEN 1 END) as high_priority,
  ROUND(AVG(distance_to_nearest_farm_km), 1) as avg_distance_km,
  MIN(distance_to_nearest_farm_km) as min_distance_km,
  MAX(distance_to_nearest_farm_km) as max_distance_km
FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
GROUP BY station_type
ORDER BY station_count DESC
"""

summary_df = client.query(summary_query).to_dataframe()
print("\n" + summary_df.to_string(index=False))

# 10. Show high-priority buoys near wind farms
print(f"\n🎯 High-Priority Buoys Near Wind Farms (< 200km):")

priority_query = f"""
SELECT
  station_name_clean,
  station_type,
  nearest_wind_farm,
  ROUND(distance_to_nearest_farm_km, 1) as distance_km,
  uk_region
FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
WHERE priority_for_integration = 'HIGH'
  AND distance_to_nearest_farm_km < 200
ORDER BY distance_to_nearest_farm_km
LIMIT 10
"""

priority_df = client.query(priority_query).to_dataframe()
if len(priority_df) > 0:
    print("\n" + priority_df.to_string(index=False))
else:
    print("   No high-priority stations found within 200km")

print("\n" + "=" * 80)
print("✅ MET OFFICE MARINE STATIONS INGESTION COMPLETE")
print("=" * 80)
print(f"\nTables/Views Created:")
print(f"  📊 {PROJECT_ID}.{DATASET}.{TABLE_NAME}")
print(f"  🔗 {PROJECT_ID}.{DATASET}.metoffice_stations_to_wind_farms")
print(f"  📋 {PROJECT_ID}.{DATASET}.weather_data_source_registry")
print(f"\nNext Steps:")
print(f"  1. Query stations: SELECT * FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`")
print(f"  2. View spatial links: SELECT * FROM `{PROJECT_ID}.{DATASET}.metoffice_stations_to_wind_farms`")
print(f"  3. Check data registry: SELECT * FROM `{PROJECT_ID}.{DATASET}.weather_data_source_registry`")
print(f"  4. Set up Met Office DataPoint API to download observations")
print("=" * 80)
