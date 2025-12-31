#!/usr/bin/env python3
"""
Wind Drop Alert System

Monitors upstream farms and ERA5 grid points for rapid wind speed drops.
Generates alerts 30min-2h ahead for downstream farms.

Alert levels:
- 🟢 STABLE: Wind speed stable or increasing
- 🟡 DECLINING: Wind speed dropping 10-20% in 1h
- 🔴 RAPID DROP: Wind speed dropping >20% in 1h
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Spatial correlations from previous analysis
UPSTREAM_DOWNSTREAM_PAIRS = [
    ('Moray West', 'Beatrice', 0.966, 0.5),  # (upstream, downstream, correlation, lag_hours)
    ('Sheringham Shoal', 'Dudgeon', 0.964, 0.5),
    ('Beatrice', 'Moray West', 0.959, 0.5),
    ('Triton Knoll', 'Hornsea One', 0.910, 0.5),
    ('Triton Knoll', 'Hornsea Two', 0.911, 0.5),
    ('Race Bank', 'Hornsea One', 0.904, 0.5),
    ('Sheringham Shoal', 'Race Bank', 0.917, 0.5),
    ('Greater Gabbard', 'Galloper', 0.945, 0.5),
]

# ERA5 grid to farm monitoring
ERA5_TO_FARM = {
    'Atlantic_Irish_Sea': ['Walney Extension', 'Walney', 'West of Duddon Sands'],
    'Irish_Sea_Central': ['Barrow', 'Ormonde', 'Burbo Bank'],
    'Atlantic_Hebrides': ['Moray East', 'Moray West', 'Beatrice'],
    'North_Scotland': ['Moray East', 'Moray West'],
    'Central_England': ['Hornsea One', 'Hornsea Two', 'Triton Knoll', 'Race Bank'],
    'Celtic_Sea': ['Dudgeon', 'East Anglia One'],
    'Bristol_Channel': ['Greater Gabbard', 'London Array', 'Rampion', 'Thanet'],
}

def calculate_wind_speed_change(df, window_hours=1):
    """Calculate wind speed change over specified window"""
    df = df.sort_values('time_utc')
    df['wind_speed_prev'] = df['wind_speed_100m'].shift(int(window_hours * 2))  # Assuming 30min intervals
    df['wind_speed_change'] = df['wind_speed_100m'] - df['wind_speed_prev']
    df['wind_speed_change_pct'] = (df['wind_speed_change'] / df['wind_speed_prev']) * 100
    return df

def get_alert_level(change_pct):
    """Determine alert level based on wind speed change"""
    if change_pct <= -20:
        return '🔴 RAPID DROP', 'CRITICAL'
    elif change_pct <= -10:
        return '🟡 DECLINING', 'WARNING'
    else:
        return '🟢 STABLE', 'NORMAL'

def monitor_upstream_farms():
    """Monitor upstream wind farms for speed drops"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get recent wind speed data
    current_time = datetime.now()
    lookback_time = current_time - timedelta(hours=3)
    
    upstream_farms = list(set([pair[0] for pair in UPSTREAM_DOWNSTREAM_PAIRS]))
    
    query = f"""
    SELECT 
        timestamp as time_utc,
        farm_name,
        wind_speed_100m,
        wind_direction_10m
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    WHERE farm_name IN ({','.join([f"'{f}'" for f in upstream_farms])})
        AND timestamp >= TIMESTAMP('{lookback_time}')
        AND timestamp <= TIMESTAMP('{current_time}')
    ORDER BY farm_name, timestamp
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # Calculate changes for each farm
    alerts = []
    
    for farm_name in upstream_farms:
        farm_data = df[df['farm_name'] == farm_name].copy()
        
        if len(farm_data) < 4:  # Need at least 2 hours of data
            continue
        
        farm_data = calculate_wind_speed_change(farm_data, window_hours=1)
        
        latest = farm_data.iloc[-1]
        
        if pd.isna(latest['wind_speed_change_pct']):
            continue
        
        alert_emoji, alert_level = get_alert_level(latest['wind_speed_change_pct'])
        
        # Find downstream farms affected
        downstream_farms = [
            pair[1] for pair in UPSTREAM_DOWNSTREAM_PAIRS 
            if pair[0] == farm_name
        ]
        
        for downstream_farm in downstream_farms:
            # Find lag time
            lag_hours = next(
                pair[3] for pair in UPSTREAM_DOWNSTREAM_PAIRS 
                if pair[0] == farm_name and pair[1] == downstream_farm
            )
            
            impact_time = latest['time_utc'] + timedelta(hours=lag_hours)
            time_to_impact = (impact_time - current_time).total_seconds() / 60  # minutes
            
            alerts.append({
                'upstream_farm': farm_name,
                'downstream_farm': downstream_farm,
                'current_wind_speed': latest['wind_speed_100m'],
                'wind_speed_change_pct': latest['wind_speed_change_pct'],
                'alert_level': alert_level,
                'alert_emoji': alert_emoji,
                'impact_time': impact_time,
                'time_to_impact_min': time_to_impact,
                'lag_hours': lag_hours
            })
    
    return pd.DataFrame(alerts)

def monitor_era5_grids():
    """Monitor ERA5 grid points for wind drops"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    current_time = datetime.now()
    lookback_time = current_time - timedelta(hours=3)
    
    grid_points = list(ERA5_TO_FARM.keys())
    
    query = f"""
    SELECT 
        time_utc,
        grid_point,
        wind_speed_100m
    FROM `{PROJECT_ID}.{DATASET}.era5_wind_upstream`
    WHERE grid_point IN ({','.join([f"'{g}'" for g in grid_points])})
        AND time_utc >= TIMESTAMP('{lookback_time}')
        AND time_utc <= TIMESTAMP('{current_time}')
    ORDER BY grid_point, time_utc
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) == 0:
        return pd.DataFrame()
    
    alerts = []
    
    for grid_point in grid_points:
        grid_data = df[df['grid_point'] == grid_point].copy()
        
        if len(grid_data) < 3:
            continue
        
        grid_data = calculate_wind_speed_change(grid_data, window_hours=1)
        
        latest = grid_data.iloc[-1]
        
        if pd.isna(latest['wind_speed_change_pct']):
            continue
        
        alert_emoji, alert_level = get_alert_level(latest['wind_speed_change_pct'])
        
        affected_farms = ERA5_TO_FARM.get(grid_point, [])
        
        for farm in affected_farms:
            # Typical lag for ERA5 grid points: 2-4 hours
            lag_hours = 2.0
            
            impact_time = latest['time_utc'] + timedelta(hours=lag_hours)
            time_to_impact = (impact_time - current_time).total_seconds() / 60
            
            alerts.append({
                'upstream_source': f"ERA5: {grid_point}",
                'downstream_farm': farm,
                'current_wind_speed': latest['wind_speed_100m'],
                'wind_speed_change_pct': latest['wind_speed_change_pct'],
                'alert_level': alert_level,
                'alert_emoji': alert_emoji,
                'impact_time': impact_time,
                'time_to_impact_min': time_to_impact,
                'lag_hours': lag_hours
            })
    
    return pd.DataFrame(alerts)

print("=" * 80)
print("Wind Drop Alert System")
print("=" * 80)
print()

print(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Monitor upstream farms
print("📊 Monitoring upstream wind farms...")
df_farm_alerts = monitor_upstream_farms()

if len(df_farm_alerts) > 0:
    print(f"   Found {len(df_farm_alerts)} farm-to-farm alerts")
    
    # Show critical alerts only
    critical = df_farm_alerts[df_farm_alerts['alert_level'] == 'CRITICAL']
    warning = df_farm_alerts[df_farm_alerts['alert_level'] == 'WARNING']
    
    if len(critical) > 0:
        print(f"\n🔴 CRITICAL ALERTS ({len(critical)}):")
        for _, alert in critical.iterrows():
            print(f"   {alert['upstream_farm']} → {alert['downstream_farm']}")
            print(f"      Wind drop: {alert['wind_speed_change_pct']:.1f}%")
            print(f"      Impact in: {alert['time_to_impact_min']:.0f} minutes")
            print()
    
    if len(warning) > 0:
        print(f"🟡 WARNING ALERTS ({len(warning)}):")
        for _, alert in warning.head(5).iterrows():
            print(f"   {alert['upstream_farm']} → {alert['downstream_farm']}")
            print(f"      Wind drop: {alert['wind_speed_change_pct']:.1f}%")
            print(f"      Impact in: {alert['time_to_impact_min']:.0f} minutes")
    
    # Save alerts
    df_farm_alerts.to_csv(f'wind_drop_alerts_farms_{datetime.now().strftime("%Y%m%d_%H%M")}.csv', index=False)
    print(f"\n✅ Farm alerts saved")

else:
    print("   🟢 No farm-to-farm alerts")

print()

# Monitor ERA5 grids
print("🌐 Monitoring ERA5 grid points...")
df_era5_alerts = monitor_era5_grids()

if len(df_era5_alerts) > 0:
    print(f"   Found {len(df_era5_alerts)} ERA5 grid alerts")
    
    critical = df_era5_alerts[df_era5_alerts['alert_level'] == 'CRITICAL']
    warning = df_era5_alerts[df_era5_alerts['alert_level'] == 'WARNING']
    
    if len(critical) > 0:
        print(f"\n🔴 CRITICAL ALERTS ({len(critical)}):")
        for _, alert in critical.iterrows():
            print(f"   {alert['upstream_source']} → {alert['downstream_farm']}")
            print(f"      Wind drop: {alert['wind_speed_change_pct']:.1f}%")
            print(f"      Impact in: {alert['time_to_impact_min']:.0f} minutes")
            print()
    
    if len(warning) > 0:
        print(f"🟡 WARNING ALERTS ({len(warning)} total, showing first 5):")
        for _, alert in warning.head(5).iterrows():
            print(f"   {alert['upstream_source']} → {alert['downstream_farm']}")
            print(f"      Wind drop: {alert['wind_speed_change_pct']:.1f}%")
    
    df_era5_alerts.to_csv(f'wind_drop_alerts_era5_{datetime.now().strftime("%Y%m%d_%H%M")}.csv', index=False)
    print(f"\n✅ ERA5 alerts saved")

else:
    print("   🟢 No ERA5 grid alerts")

print()
print("=" * 80)
print("✅ WIND DROP ALERT SYSTEM ACTIVE")
print("=" * 80)
print("Run this script every 15-30 minutes to monitor conditions")
print("Deploy as cron job: */15 * * * * python3 wind_drop_alerts.py")
