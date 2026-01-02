#!/usr/bin/env python3
"""
Task 5: Build Upstream Station Features

Creates virtual weather stations 50-150km west/southwest of each offshore wind farm
to track upstream signal propagation for event forecasting.

Weather systems in UK move predominantly west → east (prevailing westerlies).
By monitoring pressure/wind/temperature changes 50-150km upstream, we can detect:
- Pressure drops 6-12 hours before storm arrival at farm
- Direction shifts 1-3 hours before frontal passage
- Wind speed changes 0-2 hours before gusts hit farm

Output: era5_upstream_features table for Task 8 lead time calculation
"""

import math
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def calculate_upstream_coordinates(lat: float, lon: float, distance_km: float, bearing_deg: float = 240) -> tuple:
    """
    Calculate upstream station coordinates using great circle distance.
    
    Args:
        lat: Farm latitude (degrees)
        lon: Farm longitude (degrees)
        distance_km: Distance to upstream station (km)
        bearing_deg: Bearing in degrees (240° = WSW, prevailing wind direction)
    
    Returns:
        (upstream_lat, upstream_lon) tuple
    """
    # Earth radius in km
    R = 6371.0
    
    # Convert to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    
    # Angular distance
    angular_dist = distance_km / R
    
    # Calculate upstream coordinates using great circle formula
    upstream_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_dist) +
        math.cos(lat_rad) * math.sin(angular_dist) * math.cos(bearing_rad)
    )
    
    upstream_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_dist) * math.cos(lat_rad),
        math.cos(angular_dist) - math.sin(lat_rad) * math.sin(upstream_lat_rad)
    )
    
    # Convert back to degrees
    upstream_lat = math.degrees(upstream_lat_rad)
    upstream_lon = math.degrees(upstream_lon_rad)
    
    return (upstream_lat, upstream_lon)

def create_upstream_stations_table():
    """Create table of virtual upstream stations for each farm."""
    
    print("=" * 80)
    print("🌍 CREATING UPSTREAM WEATHER STATIONS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get farm coordinates from offshore_wind_farms table
    query = """
    SELECT DISTINCT
        f.name as farm_name,
        f.latitude,
        f.longitude
    FROM `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms` f
    WHERE f.latitude IS NOT NULL
      AND f.longitude IS NOT NULL
      AND EXISTS (
        SELECT 1 
        FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete` w
        WHERE w.farm_name = f.name
      )
    ORDER BY f.name
    """
    
    farms_df = client.query(query).to_dataframe()
    print(f"Found {len(farms_df)} farms with coordinates")
    print()
    
    # Calculate upstream stations at 50km, 100km, 150km west-southwest
    upstream_stations = []
    
    for _, farm in farms_df.iterrows():
        farm_name = farm['farm_name']
        farm_lat = farm['latitude']
        farm_lon = farm['longitude']
        
        print(f"Processing {farm_name} ({farm_lat:.2f}, {farm_lon:.2f})")
        
        for distance_km in [50, 100, 150]:
            upstream_lat, upstream_lon = calculate_upstream_coordinates(
                farm_lat, farm_lon, distance_km, bearing_deg=240
            )
            
            upstream_stations.append({
                'farm_name': farm_name,
                'farm_latitude': farm_lat,
                'farm_longitude': farm_lon,
                'upstream_distance_km': distance_km,
                'upstream_latitude': upstream_lat,
                'upstream_longitude': upstream_lon,
                'bearing_deg': 240,  # WSW - prevailing wind direction
            })
            
            print(f"  {distance_km}km upstream: ({upstream_lat:.2f}, {upstream_lon:.2f})")
    
    print()
    print(f"✅ Created {len(upstream_stations)} upstream stations ({len(farms_df)} farms × 3 distances)")
    print()
    
    # Create BigQuery table
    schema = [
        bigquery.SchemaField("farm_name", "STRING"),
        bigquery.SchemaField("farm_latitude", "FLOAT"),
        bigquery.SchemaField("farm_longitude", "FLOAT"),
        bigquery.SchemaField("upstream_distance_km", "INTEGER"),
        bigquery.SchemaField("upstream_latitude", "FLOAT"),
        bigquery.SchemaField("upstream_longitude", "FLOAT"),
        bigquery.SchemaField("bearing_deg", "INTEGER"),
    ]
    
    table_id = f"{PROJECT_ID}.{DATASET}.upstream_stations"
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    import pandas as pd
    upstream_df = pd.DataFrame(upstream_stations)
    
    load_job = client.load_table_from_dataframe(upstream_df, table_id, job_config=job_config)
    load_job.result()
    
    print(f"✅ Loaded {len(upstream_df)} upstream stations to: {table_id}")
    print()
    
    return len(upstream_df)

def create_upstream_weather_view():
    """
    Create view that extracts upstream weather for each farm using nearest-neighbor matching.
    
    Since we don't have weather data at exact upstream coordinates, we use the nearest
    farm's weather data as a proxy (UK offshore farms are relatively close together).
    """
    
    print("=" * 80)
    print("🌦️  CREATING UPSTREAM WEATHER VIEW")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.upstream_weather_proxy` AS
    WITH farm_coords AS (
      SELECT DISTINCT
        name as farm_name,
        latitude as farm_lat,
        longitude as farm_lon
      FROM `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms`
      WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    ),
    upstream_coords AS (
      SELECT 
        farm_name,
        upstream_distance_km,
        upstream_latitude,
        upstream_longitude
      FROM `inner-cinema-476211-u9.uk_energy_prod.upstream_stations`
    ),
    -- Find nearest farm to each upstream station using Haversine distance
    nearest_farms AS (
      SELECT
        u.farm_name,
        u.upstream_distance_km,
        u.upstream_latitude,
        u.upstream_longitude,
        f.farm_name as proxy_farm_name,
        f.farm_lat as proxy_lat,
        f.farm_lon as proxy_lon,
        -- Haversine distance in km
        2 * 6371 * ASIN(SQRT(
          POW(SIN((ACOS(-1) * (f.farm_lat - u.upstream_latitude) / 180) / 2), 2) +
          COS(ACOS(-1) * u.upstream_latitude / 180) * COS(ACOS(-1) * f.farm_lat / 180) *
          POW(SIN((ACOS(-1) * (f.farm_lon - u.upstream_longitude) / 180) / 2), 2)
        )) as distance_to_proxy_km,
        ROW_NUMBER() OVER (
          PARTITION BY u.farm_name, u.upstream_distance_km 
          ORDER BY 2 * 6371 * ASIN(SQRT(
            POW(SIN((ACOS(-1) * (f.farm_lat - u.upstream_latitude) / 180) / 2), 2) +
            COS(ACOS(-1) * u.upstream_latitude / 180) * COS(ACOS(-1) * f.farm_lat / 180) *
            POW(SIN((ACOS(-1) * (f.farm_lon - u.upstream_longitude) / 180) / 2), 2)
          ))
        ) as rn
      FROM upstream_coords u
      CROSS JOIN farm_coords f
    )
    SELECT
      nf.farm_name,
      nf.upstream_distance_km,
      nf.proxy_farm_name,
      nf.distance_to_proxy_km,
      w.timestamp,
      w.surface_pressure_hpa as upstream_pressure_hpa,
      w.wind_speed_100m_ms as upstream_wind_speed_ms,
      w.wind_direction_100m_deg as upstream_wind_direction_deg,
      w.temperature_2m_c as upstream_temperature_c,
      w.wind_gusts_10m_ms as upstream_wind_gusts_ms
    FROM nearest_farms nf
    JOIN `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete` w
      ON nf.proxy_farm_name = w.farm_name
    WHERE nf.rn = 1  -- Only nearest farm
    """
    
    print("Creating upstream_weather_proxy view...")
    print("(Uses nearest farm as proxy for upstream coordinates)")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ View created: upstream_weather_proxy")
    print()
    
    # Test view
    test_query = """
    SELECT
      COUNT(*) as total_observations,
      COUNT(DISTINCT farm_name) as farms,
      COUNT(DISTINCT upstream_distance_km) as distances,
      MIN(timestamp) as earliest,
      MAX(timestamp) as latest
    FROM `inner-cinema-476211-u9.uk_energy_prod.upstream_weather_proxy`
    """
    
    df = client.query(test_query).to_dataframe()
    print("View validation:")
    print(f"  Total observations: {int(df['total_observations'][0]):,}")
    print(f"  Farms: {int(df['farms'][0])}")
    print(f"  Upstream distances: {int(df['distances'][0])} (50km, 100km, 150km)")
    print(f"  Date range: {df['earliest'][0]} to {df['latest'][0]}")
    print()

def create_upstream_features_table():
    """
    Create era5_upstream_features table with gradients and changes.
    
    Calculates:
    - Pressure gradient: (upstream_pressure - farm_pressure) / distance_km
    - Wind speed change: upstream_wind - farm_wind
    - Direction shift: upstream_direction - farm_direction (circular arithmetic)
    - Temperature gradient: (upstream_temp - farm_temp) / distance_km
    """
    
    print("=" * 80)
    print("📊 CREATING UPSTREAM FEATURES TABLE")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.era5_upstream_features` AS
    WITH farm_weather AS (
      SELECT
        farm_name,
        timestamp,
        surface_pressure_hpa as farm_pressure_hpa,
        wind_speed_100m_ms as farm_wind_speed_ms,
        wind_direction_100m_deg as farm_wind_direction_deg,
        temperature_2m_c as farm_temperature_c,
        wind_gusts_10m_ms as farm_wind_gusts_ms
      FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
    ),
    upstream_weather AS (
      SELECT
        farm_name,
        upstream_distance_km,
        proxy_farm_name,
        distance_to_proxy_km,
        timestamp,
        upstream_pressure_hpa,
        upstream_wind_speed_ms,
        upstream_wind_direction_deg,
        upstream_temperature_c,
        upstream_wind_gusts_ms
      FROM `inner-cinema-476211-u9.uk_energy_prod.upstream_weather_proxy`
    )
    SELECT
      f.farm_name,
      f.timestamp,
      u.upstream_distance_km,
      u.proxy_farm_name,
      u.distance_to_proxy_km,
      
      -- Farm (on-site) variables
      f.farm_pressure_hpa,
      f.farm_wind_speed_ms,
      f.farm_wind_direction_deg,
      f.farm_temperature_c,
      f.farm_wind_gusts_ms,
      
      -- Upstream variables
      u.upstream_pressure_hpa,
      u.upstream_wind_speed_ms,
      u.upstream_wind_direction_deg,
      u.upstream_temperature_c,
      u.upstream_wind_gusts_ms,
      
      -- Gradients and changes
      (u.upstream_pressure_hpa - f.farm_pressure_hpa) / u.upstream_distance_km 
        as pressure_gradient_hpa_per_km,
      
      (u.upstream_temperature_c - f.farm_temperature_c) / u.upstream_distance_km 
        as temperature_gradient_c_per_km,
      
      (u.upstream_wind_speed_ms - f.farm_wind_speed_ms) 
        as wind_speed_change_ms,
      
      (u.upstream_wind_gusts_ms - f.farm_wind_gusts_ms) 
        as wind_gust_change_ms,
      
      -- Direction shift with circular arithmetic (handles 0°/360° wrap)
      CASE
        WHEN ABS(u.upstream_wind_direction_deg - f.farm_wind_direction_deg) <= 180
        THEN u.upstream_wind_direction_deg - f.farm_wind_direction_deg
        WHEN u.upstream_wind_direction_deg > f.farm_wind_direction_deg
        THEN u.upstream_wind_direction_deg - f.farm_wind_direction_deg - 360
        ELSE u.upstream_wind_direction_deg - f.farm_wind_direction_deg + 360
      END as wind_direction_shift_deg
      
    FROM farm_weather f
    JOIN upstream_weather u
      ON f.farm_name = u.farm_name
      AND f.timestamp = u.timestamp
    """
    
    print("Creating era5_upstream_features table...")
    print("Calculating gradients and changes for:")
    print("  • Pressure gradient (hPa/km)")
    print("  • Temperature gradient (°C/km)")
    print("  • Wind speed change (m/s)")
    print("  • Wind gust change (m/s)")
    print("  • Wind direction shift (degrees, circular)")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Table created: era5_upstream_features")
    print()
    
    # Summary statistics
    summary_query = """
    SELECT
      COUNT(*) as total_observations,
      COUNT(DISTINCT farm_name) as farms,
      COUNT(DISTINCT upstream_distance_km) as distances,
      MIN(timestamp) as earliest,
      MAX(timestamp) as latest,
      AVG(pressure_gradient_hpa_per_km) as avg_pressure_gradient,
      STDDEV(pressure_gradient_hpa_per_km) as std_pressure_gradient,
      AVG(wind_speed_change_ms) as avg_wind_speed_change,
      STDDEV(wind_speed_change_ms) as std_wind_speed_change
    FROM `inner-cinema-476211-u9.uk_energy_prod.era5_upstream_features`
    """
    
    df = client.query(summary_query).to_dataframe()
    
    print("Table summary:")
    print(f"  Total observations: {int(df['total_observations'][0]):,}")
    print(f"  Farms: {int(df['farms'][0])}")
    print(f"  Upstream distances: {int(df['distances'][0])}")
    print(f"  Date range: {df['earliest'][0]} to {df['latest'][0]}")
    print()
    print(f"  Avg pressure gradient: {df['avg_pressure_gradient'][0]:.4f} ± {df['std_pressure_gradient'][0]:.4f} hPa/km")
    print(f"  Avg wind speed change: {df['avg_wind_speed_change'][0]:.2f} ± {df['std_wind_speed_change'][0]:.2f} m/s")
    print()

def analyze_upstream_signal_strength():
    """Analyze which upstream signals have strongest correlation with events."""
    
    print("=" * 80)
    print("📈 UPSTREAM SIGNAL STRENGTH ANALYSIS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Check which upstream signals vary most (highest variance = most informative)
    query = """
    SELECT
      upstream_distance_km,
      
      -- Pressure gradient statistics
      AVG(ABS(pressure_gradient_hpa_per_km)) as avg_abs_pressure_gradient,
      STDDEV(pressure_gradient_hpa_per_km) as std_pressure_gradient,
      MAX(ABS(pressure_gradient_hpa_per_km)) as max_abs_pressure_gradient,
      
      -- Wind speed change statistics
      AVG(ABS(wind_speed_change_ms)) as avg_abs_wind_speed_change,
      STDDEV(wind_speed_change_ms) as std_wind_speed_change,
      MAX(ABS(wind_speed_change_ms)) as max_abs_wind_speed_change,
      
      -- Direction shift statistics
      AVG(ABS(wind_direction_shift_deg)) as avg_abs_direction_shift,
      STDDEV(wind_direction_shift_deg) as std_direction_shift,
      MAX(ABS(wind_direction_shift_deg)) as max_abs_direction_shift,
      
      COUNT(*) as observations
    FROM `inner-cinema-476211-u9.uk_energy_prod.era5_upstream_features`
    GROUP BY upstream_distance_km
    ORDER BY upstream_distance_km
    """
    
    df = client.query(query).to_dataframe()
    
    print("Signal strength by upstream distance:\n")
    
    for _, row in df.iterrows():
        dist = int(row['upstream_distance_km'])
        print(f"📍 {dist}km upstream ({int(row['observations']):,} observations):")
        print()
        print(f"  Pressure gradient:")
        print(f"    Mean |Δ|: {row['avg_abs_pressure_gradient']:.4f} hPa/km")
        print(f"    Std dev:  {row['std_pressure_gradient']:.4f} hPa/km")
        print(f"    Max |Δ|:  {row['max_abs_pressure_gradient']:.4f} hPa/km")
        print()
        print(f"  Wind speed change:")
        print(f"    Mean |Δ|: {row['avg_abs_wind_speed_change']:.2f} m/s")
        print(f"    Std dev:  {row['std_wind_speed_change']:.2f} m/s")
        print(f"    Max |Δ|:  {row['max_abs_wind_speed_change']:.1f} m/s")
        print()
        print(f"  Direction shift:")
        print(f"    Mean |Δ|: {row['avg_abs_direction_shift']:.1f}°")
        print(f"    Std dev:  {row['std_direction_shift']:.1f}°")
        print(f"    Max |Δ|:  {row['max_abs_direction_shift']:.0f}°")
        print()
    
    print("=" * 80)
    print("💡 INTERPRETATION:")
    print("=" * 80)
    print()
    print("High variance = informative signal for event prediction")
    print()
    print("Expected patterns:")
    print("  • Pressure gradient: Larger at 150km (more lead time for storm detection)")
    print("  • Wind speed: Smaller differences (smooth gradients over distance)")
    print("  • Direction: Frontal passages show rapid shifts (40-90° changes)")
    print()

def validate_with_sample_events():
    """Validate upstream features by examining CALM and STORM events."""
    
    print("=" * 80)
    print("🔍 VALIDATING UPSTREAM FEATURES WITH SAMPLE EVENTS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Sample CALM events with upstream signals
    query_calm = """
    SELECT
      e.farm_name,
      e.event_type,
      e.peak_ts,
      e.duration_hours,
      e.avg_cf_deviation_pct,
      u.upstream_distance_km,
      u.pressure_gradient_hpa_per_km,
      u.wind_speed_change_ms,
      u.farm_wind_speed_ms,
      u.upstream_wind_speed_ms
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_detected` e
    JOIN `inner-cinema-476211-u9.uk_energy_prod.era5_upstream_features` u
      ON e.farm_name = u.farm_name
      AND e.peak_ts = u.timestamp
    WHERE e.event_type = 'CALM'
      AND u.upstream_distance_km = 100  -- Focus on 100km for analysis
    ORDER BY e.revenue_impact_gbp DESC
    LIMIT 10
    """
    
    df_calm = client.query(query_calm).to_dataframe()
    
    if len(df_calm) > 0:
        print("🌫️  CALM EVENTS (Top 10 by revenue impact):\n")
        
        for idx, row in df_calm.iterrows():
            print(f"Event {idx+1}: {row['farm_name']} at {row['peak_ts']}")
            print(f"  Duration: {int(row['duration_hours'])}h, CF deviation: {row['avg_cf_deviation_pct']:.1f}%")
            print(f"  On-site wind: {row['farm_wind_speed_ms']:.1f} m/s")
            print(f"  100km upstream wind: {row['upstream_wind_speed_ms']:.1f} m/s")
            print(f"  Wind speed change: {row['wind_speed_change_ms']:.1f} m/s")
            print(f"  Pressure gradient: {row['pressure_gradient_hpa_per_km']:.4f} hPa/km")
            print()
    else:
        print("⚠️  No CALM events found with upstream features")
        print()
    
    # Sample STORM events
    query_storm = """
    SELECT
      e.farm_name,
      e.event_type,
      e.peak_ts,
      e.duration_hours,
      e.avg_cf_deviation_pct,
      u.upstream_distance_km,
      u.pressure_gradient_hpa_per_km,
      u.wind_direction_shift_deg,
      u.farm_pressure_hpa,
      u.upstream_pressure_hpa
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_detected` e
    JOIN `inner-cinema-476211-u9.uk_energy_prod.era5_upstream_features` u
      ON e.farm_name = u.farm_name
      AND e.peak_ts = u.timestamp
    WHERE e.event_type = 'STORM'
      AND u.upstream_distance_km = 100
    ORDER BY ABS(u.pressure_gradient_hpa_per_km) DESC
    LIMIT 10
    """
    
    df_storm = client.query(query_storm).to_dataframe()
    
    if len(df_storm) > 0:
        print("⛈️  STORM EVENTS (Top 10 by pressure gradient):\n")
        
        for idx, row in df_storm.iterrows():
            print(f"Event {idx+1}: {row['farm_name']} at {row['peak_ts']}")
            print(f"  Duration: {int(row['duration_hours'])}h, CF deviation: {row['avg_cf_deviation_pct']:.1f}%")
            print(f"  On-site pressure: {row['farm_pressure_hpa']:.1f} hPa")
            print(f"  100km upstream pressure: {row['upstream_pressure_hpa']:.1f} hPa")
            print(f"  Pressure gradient: {row['pressure_gradient_hpa_per_km']:.4f} hPa/km")
            print(f"  Direction shift: {row['wind_direction_shift_deg']:.1f}°")
            print()
    else:
        print("⚠️  No STORM events found with upstream features")
        print()

def main():
    """Run complete upstream features pipeline."""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "TASK 5: UPSTREAM STATION FEATURES" + " " * 23 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Goal: Create virtual weather stations 50-150km west of farms")
    print("Purpose: Track upstream signal propagation for event forecasting")
    print()
    print("Expected lead times:")
    print("  • Pressure gradients: 6-12 hours (long-range storm warning)")
    print("  • Direction shifts: 1-3 hours (frontal passage detection)")
    print("  • Wind gusts: 0-2 hours (immediate turbulence warning)")
    print()
    
    try:
        # Step 1: Create upstream station coordinates
        num_stations = create_upstream_stations_table()
        
        # Step 2: Create upstream weather proxy view
        create_upstream_weather_view()
        
        # Step 3: Create upstream features table with gradients
        create_upstream_features_table()
        
        # Step 4: Analyze signal strength
        analyze_upstream_signal_strength()
        
        # Step 5: Validate with sample events
        validate_with_sample_events()
        
        print("=" * 80)
        print("✅ TASK 5 COMPLETE: UPSTREAM FEATURES CREATED")
        print("=" * 80)
        print()
        print("Created Resources:")
        print(f"  • upstream_stations table: {num_stations} virtual stations")
        print("  • upstream_weather_proxy view: Nearest-neighbor weather matching")
        print("  • era5_upstream_features table: Gradients and changes")
        print()
        print("Ready For:")
        print("  • Task 6: Unified hourly features view (join all signals)")
        print("  • Task 8: Lead time calculation (correlate upstream → generation)")
        print("  • Task 11: Cross-correlation analysis (statistical validation)")
        print()
        print("Next: Task 6 - Create unified hourly features view")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
