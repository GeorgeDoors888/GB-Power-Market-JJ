#!/usr/bin/env python3
"""
ERA5 CDS Optimized Download - Icing Season Priority
Downloads in small chunks to avoid CDS "request too large" errors.

Strategy:
1. Download icing season first (Nov-Mar, 2020-2025)
2. Download 2-3 variables per request (stays under CDS limits)
3. Download 1 month at a time per farm (matches CDS tape structure)
4. Then download remaining months (Apr-Oct)

Data Source: ERA5 hourly data on single levels
License: CC-BY-4.0 © ECMWF
DOI: 10.24381/cds.adbb2d47
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

# Storage directory for downloaded files (PERMANENT - files not deleted)
STORAGE_DIR = Path.home() / "era5_downloads" / "weather"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Icing season months (Nov-Mar) - PRIORITY
ICING_MONTHS = [11, 12, 1, 2, 3]
NON_ICING_MONTHS = [4, 5, 6, 7, 8, 9, 10]

# Date range
START_YEAR = 2020
END_YEAR = 2025

# Variable groups (download separately to stay under CDS limits)
VARIABLE_GROUPS = [
    {
        'name': 'temperature_humidity',
        'vars': ['2m_temperature', '2m_dewpoint_temperature'],
        'wait_seconds': 400  # 6.7 minutes
    },
    {
        'name': 'precipitation_cloud',
        'vars': ['total_precipitation', 'total_cloud_cover'],
        'wait_seconds': 400
    },
    {
        'name': 'wind_100m',
        'vars': ['100m_u_component_of_wind', '100m_v_component_of_wind'],
        'wait_seconds': 400
    },
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
        logging.FileHandler('/tmp/era5_icing_download.log'),
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
        raise

def generate_month_list(priority_icing_season=True):
    """Generate list of (year, month) tuples with icing season first."""
    months = []
    
    # Priority: Icing season months
    if priority_icing_season:
        for year in range(START_YEAR, END_YEAR + 1):
            for month in ICING_MONTHS:
                if year == END_YEAR and month > 12:
                    continue  # Skip invalid months
                months.append((year, month))
    
    # Then: Non-icing months
    for year in range(START_YEAR, END_YEAR + 1):
        for month in NON_ICING_MONTHS:
            months.append((year, month))
    
    return months

def download_era5_month_group(client, farm_name, farm_coords, year, month, var_group, output_file):
    """Download ERA5 data for one farm, one month, one variable group."""
    
    # Create bounding box
    north = farm_coords['lat'] + 0.25
    south = farm_coords['lat'] - 0.25
    east = farm_coords['lon'] + 0.25
    west = farm_coords['lon'] - 0.25
    
    # Calculate days in month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    last_day = (next_month - timedelta(days=1)).day
    
    request = {
        'product_type': 'reanalysis',
        'variable': var_group['vars'],
        'year': str(year),
        'month': f'{month:02d}',
        'day': [f'{d:02d}' for d in range(1, last_day + 1)],
        'time': [f'{h:02d}:00' for h in range(0, 24)],
        'area': [north, west, south, east],
        'format': 'netcdf',
    }
    
    logger.info(f"📥 {farm_name}: {year}-{month:02d} ({var_group['name']})")
    logger.info(f"   Variables: {', '.join(var_group['vars'])}")
    
    try:
        client.retrieve('reanalysis-era5-single-levels', request, output_file)
        logger.info(f"✅ Downloaded: {output_file}")
        return True
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        return False

def parse_netcdf_to_dataframe(netcdf_files, farm_name, farm_coords, year, month):
    """Parse multiple NetCDF files (one per variable group) into single DataFrame."""
    logger.info(f"📊 Parsing {len(netcdf_files)} NetCDF files for {farm_name} {year}-{month:02d}...")
    
    try:
        # Initialize empty dict for all variables
        data_dict = {
            'farm_name': farm_name,
            'latitude': farm_coords['lat'],
            'longitude': farm_coords['lon'],
        }
        
        # Read each NetCDF file and extract variables
        time_utc = None
        for nc_file in netcdf_files:
            if not os.path.exists(nc_file):
                logger.warning(f"⚠️ File not found: {nc_file}")
                continue
            
            # Check if file is actually a ZIP (CDS sends some variables as zipped NetCDF)
            import zipfile
            if zipfile.is_zipfile(nc_file):
                logger.info(f"📦 Unzipping {os.path.basename(nc_file)}...")
                with zipfile.ZipFile(nc_file, 'r') as zip_ref:
                    # Extract to same directory
                    temp_dir = os.path.dirname(nc_file)
                    zip_ref.extractall(temp_dir)
                    # Get the extracted NetCDF file (usually same name inside)
                    extracted_files = [f for f in zip_ref.namelist() if f.endswith('.nc')]
                    if extracted_files:
                        nc_file = os.path.join(temp_dir, extracted_files[0])
                        logger.info(f"✅ Extracted: {extracted_files[0]}")
                    else:
                        logger.error(f"❌ No .nc file found in ZIP")
                        continue
                
            ds = xr.open_dataset(nc_file)
            
            # Get time (should be same for all files)
            # ERA5 uses 'valid_time' not 'time'
            if time_utc is None:
                time_coord = 'valid_time' if 'valid_time' in ds.coords else 'time'
                time_utc = pd.to_datetime(ds[time_coord].values)
            
            # Extract variables based on what's in this file
            if 't2m' in ds.variables:
                data_dict['temperature_2m'] = ds['t2m'].values.flatten() - 273.15  # K to °C
            if 'd2m' in ds.variables:
                data_dict['dewpoint_2m'] = ds['d2m'].values.flatten() - 273.15
            if 'tp' in ds.variables:
                data_dict['precipitation'] = ds['tp'].values.flatten() * 1000  # m to mm
            if 'tcc' in ds.variables:
                data_dict['cloud_cover'] = ds['tcc'].values.flatten() * 100  # 0-1 to %
            if 'u100' in ds.variables:
                data_dict['wind_u_100m'] = ds['u100'].values.flatten()
            if 'v100' in ds.variables:
                data_dict['wind_v_100m'] = ds['v100'].values.flatten()
            
            ds.close()
        
        # Create DataFrame
        data_dict['time_utc'] = time_utc
        df = pd.DataFrame(data_dict)
        
        # Calculate derived variables if we have the required data
        if 'temperature_2m' in df.columns and 'dewpoint_2m' in df.columns:
            df['relative_humidity_2m'] = calculate_relative_humidity(
                df['temperature_2m'], 
                df['dewpoint_2m']
            )
        
        if 'wind_u_100m' in df.columns and 'wind_v_100m' in df.columns:
            df['wind_speed_100m'] = (df['wind_u_100m']**2 + df['wind_v_100m']**2)**0.5
            import numpy as np
            df['wind_direction_100m'] = (180 + np.degrees(np.arctan2(df['wind_u_100m'], df['wind_v_100m']))) % 360
        
        logger.info(f"✅ Parsed {len(df)} rows for {farm_name} {year}-{month:02d}")
        return df
        
    except Exception as e:
        logger.error(f"❌ Failed to parse NetCDF files: {e}")
        return None

def calculate_relative_humidity(temp_c, dewpoint_c):
    """Calculate relative humidity from temperature and dewpoint (Magnus formula)."""
    import numpy as np
    a = 17.27
    b = 237.7
    alpha_t = (a * temp_c) / (b + temp_c)
    alpha_td = (a * dewpoint_c) / (b + dewpoint_c)
    rh = 100 * np.exp(alpha_td - alpha_t)
    return np.clip(rh, 0, 100)

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
        
        # Create table if not exists
        try:
            client.get_table(table_id)
        except:
            table_obj = bigquery.Table(table_id, schema=schema)
            table_obj.description = f"""ERA5 weather data (icing season priority). License: CC-BY-4.0 © ECMWF. DOI: 10.24381/cds.adbb2d47"""
            table_obj = client.create_table(table_obj)
            logger.info(f"✅ Created table {table_id}")
        
        # Upload
        job_config = bigquery.LoadJobConfig(schema=schema, write_disposition='WRITE_APPEND')
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Uploaded {len(df)} rows to BigQuery")
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery upload failed: {e}")
        return False

def main():
    """Main download pipeline."""
    logger.info("="*80)
    logger.info("ERA5 CDS ICING SEASON PRIORITY DOWNLOAD")
    logger.info("="*80)
    logger.info(f"Strategy: Icing season (Nov-Mar) first, then remaining months")
    logger.info(f"Years: {START_YEAR}-{END_YEAR}")
    logger.info(f"Farms: {len(WIND_FARMS)}")
    logger.info(f"Variable groups: {len(VARIABLE_GROUPS)}")
    logger.info("")
    
    # Initialize
    cds_client = init_cds_client()
    months = generate_month_list(priority_icing_season=True)
    temp_dir = Path('/tmp/era5_cds')
    temp_dir.mkdir(exist_ok=True)
    
    total_ops = len(WIND_FARMS) * len(months) * len(VARIABLE_GROUPS)
    completed = 0
    failed = 0
    
    logger.info(f"📅 Total operations: {total_ops} (41 farms × {len(months)} months × {len(VARIABLE_GROUPS)} var groups)")
    logger.info("")
    
    # Process each farm
    for farm_idx, (farm_name, farm_coords) in enumerate(WIND_FARMS.items(), 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"🌬️ STARTING FARM: {farm_name}")
        logger.info(f"📍 Location: {farm_coords['lat']:.2f}N, {farm_coords['lon']:.2f}E")
        logger.info(f"📊 Farm progress: Farm {farm_idx}/{len(WIND_FARMS)}")
        
        farm_completed = 0
        farm_requests = len(months) * len(VARIABLE_GROUPS)
        
        # Process each month
        for year, month in months:
            month_files = []
            month_success = True
            
            # Download each variable group
            for var_group in VARIABLE_GROUPS:
                output_file = temp_dir / f"{farm_name.replace(' ', '_')}_{year}_{month:02d}_{var_group['name']}.nc"
                
                success = download_era5_month_group(
                    cds_client, farm_name, farm_coords, year, month, var_group, str(output_file)
                )
                
                if success:
                    month_files.append(str(output_file))
                    completed += 1
                    farm_completed += 1
                    logger.info(f"✅ Request complete: {farm_completed}/{farm_requests} for {farm_name} ({farm_completed/farm_requests*100:.1f}%)")
                    
                    # Rate limiting
                    logger.info(f"⏳ Waiting {var_group['wait_seconds']}s (CDS rate limiting)...")
                    time.sleep(var_group['wait_seconds'])
                else:
                    month_success = False
                    failed += 1
            
            # Parse and upload if all variable groups downloaded successfully
            if month_success and len(month_files) == len(VARIABLE_GROUPS):
                df = parse_netcdf_to_dataframe(month_files, farm_name, farm_coords, year, month)
                
                if df is not None:
                    upload_to_bigquery(df, PROJECT_ID, DATASET, TABLE, LOCATION)
                
                # Move files to permanent storage (instead of deleting)
                for f in month_files:
                    try:
                        src = Path(f)
                        dst = STORAGE_DIR / src.name
                        src.rename(dst)
                        logger.info(f"💾 Saved to: {dst}")
                    except Exception as e:
                        logger.error(f"Failed to move {f}: {e}")
            
            logger.info(f"📊 Farm: {farm_completed}/{farm_requests} | Overall: {completed}/{total_ops}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ FARM COMPLETE: {farm_name}")
        logger.info(f"📊 Downloaded: {farm_completed}/{farm_requests} requests")
        logger.info(f"📊 Remaining farms: {len(WIND_FARMS) - farm_idx}")
        logger.info(f"{'='*80}\n")
    
    logger.info("")
    logger.info("="*80)
    logger.info("=== DOWNLOAD COMPLETE ===")
    logger.info(f"Completed: {completed}/{total_ops} ({100*completed/total_ops:.1f}%)")
    logger.info(f"Failed: {failed}")
    logger.info("="*80)

if __name__ == "__main__":
    main()
