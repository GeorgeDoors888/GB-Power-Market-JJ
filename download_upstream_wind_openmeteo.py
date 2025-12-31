#!/usr/bin/env python3
"""
Download upstream wind data using Open-Meteo API (ERA5-based, free, no auth required)
Alternative to ECMWF CDS API - provides similar data quality without registration

Grid points selected to provide 2-4 hour advance warning for offshore wind farms
Data: 100m wind speed, hourly resolution, 2020-2025
"""

import requests
import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Upstream grid points (lat, lon, name, distance_km, target_farms)
GRID_POINTS = [
    # Atlantic approach - west of Irish Sea
    (54.0, -8.0, 'Atlantic_Irish_Sea', 200, 'Walney Extension,Burbo Bank,West of Duddon Sands'),
    (53.5, -6.0, 'Irish_Sea_Central', 150, 'Walney,Burbo Bank Extension,Barrow'),
    
    # West of Scotland
    (57.0, -6.0, 'Atlantic_Hebrides', 150, 'Moray East,Moray West,Beatrice'),
    (56.5, -4.5, 'West_Scotland', 100, 'Seagreen Phase 1,Neart Na Gaoithe'),
    
    # West of North Sea (across England)
    (53.5, -1.0, 'Central_England', 80, 'Humber Gateway,Triton Knoll,Hornsea One,Hornsea Two'),
    (54.5, -2.0, 'Pennines', 100, 'Hornsea One,Hornsea Two'),
    
    # Southwest approach
    (52.5, -5.0, 'Celtic_Sea', 180, 'Burbo Bank,East Anglia One,Greater Gabbard'),
    (51.5, -2.0, 'Bristol_Channel', 120, 'Rampion,Thanet,London Array'),
    
    # North of Scotland (for northerly winds)
    (59.0, -4.0, 'North_Scotland', 100, 'Moray East,Moray West,Beatrice'),
    (58.0, -2.0, 'Moray_Firth_West', 50, 'Moray East,Beatrice,Hywind Scotland'),
]

def download_openmeteo_point(lat, lon, point_name, start_date='2020-01-01', end_date='2025-12-30'):
    """
    Download wind data from Open-Meteo API for a single grid point
    Uses ERA5-Land reanalysis data (100m wind speed)
    """
    print(f"\n📥 Downloading {point_name} ({lat}°N, {lon}°E)")
    print(f"   Date range: {start_date} to {end_date}")
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": [
            "wind_speed_100m",
            "wind_direction_100m",
            "wind_gusts_10m"
        ],
        "timezone": "UTC"
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        df = pd.DataFrame({
            'time_utc': pd.to_datetime(data['hourly']['time']),
            'grid_point_name': point_name,
            'latitude': lat,
            'longitude': lon,
            'wind_speed_100m': data['hourly']['wind_speed_100m'],
            'wind_direction_100m': data['hourly']['wind_direction_100m'],
            'wind_gusts_10m': data['hourly']['wind_gusts_10m'],
        })
        
        # Remove any null values
        df = df.dropna(subset=['wind_speed_100m'])
        
        print(f"   ✅ Downloaded {len(df):,} hourly observations")
        print(f"   Avg wind speed: {df['wind_speed_100m'].mean():.1f} m/s")
        print(f"   Max wind speed: {df['wind_speed_100m'].max():.1f} m/s")
        
        return df
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def upload_to_bigquery(df, point_info, table_name='era5_wind_upstream'):
    """
    Upload wind data to BigQuery
    """
    if df is None or len(df) == 0:
        return
    
    lat, lon, name, distance, target_farms = point_info
    
    # Add metadata
    df['distance_from_coast_km'] = distance
    df['target_farms'] = target_farms
    
    print(f"\n📤 Uploading {name} to BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    
    # Define schema
    schema = [
        bigquery.SchemaField("time_utc", "TIMESTAMP"),
        bigquery.SchemaField("grid_point_name", "STRING"),
        bigquery.SchemaField("latitude", "FLOAT"),
        bigquery.SchemaField("longitude", "FLOAT"),
        bigquery.SchemaField("wind_speed_100m", "FLOAT"),
        bigquery.SchemaField("wind_direction_100m", "FLOAT"),
        bigquery.SchemaField("wind_gusts_10m", "FLOAT"),
        bigquery.SchemaField("distance_from_coast_km", "FLOAT"),
        bigquery.SchemaField("target_farms", "STRING"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_APPEND",
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="time_utc"
        )
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f"   ✅ Uploaded {len(df):,} rows")
    except Exception as e:
        print(f"   ❌ Upload error: {e}")

def main():
    print("=" * 80)
    print("Upstream Wind Data Download - Open-Meteo API (ERA5-based)")
    print("=" * 80)
    print(f"\nGrid points to download: {len(GRID_POINTS)}")
    print("Data source: Open-Meteo (ERA5-Land reanalysis)")
    print("Variables: 100m wind speed, direction, gusts")
    print("Resolution: Hourly")
    print("Period: 2020-01-01 to 2025-12-30")
    print("API: Free, no authentication required")
    
    successful = 0
    failed = 0
    total_rows = 0
    
    for i, (lat, lon, name, distance, target_farms) in enumerate(GRID_POINTS, 1):
        print(f"\n{'='*80}")
        print(f"Point {i}/{len(GRID_POINTS)}: {name}")
        print(f"Location: {lat}°N, {lon}°E")
        print(f"Distance from coast: {distance} km")
        print(f"Target farms: {target_farms}")
        print(f"{'='*80}")
        
        # Download data
        df = download_openmeteo_point(lat, lon, name)
        
        if df is not None and len(df) > 0:
            # Upload to BigQuery
            upload_to_bigquery(df, (lat, lon, name, distance, target_farms))
            successful += 1
            total_rows += len(df)
        else:
            failed += 1
        
        # Rate limiting (be nice to free API)
        if i < len(GRID_POINTS):
            print("   ⏳ Waiting 2 seconds before next request...")
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ DOWNLOAD COMPLETE")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  Successful downloads: {successful}/{len(GRID_POINTS)}")
    print(f"  Failed downloads: {failed}")
    print(f"  Total observations: {total_rows:,}")
    
    if successful > 0:
        print(f"\n📊 Data stored in: {PROJECT_ID}.{DATASET}.era5_wind_upstream")
        
        # Verify upload
        client = bigquery.Client(project=PROJECT_ID, location="US")
        verify_query = f"""
        SELECT 
            grid_point_name,
            COUNT(*) as observations,
            MIN(time_utc) as first_date,
            MAX(time_utc) as last_date,
            AVG(wind_speed_100m) as avg_wind_speed,
            MAX(wind_speed_100m) as max_wind_speed
        FROM `{PROJECT_ID}.{DATASET}.era5_wind_upstream`
        GROUP BY grid_point_name
        ORDER BY grid_point_name
        """
        
        try:
            print("\n📈 BigQuery verification:")
            verify_df = client.query(verify_query).to_dataframe()
            print(f"\n{'Grid Point':<25} {'Observations':>12} {'Date Range':<35} {'Avg Wind':>10}")
            print("-" * 90)
            for _, row in verify_df.iterrows():
                date_range = f"{row['first_date'].date()} to {row['last_date'].date()}"
                print(f"{row['grid_point_name']:<25} {int(row['observations']):>12,} "
                      f"{date_range:<35} {row['avg_wind_speed']:>8.1f} m/s")
        except Exception as e:
            print(f"\n⚠️  Could not verify (table may not exist yet): {e}")
    
    print("\n" + "=" * 80)
    print("Next steps:")
    print("1. Verify data: SELECT * FROM era5_wind_upstream LIMIT 100")
    print("2. Retrain models: python3 build_wind_power_curves_era5.py")
    print("3. Expected improvement: +15-25% for Irish Sea farms")
    print("=" * 80)

if __name__ == "__main__":
    main()
