#!/usr/bin/env python3
"""
ERA5 Ocean/Wave Variables Download - Optimized for Offshore Wind Forecasting

Downloads ocean-atmosphere interaction variables that affect wind turbine power:
1. Air-sea interaction (air density, drag, stress, wind speed corrections)
2. Wave state (height, period, direction for wind waves and swell)
3. Spectral properties (peakedness, directional width, mean square slope)
4. Bathymetry (model depth)

Priority Variables (Fixed-Bottom):
- Air density over oceans
- Coefficient of drag with waves
- Ocean surface stress equivalent 10m neutral wind speed/direction
- Significant wave height (combined)
- Peak wave period
- Mean wave direction

Additional for Floating Wind (Hywind Scotland, Kincardine):
- Maximum individual wave height
- Wave spectral peakedness/directional width
- Swell partition details

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
TABLE = "era5_ocean_wave_data"
LOCATION = "US"

# Storage directory for downloaded files (PERMANENT - files not deleted)
STORAGE_DIR = Path.home() / "era5_downloads" / "ocean_wave"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Icing season months (Nov-Mar) - PRIORITY (for consistency)
ICING_MONTHS = [11, 12, 1, 2, 3]
NON_ICING_MONTHS = [4, 5, 6, 7, 8, 9, 10]

# Date range
START_YEAR = 2020
END_YEAR = 2025

# Variable groups (split to avoid CDS "request too large" errors)
# Group 1: Air-sea interaction (HIGHEST PRIORITY for power forecasting)
# Group 2: Wave height/period/direction
# Group 3: Spectral properties (advanced features)
# Group 4: Bathymetry (static but useful for wave transformation)

VARIABLE_GROUPS = [
    {
        'name': 'air_sea_interaction',
        'vars': [
            'air_density_over_the_oceans',  # ρ for power = ρ·v³
            'coefficient_of_drag_with_waves',  # Surface roughness → wind shear/turbulence
            'ocean_surface_stress_equivalent_10m_neutral_wind_speed',  # Stress-corrected wind
            'ocean_surface_stress_equivalent_10m_neutral_wind_direction',
            'normalized_energy_flux_into_ocean',  # Atmosphere → ocean energy transfer
        ],
        'wait_seconds': 400
    },
    {
        'name': 'wave_basics',
        'vars': [
            'significant_height_of_combined_wind_waves_and_swell',  # Hsig total
            'significant_height_of_wind_waves',  # Wind-driven waves
            'significant_height_of_total_swell',  # Distant swell
            'mean_wave_period',  # Average period
            'peak_wave_period',  # Period of most energetic waves
            'mean_wave_direction',  # Direction of wave propagation
        ],
        'wait_seconds': 400
    },
    {
        'name': 'wave_details',
        'vars': [
            'mean_direction_of_wind_waves',  # Local wind-driven wave direction
            'mean_direction_of_total_swell',  # Swell direction
            'mean_period_of_wind_waves',  # Wind wave period
            'mean_period_of_total_swell',  # Swell period
            'mean_zero_crossing_wave_period',  # Time between zero-crossings
            'maximum_individual_wave_height',  # Extreme wave (floating wind)
        ],
        'wait_seconds': 400
    },
    {
        'name': 'spectral_properties',
        'vars': [
            'wave_spectral_peakedness',  # JONSWAP γ (how concentrated energy is)
            'wave_spectral_directional_width',  # Overall directional spread
            'wave_spectral_directional_width_for_swell',  # Swell directional spread
            'wave_spectral_directional_width_for_wind_waves',  # Wind wave directional spread
            'mean_square_slope_of_waves',  # Surface steepness → roughness
        ],
        'wait_seconds': 400
    },
    {
        'name': 'additional_stress',
        'vars': [
            'normalized_stress_into_ocean',  # Momentum transfer
            'period_corresponding_to_maximum_individual_wave_height',  # Extreme wave period
        ],
        'wait_seconds': 400
    },
]

# Offshore Wind Farms (29 offshore, excluding onshore/nearshore)
OFFSHORE_FARMS = {
    # Scotland (including 2 floating: Hywind, Kincardine)
    'Beatrice': {'lat': 58.25, 'lon': -3.00, 'type': 'fixed'},
    'Moray East': {'lat': 58.15, 'lon': -2.80, 'type': 'fixed'},
    'Seagreen Phase 1': {'lat': 56.55, 'lon': -1.75, 'type': 'fixed'},
    'Neart na Gaoithe': {'lat': 56.30, 'lon': -1.90, 'type': 'fixed'},
    'Inch Cape': {'lat': 56.45, 'lon': -2.05, 'type': 'fixed'},
    'Moray West': {'lat': 58.20, 'lon': -2.95, 'type': 'fixed'},
    'Kincardine': {'lat': 56.70, 'lon': -2.30, 'type': 'floating'},  # FLOATING
    'Hywind Scotland': {'lat': 57.50, 'lon': -1.85, 'type': 'floating'},  # FLOATING
    'EOWDC': {'lat': 57.15, 'lon': -1.95, 'type': 'fixed'},
    
    # North Sea (Hornsea, Dogger Bank, East Anglia)
    'Hornsea One': {'lat': 53.90, 'lon': 1.75, 'type': 'fixed'},
    'Hornsea Two': {'lat': 53.95, 'lon': 1.65, 'type': 'fixed'},
    'Hornsea Three': {'lat': 54.15, 'lon': 1.40, 'type': 'fixed'},
    'Dogger Bank A': {'lat': 55.15, 'lon': 1.35, 'type': 'fixed'},
    'Dogger Bank B': {'lat': 55.25, 'lon': 1.50, 'type': 'fixed'},
    'Dogger Bank C': {'lat': 55.05, 'lon': 1.20, 'type': 'fixed'},
    'East Anglia One': {'lat': 52.05, 'lon': 2.05, 'type': 'fixed'},
    'East Anglia Three': {'lat': 52.25, 'lon': 2.15, 'type': 'fixed'},
    'Triton Knoll': {'lat': 53.40, 'lon': 0.75, 'type': 'fixed'},
    'Greater Gabbard': {'lat': 51.95, 'lon': 2.00, 'type': 'fixed'},
    'Galloper': {'lat': 51.90, 'lon': 2.10, 'type': 'fixed'},
    'London Array': {'lat': 51.65, 'lon': 1.50, 'type': 'fixed'},
    'Thanet': {'lat': 51.45, 'lon': 1.60, 'type': 'fixed'},
    'Rampion': {'lat': 50.65, 'lon': -0.25, 'type': 'fixed'},
    'Westermost Rough': {'lat': 53.80, 'lon': 0.15, 'type': 'fixed'},
    'Lincs': {'lat': 53.30, 'lon': 0.50, 'type': 'fixed'},
    'Race Bank': {'lat': 53.25, 'lon': 0.60, 'type': 'fixed'},
    'Sheringham Shoal': {'lat': 53.00, 'lon': 0.95, 'type': 'fixed'},
    'Dudgeon': {'lat': 53.25, 'lon': 1.30, 'type': 'fixed'},
    'Scroby Sands': {'lat': 52.65, 'lon': 1.75, 'type': 'fixed'},
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/era5_ocean_wave_download.log'),
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
    
    # Priority: Icing season months (for consistency with weather download)
    if priority_icing_season:
        for year in range(START_YEAR, END_YEAR + 1):
            for month in ICING_MONTHS:
                if year == END_YEAR and month > 12:
                    continue
                months.append((year, month))
    
    # Then: Non-icing months
    for year in range(START_YEAR, END_YEAR + 1):
        for month in NON_ICING_MONTHS:
            months.append((year, month))
    
    return months

def download_era5_ocean_month_group(client, farm_name, farm_coords, year, month, var_group, output_file):
    """Download ERA5 ocean/wave data for one farm, one month, one variable group."""
    
    # Create bounding box (0.5° grid for ocean variables)
    north = farm_coords['lat'] + 0.25
    south = farm_coords['lat'] - 0.25
    east = farm_coords['lon'] + 0.25
    west = farm_coords['lon'] - 0.25
    
    # Get days in month
    if month == 2:
        days_in_month = 29 if year % 4 == 0 else 28
    elif month in [4, 6, 9, 11]:
        days_in_month = 30
    else:
        days_in_month = 31
    
    days = [str(d).zfill(2) for d in range(1, days_in_month + 1)]
    
    # All hours
    hours = [f"{h:02d}:00" for h in range(24)]
    
    request = {
        'product_type': ['reanalysis'],
        'variable': var_group['vars'],
        'year': [str(year)],
        'month': [str(month).zfill(2)],
        'day': days,
        'time': hours,
        'area': [north, west, south, east],  # N, W, S, E
        'data_format': 'netcdf',
        'download_format': 'unarchived',
    }
    
    try:
        logger.info(f"📥 Downloading {farm_name} {year}-{month:02d} {var_group['name']}")
        logger.info(f"   Variables: {', '.join(var_group['vars'][:3])}...")
        
        result = client.retrieve('reanalysis-era5-single-levels', request)
        result.download(output_file)
        
        logger.info(f"✅ Downloaded to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        return False

def parse_and_upload_ocean_wave(nc_file, farm_name, farm_coords):
    """Parse ocean/wave NetCDF and upload to BigQuery."""
    try:
        ds = xr.open_dataset(nc_file)
        
        # Extract variables
        data_rows = []
        
        # ERA5 uses 'valid_time' not 'time'
        time_coord = 'valid_time' if 'valid_time' in ds.coords else 'time'
        
        for time_idx in range(len(ds[time_coord])):
            time_val = pd.Timestamp(ds[time_coord].values[time_idx])
            
            row = {
                'farm_name': farm_name,
                'time_utc': time_val,
                'latitude': float(farm_coords['lat']),
                'longitude': float(farm_coords['lon']),
            }
            
            # Air-sea interaction variables
            if 'air_density_over_the_oceans' in ds:
                row['air_density_kg_m3'] = float(ds['air_density_over_the_oceans'].values[time_idx, 0, 0])
            if 'coefficient_of_drag_with_waves' in ds:
                row['drag_coefficient'] = float(ds['coefficient_of_drag_with_waves'].values[time_idx, 0, 0])
            if 'ocean_surface_stress_equivalent_10m_neutral_wind_speed' in ds:
                row['stress_equiv_wind_speed_10m'] = float(ds['ocean_surface_stress_equivalent_10m_neutral_wind_speed'].values[time_idx, 0, 0])
            if 'ocean_surface_stress_equivalent_10m_neutral_wind_direction' in ds:
                row['stress_equiv_wind_direction_10m'] = float(ds['ocean_surface_stress_equivalent_10m_neutral_wind_direction'].values[time_idx, 0, 0])
            if 'normalized_energy_flux_into_ocean' in ds:
                row['energy_flux_into_ocean'] = float(ds['normalized_energy_flux_into_ocean'].values[time_idx, 0, 0])
            if 'normalized_stress_into_ocean' in ds:
                row['stress_into_ocean'] = float(ds['normalized_stress_into_ocean'].values[time_idx, 0, 0])
            
            # Wave height
            if 'significant_height_of_combined_wind_waves_and_swell' in ds:
                row['wave_height_significant_m'] = float(ds['significant_height_of_combined_wind_waves_and_swell'].values[time_idx, 0, 0])
            if 'significant_height_of_wind_waves' in ds:
                row['wave_height_wind_waves_m'] = float(ds['significant_height_of_wind_waves'].values[time_idx, 0, 0])
            if 'significant_height_of_total_swell' in ds:
                row['wave_height_swell_m'] = float(ds['significant_height_of_total_swell'].values[time_idx, 0, 0])
            if 'maximum_individual_wave_height' in ds:
                row['wave_height_max_m'] = float(ds['maximum_individual_wave_height'].values[time_idx, 0, 0])
            
            # Wave period
            if 'mean_wave_period' in ds:
                row['wave_period_mean_s'] = float(ds['mean_wave_period'].values[time_idx, 0, 0])
            if 'peak_wave_period' in ds:
                row['wave_period_peak_s'] = float(ds['peak_wave_period'].values[time_idx, 0, 0])
            if 'mean_zero_crossing_wave_period' in ds:
                row['wave_period_zero_crossing_s'] = float(ds['mean_zero_crossing_wave_period'].values[time_idx, 0, 0])
            if 'mean_period_of_wind_waves' in ds:
                row['wave_period_wind_waves_s'] = float(ds['mean_period_of_wind_waves'].values[time_idx, 0, 0])
            if 'mean_period_of_total_swell' in ds:
                row['wave_period_swell_s'] = float(ds['mean_period_of_total_swell'].values[time_idx, 0, 0])
            if 'period_corresponding_to_maximum_individual_wave_height' in ds:
                row['wave_period_max_height_s'] = float(ds['period_corresponding_to_maximum_individual_wave_height'].values[time_idx, 0, 0])
            
            # Wave direction
            if 'mean_wave_direction' in ds:
                row['wave_direction_mean_deg'] = float(ds['mean_wave_direction'].values[time_idx, 0, 0])
            if 'mean_direction_of_wind_waves' in ds:
                row['wave_direction_wind_waves_deg'] = float(ds['mean_direction_of_wind_waves'].values[time_idx, 0, 0])
            if 'mean_direction_of_total_swell' in ds:
                row['wave_direction_swell_deg'] = float(ds['mean_direction_of_total_swell'].values[time_idx, 0, 0])
            
            # Spectral properties
            if 'wave_spectral_peakedness' in ds:
                row['wave_spectral_peakedness'] = float(ds['wave_spectral_peakedness'].values[time_idx, 0, 0])
            if 'wave_spectral_directional_width' in ds:
                row['wave_spectral_directional_width'] = float(ds['wave_spectral_directional_width'].values[time_idx, 0, 0])
            if 'wave_spectral_directional_width_for_swell' in ds:
                row['wave_spectral_directional_width_swell'] = float(ds['wave_spectral_directional_width_for_swell'].values[time_idx, 0, 0])
            if 'wave_spectral_directional_width_for_wind_waves' in ds:
                row['wave_spectral_directional_width_wind_waves'] = float(ds['wave_spectral_directional_width_for_wind_waves'].values[time_idx, 0, 0])
            if 'mean_square_slope_of_waves' in ds:
                row['wave_mean_square_slope'] = float(ds['mean_square_slope_of_waves'].values[time_idx, 0, 0])
            
            data_rows.append(row)
        
        ds.close()
        
        # Upload to BigQuery
        if data_rows:
            df = pd.DataFrame(data_rows)
            
            client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
            table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
            
            job_config = bigquery.LoadJobConfig(
                write_disposition='WRITE_APPEND',
                schema_update_options=[
                    bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
                ]
            )
            
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Uploaded {len(df)} rows to BigQuery")
            return len(df)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Parse/upload failed: {e}")
        return 0

def main():
    """Main download loop."""
    logger.info("=" * 80)
    logger.info("ERA5 Ocean/Wave Variables Download - Optimized for Offshore Wind")
    logger.info("=" * 80)
    logger.info(f"Farms: {len(OFFSHORE_FARMS)}")
    logger.info(f"Variable groups: {len(VARIABLE_GROUPS)}")
    logger.info(f"Period: {START_YEAR}-{END_YEAR}")
    logger.info(f"Strategy: Icing season (Nov-Mar) first, then Apr-Oct")
    logger.info("=" * 80)
    
    # Initialize CDS client
    client = init_cds_client()
    
    # Create temp directory
    temp_dir = Path('/tmp/era5_ocean_wave_downloads')
    temp_dir.mkdir(exist_ok=True)
    
    # Generate month list
    month_list = generate_month_list(priority_icing_season=True)
    
    # Calculate total requests
    total_requests = len(OFFSHORE_FARMS) * len(month_list) * len(VARIABLE_GROUPS)
    completed = 0
    failed = 0
    total_rows = 0
    
    logger.info(f"📊 Total requests to process: {total_requests}")
    logger.info(f"📊 Estimated time: {total_requests * 6.7 / 60:.1f} hours ({total_requests * 6.7 / 60 / 24:.1f} days)")
    
    # Download loop - ONE FARM AT A TIME (complete all months/variables for each farm)
    for farm_name, farm_coords in OFFSHORE_FARMS.items():
        farm_type = farm_coords['type']
        logger.info(f"\n{'='*80}")
        logger.info(f"🌊 STARTING FARM: {farm_name} ({farm_type.upper()})")
        logger.info(f"📍 Location: {farm_coords['lat']:.2f}N, {farm_coords['lon']:.2f}E")
        logger.info(f"📊 Farm progress: Farm {list(OFFSHORE_FARMS.keys()).index(farm_name) + 1}/{len(OFFSHORE_FARMS)}")
        
        farm_completed = 0
        farm_requests = len(month_list) * len(VARIABLE_GROUPS)
        farm_rows = 0
        
        for year, month in month_list:
            for var_group in VARIABLE_GROUPS:
                output_file = temp_dir / f"{farm_name.replace(' ', '_')}_{year}_{month:02d}_{var_group['name']}.nc"
                
                # Download
                success = download_era5_ocean_month_group(
                    client, farm_name, farm_coords, year, month, var_group, output_file
                )
                
                if success and output_file.exists():
                    # Parse and upload
                    rows = parse_and_upload_ocean_wave(output_file, farm_name, farm_coords)
                    total_rows += rows
                    farm_rows += rows
                    
                    # Move to permanent storage (instead of deleting)
                    permanent_path = STORAGE_DIR / output_file.name
                    output_file.rename(permanent_path)
                    logger.info(f"💾 Saved to: {permanent_path}")
                    
                    completed += 1
                    farm_completed += 1
                    logger.info(f"✅ Request complete: {farm_completed}/{farm_requests} for {farm_name} ({farm_completed/farm_requests*100:.1f}%)")
                    logger.info(f"✅ Overall: {completed}/{total_requests} ({completed/total_requests*100:.1f}%)")
                else:
                    failed += 1
                    logger.error(f"❌ Failed: {farm_name} {year}-{month:02d} {var_group['name']}")
                
                # Progress summary
                logger.info(f"📊 Farm: {farm_completed}/{farm_requests} | Overall: {completed}/{total_requests} | Rows: {farm_rows:,}/{total_rows:,}")
                
                # Rate limiting
                if completed < total_requests:  # Don't wait after last request
                    wait_time = var_group['wait_seconds']
                    logger.info(f"⏳ Waiting {wait_time} seconds before next request...")
                    time.sleep(wait_time)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ FARM COMPLETE: {farm_name}")
        logger.info(f"📊 Downloaded: {farm_completed}/{farm_requests} requests, {farm_rows:,} rows")
        logger.info(f"📊 Remaining farms: {len(OFFSHORE_FARMS) - list(OFFSHORE_FARMS.keys()).index(farm_name) - 1}")
        logger.info(f"{'='*80}\n")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ DOWNLOAD COMPLETE")
    logger.info(f"📊 Final stats: {completed} completed, {failed} failed, {total_rows:,} rows uploaded")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()
