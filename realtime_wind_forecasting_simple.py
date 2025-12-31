#!/usr/bin/env python3
"""
Real-time wind forecasting - simplified version.
Compares our ML predictions with NESO forecasts.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
import joblib
import os
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"
MODEL_DIR = "models/wind_power_curves"

def load_models():
    """Load all trained ML models."""
    print("\n📦 Loading trained models...")
    models = {}
    for model_file in sorted(os.listdir(MODEL_DIR)):
        if model_file.endswith('.joblib'):
            farm_name = model_file.replace('.joblib', '').replace('_', ' ')
            model_path = os.path.join(MODEL_DIR, model_file)
            models[farm_name] = joblib.load(model_path)
            print(f"  ✅ Loaded: {farm_name}")
    
    print(f"✅ Loaded {len(models)} farm models")
    return models

def fetch_neso_forecast():
    """Fetch latest NESO wind forecast."""
    print("\n📡 Fetching NESO wind forecast...")
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    query = f"""
    SELECT
        startTime as forecast_time,
        generation as neso_forecast_mw,
        publishTime
    FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor_iris`
    WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 6 HOUR)
      AND startTime >= CURRENT_TIMESTAMP()
      AND startTime <= TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY publishTime DESC, startTime
    """
    
    df = client.query(query).to_dataframe()
    
    # Keep latest publish per forecast time
    df = df.sort_values('publishTime', ascending=False).drop_duplicates(
        subset=['forecast_time'], keep='first'
    )
    
    print(f"✅ Loaded {len(df)} forecast hours")
    return df[['forecast_time', 'neso_forecast_mw']]

def fetch_recent_weather():
    """Fetch recent historical weather as proxy for current conditions."""
    print("\n🌤️  Fetching recent weather data...")
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    query = f"""
    SELECT 
        farm_name,
        time_utc,
        EXTRACT(HOUR FROM time_utc) as hour_of_day,
        EXTRACT(MONTH FROM time_utc) as month,
        EXTRACT(DAYOFWEEK FROM time_utc) as day_of_week,
        wind_speed_100m,
        wind_direction_10m,
        wind_gusts_10m,
        capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    WHERE time_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      AND time_utc <= CURRENT_TIMESTAMP()
    ORDER BY farm_name, time_utc DESC
    """
    
    df = client.query(query).to_dataframe()
    
    # Get latest reading per farm
    df = df.sort_values('time_utc', ascending=False).drop_duplicates(
        subset=['farm_name'], keep='first'
    )
    
    print(f"✅ Loaded latest weather for {len(df)} farms")
    return df

def predict_current_generation(models, weather_df):
    """Generate predictions for current conditions."""
    print("\n🔮 Generating predictions...")
    
    features = ['wind_speed_100m', 'wind_direction_10m', 'hour_of_day', 
                'month', 'day_of_week', 'wind_gusts_10m']
    
    predictions = []
    for idx, row in weather_df.iterrows():
        farm_name = row['farm_name']
        if farm_name not in models:
            continue
        
        X = row[features].values.reshape(1, -1)
        pred_mw = models[farm_name].predict(X)[0]
        
        # Clip to capacity
        pred_mw = np.clip(pred_mw, 0, row['capacity_mw'])
        
        predictions.append({
            'farm_name': farm_name,
            'capacity_mw': row['capacity_mw'],
            'predicted_mw': pred_mw,
            'wind_speed_100m': row['wind_speed_100m']
        })
    
    pred_df = pd.DataFrame(predictions)
    total_pred = pred_df['predicted_mw'].sum()
    total_capacity = pred_df['capacity_mw'].sum()
    capacity_factor = total_pred / total_capacity if total_capacity > 0 else 0
    
    print(f"✅ Total predicted: {total_pred:.0f} MW ({capacity_factor:.1%} capacity)")
    return pred_df

def main():
    print("=" * 70)
    print("  Real-Time Wind Generation Forecasting - Simplified")
    print("=" * 70)
    
    # Load models
    models = load_models()
    
    # Fetch NESO forecast
    try:
        neso_df = fetch_neso_forecast()
        neso_current = neso_df.iloc[0]['neso_forecast_mw']
        print(f"\n📊 NESO Current Forecast: {neso_current:.0f} MW")
    except Exception as e:
        print(f"⚠️  Could not fetch NESO forecast: {e}")
        neso_current = None
    
    # Fetch weather
    weather_df = fetch_recent_weather()
    
    # Generate predictions
    pred_df = predict_current_generation(models, weather_df)
    our_forecast = pred_df['predicted_mw'].sum()
    
    print(f"\n📊 Our ML Forecast: {our_forecast:.0f} MW")
    
    # Compare
    if neso_current is not None:
        diff_mw = our_forecast - neso_current
        diff_pct = (diff_mw / neso_current) * 100 if neso_current > 0 else 0
        
        print(f"\n🔍 Forecast Comparison:")
        print(f"   Our forecast:  {our_forecast:>8.0f} MW")
        print(f"   NESO forecast: {neso_current:>8.0f} MW")
        print(f"   Difference:    {diff_mw:>8.0f} MW ({diff_pct:+.1f}%)")
        
        # Trading signal
        if abs(diff_mw) < 500:
            signal = "HOLD"
            emoji = "⚪"
            action = "Within tolerance, no action"
        elif diff_mw > 500:
            signal = "SHORT"
            emoji = "🔴"
            action = "We predict MORE wind → Lower prices → Short power"
        else:
            signal = "LONG"
            emoji = "🟢"
            action = "We predict LESS wind → Higher prices → Long power"
        
        print(f"\n{emoji} Trading Signal: {signal}")
        print(f"   {action}")
    
    # Show top/bottom farms
    print(f"\n🏆 Top 5 Generators (by capacity factor):")
    pred_df['capacity_factor'] = pred_df['predicted_mw'] / pred_df['capacity_mw']
    top5 = pred_df.nlargest(5, 'capacity_factor')
    for idx, row in top5.iterrows():
        print(f"   {row['farm_name'][:30]:<30} {row['predicted_mw']:>6.0f} MW "
              f"({row['capacity_factor']:>4.0%}) @ {row['wind_speed_100m']:.1f} m/s")
    
    print(f"\n📉 Bottom 5 Generators:")
    bottom5 = pred_df.nsmallest(5, 'capacity_factor')
    for idx, row in bottom5.iterrows():
        print(f"   {row['farm_name'][:30]:<30} {row['predicted_mw']:>6.0f} MW "
              f"({row['capacity_factor']:>4.0%}) @ {row['wind_speed_100m']:.1f} m/s")
    
    print("\n✅ Analysis complete!")
    return 0

if __name__ == "__main__":
    exit(main())
