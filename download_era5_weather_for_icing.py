#!/usr/bin/env python3
"""
Download ERA5 Weather Data for Icing Detection (Todo #4)

Downloads temperature, humidity, precipitation, cloud cover, pressure, and radiation
for all 48 wind farm locations (2021-2025) to enable accurate icing risk detection.

Icing Conditions (to be validated):
- Temperature: -3°C to +2°C (near-freezing range)
- Humidity: >92% (moisture for ice accretion)
- Precipitation: >0 mm (supercooled droplets)
- Season: Nov-Mar only (UK icing season)

Author: AI Coding Agent
Date: December 30, 2025
"""

import time
from datetime import datetime, timedelta
import requests
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def fetch_openmeteo_weather(lat, lon, start_date, end_date, farm_name):
    """
    Fetch historical weather data from Open-Meteo Archive API.
    
    Variables for icing detection:
    - temperature_2m: Air temperature at 2m (°C)
    - relative_humidity_2m: Relative humidity at 2m (%)
    - precipitation: Total precipitation (mm)
    - cloud_cover: Cloud cover (%)
    - pressure_msl: Mean sea level pressure (hPa)
    - shortwave_radiation: Solar radiation (W/m²)
    """
    
    # Open-Meteo Archive API for historical data
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
        print(f"  Fetching {farm_name}: {start_date} to {end_date}")
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()
        
        data = response.json()
        
        if "hourly" not in data:
            print(f"  ❌ No hourly data returned for {farm_name}")
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
            print(f"  ⚠️  Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return fetch_openmeteo_weather(lat, lon, start_date, end_date, farm_name)
        else:
            print(f"  ❌ HTTP error for {farm_name}: {e}")
            return None
    except Exception as e:
        print(f"  ❌ Error for {farm_name}: {e}")
        return None

def main():
    print("="*70)
    print("ERA5 Weather Data Download for Icing Detection (Todo #4)")
    print("="*70)
    print("Variables: temperature, humidity, precipitation, cloud cover,")
    print("           pressure, solar radiation")
    print("Period: 2021-01-01 to 2025-12-30")
    print("="*70)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get farm locations from existing data
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
    print(f"Expected records: {len(farms_df)} farms × ~43,800 hours = ~2.1M records")
    print(f"Estimated download time: 2-3 hours (API rate limits)\n")
    
    # Download in chunks to avoid rate limits
    all_data = []
    start_time = time.time()
    
    # Split into yearly chunks to manage API limits
    date_ranges = [
        ("2021-01-01", "2021-12-31"),
        ("2022-01-01", "2022-12-31"),
        ("2023-01-01", "2023-12-31"),
        ("2024-01-01", "2024-12-31"),
        ("2025-01-01", "2025-12-30")
    ]
    
    for year_idx, (start_date, end_date) in enumerate(date_ranges, 1):
        print(f"\n{'='*70}")
        print(f"Year {year_idx}/5: {start_date} to {end_date}")
        print(f"{'='*70}")
        
        year_data = []
        
        for idx, row in farms_df.iterrows():
            farm_name = row['farm_name']
            lat = row['latitude']
            lon = row['longitude']
            
            df = fetch_openmeteo_weather(lat, lon, start_date, end_date, farm_name)
            
            if df is not None and len(df) > 0:
                year_data.append(df)
            
            # Rate limiting: 10 requests per minute for free tier
            if (idx + 1) % 10 == 0:
                print(f"  ⏸️  Rate limit pause (10 requests)...")
                time.sleep(65)  # Wait 65 seconds
        
        if year_data:
            year_combined = pd.concat(year_data, ignore_index=True)
            all_data.append(year_combined)
            print(f"\n✅ Year {year_idx} complete: {len(year_combined):,} records")
    
    if not all_data:
        print("\n❌ No data downloaded!")
        return
    
    # Combine all years
    print(f"\n{'='*70}")
    print("Combining all data...")
    print(f"{'='*70}")
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print(f"\n✅ Total records downloaded: {len(combined_df):,}")
    print(f"⏱️  Total time: {(time.time() - start_time) / 60:.1f} minutes")
    
    # Basic validation
    print(f"\n{'='*70}")
    print("Data Validation:")
    print(f"{'='*70}")
    print(f"Date range: {combined_df['time_utc'].min()} to {combined_df['time_utc'].max()}")
    print(f"Farms: {combined_df['farm_name'].nunique()}")
    print(f"Null values:")
    print(combined_df.isnull().sum())
    
    print(f"\nTemperature stats (for icing validation):")
    print(f"  Min: {combined_df['temperature_2m'].min():.1f}°C")
    print(f"  Mean: {combined_df['temperature_2m'].mean():.1f}°C")
    print(f"  Max: {combined_df['temperature_2m'].max():.1f}°C")
    print(f"  Icing range (-3 to +2°C): {((combined_df['temperature_2m'] >= -3) & (combined_df['temperature_2m'] <= 2)).sum():,} hours ({((combined_df['temperature_2m'] >= -3) & (combined_df['temperature_2m'] <= 2)).sum() / len(combined_df) * 100:.1f}%)")
    
    print(f"\nHumidity stats (for icing validation):")
    print(f"  Min: {combined_df['relative_humidity_2m'].min():.1f}%")
    print(f"  Mean: {combined_df['relative_humidity_2m'].mean():.1f}%")
    print(f"  Max: {combined_df['relative_humidity_2m'].max():.1f}%")
    print(f"  High humidity (>92%): {(combined_df['relative_humidity_2m'] > 92).sum():,} hours ({(combined_df['relative_humidity_2m'] > 92).sum() / len(combined_df) * 100:.1f}%)")
    
    # Upload to BigQuery
    print(f"\n{'='*70}")
    print("Uploading to BigQuery...")
    print(f"{'='*70}")
    
    table_id = f"{PROJECT_ID}.{DATASET}.era5_weather_icing"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
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
    
    job = client.load_table_from_dataframe(combined_df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded {len(combined_df):,} records to {table_id}")
    
    # Check for icing conditions
    print(f"\n{'='*70}")
    print("Potential Icing Conditions Analysis:")
    print(f"{'='*70}")
    
    icing_conditions = (
        (combined_df['temperature_2m'] >= -3) & 
        (combined_df['temperature_2m'] <= 2) &
        (combined_df['relative_humidity_2m'] > 92) &
        (combined_df['precipitation'] > 0)
    )
    
    icing_df = combined_df[icing_conditions].copy()
    icing_df['month'] = icing_df['time_utc'].dt.month
    
    print(f"\nTotal potential icing hours: {len(icing_df):,} ({len(icing_df) / len(combined_df) * 100:.2f}%)")
    print(f"\nBy month:")
    monthly_icing = icing_df.groupby('month').size()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for month_num, count in monthly_icing.items():
        print(f"  {months[month_num-1]}: {count:,} hours")
    
    print(f"\n{'='*70}")
    print("✅ ERA5 WEATHER DATA DOWNLOAD COMPLETE")
    print(f"{'='*70}")
    print(f"Table: {table_id}")
    print(f"Records: {len(combined_df):,}")
    print(f"Next: Retrain icing classifier with weather data")
    print(f"      python3 icing_risk_pipeline_parallel.py")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
