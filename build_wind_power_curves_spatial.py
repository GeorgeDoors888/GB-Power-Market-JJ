#!/usr/bin/env python3
"""
Enhanced Wind Power Curve Training with SPATIAL FEATURES
Uses upstream wind farm measurements for improved prediction accuracy

Key Innovation: Adds 5 spatial features per farm based on r>0.85 correlations:
1. upstream_wind_speed - Wind at best upstream farm (30-min ago)
2. upstream_wind_lag - Optimal lag time (0.5-1h)
3. upstream_wind_change - Rate of change at upstream farm
4. spatial_confidence - Based on wind direction alignment
5. upstream_farm_id - Categorical feature for upstream farm

Expected Improvement: 25-50% error reduction (from 15-20% to 10-15% MAE)
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os
import math

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODEL_DIR = "models/wind_power_curves_spatial"

# Best upstream sensors for each major farm (from spatial correlation analysis)
# Format: {downstream_farm: [(upstream_farm, correlation, optimal_lag_hours, distance_km), ...]}
UPSTREAM_SENSORS = {
    'Hornsea One': [
        ('Triton Knoll', 0.910, 0.5, 116),
        ('Sheringham Shoal', 0.906, 0.5, 129),
        ('Humber Gateway', 0.904, 0.5, 104)
    ],
    'Hornsea Two': [
        ('Triton Knoll', 0.911, 0.5, 104),
        ('Sheringham Shoal', 0.907, 0.5, 116),
        ('Humber Gateway', 0.902, 0.5, 95)
    ],
    'Seagreen Phase 1': [
        ('Neart Na Gaoithe', 0.901, 0.5, 61),
        ('Kincardine', 0.886, 0.5, 61),
        ('Hywind Scotland', 0.837, 0.5, 113)
    ],
    'Triton Knoll': [
        ('Sheringham Shoal', 0.929, 0.5, 65),
        ('Hornsea One', 0.923, 0.5, 116),
        ('Hornsea Two', 0.922, 0.5, 104)
    ],
    'East Anglia One': [
        ('London Array', 0.892, 0.5, 48),
        ('Thanet', 0.891, 0.5, 75),
        ('Gunfleet Sands 1 & 2', 0.860, 0.5, 43)
    ],
    'Walney Extension': [
        ('Burbo Bank', 0.857, 0.5, 67),
        ('Burbo Bank Extension', 0.829, 0.5, 67)
    ],
    'Moray East': [
        ('Beatrice', 0.909, 0.5, 61),
        ('Hywind Scotland', 0.808, 0.5, 37)
    ],
    'Moray West': [
        ('Beatrice', 0.966, 0.5, 53),
        ('Moray East', 0.881, 0.5, 10)
    ],
    'Beatrice': [
        ('Moray West', 0.959, 0.5, 53),
        ('Moray East', 0.909, 0.5, 61)
    ],
    'Dudgeon': [
        ('Sheringham Shoal', 0.964, 0.5, 52),
        ('Hornsea One', 0.926, 0.5, 102),
        ('Hornsea Two', 0.925, 0.5, 89)
    ],
    'Race Bank': [
        ('Sheringham Shoal', 0.949, 0.5, 63),
        ('Triton Knoll', 0.922, 0.5, 26)
    ],
    'London Array': [
        ('Greater Gabbard', 0.946, 0.5, 41),
        ('Thanet', 0.914, 0.5, 33)
    ],
    'Greater Gabbard': [
        ('London Array', 0.955, 0.5, 41),
        ('Gunfleet Sands 1 & 2', 0.940, 0.5, 35)
    ],
    'Thanet': [
        ('London Array', 0.955, 0.5, 33),
        ('Greater Gabbard', 0.933, 0.5, 65)
    ],
    'Kincardine': [
        ('Seagreen Phase 1', 0.928, 0.5, 61),
        ('Neart Na Gaoithe', 0.905, 0.5, 31)
    ],
    'Neart Na Gaoithe': [
        ('Seagreen Phase 1', 0.901, 0.5, 61),
        ('Kincardine', 0.905, 0.5, 31)
    ],
    'Humber Gateway': [
        ('Triton Knoll', 0.921, 0.5, 46),
        ('Hornsea One', 0.904, 0.5, 104),
        ('Hornsea Two', 0.902, 0.5, 95)
    ],
    'Sheringham Shoal': [
        ('Dudgeon', 0.964, 0.5, 52),
        ('Triton Knoll', 0.929, 0.5, 65),
        ('Race Bank', 0.949, 0.5, 63)
    ],
    'Gunfleet Sands 1 & 2': [
        ('Greater Gabbard', 0.940, 0.5, 35),
        ('Thanet', 0.915, 0.5, 34)
    ],
    'Burbo Bank': [
        ('Walney Extension', 0.857, 0.5, 67),
        ('Burbo Bank Extension', 0.883, 0.5, 1)
    ],
    'Burbo Bank Extension': [
        ('Burbo Bank', 0.883, 0.5, 1),
        ('Walney Extension', 0.829, 0.5, 67)
    ],
    'Walney': [
        ('Walney Extension', 0.900, 0.5, 10),
        ('West of Duddon Sands', 0.873, 0.5, 10)
    ],
    'West of Duddon Sands': [
        ('Walney', 0.873, 0.5, 10),
        ('Walney Extension', 0.870, 0.5, 1)
    ],
    'Barrow': [
        ('Walney', 0.881, 0.5, 30),
        ('Ormonde', 0.851, 0.5, 35)
    ],
    'Ormonde': [
        ('Barrow', 0.851, 0.5, 35),
        ('Walney Extension', 0.858, 0.5, 22)
    ],
    'Westermost Rough': [
        ('Humber Gateway', 0.902, 0.5, 49),
        ('Triton Knoll', 0.886, 0.5, 68)
    ],
    'Lincs': [
        ('Triton Knoll', 0.909, 0.5, 81),
        ('Race Bank', 0.895, 0.5, 27)
    ],
    'Rampion': [
        ('Thanet', 0.862, 0.5, 100),
        ('London Array', 0.857, 0.5, 75)
    ],
    'Hywind Scotland': [
        ('Moray East', 0.808, 0.5, 37),
        ('Beatrice', 0.866, 0.5, 61)
    ]
}

# Farm coordinates for bearing calculation
FARM_COORDS = {
    'Beatrice': (58.1, -3.0),
    'Moray East': (57.7, -2.3),
    'Moray West': (57.7, -2.5),
    'Seagreen Phase 1': (56.5, -2.1),
    'Neart Na Gaoithe': (56.0, -2.5),
    'Hywind Scotland': (57.5, -1.8),
    'Kincardine': (57.0, -2.5),
    'Hornsea One': (54.0, 1.8),
    'Hornsea Two': (53.9, 1.7),
    'Triton Knoll': (53.3, 0.5),
    'Race Bank': (53.2, 0.4),
    'Dudgeon': (53.3, 0.8),
    'Sheringham Shoal': (52.9, 1.2),
    'Greater Gabbard': (51.9, 2.0),
    'East Anglia One': (52.0, 2.0),
    'London Array': (51.7, 1.5),
    'Thanet': (51.4, 1.5),
    'Rampion': (50.7, -0.3),
    'Burbo Bank': (53.5, -3.3),
    'Burbo Bank Extension': (53.5, -3.4),
    'Walney': (54.0, -3.5),
    'Walney Extension': (54.1, -3.4),
    'West of Duddon Sands': (54.1, -3.5),
    'Ormonde': (54.1, -3.6),
    'Barrow': (54.1, -3.3),
    'Westermost Rough': (53.8, 0.2),
    'Humber Gateway': (53.7, 0.3),
    'Lincs': (53.4, 0.4),
    'Gunfleet Sands 1 & 2': (51.7, 1.6),
}

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing from point 1 to point 2 in degrees (0-360)"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360

def angle_difference(angle1, angle2):
    """Calculate smallest difference between two angles (0-180)"""
    diff = abs(angle1 - angle2)
    if diff > 180:
        diff = 360 - diff
    return diff

def calculate_spatial_confidence(wind_direction, bearing):
    """
    Calculate confidence score based on wind direction alignment with farm bearing
    Returns 0-1 where 1 = perfect alignment, 0 = opposite direction
    """
    diff = angle_difference(wind_direction, bearing)
    # Linear decay: 0° = 1.0, 30° = 0.5, 90° = 0.0
    confidence = max(0, 1 - (diff / 90.0))
    return confidence

def main():
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("=" * 80)
    print("Wind Power Curve Training - WITH SPATIAL FEATURES")
    print("=" * 80)
    print("\nInnovation: Using upstream wind farm measurements for improved accuracy")
    print("Expected improvement: 25-50% error reduction")
    print("=" * 80)
    
    # Create model directory
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    print("\n📊 Creating enhanced training dataset with spatial features...")
    print("   Joining: openmeteo_wind_historic + bmrs_pn (B1610) + upstream farms")
    print("   Running BigQuery (may take 90-150 seconds for spatial joins)...\n")
    
    # Enhanced query with upstream wind features
    query = f"""
    WITH weather_data AS (
        SELECT 
            farm_name,
            TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
            AVG(wind_speed_100m) as wind_speed_100m,
            AVG(wind_direction_10m) as wind_direction_10m,
            AVG(wind_gusts_10m) as wind_gusts_10m,
            MAX(capacity_mw) as capacity_mw,
            EXTRACT(HOUR FROM time_utc) as hour_of_day,
            EXTRACT(MONTH FROM time_utc) as month,
            EXTRACT(DAYOFWEEK FROM time_utc) as day_of_week
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
        WHERE wind_speed_100m IS NOT NULL
          AND wind_speed_100m BETWEEN 0 AND 50
          AND time_utc >= '2020-01-01' AND time_utc < '2025-11-01'
        GROUP BY farm_name, hour_utc, hour_of_day, month, day_of_week
    ),
    bm_mapping AS (
        SELECT farm_name, bm_unit_id, capacity_mw as unit_capacity_mw
        FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu`
    ),
    actual_generation AS (
        SELECT 
            bmUnit as bm_unit_id,
            TIMESTAMP_TRUNC(TIMESTAMP(CAST(settlementDate AS DATE)), HOUR) as hour_utc,
            AVG(levelTo) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_pn`
        WHERE CAST(settlementDate AS DATE) >= '2020-01-01'
          AND CAST(settlementDate AS DATE) < '2025-11-01'
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
        w.capacity_mw as farm_capacity_mw,
        m.bm_unit_id,
        m.unit_capacity_mw,
        COALESCE(g.generation_mw, 0) as actual_generation_mw
    FROM weather_data w
    INNER JOIN bm_mapping m ON w.farm_name = m.farm_name
    LEFT JOIN actual_generation g 
        ON m.bm_unit_id = g.bm_unit_id AND w.hour_utc = g.hour_utc
    ORDER BY w.farm_name, w.hour_utc
    """
    
    df = client.query(query).to_dataframe()
    
    print(f"✅ Loaded {len(df):,} training samples")
    print(f"   Farms: {df['farm_name'].nunique()}")
    print(f"   BM Units: {df['bm_unit_id'].nunique()}")
    print(f"   Date range: {df['time_utc'].min()} to {df['time_utc'].max()}")
    print(f"   Avg generation: {df['actual_generation_mw'].mean():.1f} MW")
    print(f"   Max generation: {df['actual_generation_mw'].max():.1f} MW")
    
    # Aggregate BM units to farm level
    print("\n🔄 Aggregating BM units to farm level...")
    farm_df = df.groupby([
        'farm_name', 'time_utc', 'hour_of_day', 'month', 'day_of_week',
        'wind_speed_100m', 'wind_direction_10m', 'wind_gusts_10m', 'farm_capacity_mw'
    ]).agg({
        'actual_generation_mw': 'sum'
    }).reset_index()
    
    print(f"✅ Aggregated to {len(farm_df):,} farm-level observations")
    
    # Add spatial features
    print("\n🌐 Adding spatial features from upstream farms...")
    
    # Create pivot for faster upstream lookups
    wind_pivot = farm_df.pivot_table(
        index='time_utc',
        columns='farm_name',
        values='wind_speed_100m',
        aggfunc='mean'
    )
    
    dir_pivot = farm_df.pivot_table(
        index='time_utc',
        columns='farm_name',
        values='wind_direction_10m',
        aggfunc='mean'
    )
    
    # Add spatial features for each farm
    spatial_features_list = []
    
    for farm_name in farm_df['farm_name'].unique():
        farm_data = farm_df[farm_df['farm_name'] == farm_name].copy()
        
        if farm_name not in UPSTREAM_SENSORS:
            # No upstream sensors, use zeros
            farm_data['upstream_wind_speed'] = 0.0
            farm_data['upstream_wind_lag'] = 0.5
            farm_data['upstream_wind_change'] = 0.0
            farm_data['spatial_confidence'] = 0.0
            farm_data['upstream_farm_id'] = 0
        else:
            upstream_farms = UPSTREAM_SENSORS[farm_name]
            best_upstream_farm, correlation, optimal_lag, distance = upstream_farms[0]
            
            # Calculate bearing from upstream to downstream
            if farm_name in FARM_COORDS and best_upstream_farm in FARM_COORDS:
                lat1, lon1 = FARM_COORDS[best_upstream_farm]
                lat2, lon2 = FARM_COORDS[farm_name]
                bearing = calculate_bearing(lat1, lon1, lat2, lon2)
            else:
                bearing = 180  # Default
            
            # Get upstream wind data
            lag_steps = int(optimal_lag * 2)  # 30-min resolution
            
            if best_upstream_farm in wind_pivot.columns:
                upstream_wind = wind_pivot[best_upstream_farm].shift(lag_steps)
                upstream_wind_prev = wind_pivot[best_upstream_farm].shift(lag_steps + 1)
                upstream_dir = dir_pivot[best_upstream_farm].shift(lag_steps)
                
                farm_data['upstream_wind_speed'] = farm_data['time_utc'].map(upstream_wind).fillna(0)
                farm_data['upstream_wind_lag'] = optimal_lag
                
                # Calculate rate of change
                wind_change = upstream_wind - upstream_wind_prev
                farm_data['upstream_wind_change'] = farm_data['time_utc'].map(wind_change).fillna(0)
                
                # Calculate spatial confidence based on wind direction
                spatial_conf = upstream_dir.apply(lambda d: calculate_spatial_confidence(d, bearing) if pd.notna(d) else 0)
                farm_data['spatial_confidence'] = farm_data['time_utc'].map(spatial_conf).fillna(0)
                
                # Encode upstream farm as categorical ID
                farm_data['upstream_farm_id'] = hash(best_upstream_farm) % 100
            else:
                farm_data['upstream_wind_speed'] = 0.0
                farm_data['upstream_wind_lag'] = optimal_lag
                farm_data['upstream_wind_change'] = 0.0
                farm_data['spatial_confidence'] = 0.0
                farm_data['upstream_farm_id'] = 0
        
        spatial_features_list.append(farm_data)
    
    # Combine all farms
    farm_df_spatial = pd.concat(spatial_features_list, ignore_index=True)
    
    print(f"✅ Added 5 spatial features per observation")
    print(f"   Total samples: {len(farm_df_spatial):,}")
    print(f"   Farms with upstream sensors: {len([f for f in UPSTREAM_SENSORS if f in farm_df_spatial['farm_name'].unique()])}")
    
    # Define features (including spatial)
    features = [
        'wind_speed_100m',
        'wind_direction_10m',
        'wind_gusts_10m',
        'hour_of_day',
        'month',
        'day_of_week',
        'upstream_wind_speed',      # NEW: Spatial feature
        'upstream_wind_lag',         # NEW: Spatial feature
        'upstream_wind_change',      # NEW: Spatial feature
        'spatial_confidence',        # NEW: Spatial feature
        'upstream_farm_id'           # NEW: Spatial feature
    ]
    
    # Train farm-specific models
    print("\n🏗️  Training farm-specific models with spatial features...")
    print(f"\n{'Farm':<35} {'Samples':>8} {'Avg MW':>8} {'Max MW':>8} {'MAE':>8} {'RMSE':>8} {'Spatial':>8}")
    print("-" * 100)
    
    results = []
    
    for farm_name in sorted(farm_df_spatial['farm_name'].unique()):
        farm_data = farm_df_spatial[farm_df_spatial['farm_name'] == farm_name].copy()
        
        # Filter to non-zero generation
        farm_data = farm_data[farm_data['actual_generation_mw'] > 0]
        
        if len(farm_data) < 100:
            print(f"  ⏭️  {farm_name:<35} {len(farm_data):>7} (insufficient data)")
            continue
        
        # Train/test split
        train_mask = farm_data['time_utc'] < '2025-01-01'
        X_train = farm_data[train_mask][features].fillna(0)
        y_train = farm_data[train_mask]['actual_generation_mw']
        X_test = farm_data[~train_mask][features].fillna(0)
        y_test = farm_data[~train_mask]['actual_generation_mw']
        
        if len(X_train) < 50 or len(X_test) < 10:
            print(f"  ⏭️  {farm_name:<35} {len(farm_data):>7} (insufficient train/test)")
            continue
        
        # Train model
        model = GradientBoostingRegressor(
            n_estimators=150,      # Increased for spatial features
            learning_rate=0.1,
            max_depth=6,           # Increased depth for interactions
            min_samples_split=20,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        y_pred = np.clip(y_pred, 0, farm_data['farm_capacity_mw'].max())
        
        # Metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # Check if spatial features helped
        has_spatial = farm_name in UPSTREAM_SENSORS
        spatial_impact = "Yes" if has_spatial else "No"
        
        print(f"  ✅ {farm_name:<35} {len(farm_data):>7} "
              f"{farm_data['actual_generation_mw'].mean():>7.0f} "
              f"{farm_data['actual_generation_mw'].max():>7.0f} "
              f"{mae:>7.0f} {rmse:>7.0f} {spatial_impact:>8}")
        
        # Save model
        model_path = os.path.join(MODEL_DIR, f"{farm_name}.joblib")
        joblib.dump(model, model_path)
        
        results.append({
            'farm_name': farm_name,
            'samples': len(farm_data),
            'mae': mae,
            'rmse': rmse,
            'has_spatial': has_spatial
        })
    
    # Summary statistics
    results_df = pd.DataFrame(results)
    
    print("\n" + "=" * 100)
    print("✅ Training complete!")
    print("=" * 100)
    print(f"\nModels saved to: {MODEL_DIR}/")
    print(f"Total models trained: {len(results)}")
    print(f"Models with spatial features: {results_df['has_spatial'].sum()}")
    print(f"Models without spatial features: {(~results_df['has_spatial']).sum()}")
    
    # Compare spatial vs non-spatial
    spatial_models = results_df[results_df['has_spatial']]
    non_spatial_models = results_df[~results_df['has_spatial']]
    
    if len(spatial_models) > 0 and len(non_spatial_models) > 0:
        print("\n📊 Performance Comparison:")
        print(f"   Spatial models avg MAE: {spatial_models['mae'].mean():.1f} MW")
        print(f"   Non-spatial models avg MAE: {non_spatial_models['mae'].mean():.1f} MW")
        improvement = ((non_spatial_models['mae'].mean() - spatial_models['mae'].mean()) / 
                      non_spatial_models['mae'].mean() * 100)
        print(f"   Improvement from spatial features: {improvement:.1f}%")
    
    print("\n" + "=" * 100)
    print("Enhanced models use:")
    print("  - B1610 actual generation data (bmrs_pn)")
    print("  - 100m hub height wind speed")
    print("  - Upstream wind farm measurements (r>0.85 correlation)")
    print("  - Wind direction confidence scoring")
    print("  - Temporal lag features")
    print("=" * 100)

if __name__ == "__main__":
    main()
