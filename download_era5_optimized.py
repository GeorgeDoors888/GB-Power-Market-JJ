#!/usr/bin/env python3
"""
Optimized ERA5 Weather Data Download - Smaller chunks, longer delays
Handles rate limiting gracefully with exponential backoff
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
        logging.FileHandler('/tmp/era5_optimized.log'),
        logging.StreamHandler()
    ]
)

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_weather_data"

# Rate limiting: 1 request per 5 seconds = 720 requests/hour (well under limit)
REQUEST_DELAY = 5  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 120  # 2 minutes between retries

# Download in smaller 6-month chunks instead of full years
CHUNK_MONTHS = 6

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

def download_era5_chunk(farm: Dict, start_date: str, end_date: str) -> pd.DataFrame:
    """Download ERA5 data for a single farm and date range with rate limiting"""
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": farm["lat"],
        "longitude": farm["lon"],
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_100m,wind_direction_100m",
        "timezone": "Europe/London"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"  Fetching {farm['name']}: {start_date} to {end_date} (attempt {attempt+1}/{MAX_RETRIES})")
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
            
            df = pd.DataFrame({
                "farm_name": farm["name"],
                "timestamp": pd.to_datetime(data["hourly"]["time"]),
                "temperature_2m": data["hourly"]["temperature_2m"],
                "relative_humidity_2m": data["hourly"]["relative_humidity_2m"],
                "precipitation": data["hourly"]["precipitation"],
                "cloud_cover": data["hourly"]["cloud_cover"],
                "wind_speed_100m": data["hourly"]["wind_speed_100m"],
                "wind_direction_100m": data["hourly"]["wind_direction_100m"],
            })
            
            logging.info(f"  ✅ Downloaded {len(df)} rows for {farm['name']}")
            time.sleep(REQUEST_DELAY)  # Rate limiting delay
            return df
            
        except requests.exceptions.RequestException as e:
            logging.error(f"  ❌ Error fetching {farm['name']}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"  ❌ Max retries exceeded for {farm['name']}, skipping chunk")
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
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
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
    logging.info("=== ERA5 OPTIMIZED DOWNLOAD STARTING ===")
    logging.info(f"Farms: {len(WIND_FARMS)}")
    logging.info(f"Date range: 2021-01-01 to 2025-12-31")
    logging.info(f"Chunk size: {CHUNK_MONTHS} months")
    logging.info(f"Request delay: {REQUEST_DELAY} seconds")
    logging.info(f"Max retries: {MAX_RETRIES}")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Create table if not exists
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    schema = [
        bigquery.SchemaField("farm_name", "STRING"),
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
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
        logging.info(f"Table already exists or creation error: {e}")
    
    # Generate 6-month chunks from 2021-01-01 to 2025-12-31
    start = datetime(2021, 1, 1)
    end = datetime(2025, 12, 31)
    
    chunks = []
    current = start
    while current < end:
        chunk_end = min(current + timedelta(days=CHUNK_MONTHS * 30), end)
        chunks.append((current.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
        current = chunk_end + timedelta(days=1)
    
    logging.info(f"Total chunks: {len(chunks)} × {len(WIND_FARMS)} farms = {len(chunks) * len(WIND_FARMS)} downloads")
    logging.info(f"Estimated time: {len(chunks) * len(WIND_FARMS) * REQUEST_DELAY / 3600:.1f} hours")
    
    total_rows = 0
    for farm in WIND_FARMS:
        logging.info(f"\n📍 Processing farm: {farm['name']}")
        
        for chunk_start, chunk_end in chunks:
            df = download_era5_chunk(farm, chunk_start, chunk_end)
            
            if not df.empty:
                upload_to_bigquery(df, client)
                total_rows += len(df)
                logging.info(f"  Progress: {total_rows:,} total rows downloaded")
    
    logging.info(f"\n=== DOWNLOAD COMPLETE ===")
    logging.info(f"Total rows: {total_rows:,}")
    logging.info(f"Farms: {len(WIND_FARMS)}")

if __name__ == "__main__":
    main()
