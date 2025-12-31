#!/usr/bin/env python3
"""
Incremental ERA5 weather data download (daily updates only).
Downloads only new data since last BigQuery update.
Run daily at 03:00 UTC via cron.
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_weather_icing"
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"


def get_last_date():
    """Get the most recent date in BigQuery table."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT MAX(DATE(time_utc)) as last_date
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df['last_date'][0]
    except Exception as e:
        print(f"⚠️  Error getting last date: {e}")
        return None


def get_farm_coordinates():
    """Get wind farm coordinates from existing data."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT
        farm_name,
        latitude,
        longitude
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    ORDER BY farm_name
    """
    
    df = client.query(query).to_dataframe()
    return [(row.farm_name, row.latitude, row.longitude) for _, row in df.iterrows()]


def download_weather_for_farm(farm_name, latitude, longitude, start_date, end_date):
    """Download weather data for one farm and date range."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "cloud_cover",
            "pressure_msl",
            "shortwave_radiation"
        ]),
        "timezone": "UTC",
    }
    
    try:
        response = requests.get(ARCHIVE_API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if "hourly" not in data:
            return pd.DataFrame()
        
        hourly = data["hourly"]
        df = pd.DataFrame({
            "farm_name": farm_name,
            "latitude": latitude,
            "longitude": longitude,
            "time_utc": pd.to_datetime(hourly["time"]),
            "temperature_2m": hourly.get("temperature_2m"),
            "relative_humidity_2m": hourly.get("relative_humidity_2m"),
            "precipitation": hourly.get("precipitation"),
            "cloud_cover": hourly.get("cloud_cover"),
            "pressure_msl": hourly.get("pressure_msl"),
            "shortwave_radiation": hourly.get("shortwave_radiation"),
        })
        
        return df
    
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return pd.DataFrame()


def upload_to_bigquery(df):
    """Upload incremental data to BigQuery (append mode)."""
    if df.empty:
        print("⚪ No data to upload")
        return
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    print(f"📤 Uploading {len(df):,} records to BigQuery...")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded to {table_id}")


def main():
    """Download incremental ERA5 weather data."""
    print("="*80)
    print("ERA5 Weather - Incremental Update")
    print("="*80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Get last date in BigQuery
    last_date = get_last_date()
    
    if last_date is None:
        print("❌ Could not determine last date - run full download first")
        sys.exit(1)
    
    print(f"Last data in BigQuery: {last_date}")
    
    # ERA5 has T-5 days lag, so download T-5 to T-1
    end_date = datetime.now().date() - timedelta(days=1)
    start_date = last_date + timedelta(days=1)
    
    if start_date > end_date:
        print(f"✅ Already up to date (last: {last_date})")
        sys.exit(0)
    
    print(f"Downloading: {start_date} to {end_date}")
    days_to_download = (end_date - start_date).days + 1
    print(f"Days: {days_to_download}")
    print()
    
    # Get farm coordinates
    farms = get_farm_coordinates()
    print(f"Farms: {len(farms)}")
    print()
    
    # Download data for each farm
    all_data = []
    
    for i, (farm_name, lat, lon) in enumerate(farms, 1):
        print(f"[{i}/{len(farms)}] {farm_name}")
        
        df = download_weather_for_farm(farm_name, lat, lon, start_date, end_date)
        
        if not df.empty:
            print(f"  ✅ {len(df):,} records")
            all_data.append(df)
        else:
            print(f"  ⚠️  No data")
        
        # Rate limiting (10 req/min for free tier)
        if i < len(farms):
            time.sleep(6)
    
    # Combine and upload
    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        print(f"\n✅ Total new records: {len(df_combined):,}")
        upload_to_bigquery(df_combined)
    else:
        print("\n⚠️  No new data downloaded")
    
    print("\n" + "="*80)
    print(f"✅ Incremental update complete - now up to {end_date}")
    print("="*80)


if __name__ == "__main__":
    main()
