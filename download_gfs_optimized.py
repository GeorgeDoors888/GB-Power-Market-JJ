#!/usr/bin/env python3
"""
Optimized GFS Forecasts Download - Better rate limiting
Downloads 7-day forecasts for wind farms
"""

import time
import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
from typing import List, Dict
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/gfs_optimized.log'),
        logging.StreamHandler()
    ]
)

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "gfs_forecasts"

REQUEST_DELAY = 3  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 60

WIND_FARMS = [
    {"name": "Hornsea Two", "lat": 53.9167, "lon": 1.7833},
    {"name": "Hornsea One", "lat": 53.8667, "lon": 1.7167},
    {"name": "Dogger Bank A", "lat": 55.0500, "lon": 2.0000},
    {"name": "Dogger Bank B", "lat": 55.0000, "lon": 2.2000},
    {"name": "Walney Extension", "lat": 54.0333, "lon": -3.5333},
    {"name": "London Array", "lat": 51.6500, "lon": 1.3167},
    {"name": "Triton Knoll", "lat": 53.3667, "lon": 0.6167},
    {"name": "Race Bank", "lat": 53.2667, "lon": 0.5833},
    {"name": "Rampion", "lat": 50.6667, "lon": -0.3833},
    {"name": "Beatrice", "lat": 58.2000, "lon": -3.0833},
]

def download_gfs_forecast(farm: Dict) -> pd.DataFrame:
    """Download 7-day GFS forecast for a single farm"""
    url = "https://api.open-meteo.com/v1/gfs"
    
    params = {
        "latitude": farm["lat"],
        "longitude": farm["lon"],
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_100m,wind_direction_100m",
        "forecast_days": 7,
        "timezone": "Europe/London"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"  Fetching {farm['name']} (attempt {attempt+1}/{MAX_RETRIES})")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                wait_time = RETRY_DELAY * (attempt + 1)
                logging.warning(f"  ⚠️  Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            if "hourly" not in data:
                logging.warning(f"  ⚠️  No hourly data returned for {farm['name']}")
                return pd.DataFrame()
            
            forecast_times = pd.to_datetime(data["hourly"]["time"])
            forecast_time = datetime.now()
            
            df = pd.DataFrame({
                "farm_name": farm["name"],
                "forecast_time": forecast_time,
                "valid_time": forecast_times,
                "forecast_hour": [(t - forecast_time).total_seconds() / 3600 for t in forecast_times],
                "temperature_2m": data["hourly"]["temperature_2m"],
                "relative_humidity_2m": data["hourly"]["relative_humidity_2m"],
                "precipitation": data["hourly"]["precipitation"],
                "cloud_cover": data["hourly"]["cloud_cover"],
                "wind_speed_100m": data["hourly"]["wind_speed_100m"],
                "wind_direction_100m": data["hourly"]["wind_direction_100m"],
            })
            
            logging.info(f"  ✅ Downloaded {len(df)} rows for {farm['name']}")
            time.sleep(REQUEST_DELAY)
            return df
            
        except requests.exceptions.RequestException as e:
            logging.error(f"  ❌ Error fetching {farm['name']}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"  ❌ Max retries exceeded for {farm['name']}, skipping")
                return pd.DataFrame()
    
    return pd.DataFrame()

def upload_to_bigquery(df: pd.DataFrame, client: bigquery.Client):
    """Upload dataframe to BigQuery"""
    if df.empty:
        logging.warning("  ⚠️  Empty dataframe, skipping upload")
        return
    
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=[
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("forecast_time", "TIMESTAMP"),
            bigquery.SchemaField("valid_time", "TIMESTAMP"),
            bigquery.SchemaField("forecast_hour", "FLOAT64"),
            bigquery.SchemaField("temperature_2m", "FLOAT64"),
            bigquery.SchemaField("relative_humidity_2m", "FLOAT64"),
            bigquery.SchemaField("precipitation", "FLOAT64"),
            bigquery.SchemaField("cloud_cover", "FLOAT64"),
            bigquery.SchemaField("wind_speed_100m", "FLOAT64"),
            bigquery.SchemaField("wind_direction_100m", "FLOAT64"),
        ]
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logging.info(f"  ✅ Uploaded {len(df)} rows to BigQuery")
    except Exception as e:
        logging.error(f"  ❌ Upload error: {e}")

def main():
    logging.info("=== GFS OPTIMIZED DOWNLOAD STARTING ===")
    logging.info(f"Farms: {len(WIND_FARMS)}")
    logging.info(f"Forecast horizon: 7 days")
    logging.info(f"Request delay: {REQUEST_DELAY} seconds")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Create table if not exists
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    schema = [
        bigquery.SchemaField("farm_name", "STRING"),
        bigquery.SchemaField("forecast_time", "TIMESTAMP"),
        bigquery.SchemaField("valid_time", "TIMESTAMP"),
        bigquery.SchemaField("forecast_hour", "FLOAT64"),
        bigquery.SchemaField("temperature_2m", "FLOAT64"),
        bigquery.SchemaField("relative_humidity_2m", "FLOAT64"),
        bigquery.SchemaField("precipitation", "FLOAT64"),
        bigquery.SchemaField("cloud_cover", "FLOAT64"),
        bigquery.SchemaField("wind_speed_100m", "FLOAT64"),
        bigquery.SchemaField("wind_direction_100m", "FLOAT64"),
    ]
    
    try:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        logging.info(f"✅ Created table {table_id}")
    except Exception as e:
        logging.info(f"Table already exists: {e}")
    
    total_rows = 0
    for farm in WIND_FARMS:
        logging.info(f"\n📍 Processing farm: {farm['name']}")
        df = download_gfs_forecast(farm)
        
        if not df.empty:
            upload_to_bigquery(df, client)
            total_rows += len(df)
            logging.info(f"  Progress: {total_rows:,} total rows")
    
    logging.info(f"\n=== DOWNLOAD COMPLETE ===")
    logging.info(f"Total rows: {total_rows:,}")

if __name__ == "__main__":
    main()
