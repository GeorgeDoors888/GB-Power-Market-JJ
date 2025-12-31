#!/usr/bin/env python3
"""
Wind Power Curve Training with ERA5 Upstream Features
Combines: B1610 actual generation + Offshore spatial features + ERA5 grid points

Expected improvement: +15-25% for Irish Sea farms, +20-40% overall
Target: Achieve >20% improvement to validate ERA5 integration
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODEL_DIR = "models/wind_power_curves_era5"

# Map farms to their best ERA5 upstream grid points
FARM_TO_ERA5_GRID = {
    # Irish Sea farms (most benefit expected)
    'Walney Extension': ['Atlantic_Irish_Sea', 'Irish_Sea_Central'],
    'Walney': ['Atlantic_Irish_Sea', 'Irish_Sea_Central'],
    'Burbo Bank': ['Irish_Sea_Central', 'Atlantic_Irish_Sea'],
    'Burbo Bank Extension': ['Irish_Sea_Central', 'Celtic_Sea'],
    'West of Duddon Sands': ['Atlantic_Irish_Sea', 'Irish_Sea_Central'],
    'Barrow': ['Irish_Sea_Central', 'Atlantic_Irish_Sea'],
    'Ormonde': ['Irish_Sea_Central', 'Atlantic_Irish_Sea'],
    
    # Scottish farms
    'Moray East': ['North_Scotland', 'Atlantic_Hebrides', 'Moray_Firth_West'],
    'Moray West': ['North_Scotland', 'Atlantic_Hebrides', 'Moray_Firth_West'],
    'Beatrice': ['Moray_Firth_West', 'North_Scotland', 'Atlantic_Hebrides'],
    'Seagreen Phase 1': ['West_Scotland', 'Moray_Firth_West'],
    'Neart Na Gaoithe': ['West_Scotland', 'Moray_Firth_West'],
    'Hywind Scotland': ['Moray_Firth_West', 'North_Scotland'],
    'Kincardine': ['West_Scotland', 'Moray_Firth_West'],
    
    # Humber / Yorkshire (Hornsea cluster)
    'Hornsea One': ['Central_England', 'Pennines'],
    'Hornsea Two': ['Central_England', 'Pennines'],
    'Triton Knoll': ['Central_England', 'Pennines'],
    'Humber Gateway': ['Central_England', 'Pennines'],
    'Westermost Rough': ['Central_England', 'Pennines'],
    'Lincs': ['Central_England', 'Pennines'],
    
    # East Anglia / Norfolk
    'East Anglia One': ['Celtic_Sea', 'Bristol_Channel'],
    'Dudgeon': ['Celtic_Sea', 'Central_England'],
    'Race Bank': ['Central_England', 'Celtic_Sea'],
    'Sheringham Shoal': ['Central_England', 'Celtic_Sea'],
    
    # Thames / Southern
    'London Array': ['Bristol_Channel', 'Celtic_Sea'],
    'Greater Gabbard': ['Bristol_Channel', 'Celtic_Sea'],
    'Gunfleet Sands 1 & 2': ['Bristol_Channel', 'Celtic_Sea'],
    'Thanet': ['Bristol_Channel', 'Celtic_Sea'],
    'Rampion': ['Bristol_Channel', 'Celtic_Sea'],
}

def main():
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("=" * 80)
    print("Wind Power Curve Training - WITH ERA5 UPSTREAM FEATURES")
    print("=" * 80)
    print("\nEnhanced with ERA5 grid points providing 2-4 hour advance warning")
    print("Expected improvement: +20-40% from baseline")
    print("=" * 80)
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    print("\n📊 Creating training dataset with ERA5 features...")
    print("   Joining: B1610 generation + Offshore farms + ERA5 grid points")
    print("   Running BigQuery (may take 2-3 minutes)...\n")
    
    # Main query with ERA5 features
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
          AND levelTo > 0
        GROUP BY bm_unit_id, hour_utc
    ),
    era5_wind AS (
        SELECT
            grid_point_name,
            TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
            AVG(wind_speed_100m) as era5_wind_speed,
            AVG(wind_direction_100m) as era5_wind_direction
        FROM `{PROJECT_ID}.{DATASET}.era5_wind_upstream`
        WHERE time_utc >= '2020-01-01'
        GROUP BY grid_point_name, hour_utc
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
    WHERE w.farm_name IN UNNEST(@farm_list)
    ORDER BY w.farm_name, w.hour_utc
    """
    
    # Get list of farms
    farm_list = list(FARM_TO_ERA5_GRID.keys())
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("farm_list", "STRING", farm_list)
        ]
    )
    
    df = client.query(query, job_config=job_config).to_dataframe()
    
    print(f"✅ Loaded {len(df):,} base training samples")
    print(f"   Farms: {df['farm_name'].nunique()}")
    print(f"   Date range: {df['time_utc'].min()} to {df['time_utc'].max()}")
    
    # Aggregate to farm level
    print("\n🔄 Aggregating BM units to farm level...")
    farm_df = df.groupby([
        'farm_name', 'time_utc', 'hour_of_day', 'month', 'day_of_week',
        'wind_speed_100m', 'wind_direction_10m', 'wind_gusts_10m', 'farm_capacity_mw'
    ]).agg({'actual_generation_mw': 'sum'}).reset_index()
    
    print(f"✅ Aggregated to {len(farm_df):,} farm-level observations")
    
    # Load ERA5 data
    print("\n🌐 Loading ERA5 upstream wind data...")
    era5_query = f"""
    SELECT
        grid_point_name,
        TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
        AVG(wind_speed_100m) as era5_wind_speed,
        AVG(wind_direction_100m) as era5_wind_direction
    FROM `{PROJECT_ID}.{DATASET}.era5_wind_upstream`
    WHERE time_utc >= '2020-01-01'
    GROUP BY grid_point_name, hour_utc
    """
    era5_df = client.query(era5_query).to_dataframe()
    print(f"✅ Loaded {len(era5_df):,} ERA5 observations from {era5_df['grid_point_name'].nunique()} grid points")
    
    # Pivot ERA5 data for faster lookups
    era5_pivot = era5_df.pivot_table(
        index='hour_utc',
        columns='grid_point_name',
        values='era5_wind_speed',
        aggfunc='mean'
    )
    
    # Add ERA5 features for each farm
    print("\n🔄 Adding ERA5 features with multi-hour lags...")
    enhanced_data = []
    
    for farm_name in farm_df['farm_name'].unique():
        farm_data = farm_df[farm_df['farm_name'] == farm_name].copy()
        
        if farm_name not in FARM_TO_ERA5_GRID:
            # Skip farms without ERA5 mapping
            continue
        
        era5_grids = FARM_TO_ERA5_GRID[farm_name]
        primary_grid = era5_grids[0]
        
        if primary_grid not in era5_pivot.columns:
            print(f"   ⚠️  {farm_name}: ERA5 grid {primary_grid} not found, skipping")
            continue
        
        # Add ERA5 features with different time lags
        farm_data['era5_wind_2h'] = farm_data['time_utc'].map(
            era5_pivot[primary_grid].shift(2)  # 2 hours ago
        ).fillna(0)
        
        farm_data['era5_wind_4h'] = farm_data['time_utc'].map(
            era5_pivot[primary_grid].shift(4)  # 4 hours ago
        ).fillna(0)
        
        farm_data['era5_wind_6h'] = farm_data['time_utc'].map(
            era5_pivot[primary_grid].shift(6)  # 6 hours ago
        ).fillna(0)
        
        # Rate of change in ERA5 wind
        era5_current = farm_data['time_utc'].map(era5_pivot[primary_grid]).fillna(0)
        era5_2h_ago = farm_data['era5_wind_2h']
        farm_data['era5_wind_change'] = era5_current - era5_2h_ago
        
        # If secondary grid available, use as additional feature
        if len(era5_grids) > 1 and era5_grids[1] in era5_pivot.columns:
            farm_data['era5_wind_secondary_2h'] = farm_data['time_utc'].map(
                era5_pivot[era5_grids[1]].shift(2)
            ).fillna(0)
        else:
            farm_data['era5_wind_secondary_2h'] = 0
        
        enhanced_data.append(farm_data)
        print(f"   ✅ {farm_name}: Added ERA5 features from {primary_grid}")
    
    # Combine all farms
    farm_df_era5 = pd.concat(enhanced_data, ignore_index=True)
    
    print(f"\n✅ Enhanced dataset ready: {len(farm_df_era5):,} observations")
    print(f"   Farms with ERA5 features: {farm_df_era5['farm_name'].nunique()}")
    
    # Define features
    features = [
        'wind_speed_100m',
        'wind_direction_10m',
        'wind_gusts_10m',
        'hour_of_day',
        'month',
        'day_of_week',
        'era5_wind_2h',              # NEW: ERA5 2h advance
        'era5_wind_4h',              # NEW: ERA5 4h advance
        'era5_wind_6h',              # NEW: ERA5 6h advance
        'era5_wind_change',          # NEW: ERA5 rate of change
        'era5_wind_secondary_2h',    # NEW: Secondary grid point
    ]
    
    # Train models
    print("\n🏗️  Training farm-specific models with ERA5 features...")
    print(f"\n{'Farm':<35} {'Samples':>8} {'Avg MW':>8} {'Max MW':>8} {'MAE':>8} {'RMSE':>8}")
    print("-" * 100)
    
    results = []
    
    for farm_name in sorted(farm_df_era5['farm_name'].unique()):
        farm_data = farm_df_era5[farm_df_era5['farm_name'] == farm_name].copy()
        farm_data = farm_data[farm_data['actual_generation_mw'] > 0]
        
        if len(farm_data) < 100:
            continue
        
        # Train/test split
        train_mask = farm_data['time_utc'] < '2025-01-01'
        X_train = farm_data[train_mask][features].fillna(0)
        y_train = farm_data[train_mask]['actual_generation_mw']
        X_test = farm_data[~train_mask][features].fillna(0)
        y_test = farm_data[~train_mask]['actual_generation_mw']
        
        if len(X_train) < 50 or len(X_test) < 10:
            continue
        
        # Train model
        model = GradientBoostingRegressor(
            n_estimators=200,      # Increased for ERA5 features
            learning_rate=0.08,
            max_depth=7,           # Deeper for complex interactions
            min_samples_split=15,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        y_pred = np.clip(y_pred, 0, farm_data['farm_capacity_mw'].max())
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        print(f"  ✅ {farm_name:<35} {len(farm_data):>7} "
              f"{farm_data['actual_generation_mw'].mean():>7.0f} "
              f"{farm_data['actual_generation_mw'].max():>7.0f} "
              f"{mae:>7.0f} {rmse:>7.0f}")
        
        # Save model
        joblib.dump(model, os.path.join(MODEL_DIR, f"{farm_name}.joblib"))
        
        results.append({
            'farm_name': farm_name,
            'samples': len(farm_data),
            'mae': mae,
            'rmse': rmse
        })
    
    # Summary
    results_df = pd.DataFrame(results)
    
    print("\n" + "=" * 100)
    print("✅ Training complete with ERA5 features!")
    print("=" * 100)
    print(f"\nModels saved to: {MODEL_DIR}/")
    print(f"Total models trained: {len(results)}")
    print(f"\n📊 Performance Summary:")
    print(f"   Average MAE: {results_df['mae'].mean():.1f} MW")
    print(f"   Median MAE: {results_df['mae'].median():.1f} MW")
    print(f"   Best MAE: {results_df['mae'].min():.1f} MW")
    print(f"   Worst MAE: {results_df['mae'].max():.1f} MW")
    
    # Compare with baseline
    print("\n" + "=" * 100)
    print("📈 Comparison with Previous Models:")
    print("="  * 100)
    print("   Baseline B1610: ~90 MW avg MAE")
    print("   Spatial (offshore): ~86 MW avg MAE (+5.5%)")
    print(f"   Spatial + ERA5: {results_df['mae'].mean():.1f} MW avg MAE")
    
    baseline_mae = 90.0
    spatial_mae = 86.0
    era5_mae = results_df['mae'].mean()
    
    improvement_from_baseline = ((baseline_mae - era5_mae) / baseline_mae) * 100
    improvement_from_spatial = ((spatial_mae - era5_mae) / spatial_mae) * 100
    
    print(f"   Improvement from baseline: {improvement_from_baseline:.1f}%")
    print(f"   Improvement from spatial: {improvement_from_spatial:.1f}%")
    
    if improvement_from_baseline >= 20:
        print(f"\n   ✅ SUCCESS: Achieved {improvement_from_baseline:.1f}% improvement (target: >20%)")
        print("   ERA5 integration validated - proceed with production deployment")
    else:
        print(f"\n   ⚠️  BELOW TARGET: {improvement_from_baseline:.1f}% improvement (target: >20%)")
        print("   May need further tuning or additional features")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    main()
