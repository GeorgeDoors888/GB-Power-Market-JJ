#!/usr/bin/env python3
"""
Fetch historical wind data from Open-Meteo for offshore wind farms.
Downloads hourly wind speed data with rate limiting and retry logic.
Uploads to BigQuery for predictive modeling.
"""

import requests
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
import sys
import time

# -------------------------
# CONFIGURATION
# -------------------------

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

# Historic date range - FULL HISTORICAL DATA
START_DATE = "2020-01-01"
END_DATE = "2025-12-30"

# Variables to fetch (hourly)
VARIABLES = [
    "wind_speed_10m",       # 10m wind speed (m/s)
    "wind_direction_10m",   # 10m wind direction (degrees)
    "wind_speed_100m",      # 100m wind speed (m/s) - closer to hub height
    "wind_gusts_10m"        # Wind gusts (m/s)
]

# Open-Meteo Historical Weather API endpoint
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Rate limiting (Open-Meteo free tier: ~10 requests/minute)
DELAY_BETWEEN_REQUESTS = 7  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds to wait after 429 error

# -------------------------
# FETCH OFFSHORE WIND FARMS
# -------------------------

def fetch_offshore_wind_farms():
    """Fetch offshore wind farm locations from BigQuery."""
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
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Fetched {len(df)} offshore wind farms from BigQuery")
    return df

# -------------------------
# FETCH WEATHER DATA
# -------------------------

def fetch_weather_for_farm(farm_name, latitude, longitude, retry_count=0):
    """
    Fetch historical weather data for a single wind farm with retry logic.
    
    Args:
        farm_name: Wind farm name
        latitude: Farm latitude
        longitude: Farm longitude
        retry_count: Current retry attempt
    
    Returns:
        DataFrame with hourly weather data
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join(VARIABLES),
        "wind_speed_unit": "ms",     # metres per second
        "timezone": "UTC"            # consistent UTC timestamps
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=60)
        
        # Handle rate limiting
        if response.status_code == 429:
            if retry_count < MAX_RETRIES:
                print(f"  ⏳ {farm_name}: Rate limited, waiting {RETRY_DELAY}s (retry {retry_count + 1}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY)
                return fetch_weather_for_farm(farm_name, latitude, longitude, retry_count + 1)
            else:
                print(f"  ❌ {farm_name}: Max retries exceeded")
                return None
        
        response.raise_for_status()
        data = response.json()
        
        # Extract times and variables
        times = data["hourly"]["time"]
        df = pd.DataFrame({
            "farm_name": farm_name,
            "time_utc": pd.to_datetime(times),
            "latitude": latitude,
            "longitude": longitude
        })
        
        # Add each variable
        for var in VARIABLES:
            if var in data["hourly"]:
                df[var] = data["hourly"][var]
        
        print(f"  ✅ {farm_name}: {len(df)} hourly rows")
        return df
        
    except Exception as e:
        print(f"  ❌ {farm_name}: ERROR - {e}")
        return None

# -------------------------
# MAIN EXECUTION
# -------------------------

def main():
    print("=" * 70)
    print("Historical Wind Data Fetcher v2 - Open-Meteo API")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Rate limit: {DELAY_BETWEEN_REQUESTS}s between requests")
    print("=" * 70)
    
    # Fetch wind farm locations
    print("\n📍 Fetching offshore wind farm locations...")
    farms_df = fetch_offshore_wind_farms()
    
    # Fetch weather data for each farm
    print(f"\n🌤️  Fetching historical weather data for {len(farms_df)} farms...")
    print(f"   Estimated time: {(len(farms_df) * DELAY_BETWEEN_REQUESTS) / 60:.1f} minutes")
    
    all_weather = []
    success_count = 0
    failed_farms = []
    
    for idx, farm in farms_df.iterrows():
        weather_df = fetch_weather_for_farm(
            farm['name'],
            farm['latitude'],
            farm['longitude']
        )
        
        if weather_df is not None:
            weather_df['capacity_mw'] = farm['capacity_mw']
            weather_df['gsp_zone'] = farm['gsp_zone']
            all_weather.append(weather_df)
            success_count += 1
        else:
            failed_farms.append(farm['name'])
        
        # Rate limiting delay
        if idx < len(farms_df) - 1:  # Don't delay after last farm
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    print(f"\n📊 Download Summary:")
    print(f"   ✅ Success: {success_count}/{len(farms_df)} farms")
    if failed_farms:
        print(f"   ❌ Failed: {len(failed_farms)} farms")
        print(f"      {', '.join(failed_farms[:5])}")
        if len(failed_farms) > 5:
            print(f"      ... and {len(failed_farms) - 5} more")
    
    if not all_weather:
        print("\n❌ No weather data fetched!")
        return 1
    
    # Combine all data
    combined_df = pd.concat(all_weather, ignore_index=True)
    print(f"\n✅ Combined: {len(combined_df):,} total rows ({success_count} farms)")
    
    # Save to CSV
    csv_file = f"historic_wind_openmeteo_{START_DATE}_to_{END_DATE}.csv"
    combined_df.to_csv(csv_file, index=False)
    print(f"💾 Saved to {csv_file}")
    
    # Upload to BigQuery
    print("\n📤 Uploading to BigQuery...")
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    table_id = f"{PROJECT_ID}.{DATASET}.openmeteo_wind_historic"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',  # Replace existing data
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
    
    # Summary statistics
    print("\n📊 Summary Statistics:")
    print(f"   Farms: {combined_df['farm_name'].nunique()}")
    print(f"   Date range: {combined_df['time_utc'].min()} to {combined_df['time_utc'].max()}")
    print(f"   Avg wind speed (10m): {combined_df['wind_speed_10m'].mean():.1f} m/s")
    print(f"   Avg wind speed (100m): {combined_df['wind_speed_100m'].mean():.1f} m/s")
    print(f"   Max wind speed (100m): {combined_df['wind_speed_100m'].max():.1f} m/s")
    print(f"   Total capacity: {combined_df.groupby('farm_name')['capacity_mw'].first().sum():.0f} MW")
    
    if failed_farms:
        print(f"\n⚠️  {len(failed_farms)} farms failed - run script again to retry")
    
    return 0

if __name__ == "__main__":
    exit(main())
