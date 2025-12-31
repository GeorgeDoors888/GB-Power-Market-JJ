#!/usr/bin/env python3
"""
Spatial Wind Correlation Analysis
Analyze upstream/downstream wind speed correlations for advance forecasting
Uses actual offshore wind farm locations to find spatial patterns
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from scipy.stats import pearsonr
import math

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Offshore wind farm approximate coordinates (lat, lon)
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
    'Dogger Bank A': (54.7, 1.8),
    'Dogger Bank B': (54.7, 2.0),
    'Triton Knoll': (53.3, 0.5),
    'Race Bank': (53.2, 0.4),
    'Dudgeon': (53.3, 0.8),
    'Sheringham Shoal': (52.9, 1.2),
    'Greater Gabbard': (51.9, 2.0),
    'Galloper': (51.9, 2.1),
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

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance in km using Haversine formula"""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def angle_difference(angle1, angle2):
    """Calculate smallest difference between two angles (0-180)"""
    diff = abs(angle1 - angle2)
    if diff > 180:
        diff = 360 - diff
    return diff

def main():
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("=" * 80)
    print("Spatial Wind Correlation Analysis - Upstream Prediction")
    print("=" * 80)
    
    # Load wind data for 2024 (full year for robust statistics)
    print("\n📊 Loading wind data for 2024...")
    query = f"""
    SELECT 
        farm_name,
        time_utc,
        wind_speed_100m,
        wind_direction_10m
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    WHERE time_utc >= '2024-01-01'
      AND time_utc < '2025-01-01'
      AND wind_speed_100m IS NOT NULL
      AND wind_direction_10m IS NOT NULL
    ORDER BY time_utc
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Loaded {len(df):,} observations from {df['farm_name'].nunique()} farms")
    
    # Convert to wide format (one column per farm)
    print("\n🔄 Pivoting data to wide format...")
    df_wind = df.pivot(index='time_utc', columns='farm_name', values='wind_speed_100m')
    df_dir = df.pivot(index='time_utc', columns='farm_name', values='wind_direction_10m')
    
    print(f"   Time range: {df_wind.index.min()} to {df_wind.index.max()}")
    print(f"   Time steps: {len(df_wind):,}")
    
    # Analyze all farm pairs
    print("\n🔍 Analyzing spatial correlations between farm pairs...")
    print("   Testing time lags: 0.5h, 1.0h, 1.5h, 2.0h, 2.5h, 3.0h, 3.5h, 4.0h")
    print("   Filtering: Wind direction aligned with farm bearing (±30°)")
    
    results = []
    
    farms = [f for f in FARM_COORDS.keys() if f in df_wind.columns]
    print(f"   Farms with data: {len(farms)}")
    
    total_pairs = 0
    
    for i, farm1 in enumerate(farms):
        lat1, lon1 = FARM_COORDS[farm1]
        
        for farm2 in farms:
            if farm1 == farm2:
                continue
            
            total_pairs += 1
            
            lat2, lon2 = FARM_COORDS[farm2]
            distance = calculate_distance(lat1, lon1, lat2, lon2)
            bearing = calculate_bearing(lat1, lon1, lat2, lon2)
            
            # Only consider pairs >30 km apart (avoid local correlations)
            if distance < 30:
                continue
            
            # Test different time lags
            for lag_hours in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
                lag_steps = int(lag_hours * 2)  # 30-min resolution
                
                # Get wind speed at both farms
                wind1 = df_wind[farm1]
                wind2 = df_wind[farm2].shift(-lag_steps)  # Shift farm2 back in time
                
                # Get wind direction at farm1 (upstream)
                wind_dir1 = df_dir[farm1]
                
                # Filter to times when wind direction aligns with bearing (±30°)
                direction_aligned = wind_dir1.apply(
                    lambda d: angle_difference(d, bearing) < 30 if pd.notna(d) else False
                )
                
                # Combine all masks
                valid_mask = (
                    wind1.notna() & 
                    wind2.notna() & 
                    wind_dir1.notna() & 
                    direction_aligned
                )
                
                wind1_valid = wind1[valid_mask]
                wind2_valid = wind2[valid_mask]
                
                # Need at least 50 samples for reliable correlation
                if len(wind1_valid) < 50:
                    continue
                
                # Calculate Pearson correlation
                correlation, p_value = pearsonr(wind1_valid, wind2_valid)
                
                # Calculate expected travel time based on average wind speed
                avg_wind_speed = wind1_valid.mean()  # m/s
                expected_travel_hours = distance * 1000 / (avg_wind_speed * 3600)  # Convert km to m, m/s to hours
                
                results.append({
                    'upstream_farm': farm1,
                    'downstream_farm': farm2,
                    'distance_km': distance,
                    'bearing_degrees': bearing,
                    'lag_hours': lag_hours,
                    'correlation': correlation,
                    'p_value': p_value,
                    'n_samples': len(wind1_valid),
                    'avg_wind_speed_ms': avg_wind_speed,
                    'expected_travel_hours': expected_travel_hours,
                    'lag_vs_expected': abs(lag_hours - expected_travel_hours)
                })
        
        if (i + 1) % 5 == 0:
            print(f"   Processed {i+1}/{len(farms)} upstream farms...")
    
    results_df = pd.DataFrame(results)
    print(f"\n✅ Analyzed {total_pairs:,} farm pairs")
    print(f"   Total pair-lag combinations tested: {len(results_df):,}")
    
    # Filter to significant correlations
    significant = results_df[
        (results_df['p_value'] < 0.01) &
        (results_df['correlation'] > 0.4) &
        (results_df['n_samples'] > 100)
    ].copy()
    
    print(f"   Significant correlations (r > 0.4, p < 0.01, n > 100): {len(significant):,}")
    
    # Sort by correlation strength
    significant = significant.sort_values('correlation', ascending=False)
    
    # Display top 20 spatial correlations
    print("\n" + "=" * 80)
    print("🎯 Top 20 Spatial Wind Correlations (Upstream → Downstream)")
    print("=" * 80)
    print(f"\n{'Upstream Farm':<25} {'→':<2} {'Downstream Farm':<25} {'Dist':>7} {'Lag':>7} {'Corr':>7} {'N':>8}")
    print("-" * 90)
    
    for idx, row in significant.head(20).iterrows():
        print(f"{row['upstream_farm']:<25} → {row['downstream_farm']:<25} "
              f"{row['distance_km']:>6.0f}km {row['lag_hours']:>5.1f}h "
              f"{row['correlation']:>6.3f} {row['n_samples']:>7,.0f}")
    
    # Find optimal lag for each farm pair
    print("\n" + "=" * 80)
    print("📈 Best Correlations by Farm Pair (Optimal Lag)")
    print("=" * 80)
    
    best_pairs = significant.groupby(['upstream_farm', 'downstream_farm']).apply(
        lambda x: x.loc[x['correlation'].idxmax()]
    ).reset_index(drop=True).sort_values('correlation', ascending=False)
    
    print(f"\n{'Upstream':<25} {'→':<2} {'Downstream':<25} {'Dist':>7} {'Best Lag':>9} {'Corr':>7} {'Travel':>9}")
    print("-" * 100)
    
    for idx, row in best_pairs.head(15).iterrows():
        print(f"{row['upstream_farm']:<25} → {row['downstream_farm']:<25} "
              f"{row['distance_km']:>6.0f}km {row['lag_hours']:>7.1f}h "
              f"{row['correlation']:>6.3f} {row['expected_travel_hours']:>7.1f}h")
    
    # Analyze by wind direction patterns
    print("\n" + "=" * 80)
    print("🌬️  Correlation by Geographic Pattern")
    print("=" * 80)
    
    # Classify directions
    def classify_direction(bearing):
        if 315 <= bearing or bearing < 45:
            return "North (315-45°)"
        elif 45 <= bearing < 135:
            return "East (45-135°)"
        elif 135 <= bearing < 225:
            return "South (135-225°)"
        else:
            return "West (225-315°)"
    
    significant['direction_pattern'] = significant['bearing_degrees'].apply(classify_direction)
    
    direction_stats = significant.groupby('direction_pattern').agg({
        'correlation': ['mean', 'max', 'count'],
        'distance_km': 'mean',
        'lag_hours': 'mean'
    }).round(3)
    
    print("\nSpatial patterns by wind direction:")
    print(direction_stats)
    
    # Save full results
    results_df.to_csv('spatial_wind_correlations_full.csv', index=False)
    significant.to_csv('spatial_wind_correlations_significant.csv', index=False)
    best_pairs.to_csv('spatial_wind_correlations_best_pairs.csv', index=False)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print("Files saved:")
    print("  - spatial_wind_correlations_full.csv (all results)")
    print("  - spatial_wind_correlations_significant.csv (r>0.4, p<0.01)")
    print("  - spatial_wind_correlations_best_pairs.csv (optimal lag per pair)")
    
    # Summary statistics
    print("\n📊 Summary Statistics:")
    print(f"   Highest correlation: {significant['correlation'].max():.3f}")
    print(f"   Median correlation: {significant['correlation'].median():.3f}")
    print(f"   Avg optimal lag: {best_pairs['lag_hours'].mean():.1f} hours")
    print(f"   Avg distance: {best_pairs['distance_km'].mean():.0f} km")
    
    # Identify best upstream sensors for each major farm
    major_farms = ['Hornsea One', 'Hornsea Two', 'Seagreen Phase 1', 'Walney Extension', 
                   'Moray East', 'Triton Knoll', 'East Anglia One']
    
    print("\n" + "=" * 80)
    print("🎯 Best Upstream Sensors for Major Farms")
    print("=" * 80)
    
    for farm in major_farms:
        if farm not in df_wind.columns:
            continue
        
        farm_upstream = best_pairs[best_pairs['downstream_farm'] == farm].head(3)
        
        if len(farm_upstream) > 0:
            print(f"\n{farm}:")
            for _, row in farm_upstream.iterrows():
                print(f"   {row['upstream_farm']:<25} "
                      f"(r={row['correlation']:.3f}, lag={row['lag_hours']:.1f}h, "
                      f"dist={row['distance_km']:.0f}km)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
