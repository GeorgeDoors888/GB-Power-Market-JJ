#!/usr/bin/env python3
"""
Build power curve models: 100m wind speed → MW generation output.
Train farm-specific ML models using historical weather + actual generation.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
from datetime import datetime

# -------------------------
# CONFIGURATION
# -------------------------

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

# Model output directory
MODEL_DIR = "models/wind_power_curves"
os.makedirs(MODEL_DIR, exist_ok=True)

# -------------------------
# DATA PREPARATION
# -------------------------

def create_training_dataset():
    """
    Join historical weather data with actual offshore wind generation.
    Uses bmrs_fuelinst_iris for offshore wind totals (simplest approach).
    """
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    print("📊 Creating training dataset...")
    print("   Joining: openmeteo_wind_historic + bmrs_fuelinst_iris (offshore wind)")
    print("   Note: Using GB-wide offshore wind as proxy for training")
    
    query = f"""
    WITH weather AS (
        SELECT 
            farm_name,
            time_utc,
            wind_speed_100m,
            wind_speed_10m,
            wind_direction_10m,
            wind_gusts_10m,
            capacity_mw as farm_capacity_mw
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
        WHERE wind_speed_100m IS NOT NULL
    ),
    offshore_wind_gen AS (
        -- Get offshore wind generation from fuel mix
        SELECT
            settlementDate,
            settlementPeriod,
            generation as gb_offshore_wind_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE fuelType = 'WIND'
          AND psrType = 'Wind Offshore'
          AND generation IS NOT NULL
          AND generation >= 0
    )
    SELECT
        w.farm_name,
        w.time_utc,
        EXTRACT(HOUR FROM w.time_utc) as hour_of_day,
        EXTRACT(MONTH FROM w.time_utc) as month,
        EXTRACT(DAYOFWEEK FROM w.time_utc) as day_of_week,
        w.wind_speed_100m,
        w.wind_speed_10m,
        w.wind_direction_10m,
        w.wind_gusts_10m,
        w.farm_capacity_mw,
        g.gb_offshore_wind_mw,
        -- Estimate farm generation proportional to capacity
        (g.gb_offshore_wind_mw * w.farm_capacity_mw / 16410.0) as estimated_generation_mw,
        g.gb_offshore_wind_mw / 16410.0 as gb_capacity_factor
    FROM weather w
    JOIN offshore_wind_gen g
        ON DATE(w.time_utc) = g.settlementDate
        AND EXTRACT(HOUR FROM w.time_utc) * 2 + 1 = g.settlementPeriod
    WHERE w.wind_speed_100m BETWEEN 0 AND 50  -- Realistic wind speeds
      AND g.gb_offshore_wind_mw >= 0
      AND g.gb_offshore_wind_mw <= 17000  -- Max GB offshore capacity + margin
    ORDER BY w.farm_name, w.time_utc
    """
    
    print("   Running BigQuery (may take 30-60 seconds)...")
    df = client.query(query).to_dataframe()
    
    print(f"✅ Training dataset: {len(df):,} rows")
    print(f"   Farms: {df['farm_name'].nunique()}")
    print(f"   Date range: {df['time_utc'].min()} to {df['time_utc'].max()}")
    
    return df

# -------------------------
# MODEL TRAINING
# -------------------------

def train_power_curve_model(farm_df, farm_name):
    """
    Train gradient boosting model for a single farm.
    
    Args:
        farm_df: DataFrame with features and target for one farm
        farm_name: Name of the wind farm
    
    Returns:
        Trained model, test metrics
    """
    print(f"\n🏗️  Training model: {farm_name}")
    print(f"   Training samples: {len(farm_df):,}")
    
    # Feature engineering
    features = [
        'wind_speed_100m',
        'wind_direction_10m',
        'hour_of_day',
        'month',
        'day_of_week',
        'wind_gusts_10m'
    ]
    
    X = farm_df[features].copy()
    y = farm_df['estimated_generation_mw'].copy()
    
    # Handle missing values
    X = X.fillna(X.median())
    
    # Split: 2020-2024 train, 2025 test
    train_mask = farm_df['time_utc'] < '2025-01-01'
    test_mask = farm_df['time_utc'] >= '2025-01-01'
    
    X_train = X[train_mask]
    y_train = y[train_mask]
    X_test = X[test_mask]
    y_test = y[test_mask]
    
    print(f"   Train: {len(X_train):,} rows (2020-2024)")
    print(f"   Test: {len(X_test):,} rows (2025)")
    
    if len(X_test) < 10:
        print(f"   ⚠️  Insufficient test data, skipping")
        return None, None
    
    # Train model
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Clip predictions to [0, capacity]
    capacity = farm_df['farm_capacity_mw'].iloc[0]
    y_pred_test = np.clip(y_pred_test, 0, capacity)
    
    metrics = {
        'train_mae': mean_absolute_error(y_train, y_pred_train),
        'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
        'train_r2': r2_score(y_train, y_pred_train),
        'test_mae': mean_absolute_error(y_test, y_pred_test),
        'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
        'test_r2': r2_score(y_test, y_pred_test),
        'capacity_mw': capacity,
        'train_samples': len(X_train),
        'test_samples': len(X_test)
    }
    
    print(f"   📊 Train MAE: {metrics['train_mae']:.1f} MW, R²: {metrics['train_r2']:.3f}")
    print(f"   📊 Test MAE: {metrics['test_mae']:.1f} MW, R²: {metrics['test_r2']:.3f}")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"   🔝 Top features:")
    for _, row in importance.head(3).iterrows():
        print(f"      {row['feature']}: {row['importance']:.3f}")
    
    # Save model
    model_path = os.path.join(MODEL_DIR, f"{farm_name.replace(' ', '_')}.joblib")
    joblib.dump(model, model_path)
    print(f"   💾 Saved: {model_path}")
    
    return model, metrics

# -------------------------
# MAIN EXECUTION
# -------------------------

def main():
    print("=" * 70)
    print("Wind Power Curve Model Training")
    print("=" * 70)
    
    # Create training dataset
    df = create_training_dataset()
    
    if len(df) == 0:
        print("\n❌ No training data available!")
        print("   Ensure openmeteo_wind_historic and bmrs_indgen_iris tables have data")
        return 1
    
    # Train models for each farm
    print("\n" + "=" * 70)
    print("Training Farm-Specific Models")
    print("=" * 70)
    
    all_metrics = []
    
    for farm_name in df['farm_name'].unique():
        farm_df = df[df['farm_name'] == farm_name]
        model, metrics = train_power_curve_model(farm_df, farm_name)
        
        if metrics:
            metrics['farm_name'] = farm_name
            all_metrics.append(metrics)
    
    # Summary report
    if all_metrics:
        metrics_df = pd.DataFrame(all_metrics)
        
        print("\n" + "=" * 70)
        print("📊 MODEL PERFORMANCE SUMMARY")
        print("=" * 70)
        
        for _, row in metrics_df.iterrows():
            print(f"\n{row['farm_name']} ({row['capacity_mw']:.0f} MW):")
            print(f"  Test MAE: {row['test_mae']:.1f} MW ({row['test_mae']/row['capacity_mw']*100:.1f}% of capacity)")
            print(f"  Test RMSE: {row['test_rmse']:.1f} MW")
            print(f"  Test R²: {row['test_r2']:.3f}")
        
        print(f"\n📊 AVERAGE PERFORMANCE:")
        print(f"  Avg Test MAE: {metrics_df['test_mae'].mean():.1f} MW")
        print(f"  Avg Test R²: {metrics_df['test_r2'].mean():.3f}")
        
        # Save metrics
        metrics_df.to_csv('models/wind_power_curves/model_metrics.csv', index=False)
        print(f"\n💾 Saved metrics to models/wind_power_curves/model_metrics.csv")
    
    print("\n✅ Model training complete!")
    print(f"   Models saved in: {MODEL_DIR}/")
    print(f"   Farms trained: {len(all_metrics)}")
    
    return 0

if __name__ == "__main__":
    exit(main())
