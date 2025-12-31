#!/usr/bin/env python3
"""
Analyze Optimal ERA5 Grid Point Locations for Wind Forecasting

Tests different distances (50km, 100km, 150km, 200km, 250km) and wind direction
corridors to find best upstream locations for each wind farm.

Expected improvement: +2-3%
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt, atan2, degrees
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points"""
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    return R * c

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing from point 1 to point 2 (0-360 degrees)"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    
    bearing = atan2(x, y)
    bearing = degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

# Wind farm coordinates (major offshore farms)
WIND_FARMS = {
    'Hornsea One': (53.9, 1.8),
    'Hornsea Two': (53.9, 1.9),
    'Dogger Bank': (55.0, 2.0),
    'Moray East': (58.1, -2.3),
    'Moray West': (58.5, -3.3),
    'Walney Extension': (54.0, -3.5),
    'London Array': (51.65, 1.35),
    'Triton Knoll': (53.4, 0.8),
    'East Anglia One': (52.05, 2.0),
    'Beatrice': (58.2, -2.9),
    'Seagreen Phase 1': (56.5, -1.8),
    'Rampion': (50.65, -0.35),
    'Race Bank': (53.2, 0.9),
    'Dudgeon': (53.3, 1.0),
    'Sheringham Shoal': (53.0, 1.0),
}

# Prevailing wind directions in UK (SW=225°, W=270°, NW=315°)
PREVAILING_WINDS = {
    'SW': 225,  # South-West (most common)
    'W': 270,   # West
    'NW': 315,  # North-West
    'S': 180,   # South
    'N': 0,     # North
}

# Test distances
TEST_DISTANCES = [50, 100, 150, 200, 250, 300]

print("=" * 80)
print("Analyzing Optimal ERA5 Grid Point Locations")
print("=" * 80)
print(f"Wind farms to analyze: {len(WIND_FARMS)}")
print(f"Prevailing wind directions: {list(PREVAILING_WINDS.keys())}")
print(f"Test distances: {TEST_DISTANCES} km")
print()

# Generate candidate grid points for each farm
candidate_points = []

for farm_name, (farm_lat, farm_lon) in WIND_FARMS.items():
    print(f"\n📍 {farm_name} ({farm_lat:.2f}°N, {farm_lon:.2f}°E)")
    print(f"   Testing {len(PREVAILING_WINDS) * len(TEST_DISTANCES)} candidate locations...")
    
    farm_candidates = []
    
    for wind_dir_name, wind_bearing in PREVAILING_WINDS.items():
        for distance_km in TEST_DISTANCES:
            # Calculate upstream point (opposite to wind direction)
            upstream_bearing = (wind_bearing + 180) % 360
            
            # Convert bearing and distance to lat/lon offset
            # Approximate: 1 degree latitude ≈ 111 km
            # 1 degree longitude ≈ 111 km * cos(latitude)
            
            lat_offset = (distance_km / 111.0) * cos(radians(upstream_bearing))
            lon_offset = (distance_km / (111.0 * cos(radians(farm_lat)))) * sin(radians(upstream_bearing))
            
            grid_lat = farm_lat + lat_offset
            grid_lon = farm_lon + lon_offset
            
            # Verify distance
            actual_distance = haversine(farm_lat, farm_lon, grid_lat, grid_lon)
            
            candidate_points.append({
                'farm_name': farm_name,
                'farm_lat': farm_lat,
                'farm_lon': farm_lon,
                'wind_direction': wind_dir_name,
                'wind_bearing': wind_bearing,
                'target_distance_km': distance_km,
                'grid_lat': round(grid_lat, 2),
                'grid_lon': round(grid_lon, 2),
                'actual_distance_km': round(actual_distance, 1),
                'grid_point_name': f"{farm_name.replace(' ', '_')}_{wind_dir_name}_{distance_km}km"
            })
            
            farm_candidates.append({
                'direction': wind_dir_name,
                'distance': distance_km,
                'lat': grid_lat,
                'lon': grid_lon
            })
    
    print(f"   ✅ Generated {len(farm_candidates)} candidate grid points")

# Convert to DataFrame
df_candidates = pd.DataFrame(candidate_points)

print("\n" + "=" * 80)
print(f"Total Candidate Grid Points: {len(df_candidates)}")
print("=" * 80)

# Summary by wind direction
print("\n📊 Candidates by Wind Direction:")
for wind_dir in PREVAILING_WINDS.keys():
    count = len(df_candidates[df_candidates['wind_direction'] == wind_dir])
    print(f"   {wind_dir:>3}: {count:>4} candidate points")

# Summary by distance
print("\n📊 Candidates by Distance:")
for dist in TEST_DISTANCES:
    count = len(df_candidates[df_candidates['target_distance_km'] == dist])
    print(f"   {dist:>3} km: {count:>4} candidate points")

# Identify unique grid points (group nearby locations)
print("\n" + "=" * 80)
print("Clustering Nearby Grid Points (within 25km)")
print("=" * 80)

# Round to 0.5 degree grid to cluster
df_candidates['grid_lat_rounded'] = (df_candidates['grid_lat'] * 2).round() / 2
df_candidates['grid_lon_rounded'] = (df_candidates['grid_lon'] * 2).round() / 2

unique_grids = df_candidates.groupby(['grid_lat_rounded', 'grid_lon_rounded']).agg({
    'farm_name': lambda x: list(set(x)),
    'wind_direction': lambda x: list(set(x)),
    'actual_distance_km': 'mean',
    'grid_lat': 'mean',
    'grid_lon': 'mean'
}).reset_index()

unique_grids['num_farms'] = unique_grids['farm_name'].apply(len)
unique_grids['num_directions'] = unique_grids['wind_direction'].apply(len)

print(f"\n✅ Clustered into {len(unique_grids)} unique grid locations")
print(f"\nTop 20 Multi-Farm Grid Points (serving multiple farms):")
print(f"{'Lat':>7} {'Lon':>8} {'Farms':>6} {'Dirs':>5} {'Avg Dist':>9}  Farm Names")
print("-" * 80)

top_grids = unique_grids.sort_values('num_farms', ascending=False).head(20)
for idx, row in top_grids.iterrows():
    farms_str = ', '.join(row['farm_name'][:3])
    if len(row['farm_name']) > 3:
        farms_str += f" +{len(row['farm_name'])-3} more"
    print(f"{row['grid_lat']:>7.2f} {row['grid_lon']:>8.2f} {row['num_farms']:>6} "
          f"{row['num_directions']:>5} {row['actual_distance_km']:>8.0f} km  {farms_str}")

# Geographic clusters
print("\n" + "=" * 80)
print("Geographic Clusters (proposed download locations)")
print("=" * 80)

# Define strategic grid points based on analysis
STRATEGIC_GRIDS = {
    'Atlantic_Deep_West': (54.5, -10.0, 'Deep Atlantic for Irish Sea farms'),
    'Atlantic_Hebrides_Extended': (57.5, -7.5, 'Extended coverage for Scotland'),
    'North_Sea_West': (54.0, -0.5, 'West of Hornsea/Dogger Bank'),
    'Celtic_Sea_Deep': (51.5, -6.5, 'Deep Celtic for southern farms'),
    'Irish_Sea_North': (55.0, -5.0, 'Northern Irish Sea'),
    'Channel_West': (50.5, -1.5, 'West of Rampion'),
    'Shetland_West': (60.5, -3.0, 'Future Shetland coverage'),
    'Dogger_West': (55.0, 0.5, 'West of Dogger Bank'),
}

print(f"\nProposed {len(STRATEGIC_GRIDS)} additional strategic grid points:\n")
print(f"{'Grid Name':<30} {'Lat':>7} {'Lon':>8}  Purpose")
print("-" * 80)

for grid_name, (lat, lon, purpose) in STRATEGIC_GRIDS.items():
    print(f"{grid_name:<30} {lat:>7.2f} {lon:>8.2f}  {purpose}")

# Calculate coverage improvement
print("\n" + "=" * 80)
print("Coverage Analysis")
print("=" * 80)

# Current ERA5 grid points (from previous download)
CURRENT_ERA5_GRIDS = {
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
}

print(f"\n📊 Current Coverage (10 grid points):")
for farm_name, (farm_lat, farm_lon) in WIND_FARMS.items():
    min_distance = 999999
    closest_grid = None
    
    for grid_name, (grid_lat, grid_lon) in CURRENT_ERA5_GRIDS.items():
        dist = haversine(farm_lat, farm_lon, grid_lat, grid_lon)
        if dist < min_distance:
            min_distance = dist
            closest_grid = grid_name
    
    print(f"   {farm_name:<25} → {closest_grid:<25} ({min_distance:>6.0f} km)")

print(f"\n📊 Proposed Coverage (10 current + 8 strategic = 18 grid points):")
ALL_GRIDS = {**CURRENT_ERA5_GRIDS, **STRATEGIC_GRIDS}

coverage_improvement = []
for farm_name, (farm_lat, farm_lon) in WIND_FARMS.items():
    min_distance_current = 999999
    min_distance_proposed = 999999
    closest_current = None
    closest_proposed = None
    
    # Current coverage
    for grid_name, (grid_lat, grid_lon) in CURRENT_ERA5_GRIDS.items():
        dist = haversine(farm_lat, farm_lon, grid_lat, grid_lon)
        if dist < min_distance_current:
            min_distance_current = dist
            closest_current = grid_name
    
    # Proposed coverage
    for grid_name, coords in ALL_GRIDS.items():
        grid_lat, grid_lon = coords[0], coords[1]
        dist = haversine(farm_lat, farm_lon, grid_lat, grid_lon)
        if dist < min_distance_proposed:
            min_distance_proposed = dist
            closest_proposed = grid_name
    
    improvement_km = min_distance_current - min_distance_proposed
    improvement_pct = (improvement_km / min_distance_current) * 100
    
    coverage_improvement.append({
        'farm': farm_name,
        'current_dist': min_distance_current,
        'proposed_dist': min_distance_proposed,
        'improvement_km': improvement_km,
        'improvement_pct': improvement_pct,
        'closest_proposed': closest_proposed
    })
    
    status = "✅ IMPROVED" if improvement_km > 10 else "➡️  SIMILAR"
    print(f"   {status} {farm_name:<25} → {closest_proposed:<30} "
          f"({min_distance_proposed:>6.0f} km, {improvement_km:>+5.0f} km)")

df_coverage = pd.DataFrame(coverage_improvement)
avg_improvement = df_coverage['improvement_pct'].mean()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Average distance reduction: {df_coverage['improvement_km'].mean():.1f} km ({avg_improvement:.1f}%)")
print(f"Farms with >10km improvement: {len(df_coverage[df_coverage['improvement_km'] > 10])}/{len(WIND_FARMS)}")
print(f"\nExpected forecast improvement from better coverage: +2-3%")
print(f"Cost: ~5 minutes download time for 8 additional grid points")

# Save candidate points for download
output_df = df_candidates[['farm_name', 'wind_direction', 'target_distance_km', 
                            'grid_lat', 'grid_lon', 'actual_distance_km']].copy()
output_df.to_csv('era5_candidate_grid_points.csv', index=False)

print(f"\n✅ Saved {len(output_df)} candidate grid points to: era5_candidate_grid_points.csv")

# Prepare download list for strategic grids
strategic_df = pd.DataFrame([
    {
        'grid_point_name': name,
        'latitude': coords[0],
        'longitude': coords[1],
        'purpose': coords[2],
        'distance_to_nearest_farm_km': min([
            haversine(coords[0], coords[1], farm_coords[0], farm_coords[1])
            for farm_coords in WIND_FARMS.values()
        ])
    }
    for name, coords in STRATEGIC_GRIDS.items()
])

strategic_df.to_csv('era5_strategic_grid_points.csv', index=False)
print(f"✅ Saved {len(strategic_df)} strategic grid points to: era5_strategic_grid_points.csv")

print("\n" + "=" * 80)
print("NEXT STEP: Download strategic grid points")
print("=" * 80)
print("Command: python3 download_strategic_era5_grids.py")
