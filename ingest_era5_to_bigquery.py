#!/usr/bin/env python3
"""
Ingest ERA5 Parquet files to BigQuery
Uploads all downloaded ERA5 turbine point data to uk_energy_prod.era5_turbine_hourly
"""

import os
import glob
from datetime import datetime
import pandas as pd
from google.cloud import bigquery

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_turbine_hourly"
ERA5_DIR = "era5_points"

print("="*80)
print("ERA5 TO BIGQUERY INGESTION")
print("="*80)

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID, location="US")
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

# Find all parquet files
parquet_files = sorted(glob.glob(os.path.join(ERA5_DIR, "*.parquet")))
if not parquet_files:
    print(f"❌ No parquet files found in {ERA5_DIR}")
    print("   Run download_era5_turbine_points.py first")
    exit(1)

print(f"\n✅ Found {len(parquet_files)} parquet files")
print(f"   Expected: 246 files (41 turbines × 6 years)")

# Load and combine all parquet files
print("\nLoading data...")
dfs = []
for i, pq_file in enumerate(parquet_files, 1):
    if i % 50 == 0 or i == len(parquet_files):
        print(f"  Loading file {i}/{len(parquet_files)}...")
    df = pd.read_parquet(pq_file)
    dfs.append(df)

df_combined = pd.concat(dfs, ignore_index=True)
print(f"✅ Loaded {len(df_combined):,} rows")

# Add derived columns
print("\nAdding derived columns...")
df_combined['t2m_c'] = df_combined['t2m_k'] - 273.15  # Kelvin to Celsius
df_combined['ingested_at'] = datetime.utcnow()

# Get turbine locations from turbines.csv
turbines = pd.read_csv('turbines.csv')
turbine_coords = turbines[['id', 'latitude', 'longitude']].rename(columns={'id': 'turbine_id'})
df_combined = df_combined.merge(turbine_coords, on='turbine_id', how='left')

# Reorder columns
column_order = [
    'turbine_id',
    'time',
    'latitude',
    'longitude',
    'u100',
    'v100',
    't2m_k',
    't2m_c',
    'd2m_k',
    'wind_speed_100m',
    'wind_dir_from_deg',
    'rh_2m_pct',
    'ingested_at'
]
df_final = df_combined[column_order]

# Define BigQuery schema
schema = [
    bigquery.SchemaField("turbine_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("time", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("latitude", "FLOAT64"),
    bigquery.SchemaField("longitude", "FLOAT64"),
    bigquery.SchemaField("u100", "FLOAT64", description="U-component wind at 100m (m/s)"),
    bigquery.SchemaField("v100", "FLOAT64", description="V-component wind at 100m (m/s)"),
    bigquery.SchemaField("t2m_k", "FLOAT64", description="2m temperature (Kelvin)"),
    bigquery.SchemaField("t2m_c", "FLOAT64", description="2m temperature (Celsius)"),
    bigquery.SchemaField("d2m_k", "FLOAT64", description="2m dewpoint temperature (Kelvin)"),
    bigquery.SchemaField("wind_speed_100m", "FLOAT64", description="Wind speed at hub height (m/s)"),
    bigquery.SchemaField("wind_dir_from_deg", "FLOAT64", description="Wind direction from (degrees, 0=N)"),
    bigquery.SchemaField("rh_2m_pct", "FLOAT64", description="Relative humidity (%)"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
]

# Upload to BigQuery
print(f"\nUploading to BigQuery: {table_id}")
print(f"  Rows: {len(df_final):,}")
print(f"  Size: ~{len(df_final) * 13 * 8 / 1024 / 1024:.1f} MB")

job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition="WRITE_TRUNCATE",  # Replace existing data
)

job = client.load_table_from_dataframe(df_final, table_id, job_config=job_config)
job.result()  # Wait for completion

print("✅ Upload complete!")

# Verify and show statistics
print("\nVerification Query:")
query = f"""
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT turbine_id) as turbines,
    MIN(time) as earliest_date,
    MAX(time) as latest_date,
    ROUND(AVG(wind_speed_100m), 2) as avg_wind_speed_ms,
    ROUND(AVG(t2m_c), 2) as avg_temp_c,
    ROUND(AVG(rh_2m_pct), 2) as avg_humidity_pct
FROM `{table_id}`
"""

result = client.query(query).to_dataframe()
print(result.to_string(index=False))

print("\n" + "="*80)
print("✅ ERA5 INGESTION COMPLETE")
print("="*80)
print(f"\nTable: {table_id}")
print(f"Query example:")
print(f"  SELECT turbine_id, time, wind_speed_100m, t2m_c")
print(f"  FROM `{table_id}`")
print(f"  WHERE turbine_id = 'Hornsea One'")
print(f"    AND DATE(time) = '2025-01-01'")
print(f"  ORDER BY time")
