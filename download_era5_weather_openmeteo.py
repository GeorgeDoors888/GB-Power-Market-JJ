#!/usr/bin/env python3
"""
Download ERA5 Weather Data for Offshore Wind Farms via Open-Meteo API

Uses Open-Meteo Archive API (ERA5 reanalysis) instead of CDS API.
- Works for offshore/ocean coordinates (unlike CDS land-only)
- No authentication required
- Faster download speeds
- Temperature, humidity, precipitation, wind speed

Target table: era5_weather_data
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

# Date range
START_DATE = "2020-01-01"
END_DATE = "2025-11-30"

def get_offshore_wind_farms():
    """Get wind farm coordinates from BigQuery."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        name as farm_name,
        latitude,
        longitude,
        capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
    WHERE status = 'Operational'
    ORDER BY name
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Loaded {len(df)} offshore wind farms")
    return df

def download_weather_for_farm(farm_name, latitude, longitude):
    """Download weather data for one farm from Open-Meteo API."""
    
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
    
    try:
        response = requests.get(API_URL, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        if "hourly" not in data:
            print(f"   ❌ No hourly data in response")
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
        
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout after 120 seconds")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
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
print("ERA5 Weather Data Download via Open-Meteo API")
print("=" * 80)
print(f"API: {API_URL}")
print(f"Date range: {START_DATE} to {END_DATE}")
print(f"Target table: {PROJECT_ID}.{DATASET}.{TABLE_NAME}")
print()

# Get wind farms
farms_df = get_offshore_wind_farms()
total_farms = len(farms_df)

# Download for each farm
all_dfs = []
successful = 0
failed = 0
start_time = time.time()

for idx, row in farms_df.iterrows():
    farm_name = row['farm_name']
    latitude = row['latitude']
    longitude = row['longitude']
    capacity = row['capacity_mw']
    
    print(f"[{idx+1}/{total_farms}] {farm_name} ({capacity:.0f} MW)")
    print(f"   Location: {latitude:.3f}°N, {longitude:.3f}°E")
    
    df = download_weather_for_farm(farm_name, latitude, longitude)
    
    if df is not None and len(df) > 0:
        print(f"   ✅ Downloaded {len(df):,} hourly observations")
        print(f"   Temperature: {df['temperature_2m'].mean():.1f}°C (avg), {df['temperature_2m'].min():.1f}°C (min)")
        print(f"   Humidity: {df['relative_humidity_2m'].mean():.0f}% (avg)")
        print(f"   Wind: {df['wind_speed_100m'].mean():.1f} m/s (avg)")
        all_dfs.append(df)
        successful += 1
    else:
        print(f"   ❌ Download failed")
        failed += 1
    
    # Rate limiting
    if idx < total_farms - 1:
        print(f"   ⏳ Waiting 2 seconds...")
        time.sleep(2)
    print()

# Upload all data in single batch
if len(all_dfs) > 0:
    print("=" * 80)
    print("📤 Uploading to BigQuery...")
    print("=" * 80)
    combined_df = pd.concat(all_dfs, ignore_index=True)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    try:
        upload_to_bigquery(combined_df, table_id)
        print(f"✅ Uploaded {len(combined_df):,} total rows ({len(all_dfs)} farms)")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        print(f"💾 Saving to CSV backup...")
        backup_file = f"era5_weather_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        combined_df.to_csv(backup_file, index=False)
        print(f"   Saved to: {backup_file}")
        sys.exit(1)
else:
    print("❌ No data to upload")
    sys.exit(1)

# Summary
elapsed = time.time() - start_time
print()
print("=" * 80)
print("DOWNLOAD COMPLETE")
print("=" * 80)
print(f"Successful: {successful}/{total_farms}")
print(f"Failed: {failed}")
print(f"Total observations: {len(combined_df):,}")
print(f"Total time: {elapsed/60:.1f} minutes")
print()

# Verify upload
print("🔍 Verifying BigQuery upload...")
client = bigquery.Client(project=PROJECT_ID, location="US")
verify_query = f"""
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT farm_name) as farms,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest,
    AVG(temperature_2m) as avg_temp,
    AVG(relative_humidity_2m) as avg_humidity,
    AVG(wind_speed_100m) as avg_wind
FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
"""

verify_df = client.query(verify_query).to_dataframe()
print(verify_df.to_string(index=False))
print()

print("✅ ERA5 weather data ready for analysis!")
print(f"   Next: python3 analyze_wave_weather_generation.py")
