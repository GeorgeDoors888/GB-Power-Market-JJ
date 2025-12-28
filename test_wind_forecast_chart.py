#!/usr/bin/env python3
"""
Test script to verify wind forecast data in publication table and Apps Script accessibility.
"""
from google.cloud import bigquery
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def main():
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Query to get wind forecast data structure
    query = f"""
    SELECT 
      intraday_wind AS actual,
      intraday_wind_forecast AS forecast
    FROM `{PROJECT_ID}.{DATASET}.publication_dashboard_live`
    LIMIT 1
    """
    
    print("🔍 Checking Wind Forecast Data in Publication Table\n")
    print("=" * 60)
    
    result = client.query(query).to_dataframe()
    
    if result.empty:
        print("❌ No data in publication table!")
        return
    
    actual = result['actual'].iloc[0]
    forecast = result['forecast'].iloc[0]
    
    print(f"✅ Actual Wind Data Points: {len(actual)}")
    print(f"   First 5 values: {actual[:5]}")
    print(f"   Sample (period 10): {actual[10] if len(actual) > 10 else 'N/A'}")
    
    print(f"\n✅ Forecast Wind Data Points: {len(forecast)}")
    print(f"   First 5 values: {forecast[:5]}")
    print(f"   Sample (period 10): {forecast[10] if len(forecast) > 10 else 'N/A'}")
    
    print("\n" + "=" * 60)
    print("📊 Chart Data Preview (first 10 periods):")
    print(f"{'Period':<10} {'Actual (MW)':<15} {'Forecast (MW)':<15}")
    print("-" * 40)
    for i in range(min(10, len(actual), len(forecast))):
        act_val = f"{actual[i]:.0f}" if actual[i] != -999 else "null"
        fcst_val = f"{forecast[i]:.0f}" if forecast[i] != -999 else "null"
        print(f"{i+1:<10} {act_val:<15} {fcst_val:<15}")
    
    # Check for null values (-999 markers)
    actual_nulls = sum(1 for x in actual if x == -999)
    forecast_nulls = sum(1 for x in forecast if x == -999)
    
    print(f"\n📌 Null values (-999): Actual={actual_nulls}, Forecast={forecast_nulls}")
    
    if actual_nulls > 40 or forecast_nulls > 40:
        print("⚠️  WARNING: Too many null values may cause chart to appear empty!")
    else:
        print("✅ Data looks good for charting!")

if __name__ == "__main__":
    main()
