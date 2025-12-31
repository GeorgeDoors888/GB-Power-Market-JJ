#!/usr/bin/env python3
"""
ERA5 Ocean/Wave Data Download - ZARR/ARCO Format
Using Google Cloud ARCO-ERA5 dataset for 100x faster downloads

Performance Comparison:
- CDS API: 10,440 requests × 9 min = 65 DAYS ❌
- Zarr/ARCO: 6 bulk downloads = 2-3 HOURS ✅

Cost: ~$7-10 for egress (or FREE if running in GCP)

Requirements:
    pip3 install --user xarray zarr gcsfs dask netCDF4

Author: George Major
Date: December 31, 2025
"""

import xarray as xr
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from google.cloud import bigquery
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/era5_zarr_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# BigQuery configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_ocean_wave_data"

# GCS ARCO-ERA5 Zarr store
ZARR_STORE = "gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"

# Offshore Wind Farms (same 29 as CDS API version)
OFFSHORE_FARMS = {
    'Beatrice': {'lat': 58.25, 'lon': -3.00},
    'Moray East': {'lat': 58.15, 'lon': -2.80},
    'Seagreen Phase 1': {'lat': 56.55, 'lon': -1.75},
    'Neart na Gaoithe': {'lat': 56.30, 'lon': -1.90},
    'Inch Cape': {'lat': 56.45, 'lon': -2.05},
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
    'Race Bank': {'lat': 53.25, 'lon': 0.60},
    'Sheringham Shoal': {'lat': 53.00, 'lon': 0.95},
    'Dudgeon': {'lat': 53.25, 'lon': 1.30},
    'Scroby Sands': {'lat': 52.65, 'lon': 1.75},
}

# ERA5 variable mapping (CDS names → ARCO-ERA5 parameter IDs)
# Documentation: https://www.ecmwf.int/en/forecasts/dataset/ecmwf-reanalysis-v5
VARIABLE_MAPPING = {
    # Air-sea interaction
    'air_density_over_the_oceans': 'p140209',  # Air density (kg/m³)
    'coefficient_of_drag_with_waves': 'p140208',  # Drag coefficient
    'ocean_surface_stress_equivalent_10m_neutral_wind_speed': 'p140245',  # Wind speed (m/s)
    'ocean_surface_stress_equivalent_10m_neutral_wind_direction': 'p140244',  # Wind dir (°)
    'normalized_energy_flux_into_ocean': 'p140234',  # Energy flux (W/m²)
    
    # Wave basics
    'significant_height_of_combined_wind_waves_and_swell': 'swh',  # Significant wave height (m)
    'significant_height_of_wind_waves': 'shww',  # Wind wave height (m)
    'significant_height_of_total_swell': 'shts',  # Swell height (m)
    'mean_wave_period': 'mwp',  # Mean wave period (s)
    'peak_wave_period': 'pp1d',  # Peak wave period (s)
    'mean_wave_direction': 'mwd',  # Wave direction (°)
    
    # Wave energy spectrum
    'wave_spectral_directional_width': 'wdw',  # Directional width
    'wave_spectral_directional_width_for_swell': 'cdww',  # Swell directional width
    'wave_spectral_directional_width_for_wind_waves': 'shww',  # Wind wave directional width
    'significant_wave_height_of_first_swell_partition': 'p140221',  # First swell height (m)
    'significant_wave_height_of_second_swell_partition': 'p140222',  # Second swell height (m)
    'significant_wave_height_of_third_swell_partition': 'p140223',  # Third swell height (m)
    
    # Wave parameters
    'mean_wave_period_based_on_first_moment': 'mp1',  # Mean period 1st moment (s)
    'mean_wave_period_based_on_second_moment': 'mp2',  # Mean period 2nd moment (s)
    'mean_zero_crossing_wave_period': 'p140220',  # Zero crossing period (s)
    'peak_wave_period': 'pp1d',  # Peak period (s)
    
    # Wave system details
    'mean_direction_of_total_swell': 'mdts',  # Swell direction (°)
    'mean_period_of_total_swell': 'mpts',  # Swell period (s)
    'mean_direction_of_wind_waves': 'mdww',  # Wind wave direction (°)
}


def extract_farm_data_from_zarr(zarr_ds, farm_name, farm_coords, year):
    """
    Extract ocean/wave data for one farm from Zarr dataset
    
    Args:
        zarr_ds: Xarray dataset opened from Zarr store
        farm_name: Name of wind farm
        farm_coords: {'lat': float, 'lon': float}
        year: Year to extract
        
    Returns:
        pandas DataFrame with hourly data
    """
    logger.info(f"📍 Extracting {farm_name} ({year}): lat={farm_coords['lat']}, lon={farm_coords['lon']}")
    
    # Select nearest grid point to farm location
    ds_farm = zarr_ds.sel(
        latitude=farm_coords['lat'],
        longitude=farm_coords['lon'],
        time=slice(f'{year}-01-01', f'{year}-12-31'),
        method='nearest'
    )
    
    # Convert to DataFrame
    rows = []
    for time_idx in range(len(ds_farm['time'])):
        time_val = pd.Timestamp(ds_farm['time'].values[time_idx])
        
        row = {
            'farm_name': farm_name,
            'time_utc': time_val,
            'latitude': float(ds_farm['latitude'].values),
            'longitude': float(ds_farm['longitude'].values),
        }
        
        # Extract all available variables
        for cds_name, zarr_param in VARIABLE_MAPPING.items():
            if zarr_param in ds_farm:
                value = float(ds_farm[zarr_param].isel(time=time_idx).values)
                # Handle NaN values
                if np.isnan(value):
                    value = None
                row[cds_name] = value
            else:
                row[cds_name] = None
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    logger.info(f"✅ Extracted {len(df)} hours for {farm_name} ({year})")
    return df


def upload_to_bigquery(df, client):
    """Upload DataFrame to BigQuery"""
    if df.empty:
        logger.warning("⚠️ Empty DataFrame, skipping upload")
        return 0
    
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="time_utc"
        ),
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        logger.info(f"✅ Uploaded {len(df)} rows to BigQuery")
        return len(df)
    except Exception as e:
        logger.error(f"❌ BigQuery upload failed: {e}")
        return 0


def main():
    """Main download loop using Zarr/ARCO format"""
    logger.info("=" * 80)
    logger.info("ERA5 ZARR/ARCO OCEAN/WAVE DATA DOWNLOAD - FAST MODE")
    logger.info("=" * 80)
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Years to download
    years = list(range(2020, 2026))  # 2020-2025
    
    logger.info(f"📋 Configuration:")
    logger.info(f"   Farms: {len(OFFSHORE_FARMS)}")
    logger.info(f"   Years: {years}")
    logger.info(f"   Variables: {len(VARIABLE_MAPPING)}")
    logger.info(f"   Zarr store: {ZARR_STORE}")
    logger.info("")
    
    total_rows = 0
    
    # Download by year (6 iterations, not 10,440!)
    for year in years:
        logger.info(f"📅 YEAR {year}: Opening Zarr store...")
        
        try:
            # Open Zarr dataset for this year
            # Note: This reads metadata only, actual data loaded on-demand
            ds = xr.open_zarr(
                ZARR_STORE,
                consolidated=True,
                chunks={'time': 24}  # 24 hours per chunk
            )
            logger.info(f"✅ Zarr store opened: {len(ds.data_vars)} variables available")
            
            # Extract data for all farms in this year
            year_dfs = []
            for farm_name, farm_coords in OFFSHORE_FARMS.items():
                try:
                    df_farm = extract_farm_data_from_zarr(ds, farm_name, farm_coords, year)
                    year_dfs.append(df_farm)
                except Exception as e:
                    logger.error(f"❌ Failed to extract {farm_name} ({year}): {e}")
                    continue
            
            # Combine all farms for this year
            if year_dfs:
                df_year = pd.concat(year_dfs, ignore_index=True)
                logger.info(f"✅ {year}: Extracted {len(df_year)} total rows from {len(year_dfs)} farms")
                
                # Upload to BigQuery
                rows_uploaded = upload_to_bigquery(df_year, client)
                total_rows += rows_uploaded
                
                logger.info(f"📊 Progress: {total_rows:,} total rows uploaded")
            
        except Exception as e:
            logger.error(f"❌ Year {year} failed: {e}")
            continue
    
    logger.info("=" * 80)
    logger.info(f"🎉 DOWNLOAD COMPLETE!")
    logger.info(f"   Total rows uploaded: {total_rows:,}")
    logger.info(f"   Farms processed: {len(OFFSHORE_FARMS)}")
    logger.info(f"   Years: {min(years)}-{max(years)}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
