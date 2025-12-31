#!/usr/bin/env python3
"""
Optimized Wind Power Curve Training - FAST VERSION

Uses the proven working query structure from ERA5 script.
Simplified to avoid slow JOINs and query complexity.
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import joblib
from math import radians, cos, sin, asin, sqrt
import os
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODEL_DIR = "models/wind_power_curves_optimized"

# Map each farm to its 3 best ERA5 grid points (closest + upwind)
FARM_TO_ERA5_GRID = {
    'Hornsea One': ['Central_England', 'North_Sea_West', 'Pennines'],
    'Hornsea Two': ['Central_England', 'North_Sea_West', 'Pennines'],
    'Dogger Bank': ['North_Sea_West', 'Dogger_West', 'Pennines'],
    'Moray East': ['North_Scotland', 'Atlantic_Hebrides', 'Moray_Firth_West'],
    'Moray West': ['North_Scotland', 'Atlantic_Hebrides', 'Moray_Firth_West'],
    'Beatrice': ['Moray_Firth_West', 'North_Scotland', 'Atlantic_Hebrides'],
    'Walney Extension': ['Atlantic_Irish_Sea', 'Irish_Sea_Central', 'Atlantic_Deep_West'],
    'Walney': ['Atlantic_Irish_Sea', 'Irish_Sea_Central', 'Atlantic_Deep_West'],
    'West of Duddon Sands': ['Atlantic_Irish_Sea', 'Irish_Sea_Central', 'Irish_Sea_North'],
    'Burbo Bank': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Burbo Bank Extension': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Ormonde': ['Irish_Sea_Central', 'Irish_Sea_North', 'Atlantic_Irish_Sea'],
    'London Array': ['Bristol_Channel', 'Channel_West', 'Celtic_Sea'],
    'Thanet': ['Bristol_Channel', 'Channel_West', 'Celtic_Sea'],
    'Rampion': ['Channel_West', 'Bristol_Channel', 'Celtic_Sea'],
    'Dudgeon': ['Celtic_Sea', 'Central_England', 'Pennines'],
    'Sheringham Shoal': ['Central_England', 'Celtic_Sea', 'Pennines'],
    'Race Bank': ['Central_England', 'Celtic_Sea', 'Pennines'],
    'Triton Knoll': ['Central_England', 'Celtic_Sea', 'Pennines'],
    'Lincs': ['Central_England', 'Celtic_Sea', 'Pennines'],
    'Westermost Rough': ['Central_England', 'North_Sea_West', 'Pennines'],
    'Humber Gateway': ['Central_England', 'North_Sea_West', 'Pennines'],
    'East Anglia One': ['Celtic_Sea', 'Central_England', 'Bristol_Channel'],
    'Greater Gabbard': ['Bristol_Channel', 'Celtic_Sea', 'Central_England'],
    'Gunfleet Sands 1 & 2': ['Bristol_Channel', 'Celtic_Sea', 'Central_England'],
    'Seagreen Phase 1': ['West_Scotland', 'Moray_Firth_West', 'North_Scotland'],
    'Neart Na Gaoithe': ['West_Scotland', 'Moray_Firth_West', 'Atlantic_Hebrides'],
    'Kincardine': ['West_Scotland', 'Moray_Firth_West', 'Atlantic_Hebrides'],
    'Hywind Scotland': ['Moray_Firth_West', 'Shetland_West', 'North_Scotland'],
    'Barrow': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
}

# ERA5 grid coordinates (for distance calculations)
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

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def calculate_dynamic_lag(distance_km, wind_speed_ms):
    """Calculate optimal lag based on wind transit time"""
    if wind_speed_ms < 5:
        wind_speed_ms = 10  # Use conservative default for low wind
    transit_hours = distance_km / (wind_speed_ms * 3.6)  # Convert m/s to km/h
    lag_hours = round(transit_hours * 2) / 2  # Round to nearest 0.5h
    lag_hours = max(0.5, min(8.0, lag_hours))  # Constrain to 0.5-8h
    return lag_hours

def main():
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("=" * 80)
    print("Optimized Wind Power Curve Training - FAST VERSION")
    print("=" * 80)
    print("Improvements implemented:")
    print("  1. ✅ 18 ERA5 grid points (10 original + 8 strategic)")
    print("  2. ✅ Dynamic lag calculation (wind-speed dependent)")
    print("  3. ✅ Ensemble grid points (weighted average of 3 grids)")
    print("  4. ✅ Interaction features (4 new features)")
    print("  5. ✅ XGBoost model (upgraded from GradientBoosting)")
    print()
    print("Expected improvement: >20% from baseline (target <72 MW MAE)")
    print("=" * 80)
    print()
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Use the proven working query structure from ERA5 script
    print("📊 Loading training dataset (3-5 minutes)...")
    
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
        w.farm_name,
        w.hour_utc as time_utc,
        w.hour_of_day,
        w.month,
        w.day_of_week,
        w.wind_speed_100m,
        w.wind_direction_10m,
        w.wind_gusts_10m,
        w.farm_lat,
        w.farm_lon,
        SUM(COALESCE(g.generation_mw, 0)) as actual_generation_mw
    FROM weather_data w
    INNER JOIN bm_mapping m ON w.farm_name = m.farm_name
    LEFT JOIN actual_generation g 
        ON m.bm_unit_id = g.bm_unit_id AND w.hour_utc = g.hour_utc
    GROUP BY w.farm_name, w.hour_utc, w.hour_of_day, w.month, w.day_of_week,
             w.wind_speed_100m, w.wind_direction_10m, w.wind_gusts_10m,
             w.farm_lat, w.farm_lon
    ORDER BY w.farm_name, w.hour_utc
    """
    
    df_base = client.query(query).to_dataframe()
    
    print(f"✅ Loaded {len(df_base):,} base training samples")
    print(f"   Farms: {df_base['farm_name'].nunique()}")
    print(f"   Date range: {df_base['time_utc'].min()} to {df_base['time_utc'].max()}")
    print()
    
    # Load ERA5 data
    print("🌐 Loading ERA5 upstream wind data...")
    era5_query = f"""
    SELECT 
      time_utc,
      grid_point_name as grid_point,
      latitude as grid_lat,
      longitude as grid_lon,
      wind_speed_100m as era5_wind,
      wind_direction_100m as era5_direction
    FROM `{PROJECT_ID}.{DATASET}.era5_wind_upstream`
    WHERE time_utc >= '2020-01-01'
    AND time_utc < '2025-11-01'
    """
    
    df_era5 = client.query(era5_query).to_dataframe()
    print(f"✅ Loaded {len(df_era5):,} ERA5 observations from {df_era5['grid_point'].nunique()} grid points")
    print()
    
    # Pivot ERA5 data for faster lookups
    df_era5['time_utc'] = pd.to_datetime(df_era5['time_utc'])
    era5_pivot = df_era5.pivot_table(
        index='time_utc',
        columns='grid_point',
        values=['era5_wind', 'era5_direction'],
        aggfunc='first'
    )
    
    # Train models for each farm
    print("🏗️  Training farm-specific models with optimized features...")
    print()
    
    results = []
    
    for farm_name in sorted(FARM_TO_ERA5_GRID.keys()):
        farm_data = df_base[df_base['farm_name'] == farm_name].copy()
        
        if len(farm_data) < 100:
            continue
        
        farm_lat = farm_data['farm_lat'].iloc[0]
        farm_lon = farm_data['farm_lon'].iloc[0]
        
        # Get ERA5 grids for this farm
        era5_grids = FARM_TO_ERA5_GRID[farm_name]
        
        # Calculate distances to each grid
        grid_distances = {}
        for grid_name in era5_grids:
            if grid_name in ERA5_GRID_COORDS:
                grid_lat, grid_lon = ERA5_GRID_COORDS[grid_name]
                dist = haversine(farm_lat, farm_lon, grid_lat, grid_lon)
                grid_distances[grid_name] = dist
        
        # Add dynamic lag ERA5 features
        primary_grid = era5_grids[0]
        primary_distance = grid_distances.get(primary_grid, 100)
        
        # Dynamic lag based on local wind speed
        farm_data['optimal_lag_hours'] = farm_data['wind_speed_100m'].apply(
            lambda ws: calculate_dynamic_lag(primary_distance, ws)
        )
        
        # Get ERA5 wind with dynamic lag
        era5_winds_dynamic = []
        for idx, row in farm_data.iterrows():
            lag_hours = row['optimal_lag_hours']
            lag_time = row['time_utc'] - timedelta(hours=lag_hours)
            
            if lag_time in era5_pivot.index and primary_grid in era5_pivot['era5_wind'].columns:
                era5_winds_dynamic.append(era5_pivot['era5_wind'][primary_grid].loc[lag_time])
            else:
                era5_winds_dynamic.append(np.nan)
        
        farm_data['era5_wind_dynamic'] = era5_winds_dynamic
        
        # Ensemble grid points (weighted average of top 3)
        ensemble_weights = []
        ensemble_winds = []
        for grid_name in era5_grids[:3]:
            if grid_name in grid_distances and grid_name in era5_pivot['era5_wind'].columns:
                dist = grid_distances[grid_name]
                weight = 1.0 / (dist + 10)  # Inverse distance weighting
                ensemble_weights.append(weight)
                
                # Get ERA5 wind at 2h lag (conservative fixed lag for ensemble)
                grid_wind = farm_data['time_utc'].apply(
                    lambda t: era5_pivot['era5_wind'][grid_name].loc[t - timedelta(hours=2)]
                    if (t - timedelta(hours=2)) in era5_pivot.index else np.nan
                )
                ensemble_winds.append(grid_wind * weight)
        
        if len(ensemble_weights) > 0:
            farm_data['era5_ensemble'] = sum(ensemble_winds) / sum(ensemble_weights)
        else:
            farm_data['era5_ensemble'] = 0
        
        # Interaction features
        farm_data['local_x_era5'] = farm_data['wind_speed_100m'] * farm_data['era5_wind_dynamic']
        farm_data['era5_change_x_dist'] = (farm_data['era5_wind_dynamic'] - farm_data['era5_ensemble']) * primary_distance
        
        # Direction alignment (how well local and ERA5 wind directions align)
        era5_directions = []
        for idx, row in farm_data.iterrows():
            lag_time = row['time_utc'] - timedelta(hours=2)
            if lag_time in era5_pivot.index and primary_grid in era5_pivot['era5_direction'].columns:
                era5_directions.append(era5_pivot['era5_direction'][primary_grid].loc[lag_time])
            else:
                era5_directions.append(np.nan)
        
        farm_data['era5_direction'] = era5_directions
        direction_diff = np.abs(farm_data['wind_direction_10m'] - farm_data['era5_direction'])
        farm_data['direction_alignment'] = np.cos(np.radians(direction_diff))
        
        # Diurnal interaction
        farm_data['hour_x_era5'] = farm_data['hour_of_day'] * farm_data['era5_wind_dynamic']
        
        # Drop rows with missing ERA5 data
        farm_data = farm_data.dropna(subset=['era5_wind_dynamic', 'actual_generation_mw'])
        
        if len(farm_data) < 100:
            continue
        
        # Define features (15 total: 6 baseline + 9 optimized)
        features = [
            # Baseline (6)
            'wind_speed_100m', 'wind_direction_10m', 'wind_gusts_10m',
            'hour_of_day', 'month', 'day_of_week',
            # Optimized ERA5 features (9)
            'optimal_lag_hours', 'era5_wind_dynamic', 'era5_ensemble',
            'local_x_era5', 'era5_change_x_dist', 'direction_alignment',
            'hour_x_era5', 'era5_direction'
        ]
        
        X = farm_data[features + ['farm_name']]
        y = farm_data['actual_generation_mw']
        
        # Split train/test (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        X_train = X_train[features]
        X_test = X_test[features]
        
        # XGBoost model
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
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred = model.predict(X_test)
        
        # Metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # Save model
        model_path = os.path.join(MODEL_DIR, f'{farm_name.replace(" ", "_")}.pkl')
        joblib.dump({
            'model': model,
            'features': features,
            'farm_name': farm_name,
            'era5_grids': era5_grids,
            'grid_distances': grid_distances,
            'trained_date': datetime.now().isoformat()
        }, model_path)
        
        results.append({
            'farm_name': farm_name,
            'samples': len(farm_data),
            'avg_generation_mw': y.mean(),
            'max_generation_mw': y.max(),
            'mae': mae,
            'rmse': rmse,
            'r2': r2
        })
        
        print(f"  ✅ {farm_name:<40} {len(farm_data):>6} {y.mean():>7.0f} {y.max():>7.0f} {mae:>8.0f} {rmse:>8.0f}")
    
    # Save results
    df_results = pd.DataFrame(results)
    df_results.to_csv('wind_power_curves_optimized_results.csv', index=False)
    
    print()
    print("=" * 80)
    print("✅ Training complete with ALL optimizations!")
    print("=" * 80)
    print(f"\nModels saved to: {MODEL_DIR}/")
    print(f"Total models trained: {len(results)}")
    print()
    print("📊 Performance Summary:")
    print(f"   Average MAE: {df_results['mae'].mean():.1f} MW")
    print(f"   Median MAE: {df_results['mae'].median():.1f} MW")
    print(f"   Best MAE: {df_results['mae'].min():.1f} MW")
    print(f"   Worst MAE: {df_results['mae'].max():.1f} MW")
    print()
    print("=" * 80)
    print("📈 Comparison with Previous Models:")
    print("=" * 80)
    print("   Baseline B1610: ~90 MW avg MAE")
    print("   Spatial (offshore): ~86 MW avg MAE (+5.5%)")
    print("   Spatial + ERA5: 81.1 MW avg MAE (+9.9%)")
    print(f"   OPTIMIZED: {df_results['mae'].mean():.1f} MW avg MAE")
    baseline_mae = 90.0
    improvement = ((baseline_mae - df_results['mae'].mean()) / baseline_mae) * 100
    print(f"   Improvement from baseline: {improvement:.1f}%")
    print()
    if improvement >= 20:
        print("   ✅ TARGET ACHIEVED: >20% improvement!")
    else:
        print(f"   ⚠️  BELOW TARGET: {improvement:.1f}% (target: >20%)")
    print("=" * 80)

if __name__ == "__main__":
    main()
