#!/usr/bin/env python3
"""
Download ERA5 Weather Data INCLUDING WIND GUSTS via Open-Meteo API

FIXES:
1. Explicitly labels wind_speed_100m as km/h (not m/s)
2. Adds wind_gusts_10m data
3. Adds surface_pressure (for upstream station analysis)
4. Downloads remaining 20 farms

Target table: era5_weather_data_v2 (corrected schema)
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_weather_data_v2"
API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Date range
START_DATE = "2020-01-01"
END_DATE = "2025-11-30"

def get_remaining_farms():
    """Get farms not yet downloaded."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get all farms
    query_all = f"""
    SELECT 
        name as farm_name,
        latitude,
        longitude,
        capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
    WHERE status = 'Operational'
    ORDER BY name
    """
    all_farms = client.query(query_all).to_dataframe()
    
    # Get already downloaded farms
    query_done = f"""
    SELECT DISTINCT farm_name
    FROM `{PROJECT_ID}.{DATASET}.era5_weather_data`
    """
    done_farms = client.query(query_done).to_dataframe()
    
    # Find remaining
    remaining = all_farms[~all_farms['farm_name'].isin(done_farms['farm_name'])]
    print(f"✅ Total farms: {len(all_farms)}")
    print(f"✅ Already downloaded: {len(done_farms)}")
    print(f"✅ Remaining: {len(remaining)}")
    
    return remaining

def download_weather_for_farm(farm_name, latitude, longitude):
    """Download weather data INCLUDING GUSTS and PRESSURE."""
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "surface_pressure",           # NEW: For upstream station analysis
            "wind_speed_100m",             # km/h (mean wind)
            "wind_gusts_10m",              # NEW: km/h (gusts)
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
            "temperature_2m_c": hourly.get("temperature_2m"),
            "relative_humidity_2m_pct": hourly.get("relative_humidity_2m"),
            "precipitation_mm": hourly.get("precipitation"),
            "surface_pressure_hpa": hourly.get("surface_pressure"),
            "wind_speed_100m_kmh": hourly.get("wind_speed_100m"),  # LABELED AS km/h
            "wind_gusts_10m_kmh": hourly.get("wind_gusts_10m"),    # NEW
            "wind_direction_100m_deg": hourly.get("wind_direction_100m"),
        })
        
        # Add computed m/s columns
        df['wind_speed_100m_ms'] = df['wind_speed_100m_kmh'] / 3.6
        df['wind_gusts_10m_ms'] = df['wind_gusts_10m_kmh'] / 3.6
        
        return df
        
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout after 120 seconds")
        return None
    except requests.exceptions.HTTPError as e:
        if "429" in str(e):
            print(f"   ⏸️  Rate limited - will retry in 24h")
            return "RATE_LIMITED"
        print(f"   ❌ HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def upload_to_bigquery(df, table_id):
    """Upload DataFrame to BigQuery."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=[
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("temperature_2m_c", "FLOAT64"),
            bigquery.SchemaField("relative_humidity_2m_pct", "FLOAT64"),
            bigquery.SchemaField("precipitation_mm", "FLOAT64"),
            bigquery.SchemaField("surface_pressure_hpa", "FLOAT64"),
            bigquery.SchemaField("wind_speed_100m_kmh", "FLOAT64"),
            bigquery.SchemaField("wind_gusts_10m_kmh", "FLOAT64"),
            bigquery.SchemaField("wind_direction_100m_deg", "FLOAT64"),
            bigquery.SchemaField("wind_speed_100m_ms", "FLOAT64"),
            bigquery.SchemaField("wind_gusts_10m_ms", "FLOAT64"),
        ],
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"   ✅ Uploaded {len(df):,} rows to {table_id}")

def main():
    """Download remaining farms."""
    
    print('=' * 80)
    print('🌦️  DOWNLOAD ERA5 WEATHER (WITH GUSTS) - REMAINING FARMS')
    print('=' * 80)
    print()
    
    farms = get_remaining_farms()
    
    if len(farms) == 0:
        print('✅ All farms already downloaded!')
        return
    
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    downloaded = 0
    rate_limited = False
    
    for idx, row in farms.iterrows():
        farm = row['farm_name']
        lat = row['latitude']
        lon = row['longitude']
        
        print(f"[{idx+1}/{len(farms)}] {farm} ({lat:.2f}, {lon:.2f})")
        
        df = download_weather_for_farm(farm, lat, lon)
        
        if df == "RATE_LIMITED":
            rate_limited = True
            break
        
        if df is not None:
            upload_to_bigquery(df, table_id)
            downloaded += 1
            print(f"   📊 Progress: {downloaded}/{len(farms)} farms")
            time.sleep(10)  # Rate limit protection
        
        print()
    
    print('=' * 80)
    if rate_limited:
        print('⏸️  RATE LIMITED - Schedule cron job to resume in 24 hours')
    else:
        print('✅ DOWNLOAD COMPLETE')
    print('=' * 80)
    print()
    print(f'Downloaded: {downloaded} farms')
    print(f'Remaining: {len(farms) - downloaded} farms')
    print()
    print('Next: Run download_era5_remaining_farms_24h.sh tomorrow')

if __name__ == '__main__':
    main()
