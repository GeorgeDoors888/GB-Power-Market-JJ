#!/usr/bin/env python3
"""
Enhanced Weather Features for Wind Forecasting (Todo #16)

Creates interaction features that capture physical relationships:
1. temp_x_wind: Air density effects (cold air = denser = more power)
2. humidity_x_temp: Icing risk proxy (high humidity + near-freezing temp)
3. pressure_gradient: Frontal systems detection (rapid pressure changes)
4. wind_shear: Turbulence indicator (100m-10m speed difference)
5. temperature_gradient: Atmospheric stability
6. wind_power_density: Air density × wind_speed³

Expected improvement: +3-5% accuracy (based on literature)

Author: AI Coding Agent
Date: December 30, 2025
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import argparse

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_enhanced_features(df):
    """
    Create physics-based interaction features.
    
    Args:
        df: DataFrame with columns:
            - wind_speed_100m, wind_speed_10m (m/s)
            - temperature_2m (°C)
            - relative_humidity_2m (%)
            - pressure_msl (hPa)
            - wind_direction_10m (degrees)
    
    Returns:
        DataFrame with additional feature columns
    """
    
    print("Creating enhanced weather features...")
    
    # 1. Air density effects (temp_x_wind)
    # Colder air is denser → more power at same wind speed
    # Air density ≈ 353.05 / (temperature_K)
    # Simplified: use (1 / (temperature_C + 273.15)) as proxy
    df['temp_kelvin'] = df['temperature_2m'] + 273.15
    df['air_density_proxy'] = 353.05 / df['temp_kelvin']  # Simplified ideal gas law
    df['temp_x_wind'] = df['air_density_proxy'] * df['wind_speed_100m']
    
    # 2. Icing risk proxy (humidity_x_temp)
    # High humidity + near-freezing temp = icing risk
    # Peak risk around 0°C with high humidity
    df['icing_risk_score'] = (
        (df['relative_humidity_2m'] / 100) *  # Normalize to 0-1
        np.exp(-((df['temperature_2m'] - 0) ** 2) / 10)  # Gaussian centered at 0°C
    )
    df['humidity_x_temp'] = df['relative_humidity_2m'] * df['temperature_2m']
    
    # 3. Pressure gradient (frontal systems detection)
    # Rapid pressure changes indicate weather fronts
    df['pressure_gradient'] = df['pressure_msl'].diff().fillna(0)
    df['pressure_gradient_abs'] = df['pressure_gradient'].abs()
    
    # 4. Wind shear (turbulence indicator)
    # Large difference between 100m and 10m = high turbulence
    df['wind_shear'] = df['wind_speed_100m'] - df['wind_speed_10m']
    df['wind_shear_ratio'] = df['wind_speed_100m'] / (df['wind_speed_10m'] + 0.1)  # Avoid division by zero
    
    # 5. Temperature gradient (atmospheric stability)
    # Rapid temp changes = unstable atmosphere = gusty winds
    df['temperature_gradient'] = df['temperature_2m'].diff().fillna(0)
    df['temperature_gradient_abs'] = df['temperature_gradient'].abs()
    
    # 6. Wind power density
    # Power ∝ air_density × wind_speed³
    df['wind_power_density'] = df['air_density_proxy'] * (df['wind_speed_100m'] ** 3)
    
    # 7. Wind direction change (frontal passage)
    # Sudden wind direction shifts = frontal systems
    df['wind_direction_change'] = df['wind_direction_10m'].diff().fillna(0)
    # Handle 360° wrap-around
    df.loc[df['wind_direction_change'] > 180, 'wind_direction_change'] -= 360
    df.loc[df['wind_direction_change'] < -180, 'wind_direction_change'] += 360
    df['wind_direction_change_abs'] = df['wind_direction_change'].abs()
    
    # 8. Diurnal stability indicator
    # hour + temperature interaction (thermal effects)
    df['hour'] = pd.to_datetime(df['settlementDate']).dt.hour if 'settlementDate' in df.columns else 12
    df['diurnal_stability'] = np.sin(2 * np.pi * df['hour'] / 24) * df['temperature_2m']
    
    # 9. Humidity-pressure interaction
    # High humidity + low pressure = precipitation/storms
    df['humidity_x_pressure'] = df['relative_humidity_2m'] * (1000 - df['pressure_msl'])
    
    # 10. Wind consistency (rolling std)
    # Low std = steady winds, high std = gusty/variable
    df['wind_consistency'] = df['wind_speed_100m'].rolling(window=6, min_periods=1).std()
    
    print(f"✅ Created {10} enhanced feature groups:")
    print("   1. temp_x_wind (air density effects)")
    print("   2. icing_risk_score, humidity_x_temp (icing proxy)")
    print("   3. pressure_gradient, pressure_gradient_abs (frontal systems)")
    print("   4. wind_shear, wind_shear_ratio (turbulence)")
    print("   5. temperature_gradient, temperature_gradient_abs (stability)")
    print("   6. wind_power_density (power potential)")
    print("   7. wind_direction_change, wind_direction_change_abs (frontal passage)")
    print("   8. diurnal_stability (thermal effects)")
    print("   9. humidity_x_pressure (storm indicator)")
    print("  10. wind_consistency (wind variability)")
    
    return df

def get_training_data_with_features(farm_name, start_date, end_date):
    """
    Get training data for a farm with enhanced weather features.
    
    Args:
        farm_name: Wind farm name
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        DataFrame with generation + enhanced weather features
    """
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH wind_data AS (
        SELECT
            farm_name,
            settlementDate,
            generation,
            wind_speed_100m,
            wind_speed_10m,
            wind_direction_10m,
            wind_gusts_10m,
            temperature_2m,
            relative_humidity_2m,
            pressure_msl,
            cloud_cover,
            precipitation
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
        WHERE farm_name = '{farm_name}'
          AND DATE(settlementDate) BETWEEN '{start_date}' AND '{end_date}'
          AND generation IS NOT NULL
        ORDER BY settlementDate
    )
    SELECT * FROM wind_data
    """
    
    print(f"\nFetching data for {farm_name} ({start_date} to {end_date})...")
    df = client.query(query).to_dataframe()
    print(f"  Raw records: {len(df):,}")
    
    if len(df) == 0:
        print(f"  ⚠️  No data for {farm_name}")
        return None
    
    # Create enhanced features
    df = create_enhanced_features(df)
    
    # Remove intermediate columns
    df = df.drop(columns=['temp_kelvin', 'air_density_proxy'], errors='ignore')
    
    print(f"  ✅ Total features: {len(df.columns)} (including {10} enhanced groups)")
    
    return df

def analyze_feature_importance_sample(farm_name="Hornsea 1"):
    """
    Quick analysis of enhanced features on one farm.
    Shows correlation with generation.
    """
    
    print("="*70)
    print("Enhanced Features Analysis (Sample Farm)")
    print("="*70)
    
    # Get recent data (last 6 months for speed)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    df = get_training_data_with_features(farm_name, start_date, end_date)
    
    if df is None:
        print("❌ No data available")
        return
    
    # Calculate correlations with generation
    print(f"\n{'='*70}")
    print("Feature Correlations with Generation:")
    print(f"{'='*70}")
    
    enhanced_features = [
        'temp_x_wind',
        'icing_risk_score',
        'humidity_x_temp',
        'pressure_gradient',
        'pressure_gradient_abs',
        'wind_shear',
        'wind_shear_ratio',
        'temperature_gradient',
        'temperature_gradient_abs',
        'wind_power_density',
        'wind_direction_change',
        'wind_direction_change_abs',
        'diurnal_stability',
        'humidity_x_pressure',
        'wind_consistency'
    ]
    
    correlations = []
    for feature in enhanced_features:
        if feature in df.columns:
            corr = df[[feature, 'generation']].corr().iloc[0, 1]
            correlations.append((feature, corr))
    
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    
    print(f"\n{'Feature':<30} {'Correlation':>15}")
    print("-" * 50)
    for feature, corr in correlations:
        print(f"{feature:<30} {corr:>15.4f}")
    
    # Top 5 features
    print(f"\n{'='*70}")
    print("Top 5 Enhanced Features:")
    print(f"{'='*70}")
    top_5 = correlations[:5]
    for rank, (feature, corr) in enumerate(top_5, 1):
        print(f"{rank}. {feature}: {corr:.4f}")
    
    # Statistics
    print(f"\n{'='*70}")
    print("Enhanced Features Statistics:")
    print(f"{'='*70}")
    
    stats_features = ['wind_power_density', 'icing_risk_score', 'wind_shear', 'pressure_gradient_abs']
    
    for feature in stats_features:
        if feature in df.columns:
            print(f"\n{feature}:")
            print(f"  Min: {df[feature].min():.4f}")
            print(f"  Mean: {df[feature].mean():.4f}")
            print(f"  Max: {df[feature].max():.4f}")
            print(f"  Std: {df[feature].std():.4f}")
    
    print(f"\n{'='*70}")
    print("✅ ENHANCED FEATURES ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print("Next Steps:")
    print("1. Retrain models with enhanced features")
    print("2. Compare accuracy: baseline vs enhanced")
    print("3. Expected improvement: +3-5% (based on literature)")
    print(f"{'='*70}")

def main():
    parser = argparse.ArgumentParser(description="Enhanced Weather Features (Todo #16)")
    parser.add_argument("--farm", default="Hornsea 1", help="Farm name for analysis")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    if args.start_date and args.end_date:
        df = get_training_data_with_features(args.farm, args.start_date, args.end_date)
        if df is not None:
            output_file = f"enhanced_features_{args.farm.replace(' ', '_')}.csv"
            df.to_csv(output_file, index=False)
            print(f"\n✅ Saved to: {output_file}")
    else:
        # Run sample analysis
        analyze_feature_importance_sample(args.farm)

if __name__ == "__main__":
    main()
