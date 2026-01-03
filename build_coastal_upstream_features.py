#!/usr/bin/env python3
"""
Task 5 ENHANCEMENT: Build Upstream Features with Actual Coastal Weather Stations

ISSUE FROM TASK 8:
- Original Task 5 used nearest-neighbor wind farm proxy for "upstream" stations
- Result: Farms matched to themselves → ZERO spatial gradients
- No detectable lead times because pressure/temp/wind identical at "upstream" vs on-site

SOLUTION:
- Add actual UK coastal weather stations 150-250km WEST of offshore wind farms
- Use Met Office land stations or Open-Meteo Archive API for coastal locations
- Calculate real pressure/temperature/wind gradients between coast and offshore
- Enable 6-12 hour lead time detection for pressure systems moving west→east

Coastal Reference Stations (WSW of offshore wind clusters):
1. Blackpool (53.8°N, -3.0°W) - Irish Sea coast, 150km west of Hornsea
2. Liverpool (53.4°N, -3.0°W) - Mersey coast, west of Burbo Bank
3. Aberystwyth (52.4°N, -4.1°W) - Welsh coast, 200km west of southern farms
4. Stornoway (58.2°N, -6.4°W) - Outer Hebrides, 250km west of Moray/Beatrice
5. Tiree (56.5°N, -6.9°W) - Inner Hebrides, 300km west of Scottish farms
6. Dún Laoghaire (53.3°N, -6.1°W) - Irish coast, 250km west of Irish Sea farms

These provide genuine UPSTREAM signals 4-8 hours before weather reaches offshore farms.
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import math
import time
import requests

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# UK Coastal Weather Stations (selected for upstream positioning relative to offshore wind)
COASTAL_STATIONS = [
    # Name, Latitude, Longitude, Description
    ("Blackpool", 53.817, -3.050, "Irish Sea coast - upstream of Hornsea/Race Bank"),
    ("Liverpool", 53.425, -3.000, "Mersey coast - upstream of Burbo Bank/Walney"),
    ("Aberystwyth", 52.415, -4.082, "Welsh coast - upstream of southern farms"),
    ("Stornoway", 58.210, -6.391, "Outer Hebrides - upstream of Moray/Beatrice"),
    ("Tiree", 56.499, -6.879, "Inner Hebrides - upstream of Scottish offshore"),
    ("Malin_Head", 55.367, -7.344, "N Ireland - upstream of Irish Sea farms"),
]

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate great circle distance between two points on Earth.
    Returns distance in km.
    """
    R = 6371  # Earth radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate bearing from point 1 to point 2.
    Returns bearing in degrees (0° = North, 90° = East, 180° = South, 270° = West).
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def download_coastal_weather_openmeteo(station_name, lat, lon, start_date="2020-01-01", end_date="2025-11-30"):
    """
    Download weather data from Open-Meteo Archive API for a coastal station.
    
    Variables:
    - temperature_2m (°C)
    - relative_humidity_2m (%)
    - surface_pressure (hPa)
    - wind_speed_10m (m/s)
    - wind_direction_10m (°)
    - wind_gusts_10m (m/s)
    """
    
    print(f"  Downloading weather for {station_name} ({lat:.3f}, {lon:.3f})...")
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m"
        ],
        "timezone": "UTC"
    }
    
    response = requests.get(url, params=params, timeout=120)
    
    if response.status_code != 200:
        print(f"    ❌ Error {response.status_code}: {response.text}")
        return None
    
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame({
        'station_name': station_name,
        'latitude': lat,
        'longitude': lon,
        'timestamp': pd.to_datetime(data['hourly']['time']),
        'temperature_2m_c': data['hourly']['temperature_2m'],
        'relative_humidity_2m_pct': data['hourly']['relative_humidity_2m'],
        'surface_pressure_hpa': data['hourly']['surface_pressure'],
        'wind_speed_10m_ms': data['hourly']['wind_speed_10m'],
        'wind_direction_10m_deg': data['hourly']['wind_direction_10m'],
        'wind_gusts_10m_ms': data['hourly']['wind_gusts_10m']
    })
    
    print(f"    ✅ Retrieved {len(df):,} hours")
    return df

def create_coastal_stations_table():
    """
    Create table of UK coastal weather stations for upstream analysis.
    """
    
    print("=" * 80)
    print("🌊 STEP 1: CREATE COASTAL WEATHER STATIONS TABLE")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Create stations reference table
    stations_df = pd.DataFrame(COASTAL_STATIONS, columns=['station_name', 'latitude', 'longitude', 'description'])
    
    table_id = f"{PROJECT_ID}.{DATASET}.coastal_weather_stations"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("station_name", "STRING"),
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
            bigquery.SchemaField("description", "STRING"),
        ]
    )
    
    job = client.load_table_from_dataframe(stations_df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Created {table_id} with {len(stations_df)} coastal stations")
    print()
    
    for _, row in stations_df.iterrows():
        print(f"  • {row['station_name']:15} ({row['latitude']:>7.3f}, {row['longitude']:>7.3f}) - {row['description']}")
    print()

def download_all_coastal_weather():
    """
    Download historical weather data for all coastal stations.
    """
    
    print("=" * 80)
    print("📥 STEP 2: DOWNLOAD COASTAL WEATHER DATA (2020-2025)")
    print("=" * 80)
    print()
    
    all_data = []
    
    for station_name, lat, lon, desc in COASTAL_STATIONS:
        print(f"\n[{len(all_data)+1}/{len(COASTAL_STATIONS)}] {station_name}")
        
        df = download_coastal_weather_openmeteo(station_name, lat, lon)
        
        if df is not None:
            all_data.append(df)
        
        # Rate limiting: 15 seconds between requests
        if len(all_data) < len(COASTAL_STATIONS):
            print("    ⏳ Waiting 15 seconds...")
            time.sleep(15)
    
    if len(all_data) == 0:
        print("❌ No data downloaded!")
        return None
    
    # Combine all stations
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print()
    print(f"✅ Downloaded {len(combined_df):,} total hours across {len(all_data)} stations")
    print()
    
    return combined_df

def upload_coastal_weather_to_bigquery(df):
    """
    Upload coastal weather data to BigQuery.
    """
    
    print("=" * 80)
    print("📤 STEP 3: UPLOAD COASTAL WEATHER TO BIGQUERY")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    table_id = f"{PROJECT_ID}.{DATASET}.coastal_weather_data"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("station_name", "STRING"),
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("temperature_2m_c", "FLOAT"),
            bigquery.SchemaField("relative_humidity_2m_pct", "FLOAT"),
            bigquery.SchemaField("surface_pressure_hpa", "FLOAT"),
            bigquery.SchemaField("wind_speed_10m_ms", "FLOAT"),
            bigquery.SchemaField("wind_direction_10m_deg", "FLOAT"),
            bigquery.SchemaField("wind_gusts_10m_ms", "FLOAT"),
        ]
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded {len(df):,} rows to {table_id}")
    print()
    
    # Validate
    validation_query = f"""
    SELECT
        station_name,
        COUNT(*) as hours,
        MIN(timestamp) as first_data,
        MAX(timestamp) as last_data,
        AVG(surface_pressure_hpa) as avg_pressure,
        AVG(wind_speed_10m_ms) as avg_wind
    FROM `{table_id}`
    GROUP BY station_name
    ORDER BY station_name
    """
    
    validation_df = client.query(validation_query).to_dataframe()
    
    print("Coastal Weather Data Summary:\n")
    for _, row in validation_df.iterrows():
        print(f"{row['station_name']:15} {int(row['hours']):>7,} hours | "
              f"{row['first_data']} to {row['last_data']} | "
              f"Pressure: {row['avg_pressure']:.1f} hPa | Wind: {row['avg_wind']:.1f} m/s")
    print()

def create_upstream_coastal_features():
    """
    Match each offshore wind farm to nearest appropriate coastal station
    and calculate gradients.
    """
    
    print("=" * 80)
    print("🔗 STEP 4: MATCH FARMS TO COASTAL STATIONS & CALCULATE GRADIENTS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.upstream_coastal_features` AS
    WITH farm_coords AS (
      SELECT DISTINCT name as farm_name, latitude, longitude
      FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
    ),
    farm_weather AS (
      SELECT
        w.farm_name,
        w.timestamp as hour,
        f.latitude as farm_lat,
        f.longitude as farm_lon,
        w.temperature_2m_c as farm_temp,
        w.surface_pressure_hpa as farm_pressure,
        w.wind_speed_100m_ms as farm_wind_speed,
        w.wind_direction_100m_deg as farm_wind_direction
      FROM `{PROJECT_ID}.{DATASET}.era5_weather_data_complete` w
      JOIN farm_coords f ON w.farm_name = f.farm_name
      WHERE w.surface_pressure_hpa IS NOT NULL
    ),
    coastal_stations_data AS (
      SELECT
        c.station_name,
        c.latitude as coastal_lat,
        c.longitude as coastal_lon,
        c.timestamp as hour,
        c.temperature_2m_c as coastal_temp,
        c.surface_pressure_hpa as coastal_pressure,
        c.wind_speed_10m_ms as coastal_wind_speed,
        c.wind_direction_10m_deg as coastal_wind_direction
      FROM `{PROJECT_ID}.{DATASET}.coastal_weather_data` c
    ),
    matched AS (
      SELECT
        f.farm_name,
        f.hour,
        f.farm_lat,
        f.farm_lon,
        f.farm_temp,
        f.farm_pressure,
        f.farm_wind_speed,
        f.farm_wind_direction,
        c.station_name as upstream_station,
        c.coastal_lat,
        c.coastal_lon,
        c.coastal_temp,
        c.coastal_pressure,
        c.coastal_wind_speed,
        c.coastal_wind_direction,
        -- Calculate distance using Haversine (BigQuery ST_DISTANCE equivalent)
        ST_DISTANCE(
          ST_GEOGPOINT(f.farm_lon, f.farm_lat),
          ST_GEOGPOINT(c.coastal_lon, c.coastal_lat)
        ) / 1000 as distance_km,
        -- Bearing from coast to farm (should be roughly eastward = 60-120°)
        ST_AZIMUTH(
          ST_GEOGPOINT(c.coastal_lon, c.coastal_lat),
          ST_GEOGPOINT(f.farm_lon, f.farm_lat)
        ) * 180 / ACOS(-1) as bearing_deg,
        ROW_NUMBER() OVER (
          PARTITION BY f.farm_name, f.hour 
          ORDER BY ST_DISTANCE(
            ST_GEOGPOINT(f.farm_lon, f.farm_lat),
            ST_GEOGPOINT(c.coastal_lon, c.coastal_lat)
          )
        ) as station_rank
      FROM farm_weather f
      CROSS JOIN coastal_stations_data c
      WHERE f.hour = c.hour
    ),
    nearest_station AS (
      SELECT * FROM matched
      WHERE station_rank = 1  -- Closest coastal station
        AND bearing_deg BETWEEN 0 AND 180  -- Upstream must be west/southwest (bearing east from coast)
        AND distance_km BETWEEN 50 AND 400  -- Reasonable upstream distance
    )
    SELECT
      farm_name,
      hour,
      upstream_station,
      distance_km,
      bearing_deg,
      -- Pressure gradient (hPa per km)
      (farm_pressure - coastal_pressure) / NULLIF(distance_km, 0) as pressure_gradient_hpa_per_km,
      -- Temperature gradient (°C per km)
      (farm_temp - coastal_temp) / NULLIF(distance_km, 0) as temperature_gradient_c_per_km,
      -- Wind speed change (m/s)
      (farm_wind_speed - coastal_wind_speed) as wind_speed_change_ms,
      -- Wind direction shift (degrees, accounting for circular wrapping)
      CASE
        WHEN ABS(farm_wind_direction - coastal_wind_direction) <= 180
        THEN farm_wind_direction - coastal_wind_direction
        WHEN farm_wind_direction > coastal_wind_direction
        THEN farm_wind_direction - coastal_wind_direction - 360
        ELSE farm_wind_direction - coastal_wind_direction + 360
      END as wind_direction_shift_deg,
      -- Raw values for reference
      farm_pressure,
      coastal_pressure,
      farm_temp,
      coastal_temp,
      farm_wind_speed,
      coastal_wind_speed,
      farm_wind_direction,
      coastal_wind_direction
    FROM nearest_station
    ORDER BY farm_name, hour
    """
    
    print("Creating upstream_coastal_features table...")
    print("Logic:")
    print("  • Match each farm to nearest coastal station west/southwest")
    print("  • Distance: 50-400km (typical synoptic system spacing)")
    print("  • Bearing: 0-180° east from coast (upstream positioning)")
    print("  • Calculate pressure/temp/wind gradients")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Table created")
    print()
    
    # Validation
    validation_query = f"""
    SELECT
        farm_name,
        upstream_station,
        COUNT(*) as matched_hours,
        AVG(distance_km) as avg_distance_km,
        AVG(bearing_deg) as avg_bearing_deg,
        AVG(ABS(pressure_gradient_hpa_per_km)) as avg_abs_pressure_gradient,
        MAX(ABS(pressure_gradient_hpa_per_km)) as max_abs_pressure_gradient,
        STDDEV(pressure_gradient_hpa_per_km) as stddev_pressure_gradient
    FROM `{PROJECT_ID}.{DATASET}.upstream_coastal_features`
    GROUP BY farm_name, upstream_station
    ORDER BY farm_name, matched_hours DESC
    """
    
    validation_df = client.query(validation_query).to_dataframe()
    
    print("Farm → Coastal Station Matches:\n")
    for _, row in validation_df.iterrows():
        print(f"{row['farm_name']:30} → {row['upstream_station']:15}")
        print(f"  Matched hours: {int(row['matched_hours']):>7,} | "
              f"Distance: {row['avg_distance_km']:>6.1f} km | "
              f"Bearing: {row['avg_bearing_deg']:>5.1f}°")
        print(f"  Pressure gradient: {row['avg_abs_pressure_gradient']:.4f} ± {row['stddev_pressure_gradient']:.4f} hPa/km "
              f"(max: {row['max_abs_pressure_gradient']:.4f})")
        print()
    
    return validation_df

def main():
    """
    Run Task 5 enhancement with actual coastal weather stations.
    """
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "TASK 5 ENHANCEMENT: COASTAL UPSTREAM STATIONS" + " " * 18 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Goal: Replace wind farm proxy with ACTUAL UK coastal weather stations")
    print("Purpose: Enable real pressure/temp gradients for 6-12h lead time detection")
    print()
    print("Coastal Stations: 6 locations along UK/Ireland west coast")
    print("Distance: 50-400km west of offshore wind farms")
    print("Data Source: Open-Meteo Archive API (2020-2025)")
    print()
    
    try:
        # Step 1: Create stations reference
        create_coastal_stations_table()
        
        # Step 2: Download weather data
        coastal_df = download_all_coastal_weather()
        
        if coastal_df is None:
            print("❌ Failed to download coastal weather data")
            return
        
        # Step 3: Upload to BigQuery
        upload_coastal_weather_to_bigquery(coastal_df)
        
        # Step 4: Match farms to stations and calculate gradients
        validation_df = create_upstream_coastal_features()
        
        print("=" * 80)
        print("✅ TASK 5 ENHANCEMENT COMPLETE")
        print("=" * 80)
        print()
        print("Created Resources:")
        print("  • coastal_weather_stations: 6 UK/Ireland coastal stations")
        print("  • coastal_weather_data: ~300k hours of coastal weather (2020-2025)")
        print("  • upstream_coastal_features: Farm-to-coast gradients")
        print()
        print("Next Steps:")
        print("  1. Re-run Task 8 (calculate_event_lead_times.py) with coastal data")
        print("  2. Replace wind_unified_features upstream join to use coastal data")
        print("  3. Validate 6-12h lead times for pressure-driven events")
        print()
        print("Expected Results:")
        print("  • NON-ZERO pressure gradients (coastal vs offshore different)")
        print("  • Detectable lead times for frontal systems moving west→east")
        print("  • Validation of theoretical 1-12h lead time ranges")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
