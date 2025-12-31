#!/usr/bin/env python3
"""
Multi-Horizon Wind Forecasting Models
Create 4 forecasting horizons: t+1h, t+6h, t+24h, t+72h
Purpose: Enable operational day-ahead wind forecasting for trading
Total models: 48 farms × 4 horizons = 192 models
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import os
from datetime import datetime, timedelta
import warnings
from multiprocessing import Pool, cpu_count

warnings.filterwarnings('ignore')

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODELS_DIR = "models/multi_horizon"

# Forecasting horizons (hours ahead)
HORIZONS = [1, 6, 24, 72]


def create_lagged_features(df, target_col, lags):
    """Create lagged features for time series forecasting."""
    for lag in lags:
        df[f'{target_col}_lag_{lag}h'] = df[target_col].shift(lag)
    return df


def create_rolling_features(df, col, windows):
    """Create rolling mean/std features."""
    for window in windows:
        df[f'{col}_rolling_mean_{window}h'] = df[col].rolling(window=window, min_periods=1).mean()
        df[f'{col}_rolling_std_{window}h'] = df[col].rolling(window=window, min_periods=1).std()
    return df


def prepare_multihorizon_data(farm_name, horizon_hours):
    """
    Prepare training data for specific forecast horizon.
    
    Features:
    - Current wind conditions (t)
    - Lagged generation (t-1h, t-6h, t-24h)
    - Rolling statistics (3h, 6h, 12h windows)
    - Time features (hour, day, month, season)
    - GFS forecast weather (if available)
    
    Target: Generation at t+horizon_hours
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get historical wind and generation data
    query = f"""
    WITH wind_data AS (
        SELECT
            TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
            AVG(wind_speed_100m) as wind_speed_100m,
            AVG(wind_direction_10m) as wind_direction_10m,
            AVG(wind_gusts_10m) as wind_gusts_10m
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
        WHERE farm_name = '{farm_name}'
          AND DATE(time_utc) >= '2021-01-01'
        GROUP BY hour_utc
    ),
    
    generation_data AS (
        SELECT
            bmu.farm_name,
            TIMESTAMP_TRUNC(TIMESTAMP(pn.settlementDate), HOUR) as hour_utc,
            SUM(pn.levelTo) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_pn` pn
        JOIN `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu` bmu
            ON pn.bmUnit = bmu.bm_unit_id
        WHERE bmu.farm_name = '{farm_name}'
          AND CAST(pn.settlementDate AS DATE) >= '2021-01-01'
          AND pn.levelTo >= 0
        GROUP BY bmu.farm_name, hour_utc
    )
    
    SELECT
        w.hour_utc,
        w.wind_speed_100m,
        w.wind_direction_10m,
        w.wind_gusts_10m,
        g.generation_mw
    FROM wind_data w
    LEFT JOIN generation_data g ON w.hour_utc = g.hour_utc
    WHERE g.generation_mw IS NOT NULL
    ORDER BY w.hour_utc
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if df.empty or len(df) < 1000:
            return pd.DataFrame()
        
        # Create target: generation at t+horizon
        df['target'] = df['generation_mw'].shift(-horizon_hours)
        
        # Create lagged generation features
        df = create_lagged_features(df, 'generation_mw', [1, 6, 12, 24, 48])
        
        # Create rolling statistics for wind
        df = create_rolling_features(df, 'wind_speed_100m', [3, 6, 12])
        df = create_rolling_features(df, 'generation_mw', [3, 6, 12])
        
        # Time features
        df['hour'] = df['hour_utc'].dt.hour
        df['day_of_week'] = df['hour_utc'].dt.dayofweek
        df['month'] = df['hour_utc'].dt.month
        df['season'] = df['month'].apply(lambda x: (x % 12 + 3) // 3)  # 1=winter, 2=spring, 3=summer, 4=fall
        
        # Derived features
        df['wind_direction_sin'] = np.sin(np.radians(df['wind_direction_10m']))
        df['wind_direction_cos'] = np.cos(np.radians(df['wind_direction_10m']))
        
        # Drop rows with NaN in target or key features
        df = df.dropna(subset=['target', 'generation_mw_lag_1h'])
        
        return df
        
    except Exception as e:
        print(f"  ⚠️  Error preparing data: {e}")
        return pd.DataFrame()


def train_horizon_model(args):
    """Train model for one farm and one horizon (parallel worker function)."""
    farm_name, horizon_hours = args
    
    print(f"  [{horizon_hours}h] {farm_name}")
    
    # Prepare data
    df = prepare_multihorizon_data(farm_name, horizon_hours)
    
    if df.empty:
        print(f"    ⚠️  No data available")
        return None
    
    # Define features
    feature_cols = [
        'wind_speed_100m', 'wind_direction_10m', 'wind_gusts_10m',
        'wind_direction_sin', 'wind_direction_cos',
        'generation_mw_lag_1h', 'generation_mw_lag_6h', 'generation_mw_lag_12h', 
        'generation_mw_lag_24h', 'generation_mw_lag_48h',
        'wind_speed_100m_rolling_mean_3h', 'wind_speed_100m_rolling_std_3h',
        'wind_speed_100m_rolling_mean_6h', 'wind_speed_100m_rolling_std_6h',
        'wind_speed_100m_rolling_mean_12h', 'wind_speed_100m_rolling_std_12h',
        'generation_mw_rolling_mean_3h', 'generation_mw_rolling_std_3h',
        'generation_mw_rolling_mean_6h', 'generation_mw_rolling_std_6h',
        'generation_mw_rolling_mean_12h', 'generation_mw_rolling_std_12h',
        'hour', 'day_of_week', 'month', 'season'
    ]
    
    # Filter to available features
    available_features = [f for f in feature_cols if f in df.columns]
    
    X = df[available_features]
    y = df['target']
    
    # Drop any remaining NaN values
    mask = ~(X.isna().any(axis=1) | y.isna())
    X = X[mask]
    y = y[mask]
    
    if len(X) < 1000:
        print(f"    ⚠️  Insufficient data after NaN removal")
        return None
    
    # Time series split for validation
    tscv = TimeSeriesSplit(n_splits=3)
    mae_scores = []
    
    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Train model
        model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            min_samples_split=20,
            min_samples_leaf=10,
            subsample=0.8,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Validate
        y_pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        mae_scores.append(mae)
    
    # Train final model on all data
    final_model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        min_samples_split=20,
        min_samples_leaf=10,
        subsample=0.8,
        random_state=42
    )
    
    final_model.fit(X, y)
    
    # Final predictions for metrics
    y_pred_final = final_model.predict(X)
    mae_final = mean_absolute_error(y, y_pred_final)
    rmse_final = np.sqrt(mean_squared_error(y, y_pred_final))
    r2_final = r2_score(y, y_pred_final)
    
    # Calculate relative error
    mean_generation = y.mean()
    relative_error = (mae_final / mean_generation * 100) if mean_generation > 0 else 0
    
    # Save model
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_filename = f"{MODELS_DIR}/{farm_name}_horizon_{horizon_hours}h.pkl"
    
    with open(model_filename, 'wb') as f:
        pickle.dump({
            'model': final_model,
            'features': available_features,
            'farm_name': farm_name,
            'horizon_hours': horizon_hours,
            'training_samples': len(df),
            'mae': mae_final,
            'rmse': rmse_final,
            'r2': r2_final,
            'mean_generation': mean_generation
        }, f)
    
    print(f"    ✅ MAE: {mae_final:.2f} MW ({relative_error:.1f}% relative)")
    
    return {
        'farm_name': farm_name,
        'horizon_hours': horizon_hours,
        'training_samples': len(df),
        'cv_mae_mean': np.mean(mae_scores),
        'cv_mae_std': np.std(mae_scores),
        'final_mae': mae_final,
        'final_rmse': rmse_final,
        'final_r2': r2_final,
        'mean_generation': mean_generation,
        'relative_error_pct': relative_error,
        'model_file': model_filename
    }


def main():
    """Train multi-horizon forecasting models for all farms."""
    print("="*80)
    print("Multi-Horizon Wind Forecasting - Model Training")
    print("="*80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get list of wind farms
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT farm_name
    FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu`
    ORDER BY farm_name
    """
    
    farms_df = client.query(query).to_dataframe()
    farms = farms_df['farm_name'].tolist()
    
    print(f"Wind farms: {len(farms)}")
    print(f"Horizons: {HORIZONS}")
    print(f"Total models: {len(farms) * len(HORIZONS)}")
    print()
    
    # Create training tasks (farm, horizon) pairs
    tasks = []
    for farm in farms[:10]:  # Test with first 10 farms
        for horizon in HORIZONS:
            tasks.append((farm, horizon))
    
    print(f"Training {len(tasks)} models...")
    print()
    
    # Train models in parallel
    num_cores = min(cpu_count(), 16)  # Use max 16 cores
    
    start_time = datetime.now()
    
    with Pool(processes=num_cores) as pool:
        results = pool.map(train_horizon_model, tasks)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    # Filter out None results
    results = [r for r in results if r is not None]
    
    # Save results summary
    if results:
        df_results = pd.DataFrame(results)
        output_file = 'multi_horizon_training_results.csv'
        df_results.to_csv(output_file, index=False)
        
        print("\n" + "="*80)
        print("Training Summary")
        print("="*80)
        print(f"Models trained: {len(results)}/{len(tasks)}")
        print(f"Training time: {duration:.1f} minutes")
        print(f"Avg time per model: {duration*60/len(results):.1f} seconds")
        print()
        
        # Summary by horizon
        for horizon in HORIZONS:
            horizon_results = df_results[df_results['horizon_hours'] == horizon]
            if not horizon_results.empty:
                print(f"Horizon t+{horizon}h:")
                print(f"  Farms: {len(horizon_results)}")
                print(f"  Avg MAE: {horizon_results['final_mae'].mean():.2f} MW")
                print(f"  Avg Relative Error: {horizon_results['relative_error_pct'].mean():.1f}%")
                print(f"  Avg R²: {horizon_results['final_r2'].mean():.3f}")
                print()
        
        print(f"Results saved to: {output_file}")
        print("="*80)
    
    print("\n" + "="*80)
    print("✅ Multi-Horizon Training Complete")
    print("="*80)
    print("\nNext Steps:")
    print("1. Review multi_horizon_training_results.csv")
    print("2. Test forecasting:")
    print("   python3 test_multi_horizon_forecast.py")
    print("3. Deploy to production:")
    print("   python3 realtime_multi_horizon_forecasting.py")
    print("4. Setup hourly cron job for continuous forecasting")
    print("="*80)


if __name__ == "__main__":
    main()
