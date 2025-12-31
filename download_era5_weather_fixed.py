#!/usr/bin/env python3
"""
Download ERA5 Weather Data for Icing Detection (Todo #4) - FIXED VERSION

Improvements:
- Max retry limit (3 attempts per farm/year)
- Incremental upload to BigQuery (per year, not all-at-once)
- Skip problematic farms and continue
- Better timeout handling
- Progress tracking

Author: AI Coding Agent
Date: December 30, 2025
"""

import time
from datetime import datetime, timedelta
import requests
import pandas as pd
from google.cloud import bigquery
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MAX_RETRIES = 3

def fetch_openmeteo_weather(lat, lon, start_date, end_date, farm_name, retry_count=0):
    """
    Fetch historical weather data from Open-Meteo Archive API with retry logic.
    
    Variables for icing detection:
    - temperature_2m, relative_humidity_2m, precipitation, cloud_cover,
      pressure_msl, shortwave_radiation
    """
    
    if retry_count >= MAX_RETRIES:
        print(f"  ❌ Max retries ({MAX_RETRIES}) reached for {farm_name} - SKIPPING")
        return None
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "cloud_cover",
            "pressure_msl",
            "shortwave_radiation"
        ],
        "timezone": "UTC"
    }
    
    try:
        if retry_count > 0:
            print(f"  🔄 Retry {retry_count}/{MAX_RETRIES} for {farm_name}")
        else:
            print(f"  Fetching {farm_name}: {start_date} to {end_date}")
        
        response = requests.get(url, params=params, timeout=120)  # 2 min timeout
        response.raise_for_status()
        
        data = response.json()
        
        if "hourly" not in data:
            print(f"  ❌ No hourly data for {farm_name} - SKIPPING")
            return None
        
        hourly = data["hourly"]
        
        df = pd.DataFrame({
            "time_utc": pd.to_datetime(hourly["time"]),
            "temperature_2m": hourly["temperature_2m"],
            "relative_humidity_2m": hourly["relative_humidity_2m"],
            "precipitation": hourly["precipitation"],
            "cloud_cover": hourly["cloud_cover"],
            "pressure_msl": hourly["pressure_msl"],
            "shortwave_radiation": hourly["shortwave_radiation"],
            "farm_name": farm_name,
            "latitude": lat,
            "longitude": lon
        })
        
        print(f"  ✅ {farm_name}: {len(df):,} records")
        return df
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            wait_time = 60 + (retry_count * 30)  # Exponential backoff
            print(f"  ⚠️  Rate limited, waiting {wait_time}s (retry {retry_count+1}/{MAX_RETRIES})...")
            time.sleep(wait_time)
            return fetch_openmeteo_weather(lat, lon, start_date, end_date, farm_name, retry_count + 1)
        else:
            print(f"  ❌ HTTP {e.response.status_code} for {farm_name} - SKIPPING")
            return None
    except requests.exceptions.Timeout:
        print(f"  ⏱️  Timeout for {farm_name} - retrying...")
        time.sleep(30)
        return fetch_openmeteo_weather(lat, lon, start_date, end_date, farm_name, retry_count + 1)
    except Exception as e:
        print(f"  ❌ Error for {farm_name}: {e} - SKIPPING")
        return None

def upload_to_bigquery(df, year, client, table_id):
    """Upload data to BigQuery with WRITE_APPEND."""
    
    if df is None or len(df) == 0:
        print(f"  ⚠️  No data to upload for year {year}")
        return False
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",  # Changed from WRITE_TRUNCATE
        schema=[
            bigquery.SchemaField("time_utc", "TIMESTAMP"),
            bigquery.SchemaField("temperature_2m", "FLOAT"),
            bigquery.SchemaField("relative_humidity_2m", "FLOAT"),
            bigquery.SchemaField("precipitation", "FLOAT"),
            bigquery.SchemaField("cloud_cover", "FLOAT"),
            bigquery.SchemaField("pressure_msl", "FLOAT"),
            bigquery.SchemaField("shortwave_radiation", "FLOAT"),
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
        ]
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f"  ✅ Uploaded {len(df):,} records for year {year}")
        return True
    except Exception as e:
        print(f"  ❌ Upload failed for year {year}: {e}")
        return False

def main():
    print("="*70)
    print("ERA5 Weather Data Download (FIXED VERSION)")
    print("="*70)
    print("Improvements:")
    print("- Max 3 retries per farm/year (no infinite loops)")
    print("- Incremental upload per year")
    print("- Skip problematic farms and continue")
    print("- Better timeout handling")
    print("="*70)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Check if table exists, create if not
    table_id = f"{PROJECT_ID}.{DATASET}.era5_weather_icing"
    
    try:
        client.get_table(table_id)
        print(f"\n✅ Table exists: {table_id}")
        print("   Using WRITE_APPEND mode (incremental upload)")
    except:
        print(f"\n📝 Creating table: {table_id}")
        schema = [
            bigquery.SchemaField("time_utc", "TIMESTAMP"),
            bigquery.SchemaField("temperature_2m", "FLOAT"),
            bigquery.SchemaField("relative_humidity_2m", "FLOAT"),
            bigquery.SchemaField("precipitation", "FLOAT"),
            bigquery.SchemaField("cloud_cover", "FLOAT"),
            bigquery.SchemaField("pressure_msl", "FLOAT"),
            bigquery.SchemaField("shortwave_radiation", "FLOAT"),
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"✅ Table created: {table_id}")
    
    # Get farm locations
    query = f"""
    SELECT DISTINCT
        farm_name,
        latitude,
        longitude
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    ORDER BY farm_name
    """
    
    farms_df = client.query(query).to_dataframe()
    print(f"\n📍 Found {len(farms_df)} wind farm locations")
    
    # Date ranges (yearly chunks)
    date_ranges = [
        ("2021-01-01", "2021-12-31", "2021"),
        ("2022-01-01", "2022-12-31", "2022"),
        ("2023-01-01", "2023-12-31", "2023"),
        ("2024-01-01", "2024-12-31", "2024"),
        ("2025-01-01", "2025-12-30", "2025")
    ]
    
    start_time = time.time()
    total_records = 0
    failed_farms = []
    
    for year_idx, (start_date, end_date, year) in enumerate(date_ranges, 1):
        print(f"\n{'='*70}")
        print(f"Year {year_idx}/5: {year} ({start_date} to {end_date})")
        print(f"{'='*70}")
        
        year_data = []
        year_failed = []
        
        for idx, row in farms_df.iterrows():
            farm_name = row['farm_name']
            lat = row['latitude']
            lon = row['longitude']
            
            df = fetch_openmeteo_weather(lat, lon, start_date, end_date, farm_name)
            
            if df is not None and len(df) > 0:
                year_data.append(df)
            else:
                year_failed.append(farm_name)
            
            # Rate limiting: 10 requests per minute for free tier
            if (idx + 1) % 10 == 0:
                print(f"  ⏸️  Rate limit pause (progress: {idx+1}/{len(farms_df)})...")
                time.sleep(65)
        
        # Upload this year's data
        if year_data:
            year_combined = pd.concat(year_data, ignore_index=True)
            upload_to_bigquery(year_combined, year, client, table_id)
            total_records += len(year_combined)
            print(f"\n✅ Year {year} complete: {len(year_combined):,} records uploaded")
        else:
            print(f"\n⚠️  Year {year}: No data to upload")
        
        if year_failed:
            failed_farms.extend([(year, farm) for farm in year_failed])
            print(f"⚠️  Failed farms for {year}: {len(year_failed)}")
        
        sys.stdout.flush()  # Force output
    
    elapsed = (time.time() - start_time) / 60
    
    # Final summary
    print(f"\n{'='*70}")
    print("✅ DOWNLOAD COMPLETE")
    print(f"{'='*70}")
    print(f"Total time: {elapsed:.1f} minutes")
    print(f"Total records: {total_records:,}")
    
    if failed_farms:
        print(f"\n⚠️  Failed downloads ({len(failed_farms)} farm-years):")
        for year, farm in failed_farms[:10]:  # Show first 10
            print(f"  - {year}: {farm}")
        if len(failed_farms) > 10:
            print(f"  ... and {len(failed_farms) - 10} more")
    
    # Verify in BigQuery
    print(f"\n{'='*70}")
    print("Verifying uploaded data...")
    print(f"{'='*70}")
    
    verify_query = f"""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT farm_name) as farms,
        MIN(DATE(time_utc)) as first_date,
        MAX(DATE(time_utc)) as last_date
    FROM `{table_id}`
    """
    
    verify_df = client.query(verify_query).to_dataframe()
    print(verify_df.to_string(index=False))
    
    print(f"\n{'='*70}")
    print("NEXT STEPS:")
    print(f"{'='*70}")
    print("1. Review failed farms (if any)")
    print("2. Run: python3 validate_icing_conditions.py")
    print("3. Retrain icing classifier with weather data")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
