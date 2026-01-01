#!/usr/bin/env python3
"""
Ingest CMEMS Wave NetCDF files to BigQuery
Uploads UK wave grid data to uk_energy_prod.cmems_waves_uk_grid
"""

import os
import glob
from datetime import datetime
import pandas as pd
import xarray as xr
from google.cloud import bigquery

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "cmems_waves_uk_grid"
WAVES_DIR = "cmems_waves_uk"

print("="*80)
print("CMEMS WAVES TO BIGQUERY INGESTION")
print("="*80)

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID, location="US")
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

# Find all NetCDF files
nc_files = sorted(glob.glob(os.path.join(WAVES_DIR, "*.nc")))
if not nc_files:
    print(f"❌ No NetCDF files found in {WAVES_DIR}")
    print("   Run download_cmems_waves_uk.py first")
    exit(1)

print(f"\n✅ Found {len(nc_files)} NetCDF files")
for f in nc_files:
    size_mb = os.path.getsize(f) / (1024**2)
    print(f"   {os.path.basename(f)}: {size_mb:.1f} MB")

# Load and process NetCDF files
print("\nLoading wave data...")
all_dfs = []

for i, nc_file in enumerate(nc_files, 1):
    print(f"\n[{i}/{len(nc_files)}] Processing {os.path.basename(nc_file)}...")
    
    ds = xr.open_dataset(nc_file)
    print(f"  Variables: {list(ds.data_vars)}")
    print(f"  Dimensions: {dict(ds.dims)}")
    
    # Convert to DataFrame (flatten grid)
    df = ds.to_dataframe().reset_index()
    
    # Add metadata
    df['source_file'] = os.path.basename(nc_file)
    
    all_dfs.append(df)
    ds.close()
    
    print(f"  Rows extracted: {len(df):,}")

# Combine all dataframes
df_combined = pd.concat(all_dfs, ignore_index=True)
print(f"\n✅ Total rows: {len(df_combined):,}")

# Add ingestion timestamp
df_combined['ingested_at'] = datetime.utcnow()

# Rename columns to match BigQuery naming conventions
rename_map = {
    'time': 'time',
    'latitude': 'latitude',
    'longitude': 'longitude',
}
# Keep all variable columns as-is (VHM0, VTPK, etc.)
df_combined = df_combined.rename(columns=rename_map)

# Build dynamic schema based on actual columns
schema_fields = [
    bigquery.SchemaField("time", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("latitude", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("longitude", "FLOAT64", mode="REQUIRED"),
]

# Add wave variable columns dynamically
wave_vars = [col for col in df_combined.columns 
             if col not in ['time', 'latitude', 'longitude', 'source_file', 'ingested_at']]

for var in wave_vars:
    schema_fields.append(
        bigquery.SchemaField(var, "FLOAT64", description=f"Wave parameter: {var}")
    )

# Add metadata columns
schema_fields.extend([
    bigquery.SchemaField("source_file", "STRING"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
])

print(f"\nSchema: {len(schema_fields)} columns")
print(f"  Wave variables: {wave_vars}")

# Upload to BigQuery
print(f"\nUploading to BigQuery: {table_id}")
print(f"  Rows: {len(df_combined):,}")
print(f"  Estimated size: ~{len(df_combined) * len(schema_fields) * 8 / 1024 / 1024:.1f} MB")

job_config = bigquery.LoadJobConfig(
    schema=schema_fields,
    write_disposition="WRITE_TRUNCATE",  # Replace existing data
)

job = client.load_table_from_dataframe(df_combined, table_id, job_config=job_config)
job.result()  # Wait for completion

print("✅ Upload complete!")

# Verify and show statistics
print("\nVerification Query:")
query = f"""
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT DATE(time)) as unique_dates,
    MIN(time) as earliest_time,
    MAX(time) as latest_time,
    ROUND(MIN(latitude), 2) as min_lat,
    ROUND(MAX(latitude), 2) as max_lat,
    ROUND(MIN(longitude), 2) as min_lon,
    ROUND(MAX(longitude), 2) as max_lon
FROM `{table_id}`
"""

result = client.query(query).to_dataframe()
print(result.to_string(index=False))

# Wave statistics if VHM0 exists
if 'VHM0' in wave_vars:
    wave_stats_query = f"""
    SELECT 
        ROUND(AVG(VHM0), 2) as avg_sig_wave_height_m,
        ROUND(MIN(VHM0), 2) as min_sig_wave_height_m,
        ROUND(MAX(VHM0), 2) as max_sig_wave_height_m,
        COUNTIF(VHM0 > 10) as extreme_waves_over_10m
    FROM `{table_id}`
    WHERE VHM0 IS NOT NULL
    """
    wave_result = client.query(wave_stats_query).to_dataframe()
    print("\nWave Statistics:")
    print(wave_result.to_string(index=False))

print("\n" + "="*80)
print("✅ CMEMS WAVE INGESTION COMPLETE")
print("="*80)
print(f"\nTable: {table_id}")
print(f"Query example:")
print(f"  SELECT time, latitude, longitude, VHM0, VTPK")
print(f"  FROM `{table_id}`")
print(f"  WHERE latitude BETWEEN 50 AND 55")
print(f"    AND longitude BETWEEN -5 AND 2")
print(f"    AND DATE(time) = '2025-01-01'")
print(f"  ORDER BY time, latitude, longitude")
