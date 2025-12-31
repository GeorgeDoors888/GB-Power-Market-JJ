#!/usr/bin/env python3
"""
Download GFS (Global Forecast System) forecast data for wind farms.
NOAA GFS: 0.25° resolution, 0-384 hour forecasts, updated every 6 hours.
"""

import requests
import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
from typing import List, Dict, Tuple

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "gfs_forecast_weather"

# Open-Meteo Forecast API (provides GFS data in clean format)
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"


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


def download_gfs_forecast(farm_name: str, latitude: float, longitude: float, 
                          forecast_days: int = 7) -> pd.DataFrame:
    """
    Download GFS forecast data for a wind farm location.
    
    Args:
        farm_name: Wind farm name
        latitude: Farm latitude
        longitude: Farm longitude
        forecast_days: Forecast horizon (days, max 16)
    
    Returns:
        DataFrame with hourly forecast data
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "surface_pressure",
            "cloud_cover",
            "wind_speed_10m",
            "wind_speed_100m",
            "wind_direction_10m",
            "wind_direction_100m",
            "wind_gusts_10m",
        ]),
        "forecast_days": forecast_days,
        "timezone": "UTC",
    }
    
    try:
        response = requests.get(FORECAST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "hourly" not in data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        hourly = data["hourly"]
        df = pd.DataFrame({
            "farm_name": farm_name,
            "latitude": latitude,
            "longitude": longitude,
            "forecast_time": datetime.utcnow(),  # When forecast was made
            "valid_time": pd.to_datetime(hourly["time"]),  # When forecast is valid
            "temperature_2m": hourly.get("temperature_2m"),
            "relative_humidity_2m": hourly.get("relative_humidity_2m"),
            "precipitation": hourly.get("precipitation"),
            "surface_pressure": hourly.get("surface_pressure"),
            "cloud_cover": hourly.get("cloud_cover"),
            "wind_speed_10m": hourly.get("wind_speed_10m"),
            "wind_speed_100m": hourly.get("wind_speed_100m"),
            "wind_direction_10m": hourly.get("wind_direction_10m"),
            "wind_direction_100m": hourly.get("wind_direction_100m"),
            "wind_gusts_10m": hourly.get("wind_gusts_10m"),
        })
        
        # Calculate forecast horizon (hours ahead)
        df["forecast_horizon_hours"] = (df["valid_time"] - df["forecast_time"]).dt.total_seconds() / 3600
        
        return df
    
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return pd.DataFrame()


def upload_to_bigquery(df: pd.DataFrame, mode: str = "append"):
    """
    Upload GFS forecast data to BigQuery.
    
    Args:
        df: Forecast data
        mode: 'append' (add to existing) or 'replace' (overwrite table)
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    schema = [
        bigquery.SchemaField("farm_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("latitude", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("longitude", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("forecast_time", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("valid_time", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("forecast_horizon_hours", "FLOAT64"),
        bigquery.SchemaField("temperature_2m", "FLOAT64"),
        bigquery.SchemaField("relative_humidity_2m", "FLOAT64"),
        bigquery.SchemaField("precipitation", "FLOAT64"),
        bigquery.SchemaField("surface_pressure", "FLOAT64"),
        bigquery.SchemaField("cloud_cover", "FLOAT64"),
        bigquery.SchemaField("wind_speed_10m", "FLOAT64"),
        bigquery.SchemaField("wind_speed_100m", "FLOAT64"),
        bigquery.SchemaField("wind_direction_10m", "FLOAT64"),
        bigquery.SchemaField("wind_direction_100m", "FLOAT64"),
        bigquery.SchemaField("wind_gusts_10m", "FLOAT64"),
    ]
    
    # Create table if doesn't exist
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)
    
    print(f"\n📤 Uploading {len(df)} forecast records to BigQuery...")
    
    write_disposition = (
        bigquery.WriteDisposition.WRITE_TRUNCATE if mode == "replace"
        else bigquery.WriteDisposition.WRITE_APPEND
    )
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=write_disposition,
        schema=schema,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded to {table_id}")


def main():
    """Download GFS forecasts for all wind farms."""
    print("=" * 80)
    print("GFS Forecast Data Downloader")
    print("=" * 80)
    print("Source: NOAA GFS via Open-Meteo API")
    print("Resolution: 0.25° (~25 km)")
    print("Forecast horizon: 7 days (168 hours)")
    print("Update frequency: Every 6 hours")
    print(f"Target: {PROJECT_ID}.{DATASET}.{TABLE_NAME}")
    print("=" * 80)
    
    # Get wind farm coordinates
    print("\n📍 Fetching wind farm coordinates from BigQuery...")
    farms = get_wind_farm_coordinates()
    print(f"✅ Found {len(farms)} wind farms")
    
    all_forecasts = []
    
    for i, (farm_name, lat, lon) in enumerate(farms, 1):
        print(f"\n[{i}/{len(farms)}] Downloading forecast: {farm_name}")
        print(f"  📍 Location: {lat:.4f}, {lon:.4f}")
        
        df = download_gfs_forecast(farm_name, lat, lon, forecast_days=7)
        
        if not df.empty:
            print(f"  ✅ {len(df)} hourly forecasts (0-{df['forecast_horizon_hours'].max():.0f}h)")
            all_forecasts.append(df)
        else:
            print(f"  ⚠️  No data returned")
        
        # Rate limiting (10 req/min for free tier)
        if i < len(farms):
            time.sleep(6)
    
    if not all_forecasts:
        print("\n⚠️  No forecast data downloaded")
        return
    
    # Combine all forecasts
    df_combined = pd.concat(all_forecasts, ignore_index=True)
    print(f"\n✅ Total forecast records: {len(df_combined):,}")
    print(f"   Farms: {df_combined['farm_name'].nunique()}")
    print(f"   Forecast time: {df_combined['forecast_time'].iloc[0]}")
    print(f"   Valid time range: {df_combined['valid_time'].min()} to {df_combined['valid_time'].max()}")
    
    # Upload to BigQuery
    upload_to_bigquery(df_combined, mode="replace")
    
    print("\n" + "=" * 80)
    print("✅ GFS forecast download complete!")
    print("=" * 80)
    print("\n💡 To automate, add to crontab:")
    print("   0 */6 * * * cd /home/george/GB-Power-Market-JJ && python3 download_gfs_forecasts.py")
    print("   (Runs every 6 hours to match GFS update cycle)")


if __name__ == "__main__":
    main()
