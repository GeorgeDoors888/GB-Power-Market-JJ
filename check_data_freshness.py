#!/usr/bin/env python3
"""
Data Freshness Monitor - Check last update times for all weather data sources.
Run hourly via cron to ensure data pipeline is functioning.
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Expected update frequencies (hours)
FRESHNESS_THRESHOLDS = {
    "era5_weather_icing": 24 * 6,  # ERA5 has T-5 day lag, check weekly
    "gfs_forecast_weather": 8,  # Should update every 6 hours
    "remit_unavailability_messages": 26,  # Should update daily
    "openmeteo_wind_realtime": 1,  # Should update every 15 minutes
    "openmeteo_wind_historic": 24 * 7,  # Historical, updated weekly
}


def check_table_freshness(table_name, time_column, threshold_hours):
    """Check when table was last updated."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        MAX({time_column}) as last_update,
        COUNT(*) as total_records
    FROM `{PROJECT_ID}.{DATASET}.{table_name}`
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if df.empty or pd.isna(df['last_update'][0]):
            return {
                "table": table_name,
                "status": "EMPTY",
                "last_update": None,
                "hours_ago": None,
                "total_records": 0,
            }
        
        last_update = df['last_update'][0]
        hours_ago = (datetime.now(tz=last_update.tzinfo) - last_update).total_seconds() / 3600
        
        if hours_ago > threshold_hours:
            status = "STALE"
        elif hours_ago > threshold_hours * 0.8:
            status = "WARNING"
        else:
            status = "OK"
        
        return {
            "table": table_name,
            "status": status,
            "last_update": last_update,
            "hours_ago": round(hours_ago, 1),
            "total_records": int(df['total_records'][0]),
            "threshold_hours": threshold_hours,
        }
    
    except Exception as e:
        return {
            "table": table_name,
            "status": "ERROR",
            "error": str(e),
        }


def main():
    """Check data freshness for all weather sources."""
    print("="*80)
    print("Weather Data Freshness Check")
    print("="*80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Check each data source
    results = []
    
    # ERA5 Weather
    result = check_table_freshness("era5_weather_icing", "time_utc", FRESHNESS_THRESHOLDS["era5_weather_icing"])
    results.append(result)
    
    # GFS Forecasts
    result = check_table_freshness("gfs_forecast_weather", "forecast_time", FRESHNESS_THRESHOLDS["gfs_forecast_weather"])
    results.append(result)
    
    # REMIT Messages
    result = check_table_freshness("remit_unavailability_messages", "publishTime", FRESHNESS_THRESHOLDS["remit_unavailability_messages"])
    results.append(result)
    
    # Real-Time Wind
    result = check_table_freshness("openmeteo_wind_realtime", "time_utc", FRESHNESS_THRESHOLDS["openmeteo_wind_realtime"])
    results.append(result)
    
    # Historical Wind
    result = check_table_freshness("openmeteo_wind_historic", "time_utc", FRESHNESS_THRESHOLDS["openmeteo_wind_historic"])
    results.append(result)
    
    # Print results
    has_issues = False
    
    for result in results:
        table = result["table"]
        status = result["status"]
        
        if status == "OK":
            icon = "✅"
        elif status == "WARNING":
            icon = "⚠️"
            has_issues = True
        elif status == "STALE":
            icon = "❌"
            has_issues = True
        elif status == "EMPTY":
            icon = "⚪"
            has_issues = True
        else:  # ERROR
            icon = "💥"
            has_issues = True
        
        print(f"{icon} {table}")
        
        if status in ["OK", "WARNING", "STALE"]:
            print(f"   Last update: {result['last_update'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   Hours ago: {result['hours_ago']} (threshold: {result['threshold_hours']})")
            print(f"   Records: {result['total_records']:,}")
        elif status == "EMPTY":
            print(f"   ⚠️  Table is empty!")
        elif status == "ERROR":
            print(f"   Error: {result['error']}")
        
        print()
    
    print("="*80)
    
    if has_issues:
        print("⚠️  Data freshness issues detected!")
        print("="*80)
        sys.exit(1)
    else:
        print("✅ All data sources are up to date")
        print("="*80)
        sys.exit(0)


if __name__ == "__main__":
    main()
