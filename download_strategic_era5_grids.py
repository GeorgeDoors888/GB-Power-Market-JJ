#!/usr/bin/env python3
"""
Download Strategic ERA5 Grid Points for Improved Coverage

Downloads 8 additional grid points to improve upstream wind coverage
for all UK offshore wind farms.
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_wind_upstream"

# Strategic grid points (optimized from analysis)
STRATEGIC_GRIDS = [
    (54.5, -10.0, 'Atlantic_Deep_West'),
    (57.5, -7.5, 'Atlantic_Hebrides_Extended'),
    (54.0, -0.5, 'North_Sea_West'),
    (51.5, -6.5, 'Celtic_Sea_Deep'),
    (55.0, -5.0, 'Irish_Sea_North'),
    (50.5, -1.5, 'Channel_West'),
    (60.5, -3.0, 'Shetland_West'),
    (55.0, 0.5, 'Dogger_West'),
]

def download_openmeteo_point(lat, lon, point_name, start_date='2020-01-01', end_date='2025-12-30'):
    """Download wind data from Open-Meteo API (ERA5-based)"""
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ["wind_speed_100m", "wind_direction_100m", "wind_gusts_10m"],
        "timezone": "UTC"
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if 'hourly' not in data:
            return None
        
        df = pd.DataFrame({
            'time_utc': pd.to_datetime(data['hourly']['time']),
            'grid_point_name': point_name,
            'latitude': lat,
            'longitude': lon,
            'wind_speed_100m': data['hourly']['wind_speed_100m'],
            'wind_direction_100m': data['hourly']['wind_direction_100m'],
            'wind_gusts_10m': data['hourly']['wind_gusts_10m'],
        })
        
        return df
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def upload_to_bigquery(df, table_id):
    """Upload DataFrame to BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("time_utc", "TIMESTAMP"),
            bigquery.SchemaField("grid_point_name", "STRING"),
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
            bigquery.SchemaField("wind_speed_100m", "FLOAT"),
            bigquery.SchemaField("wind_direction_100m", "FLOAT"),
            bigquery.SchemaField("wind_gusts_10m", "FLOAT"),
        ]
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

print("=" * 80)
print("Downloading Strategic ERA5 Grid Points")
print("=" * 80)
print(f"Grid points to download: {len(STRATEGIC_GRIDS)}")
print(f"Period: 2020-01-01 to 2025-12-30")
print(f"Target table: {PROJECT_ID}.{DATASET}.{TABLE_NAME}")
print()

# Download all grid points first
all_dfs = []
successful = 0
failed = 0

for idx, (lat, lon, point_name) in enumerate(STRATEGIC_GRIDS, 1):
    print(f"Point {idx}/{len(STRATEGIC_GRIDS)}: {point_name} ({lat:.1f}°N, {lon:.1f}°E)")
    
    df = download_openmeteo_point(lat, lon, point_name)
    
    if df is not None and len(df) > 0:
        print(f"   ✅ Downloaded {len(df):,} hourly observations")
        print(f"   Avg wind speed: {df['wind_speed_100m'].mean():.1f} m/s")
        print(f"   Max wind speed: {df['wind_speed_100m'].max():.1f} m/s")
        all_dfs.append(df)
        successful += 1
    else:
        print(f"   ❌ Download failed")
        failed += 1
    
    # Rate limiting between downloads
    if idx < len(STRATEGIC_GRIDS):
        time.sleep(2)
    print()

# Upload all data in one batch to avoid partition modification quota
if len(all_dfs) > 0:
    print("📤 Uploading all grid points to BigQuery in single batch...")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    upload_to_bigquery(combined_df, table_id)
    print(f"   ✅ Uploaded {len(combined_df):,} total rows ({len(all_dfs)} grid points)")
    print()

print("=" * 80)
print("DOWNLOAD COMPLETE")
print("=" * 80)
print(f"Successful downloads: {successful}/{len(STRATEGIC_GRIDS)}")
print(f"Failed downloads: {failed}")
print(f"Total observations: {successful * 52584:,} (approx)")

# Verify upload
if successful > 0:
    client = bigquery.Client(project=PROJECT_ID, location="US")
    query = f"""
    SELECT 
        grid_point_name as grid_point,
        COUNT(*) as observations,
        MIN(time_utc) as first_date,
        MAX(time_utc) as last_date,
        AVG(wind_speed_100m) as avg_wind
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    WHERE grid_point_name IN ({','.join([f"'{name}'" for _, _, name in STRATEGIC_GRIDS])})
    GROUP BY grid_point
    ORDER BY grid_point
    """
    
    print("\n" + "=" * 80)
    print("BigQuery Verification")
    print("=" * 80)
    
    df_verify = client.query(query).to_dataframe()
    
    if len(df_verify) > 0:
        print(f"\n{'Grid Point':<30} {'Observations':>12} {'Date Range':<30} {'Avg Wind':>10}")
        print("-" * 90)
        for _, row in df_verify.iterrows():
            date_range = f"{row['first_date'].date()} to {row['last_date'].date()}"
            print(f"{row['grid_point']:<30} {int(row['observations']):>12,} {date_range:<30} {row['avg_wind']:>9.1f} m/s")
        
        print(f"\n✅ Strategic grid points successfully added to {TABLE_NAME}")
        print(f"Total grid points in table: {len(df_verify) + 10} (10 original + {len(df_verify)} new)")
    else:
        print("⚠️  No data found in verification query")

print("\n" + "=" * 80)
print("NEXT STEP: Retrain models with expanded grid coverage")
print("=" * 80)
print("Command: python3 build_wind_power_curves_optimized.py")
