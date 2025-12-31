#!/usr/bin/env python3
"""
Train wind power curve models using ACTUAL generation data from boalf_with_prices.
This uses real BM unit acceptances (MW dispatch) instead of theoretical curves.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.ensemble import GradientBoostingRegressor
import joblib
import os
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODEL_DIR = "models/wind_power_curves_actual"
os.makedirs(MODEL_DIR, exist_ok=True)

def main():
    print("=" * 70)
    print("Wind Power Curve Training - Using ACTUAL Generation Data")
    print("=" * 70)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Step 1: Join weather data with actual BM unit generation (B1610 Physical Notifications)
    print("\n📊 Creating training dataset...")
    print("   Joining: openmeteo_wind_historic + bmrs_pn (B1610 actual generation)")
    print("   Note: B1610 = Actual Generation Output Per Generation Unit")
    
    query = f"""
    WITH weather_data AS (
        SELECT 
            farm_name,
            TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
            EXTRACT(HOUR FROM time_utc) as hour_of_day,
            EXTRACT(MONTH FROM time_utc) as month,
            EXTRACT(DAYOFWEEK FROM time_utc) as day_of_week,
            AVG(wind_speed_100m) as wind_speed_100m,
            AVG(wind_direction_10m) as wind_direction_10m,
            AVG(wind_gusts_10m) as wind_gusts_10m,
            MAX(capacity_mw) as capacity_mw
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
        WHERE wind_speed_100m IS NOT NULL
          AND wind_speed_100m BETWEEN 0 AND 50
          AND time_utc >= '2020-01-01'
          AND time_utc < '2025-11-01'
        GROUP BY farm_name, hour_utc, hour_of_day, month, day_of_week
    ),
    bm_mapping AS (
        SELECT 
            farm_name,
            bm_unit_id,
            capacity_mw as unit_capacity_mw
        FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu`
    ),
    actual_generation AS (
        SELECT 
            bmUnit as bm_unit_id,
            TIMESTAMP_TRUNC(TIMESTAMP(CAST(settlementDate AS DATE)), HOUR) as hour_utc,
            AVG(levelTo) as generation_mw  -- Average across settlement periods in the hour
        FROM `{PROJECT_ID}.{DATASET}.bmrs_pn`
        WHERE CAST(settlementDate AS DATE) >= '2020-01-01'
          AND CAST(settlementDate AS DATE) < '2025-11-01'
          AND levelTo > 0  -- B1610 actual generation output
        GROUP BY bm_unit_id, hour_utc
    )
    SELECT 
        w.farm_name,
        w.hour_utc as time_utc,
        w.hour_of_day,
        w.month,
        w.day_of_week,
        w.wind_speed_100m,
        w.wind_direction_10m,
        w.wind_gusts_10m,
        w.capacity_mw as farm_capacity_mw,
        m.bm_unit_id,
        m.unit_capacity_mw,
        COALESCE(g.generation_mw, 0) as actual_generation_mw
    FROM weather_data w
    INNER JOIN bm_mapping m
        ON w.farm_name = m.farm_name
    LEFT JOIN actual_generation g
        ON m.bm_unit_id = g.bm_unit_id
        AND w.hour_utc = g.hour_utc
    """
    
    print("   Running BigQuery (may take 60-120 seconds for hourly aggregation)...")
    df = client.query(query).to_dataframe()
    
    if len(df) == 0:
        print("❌ No data returned from query!")
        return 1
    
    print(f"✅ Loaded {len(df):,} training samples")
    print(f"   Farms: {df['farm_name'].nunique()}")
    print(f"   BM Units: {df['bm_unit_id'].nunique()}")
    print(f"   Date range: {df['time_utc'].min()} to {df['time_utc'].max()}")
    print(f"   Avg generation: {df['actual_generation_mw'].mean():.1f} MW")
    print(f"   Max generation: {df['actual_generation_mw'].max():.1f} MW")
    
    # Aggregate to farm level (sum all BM units)
    print("\n🔄 Aggregating BM units to farm level...")
    farm_df = df.groupby(['farm_name', 'time_utc', 'hour_of_day', 'month', 'day_of_week',
                          'wind_speed_100m', 'wind_direction_10m', 'wind_gusts_10m', 
                          'farm_capacity_mw']).agg({
        'actual_generation_mw': 'sum'
    }).reset_index()
    
    print(f"✅ Aggregated to {len(farm_df):,} farm-level observations")
    
    # Train models per farm
    print("\n🏗️  Training farm-specific models...")
    print(f"{'Farm':<35} {'Samples':>8} {'Avg MW':>8} {'Max MW':>8} {'MAE':>8} {'RMSE':>8}")
    print("-" * 90)
    
    features = ['wind_speed_100m', 'wind_direction_10m', 'hour_of_day', 
                'month', 'day_of_week', 'wind_gusts_10m']
    
    trained_count = 0
    for farm_name in sorted(farm_df['farm_name'].unique()):
        farm_data = farm_df[farm_df['farm_name'] == farm_name].copy()
        
        # Filter to samples with actual generation data
        farm_data = farm_data[farm_data['actual_generation_mw'] > 0]
        
        if len(farm_data) < 100:
            print(f"  ⚠️  {farm_name[:34]:<34} - Insufficient data ({len(farm_data)} samples)")
            continue
        
        # Train/test split by date
        train_mask = farm_data['time_utc'] < '2025-01-01'
        X_train = farm_data[train_mask][features].fillna(0)
        y_train = farm_data[train_mask]['actual_generation_mw']
        X_test = farm_data[~train_mask][features].fillna(0)
        y_test = farm_data[~train_mask]['actual_generation_mw']
        
        if len(X_test) < 10:
            print(f"  ⚠️  {farm_name[:34]:<34} - Insufficient test data")
            continue
        
        # Train model
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=20,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = np.mean(np.abs(y_test - y_pred))
        rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
        
        avg_mw = farm_data['actual_generation_mw'].mean()
        max_mw = farm_data['actual_generation_mw'].max()
        
        print(f"  ✅ {farm_name[:34]:<34} {len(farm_data):>8,} {avg_mw:>8.0f} {max_mw:>8.0f} {mae:>8.0f} {rmse:>8.0f}")
        
        # Save model
        model_path = os.path.join(MODEL_DIR, f"{farm_name.replace(' ', '_')}.joblib")
        joblib.dump(model, model_path)
        trained_count += 1
    
    print("\n" + "=" * 90)
    print(f"✅ Training complete! {trained_count} models saved to {MODEL_DIR}/")
    print(f"   Models use ACTUAL generation data from bmrs_pn (B1610)")
    print(f"   B1610 = Actual Generation Output Per Generation Unit")
    print(f"   Date range: 2020-2025 (5 years)")
    print("=" * 90)
    
    return 0

if __name__ == "__main__":
    exit(main())
