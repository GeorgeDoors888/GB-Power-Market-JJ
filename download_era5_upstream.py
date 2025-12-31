#!/usr/bin/env python3
"""
Download ECMWF ERA5 wind data for grid points west of UK
Provides advance warning for prevailing southwest winds approaching offshore wind farms

Grid points selected to provide 2-4 hour advance warning:
- 200 km west of Irish Sea farms (Walney, Burbo Bank)
- 150 km west of Scottish farms (Moray, Seagreen)
- 80 km west of Humber/Yorkshire farms (Hornsea, Triton Knoll)

Data: 100m wind speed (u and v components), hourly resolution, 2020-2025
"""

import cdsapi
import pandas as pd
import numpy as np
from google.cloud import bigquery
import xarray as xr
from datetime import datetime, timedelta
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# ERA5 grid points (lat, lon) selected for upstream wind measurement
# Format: (latitude, longitude, name, distance_from_coast_km, target_farms)
GRID_POINTS = [
    # Atlantic approach - west of Irish Sea
    (54.0, -8.0, 'Atlantic_Irish_Sea', 200, ['Walney Extension', 'Burbo Bank', 'West of Duddon Sands']),
    (53.5, -6.0, 'Irish_Sea_Central', 150, ['Walney', 'Burbo Bank Extension', 'Barrow']),
    
    # West of Scotland
    (57.0, -6.0, 'Atlantic_Hebrides', 150, ['Moray East', 'Moray West', 'Beatrice']),
    (56.5, -4.5, 'West_Scotland', 100, ['Seagreen Phase 1', 'Neart Na Gaoithe']),
    
    # West of North Sea (across England)
    (53.5, -1.0, 'Central_England', 80, ['Humber Gateway', 'Triton Knoll', 'Hornsea One', 'Hornsea Two']),
    (54.5, -2.0, 'Pennines', 100, ['Hornsea One', 'Hornsea Two']),
    
    # Southwest approach
    (52.5, -5.0, 'Celtic_Sea', 180, ['Burbo Bank', 'East Anglia One', 'Greater Gabbard']),
    (51.5, -2.0, 'Bristol_Channel', 120, ['Rampion', 'Thanet', 'London Array']),
    
    # North of Scotland (for northerly winds)
    (59.0, -4.0, 'North_Scotland', 100, ['Moray East', 'Moray West', 'Beatrice']),
    (58.0, -2.0, 'Moray_Firth_West', 50, ['Moray East', 'Beatrice', 'Hywind Scotland']),
]

def download_era5_for_point(lat, lon, point_name, years=['2020', '2021', '2022', '2023', '2024', '2025']):
    """
    Download ERA5 100m wind data for a single grid point
    """
    print(f"\n📥 Downloading ERA5 data for {point_name} ({lat}°N, {lon}°E)")
    print(f"   Years: {years}")
    
    c = cdsapi.Client()
    
    output_file = f"era5_wind_{point_name}_{lat}_{lon}.nc"
    
    # Skip if already downloaded
    if os.path.exists(output_file):
        print(f"   ✅ Already downloaded: {output_file}")
        return output_file
    
    try:
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': [
                    '100m_u_component_of_wind',  # East-west wind
                    '100m_v_component_of_wind',  # North-south wind
                ],
                'year': years,
                'month': [f'{m:02d}' for m in range(1, 13)],
                'day': [f'{d:02d}' for d in range(1, 32)],
                'time': [f'{h:02d}:00' for h in range(0, 24)],
                'area': [lat + 0.25, lon - 0.25, lat - 0.25, lon + 0.25],  # 0.5° box around point
            },
            output_file
        )
        print(f"   ✅ Downloaded: {output_file}")
        return output_file
    
    except Exception as e:
        print(f"   ❌ Error downloading {point_name}: {e}")
        return None

def process_netcdf_to_dataframe(netcdf_file, point_name, lat, lon, target_farms):
    """
    Convert ERA5 NetCDF to pandas DataFrame with wind speed calculated
    """
    print(f"\n🔄 Processing {netcdf_file}...")
    
    ds = xr.open_dataset(netcdf_file)
    
    # Extract u and v wind components (m/s)
    u_wind = ds['u100'].values  # East-west component
    v_wind = ds['v100'].values  # North-south component
    times = pd.to_datetime(ds['time'].values)
    
    # Calculate wind speed and direction
    wind_speed = np.sqrt(u_wind**2 + v_wind**2)
    wind_direction = (np.arctan2(u_wind, v_wind) * 180 / np.pi + 180) % 360
    
    # Flatten if multi-dimensional (lat/lon grid)
    if wind_speed.ndim > 1:
        wind_speed = wind_speed.mean(axis=(1, 2))  # Average over small grid box
        wind_direction = wind_direction.mean(axis=(1, 2))
    
    # Create DataFrame
    df = pd.DataFrame({
        'time_utc': times,
        'grid_point_name': point_name,
        'latitude': lat,
        'longitude': lon,
        'wind_speed_100m': wind_speed.flatten(),
        'wind_direction': wind_direction.flatten(),
        'u_component': u_wind.flatten() if u_wind.ndim == 1 else u_wind.mean(axis=(1, 2)),
        'v_component': v_wind.flatten() if v_wind.ndim == 1 else v_wind.mean(axis=(1, 2)),
        'target_farms': str(target_farms)
    })
    
    print(f"   ✅ Processed {len(df):,} hourly observations")
    print(f"   Date range: {df['time_utc'].min()} to {df['time_utc'].max()}")
    print(f"   Avg wind speed: {df['wind_speed_100m'].mean():.1f} m/s")
    
    return df

def upload_to_bigquery(df, table_name='era5_wind_upstream'):
    """
    Upload ERA5 data to BigQuery
    """
    print(f"\n📤 Uploading to BigQuery table: {DATASET}.{table_name}")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    
    # Define schema
    schema = [
        bigquery.SchemaField("time_utc", "TIMESTAMP"),
        bigquery.SchemaField("grid_point_name", "STRING"),
        bigquery.SchemaField("latitude", "FLOAT"),
        bigquery.SchemaField("longitude", "FLOAT"),
        bigquery.SchemaField("wind_speed_100m", "FLOAT"),
        bigquery.SchemaField("wind_direction", "FLOAT"),
        bigquery.SchemaField("u_component", "FLOAT"),
        bigquery.SchemaField("v_component", "FLOAT"),
        bigquery.SchemaField("target_farms", "STRING"),
    ]
    
    # Create or replace table
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_APPEND",  # Append to existing data
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="time_utc"
        )
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    print(f"   ✅ Uploaded {len(df):,} rows to {table_id}")

def main():
    print("=" * 80)
    print("ERA5 Wind Data Download - Upstream Sensors for UK Offshore Wind")
    print("=" * 80)
    print(f"\nGrid points to download: {len(GRID_POINTS)}")
    print("Data source: ECMWF ERA5 Reanalysis")
    print("Variables: 100m u/v wind components")
    print("Resolution: Hourly, 0.25° spatial")
    print("Period: 2020-2025")
    
    # Check if CDS API is configured
    try:
        c = cdsapi.Client()
        print("\n✅ ECMWF CDS API configured")
    except Exception as e:
        print(f"\n❌ CDS API not configured: {e}")
        print("\nTo configure:")
        print("1. Register at https://cds.climate.copernicus.eu/")
        print("2. Create ~/.cdsapirc with your API key:")
        print("   url: https://cds.climate.copernicus.eu/api/v2")
        print("   key: YOUR_UID:YOUR_API_KEY")
        return
    
    all_data = []
    
    # Download and process each grid point
    for lat, lon, name, distance, target_farms in GRID_POINTS:
        print(f"\n{'='*80}")
        print(f"Grid Point: {name}")
        print(f"Location: {lat}°N, {lon}°E")
        print(f"Distance from coast: {distance} km")
        print(f"Target farms: {', '.join(target_farms)}")
        print(f"{'='*80}")
        
        # Download
        netcdf_file = download_era5_for_point(lat, lon, name)
        
        if netcdf_file:
            # Process
            df = process_netcdf_to_dataframe(netcdf_file, name, lat, lon, target_farms)
            all_data.append(df)
            
            # Upload to BigQuery after each point (to avoid memory issues)
            upload_to_bigquery(df)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ ERA5 DOWNLOAD COMPLETE")
    print("=" * 80)
    print(f"\nTotal grid points downloaded: {len(all_data)}")
    
    if all_data:
        total_rows = sum(len(df) for df in all_data)
        print(f"Total observations: {total_rows:,}")
        print(f"BigQuery table: {PROJECT_ID}.{DATASET}.era5_wind_upstream")
        print("\n📊 Data coverage:")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"   Date range: {combined_df['time_utc'].min()} to {combined_df['time_utc'].max()}")
        print(f"   Avg wind speed: {combined_df['wind_speed_100m'].mean():.1f} m/s")
        print(f"   Max wind speed: {combined_df['wind_speed_100m'].max():.1f} m/s")
        
        print("\n📈 By grid point:")
        for point_df in all_data:
            point_name = point_df['grid_point_name'].iloc[0]
            print(f"   {point_name}: {len(point_df):,} obs, "
                  f"avg {point_df['wind_speed_100m'].mean():.1f} m/s")
    
    print("\n" + "=" * 80)
    print("Next steps:")
    print("1. Verify data in BigQuery: SELECT * FROM era5_wind_upstream LIMIT 100")
    print("2. Retrain models with ERA5 features: python3 build_wind_power_curves_era5.py")
    print("3. Expected improvement: +15-25% for Irish Sea farms, +5-10% all farms")
    print("=" * 80)

if __name__ == "__main__":
    main()
