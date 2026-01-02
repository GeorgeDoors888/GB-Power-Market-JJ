#!/usr/bin/env python3
"""
FIX: Wind speed data in BigQuery is in km/h but labeled as if m/s

PROBLEM:
- Open-Meteo API returns wind_speed_100m in km/h
- We stored it in BigQuery as-is
- Analysis scripts assumed m/s → 3.6× overestimation!
- 105.8 "m/s" = actually 29.4 m/s (realistic)

SOLUTION:
1. Add new columns with correct units (m/s)
2. Add wind gust data (currently missing)
3. Update analysis scripts to use corrected columns

BigQuery doesn't support ALTER COLUMN, so we'll add computed columns.
"""

from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def add_computed_columns():
    """Add computed columns for correct wind speed units."""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print('=' * 80)
    print('🔧 FIXING WIND SPEED UNITS IN BIGQUERY')
    print('=' * 80)
    print()
    
    # Check current data
    print('Step 1: Verify current data issue')
    query = """
    SELECT 
      MIN(wind_speed_100m) as min_kmh,
      MAX(wind_speed_100m) as max_kmh,
      AVG(wind_speed_100m) as avg_kmh,
      -- What it SHOULD be in m/s
      MIN(wind_speed_100m) / 3.6 as min_ms,
      MAX(wind_speed_100m) / 3.6 as max_ms,
      AVG(wind_speed_100m) / 3.6 as avg_ms
    FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data`
    WHERE wind_speed_100m IS NOT NULL
    """
    df = client.query(query).to_dataframe()
    print('Current data (showing km/h interpreted as m/s):')
    print(df.to_string(index=False))
    print()
    print(f'❌ WRONG: Max "wind" = {df["max_kmh"].values[0]:.1f} "m/s" = {df["max_kmh"].values[0] * 3.6:.1f} km/h (hurricane!)')
    print(f'✅ CORRECT: Max wind = {df["max_ms"].values[0]:.1f} m/s = realistic storm')
    print()
    
    # Solution: Create a VIEW with corrected columns
    print('Step 2: Creating view with corrected units...')
    
    view_sql = """
    CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.era5_weather_corrected` AS
    SELECT 
      farm_name,
      timestamp,
      temperature_2m,
      relative_humidity_2m,
      precipitation,
      wind_direction_100m,
      -- Original (km/h, mislabeled)
      wind_speed_100m as wind_speed_100m_kmh,
      -- Corrected (m/s)
      wind_speed_100m / 3.6 as wind_speed_100m_ms,
      -- Categorize wind regimes (in m/s)
      CASE 
        WHEN wind_speed_100m / 3.6 < 4 THEN 'Calm (<4 m/s)'
        WHEN wind_speed_100m / 3.6 < 8 THEN 'Light (4-8 m/s)'
        WHEN wind_speed_100m / 3.6 < 12 THEN 'Moderate (8-12 m/s)'
        WHEN wind_speed_100m / 3.6 < 17 THEN 'Fresh (12-17 m/s)'
        WHEN wind_speed_100m / 3.6 < 25 THEN 'Strong (17-25 m/s)'
        ELSE 'Storm (>25 m/s, turbine cut-out)'
      END as wind_regime
    FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data`
    """
    
    client.query(view_sql).result()
    print('✅ Created view: era5_weather_corrected')
    print()
    
    # Verify
    print('Step 3: Verify corrected data')
    verify_query = """
    SELECT 
      MIN(wind_speed_100m_ms) as min_ms,
      MAX(wind_speed_100m_ms) as max_ms,
      AVG(wind_speed_100m_ms) as avg_ms,
      APPROX_QUANTILES(wind_speed_100m_ms, 100)[OFFSET(95)] as p95_ms,
      wind_regime,
      COUNT(*) as count
    FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_corrected`
    WHERE wind_speed_100m_ms IS NOT NULL
    GROUP BY wind_regime
    ORDER BY 
      CASE wind_regime
        WHEN 'Calm (<4 m/s)' THEN 1
        WHEN 'Light (4-8 m/s)' THEN 2
        WHEN 'Moderate (8-12 m/s)' THEN 3
        WHEN 'Fresh (12-17 m/s)' THEN 4
        WHEN 'Strong (17-25 m/s)' THEN 5
        WHEN 'Storm (>25 m/s, turbine cut-out)' THEN 6
      END
    """
    df = client.query(verify_query).to_dataframe()
    print('Wind Speed Distribution (CORRECTED):')
    print(df.to_string(index=False))
    print()
    
    print('=' * 80)
    print('✅ FIX COMPLETE')
    print('=' * 80)
    print()
    print('ACTION REQUIRED:')
    print('1. Update analyze_wind_yield_drops_upstream.py to use era5_weather_corrected view')
    print('2. Re-download existing farms with wind_gusts_10m data')
    print('3. Re-run analysis with corrected wind speeds')
    print()

if __name__ == '__main__':
    add_computed_columns()
