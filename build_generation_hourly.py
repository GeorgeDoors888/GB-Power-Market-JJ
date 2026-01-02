#!/usr/bin/env python3
"""
Build Generation Hourly Alignment Table

Creates wind_generation_hourly table with hourly generation data
aligned with weather conditions and expected power curves.

Purpose:
- Foundation for event detection (Task 4)
- Generation impact analysis (Task 8)
- Dashboard data source (Tasks 9-10)

Key Features:
- One row per farm-hour (no duplicates)
- Actual vs expected generation from Task 3 power curves
- Capacity factor and deviation metrics
- 2024+ coverage for recent analysis
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_generation_hourly_table():
    """Create persistent table with hourly generation data."""
    
    print("=" * 80)
    print("⚡ CREATING WIND_GENERATION_HOURLY TABLE")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly` AS
    WITH generation_by_hour AS (
      -- Aggregate generation to hourly level (AVG across settlement periods)
      SELECT
        m.farm_name,
        TIMESTAMP_TRUNC(CAST(p.settlementDate AS TIMESTAMP), HOUR) as hour,
        AVG(p.levelTo) as actual_mw,
        COUNT(*) as settlement_periods  -- Should be ~2 per hour (30-min periods)
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_pn` p
      INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_farm_to_bmu` m
        ON p.bmUnit = m.bm_unit_id
      WHERE CAST(p.settlementDate AS DATE) >= '2024-01-01'
      GROUP BY m.farm_name, hour
    ),
    with_weather_and_specs AS (
      SELECT
        g.farm_name,
        g.hour,
        g.actual_mw,
        g.settlement_periods,
        
        -- Weather
        w.wind_speed_100m_ms,
        w.temperature_2m_c,
        w.surface_pressure_hpa,
        w.wind_direction_100m_deg,
        w.wind_gusts_10m_ms,
        SAFE_DIVIDE(w.wind_gusts_10m_ms, NULLIF(w.wind_speed_100m_ms, 0)) as gust_factor,
        
        -- Turbine specs
        ts.cut_in_speed_ms,
        ts.rated_speed_ms,
        ts.cut_out_speed_ms,
        ts.rated_capacity_mw,
        ts.swept_area_m2,
        ts.total_capacity_mw as capacity_mw,
        
        -- Expected power (using Task 3 UDF)
        `inner-cinema-476211-u9.uk_energy_prod.calculate_power_output`(
          w.wind_speed_100m_ms,
          w.temperature_2m_c,
          w.surface_pressure_hpa,
          ts.cut_in_speed_ms,
          ts.rated_speed_ms,
          ts.cut_out_speed_ms,
          ts.rated_capacity_mw,
          ts.swept_area_m2
        ) * (ts.total_capacity_mw / NULLIF(ts.rated_capacity_mw, 0)) as expected_mw
        
      FROM generation_by_hour g
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete` w
        ON g.farm_name = w.farm_name
        AND g.hour = w.timestamp
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_turbine_specs` ts
        ON g.farm_name = ts.farm_name
    )
    SELECT
      farm_name,
      hour,
      actual_mw,
      expected_mw,
      capacity_mw,
      settlement_periods,
      
      -- Capacity factors
      actual_mw / NULLIF(capacity_mw, 0) * 100 as capacity_factor_pct,
      expected_mw / NULLIF(capacity_mw, 0) * 100 as expected_cf_pct,
      
      -- Deviations
      actual_mw - expected_mw as deviation_mw,
      (actual_mw / NULLIF(capacity_mw, 0) - expected_mw / NULLIF(capacity_mw, 0)) * 100 as cf_deviation_pct,
      
      -- Normalized power (0-1 scale)
      actual_mw / NULLIF(capacity_mw, 0) as normalized_power,
      
      -- Weather conditions
      wind_speed_100m_ms,
      temperature_2m_c,
      surface_pressure_hpa,
      wind_direction_100m_deg,
      wind_gusts_10m_ms,
      gust_factor,
      
      -- Turbine parameters
      cut_in_speed_ms,
      rated_speed_ms,
      cut_out_speed_ms
      
    FROM with_weather_and_specs
    WHERE actual_mw IS NOT NULL
      AND expected_mw IS NOT NULL
      AND capacity_mw IS NOT NULL
    """
    
    print("Creating table: wind_generation_hourly")
    print("  Source: bmrs_pn (B1610 Physical Notifications)")
    print("  Aggregation: AVG(levelTo) per farm-hour")
    print("  Features: Actual, expected MW, CF%, deviations, weather")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Table created successfully")
    print()
    
    # Validate
    validate_query = """
    SELECT 
        COUNT(*) as total_hours,
        COUNT(DISTINCT farm_name) as farms,
        MIN(DATE(hour)) as earliest,
        MAX(DATE(hour)) as latest,
        AVG(capacity_factor_pct) as avg_cf_pct,
        AVG(cf_deviation_pct) as avg_cf_deviation,
        SUM(CASE WHEN cf_deviation_pct < -10 THEN 1 ELSE 0 END) as underperform_hours
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly`
    """
    
    df = client.query(validate_query).to_dataframe()
    
    if len(df) > 0:
        row = df.iloc[0]
        print("Table validation:")
        print(f"  Total hours: {int(row['total_hours']):,}")
        print(f"  Farms: {int(row['farms'])}")
        print(f"  Date range: {row['earliest']} to {row['latest']}")
        print(f"  Avg CF: {row['avg_cf_pct']:.1f}%")
        print(f"  Avg CF deviation: {row['avg_cf_deviation']:.1f}%")
        print(f"  Underperforming hours (>10% below expected): {int(row['underperform_hours']):,}")
        print()

def analyze_generation_patterns():
    """Analyze generation patterns by time and weather."""
    
    print("=" * 80)
    print("📊 GENERATION PATTERN ANALYSIS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Monthly performance
    query = """
    SELECT 
        EXTRACT(YEAR FROM hour) as year,
        EXTRACT(MONTH FROM hour) as month,
        COUNT(*) as hours,
        AVG(capacity_factor_pct) as avg_cf,
        AVG(cf_deviation_pct) as avg_cf_deviation,
        SUM(actual_mw) as total_actual_mwh,
        SUM(expected_mw) as total_expected_mwh,
        SUM(expected_mw - actual_mw) as total_lost_mwh,
        SUM(expected_mw - actual_mw) * 50 as revenue_loss_gbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly`
    GROUP BY year, month
    ORDER BY year, month
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print("Monthly Performance:\n")
        print(f"{'Year-Month':<12} {'Hours':>8} {'Avg CF%':>9} {'CF Dev%':>9} {'Actual MWh':>14} {'Expected MWh':>14} {'Lost MWh':>12} {'Revenue Loss':>15}")
        print("-" * 115)
        
        for _, row in df.iterrows():
            month_str = f"{int(row['year'])}-{int(row['month']):02d}"
            print(f"{month_str:<12} "
                  f"{int(row['hours']):>8,} "
                  f"{row['avg_cf']:>8.1f}% "
                  f"{row['avg_cf_deviation']:>8.1f}% "
                  f"{row['total_actual_mwh']:>13,.0f} "
                  f"{row['total_expected_mwh']:>13,.0f} "
                  f"{row['total_lost_mwh']:>11,.0f} "
                  f"£{row['revenue_loss_gbp']:>13,.0f}")
        
        print()
        
        # Summary
        total_lost = df['total_lost_mwh'].sum()
        total_revenue_loss = df['revenue_loss_gbp'].sum()
        total_hours = df['hours'].sum()
        
        print("SUMMARY:")
        print("-" * 115)
        print(f"  • Total hours: {int(total_hours):,}")
        print(f"  • Total lost generation: {total_lost:,.0f} MWh")
        print(f"  • Total revenue loss: £{total_revenue_loss:,.0f}")
        print(f"  • Average loss per hour: {total_lost / total_hours:.1f} MWh")
        print()

def identify_problem_periods():
    """Find specific hours with severe underperformance."""
    
    print("=" * 80)
    print("🚨 SEVERE UNDERPERFORMANCE DETECTION")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    SELECT 
        farm_name,
        hour,
        capacity_factor_pct,
        expected_cf_pct,
        cf_deviation_pct,
        actual_mw,
        expected_mw,
        wind_speed_100m_ms,
        gust_factor
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly`
    WHERE cf_deviation_pct < -50  -- More than 50% below expected
      AND expected_cf_pct > 50  -- Should be producing well
      AND wind_speed_100m_ms BETWEEN 8 AND 15  -- Optimal wind conditions
    ORDER BY cf_deviation_pct
    LIMIT 20
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print(f"Top 20 Worst Performing Hours (CF >50% below expected in good wind):\n")
        print(f"{'Farm':<25} {'Hour':<20} {'CF%':>6} {'Exp%':>6} {'Dev%':>7} {'Act MW':>8} {'Exp MW':>8} {'Wind':>6} {'Gust':>6}")
        print("-" * 115)
        
        for _, row in df.iterrows():
            print(f"{row['farm_name']:<25} "
                  f"{row['hour'].strftime('%Y-%m-%d %H:%M'):<20} "
                  f"{row['capacity_factor_pct']:>5.1f}% "
                  f"{row['expected_cf_pct']:>5.1f}% "
                  f"{row['cf_deviation_pct']:>6.1f}% "
                  f"{row['actual_mw']:>7.0f} "
                  f"{row['expected_mw']:>7.0f} "
                  f"{row['wind_speed_100m_ms']:>5.1f} "
                  f"{row['gust_factor']:>5.2f}" if pd.notna(row['gust_factor']) else f"{'N/A':>6}")
        
        print()
        print("INSIGHTS:")
        print("-" * 115)
        print("  • These hours represent likely curtailment or outages")
        print("  • Good wind conditions (8-15 m/s) but severe underperformance")
        print("  • Candidates for event detection (Task 4)")
        print()
    else:
        print("✅ No severe underperformance detected in optimal wind conditions")
        print()

def check_data_quality():
    """Check for data quality issues."""
    
    print("=" * 80)
    print("✅ DATA QUALITY CHECKS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Check for duplicate farm-hours
    dup_query = """
    SELECT 
        farm_name,
        hour,
        COUNT(*) as records
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly`
    GROUP BY farm_name, hour
    HAVING COUNT(*) > 1
    LIMIT 5
    """
    
    dup_df = client.query(dup_query).to_dataframe()
    
    if len(dup_df) > 0:
        print("⚠️  DUPLICATE FARM-HOUR RECORDS FOUND:")
        print(dup_df.to_string(index=False))
        print()
    else:
        print("✅ No duplicate farm-hour records")
        print()
    
    # Check for invalid values
    invalid_query = """
    SELECT 
        'Negative CF' as issue,
        COUNT(*) as count
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly`
    WHERE capacity_factor_pct < 0
    
    UNION ALL
    
    SELECT 
        'CF > 100%' as issue,
        COUNT(*) as count
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly`
    WHERE capacity_factor_pct > 100
    
    UNION ALL
    
    SELECT 
        'Null actual_mw' as issue,
        COUNT(*) as count
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly`
    WHERE actual_mw IS NULL
    """
    
    invalid_df = client.query(invalid_query).to_dataframe()
    
    print("Invalid value checks:")
    for _, row in invalid_df.iterrows():
        status = "⚠️ " if row['count'] > 0 else "✅"
        print(f"  {status} {row['issue']}: {int(row['count'])} records")
    
    print()

def main():
    """Run complete generation hourly alignment."""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "GENERATION HOURLY ALIGNMENT" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Task 7: Build wind_generation_hourly table for event-propagation analysis")
    print("Foundation for: Event detection (Task 4), Impact analysis (Task 8), Dashboards (9-10)")
    print()
    
    try:
        # Step 1: Create table
        create_generation_hourly_table()
        
        # Step 2: Analyze patterns
        analyze_generation_patterns()
        
        # Step 3: Identify problem periods
        identify_problem_periods()
        
        # Step 4: Data quality checks
        check_data_quality()
        
        print("=" * 80)
        print("✅ TASK 7 COMPLETE: Generation Hourly Alignment Built")
        print("=" * 80)
        print()
        print("Created Resources:")
        print("  • wind_generation_hourly table (hourly generation + weather + deviations)")
        print("  • Monthly performance analysis")
        print("  • Severe underperformance detection (curtailment candidates)")
        print()
        print("Next Steps:")
        print("  • Task 4: Design event detection layer (use wind_generation_hourly)")
        print("  • Task 5: Build upstream station features (50-150km west)")
        print("  • Task 8: Calculate event onset timing and lead times")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
