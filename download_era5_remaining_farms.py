#!/usr/bin/env python3
"""
Download ERA5 Weather Data for Remaining 27 Offshore Wind Farms

This script downloads weather data for farms that failed due to Open-Meteo rate limits.
Uses longer delays and retry logic.

Run via cron: 0 3 * * * /usr/bin/python3 /path/to/download_era5_remaining_farms.py
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import time
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_weather_data"
API_URL = "https://archive-api.open-meteo.com/v1/archive"

START_DATE = "2020-01-01"
END_DATE = "2025-11-30"

# Farms that already have data (skip these)
COMPLETED_FARMS = [
    'Barrow', 'Beatrice', 'Beatrice extension', 'Burbo Bank', 'Burbo Bank Extension',
    'Dudgeon', 'East Anglia One', 'European Offshore Wind Deployment Centre',
    # Add more as they complete
]

def get_remaining_farms():
    """Get farms that don't have weather data yet."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get all farms
    all_farms_query = f"""
    SELECT 
        name as farm_name,
        latitude,
        longitude,
        capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
    WHERE status = 'Operational'
    AND latitude IS NOT NULL
    AND longitude IS NOT NULL
    ORDER BY capacity_mw DESC
    """
    all_farms = client.query(all_farms_query).to_dataframe()
    
    # Get farms with existing data
    existing_query = f"""
    SELECT DISTINCT farm_name
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    """
    existing = client.query(existing_query).to_dataframe()
    existing_set = set(existing['farm_name'].tolist())
    
    # Filter to remaining
    remaining = all_farms[~all_farms['farm_name'].isin(existing_set)]
    
    print(f"✅ Total farms: {len(all_farms)}")
    print(f"✅ Already downloaded: {len(existing_set)}")
    print(f"⏳ Remaining: {len(remaining)}")
    
    return remaining

def download_weather_for_farm(farm_name, latitude, longitude, max_retries=3):
    """Download with retry logic."""
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_100m",
            "wind_direction_100m",
        ],
        "timezone": "UTC",
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(API_URL, params=params, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            if "hourly" not in data:
                print(f"   ⚠️  No hourly data")
                return None
            
            hourly = data["hourly"]
            df = pd.DataFrame({
                "farm_name": farm_name,
                "timestamp": pd.to_datetime(hourly["time"]),
                "temperature_2m": hourly.get("temperature_2m"),
                "relative_humidity_2m": hourly.get("relative_humidity_2m"),
                "precipitation": hourly.get("precipitation"),
                "wind_speed_100m": hourly.get("wind_speed_100m"),
                "wind_direction_100m": hourly.get("wind_direction_100m"),
            })
            
            return df
            
        except requests.exceptions.HTTPError as e:
            if "429" in str(e):
                if attempt < max_retries - 1:
                    wait_time = 60 * (attempt + 1)  # 60s, 120s, 180s
                    print(f"   ⏳ Rate limited, waiting {wait_time}s (attempt {attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Rate limit exceeded after {max_retries} attempts")
                    return None
            else:
                print(f"   ❌ HTTP Error: {e}")
                return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    return None

def upload_to_bigquery(df, table_id):
    """Upload DataFrame to BigQuery."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("temperature_2m", "FLOAT"),
            bigquery.SchemaField("relative_humidity_2m", "FLOAT"),
            bigquery.SchemaField("precipitation", "FLOAT"),
            bigquery.SchemaField("wind_speed_100m", "FLOAT"),
            bigquery.SchemaField("wind_direction_100m", "FLOAT"),
        ]
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

print("=" * 80)
print("ERA5 Remaining Farms Download (Incremental)")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Get remaining farms
remaining_df = get_remaining_farms()

if len(remaining_df) == 0:
    print("✅ All farms complete!")
    sys.exit(0)

print()
print(f"Downloading {len(remaining_df)} farms (max 5 per run to avoid rate limits)")
print()

# Limit to 5 farms per run
remaining_df = remaining_df.head(5)

successful = 0
failed = 0
uploaded_rows = 0

for idx, row in remaining_df.iterrows():
    farm_name = row['farm_name']
    latitude = row['latitude']
    longitude = row['longitude']
    capacity = row['capacity_mw']
    
    print(f"[{idx+1}] {farm_name} ({capacity:.0f} MW)")
    print(f"   {latitude:.3f}°N, {longitude:.3f}°E")
    
    df = download_weather_for_farm(farm_name, latitude, longitude)
    
    if df is not None and len(df) > 0:
        print(f"   ✅ {len(df):,} observations")
        
        # Upload immediately
        table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
        try:
            upload_to_bigquery(df, table_id)
            print(f"   ✅ Uploaded to BigQuery")
            successful += 1
            uploaded_rows += len(df)
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            failed += 1
    else:
        failed += 1
    
    # Rate limiting between farms
    print(f"   ⏳ Waiting 10 seconds...")
    time.sleep(10)
    print()

print("=" * 80)
print("RUN COMPLETE")
print("=" * 80)
print(f"Successful: {successful}/{len(remaining_df)}")
print(f"Failed: {failed}")
print(f"Uploaded: {uploaded_rows:,} rows")
print()

if successful > 0:
    # Verify
    client = bigquery.Client(project=PROJECT_ID, location="US")
    verify_query = f"""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT farm_name) as farms
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    """
    verify_df = client.query(verify_query).to_dataframe()
    print("📊 Total in BigQuery:")
    print(f"   Rows: {verify_df['total_rows'][0]:,}")
    print(f"   Farms: {verify_df['farms'][0]}")
