#!/usr/bin/env python3
"""
Comprehensive Weather-Wave-Generation Correlation Analysis
Identifies how weather conditions (waves, temperature, humidity, wind speed) 
correlate with wind turbine production drops

Author: AI Coding Agent
Date: January 1, 2026
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def main():
    print("="*80)
    print("🌊⚡🌦️  COMPREHENSIVE WEATHER-GENERATION CORRELATION ANALYSIS")
    print("="*80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # ========================================================================
    # 1. Get Wind Farms with Complete Data
    # ========================================================================
    print("\n📊 Step 1: Identifying wind farms with complete data...")
    
    query_farms = f"""
    SELECT DISTINCT farm_name, SUM(capacity_mw) as total_capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu`
    GROUP BY farm_name
    HAVING SUM(capacity_mw) > 200
    ORDER BY total_capacity_mw DESC
    LIMIT 15
    """
    
    farms_df = client.query(query_farms).to_dataframe()
    print(f"✅ Found {len(farms_df)} large wind farms")
    print(f"   Top farms: {', '.join(farms_df['farm_name'].head(5).tolist())}")
    
    # ========================================================================
    # 2. Combined Wave + Weather + Generation Analysis (2024-2025)
    # ========================================================================
    print("\n📊 Step 2: Fetching combined data (this will take 60-90 seconds)...")
    
    farm_names_str = ', '.join([f"'{name}'" for name in farms_df['farm_name'].head(10)])
    
    query_combined = f"""
    WITH hourly_generation AS (
      -- Aggregate generation by farm (using AVG not SUM to avoid double-counting settlement periods)
      SELECT 
        mapping.farm_name,
        TIMESTAMP_TRUNC(TIMESTAMP(pn.settlementDate), HOUR) as hour,
        AVG(pn.levelTo) as avg_generation_mw,
        MAX(pn.levelTo) as max_bmu_mw,
        COUNT(DISTINCT pn.bmUnit) as active_bmus,
        MAX(mapping.capacity_mw) as farm_capacity_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_pn` pn
      INNER JOIN `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu` mapping
        ON pn.bmUnit = mapping.bm_unit_id
      WHERE pn.settlementDate >= '2024-01-01'
        AND pn.settlementDate < '2026-01-01'
        AND pn.levelTo >= 0
      GROUP BY mapping.farm_name, hour
    ),
    
    farm_locations AS (
      SELECT name as farm_name, latitude, longitude, capacity_mw
      FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
    ),
    
    combined_data AS (
      SELECT
        farms.farm_name,
        farms.capacity_mw,
        farms.latitude as farm_lat,
        farms.longitude as farm_lon,
        
        -- Time
        TIMESTAMP_TRUNC(waves.time, HOUR) as hour,
        EXTRACT(MONTH FROM waves.time) as month,
        EXTRACT(HOUR FROM waves.time) as hour_of_day,
        
        -- Wave metrics (nearest grid point)
        AVG(waves.VHM0) as sig_wave_height_m,
        AVG(waves.VMDR) as wave_direction_deg,
        AVG(waves.VTPK) as peak_wave_period_s,
        AVG(waves.VHM0_WW) as wind_wave_height_m,
        AVG(waves.VHM0_SW1) as swell_wave_height_m,
        
        -- Weather metrics from ERA5
        AVG(era.wind_speed_100m) as wind_speed_100m_ms,
        AVG(era.temperature_2m) as temperature_2m_c,
        AVG(era.relative_humidity_2m) as humidity_pct,
        AVG(era.precipitation) as precipitation_mm,
        0.0 as pressure_hpa,  -- Not available in this table
        
        -- Generation metrics
        gen.avg_generation_mw as total_generation_mw,
        gen.max_bmu_mw,
        gen.active_bmus,
        
        -- Capacity factor
        SAFE_DIVIDE(gen.avg_generation_mw, farms.capacity_mw) * 100 as capacity_factor_pct,
        
        -- Distance to wave grid point (aggregated)
        MIN(SQRT(
          POW((waves.latitude - farms.latitude) * 111.0, 2) + 
          POW((waves.longitude - farms.longitude) * 111.0 * COS(farms.latitude * 3.14159/180), 2)
        )) as distance_km
        
      FROM farm_locations farms
      
      -- Join to wave data (nearest grid point within 50km)
      INNER JOIN `{PROJECT_ID}.{DATASET}.cmems_waves_uk_grid` waves
        ON SQRT(
          POW((waves.latitude - farms.latitude) * 111.0, 2) + 
          POW((waves.longitude - farms.longitude) * 111.0 * COS(farms.latitude * 3.14159/180), 2)
        ) < 50
        AND waves.time >= '2024-01-01'
        AND waves.time < '2026-01-01'
      
      -- Join to ERA5 weather data
      LEFT JOIN `{PROJECT_ID}.{DATASET}.era5_weather_data` era
        ON farms.farm_name = era.farm_name
        AND TIMESTAMP_TRUNC(waves.time, HOUR) = TIMESTAMP_TRUNC(era.timestamp, HOUR)
      
      -- Join to generation data
      INNER JOIN hourly_generation gen
        ON farms.farm_name = gen.farm_name
        AND TIMESTAMP_TRUNC(waves.time, HOUR) = gen.hour
      
      WHERE farms.farm_name IN ({farm_names_str})
      
      GROUP BY 
        farms.farm_name, farms.capacity_mw, farms.latitude, farms.longitude,
        TIMESTAMP_TRUNC(waves.time, HOUR), EXTRACT(MONTH FROM waves.time), EXTRACT(HOUR FROM waves.time),
        gen.avg_generation_mw, gen.max_bmu_mw, gen.active_bmus
    )
    
    SELECT 
      farm_name,
      capacity_mw,
      hour,
      month,
      hour_of_day,
      sig_wave_height_m,
      wave_direction_deg,
      peak_wave_period_s,
      wind_wave_height_m,
      swell_wave_height_m,
      wind_speed_100m_ms,
      temperature_2m_c,
      humidity_pct,
      precipitation_mm,
      pressure_hpa,
      total_generation_mw,
      capacity_factor_pct,
      distance_km,
      
      -- Weather-induced curtailment categories
      CASE
        WHEN sig_wave_height_m >= 4.0 AND capacity_factor_pct < 30 THEN 'High Waves'
        WHEN temperature_2m_c < 0 AND capacity_factor_pct < 30 THEN 'Icing Risk'
        WHEN precipitation_mm > 5 AND capacity_factor_pct < 30 THEN 'Heavy Rain'
        WHEN wind_speed_100m_ms > 25 AND capacity_factor_pct < 20 THEN 'Storm Shutdown'
        WHEN wind_speed_100m_ms < 5 AND capacity_factor_pct < 20 THEN 'Low Wind'
        ELSE 'Normal Operation'
      END as curtailment_reason,
      
      -- Wave severity
      CASE 
        WHEN sig_wave_height_m < 2.0 THEN 'Calm'
        WHEN sig_wave_height_m < 4.0 THEN 'Moderate'
        WHEN sig_wave_height_m < 6.0 THEN 'Rough'
        ELSE 'Very Rough'
      END as sea_state
      
    FROM combined_data
    WHERE sig_wave_height_m IS NOT NULL
      AND total_generation_mw IS NOT NULL
      AND distance_km < 30
    ORDER BY farm_name, hour
    """
    
    print("   ⏳ Running BigQuery (60-90 seconds)...")
    combined_df = client.query(query_combined).to_dataframe()
    print(f"✅ Retrieved {len(combined_df):,} hourly observations")
    print(f"   Date range: {combined_df['hour'].min()} to {combined_df['hour'].max()}")
    print(f"   Farms analyzed: {combined_df['farm_name'].nunique()}")
    
    # Data quality check
    print(f"\n📊 Data Availability:")
    print(f"   Wave data: {(~combined_df['sig_wave_height_m'].isna()).sum():,} / {len(combined_df):,} ({(~combined_df['sig_wave_height_m'].isna()).sum()/len(combined_df)*100:.1f}%)")
    print(f"   Wind speed: {(~combined_df['wind_speed_100m_ms'].isna()).sum():,} / {len(combined_df):,} ({(~combined_df['wind_speed_100m_ms'].isna()).sum()/len(combined_df)*100:.1f}%)")
    print(f"   Temperature: {(~combined_df['temperature_2m_c'].isna()).sum():,} / {len(combined_df):,} ({(~combined_df['temperature_2m_c'].isna()).sum()/len(combined_df)*100:.1f}%)")
    print(f"   Humidity: {(~combined_df['humidity_pct'].isna()).sum():,} / {len(combined_df):,} ({(~combined_df['humidity_pct'].isna()).sum()/len(combined_df)*100:.1f}%)")
    
    # ========================================================================
    # 3. Correlation Analysis by Farm
    # ========================================================================
    print("\n" + "="*80)
    print("📊 Step 3: Calculating correlations by farm...")
    print("-" * 80)
    
    correlation_results = []
    
    for farm in combined_df['farm_name'].unique():
        farm_data = combined_df[combined_df['farm_name'] == farm].copy()
        
        if len(farm_data) < 100:
            continue
        
        # Pearson correlations
        corrs = {
            'farm_name': farm,
            'capacity_mw': farm_data['capacity_mw'].iloc[0],
            'observations': len(farm_data),
            'corr_wave_cf': farm_data['sig_wave_height_m'].corr(farm_data['capacity_factor_pct']),
            'avg_wave_height_m': farm_data['sig_wave_height_m'].mean(),
            'avg_capacity_factor_pct': farm_data['capacity_factor_pct'].mean()
        }
        
        # Weather correlations
        if farm_data['wind_speed_100m_ms'].notna().sum() > 50:
            corrs['corr_wind_cf'] = farm_data['wind_speed_100m_ms'].corr(farm_data['capacity_factor_pct'])
            corrs['avg_wind_speed_ms'] = farm_data['wind_speed_100m_ms'].mean()
        
        if farm_data['temperature_2m_c'].notna().sum() > 50:
            corrs['corr_temp_cf'] = farm_data['temperature_2m_c'].corr(farm_data['capacity_factor_pct'])
            corrs['avg_temperature_c'] = farm_data['temperature_2m_c'].mean()
        
        if farm_data['humidity_pct'].notna().sum() > 50:
            corrs['corr_humidity_cf'] = farm_data['humidity_pct'].corr(farm_data['capacity_factor_pct'])
            corrs['avg_humidity_pct'] = farm_data['humidity_pct'].mean()
        
        correlation_results.append(corrs)
    
    corr_df = pd.DataFrame(correlation_results).sort_values('corr_wave_cf')
    
    print("\n🔍 CORRELATION RESULTS (Sorted by Wave-CF Correlation):")
    print("-" * 80)
    for _, row in corr_df.iterrows():
        print(f"\n{row['farm_name']} ({row['capacity_mw']:.0f} MW)")
        print(f"  Observations: {row['observations']:,} hours")
        print(f"  Wave ↔ CF:        {row['corr_wave_cf']:+.3f} (Avg: {row['avg_wave_height_m']:.2f}m)")
        if 'corr_wind_cf' in row and pd.notna(row['corr_wind_cf']):
            print(f"  Wind Speed ↔ CF:  {row['corr_wind_cf']:+.3f} (Avg: {row['avg_wind_speed_ms']:.1f} m/s)")
        if 'corr_temp_cf' in row and pd.notna(row['corr_temp_cf']):
            print(f"  Temperature ↔ CF: {row['corr_temp_cf']:+.3f} (Avg: {row['avg_temperature_c']:.1f}°C)")
        if 'corr_humidity_cf' in row and pd.notna(row['corr_humidity_cf']):
            print(f"  Humidity ↔ CF:    {row['corr_humidity_cf']:+.3f} (Avg: {row['avg_humidity_pct']:.1f}%)")
        print(f"  Avg Capacity Factor: {row['avg_capacity_factor_pct']:.1f}%")
    
    # ========================================================================
    # 4. Weather-Induced Curtailment Analysis
    # ========================================================================
    print("\n" + "="*80)
    print("📊 Step 4: Weather-induced curtailment events...")
    print("-" * 80)
    
    curtailment_by_reason = combined_df[combined_df['curtailment_reason'] != 'Normal Operation'].groupby('curtailment_reason').agg({
        'hour': 'count',
        'capacity_factor_pct': 'mean',
        'total_generation_mw': 'mean'
    }).sort_values('hour', ascending=False)
    
    if len(curtailment_by_reason) > 0:
        print("\n🌦️  CURTAILMENT BY WEATHER REASON:")
        print(f"{'Reason':<20} {'Hours':>10} {'Avg CF':>10} {'Avg Gen (MW)':>15}")
        print("-" * 60)
        for reason, row in curtailment_by_reason.iterrows():
            pct_of_total = row['hour'] / len(combined_df) * 100
            print(f"{reason:<20} {row['hour']:>10,} {row['capacity_factor_pct']:>9.1f}% {row['total_generation_mw']:>14.1f} ({pct_of_total:.2f}%)")
    
    # ========================================================================
    # 5. Extreme Weather Analysis
    # ========================================================================
    print("\n" + "="*80)
    print("📊 Step 5: Extreme weather conditions...")
    print("-" * 80)
    
    extreme_events = []
    
    # Icing
    if combined_df['temperature_2m_c'].notna().sum() > 0:
        icing = combined_df[combined_df['temperature_2m_c'] < 0]
        if len(icing) > 0:
            extreme_events.append({
                'condition': 'Icing Risk (Temp < 0°C)',
                'hours': len(icing),
                'avg_cf': icing['capacity_factor_pct'].mean()
            })
    
    # Storm
    if combined_df['wind_speed_100m_ms'].notna().sum() > 0:
        storm = combined_df[combined_df['wind_speed_100m_ms'] > 25]
        if len(storm) > 0:
            extreme_events.append({
                'condition': 'Storm (Wind > 25 m/s)',
                'hours': len(storm),
                'avg_cf': storm['capacity_factor_pct'].mean()
            })
    
    # High waves
    high_waves = combined_df[combined_df['sig_wave_height_m'] >= 4.0]
    if len(high_waves) > 0:
        extreme_events.append({
            'condition': 'Rough Seas (Waves ≥ 4m)',
            'hours': len(high_waves),
            'avg_cf': high_waves['capacity_factor_pct'].mean()
        })
    
    # Combined extreme
    if combined_df['temperature_2m_c'].notna().sum() > 0:
        combined_extreme = combined_df[
            (combined_df['sig_wave_height_m'] >= 4.0) & 
            (combined_df['temperature_2m_c'] < 2.0)
        ]
        if len(combined_extreme) > 0:
            extreme_events.append({
                'condition': 'High Waves + Cold',
                'hours': len(combined_extreme),
                'avg_cf': combined_extreme['capacity_factor_pct'].mean()
            })
    
    if extreme_events:
        print("\n⚠️  EXTREME WEATHER CONDITIONS:")
        print(f"{'Condition':<30} {'Hours':>10} {'Avg CF':>10}")
        print("-" * 55)
        for event in extreme_events:
            pct = event['hours'] / len(combined_df) * 100
            print(f"{event['condition']:<30} {event['hours']:>10,} {event['avg_cf']:>9.1f}% ({pct:.2f}%)")
    
    # ========================================================================
    # 6. Save Results
    # ========================================================================
    print("\n" + "="*80)
    print("💾 Saving results...")
    
    combined_df.to_csv('wave_weather_generation_combined.csv', index=False)
    corr_df.to_csv('weather_generation_correlations.csv', index=False)
    
    print("✅ Saved:")
    print("   - wave_weather_generation_combined.csv")
    print("   - weather_generation_correlations.csv")
    
    # ========================================================================
    # 7. Summary
    # ========================================================================
    print("\n" + "="*80)
    print("🎯 KEY FINDINGS")
    print("="*80)
    
    print(f"\n📊 Dataset:")
    print(f"  Total observations: {len(combined_df):,} hours")
    print(f"  Farms: {combined_df['farm_name'].nunique()}")
    print(f"  Date range: {combined_df['hour'].min().date()} to {combined_df['hour'].max().date()}")
    
    print(f"\n🔗 Average Correlations with Capacity Factor:")
    print(f"  Wave Height: {corr_df['corr_wave_cf'].mean():+.3f}")
    if 'corr_wind_cf' in corr_df.columns:
        print(f"  Wind Speed: {corr_df['corr_wind_cf'].mean():+.3f}")
    if 'corr_temp_cf' in corr_df.columns:
        print(f"  Temperature: {corr_df['corr_temp_cf'].mean():+.3f}")
    if 'corr_humidity_cf' in corr_df.columns:
        print(f"  Humidity: {corr_df['corr_humidity_cf'].mean():+.3f}")
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
