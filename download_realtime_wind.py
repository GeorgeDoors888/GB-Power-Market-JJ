#!/usr/bin/env python3
"""
Real-time wind data download (every 15 minutes).
Downloads last 2 hours of generation for ramp detection.
Run every 15 minutes via cron.
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "openmeteo_wind_realtime"
API_URL = "https://api.open-meteo.com/v1/forecast"

# Ramp thresholds (MW change per hour)
RAMP_WARNING = 50
RAMP_CRITICAL = 150


def get_wind_farms():
    """Get wind farm coordinates from turbine specs."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT
        farm_name,
        AVG(latitude) as latitude,
        AVG(longitude) as longitude
    FROM `{PROJECT_ID}.{DATASET}.wind_turbine_specs`
    GROUP BY farm_name
    ORDER BY farm_name
    """
    
    df = client.query(query).to_dataframe()
    return [(row.farm_name, row.latitude, row.longitude) for _, row in df.iterrows()]


def download_realtime_wind(farm_name, latitude, longitude):
    """Download last 2 hours of wind data for one farm."""
    # Open-Meteo forecast API provides recent observations + forecast
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join([
            "wind_speed_100m",
            "wind_direction_100m",
            "wind_gusts_10m",
            "temperature_2m",
            "pressure_msl"
        ]),
        "past_hours": 2,
        "forecast_hours": 1,
        "timezone": "UTC",
    }
    
    try:
        response = requests.get(API_URL, params=params, timeout=30)
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
            "wind_speed_100m": hourly.get("wind_speed_100m"),
            "wind_direction_100m": hourly.get("wind_direction_100m"),
            "wind_gusts_10m": hourly.get("wind_gusts_10m"),
            "temperature_2m": hourly.get("temperature_2m"),
            "pressure_msl": hourly.get("pressure_msl"),
        })
        
        # Only keep actual observations (past data)
        now = datetime.now()
        df = df[df["time_utc"] <= now]
        
        return df
    
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return pd.DataFrame()


def detect_ramps(df):
    """Detect significant wind speed changes (ramps)."""
    if len(df) < 2:
        return []
    
    df = df.sort_values("time_utc")
    df["wind_change_1h"] = df["wind_speed_100m"].diff()
    df["wind_change_pct"] = (df["wind_change_1h"] / df["wind_speed_100m"].shift(1)) * 100
    
    alerts = []
    
    for _, row in df.iterrows():
        if pd.isna(row["wind_change_1h"]):
            continue
        
        change = abs(row["wind_change_1h"])
        change_pct = abs(row["wind_change_pct"]) if not pd.isna(row["wind_change_pct"]) else 0
        
        if change >= RAMP_CRITICAL:
            alerts.append({
                "severity": "CRITICAL",
                "farm": row["farm_name"],
                "time": row["time_utc"],
                "wind_change_ms": round(change, 2),
                "wind_change_pct": round(change_pct, 1),
            })
        elif change >= RAMP_WARNING:
            alerts.append({
                "severity": "WARNING",
                "farm": row["farm_name"],
                "time": row["time_utc"],
                "wind_change_ms": round(change, 2),
                "wind_change_pct": round(change_pct, 1),
            })
    
    return alerts


def upload_to_bigquery(df):
    """Upload real-time wind data to BigQuery (append mode with duplicate prevention)."""
    if df.empty:
        return
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    # Check if table exists
    try:
        client.get_table(table_id)
        table_exists = True
    except Exception:
        table_exists = False
        print(f"  ℹ️  Creating new table: {TABLE_NAME}")
    
    if table_exists:
        # Remove duplicates (only keep last 2 hours to avoid conflicts)
        existing_times = set()
        check_query = f"""
        SELECT DISTINCT time_utc
        FROM `{table_id}`
        WHERE time_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR)
        """
        
        try:
            existing_df = client.query(check_query).to_dataframe()
            existing_times = set(existing_df["time_utc"])
        except Exception:
            pass
        
        # Filter out duplicates
        df = df[~df["time_utc"].isin(existing_times)]
        
        if df.empty:
            return
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()


def main():
    """Download real-time wind data and detect ramps."""
    run_time = datetime.now()
    
    print("="*80)
    print("Real-Time Wind Data Update")
    print("="*80)
    print(f"Run time: {run_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Get wind farms
    farms = get_wind_farms()
    print(f"Wind farms: {len(farms)}")
    print()
    
    # Download data for each farm
    all_data = []
    all_alerts = []
    
    for farm_name, lat, lon in farms:
        df = download_realtime_wind(farm_name, lat, lon)
        
        if not df.empty:
            all_data.append(df)
            
            # Detect ramps
            alerts = detect_ramps(df)
            all_alerts.extend(alerts)
    
    # Combine and upload
    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        print(f"✅ Downloaded {len(df_combined):,} new observations")
        upload_to_bigquery(df_combined)
    else:
        print("⚠️  No new data")
    
    # Print ramp alerts
    if all_alerts:
        print("\n" + "="*80)
        print("🚨 RAMP ALERTS")
        print("="*80)
        
        for alert in all_alerts:
            severity_icon = "🔴" if alert["severity"] == "CRITICAL" else "🟡"
            print(f"{severity_icon} {alert['severity']}: {alert['farm']}")
            print(f"   Time: {alert['time'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Change: {alert['wind_change_ms']} m/s ({alert['wind_change_pct']}%)")
            print()
    
    print("="*80)
    print(f"✅ Real-time update complete")
    print("="*80)


if __name__ == "__main__":
    main()
