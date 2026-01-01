#!/usr/bin/env python3
"""
Wave Height vs Generation Correlation Analysis
Identifies when high waves correlate with reduced wind turbine output
Combines CMEMS wave data with BMRS generation data (B1610)

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
    print("🌊⚡ WAVE HEIGHT vs GENERATION CORRELATION ANALYSIS")
    print("="*80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # ========================================================================
    # 1. Get Wind Farms with Both Wave and Generation Data
    # ========================================================================
    print("\n📊 Step 1: Identifying wind farms with complete data...")
    
    query_farms = f"""
    WITH wind_farms_with_data AS (
      SELECT DISTINCT
        wf.farm_name,
        SUM(wf.capacity_mw) as total_capacity_mw,
        COUNT(DISTINCT wf.bm_unit_id) as bmu_count
      FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu` wf
      INNER JOIN `{PROJECT_ID}.{DATASET}.bmrs_pn` gen
        ON wf.bm_unit_id = gen.bmUnit
      WHERE gen.settlementDate >= '2024-01-01'
        AND gen.levelTo > 0
      GROUP BY wf.farm_name
      HAVING COUNT(DISTINCT DATE(gen.settlementDate)) > 30
    )
    SELECT * FROM wind_farms_with_data
    ORDER BY total_capacity_mw DESC
    LIMIT 20
    """
    
    farms_df = client.query(query_farms).to_dataframe()
    print(f"✅ Found {len(farms_df)} wind farms with generation data")
    print(f"   Top farms: {', '.join(farms_df['farm_name'].head(5).tolist())}")
    
    # ========================================================================
    # 2. Combined Wave + Generation Analysis (2024-2025)
    # ========================================================================
    print("\n📊 Step 2: Fetching combined wave and generation data...")
    
    query_combined = f"""
    WITH hourly_generation AS (
      -- Aggregate PN (Physical Notifications) to hourly
      SELECT 
        bmUnit,
        TIMESTAMP_TRUNC(settlementDate, HOUR) as hour,
        AVG(levelTo) as avg_generation_mw,
        MAX(levelTo) as max_generation_mw,
        MIN(levelTo) as min_generation_mw,
        COUNT(*) as periods
      FROM `{PROJECT_ID}.{DATASET}.bmrs_pn`
      WHERE settlementDate >= '2024-01-01'
        AND settlementDate < '2026-01-01'
        AND levelTo >= 0  -- Valid level only
      GROUP BY bmUnit, hour
    ),
    
    wave_generation_combined AS (
      SELECT
        wf.name as farm_name,
        wf.bm_unit_id,
        wf.capacity_mw,
        wf.latitude as farm_lat,
        wf.longitude as farm_lon,
        
        -- Time
        TIMESTAMP_TRUNC(w.time, HOUR) as hour,
        EXTRACT(MONTH FROM w.time) as month,
        EXTRACT(HOUR FROM w.time) as hour_of_day,
        
        -- Wave metrics (nearest grid point)
        AVG(w.VHM0) as sig_wave_height_m,
        AVG(w.VMDR) as wave_direction_deg,
        AVG(w.VTPK) as peak_wave_period_s,
        AVG(w.VHM0_WW) as wind_wave_height_m,
        AVG(w.VHM0_SW1) as swell_wave_height_m,
        
        -- Weather metrics from ERA5 (ADDED)
        AVG(era.wind_speed_100m_ms) as wind_speed_100m_ms,
        AVG(era.temperature_2m_c) as temperature_2m_c,
        AVG(era.relative_humidity_2m_pct) as humidity_pct,
        AVG(era.precipitation_mm) as precipitation_mm,
        AVG(era.pressure_msl_hpa) as pressure_hpa,
        
        -- Generation metrics
        gen.avg_generation_mw,
        gen.max_generation_mw,
        gen.min_generation_mw,
        
        -- Capacity factor
        SAFE_DIVIDE(gen.avg_generation_mw, wf.capacity_mw) * 100 as capacity_factor_pct,
        
        -- Distance to wave grid point
        SQRT(
          POW((w.latitude - wf.latitude) * 111.0, 2) + 
          POW((w.longitude - wf.longitude) * 111.0 * COS(wf.latitude * 3.14159/180), 2)
        ) as distance_km
        
      FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms` wf
      
      -- Join to wave data (nearest grid point within 50km)
      INNER JOIN `{PROJECT_ID}.{DATASET}.cmems_waves_uk_grid` w
        ON SQRT(
          POW((w.latitude - wf.latitude) * 111.0, 2) + 
          POW((w.longitude - wf.longitude) * 111.0 * COS(wf.latitude * 3.14159/180), 2)
        ) < 50
        AND w.time >= '2024-01-01'
        AND w.time < '2026-01-01'
      
      -- Join to ERA5 weather data (ADDED)
      LEFT JOIN `{PROJECT_ID}.{DATASET}.era5_turbine_hourly` era
        ON wf.name = era.farm_name
        AND TIMESTAMP_TRUNC(w.time, HOUR) = TIMESTAMP(era.time)
      
      -- Join to generation data
      INNER JOIN hourly_generation gen
        ON farms_df['bm_unit_id'].iloc[0] = gen.bmUnit
        AND TIMESTAMP_TRUNC(w.time, HOUR) = gen.hour
      
      WHERE wf.name IN ({','.join([f"'{name}'" for name in farms_df['farm_name'].head(10)])})
      
      GROUP BY 
        farm_name, capacity_mw, farm_lat, farm_lon,
        hour, month, hour_of_day,
        gen.avg_generation_mw, gen.max_generation_mw, gen.min_generation_mw
    )
    
    SELECT 
      farm_name,
      bm_unit_id,
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
      avg_generation_mw,
      capacity_factor_pct,
      distance_km,
      
      -- Wave severity categories
      CASE 
        WHEN sig_wave_height_m < 2.0 THEN 'Calm'
        WHEN sig_wave_height_m < 4.0 THEN 'Moderate'
        WHEN sig_wave_height_m < 6.0 THEN 'Rough'
        ELSE 'Very Rough'
      END as sea_state,
      
      -- Generation performance categories
      CASE
        WHEN capacity_factor_pct < 20 THEN 'Low Output'
        WHEN capacity_factor_pct < 50 THEN 'Medium Output'
        WHEN capacity_factor_pct < 80 THEN 'High Output'
        ELSE 'Full Output'
      END as generation_category,
      
      -- Weather-induced curtailment categories (ADDED)
      CASE
        WHEN sig_wave_height_m >= 4.0 AND capacity_factor_pct < 30 THEN 'High Waves'
        WHEN temperature_2m_c < 0 AND capacity_factor_pct < 30 THEN 'Icing Risk'
        WHEN precipitation_mm > 5 AND capacity_factor_pct < 30 THEN 'Heavy Rain'
        WHEN wind_speed_100m_ms > 25 AND capacity_factor_pct < 20 THEN 'Storm Shutdown'
        WHEN wind_speed_100m_ms < 5 AND capacity_factor_pct < 20 THEN 'Low Wind'
        ELSE 'Normal Operation'
      END as curtailment_reason
      
    FROM wave_generation_combined
    WHERE sig_wave_height_m IS NOT NULL
      AND avg_generation_mw IS NOT NULL
      AND distance_km < 30  -- Close proximity only
    ORDER BY farm_name, hour
    """
    
    print("   ⏳ Running BigQuery (this may take 30-60 seconds)...")
    combined_df = client.query(query_combined).to_dataframe()
    print(f"✅ Retrieved {len(combined_df):,} hourly observations")
    print(f"   Date range: {combined_df['hour'].min()} to {combined_df['hour'].max()}")
    print(f"   Farms analyzed: {combined_df['farm_name'].nunique()}")
    
    # ========================================================================
    # 3. Correlation Analysis by Farm
    # ========================================================================
    print("\n📊 Step 3: Calculating correlations by farm...")
    print("-" * 80)
    
    correlation_results = []
    
    for farm in combined_df['farm_name'].unique():
        farm_data = combined_df[combined_df['farm_name'] == farm].copy()
        
        if len(farm_data) < 100:
            continue
        
        # Pearson correlation - waves
        corr_wave_gen = farm_data['sig_wave_height_m'].corr(farm_data['avg_generation_mw'])
        corr_wave_cf = farm_data['sig_wave_height_m'].corr(farm_data['capacity_factor_pct'])
        corr_windwave_gen = farm_data['wind_wave_height_m'].corr(farm_data['avg_generation_mw'])
        
        # Pearson correlation - weather (ADDED)
        corr_wind_cf = farm_data['wind_speed_100m_ms'].corr(farm_data['capacity_factor_pct']) if 'wind_speed_100m_ms' in farm_data.columns else None
        corr_temp_cf = farm_data['temperature_2m_c'].corr(farm_data['capacity_factor_pct']) if 'temperature_2m_c' in farm_data.columns else None
        corr_humidity_cf = farm_data['humidity_pct'].corr(farm_data['capacity_factor_pct']) if 'humidity_pct' in farm_data.columns else None
        
        # Average metrics
        avg_wave = farm_data['sig_wave_height_m'].mean()
        avg_cf = farm_data['capacity_factor_pct'].mean()
        avg_wind = farm_data['wind_speed_100m_ms'].mean() if 'wind_speed_100m_ms' in farm_data.columns else None
        avg_temp = farm_data['temperature_2m_c'].mean() if 'temperature_2m_c' in farm_data.columns else None
        avg_humidity = farm_data['humidity_pct'].mean() if 'humidity_pct' in farm_data.columns else None
        capacity = farm_data['capacity_mw'].iloc[0]
        
        correlation_results.append({
            'farm_name': farm,
            'capacity_mw': capacity,
            'observations': len(farm_data),
            'corr_wave_generation': corr_wave_gen,
            'corr_wave_capacity_factor': corr_wave_cf,
            'corr_windwave_generation': corr_windwave_gen,
            'corr_wind_capacity_factor': corr_wind_cf,
            'corr_temp_capacity_factor': corr_temp_cf,
            'corr_humidity_capacity_factor': corr_humidity_cf,
            'avg_wave_height_m': avg_wave,
            'avg_capacity_factor_pct': avg_cf,
            'avg_wind_speed_ms': avg_wind,
            'avg_temperature_c': avg_temp,
            'avg_humidity_pct': avg_humidity
        })
    
    corr_df = pd.DataFrame(correlation_results).sort_values('corr_wave_capacity_factor')
    
    print("\n🔍 CORRELATION RESULTS (Sorted by Wave-CF Correlation):")
    print("-" * 80)
    for _, row in corr_df.iterrows():
        print(f"\n{row['farm_name']} ({row['capacity_mw']:.0f} MW)")
        print(f"  Observations: {row['observations']:,} hours")
        print(f"  Wave ↔ Generation:      {row['corr_wave_generation']:+.3f}")
        print(f"  Wave ↔ Capacity Factor: {row['corr_wave_capacity_factor']:+.3f}")
        print(f"  Wind-Wave ↔ Generation: {row['corr_windwave_generation']:+.3f}")
        
        # Weather correlations (ADDED)
        if row['corr_wind_capacity_factor'] is not None:
            print(f"  Wind Speed ↔ CF:        {row['corr_wind_capacity_factor']:+.3f}")
        if row['corr_temp_capacity_factor'] is not None:
            print(f"  Temperature ↔ CF:       {row['corr_temp_capacity_factor']:+.3f}")
        if row['corr_humidity_capacity_factor'] is not None:
            print(f"  Humidity ↔ CF:          {row['corr_humidity_capacity_factor']:+.3f}")
        
        print(f"  Avg Wave Height: {row['avg_wave_height_m']:.2f}m")
        print(f"  Avg Capacity Factor: {row['avg_capacity_factor_pct']:.1f}%")
        
        # Weather averages (ADDED)
        if row['avg_wind_speed_ms'] is not None:
            print(f"  Avg Wind Speed: {row['avg_wind_speed_ms']:.1f} m/s")
        if row['avg_temperature_c'] is not None:
            print(f"  Avg Temperature: {row['avg_temperature_c']:.1f}°C")
        if row['avg_humidity_pct'] is not None:
            print(f"  Avg Humidity: {row['avg_humidity_pct']:.1f}%")
    
    # ========================================================================
    # 4. Extreme Wave Impact Analysis
    # ========================================================================
    print("\n" + "="*80)
    print("📊 Step 4: Analyzing generation during extreme wave events...")
    print("-" * 80)
    
    # Compare generation during calm vs rough seas
    calm_data = combined_df[combined_df['sig_wave_height_m'] < 2.0]
    rough_data = combined_df[combined_df['sig_wave_height_m'] >= 4.0]
    very_rough_data = combined_df[combined_df['sig_wave_height_m'] >= 6.0]
    
    print(f"\n🌊 WAVE CONDITION IMPACT:")
    print(f"  Calm Seas (<2m):      {len(calm_data):,} hours, Avg CF: {calm_data['capacity_factor_pct'].mean():.1f}%")
    print(f"  Rough Seas (4-6m):    {len(rough_data):,} hours, Avg CF: {rough_data['capacity_factor_pct'].mean():.1f}%")
    print(f"  Very Rough (>6m):     {len(very_rough_data):,} hours, Avg CF: {very_rough_data['capacity_factor_pct'].mean():.1f}%")
    
    # ========================================================================
    # 5. Identify Curtailment Events (High Waves + Low Generation)
    # ========================================================================
    print("\n" + "="*80)
    print("📊 Step 5: Detecting weather-induced curtailment events...")
    print("-" * 80)
    
    # Curtailment: High waves (>4m) AND low capacity factor (<30%)
    curtailment_events = combined_df[
        (combined_df['sig_wave_height_m'] >= 4.0) & 
        (combined_df['capacity_factor_pct'] < 30.0)
    ].copy()
    
    curtailment_events = curtailment_events.sort_values('sig_wave_height_m', ascending=False)
    
    print(f"\n🚨 POTENTIAL CURTAILMENT EVENTS: {len(curtailment_events):,} hours")
    
    # Curtailment by weather reason (ADDED)
    if 'curtailment_reason' in combined_df.columns:
        curtailment_by_reason = combined_df[combined_df['curtailment_reason'] != 'Normal Operation'].groupby('curtailment_reason').agg({
            'hour': 'count',
            'capacity_factor_pct': 'mean',
            'avg_generation_mw': 'mean'
        }).sort_values('hour', ascending=False)
        
        print("\n🌦️  CURTAILMENT BY WEATHER REASON:")
        print(f"{'Reason':<20} {'Hours':>10} {'Avg CF':>10} {'Avg Gen (MW)':>15}")
        print("-" * 60)
        for reason, row in curtailment_by_reason.iterrows():
            print(f"{reason:<20} {row['hour']:>10,} {row['capacity_factor_pct']:>9.1f}% {row['avg_generation_mw']:>14.1f}")
    
    print("\nTop 20 Extreme Wave + Low Generation Events:")
    print("-" * 80)
    
    for i, (_, event) in enumerate(curtailment_events.head(20).iterrows(), 1):
        weather_info = ""
        if 'wind_speed_100m_ms' in event and pd.notna(event['wind_speed_100m_ms']):
            weather_info = f" | Wind: {event['wind_speed_100m_ms']:.1f} m/s"
        if 'temperature_2m_c' in event and pd.notna(event['temperature_2m_c']):
            weather_info += f" | Temp: {event['temperature_2m_c']:.1f}°C"
        
        print(f"{i:2d}. {event['hour'].strftime('%Y-%m-%d %H:%M')} | {event['farm_name']:30s}")
        print(f"    Wave: {event['sig_wave_height_m']:.2f}m | Generation: {event['avg_generation_mw']:.1f} MW ({event['capacity_factor_pct']:.1f}% CF){weather_info}")
    
    # ========================================================================
    # 6. Monthly Pattern Analysis
    # ========================================================================
    print("\n" + "="*80)
    print("📊 Step 6: Monthly wave-generation patterns...")
    print("-" * 80)
    
    monthly_agg_dict = {
        'sig_wave_height_m': 'mean',
        'capacity_factor_pct': 'mean',
        'avg_generation_mw': 'mean'
    }
    
    # Add weather columns if available (ADDED)
    if 'wind_speed_100m_ms' in combined_df.columns:
        monthly_agg_dict['wind_speed_100m_ms'] = 'mean'
    if 'temperature_2m_c' in combined_df.columns:
        monthly_agg_dict['temperature_2m_c'] = 'mean'
    if 'humidity_pct' in combined_df.columns:
        monthly_agg_dict['humidity_pct'] = 'mean'
    
    monthly_stats = combined_df.groupby('month').agg(monthly_agg_dict).round(2)
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    print("\n📅 MONTHLY AVERAGES:")
    header = f"{'Month':<8} {'Wave Height':>12} {'Capacity Factor':>18} {'Avg Generation':>18}"
    if 'wind_speed_100m_ms' in monthly_stats.columns:
        header += f"{'Wind Speed':>12}"
    if 'temperature_2m_c' in monthly_stats.columns:
        header += f"{'Temperature':>12}"
    print(header)
    print("-" * (60 + (12 * len([c for c in ['wind_speed_100m_ms', 'temperature_2m_c'] if c in monthly_stats.columns]))))
    
    for month, row in monthly_stats.iterrows():
        line = f"{month_names[month-1]:<8} {row['sig_wave_height_m']:>10.2f}m {row['capacity_factor_pct']:>16.1f}% {row['avg_generation_mw']:>15.1f} MW"
        if 'wind_speed_100m_ms' in monthly_stats.columns:
            line += f" {row['wind_speed_100m_ms']:>9.1f} m/s"
        if 'temperature_2m_c' in monthly_stats.columns:
            line += f" {row['temperature_2m_c']:>9.1f}°C"
        print(line)
    
    # ========================================================================
    # 7. Sea State vs Generation Summary
    # ========================================================================
    print("\n" + "="*80)
    print("📊 Step 7: Generation by sea state category...")
    print("-" * 80)
    
    sea_state_stats = combined_df.groupby('sea_state').agg({
        'hour': 'count',
        'capacity_factor_pct': 'mean',
        'avg_generation_mw': 'mean',
        'sig_wave_height_m': 'mean'
    }).round(2)
    
    print("\n🌊 GENERATION BY SEA STATE:")
    print(f"{'Sea State':<15} {'Hours':>10} {'Avg Wave':>12} {'Capacity Factor':>18} {'Avg Generation':>18}")
    print("-" * 80)
    for sea_state, row in sea_state_stats.iterrows():
        print(f"{sea_state:<15} {row['hour']:>10,} {row['sig_wave_height_m']:>10.2f}m {row['capacity_factor_pct']:>16.1f}% {row['avg_generation_mw']:>15.1f} MW")
    
    # ========================================================================
    # 7b. Extreme Weather Event Analysis (ADDED)
    # ========================================================================
    print("\n" + "="*80)
    print("📊 Step 7b: Extreme weather event analysis...")
    print("-" * 80)
    
    extreme_events = []
    
    # Icing conditions
    if 'temperature_2m_c' in combined_df.columns:
        icing_events = combined_df[combined_df['temperature_2m_c'] < 0]
        if len(icing_events) > 0:
            extreme_events.append({
                'condition': 'Icing Risk (Temp < 0°C)',
                'hours': len(icing_events),
                'avg_cf': icing_events['capacity_factor_pct'].mean(),
                'avg_gen': icing_events['avg_generation_mw'].mean()
            })
    
    # Storm conditions
    if 'wind_speed_100m_ms' in combined_df.columns:
        storm_events = combined_df[combined_df['wind_speed_100m_ms'] > 25]
        if len(storm_events) > 0:
            extreme_events.append({
                'condition': 'Storm (Wind > 25 m/s)',
                'hours': len(storm_events),
                'avg_cf': storm_events['capacity_factor_pct'].mean(),
                'avg_gen': storm_events['avg_generation_mw'].mean()
            })
    
    # High precipitation
    if 'precipitation_mm' in combined_df.columns:
        heavy_rain = combined_df[combined_df['precipitation_mm'] > 5]
        if len(heavy_rain) > 0:
            extreme_events.append({
                'condition': 'Heavy Rain (> 5mm)',
                'hours': len(heavy_rain),
                'avg_cf': heavy_rain['capacity_factor_pct'].mean(),
                'avg_gen': heavy_rain['avg_generation_mw'].mean()
            })
    
    # Combined extreme: high waves + low temperature
    if 'temperature_2m_c' in combined_df.columns:
        combined_extreme = combined_df[
            (combined_df['sig_wave_height_m'] >= 4.0) & 
            (combined_df['temperature_2m_c'] < 2.0)
        ]
        if len(combined_extreme) > 0:
            extreme_events.append({
                'condition': 'High Waves + Cold (Wave≥4m, Temp<2°C)',
                'hours': len(combined_extreme),
                'avg_cf': combined_extreme['capacity_factor_pct'].mean(),
                'avg_gen': combined_extreme['avg_generation_mw'].mean()
            })
    
    if extreme_events:
        print("\n⚠️  EXTREME WEATHER CONDITIONS:")
        print(f"{'Condition':<45} {'Hours':>10} {'Avg CF':>10} {'Avg Gen (MW)':>15}")
        print("-" * 85)
        for event in extreme_events:
            print(f"{event['condition']:<45} {event['hours']:>10,} {event['avg_cf']:>9.1f}% {event['avg_gen']:>14.1f}")
    
    # ========================================================================
    # 8. Save Results to CSV
    # ========================================================================
    print("\n" + "="*80)
    print("💾 Saving results to CSV files...")
    
    combined_df.to_csv('wave_generation_combined.csv', index=False)
    corr_df.to_csv('wave_generation_correlations.csv', index=False)
    curtailment_events.to_csv('wave_curtailment_events.csv', index=False)
    
    print("✅ Saved:")
    print("   - wave_generation_combined.csv (full dataset)")
    print("   - wave_generation_correlations.csv (correlation summary)")
    print("   - wave_curtailment_events.csv (high wave + low gen events)")
    
    # ========================================================================
    # 9. Key Findings Summary
    # ========================================================================
    print("\n" + "="*80)
    print("🎯 KEY FINDINGS SUMMARY")
    print("="*80)
    
    avg_corr = corr_df['corr_wave_capacity_factor'].mean()
    negative_corr_farms = (corr_df['corr_wave_capacity_factor'] < 0).sum()
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total observations: {len(combined_df):,} hours")
    print(f"  Wind farms analyzed: {combined_df['farm_name'].nunique()}")
    print(f"  Date range: {combined_df['hour'].min().date()} to {combined_df['hour'].max().date()}")
    print(f"  Average wave-CF correlation: {avg_corr:+.3f}")
    print(f"  Farms with negative correlation: {negative_corr_farms}/{len(corr_df)}")
    
    # Weather correlations (ADDED)
    if 'corr_wind_capacity_factor' in corr_df.columns:
        avg_wind_corr = corr_df['corr_wind_capacity_factor'].mean()
        print(f"  Average wind speed-CF correlation: {avg_wind_corr:+.3f}")
    if 'corr_temp_capacity_factor' in corr_df.columns:
        avg_temp_corr = corr_df['corr_temp_capacity_factor'].mean()
        print(f"  Average temperature-CF correlation: {avg_temp_corr:+.3f}")
    if 'corr_humidity_capacity_factor' in corr_df.columns:
        avg_humidity_corr = corr_df['corr_humidity_capacity_factor'].mean()
        print(f"  Average humidity-CF correlation: {avg_humidity_corr:+.3f}")
    
    print(f"\n🌊 Wave Impact:")
    calm_cf = calm_data['capacity_factor_pct'].mean()
    rough_cf = rough_data['capacity_factor_pct'].mean() if len(rough_data) > 0 else 0
    cf_reduction = calm_cf - rough_cf
    
    print(f"  Calm seas (<2m): {calm_cf:.1f}% average capacity factor")
    print(f"  Rough seas (>4m): {rough_cf:.1f}% average capacity factor")
    print(f"  Reduction: {cf_reduction:.1f} percentage points")
    
    print(f"\n🚨 Curtailment Events:")
    print(f"  High wave + low generation: {len(curtailment_events):,} hours")
    print(f"  Percentage of total: {len(curtailment_events)/len(combined_df)*100:.2f}%")
    
    # Weather-induced curtailment breakdown (ADDED)
    if 'curtailment_reason' in combined_df.columns:
        curtailment_counts = combined_df['curtailment_reason'].value_counts()
        weather_curtailment = curtailment_counts[curtailment_counts.index != 'Normal Operation']
        if len(weather_curtailment) > 0:
            print(f"\n🌦️  Weather-Induced Curtailment Breakdown:")
            for reason, count in weather_curtailment.items():
                pct = count / len(combined_df) * 100
                print(f"  {reason}: {count:,} hours ({pct:.2f}%)")
    
    if len(very_rough_data) > 0:
        print(f"\n⚠️  Very Rough Seas (>6m):")
        print(f"  Occurrences: {len(very_rough_data):,} hours")
        print(f"  Average capacity factor: {very_rough_data['capacity_factor_pct'].mean():.1f}%")
        print(f"  Max wave height: {very_rough_data['sig_wave_height_m'].max():.2f}m")
        
        # Add weather context if available (ADDED)
        if 'wind_speed_100m_ms' in very_rough_data.columns:
            print(f"  Avg wind speed during extreme waves: {very_rough_data['wind_speed_100m_ms'].mean():.1f} m/s")
        if 'temperature_2m_c' in very_rough_data.columns:
            print(f"  Avg temperature during extreme waves: {very_rough_data['temperature_2m_c'].mean():.1f}°C")
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
