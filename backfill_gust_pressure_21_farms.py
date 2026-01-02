#!/usr/bin/env python3
"""
Backfill Gust + Pressure Data for 21 Existing Farms

Downloads ONLY the missing variables for farms we already have:
- wind_gusts_10m (km/h + m/s)
- surface_pressure (hPa)

Merges with existing data to create complete dataset.
Can run in ONE SESSION (~30 minutes with 15-second delays).
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_weather_data_complete"  # New table with all variables
API_URL = "https://archive-api.open-meteo.com/v1/archive"

START_DATE = "2020-01-01"
END_DATE = "2025-11-30"

def get_existing_farms():
    """Get farms that already have basic weather data."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT 
        e.farm_name,
        f.latitude,
        f.longitude
    FROM `{PROJECT_ID}.{DATASET}.era5_weather_data` e
    JOIN `{PROJECT_ID}.{DATASET}.offshore_wind_farms` f
    ON e.farm_name = f.name
    ORDER BY e.farm_name
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Found {len(df)} farms needing gust + pressure data")
    return df

def download_gust_pressure(farm_name, latitude, longitude):
    """Download ONLY gust + pressure data."""
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": [
            "surface_pressure",
            "wind_gusts_10m",
        ],
        "timezone": "UTC",
    }
    
    try:
        print(f"   Downloading gust + pressure data...")
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
            "surface_pressure_hpa": hourly.get("surface_pressure"),
            "wind_gusts_10m_kmh": hourly.get("wind_gusts_10m"),
        })
        
        # Add computed m/s columns
        df['wind_gusts_10m_ms'] = df['wind_gusts_10m_kmh'] / 3.6
        
        print(f"   ✅ Retrieved {len(df):,} hours of data")
        return df
        
    except requests.exceptions.HTTPError as e:
        if "429" in str(e):
            print(f"   ⚠️  Rate limited - increase delay")
            return "RATE_LIMITED"
        print(f"   ❌ HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def upload_to_bigquery(df, table_id):
    """Upload gust + pressure data to BigQuery."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=[
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("surface_pressure_hpa", "FLOAT64"),
            bigquery.SchemaField("wind_gusts_10m_kmh", "FLOAT64"),
            bigquery.SchemaField("wind_gusts_10m_ms", "FLOAT64"),
        ],
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"   ✅ Uploaded to BigQuery")

def merge_tables():
    """Merge existing weather data with new gust + pressure data."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print()
    print('=' * 80)
    print('🔗 MERGING EXISTING DATA WITH NEW GUST + PRESSURE DATA')
    print('=' * 80)
    
    merge_query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.{TABLE_NAME}` AS
    SELECT 
        e.farm_name,
        e.timestamp,
        e.temperature_2m as temperature_2m_c,
        e.relative_humidity_2m as relative_humidity_2m_pct,
        e.precipitation as precipitation_mm,
        e.cloud_cover as cloud_cover_pct,
        e.wind_speed_100m as wind_speed_100m_kmh,
        e.wind_speed_100m / 3.6 as wind_speed_100m_ms,
        e.wind_direction_100m as wind_direction_100m_deg,
        g.surface_pressure_hpa,
        g.wind_gusts_10m_kmh,
        g.wind_gusts_10m_ms
    FROM `{PROJECT_ID}.{DATASET}.era5_weather_data` e
    LEFT JOIN `{PROJECT_ID}.{DATASET}.era5_gust_pressure_backfill` g
    ON e.farm_name = g.farm_name AND e.timestamp = g.timestamp
    """
    
    print('Creating merged table...')
    client.query(merge_query).result()
    print('✅ Merge complete!')
    print()
    
    # Verify
    verify_query = f"""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT farm_name) as farms,
        COUNT(surface_pressure_hpa) as rows_with_pressure,
        COUNT(wind_gusts_10m_ms) as rows_with_gusts,
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    """
    df = client.query(verify_query).to_dataframe()
    print('Final Table Statistics:')
    print(df.to_string(index=False))

def main():
    """Download gust + pressure for all 21 existing farms."""
    
    print('=' * 80)
    print('🌬️  BACKFILL GUST + PRESSURE DATA (21 FARMS)')
    print('=' * 80)
    print()
    print('Strategy: Download all farms in ONE SESSION with 15-second delays')
    print('Expected duration: ~30 minutes (21 farms × 90 seconds each)')
    print()
    
    farms = get_existing_farms()
    
    # Temporary table for new data
    temp_table_id = f"{PROJECT_ID}.{DATASET}.era5_gust_pressure_backfill"
    
    downloaded = 0
    all_data = []
    
    for idx, row in farms.iterrows():
        farm = row['farm_name']
        lat = row['latitude']
        lon = row['longitude']
        
        print(f"[{idx+1}/{len(farms)}] {farm} ({lat:.2f}, {lon:.2f})")
        
        df = download_gust_pressure(farm, lat, lon)
        
        if isinstance(df, str) and df == "RATE_LIMITED":
            print()
            print('⚠️  RATE LIMITED - Increase delay to 20 seconds and continue...')
            time.sleep(20)
            # Retry
            df = download_gust_pressure(farm, lat, lon)
        
        if df is not None and not (isinstance(df, str) and df == "RATE_LIMITED"):
            all_data.append(df)
            downloaded += 1
            
            # Upload every 5 farms to avoid memory issues
            if len(all_data) >= 5:
                combined = pd.concat(all_data, ignore_index=True)
                upload_to_bigquery(combined, temp_table_id)
                all_data = []
        
        # Rate limit protection: 15 seconds between farms
        if idx < len(farms) - 1:
            print(f"   ⏳ Waiting 15 seconds (rate limit protection)...")
            time.sleep(15)
        
        print()
    
    # Upload remaining data
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        upload_to_bigquery(combined, temp_table_id)
    
    print('=' * 80)
    print('📊 DOWNLOAD COMPLETE')
    print('=' * 80)
    print()
    print(f'✅ Downloaded: {downloaded}/{len(farms)} farms')
    print(f'⏳ Temporary table: {temp_table_id}')
    print()
    
    if downloaded == len(farms):
        # Merge tables
        merge_tables()
        
        print()
        print('=' * 80)
        print('✅ BACKFILL COMPLETE!')
        print('=' * 80)
        print()
        print('New table: era5_weather_data_complete')
        print('  - All 21 farms')
        print('  - Includes: wind_gusts_10m, surface_pressure')
        print('  - Corrected wind speed units (km/h + m/s)')
        print()
    else:
        print('⚠️  Some farms failed - review errors above')

if __name__ == '__main__':
    main()
