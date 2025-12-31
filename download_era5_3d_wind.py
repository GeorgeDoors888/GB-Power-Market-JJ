#!/usr/bin/env python3
"""
Download ERA5 3D wind components (u, v, w, omega) for advanced wind analysis.
Used for: ramp prediction, atmospheric dynamics, vertical wind profiles.
"""

import requests
import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
from typing import List, Tuple
from joblib import Parallel, delayed

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_3d_wind_components"

# Open-Meteo Archive API for ERA5 data
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"


def get_wind_farm_coordinates() -> List[Tuple[str, float, float]]:
    """Get wind farm coordinates from BigQuery."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT
        farm_name,
        latitude,
        longitude
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    ORDER BY farm_name
    """
    
    df = client.query(query).to_dataframe()
    return [(row.farm_name, row.latitude, row.longitude) for _, row in df.iterrows()]


def download_3d_wind_for_year(farm_name: str, latitude: float, longitude: float, 
                               year: int) -> pd.DataFrame:
    """
    Download ERA5 3D wind components for one year.
    
    Args:
        farm_name: Wind farm name
        latitude: Farm latitude
        longitude: Farm longitude
        year: Year (2021-2025)
    
    Returns:
        DataFrame with hourly 3D wind data
    """
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # ERA5 pressure levels (focus on surface to 100m equivalent)
    # 100m ≈ 1000 hPa (surface level)
    # Higher levels for atmospheric dynamics (850, 700 hPa)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join([
            # Surface level (10m standard)
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            # Higher level (100m for wind turbines)
            "wind_speed_100m",
            "wind_direction_100m",
            # Pressure levels for vertical motion
            "surface_pressure",
            "pressure_msl",
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
            "wind_speed_10m": hourly.get("wind_speed_10m"),
            "wind_direction_10m": hourly.get("wind_direction_10m"),
            "wind_gusts_10m": hourly.get("wind_gusts_10m"),
            "wind_speed_100m": hourly.get("wind_speed_100m"),
            "wind_direction_100m": hourly.get("wind_direction_100m"),
            "surface_pressure": hourly.get("surface_pressure"),
            "pressure_msl": hourly.get("pressure_msl"),
        })
        
        # Calculate derived features
        # Wind shear between 10m and 100m (important for power production)
        df["wind_shear"] = df["wind_speed_100m"] - df["wind_speed_10m"]
        
        # Convert wind direction to u/v components (eastward/northward)
        df["u_component_10m"] = -df["wind_speed_10m"] * np.sin(np.radians(df["wind_direction_10m"]))
        df["v_component_10m"] = -df["wind_speed_10m"] * np.cos(np.radians(df["wind_direction_10m"]))
        df["u_component_100m"] = -df["wind_speed_100m"] * np.sin(np.radians(df["wind_direction_100m"]))
        df["v_component_100m"] = -df["wind_speed_100m"] * np.cos(np.radians(df["wind_direction_100m"]))
        
        # Pressure gradient (proxy for vertical motion - ramp events)
        df["pressure_gradient"] = df["pressure_msl"] - df["surface_pressure"]
        
        return df
    
    except Exception as e:
        print(f"  ⚠️  {year}: {e}")
        return pd.DataFrame()


def download_farm_all_years(farm_name: str, latitude: float, longitude: float) -> pd.DataFrame:
    """Download 3D wind data for all years (2021-2025) for one farm."""
    years = [2021, 2022, 2023, 2024, 2025]
    farm_data = []
    
    print(f"  Fetching {farm_name}...")
    
    for year in years:
        df = download_3d_wind_for_year(farm_name, latitude, longitude, year)
        
        if not df.empty:
            print(f"    ✅ {year}: {len(df):,} records")
            farm_data.append(df)
        else:
            print(f"    ⚠️  {year}: No data")
        
        # Rate limiting (10 req/min)
        time.sleep(6)
    
    if farm_data:
        return pd.concat(farm_data, ignore_index=True)
    return pd.DataFrame()


def upload_to_bigquery(df: pd.DataFrame):
    """Upload 3D wind data to BigQuery."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    schema = [
        bigquery.SchemaField("farm_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("latitude", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("longitude", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("time_utc", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("wind_speed_10m", "FLOAT64"),
        bigquery.SchemaField("wind_direction_10m", "FLOAT64"),
        bigquery.SchemaField("wind_gusts_10m", "FLOAT64"),
        bigquery.SchemaField("wind_speed_100m", "FLOAT64"),
        bigquery.SchemaField("wind_direction_100m", "FLOAT64"),
        bigquery.SchemaField("surface_pressure", "FLOAT64"),
        bigquery.SchemaField("pressure_msl", "FLOAT64"),
        bigquery.SchemaField("wind_shear", "FLOAT64"),
        bigquery.SchemaField("u_component_10m", "FLOAT64"),
        bigquery.SchemaField("v_component_10m", "FLOAT64"),
        bigquery.SchemaField("u_component_100m", "FLOAT64"),
        bigquery.SchemaField("v_component_100m", "FLOAT64"),
        bigquery.SchemaField("pressure_gradient", "FLOAT64"),
    ]
    
    # Create table
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)
    
    print(f"\n📤 Uploading {len(df):,} records to BigQuery...")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=schema,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded to {table_id}")


def main():
    """Download ERA5 3D wind components for all wind farms (2021-2025)."""
    print("=" * 80)
    print("ERA5 3D Wind Components Downloader")
    print("=" * 80)
    print("Variables: wind u/v components, wind shear, pressure gradient")
    print("Purpose: Ramp prediction, atmospheric dynamics analysis")
    print("Period: 2021-2025")
    print(f"Target: {PROJECT_ID}.{DATASET}.{TABLE_NAME}")
    print("=" * 80)
    
    # Get wind farm coordinates
    print("\n📍 Fetching wind farm coordinates from BigQuery...")
    farms = get_wind_farm_coordinates()
    print(f"✅ Found {len(farms)} wind farms")
    
    # Estimate total API calls and time
    total_calls = len(farms) * 5  # 5 years per farm
    estimated_minutes = (total_calls * 6) / 60  # 6 seconds per call
    print(f"\n⏱️  Estimated time: {estimated_minutes:.1f} minutes ({total_calls} API calls)")
    print("   Rate limit: 10 requests/minute (6 seconds between calls)")
    print()
    
    # Download data farm by farm (NOT parallel due to rate limits)
    all_data = []
    
    for i, (farm_name, lat, lon) in enumerate(farms, 1):
        print(f"\n[{i}/{len(farms)}] Processing {farm_name} ({lat:.4f}, {lon:.4f})")
        
        df = download_farm_all_years(farm_name, lat, lon)
        
        if not df.empty:
            all_data.append(df)
            print(f"  ✅ Total: {len(df):,} records")
    
    if not all_data:
        print("\n⚠️  No data downloaded")
        return
    
    # Combine all data
    df_combined = pd.concat(all_data, ignore_index=True)
    
    print("\n" + "=" * 80)
    print(f"✅ Total records: {df_combined.shape[0]:,}")
    print(f"   Farms: {df_combined['farm_name'].nunique()}")
    print(f"   Date range: {df_combined['time_utc'].min()} to {df_combined['time_utc'].max()}")
    print(f"   Data size: ~{df_combined.memory_usage(deep=True).sum() / 1e6:.1f} MB in memory")
    print("=" * 80)
    
    # Upload to BigQuery
    upload_to_bigquery(df_combined)
    
    # Summary statistics
    print("\n📊 Feature Statistics:")
    print(f"   Wind shear (100m-10m): {df_combined['wind_shear'].mean():.2f} ± {df_combined['wind_shear'].std():.2f} m/s")
    print(f"   Pressure gradient: {df_combined['pressure_gradient'].mean():.2f} ± {df_combined['pressure_gradient'].std():.2f} hPa")
    print(f"   Wind speed 100m: {df_combined['wind_speed_100m'].mean():.2f} ± {df_combined['wind_speed_100m'].std():.2f} m/s")
    
    print("\n" + "=" * 80)
    print("✅ ERA5 3D wind components download complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
