#!/usr/bin/env python3
"""
ERA5 CDS Historical Weather Data Downloader
Downloads temperature, humidity, precipitation, cloud cover, and wind data
for UK wind farms from Copernicus Climate Data Store (CDS).

Data Source: ERA5 hourly data on single levels from 1940 to present
Provider: Copernicus Climate Change Service (C3S)
Copyright: © ECMWF
License: CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)
DOI: 10.24381/cds.adbb2d47
Dataset ID: reanalysis-era5-single-levels

Requirements:
    pip3 install cdsapi netCDF4 xarray google-cloud-bigquery pandas

Setup (5 minutes):
    1. Register: https://cds.climate.copernicus.eu/user/register
    2. Login: https://cds.climate.copernicus.eu/user/login
    3. Get API key: https://cds.climate.copernicus.eu/api-how-to
    4. Create ~/.cdsapirc:
       url: https://cds.climate.copernicus.eu/api/v2
       key: YOUR_UID:YOUR_API_KEY
"""

import cdsapi
import xarray as xr
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import os
import logging
from pathlib import Path

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "era5_weather_data"
LOCATION = "US"

# Date range (matching existing ERA5 wind upstream: 2020-01-01 to 2025-12-30)
START_DATE = "2020-01-01"
END_DATE = "2025-12-30"

# Download in 1-month chunks to avoid CDS "request too large" errors
CHUNK_MONTHS = 1

# ERA5 variables for icing detection + wind forecasting
VARIABLES = [
    '2m_temperature',           # Temperature at 2m (K) - for icing detection
    '2m_dewpoint_temperature',  # Dewpoint at 2m (K) - for humidity calculation
    'total_precipitation',      # Precipitation (m) - for icing detection
    'total_cloud_cover',        # Cloud cover (0-1) - for icing detection
    '100m_u_component_of_wind', # Wind U at 100m (m/s) - for wind shear
    '100m_v_component_of_wind', # Wind V at 100m (m/s) - for wind shear
]

# UK Wind Farms (41 farms)
WIND_FARMS = {
    'Beatrice': {'lat': 58.25, 'lon': -3.00},
    'Moray East': {'lat': 58.15, 'lon': -2.80},
    'Seagreen Phase 1': {'lat': 56.55, 'lon': -1.75},
    'Neart na Gaoithe': {'lat': 56.30, 'lon': -1.90},
    'Inch Cape': {'lat': 56.45, 'lon': -2.05},
    'Beatrice extension': {'lat': 58.30, 'lon': -3.05},
    'Moray West': {'lat': 58.20, 'lon': -2.95},
    'Kincardine': {'lat': 56.70, 'lon': -2.30},
    'Hywind Scotland': {'lat': 57.50, 'lon': -1.85},
    'EOWDC': {'lat': 57.15, 'lon': -1.95},
    'Hornsea One': {'lat': 53.90, 'lon': 1.75},
    'Hornsea Two': {'lat': 53.95, 'lon': 1.65},
    'Hornsea Three': {'lat': 54.15, 'lon': 1.40},
    'Dogger Bank A': {'lat': 55.15, 'lon': 1.35},
    'Dogger Bank B': {'lat': 55.25, 'lon': 1.50},
    'Dogger Bank C': {'lat': 55.05, 'lon': 1.20},
    'East Anglia One': {'lat': 52.05, 'lon': 2.05},
    'East Anglia Three': {'lat': 52.25, 'lon': 2.15},
    'Triton Knoll': {'lat': 53.40, 'lon': 0.75},
    'Greater Gabbard': {'lat': 51.95, 'lon': 2.00},
    'Galloper': {'lat': 51.90, 'lon': 2.10},
    'London Array': {'lat': 51.65, 'lon': 1.50},
    'Thanet': {'lat': 51.45, 'lon': 1.60},
    'Rampion': {'lat': 50.65, 'lon': -0.25},
    'Westermost Rough': {'lat': 53.80, 'lon': 0.15},
    'Lincs': {'lat': 53.30, 'lon': 0.50},
    'Lynn and Inner Dowsing': {'lat': 53.15, 'lon': 0.35},
    'Race Bank': {'lat': 53.25, 'lon': 0.60},
    'Sheringham Shoal': {'lat': 53.00, 'lon': 0.95},
    'Dudgeon': {'lat': 53.25, 'lon': 1.30},
    'Scroby Sands': {'lat': 52.65, 'lon': 1.75},
    'Gwynt y Môr': {'lat': 53.45, 'lon': -3.55},
    'Rhyl Flats': {'lat': 53.35, 'lon': -3.50},
    'North Hoyle': {'lat': 53.40, 'lon': -3.45},
    'Burbo Bank': {'lat': 53.50, 'lon': -3.20},
    'Burbo Bank Extension': {'lat': 53.52, 'lon': -3.25},
    'Walney 1': {'lat': 54.05, 'lon': -3.50},
    'Walney 2': {'lat': 54.05, 'lon': -3.50},
    'Walney Extension': {'lat': 54.10, 'lon': -3.60},
    'Ormonde': {'lat': 54.10, 'lon': -3.45},
    'West of Duddon Sands': {'lat': 54.00, 'lon': -3.40},
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/era5_cds_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_cds_client():
    """Initialize CDS API client."""
    try:
        client = cdsapi.Client()
        logger.info("✅ CDS API client initialized")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize CDS client: {e}")
        logger.error("Setup instructions:")
        logger.error("1. Register: https://cds.climate.copernicus.eu/user/register")
        logger.error("2. Get API key: https://cds.climate.copernicus.eu/api-how-to")
        logger.error("3. Create ~/.cdsapirc with your UID:API_KEY")
        raise

def generate_date_chunks(start_date, end_date, chunk_months=6):
    """Generate date chunks for downloading."""
    chunks = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    while current <= end:
        chunk_end = current + timedelta(days=chunk_months * 30)
        if chunk_end > end:
            chunk_end = end
        
        chunks.append({
            'start': current.strftime('%Y-%m-%d'),
            'end': chunk_end.strftime('%Y-%m-%d')
        })
        
        current = chunk_end + timedelta(days=1)
    
    return chunks

def download_era5_chunk(client, farm_name, farm_coords, start_date, end_date, output_file):
    """Download ERA5 data for one farm and one time chunk."""
    
    # Create bounding box around farm (±0.25° = ~31km)
    north = farm_coords['lat'] + 0.25
    south = farm_coords['lat'] - 0.25
    east = farm_coords['lon'] + 0.25
    west = farm_coords['lon'] - 0.25
    
    request = {
        'product_type': 'reanalysis',
        'variable': VARIABLES,
        'year': [str(y) for y in range(
            int(start_date.split('-')[0]), 
            int(end_date.split('-')[0]) + 1
        )],
        'month': [f'{m:02d}' for m in range(1, 13)],
        'day': [f'{d:02d}' for d in range(1, 32)],
        'time': [f'{h:02d}:00' for h in range(0, 24)],
        'area': [north, west, south, east],  # North, West, South, East
        'format': 'netcdf',
    }
    
    logger.info(f"📥 Downloading {farm_name}: {start_date} to {end_date}")
    logger.info(f"   Area: [{north:.2f}N, {west:.2f}W, {south:.2f}S, {east:.2f}E]")
    
    try:
        client.retrieve('reanalysis-era5-single-levels', request, output_file)
        logger.info(f"✅ Downloaded {farm_name} chunk to {output_file}")
        return True
    except Exception as e:
        logger.error(f"❌ Download failed for {farm_name}: {e}")
        return False

def parse_netcdf_to_dataframe(netcdf_file, farm_name, farm_coords):
    """Parse NetCDF file to pandas DataFrame."""
    logger.info(f"📊 Parsing {netcdf_file}...")
    
    try:
        ds = xr.open_dataset(netcdf_file)
        
        # Extract data
        df = pd.DataFrame({
            'farm_name': farm_name,
            'time_utc': pd.to_datetime(ds['time'].values),
            'latitude': farm_coords['lat'],
            'longitude': farm_coords['lon'],
            'temperature_2m': ds['t2m'].values.flatten() - 273.15,  # K to °C
            'dewpoint_2m': ds['d2m'].values.flatten() - 273.15,     # K to °C
            'precipitation': ds['tp'].values.flatten() * 1000,       # m to mm
            'cloud_cover': ds['tcc'].values.flatten() * 100,         # 0-1 to %
            'wind_u_100m': ds['u100'].values.flatten(),              # m/s
            'wind_v_100m': ds['v100'].values.flatten(),              # m/s
        })
        
        # Calculate derived variables
        df['relative_humidity_2m'] = calculate_relative_humidity(
            df['temperature_2m'], 
            df['dewpoint_2m']
        )
        df['wind_speed_100m'] = (df['wind_u_100m']**2 + df['wind_v_100m']**2)**0.5
        df['wind_direction_100m'] = (180 + (180/3.14159) * 
            pd.Series([0] * len(df)).apply(lambda x: 
                __import__('math').atan2(df['wind_u_100m'], df['wind_v_100m'])
            )
        ) % 360
        
        logger.info(f"✅ Parsed {len(df)} rows for {farm_name}")
        
        ds.close()
        return df
        
    except Exception as e:
        logger.error(f"❌ Failed to parse {netcdf_file}: {e}")
        return None

def calculate_relative_humidity(temp_c, dewpoint_c):
    """Calculate relative humidity from temperature and dewpoint (Magnus formula)."""
    import numpy as np
    
    # Magnus formula constants
    a = 17.27
    b = 237.7
    
    alpha_t = (a * temp_c) / (b + temp_c)
    alpha_td = (a * dewpoint_c) / (b + dewpoint_c)
    
    rh = 100 * np.exp(alpha_td - alpha_t)
    
    return np.clip(rh, 0, 100)  # Clip to 0-100%

def upload_to_bigquery(df, project_id, dataset, table, location='US'):
    """Upload DataFrame to BigQuery."""
    if df is None or len(df) == 0:
        logger.warning("⚠️ No data to upload")
        return False
    
    try:
        client = bigquery.Client(project=project_id, location=location)
        table_id = f"{project_id}.{dataset}.{table}"
        
        # Define schema
        schema = [
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("time_utc", "TIMESTAMP"),
            bigquery.SchemaField("latitude", "FLOAT64"),
            bigquery.SchemaField("longitude", "FLOAT64"),
            bigquery.SchemaField("temperature_2m", "FLOAT64", description="Temperature at 2m (°C)"),
            bigquery.SchemaField("dewpoint_2m", "FLOAT64", description="Dewpoint at 2m (°C)"),
            bigquery.SchemaField("relative_humidity_2m", "FLOAT64", description="Relative humidity (%)"),
            bigquery.SchemaField("precipitation", "FLOAT64", description="Total precipitation (mm)"),
            bigquery.SchemaField("cloud_cover", "FLOAT64", description="Total cloud cover (%)"),
            bigquery.SchemaField("wind_u_100m", "FLOAT64", description="Wind U component at 100m (m/s)"),
            bigquery.SchemaField("wind_v_100m", "FLOAT64", description="Wind V component at 100m (m/s)"),
            bigquery.SchemaField("wind_speed_100m", "FLOAT64", description="Wind speed at 100m (m/s)"),
            bigquery.SchemaField("wind_direction_100m", "FLOAT64", description="Wind direction at 100m (degrees)"),
        ]
        
        # Table metadata with CC-BY-4.0 attribution
        table_obj = bigquery.Table(table_id, schema=schema)
        table_obj.description = """
ERA5 hourly weather data for UK wind farms (2020-2025).
Includes temperature, humidity, precipitation, cloud cover, and wind data for icing detection.

Data Source: ERA5 hourly data on single levels from 1940 to present
Provider: Copernicus Climate Change Service (C3S)
Copyright: © ECMWF
License: CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)
DOI: 10.24381/cds.adbb2d47
Dataset ID: reanalysis-era5-single-levels
Downloaded: {datetime.now().strftime('%Y-%m-%d')}
        """.strip()
        
        # Create table if not exists
        try:
            client.get_table(table_id)
            logger.info(f"✅ Table {table_id} exists")
        except:
            table_obj = client.create_table(table_obj)
            logger.info(f"✅ Created table {table_id}")
        
        # Upload data
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition='WRITE_APPEND',
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        logger.info(f"✅ Uploaded {len(df)} rows to {table_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery upload failed: {e}")
        return False

def main():
    """Main download and upload pipeline."""
    logger.info("="*80)
    logger.info("ERA5 CDS HISTORICAL WEATHER DATA DOWNLOAD")
    logger.info("="*80)
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info(f"Farms: {len(WIND_FARMS)}")
    logger.info(f"Variables: {len(VARIABLES)}")
    logger.info(f"Chunk size: {CHUNK_MONTHS} months")
    logger.info("")
    
    # Initialize CDS client
    cds_client = init_cds_client()
    
    # Generate date chunks
    chunks = generate_date_chunks(START_DATE, END_DATE, CHUNK_MONTHS)
    logger.info(f"📅 Total chunks: {len(chunks)}")
    
    # Track progress
    total_farms = len(WIND_FARMS)
    total_chunks = len(chunks)
    total_operations = total_farms * total_chunks
    completed = 0
    failed = 0
    
    # Create temp directory for NetCDF files
    temp_dir = Path('/tmp/era5_cds')
    temp_dir.mkdir(exist_ok=True)
    
    # Process each farm
    for farm_idx, (farm_name, farm_coords) in enumerate(WIND_FARMS.items(), 1):
        logger.info("")
        logger.info(f"🌬️ Farm {farm_idx}/{total_farms}: {farm_name}")
        logger.info(f"   Location: {farm_coords['lat']:.2f}°N, {farm_coords['lon']:.2f}°E")
        
        # Process each time chunk
        for chunk_idx, chunk in enumerate(chunks, 1):
            output_file = temp_dir / f"{farm_name.replace(' ', '_')}_{chunk['start']}_{chunk['end']}.nc"
            
            # Download chunk
            success = download_era5_chunk(
                cds_client, 
                farm_name, 
                farm_coords, 
                chunk['start'], 
                chunk['end'], 
                str(output_file)
            )
            
            if not success:
                failed += 1
                logger.error(f"❌ Chunk {chunk_idx}/{total_chunks} failed")
                continue
            
            # Parse NetCDF
            df = parse_netcdf_to_dataframe(output_file, farm_name, farm_coords)
            
            if df is None:
                failed += 1
                logger.error(f"❌ Parsing failed for chunk {chunk_idx}/{total_chunks}")
                continue
            
            # Upload to BigQuery
            upload_success = upload_to_bigquery(df, PROJECT_ID, DATASET, TABLE, LOCATION)
            
            if upload_success:
                completed += 1
                logger.info(f"✅ Chunk {chunk_idx}/{total_chunks} complete ({completed}/{total_operations})")
            else:
                failed += 1
                logger.error(f"❌ Upload failed for chunk {chunk_idx}/{total_chunks}")
            
            # Clean up NetCDF file
            output_file.unlink()
            
            # Rate limiting: CDS allows ~10 requests/hour for free tier
            # Wait 6 minutes between requests to stay safe
            if chunk_idx < len(chunks):
                wait_time = 400  # 6.7 minutes (extra safe for 1-month chunks)
                logger.info(f"⏳ Waiting {wait_time}s before next request (CDS rate limiting)...")
                time.sleep(wait_time)
    
    # Final summary
    logger.info("")
    logger.info("="*80)
    logger.info("=== DOWNLOAD COMPLETE ===")
    logger.info(f"Total operations: {total_operations}")
    logger.info(f"Completed: {completed} ({100*completed/total_operations:.1f}%)")
    logger.info(f"Failed: {failed} ({100*failed/total_operations:.1f}%)")
    logger.info("="*80)

if __name__ == "__main__":
    main()
