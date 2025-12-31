#!/usr/bin/env python3
"""
Drift Monitoring - Population Stability Index (PSI) Calculation
Purpose: Detect model drift weekly, trigger retraining when PSI > 0.2
Method: Compare current week vs training distribution for key features
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import pickle
import os
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODELS_DIR = "models"

# PSI thresholds
PSI_STABLE = 0.1  # No drift
PSI_WARNING = 0.2  # Minor drift, monitor
PSI_CRITICAL = 0.25  # Significant drift, retrain

# Features to monitor
FEATURES_TO_MONITOR = [
    'wind_speed_100m',
    'wind_direction_10m',
    'wind_gusts_10m',
    'temperature_2m',
    'pressure_msl',
    'relative_humidity_2m'
]


def calculate_psi(expected, actual, bins=10):
    """
    Calculate Population Stability Index (PSI).
    
    PSI measures the shift in distribution between two datasets.
    PSI < 0.1: No significant change
    PSI 0.1-0.2: Minor change, monitor
    PSI > 0.2: Significant change, retrain model
    
    Formula: PSI = Σ (Actual% - Expected%) × ln(Actual% / Expected%)
    """
    # Handle edge cases
    if len(expected) == 0 or len(actual) == 0:
        return np.nan
    
    # Create bins based on expected distribution
    try:
        breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
        breakpoints = np.unique(breakpoints)  # Remove duplicates
        
        if len(breakpoints) < 2:
            return np.nan
    except Exception:
        return np.nan
    
    # Calculate distribution percentages
    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)
    
    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)
    
    # Avoid division by zero
    expected_pct = np.where(expected_pct == 0, 0.0001, expected_pct)
    actual_pct = np.where(actual_pct == 0, 0.0001, actual_pct)
    
    # Calculate PSI
    psi_values = (actual_pct - expected_pct) * np.log(actual_pct / expected_pct)
    psi = np.sum(psi_values)
    
    return psi


def get_training_distribution(farm_name):
    """Get training data distribution for baseline comparison."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get training period (2021-2024)
    query = f"""
    SELECT
        wind_speed_100m,
        wind_direction_10m,
        wind_gusts_10m
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    WHERE farm_name = '{farm_name}'
      AND DATE(time_utc) >= '2021-01-01'
      AND DATE(time_utc) < '2025-01-01'
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"  ⚠️  Error getting training distribution: {e}")
        return pd.DataFrame()


def get_current_week_data(farm_name):
    """Get last 7 days of data for drift comparison."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    query = f"""
    SELECT
        wind_speed_100m,
        wind_direction_10m,
        wind_gusts_10m
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    WHERE farm_name = '{farm_name}'
      AND DATE(time_utc) >= '{start_date}'
      AND DATE(time_utc) <= '{end_date}'
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"  ⚠️  Error getting current week data: {e}")
        return pd.DataFrame()


def get_current_week_weather(farm_name):
    """Get weather data from era5_weather_icing if available."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    query = f"""
    SELECT
        temperature_2m,
        relative_humidity_2m,
        pressure_msl
    FROM `{PROJECT_ID}.{DATASET}.era5_weather_icing`
    WHERE farm_name = '{farm_name}'
      AND DATE(time_utc) >= '{start_date}'
      AND DATE(time_utc) <= '{end_date}'
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception:
        # Table doesn't exist yet
        return pd.DataFrame()


def analyze_farm_drift(farm_name):
    """Calculate PSI for all features for one farm."""
    print(f"\n{'='*80}")
    print(f"Farm: {farm_name}")
    print(f"{'='*80}")
    
    # Get training distribution
    train_df = get_training_distribution(farm_name)
    
    if train_df.empty:
        print(f"  ⚠️  No training data available")
        return None
    
    print(f"  Training period: 2021-2024 ({len(train_df):,} hours)")
    
    # Get current week data
    current_df = get_current_week_data(farm_name)
    
    if current_df.empty:
        print(f"  ⚠️  No current week data available")
        return None
    
    print(f"  Current week: {len(current_df):,} hours")
    print()
    
    # Calculate PSI for each feature
    psi_results = {}
    
    for feature in ['wind_speed_100m', 'wind_direction_10m', 'wind_gusts_10m']:
        if feature not in train_df.columns or feature not in current_df.columns:
            continue
        
        # Remove NaN values
        train_values = train_df[feature].dropna().values
        current_values = current_df[feature].dropna().values
        
        if len(train_values) < 100 or len(current_values) < 10:
            continue
        
        psi = calculate_psi(train_values, current_values)
        
        if not np.isnan(psi):
            psi_results[feature] = psi
            
            # Determine status
            if psi < PSI_STABLE:
                status = "✅ STABLE"
            elif psi < PSI_WARNING:
                status = "⚠️  WARNING"
            else:
                status = "🔴 CRITICAL"
            
            print(f"  {feature:<25} PSI: {psi:.4f}  {status}")
    
    # Get weather data if available
    weather_df = get_current_week_weather(farm_name)
    
    if not weather_df.empty:
        print()
        print(f"  Weather data: {len(weather_df):,} hours")
        
        # Note: Can't calculate PSI without training distribution
        # This would require ERA5 training data (Todo #4-5)
        print(f"  ⚠️  Weather PSI requires ERA5 training data (coming soon)")
    
    # Overall assessment
    print()
    if psi_results:
        max_psi = max(psi_results.values())
        avg_psi = np.mean(list(psi_results.values()))
        
        print(f"  Overall Assessment:")
        print(f"    Max PSI: {max_psi:.4f}")
        print(f"    Avg PSI: {avg_psi:.4f}")
        
        if max_psi >= PSI_CRITICAL:
            print(f"    Action: 🔴 RETRAIN IMMEDIATELY")
            action = "RETRAIN"
        elif max_psi >= PSI_WARNING:
            print(f"    Action: ⚠️  MONITOR CLOSELY")
            action = "MONITOR"
        else:
            print(f"    Action: ✅ NO ACTION NEEDED")
            action = "NONE"
        
        return {
            'farm_name': farm_name,
            'max_psi': max_psi,
            'avg_psi': avg_psi,
            'action': action,
            'training_hours': len(train_df),
            'current_hours': len(current_df),
            **{f"{k}_psi": v for k, v in psi_results.items()}
        }
    else:
        print(f"  ⚠️  Could not calculate PSI")
        return None


def save_drift_report(results):
    """Save drift monitoring results to CSV."""
    if not results:
        print("\n⚠️  No results to save")
        return
    
    df = pd.DataFrame(results)
    
    # Add timestamp
    df['check_date'] = datetime.now().strftime('%Y-%m-%d')
    
    output_file = 'drift_monitoring_report.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\n{'='*80}")
    print(f"Drift Report saved to: {output_file}")
    print(f"{'='*80}")
    
    # Summary
    print("\nSummary:")
    print(f"  Farms analyzed: {len(df)}")
    
    retrain_farms = df[df['action'] == 'RETRAIN']
    monitor_farms = df[df['action'] == 'MONITOR']
    stable_farms = df[df['action'] == 'NONE']
    
    print(f"  🔴 Retrain needed: {len(retrain_farms)}")
    if len(retrain_farms) > 0:
        print(f"     {', '.join(retrain_farms['farm_name'].tolist())}")
    
    print(f"  ⚠️  Monitor: {len(monitor_farms)}")
    if len(monitor_farms) > 0:
        print(f"     {', '.join(monitor_farms['farm_name'].tolist())}")
    
    print(f"  ✅ Stable: {len(stable_farms)}")


def send_alert_email(retrain_farms):
    """Send email alert for farms needing retraining (placeholder)."""
    if not retrain_farms:
        return
    
    print(f"\n{'='*80}")
    print(f"📧 EMAIL ALERT (Placeholder)")
    print(f"{'='*80}")
    print(f"To: george@upowerenergy.uk")
    print(f"Subject: Wind Forecast Drift Alert - {len(retrain_farms)} farms need retraining")
    print()
    print(f"Farms requiring retraining:")
    for farm in retrain_farms:
        print(f"  - {farm['farm_name']} (Max PSI: {farm['max_psi']:.4f})")
    print()
    print(f"Action: Run training script to update models")
    print(f"Command: python3 build_wind_power_curves_optimized_parallel.py")
    print(f"{'='*80}")


def main():
    """Main drift monitoring pipeline."""
    print("="*80)
    print("Wind Forecasting Drift Monitoring (PSI)")
    print("="*80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get list of farms
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT farm_name
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    ORDER BY farm_name
    """
    
    farms_df = client.query(query).to_dataframe()
    farms = farms_df['farm_name'].tolist()
    
    print(f"Monitoring {len(farms)} wind farms")
    print(f"Week: {(datetime.now() - timedelta(days=7)).date()} to {datetime.now().date()}")
    print()
    
    # Analyze first 10 farms (testing)
    results = []
    
    for i, farm_name in enumerate(farms[:10], 1):
        print(f"\n[{i}/{min(10, len(farms))}]")
        result = analyze_farm_drift(farm_name)
        if result:
            results.append(result)
    
    # Save report
    save_drift_report(results)
    
    # Send alerts if needed
    retrain_farms = [r for r in results if r['action'] == 'RETRAIN']
    if retrain_farms:
        send_alert_email(retrain_farms)
    
    print("\n" + "="*80)
    print("✅ Drift Monitoring Complete")
    print("="*80)
    print("\nNext Steps:")
    print("1. Review drift_monitoring_report.csv")
    print("2. For farms needing retraining:")
    print("   python3 build_wind_power_curves_optimized_parallel.py")
    print("3. Setup weekly cron job:")
    print("   0 8 * * 1 cd /home/george/GB-Power-Market-JJ && python3 drift_monitoring_psi.py")
    print("="*80)


if __name__ == "__main__":
    main()
