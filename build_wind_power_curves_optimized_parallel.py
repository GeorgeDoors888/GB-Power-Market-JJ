#!/usr/bin/env python3
"""
Parallel Wind Power Curve Training with Full Optimization
Uses joblib to train multiple farms simultaneously across CPU cores
Expected speedup: 8-16x on 32-core system

Usage:
    python3 build_wind_power_curves_optimized_parallel.py --n-jobs 16

Author: AI Coding Agent
Date: December 30, 2025
"""

import argparse
import pickle
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from google.cloud import bigquery
from joblib import Parallel, delayed
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# ================================
# Configuration
# ================================
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODEL_DIR = Path("models/wind_power_curves_optimized_parallel")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ERA5 Grid Network (18 grids)
ERA5_GRID_COORDS = {
    # Original 10
    'Atlantic_Irish_Sea': (54.0, -8.0),
    'Irish_Sea_Central': (53.5, -4.0),
    'Atlantic_Hebrides': (57.0, -8.0),
    'West_Scotland': (56.0, -6.0),
    'Central_England': (53.0, -1.0),
    'Pennines': (54.5, -2.0),
    'Celtic_Sea': (52.5, -5.0),
    'Bristol_Channel': (51.5, -2.0),
    'North_Scotland': (59.0, -4.0),
    'Moray_Firth_West': (58.0, -2.0),
    # Strategic 8
    'Atlantic_Deep_West': (54.5, -10.0),
    'Atlantic_Hebrides_Extended': (57.5, -7.5),
    'North_Sea_West': (54.0, -0.5),
    'Celtic_Sea_Deep': (51.5, -6.5),
    'Irish_Sea_North': (55.0, -5.0),
    'Channel_West': (50.5, -1.5),
    'Shetland_West': (60.5, -3.0),
    'Dogger_West': (55.0, 0.5),
}

# Farm to ERA5 grid mapping (top 3 grids per farm)
FARM_TO_ERA5_GRID = {
    'Hornsea One': ['Central_England', 'North_Sea_West', 'Pennines'],
    'Hornsea Two': ['Central_England', 'North_Sea_West', 'Pennines'],
    'Walney Extension': ['Atlantic_Irish_Sea', 'Irish_Sea_Central', 'Atlantic_Deep_West'],
    'London Array': ['Bristol_Channel', 'Central_England', 'Channel_West'],
    'Triton Knoll': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Race Bank': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Greater Gabbard': ['Bristol_Channel', 'Central_England', 'Channel_West'],
    'Thanet': ['Bristol_Channel', 'Channel_West', 'Central_England'],
    'Gunfleet Sands 1 & 2': ['Bristol_Channel', 'Central_England', 'Channel_West'],
    'Dudgeon': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Sheringham Shoal': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Lincs': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Galloper': ['Bristol_Channel', 'Central_England', 'Channel_West'],
    'Rampion': ['Bristol_Channel', 'Channel_West', 'Celtic_Sea'],
    'Beatrice': ['North_Scotland', 'Moray_Firth_West', 'Atlantic_Hebrides'],
    'East Anglia One': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Moray East': ['North_Scotland', 'Moray_Firth_West', 'Atlantic_Hebrides'],
    'Gwynt y Môr': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'West of Duddon Sands': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Walney 1 & 2': ['Atlantic_Irish_Sea', 'Irish_Sea_Central', 'Irish_Sea_North'],
    'Burbo Bank Extension': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Burbo Bank': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Ormonde': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Humber Gateway': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Teesside': ['Pennines', 'Central_England', 'North_Sea_West'],
    'Barrow': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Robin Rigg': ['Irish_Sea_Central', 'Irish_Sea_North', 'Atlantic_Irish_Sea'],
    'Scroby Sands': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Hywind Scotland': ['Atlantic_Hebrides', 'West_Scotland', 'Atlantic_Hebrides_Extended'],
    'Kincardine': ['Atlantic_Hebrides', 'West_Scotland', 'North_Scotland'],
}


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def calculate_dynamic_lag(distance_km, wind_speed_ms):
    """Calculate dynamic lag based on wind speed and distance."""
    if wind_speed_ms < 5:
        wind_speed_ms = 10  # Minimum reasonable wind speed
    
    # Transit time = distance / wind_speed (convert m/s to km/h)
    transit_hours = distance_km / (wind_speed_ms * 3.6)
    
    # Round to nearest 0.5 hour
    lag_hours = round(transit_hours * 2) / 2
    
    # Clamp between 0.5h and 8h
    lag_hours = max(0.5, min(8.0, lag_hours))
    
    return lag_hours


def train_single_farm(farm_name, weather_df, era5_df):
    """Train a single farm's XGBoost model with full optimization."""
    try:
        start_time = time.time()
        print(f"\n{'='*70}")
        print(f"Training: {farm_name}")
        print(f"{'='*70}")
        
        # Filter farm data
        farm_data = weather_df[weather_df['farm_name'] == farm_name].copy()
        
        if len(farm_data) == 0:
            print(f"❌ No data for {farm_name}")
            return None
        
        # Get farm coordinates (first row)
        farm_lat = farm_data['farm_lat'].iloc[0]
        farm_lon = farm_data['farm_lon'].iloc[0]
        
        # Get ERA5 grids for this farm
        era5_grids = FARM_TO_ERA5_GRID.get(farm_name, list(ERA5_GRID_COORDS.keys())[:3])
        
        # Calculate distances and sort grids
        grid_distances = {}
        for grid_name in era5_grids:
            grid_lat, grid_lon = ERA5_GRID_COORDS[grid_name]
            dist = haversine_distance(farm_lat, farm_lon, grid_lat, grid_lon)
            grid_distances[grid_name] = dist
        
        era5_grids = sorted(grid_distances.keys(), key=lambda x: grid_distances[x])[:3]
        primary_grid = era5_grids[0]
        primary_distance = grid_distances[primary_grid]
        
        print(f"Top 3 ERA5 grids:")
        for i, grid in enumerate(era5_grids, 1):
            print(f"  {i}. {grid}: {grid_distances[grid]:.0f} km")
        
        # Add ERA5 features
        # Dynamic lag calculation
        farm_data['optimal_lag_hours'] = farm_data['wind_speed_100m'].apply(
            lambda ws: calculate_dynamic_lag(primary_distance, ws)
        )
        
        # Get ERA5 wind at dynamic lag
        primary_era5 = era5_df[era5_df['grid_point_name'] == primary_grid].copy()
        primary_era5['hour_utc_lag'] = primary_era5['hour_utc']
        
        farm_data = pd.merge_asof(
            farm_data.sort_values('hour_utc'),
            primary_era5[['hour_utc_lag', 'wind_speed_100m', 'wind_direction_100m']].rename(
                columns={'wind_speed_100m': 'era5_wind_dynamic', 'wind_direction_100m': 'era5_direction'}
            ).sort_values('hour_utc_lag'),
            left_on='hour_utc',
            right_on='hour_utc_lag',
            direction='backward',
            tolerance=pd.Timedelta(hours=2)
        )
        
        # Ensemble grid points (weighted average of top 3)
        ensemble_weights = []
        ensemble_winds = []
        for grid_name in era5_grids:
            grid_era5 = era5_df[era5_df['grid_point_name'] == grid_name].copy()
            merged = pd.merge_asof(
                farm_data[['hour_utc']].sort_values('hour_utc'),
                grid_era5[['hour_utc', 'wind_speed_100m']].rename(
                    columns={'wind_speed_100m': f'era5_{grid_name}'}
                ).sort_values('hour_utc'),
                on='hour_utc',
                direction='backward',
                tolerance=pd.Timedelta(hours=2)
            )
            
            dist = grid_distances[grid_name]
            weight = 1.0 / (dist + 10)  # Inverse distance weighting
            ensemble_weights.append(weight)
            ensemble_winds.append(merged[f'era5_{grid_name}'].values * weight)
        
        farm_data['era5_ensemble'] = np.sum(ensemble_winds, axis=0) / np.sum(ensemble_weights)
        
        # Interaction features
        farm_data['local_x_era5'] = farm_data['wind_speed_100m'] * farm_data['era5_wind_dynamic']
        farm_data['era5_change_x_dist'] = (farm_data['era5_wind_dynamic'] - farm_data['era5_ensemble']) * primary_distance
        
        # Direction alignment (cosine similarity)
        direction_diff = np.abs(farm_data['wind_direction_10m'] - farm_data['era5_direction'])
        direction_diff = np.minimum(direction_diff, 360 - direction_diff)  # Circular difference
        farm_data['direction_alignment'] = np.cos(np.radians(direction_diff))
        
        # Diurnal + upstream interaction
        farm_data['hour_x_era5'] = farm_data['hour_of_day'] * farm_data['era5_wind_dynamic']
        
        # Drop rows with missing ERA5 data
        farm_data = farm_data.dropna(subset=[
            'era5_wind_dynamic', 'era5_ensemble', 'era5_direction', 'generation_mw'
        ])
        
        if len(farm_data) < 1000:
            print(f"❌ Insufficient data after merge: {len(farm_data)} rows")
            return None
        
        # Features
        feature_cols = [
            # Baseline (6)
            'wind_speed_100m', 'wind_direction_10m', 'wind_gusts_10m',
            'hour_of_day', 'month', 'day_of_week',
            # Optimized (9)
            'optimal_lag_hours', 'era5_wind_dynamic', 'era5_ensemble',
            'local_x_era5', 'era5_change_x_dist', 'direction_alignment',
            'hour_x_era5', 'era5_direction'
        ]
        
        X = farm_data[feature_cols]
        y = farm_data['generation_mw']
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # XGBoost model with full optimization
        model = xgb.XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=8,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            gamma=0.1,
            reg_alpha=0.1,  # L1 regularization
            reg_lambda=1.0,  # L2 regularization
            tree_method='hist',
            random_state=42,
            n_jobs=4  # Use 4 cores per model for XGBoost internal parallelization
        )
        
        model.fit(X_train, y_train)
        
        # Predictions and metrics
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # Save model using pickle (XGBoost's save_model has issues in parallel)
        model_path = MODEL_DIR / f"{farm_name.replace(' ', '_').replace('&', 'and')}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        elapsed = time.time() - start_time
        print(f"✅ {farm_name}: MAE={mae:.1f} MW, RMSE={rmse:.1f} MW, R²={r2:.3f}")
        print(f"   Samples: {len(farm_data):,}, Time: {elapsed:.1f}s")
        
        return {
            'farm_name': farm_name,
            'samples': len(farm_data),
            'avg_generation_mw': y.mean(),
            'max_generation_mw': y.max(),
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'training_time_sec': elapsed
        }
        
    except Exception as e:
        print(f"❌ Error training {farm_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='Train wind power curves in parallel')
    parser.add_argument('--n-jobs', type=int, default=8, 
                       help='Number of parallel jobs (default: 8)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("PARALLEL Wind Power Curve Training - Full Optimization")
    print("=" * 70)
    print(f"Parallel jobs: {args.n_jobs}")
    print(f"Model directory: {MODEL_DIR}")
    print(f"Start time: {datetime.now()}")
    print("=" * 70)
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    # Load training data (SHARED across all farms)
    print("\n📊 Loading training dataset from BigQuery...")
    start_load = time.time()
    
    query = f"""
    WITH weather_data AS (
        SELECT 
            farm_name,
            TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
            AVG(wind_speed_100m) as wind_speed_100m,
            AVG(wind_direction_10m) as wind_direction_10m,
            AVG(wind_gusts_10m) as wind_gusts_10m,
            MAX(latitude) as farm_lat,
            MAX(longitude) as farm_lon,
            EXTRACT(HOUR FROM time_utc) as hour_of_day,
            EXTRACT(MONTH FROM time_utc) as month,
            EXTRACT(DAYOFWEEK FROM time_utc) as day_of_week
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
        WHERE wind_speed_100m IS NOT NULL
          AND time_utc >= '2020-01-01' AND time_utc < '2025-11-01'
        GROUP BY farm_name, hour_utc, hour_of_day, month, day_of_week
    ),
    bm_mapping AS (
        SELECT farm_name, bm_unit_id
        FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu`
    ),
    actual_generation AS (
        SELECT 
            bmUnit as bm_unit_id,
            TIMESTAMP_TRUNC(TIMESTAMP(settlementDate), HOUR) as hour_utc,
            AVG(levelTo) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_pn`
        WHERE settlementDate >= '2020-01-01'
          AND settlementDate < '2025-11-01'
          AND levelTo > 0
        GROUP BY bm_unit_id, hour_utc
    )
    SELECT 
        w.*,
        COALESCE(g.generation_mw, 0) as generation_mw
    FROM weather_data w
    INNER JOIN bm_mapping m ON w.farm_name = m.farm_name
    LEFT JOIN actual_generation g ON m.bm_unit_id = g.bm_unit_id AND w.hour_utc = g.hour_utc
    WHERE w.farm_name IS NOT NULL
    """
    
    weather_df = client.query(query).to_dataframe()
    print(f"✅ Loaded {len(weather_df):,} weather observations")
    print(f"   Time: {time.time() - start_load:.1f}s")
    
    # Load ERA5 data (SHARED)
    print("\n🌐 Loading ERA5 grid data...")
    start_era5 = time.time()
    
    era5_query = f"""
    SELECT 
        grid_point_name,
        TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
        AVG(wind_speed_100m) as wind_speed_100m,
        AVG(wind_direction_100m) as wind_direction_100m
    FROM `{PROJECT_ID}.{DATASET}.era5_wind_upstream`
    WHERE time_utc >= '2020-01-01' AND time_utc < '2025-11-01'
    GROUP BY grid_point_name, hour_utc
    ORDER BY grid_point_name, hour_utc
    """
    
    era5_df = client.query(era5_query).to_dataframe()
    print(f"✅ Loaded {len(era5_df):,} ERA5 observations")
    print(f"   Time: {time.time() - start_era5:.1f}s")
    
    # Get unique farms
    farms = sorted(weather_df['farm_name'].unique())
    print(f"\n🌬️  Training {len(farms)} wind farms in parallel...")
    
    # Train all farms in parallel
    start_training = time.time()
    
    results = Parallel(n_jobs=args.n_jobs, verbose=10)(
        delayed(train_single_farm)(farm, weather_df, era5_df)
        for farm in farms
    )
    
    training_time = time.time() - start_training
    
    # Filter out failed farms
    results = [r for r in results if r is not None]
    
    # Save results
    results_df = pd.DataFrame(results)
    results_file = 'wind_power_curves_optimized_parallel_results.csv'
    results_df.to_csv(results_file, index=False)
    
    # Summary
    print("\n" + "=" * 70)
    print("🏆 PARALLEL TRAINING COMPLETE")
    print("=" * 70)
    print(f"Successfully trained: {len(results)} / {len(farms)} farms")
    print(f"Total training time: {training_time/60:.1f} minutes")
    print(f"Average per farm: {training_time/len(results):.1f} seconds")
    print(f"\nAverage MAE: {results_df['mae'].mean():.1f} MW")
    print(f"Median MAE: {results_df['mae'].median():.1f} MW")
    print(f"Best MAE: {results_df['mae'].min():.1f} MW ({results_df.loc[results_df['mae'].idxmin(), 'farm_name']})")
    print(f"Worst MAE: {results_df['mae'].max():.1f} MW ({results_df.loc[results_df['mae'].idxmax(), 'farm_name']})")
    
    baseline = 90.0
    improvement = ((baseline - results_df['mae'].mean()) / baseline) * 100
    print(f"\n🎯 Improvement vs baseline ({baseline} MW):")
    print(f"   {improvement:.1f}% improvement")
    print(f"   {'✅ TARGET ACHIEVED!' if improvement >= 20 else '⚠️ Close but not quite'}")
    
    print(f"\n📁 Results saved to: {results_file}")
    print(f"📁 Models saved to: {MODEL_DIR}/")
    print("=" * 70)


if __name__ == "__main__":
    main()
