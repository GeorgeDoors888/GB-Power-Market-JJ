#!/usr/bin/env python3
"""
Leakage-Safe Wind Forecasting Pipeline
Purpose: Prevent data leakage in production time series models
Methods: TimeSeriesSplit, parquet caching, strict time-alignment, temporal gaps
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import os
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODELS_DIR = "models/leakage_safe"
CACHE_DIR = "cache/features"

# Temporal gap settings (prevent leakage)
TRAIN_VAL_GAP_HOURS = 168  # 1 week gap between train and validation
VAL_TEST_GAP_HOURS = 168  # 1 week gap between validation and test
FORECAST_HORIZON_HOURS = 1  # Predicting 1 hour ahead


def load_or_compute_features(farm_name, cache_file):
    """
    Load features from parquet cache if exists, otherwise compute and cache.
    This avoids re-computing expensive feature engineering.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = f"{CACHE_DIR}/{cache_file}"
    
    if os.path.exists(cache_path):
        print(f"  📦 Loading from cache: {cache_file}")
        return pd.read_parquet(cache_path)
    
    print(f"  🔄 Computing features for {farm_name}...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get wind and generation data
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
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        return pd.DataFrame()
    
    # CRITICAL: All features must use shift() to avoid lookahead bias
    # We're predicting t+1, so features at time t can only use data up to t-1
    
    # Target: generation at t+1 (what we're predicting)
    df['target'] = df['generation_mw'].shift(-FORECAST_HORIZON_HOURS)
    
    # Lagged features (safe: using past data only)
    df['generation_lag_1h'] = df['generation_mw'].shift(1)
    df['generation_lag_2h'] = df['generation_mw'].shift(2)
    df['generation_lag_6h'] = df['generation_mw'].shift(6)
    df['generation_lag_24h'] = df['generation_mw'].shift(24)
    
    df['wind_speed_lag_1h'] = df['wind_speed_100m'].shift(1)
    df['wind_speed_lag_2h'] = df['wind_speed_100m'].shift(2)
    
    # Rolling features (safe: using past data only)
    # Note: rolling() looks backward by default, but we shift by 1 to ensure no current data
    df['wind_speed_rolling_3h'] = df['wind_speed_100m'].shift(1).rolling(window=3, min_periods=1).mean()
    df['wind_speed_rolling_6h'] = df['wind_speed_100m'].shift(1).rolling(window=6, min_periods=1).mean()
    df['wind_speed_rolling_12h'] = df['wind_speed_100m'].shift(1).rolling(window=12, min_periods=1).mean()
    
    df['generation_rolling_3h'] = df['generation_mw'].shift(1).rolling(window=3, min_periods=1).mean()
    df['generation_rolling_6h'] = df['generation_mw'].shift(1).rolling(window=6, min_periods=1).mean()
    
    # Rolling std (volatility)
    df['wind_speed_rolling_std_6h'] = df['wind_speed_100m'].shift(1).rolling(window=6, min_periods=1).std()
    df['generation_rolling_std_6h'] = df['generation_mw'].shift(1).rolling(window=6, min_periods=1).std()
    
    # Change features (safe: comparing past periods)
    df['wind_speed_change_1h'] = df['wind_speed_100m'].shift(1) - df['wind_speed_100m'].shift(2)
    df['generation_change_1h'] = df['generation_mw'].shift(1) - df['generation_mw'].shift(2)
    
    # Time features (safe: deterministic, no future information)
    df['hour'] = df['hour_utc'].dt.hour
    df['day_of_week'] = df['hour_utc'].dt.dayofweek
    df['month'] = df['hour_utc'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Cyclical encoding for hour (better than raw hour)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    
    # Direction encoding (safe: using lagged wind direction)
    df['wind_direction_lag_1h'] = df['wind_direction_10m'].shift(1)
    df['wind_dir_sin'] = np.sin(np.radians(df['wind_direction_lag_1h']))
    df['wind_dir_cos'] = np.cos(np.radians(df['wind_direction_lag_1h']))
    
    # Drop rows with NaN in critical columns
    df = df.dropna(subset=['target', 'generation_lag_1h'])
    
    # Save to cache
    df.to_parquet(cache_path, index=False)
    print(f"  💾 Cached to: {cache_path}")
    
    return df


def create_leakage_safe_splits(df, n_splits=5):
    """
    Create time series splits with temporal gaps to prevent leakage.
    
    Standard TimeSeriesSplit:
    Train: [----]
    Val:        [--]   ❌ Adjacent, potential leakage from rolling features
    
    Leakage-Safe Split:
    Train: [----]
    Gap:         [gap]
    Val:              [--]  ✅ Clean separation
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    splits = []
    
    for train_idx, val_idx in tscv.split(df):
        # Add gap: remove last N hours from train, first N hours from val
        train_cutoff = train_idx[-1] - TRAIN_VAL_GAP_HOURS
        val_start = val_idx[0] + TRAIN_VAL_GAP_HOURS
        
        # Ensure we don't remove too much data
        if train_cutoff < train_idx[0] or val_start > val_idx[-1]:
            continue
        
        # Create gap-adjusted indices
        train_safe = train_idx[train_idx <= train_cutoff]
        val_safe = val_idx[val_idx >= val_start]
        
        if len(train_safe) > 1000 and len(val_safe) > 100:
            splits.append((train_safe, val_safe))
    
    return splits


def train_leakage_safe_model(farm_name):
    """Train model with strict leakage prevention."""
    print(f"\n{'='*80}")
    print(f"Farm: {farm_name}")
    print(f"{'='*80}")
    
    # Load or compute features (with caching)
    cache_file = f"{farm_name}_features.parquet"
    df = load_or_compute_features(farm_name, cache_file)
    
    if df.empty:
        print(f"  ⚠️  No data available")
        return None
    
    print(f"  📊 Total samples: {len(df):,}")
    print(f"  📅 Date range: {df['hour_utc'].min()} to {df['hour_utc'].max()}")
    
    # Define features (all lagged/safe)
    feature_cols = [
        'generation_lag_1h', 'generation_lag_2h', 'generation_lag_6h', 'generation_lag_24h',
        'wind_speed_lag_1h', 'wind_speed_lag_2h',
        'wind_speed_rolling_3h', 'wind_speed_rolling_6h', 'wind_speed_rolling_12h',
        'generation_rolling_3h', 'generation_rolling_6h',
        'wind_speed_rolling_std_6h', 'generation_rolling_std_6h',
        'wind_speed_change_1h', 'generation_change_1h',
        'hour_sin', 'hour_cos', 'day_of_week', 'month', 'is_weekend',
        'wind_dir_sin', 'wind_dir_cos'
    ]
    
    # Filter to available features
    available_features = [f for f in feature_cols if f in df.columns]
    
    X = df[available_features]
    y = df['target']
    
    # Leakage-safe splits with temporal gaps
    print(f"\n  🔒 Creating leakage-safe splits (gap: {TRAIN_VAL_GAP_HOURS}h)...")
    splits = create_leakage_safe_splits(df)
    
    print(f"  ✅ {len(splits)} validation splits created")
    
    # Cross-validation with leakage-safe splits
    cv_scores = []
    
    for i, (train_idx, val_idx) in enumerate(splits, 1):
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
        cv_scores.append(mae)
        
        print(f"    Split {i}: MAE = {mae:.2f} MW (train: {len(train_idx):,}, val: {len(val_idx):,})")
    
    print(f"\n  📈 Cross-Validation Results:")
    print(f"    Mean MAE: {np.mean(cv_scores):.2f} MW")
    print(f"    Std MAE: {np.std(cv_scores):.2f} MW")
    
    # Train final model on all data
    print(f"\n  🎯 Training final model...")
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
    
    # Final metrics
    y_pred_final = final_model.predict(X)
    mae_final = mean_absolute_error(y, y_pred_final)
    rmse_final = np.sqrt(mean_squared_error(y, y_pred_final))
    r2_final = r2_score(y, y_pred_final)
    
    print(f"  ✅ Final MAE: {mae_final:.2f} MW")
    print(f"  ✅ Final RMSE: {rmse_final:.2f} MW")
    print(f"  ✅ Final R²: {r2_final:.3f}")
    
    # Save model
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_file = f"{MODELS_DIR}/{farm_name}_leakage_safe.pkl"
    
    with open(model_file, 'wb') as f:
        pickle.dump({
            'model': final_model,
            'features': available_features,
            'farm_name': farm_name,
            'forecast_horizon_hours': FORECAST_HORIZON_HOURS,
            'train_val_gap_hours': TRAIN_VAL_GAP_HOURS,
            'cv_mae_mean': np.mean(cv_scores),
            'cv_mae_std': np.std(cv_scores),
            'final_mae': mae_final,
            'final_rmse': rmse_final,
            'final_r2': r2_final,
            'training_samples': len(df),
            'leakage_safe': True
        }, f)
    
    print(f"  💾 Model saved: {model_file}")
    
    return {
        'farm_name': farm_name,
        'training_samples': len(df),
        'cv_splits': len(splits),
        'cv_mae_mean': np.mean(cv_scores),
        'cv_mae_std': np.std(cv_scores),
        'final_mae': mae_final,
        'final_rmse': rmse_final,
        'final_r2': r2_final,
        'model_file': model_file
    }


def main():
    """Train leakage-safe models for all farms."""
    print("="*80)
    print("Leakage-Safe Wind Forecasting Pipeline")
    print("="*80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Leakage Prevention Measures:")
    print(f"  ✅ All features use shift() to avoid lookahead bias")
    print(f"  ✅ Temporal gaps: {TRAIN_VAL_GAP_HOURS}h between train/val")
    print(f"  ✅ TimeSeriesSplit (not random K-Fold)")
    print(f"  ✅ Parquet caching for reproducibility")
    print(f"  ✅ Forecast horizon: {FORECAST_HORIZON_HOURS}h ahead")
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
    print()
    
    # Train models for first 5 farms (testing)
    results = []
    
    for i, farm in enumerate(farms[:5], 1):
        print(f"\n[{i}/5]")
        result = train_leakage_safe_model(farm)
        if result:
            results.append(result)
    
    # Save results
    if results:
        df_results = pd.DataFrame(results)
        output_file = 'leakage_safe_training_results.csv'
        df_results.to_csv(output_file, index=False)
        
        print("\n" + "="*80)
        print("Training Summary")
        print("="*80)
        print(f"Models trained: {len(results)}")
        print(f"Avg CV MAE: {df_results['cv_mae_mean'].mean():.2f} MW")
        print(f"Avg Final MAE: {df_results['final_mae'].mean():.2f} MW")
        print(f"Avg R²: {df_results['final_r2'].mean():.3f}")
        print()
        print(f"Results saved to: {output_file}")
        print("="*80)
    
    print("\n" + "="*80)
    print("✅ Leakage-Safe Pipeline Complete")
    print("="*80)
    print("\nKey Features:")
    print("  • Strict temporal ordering (no future data in features)")
    print("  • Temporal gaps prevent rolling feature leakage")
    print("  • Parquet caching for efficiency and reproducibility")
    print("  • Production-ready for real-time forecasting")
    print("="*80)


if __name__ == "__main__":
    main()
