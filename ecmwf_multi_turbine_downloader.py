#!/usr/bin/env python3
"""
ECMWF Multi-Turbine Wind Forecast Downloader
Downloads ECMWF IFS SCDA 10m wind forecasts for all offshore wind farms in parallel
Converts to GB settlement periods and uploads to BigQuery

Based on: ecmwf_scda_wind_to_settlement_periods.py
Enhanced: Parallel downloads for 43 offshore wind farms
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import cfgrib
    import xarray as xr
except ImportError:
    print("ERROR: cfgrib/xarray not installed. Install with:")
    print("  pip3 install cfgrib eccodes xarray")
    sys.exit(1)

try:
    from google.cloud import bigquery
except ImportError:
    print("ERROR: google-cloud-bigquery not installed. Install with:")
    print("  pip3 install google-cloud-bigquery db-dtypes pyarrow")
    sys.exit(1)

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "ecmwf_wind_turbine_forecasts"
LOCATION = "US"

ECMWF_BASE_URL = "https://data.ecmwf.int/forecasts"
GRIB_DIR = Path("ecmwf_grib_files")
GRIB_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_offshore_wind_farms():
    """
    Fetch offshore wind farm locations from BigQuery
    Returns: DataFrame with name, latitude, longitude, capacity_mw, gsp_zone
    """
    logger.info("Fetching offshore wind farm locations from BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    query = f"""
    SELECT 
        name,
        latitude,
        longitude,
        capacity_mw,
        gsp_zone,
        status
    FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
    WHERE status = 'Operational'
      AND latitude IS NOT NULL
      AND longitude IS NOT NULL
    ORDER BY capacity_mw DESC
    """
    
    df = client.query(query).to_dataframe()
    logger.info(f"✅ Fetched {len(df)} offshore wind farms")
    logger.info(f"   Total capacity: {df['capacity_mw'].sum():.0f} MW")
    
    return df


def pick_latest_run(now_utc, candidate_cycles=["06", "18"]):
    """
    Pick the latest available ECMWF forecast run
    
    Args:
        now_utc: Current UTC datetime
        candidate_cycles: Preferred forecast cycles (06z and 18z recommended)
    
    Returns:
        tuple: (run_date, run_cycle_str)
    """
    for days_back in range(3):  # Try up to 3 days back
        run_date = (now_utc - timedelta(days=days_back)).date()
        
        for cycle in candidate_cycles:
            cycle_time = datetime.combine(run_date, datetime.min.time()) + timedelta(hours=int(cycle))
            
            # ECMWF data available ~4 hours after cycle time
            if now_utc >= cycle_time + timedelta(hours=4):
                logger.info(f"Selected forecast run: {run_date} {cycle}z")
                return run_date, cycle
    
    # Fallback to yesterday 18z
    fallback_date = (now_utc - timedelta(days=1)).date()
    logger.warning(f"No recent run found, using fallback: {fallback_date} 18z")
    return fallback_date, "18"


def download_grib(run_date, run_cycle, out_path):
    """
    Download ECMWF GRIB file
    
    Args:
        run_date: Date object
        run_cycle: Cycle string ('06' or '18')
        out_path: Path to save GRIB file
    
    Returns:
        Path to downloaded file
    """
    import requests
    
    date_str = run_date.strftime("%Y%m%d")
    grib_filename = f"{date_str}/{run_cycle}z/ifs/0p25/enfo/{date_str}{run_cycle}0000-0h-enfo-ef.grib2"
    
    url = f"{ECMWF_BASE_URL}/{grib_filename}"
    
    logger.info(f"Downloading GRIB from: {url}")
    
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    
    with open(out_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    file_size_mb = out_path.stat().st_size / (1024 * 1024)
    logger.info(f"✅ Downloaded {file_size_mb:.1f} MB to {out_path}")
    
    return out_path


def extract_wind_at_point(grib_path, lat, lon):
    """
    Extract U10/V10 wind components at single lat/lon point from GRIB file
    
    Args:
        grib_path: Path to GRIB file
        lat: Latitude
        lon: Longitude
    
    Returns:
        DataFrame with columns: valid_time, u10_ms, v10_ms, wind_speed_ms
    """
    # Open GRIB file with cfgrib
    ds_u10 = xr.open_dataset(grib_path, engine='cfgrib', 
                              backend_kwargs={'filter_by_keys': {'shortName': 'u10'}})
    ds_v10 = xr.open_dataset(grib_path, engine='cfgrib',
                              backend_kwargs={'filter_by_keys': {'shortName': 'v10'}})
    
    # Extract nearest point (ECMWF grid is 0.25° resolution)
    u10 = ds_u10.sel(latitude=lat, longitude=lon, method='nearest')['u10'].values
    v10 = ds_v10.sel(latitude=lat, longitude=lon, method='nearest')['v10'].values
    times = ds_u10['valid_time'].values
    
    # Calculate wind speed
    wind_speed = np.sqrt(u10**2 + v10**2)
    
    # Create DataFrame
    df = pd.DataFrame({
        'valid_time': times,
        'u10_ms': u10,
        'v10_ms': v10,
        'wind_speed_ms': wind_speed
    })
    
    ds_u10.close()
    ds_v10.close()
    
    return df


def interpolate_to_settlement_periods(wind_df):
    """
    Interpolate 3-hourly ECMWF data to 30-minute GB settlement periods
    
    Args:
        wind_df: DataFrame with valid_time, wind_speed_ms columns
    
    Returns:
        DataFrame with settlement_date, settlement_period, wind_speed_ms
    """
    wind_df = wind_df.copy()
    wind_df['valid_time'] = pd.to_datetime(wind_df['valid_time'])
    wind_df = wind_df.set_index('valid_time').sort_index()
    
    # Resample to 30-minute intervals (linear interpolation)
    wind_30min = wind_df.resample('30T').interpolate(method='linear')
    
    # Convert to GB settlement periods (1-48, starting at 00:00 UK time)
    # Note: ECMWF is in UTC, GB settlement periods follow UK local time (UTC or UTC+1)
    # For simplicity, assume UTC (winter time). Adjust for BST if needed.
    
    wind_30min = wind_30min.reset_index()
    wind_30min['settlement_date'] = wind_30min['valid_time'].dt.date
    wind_30min['hour'] = wind_30min['valid_time'].dt.hour
    wind_30min['minute'] = wind_30min['valid_time'].dt.minute
    
    # Settlement period calculation: SP = (hour * 2) + (minute // 30) + 1
    wind_30min['settlement_period'] = (wind_30min['hour'] * 2) + (wind_30min['minute'] // 30) + 1
    
    # Calculate ramp (change from previous SP)
    wind_30min['wind_ramp_ms'] = wind_30min['wind_speed_ms'].diff()
    wind_30min['ramp_flag'] = (wind_30min['wind_ramp_ms'].abs() > 2.0).astype(int)  # >2 m/s change
    
    # Calculate volatility (rolling std over 4 SPs = 2 hours)
    wind_30min['volatility_ms'] = wind_30min['wind_speed_ms'].rolling(window=4, min_periods=1).std()
    
    return wind_30min


def download_farm_forecast(farm_row, grib_path, forecast_run_time):
    """
    Download and process wind forecast for single farm
    
    Args:
        farm_row: pandas Series with farm data
        grib_path: Path to shared GRIB file
        forecast_run_time: Forecast run timestamp
    
    Returns:
        DataFrame with farm_name, forecast_run_utc, settlement_date, settlement_period, wind_speed_ms, etc.
    """
    farm_name = farm_row['name']
    lat = farm_row['latitude']
    lon = farm_row['longitude']
    
    try:
        # Extract wind at farm location
        wind_df = extract_wind_at_point(grib_path, lat, lon)
        
        # Interpolate to settlement periods
        wind_sp = interpolate_to_settlement_periods(wind_df)
        
        # Add metadata
        wind_sp['farm_name'] = farm_name
        wind_sp['forecast_run_utc'] = forecast_run_time
        wind_sp['capacity_mw'] = farm_row['capacity_mw']
        wind_sp['gsp_zone'] = farm_row['gsp_zone']
        wind_sp['ingested_utc'] = pd.Timestamp.now(tz='UTC')
        
        logger.info(f"  ✅ {farm_name}: {len(wind_sp)} settlement periods")
        
        return wind_sp
    
    except Exception as e:
        logger.error(f"  ❌ {farm_name}: {e}")
        return None


def upload_to_bigquery(df, table_id):
    """
    Upload wind forecast data to BigQuery
    
    Args:
        df: DataFrame with forecast data
        table_id: Full table ID (project.dataset.table)
    """
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    # Prepare schema
    schema = [
        bigquery.SchemaField("farm_name", "STRING"),
        bigquery.SchemaField("forecast_run_utc", "TIMESTAMP"),
        bigquery.SchemaField("settlement_date", "DATE"),
        bigquery.SchemaField("settlement_period", "INTEGER"),
        bigquery.SchemaField("valid_time", "TIMESTAMP"),
        bigquery.SchemaField("wind_speed_ms", "FLOAT"),
        bigquery.SchemaField("u10_ms", "FLOAT"),
        bigquery.SchemaField("v10_ms", "FLOAT"),
        bigquery.SchemaField("wind_ramp_ms", "FLOAT"),
        bigquery.SchemaField("ramp_flag", "INTEGER"),
        bigquery.SchemaField("volatility_ms", "FLOAT"),
        bigquery.SchemaField("capacity_mw", "FLOAT"),
        bigquery.SchemaField("gsp_zone", "STRING"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",  # Append to existing data
        schema=schema,
        schema_update_options=["ALLOW_FIELD_ADDITION"]
    )
    
    logger.info(f"Uploading {len(df)} rows to {table_id}...")
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    logger.info(f"✅ Uploaded to BigQuery: {len(df)} rows")


def create_deduplicated_view():
    """
    Create view to get latest forecast for each settlement period
    """
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    view_id = f"{PROJECT_ID}.{DATASET}.ecmwf_wind_latest"
    
    view_query = f"""
    SELECT
        farm_name,
        settlement_date,
        settlement_period,
        valid_time,
        wind_speed_ms,
        u10_ms,
        v10_ms,
        wind_ramp_ms,
        ramp_flag,
        volatility_ms,
        capacity_mw,
        gsp_zone,
        forecast_run_utc,
        ingested_utc
    FROM (
        SELECT *,
            ROW_NUMBER() OVER(
                PARTITION BY farm_name, settlement_date, settlement_period
                ORDER BY forecast_run_utc DESC, ingested_utc DESC
            ) as rn
        FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    )
    WHERE rn = 1  -- Keep only latest forecast
    """
    
    view = bigquery.Table(view_id)
    view.view_query = view_query
    
    try:
        client.create_table(view, exists_ok=True)
        logger.info(f"✅ Created/updated view: {view_id}")
    except Exception as e:
        logger.warning(f"View creation skipped: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download ECMWF wind forecasts for offshore wind farms")
    parser.add_argument('--test', action='store_true', help='Test mode: download for 5 farms only')
    parser.add_argument('--cycle', choices=['06', '18'], help='Force specific forecast cycle')
    parser.add_argument('--max-workers', type=int, default=10, help='Parallel download workers (default: 10)')
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("ECMWF Multi-Turbine Wind Forecast Downloader")
    logger.info("=" * 70)
    
    # Fetch offshore wind farms
    farms_df = fetch_offshore_wind_farms()
    
    if args.test:
        logger.info("🧪 TEST MODE: Using top 5 farms only")
        farms_df = farms_df.head(5)
    
    # Pick latest ECMWF run
    now_utc = datetime.now(timezone.utc)
    candidate_cycles = [args.cycle] if args.cycle else ["06", "18"]
    run_date, run_cycle = pick_latest_run(now_utc, candidate_cycles)
    
    forecast_run_time = datetime.combine(run_date, datetime.min.time()) + timedelta(hours=int(run_cycle))
    forecast_run_time = forecast_run_time.replace(tzinfo=timezone.utc)
    
    # Download GRIB file (shared for all farms)
    grib_filename = f"ecmwf_{run_date.strftime('%Y%m%d')}_{run_cycle}z.grib2"
    grib_path = GRIB_DIR / grib_filename
    
    if not grib_path.exists():
        try:
            download_grib(run_date, run_cycle, grib_path)
        except Exception as e:
            logger.error(f"Failed to download GRIB: {e}")
            return 1
    else:
        logger.info(f"Using cached GRIB file: {grib_path}")
    
    # Process farms in parallel
    logger.info(f"\n📡 Extracting wind data for {len(farms_df)} farms (parallel={args.max_workers})...")
    
    results = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {}
        
        for idx, farm_row in farms_df.iterrows():
            future = executor.submit(download_farm_forecast, farm_row, grib_path, forecast_run_time)
            futures[future] = farm_row['name']
        
        for future in as_completed(futures):
            farm_name = futures[future]
            try:
                result = future.result(timeout=60)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.error(f"  ❌ {farm_name}: {e}")
    
    if not results:
        logger.error("No data extracted - check GRIB file and coordinates")
        return 1
    
    # Combine all results
    logger.info(f"\n📊 Combining data from {len(results)} farms...")
    combined_df = pd.concat(results, ignore_index=True)
    
    logger.info(f"   Total rows: {len(combined_df)}")
    logger.info(f"   Date range: {combined_df['settlement_date'].min()} to {combined_df['settlement_date'].max()}")
    logger.info(f"   Forecast horizon: {(combined_df['settlement_date'].max() - combined_df['settlement_date'].min()).days} days")
    
    # Upload to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    upload_to_bigquery(combined_df, table_id)
    
    # Create deduplicated view
    create_deduplicated_view()
    
    logger.info("\n✅ COMPLETE - Wind forecast data uploaded to BigQuery")
    logger.info(f"   Table: {table_id}")
    logger.info(f"   View: {PROJECT_ID}.{DATASET}.ecmwf_wind_latest")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
