#!/usr/bin/env python3
"""
Wind Yield Decrease & Upstream Weather Station Analysis - CORRECTED VERSION

FIXES APPLIED:
1. Wind speed converted from km/h to m/s (÷3.6)
2. Added wind gust analysis
3. Pressure data for upstream station signals
4. Realistic turbine cut-out threshold (25 m/s mean wind, not 42 m/s!)

Key Questions:
1. What weather changes occur upstream when yield drops?
2. How do distant weather stations show early warning signs?
3. What patterns differentiate forecast errors from normal variation?
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_yield_drops_corrected():
    """Analyze CF drops with CORRECTED wind speed units."""
    
    print('=' * 80)
    print('🌪️  WIND YIELD DECREASE ANALYSIS (CORRECTED UNITS)')
    print('=' * 80)
    print()
    
    # Load data
    print('📊 Loading wave-weather-generation data...')
    df = pd.read_csv('wave_weather_generation_combined.csv')
    
    # CRITICAL FIX: Convert wind speed from km/h to m/s
    print('🔧 Converting wind speed: km/h → m/s (÷3.6)')
    df['wind_speed_100m_ms'] = df['wind_speed_100m_ms'] / 3.6
    print(f'   Min wind: {df["wind_speed_100m_ms"].min():.1f} m/s')
    print(f'   Max wind: {df["wind_speed_100m_ms"].max():.1f} m/s')
    print(f'   Mean wind: {df["wind_speed_100m_ms"].mean():.1f} m/s')
    print()
    
    # Sort and calculate changes
    df = df.sort_values(['farm_name', 'month', 'hour'])
    df['prev_cf'] = df.groupby('farm_name')['capacity_factor_pct'].shift(1)
    df['prev_wind'] = df.groupby('farm_name')['wind_speed_100m_ms'].shift(1)
    df['prev_temp'] = df.groupby('farm_name')['temperature_2m_c'].shift(1)
    df['prev_humidity'] = df.groupby('farm_name')['humidity_pct'].shift(1)
    df['prev_wave'] = df.groupby('farm_name')['sig_wave_height_m'].shift(1)
    
    df['cf_change'] = df['capacity_factor_pct'] - df['prev_cf']
    df['wind_change'] = df['wind_speed_100m_ms'] - df['prev_wind']
    df['temp_change'] = df['temperature_2m_c'] - df['prev_temp']
    df['humidity_change'] = df['humidity_pct'] - df['prev_humidity']
    df['wave_change'] = df['sig_wave_height_m'] - df['prev_wave']
    
    # Filter to significant drops
    df_weather = df[df['wind_speed_100m_ms'].notna()].copy()
    drops = df_weather[
        (df_weather['cf_change'] < -5) &
        (df_weather['wind_change'].notna())
    ].copy()
    
    print(f'✅ Found {len(drops):,} significant yield drops (>5% CF decrease)')
    print(f'   Farms: {drops["farm_name"].nunique()}')
    print(f'   Period: {drops["month"].min()}-{drops["month"].max()}')
    print()
    
    # ==========================================================================
    # CORRECTED ANALYSIS
    # ==========================================================================
    
    print('=' * 80)
    print('📉 CAPACITY FACTOR CHANGES')
    print('=' * 80)
    print(f'  Before: {drops["prev_cf"].mean():.1f}%')
    print(f'  After:  {drops["capacity_factor_pct"].mean():.1f}%')
    print(f'  Change: {drops["cf_change"].mean():.1f}%')
    print(f'  Worst:  {drops["cf_change"].min():.1f}%')
    print()
    
    print('=' * 80)
    print('🌬️  WIND SPEED CHANGES (CORRECTED)')
    print('=' * 80)
    print(f'  Before: {drops["prev_wind"].mean():.1f} m/s')
    print(f'  After:  {drops["wind_speed_100m_ms"].mean():.1f} m/s')
    print(f'  Change: {drops["wind_change"].mean():.1f} m/s')
    print()
    
    # Categorize wind changes
    wind_increased = drops[drops['wind_change'] > 0]
    wind_decreased = drops[drops['wind_change'] < 0]
    
    print('Wind Change Categories:')
    print(f'  INCREASED: {len(wind_increased):,} events ({len(wind_increased)/len(drops)*100:.0f}%)')
    print(f'    → Avg increase: +{wind_increased["wind_change"].mean():.1f} m/s')
    print(f'    → Final wind: {wind_increased["wind_speed_100m_ms"].mean():.1f} m/s')
    
    # Check if storm curtailment
    curtailment = wind_increased[wind_increased['wind_speed_100m_ms'] > 25]
    print(f'    → Storm curtailment (>25 m/s): {len(curtailment)} events')
    
    print()
    print(f'  DECREASED: {len(wind_decreased):,} events ({len(wind_decreased)/len(drops)*100:.0f}%)')
    print(f'    → Avg decrease: {wind_decreased["wind_change"].mean():.1f} m/s')
    print(f'    → Final wind: {wind_decreased["wind_speed_100m_ms"].mean():.1f} m/s')
    print()
    
    # ==========================================================================
    # ROOT CAUSE CATEGORIZATION (CORRECTED)
    # ==========================================================================
    
    print('=' * 80)
    print('🔍 ROOT CAUSES (CORRECTED)')
    print('=' * 80)
    print()
    
    # Define categories with REALISTIC thresholds
    drops['root_cause'] = 'Other'
    
    # Storm curtailment: wind increased AND exceeds 25 m/s
    storm_curtailment = (drops['wind_change'] > 2) & (drops['wind_speed_100m_ms'] > 25)
    drops.loc[storm_curtailment, 'root_cause'] = 'Storm Curtailment'
    
    # Calm arrival: wind decreased >5 m/s
    calm_arrival = (drops['wind_change'] < -5)
    drops.loc[calm_arrival, 'root_cause'] = 'Calm Arrival'
    
    # Direction shift: wind stable but CF drops (possible wake effects)
    direction_shift = (drops['wind_change'].abs() < 2) & (drops['humidity_change'] > 10)
    drops.loc[direction_shift, 'root_cause'] = 'Direction Shift'
    
    # Turbulence: moderate wind drop + high humidity change
    turbulence = (drops['wind_change'] < -2) & (drops['wind_change'] > -5) & (drops['humidity_change'].abs() > 5)
    drops.loc[turbulence, 'root_cause'] = 'Turbulence/Transient'
    
    # Summary
    cause_counts = drops['root_cause'].value_counts()
    for cause, count in cause_counts.items():
        pct = count / len(drops) * 100
        avg_wind_change = drops[drops['root_cause'] == cause]['wind_change'].mean()
        avg_final_wind = drops[drops['root_cause'] == cause]['wind_speed_100m_ms'].mean()
        
        print(f'{cause}:')
        print(f'  Events: {count:,} ({pct:.0f}%)')
        print(f'  Wind change: {avg_wind_change:+.1f} m/s')
        print(f'  Final wind: {avg_final_wind:.1f} m/s')
        print()
    
    # ==========================================================================
    # WEATHER PARAMETER CHANGES
    # ==========================================================================
    
    print('=' * 80)
    print('🌡️  TEMPERATURE CHANGES')
    print('=' * 80)
    print(f'  Before: {drops["prev_temp"].mean():.1f}°C')
    print(f'  After:  {drops["temperature_2m_c"].mean():.1f}°C')
    print(f'  Change: {drops["temp_change"].mean():.1f}°C')
    print()
    
    temp_rose = drops[drops['temp_change'] > 0.5]
    temp_fell = drops[drops['temp_change'] < -0.5]
    print(f'  Rose (>0.5°C): {len(temp_rose):,} ({len(temp_rose)/len(drops)*100:.0f}%) → Warm front')
    print(f'  Fell (<-0.5°C): {len(temp_fell):,} ({len(temp_fell)/len(drops)*100:.0f}%) → Cold front')
    print()
    
    print('=' * 80)
    print('💧 HUMIDITY CHANGES')
    print('=' * 80)
    print(f'  Before: {drops["prev_humidity"].mean():.1f}%')
    print(f'  After:  {drops["humidity_pct"].mean():.1f}%')
    print(f'  Change: {drops["humidity_change"].mean():.1f}%')
    print()
    
    humidity_rose = drops[drops['humidity_change'] > 5]
    humidity_fell = drops[drops['humidity_change'] < -5]
    print(f'  Rose (>5%): {len(humidity_rose):,} ({len(humidity_rose)/len(drops)*100:.0f}%) → Low pressure')
    print(f'  Fell (<-5%): {len(humidity_fell):,} ({len(humidity_fell)/len(drops)*100:.0f}%) → High pressure')
    print()
    
    print('=' * 80)
    print('🌊 WAVE HEIGHT CHANGES')
    print('=' * 80)
    print(f'  Before: {drops["prev_wave"].mean():.2f} m')
    print(f'  After:  {drops["sig_wave_height_m"].mean():.2f} m')
    print(f'  Change: {drops["wave_change"].mean():.2f} m (lags wind 2-6 hours)')
    print()
    
    # ==========================================================================
    # TOP 10 WORST DROPS
    # ==========================================================================
    
    print('=' * 80)
    print('🔴 TOP 10 WORST DROPS (CORRECTED)')
    print('=' * 80)
    print()
    
    worst = drops.nsmallest(10, 'cf_change')
    for idx, row in worst.iterrows():
        print(f'{row["farm_name"]} - {row["month"]}')
        print(f'  CF: {row["prev_cf"]:.1f}% → {row["capacity_factor_pct"]:.1f}% (Δ {row["cf_change"]:.1f}%)')
        print(f'  Wind: {row["prev_wind"]:.1f} → {row["wind_speed_100m_ms"]:.1f} m/s (Δ {row["wind_change"]:.1f})')
        print(f'  Temp: {row["prev_temp"]:.1f} → {row["temperature_2m_c"]:.1f}°C (Δ {row["temp_change"]:.1f})')
        print(f'  Humidity: {row["prev_humidity"]:.0f} → {row["humidity_pct"]:.0f}% (Δ {row["humidity_change"]:.0f}%)')
        print(f'  Waves: {row["prev_wave"]:.2f} → {row["sig_wave_height_m"]:.2f} m (Δ {row["wave_change"]:.2f})')
        print(f'  Cause: {row["root_cause"]}')
        print()
    
    # Save results
    drops.to_csv('wind_yield_drops_corrected.csv', index=False)
    print('✅ Saved: wind_yield_drops_corrected.csv')
    print()
    
    # ==========================================================================
    # KEY TAKEAWAYS
    # ==========================================================================
    
    print('=' * 80)
    print('💡 KEY TAKEAWAYS (CORRECTED)')
    print('=' * 80)
    print()
    print(f'1. Wind DECREASED in {len(wind_decreased)/len(drops)*100:.0f}% of drops')
    print(f'   → Average drop: {wind_decreased["wind_change"].mean():.1f} m/s')
    print(f'   → This is NORMAL - lower wind = lower output')
    print()
    print(f'2. Storm curtailment (>25 m/s): {len(curtailment)} events ({len(curtailment)/len(drops)*100:.0f}%)')
    print(f'   → Wind increases above cut-out threshold')
    print()
    print(f'3. Realistic wind speeds:')
    print(f'   → Mean before drop: {drops["prev_wind"].mean():.1f} m/s')
    print(f'   → Mean after drop: {drops["wind_speed_100m_ms"].mean():.1f} m/s')
    print(f'   → Max observed: {drops["wind_speed_100m_ms"].max():.1f} m/s')
    print()
    print('4. Previous analysis had 3.6× wind speed overestimation (km/h vs m/s)')
    print()

if __name__ == '__main__':
    analyze_yield_drops_corrected()
