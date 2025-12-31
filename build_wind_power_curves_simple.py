#!/usr/bin/env python3
"""
Simple power curve training using theoretical power curves.
Since we don't have farm-level generation data, use physics-based approach.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.ensemble import GradientBoostingRegressor
import joblib
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODEL_DIR = "models/wind_power_curves"
os.makedirs(MODEL_DIR, exist_ok=True)

def theoretical_power_curve(wind_speed_ms):
    """
    Theoretical offshore wind turbine power curve.
    Based on typical 15 MW turbines with:
    - Cut-in: 3 m/s
    - Rated: 12 m/s  
    - Cut-out: 25 m/s
    """
    capacity_factor = np.zeros_like(wind_speed_ms, dtype=float)
    
    # Below cut-in
    mask_cutin = wind_speed_ms < 3
    capacity_factor[mask_cutin] = 0
    
    # Between cut-in and rated (cubic relationship)
    mask_ramp = (wind_speed_ms >= 3) & (wind_speed_ms < 12)
    capacity_factor[mask_ramp] = ((wind_speed_ms[mask_ramp] - 3) / 9) ** 3
    
    # Rated power
    mask_rated = (wind_speed_ms >= 12) & (wind_speed_ms < 25)
    capacity_factor[mask_rated] = 1.0
    
    # Above cut-out
    mask_cutout = wind_speed_ms >= 25
    capacity_factor[mask_cutout] = 0
    
    return capacity_factor

def main():
    print("=" * 70)
    print("Wind Power Curve Training - Theoretical Approach")
    print("=" * 70)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Fetch weather data
    print("\n📊 Fetching historical weather data...")
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
    WHERE wind_speed_100m IS NOT NULL
      AND wind_speed_100m BETWEEN 0 AND 50
    ORDER BY farm_name, time_utc
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Loaded {len(df):,} training samples")
    
    # Calculate theoretical generation
    df['capacity_factor'] = theoretical_power_curve(df['wind_speed_100m'].values)
    df['generation_mw'] = df['capacity_factor'] * df['capacity_mw']
    
    print(f"\n📈 Theoretical performance:")
    print(f"   Avg capacity factor: {df['capacity_factor'].mean():.1%}")
    print(f"   Max generation: {df['generation_mw'].max():.0f} MW")
    
    # Train models per farm
    print("\n🏗️  Training farm-specific models...")
    
    features = ['wind_speed_100m', 'wind_direction_10m', 'hour_of_day', 'month', 'day_of_week', 'wind_gusts_10m']
    
    for farm_name in df['farm_name'].unique():
        farm_df = df[df['farm_name'] == farm_name].copy()
        
        # Train/test split
        train_mask = farm_df['time_utc'] < '2025-01-01'
        X_train = farm_df[train_mask][features].fillna(0)
        y_train = farm_df[train_mask]['generation_mw']
        X_test = farm_df[~train_mask][features].fillna(0)
        y_test = farm_df[~train_mask]['generation_mw']
        
        if len(X_test) < 10:
            print(f"  ⚠️  {farm_name}: Insufficient test data")
            continue
        
        # Train
        model = GradientBoostingRegressor(
            n_estimators=50,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = np.mean(np.abs(y_test - y_pred))
        rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
        
        print(f"  ✅ {farm_name[:30]:<30} MAE: {mae:5.0f} MW, RMSE: {rmse:5.0f} MW")
        
        # Save
        model_path = os.path.join(MODEL_DIR, f"{farm_name.replace(' ', '_')}.joblib")
        joblib.dump(model, model_path)
    
    print(f"\n✅ Training complete! Models saved to {MODEL_DIR}/")
    return 0

if __name__ == "__main__":
    exit(main())
