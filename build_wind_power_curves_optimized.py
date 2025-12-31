#!/usr/bin/env python3
"""
Optimized Wind Power Curve Training with ALL Improvements

Implements:
1. Optimal ERA5 grid point selection (18 total grids)
2. Dynamic lag calculation based on wind speed
3. Ensemble grid points (weighted average of 2-3 grids)
4. Interaction features (local×era5, change×distance, etc.)
5. XGBoost model architecture

Expected improvement: >20% from baseline (target <72 MW MAE)
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
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

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
    """
    Calculate optimal lag based on wind transit time
    
    Args:
        distance_km: Distance from upstream grid point to farm
        wind_speed_ms: Current wind speed in m/s
    
    Returns:
        lag_hours: Optimal lag in hours (rounded to nearest 0.5h)
    """
    if wind_speed_ms < 5:
        wind_speed_ms = 10  # Use default for low wind
    
    # Transit time = distance / (wind_speed * 3.6 to convert m/s to km/h)
    transit_hours = distance_km / (wind_speed_ms * 3.6)
    
    # Round to nearest 0.5 hours
    lag_hours = round(transit_hours * 2) / 2
    
    # Constrain to reasonable range (0.5h to 8h)
    lag_hours = max(0.5, min(8.0, lag_hours))
    
    return lag_hours

# Farm to ERA5 grid mapping (all 18 grids including strategic additions)
FARM_TO_ERA5_GRID = {
    'Hornsea One': ['Central_England', 'North_Sea_West', 'Pennines'],
    'Hornsea Two': ['Central_England', 'North_Sea_West', 'Pennines'],
    'Dogger Bank': ['Dogger_West', 'North_Sea_West', 'Central_England'],
    'Walney Extension': ['Atlantic_Irish_Sea', 'Irish_Sea_Central', 'Atlantic_Deep_West'],
    'Walney': ['Atlantic_Irish_Sea', 'Irish_Sea_Central', 'Atlantic_Deep_West'],
    'West of Duddon Sands': ['Atlantic_Irish_Sea', 'Irish_Sea_Central', 'Irish_Sea_North'],
    'Barrow': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Ormonde': ['Irish_Sea_Central', 'Irish_Sea_North', 'Atlantic_Irish_Sea'],
    'Burbo Bank': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Burbo Bank Extension': ['Irish_Sea_Central', 'Atlantic_Irish_Sea', 'Irish_Sea_North'],
    'Moray East': ['North_Scotland', 'Atlantic_Hebrides', 'Moray_Firth_West'],
    'Moray West': ['North_Scotland', 'Atlantic_Hebrides_Extended', 'Atlantic_Hebrides'],
    'Beatrice': ['Moray_Firth_West', 'North_Scotland', 'Atlantic_Hebrides'],
    'Seagreen Phase 1': ['West_Scotland', 'Moray_Firth_West', 'North_Scotland'],
    'Neart Na Gaoithe': ['West_Scotland', 'Moray_Firth_West', 'North_Scotland'],
    'Kincardine': ['West_Scotland', 'Moray_Firth_West', 'Atlantic_Hebrides'],
    'Hywind Scotland': ['Moray_Firth_West', 'West_Scotland', 'North_Scotland'],
    'Triton Knoll': ['Central_England', 'North_Sea_West', 'Pennines'],
    'Race Bank': ['Central_England', 'North_Sea_West', 'Celtic_Sea'],
    'Sheringham Shoal': ['Central_England', 'Celtic_Sea', 'North_Sea_West'],
    'Dudgeon': ['Celtic_Sea', 'Central_England', 'Bristol_Channel'],
    'Scroby Sands': ['Celtic_Sea', 'Central_England', 'Bristol_Channel'],
    'Greater Gabbard': ['Bristol_Channel', 'Celtic_Sea', 'Channel_West'],
    'Galloper': ['Bristol_Channel', 'Celtic_Sea', 'Channel_West'],
    'Gunfleet Sands 1 & 2': ['Bristol_Channel', 'Celtic_Sea', 'Channel_West'],
    'London Array': ['Bristol_Channel', 'Channel_West', 'Celtic_Sea'],
    'Thanet': ['Bristol_Channel', 'Channel_West', 'Celtic_Sea'],
    'East Anglia One': ['Celtic_Sea', 'Bristol_Channel', 'Central_England'],
    'Rampion': ['Channel_West', 'Bristol_Channel', 'Celtic_Sea_Deep'],
    'Lincs': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Humber Gateway': ['Central_England', 'Pennines', 'North_Sea_West'],
    'Westermost Rough': ['Central_England', 'North_Sea_West', 'Pennines'],
}

# ERA5 grid coordinates (10 original + 8 strategic = 18 total)
ERA5_GRID_COORDS = {
    # Original 10
    'Atlantic_Irish_Sea': (54.0, -8.0),
    'Irish_Sea_Central': (53.5, -6.0),
    'Atlantic_Hebrides': (57.0, -6.0),
    'West_Scotland': (56.5, -4.5),
    'Central_England': (53.5, -1.0),
    'Pennines': (54.5, -2.0),
    'Celtic_Sea': (52.5, -5.0),
    'Bristol_Channel': (51.5, -2.0),
    'North_Scotland': (59.0, -4.0),
    'Moray_Firth_West': (58.0, -2.0),
    # Strategic additions
    'Atlantic_Deep_West': (54.5, -10.0),
    'Atlantic_Hebrides_Extended': (57.5, -7.5),
    'North_Sea_West': (54.0, -0.5),
    'Celtic_Sea_Deep': (51.5, -6.5),
    'Irish_Sea_North': (55.0, -5.0),
    'Channel_West': (50.5, -1.5),
    'Shetland_West': (60.5, -3.0),
    'Dogger_West': (55.0, 0.5),
}

# Farm coordinates (for distance calculation)
FARM_COORDS = {
    'Hornsea One': (53.9, 1.8),
    'Hornsea Two': (53.9, 1.9),
    'Dogger Bank': (55.0, 2.0),
    'Walney Extension': (54.0, -3.5),
    'Moray East': (58.1, -2.3),
    'Moray West': (58.5, -3.3),
    'Beatrice': (58.2, -2.9),
    'Triton Knoll': (53.4, 0.8),
    'Seagreen Phase 1': (56.5, -1.8),
    'Rampion': (50.65, -0.35),
}

print("=" * 80)
print("Optimized Wind Power Curve Training - ALL IMPROVEMENTS")
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

# Load training data
print("📊 Loading training dataset...")
client = bigquery.Client(project=PROJECT_ID, location="US")

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
        TIMESTAMP_TRUNC(TIMESTAMP(CAST(settlementDate AS DATE)), HOUR) as hour_utc,
        AVG(levelTo) as generation_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_pn`
    WHERE CAST(settlementDate AS DATE) >= '2020-01-01'
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

print("Running BigQuery (may take 2-3 minutes)...")
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
era5_pivot = df_era5.pivot_table(
    index='time_utc',
    columns='grid_point',
    values=['era5_wind', 'era5_direction'],
    aggfunc='first'
)

# Train models for each farm
print("🏗️  Training farm-specific models with optimized features...")
print()

os.makedirs('models/wind_power_curves_optimized', exist_ok=True)

results = []

for farm_name in sorted(df_base['farm_name'].unique()):
    print(f"⚙️  {farm_name}...")
    
    farm_data = df_base[df_base['farm_name'] == farm_name].copy()
    
    if len(farm_data) < 500:
        print(f"   ⚠️  Insufficient data ({len(farm_data)} samples), skipping")
        continue
    
    # Get ERA5 grid points for this farm
    if farm_name not in FARM_TO_ERA5_GRID:
        print(f"   ⚠️  No ERA5 mapping, skipping")
        continue
    
    era5_grids = FARM_TO_ERA5_GRID[farm_name]
    
    # Calculate distances to each grid
    farm_lat = farm_data['farm_lat'].iloc[0]
    farm_lon = farm_data['farm_lon'].iloc[0]
    
    grid_distances = {}
    for grid_name in era5_grids:
        if grid_name in ERA5_GRID_COORDS:
            grid_lat, grid_lon = ERA5_GRID_COORDS[grid_name]
            dist = haversine(farm_lat, farm_lon, grid_lat, grid_lon)
            grid_distances[grid_name] = dist
    
    if len(grid_distances) == 0:
        print(f"   ⚠️  No valid grids, skipping")
        continue
    
    # FEATURE 1: Dynamic lag calculation
    # For each observation, calculate optimal lag based on current wind speed
    primary_grid = era5_grids[0]
    primary_distance = grid_distances.get(primary_grid, 150)
    
    # Extract ERA5 data with dynamic lags
    era5_features = []
    
    for idx, row in farm_data.iterrows():
        time_utc = row['time_utc']
        wind_speed = row['wind_speed_100m']
        
        # Calculate dynamic lag
        optimal_lag_hours = calculate_dynamic_lag(primary_distance, wind_speed)
        
        # Get ERA5 wind at optimal lag
        lag_time = pd.Timestamp(time_utc) - pd.Timedelta(hours=optimal_lag_hours)
        
        try:
            if primary_grid in era5_pivot['era5_wind'].columns:
                era5_wind = era5_pivot['era5_wind'][primary_grid].loc[lag_time]
                era5_direction = era5_pivot['era5_direction'][primary_grid].loc[lag_time]
            else:
                era5_wind = 0
                era5_direction = 0
        except KeyError:
            era5_wind = 0
            era5_direction = 0
        
        era5_features.append({
            'optimal_lag_hours': optimal_lag_hours,
            'era5_wind_dynamic': era5_wind,
            'era5_direction': era5_direction
        })
    
    df_era5_features = pd.DataFrame(era5_features)
    farm_data = pd.concat([farm_data.reset_index(drop=True), df_era5_features], axis=1)
    
    # FEATURE 2: Ensemble grid points (weighted average)
    ensemble_weights = []
    ensemble_winds = []
    
    for grid_name in era5_grids[:3]:  # Top 3 grids
        if grid_name in grid_distances and grid_name in era5_pivot['era5_wind'].columns:
            dist = grid_distances[grid_name]
            weight = 1.0 / (dist + 10)  # Inverse distance weighting
            
            ensemble_weights.append(weight)
            
            # Get grid wind (2h lag as baseline)
            grid_wind = farm_data['time_utc'].map(
                era5_pivot['era5_wind'][grid_name].shift(2)
            ).fillna(0)
            
            ensemble_winds.append(grid_wind * weight)
    
    if len(ensemble_winds) > 0:
        total_weight = sum(ensemble_weights)
        farm_data['era5_ensemble'] = sum(ensemble_winds) / total_weight
    else:
        farm_data['era5_ensemble'] = 0
    
    # FEATURE 3: Interaction terms
    farm_data['local_x_era5'] = farm_data['wind_speed_100m'] * farm_data['era5_wind_dynamic']
    farm_data['era5_change_x_dist'] = (
        farm_data['era5_wind_dynamic'] - farm_data['era5_ensemble']
    ) * primary_distance
    
    # Direction alignment (cosine of angle difference)
    direction_diff = np.abs(farm_data['wind_direction_10m'] - farm_data['era5_direction'])
    direction_diff = np.minimum(direction_diff, 360 - direction_diff)
    farm_data['direction_alignment'] = np.cos(np.radians(direction_diff))
    
    # Hour × ERA5 interaction
    farm_data['hour_of_day'] = pd.to_datetime(farm_data['time_utc']).dt.hour
    farm_data['hour_x_era5'] = farm_data['hour_of_day'] * farm_data['era5_wind_dynamic']
    
    # Additional time features
    farm_data['month'] = pd.to_datetime(farm_data['time_utc']).dt.month
    farm_data['day_of_week'] = pd.to_datetime(farm_data['time_utc']).dt.dayofweek
    
    # Define features (6 baseline + 9 optimized = 15 total)
    features = [
        # Baseline (6)
        'wind_speed_100m',
        'wind_direction_10m',
        'wind_gusts_10m',
        'hour_of_day',
        'month',
        'day_of_week',
        # Optimized (9)
        'optimal_lag_hours',      # Dynamic lag
        'era5_wind_dynamic',      # Wind at dynamic lag
        'era5_ensemble',          # Ensemble grid points
        'local_x_era5',           # Interaction: local × ERA5
        'era5_change_x_dist',     # Interaction: change × distance
        'direction_alignment',    # Interaction: direction
        'hour_x_era5',            # Interaction: hour × ERA5
        'era5_direction',         # ERA5 direction
    ]
    
    # Remove rows with missing features
    farm_data = farm_data.dropna(subset=features + ['actual_generation_mw'])
    
    if len(farm_data) < 500:
        print(f"   ⚠️  Insufficient data after feature engineering ({len(farm_data)} samples)")
        continue
    
    X = farm_data[features]
    y = farm_data['actual_generation_mw']
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # FEATURE 5: XGBoost model
    model = xgb.XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=8,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        gamma=0.1,
        reg_alpha=0.1,   # L1 regularization
        reg_lambda=1.0,  # L2 regularization
        tree_method='hist',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # Save model
    model_path = f'models/wind_power_curves_optimized/{farm_name.replace(" ", "_")}_optimized_model.pkl'
    joblib.dump({
        'model': model,
        'features': features,
        'era5_grids': era5_grids,
        'grid_distances': grid_distances,
        'farm_coords': (farm_lat, farm_lon),
        'trained_date': datetime.now().isoformat()
    }, model_path)
    
    results.append({
        'farm_name': farm_name,
        'samples': len(farm_data),
        'avg_generation_mw': y.mean(),
        'max_generation_mw': y.max(),
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'num_era5_grids': len(era5_grids),
        'primary_grid': primary_grid,
        'primary_distance_km': primary_distance
    })
    
    print(f"   ✅ Samples: {len(farm_data):>6,} | MAE: {mae:>5.0f} MW | RMSE: {rmse:>5.0f} MW | R²: {r2:.3f}")

# Summary
print()
print("=" * 80)
print("✅ TRAINING COMPLETE - OPTIMIZED MODELS")
print("=" * 80)

df_results = pd.DataFrame(results)

print(f"\nModels trained: {len(df_results)}")
print(f"\n📊 Performance Summary:")
print(f"   Average MAE: {df_results['mae'].mean():.1f} MW")
print(f"   Median MAE: {df_results['mae'].median():.1f} MW")
print(f"   Best MAE: {df_results['mae'].min():.1f} MW")
print(f"   Worst MAE: {df_results['mae'].max():.1f} MW")
print(f"   Average R²: {df_results['r2'].mean():.3f}")

# Compare with previous models
print()
print("=" * 80)
print("📈 Performance Comparison")
print("=" * 80)
print("   Baseline B1610: ~90 MW avg MAE")
print("   Spatial (offshore): ~86 MW avg MAE (+4.7%)")
print("   ERA5 basic: 81.1 MW avg MAE (+9.9%)")
print(f"   OPTIMIZED: {df_results['mae'].mean():.1f} MW avg MAE")

baseline_mae = 90.0
improvement = ((baseline_mae - df_results['mae'].mean()) / baseline_mae) * 100

print(f"\n   🎯 Total improvement from baseline: {improvement:.1f}%")

if improvement >= 20:
    print("   ✅ TARGET ACHIEVED! (>20% improvement)")
else:
    print(f"   ⚠️  Below target: {20 - improvement:.1f}% gap remaining")

# Save results
df_results.to_csv('wind_power_curves_optimized_results.csv', index=False)
print(f"\n✅ Results saved to: wind_power_curves_optimized_results.csv")

print()
print("=" * 80)
print("Models saved to: models/wind_power_curves_optimized/")
print("=" * 80)
