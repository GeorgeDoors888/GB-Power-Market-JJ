#!/usr/bin/env python3
"""
Fetch historical wind data in YEARLY chunks to avoid rate limits.
Processes one year at a time for all farms, then moves to next year.
"""

import requests
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
import sys
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

# Process in yearly chunks
YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

VARIABLES = [
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_speed_100m",
    "wind_gusts_10m"
]

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
DELAY_BETWEEN_REQUESTS = 10  # Increased to 10 seconds
RETRY_DELAY = 120  # 2 minutes after 429

def fetch_offshore_wind_farms():
    """Fetch top 10 farms by capacity (manageable chunk)."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    query = f"""
    SELECT 
        name,
        latitude,
        longitude,
        capacity_mw,
        gsp_zone
    FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
    WHERE status = 'Operational'
      AND latitude IS NOT NULL
      AND longitude IS NOT NULL
    ORDER BY capacity_mw DESC
    LIMIT 10
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Fetched {len(df)} top offshore wind farms (by capacity)")
    return df

def fetch_weather_year(farm_name, latitude, longitude, year, retry_count=0):
    """Fetch one year of data."""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31" if year < 2025 else "2025-12-30"
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(VARIABLES),
        "wind_speed_unit": "ms",
        "timezone": "UTC"
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=60)
        
        if response.status_code == 429:
            if retry_count < 3:
                print(f"    ⏳ Rate limited, waiting {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                return fetch_weather_year(farm_name, latitude, longitude, year, retry_count + 1)
            else:
                print(f"    ❌ Max retries exceeded")
                return None
        
        response.raise_for_status()
        data = response.json()
        
        times = data["hourly"]["time"]
        df = pd.DataFrame({
            "farm_name": farm_name,
            "time_utc": pd.to_datetime(times),
            "latitude": latitude,
            "longitude": longitude,
            "year": year
        })
        
        for var in VARIABLES:
            if var in data["hourly"]:
                df[var] = data["hourly"][var]
        
        print(f"    ✅ {year}: {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"    ❌ {year}: {e}")
        return None

def main():
    print("=" * 70)
    print("Historical Wind Data - CHUNKED Download (Top 10 Farms)")
    print("=" * 70)
    
    farms_df = fetch_offshore_wind_farms()
    
    all_data = []
    
    for idx, farm in farms_df.iterrows():
        print(f"\n📍 {idx + 1}/{len(farms_df)}: {farm['name']} ({farm['capacity_mw']:.0f} MW)")
        
        farm_years = []
        for year in YEARS:
            year_df = fetch_weather_year(
                farm['name'],
                farm['latitude'],
                farm['longitude'],
                year
            )
            
            if year_df is not None:
                year_df['capacity_mw'] = farm['capacity_mw']
                year_df['gsp_zone'] = farm['gsp_zone']
                farm_years.append(year_df)
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        if farm_years:
            farm_combined = pd.concat(farm_years, ignore_index=True)
            all_data.append(farm_combined)
            print(f"  ✅ Total: {len(farm_combined):,} rows for {farm['name']}")
    
    if not all_data:
        print("\n❌ No data fetched")
        return 1
    
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df.drop('year', axis=1)
    
    print(f"\n✅ Combined: {len(combined_df):,} rows")
    
    # Save CSV
    csv_file = f"historic_wind_top10_2020_2025.csv"
    combined_df.to_csv(csv_file, index=False)
    print(f"💾 Saved to {csv_file}")
    
    # Upload to BigQuery
    print("\n📤 Uploading to BigQuery...")
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    table_id = f"{PROJECT_ID}.{DATASET}.openmeteo_wind_historic"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_APPEND',
        schema=[
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("time_utc", "TIMESTAMP"),
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
            bigquery.SchemaField("wind_speed_10m", "FLOAT"),
            bigquery.SchemaField("wind_direction_10m", "FLOAT"),
            bigquery.SchemaField("wind_speed_100m", "FLOAT"),
            bigquery.SchemaField("wind_gusts_10m", "FLOAT"),
            bigquery.SchemaField("capacity_mw", "FLOAT"),
            bigquery.SchemaField("gsp_zone", "STRING"),
        ]
    )
    
    job = client.load_table_from_dataframe(combined_df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded {len(combined_df):,} rows to {table_id}")
    
    print("\n📊 Summary:")
    print(f"   Farms: {combined_df['farm_name'].nunique()}")
    print(f"   Date range: {combined_df['time_utc'].min()} to {combined_df['time_utc'].max()}")
    print(f"   Avg wind (100m): {combined_df['wind_speed_100m'].mean():.1f} m/s")
    print(f"   Max wind (100m): {combined_df['wind_speed_100m'].max():.1f} m/s")
    
    return 0

if __name__ == "__main__":
    exit(main())
