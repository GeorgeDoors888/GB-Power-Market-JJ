#!/usr/bin/env python3
"""
Weather → Generation Correlation Dashboard

Creates BigQuery views and analysis for correlating ERA5 weather data
with actual wind farm generation from bmrs_pn (B1610 Physical Notifications).

Features:
1. Hourly weather + generation aggregation (17 mapped farms)
2. Capacity factor calculation (actual vs installed capacity)
3. Icing event overlay (HIGH/MEDIUM risk periods)
4. Power curve deviation analysis
5. Revenue impact estimation
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_weather_generation_view():
    """Create unified view joining weather + generation data."""
    
    print("=" * 80)
    print("📊 CREATING WEATHER → GENERATION CORRELATION VIEW")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.weather_generation_correlation` AS
    
    WITH hourly_weather AS (
      -- Aggregate ERA5 weather to hourly (already hourly, just standardize)
      SELECT
        farm_name,
        TIMESTAMP_TRUNC(timestamp, HOUR) as hour,
        AVG(wind_speed_100m_ms) as wind_speed_ms,
        AVG(temperature_2m_c) as temperature_c,
        AVG(wind_gusts_10m_ms) as wind_gusts_ms,
        AVG(surface_pressure_hpa) as pressure_hpa,
        AVG(relative_humidity_2m_pct) as humidity_pct
      FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
      GROUP BY farm_name, hour
    ),
    
    farm_bmus AS (
      -- Get BMU mappings for wind farms
      SELECT 
        farm_name,
        bm_unit_id,
        capacity_mw
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_farm_to_bmu`
    ),
    
    hourly_generation AS (
      -- Aggregate generation data to hourly per BMU
      SELECT
        p.bmUnit,
        TIMESTAMP_TRUNC(CAST(p.settlementDate AS TIMESTAMP), HOUR) as hour,
        AVG(p.levelTo) as avg_generation_mw,
        MAX(p.levelTo) as max_generation_mw,
        MIN(p.levelTo) as min_generation_mw,
        COUNT(*) as settlement_periods
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_pn` p
      WHERE p.levelTo IS NOT NULL
      GROUP BY p.bmUnit, hour
    ),
    
    farm_generation_aggregated AS (
      -- Sum all BMUs for each farm
      SELECT
        fb.farm_name,
        g.hour,
        SUM(g.avg_generation_mw) as total_generation_mw,
        SUM(fb.capacity_mw) as total_capacity_mw,
        COUNT(DISTINCT fb.bm_unit_id) as num_bmus,
        SUM(fb.capacity_mw) / COUNT(DISTINCT fb.bm_unit_id) as avg_bmu_capacity_mw
      FROM farm_bmus fb
      INNER JOIN hourly_generation g ON fb.bm_unit_id = g.bmUnit
      GROUP BY fb.farm_name, g.hour
    ),
    
    icing_risk AS (
      -- Get icing risk classification
      SELECT
        farm_name,
        TIMESTAMP_TRUNC(timestamp, HOUR) as hour,
        icing_risk_level,
        dew_point_spread_c,
        gust_factor
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
    )
    
    SELECT
      w.farm_name,
      w.hour,
      
      -- Weather variables
      w.wind_speed_ms,
      w.temperature_c,
      w.wind_gusts_ms,
      w.pressure_hpa,
      w.humidity_pct,
      
      -- Generation data
      fg.total_generation_mw,
      fg.total_capacity_mw,
      fg.num_bmus,
      
      -- Capacity factor
      SAFE_DIVIDE(fg.total_generation_mw, NULLIF(fg.total_capacity_mw, 0)) * 100 as capacity_factor_pct,
      
      -- Power density (MW per m/s of wind)
      SAFE_DIVIDE(fg.total_generation_mw, NULLIF(w.wind_speed_ms, 0)) as power_density_mw_per_ms,
      
      -- Icing risk overlay
      ir.icing_risk_level,
      ir.dew_point_spread_c,
      ir.gust_factor,
      
      -- Flags
      CASE 
        WHEN ir.icing_risk_level = 'HIGH' THEN TRUE 
        ELSE FALSE 
      END as is_icing_event,
      
      CASE
        WHEN w.wind_speed_ms > 25 THEN TRUE  -- Cut-out wind speed ~25 m/s
        ELSE FALSE
      END as is_cutout_wind,
      
      CASE
        WHEN w.wind_speed_ms < 3 THEN TRUE  -- Cut-in wind speed ~3 m/s
        ELSE FALSE
      END as is_below_cutin
      
    FROM hourly_weather w
    LEFT JOIN farm_generation_aggregated fg 
      ON w.farm_name = fg.farm_name AND w.hour = fg.hour
    LEFT JOIN icing_risk ir
      ON w.farm_name = ir.farm_name AND w.hour = ir.hour
    
    WHERE w.hour >= '2024-01-01'  -- Focus on recent data
    """
    
    print("Creating view: weather_generation_correlation")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ View created successfully")
    print()
    
    # Test view
    test_query = """
    SELECT 
        COUNT(*) as total_hours,
        COUNT(DISTINCT farm_name) as farms,
        COUNT(DISTINCT DATE(hour)) as days,
        COUNT(CASE WHEN total_generation_mw IS NOT NULL THEN 1 END) as hours_with_generation,
        AVG(capacity_factor_pct) as avg_capacity_factor,
        SUM(CASE WHEN is_icing_event THEN 1 ELSE 0 END) as icing_hours
    FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_correlation`
    """
    
    df = client.query(test_query).to_dataframe()
    
    print("View validation:")
    print(f"  Total observations: {int(df['total_hours'][0]):,} hours")
    print(f"  Farms: {int(df['farms'][0])}")
    print(f"  Days: {int(df['days'][0])} ({df['days'][0]/365:.1f} years)")
    print(f"  Hours with generation: {int(df['hours_with_generation'][0]):,} ({df['hours_with_generation'][0]/df['total_hours'][0]*100:.1f}%)")
    print(f"  Avg capacity factor: {df['avg_capacity_factor'][0]:.1f}%")
    print(f"  Icing hours: {int(df['icing_hours'][0]):,}")
    print()

def analyze_power_curve_deviation():
    """Analyze deviation from theoretical power curve."""
    
    print("=" * 80)
    print("📈 POWER CURVE DEVIATION ANALYSIS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Simple power curve model: P = 0.5 * ρ * A * v³ * Cp
    # For analysis: expected_CF = f(wind_speed)
    # Typical offshore wind: 
    #   3-5 m/s: 10-20% CF (ramp up)
    #   8-12 m/s: 50-80% CF (rated)
    #   >25 m/s: 0% CF (cut-out)
    
    query = """
    WITH wind_bins AS (
      SELECT
        farm_name,
        CASE
          WHEN wind_speed_ms < 3 THEN '0-3 m/s (below cut-in)'
          WHEN wind_speed_ms < 5 THEN '3-5 m/s (ramp-up)'
          WHEN wind_speed_ms < 8 THEN '5-8 m/s (partial load)'
          WHEN wind_speed_ms < 12 THEN '8-12 m/s (rated power)'
          WHEN wind_speed_ms < 15 THEN '12-15 m/s (rated+)'
          WHEN wind_speed_ms < 20 THEN '15-20 m/s (high wind)'
          WHEN wind_speed_ms < 25 THEN '20-25 m/s (near cut-out)'
          ELSE '>25 m/s (cut-out)'
        END as wind_bin,
        AVG(wind_speed_ms) as avg_wind_speed,
        COUNT(*) as hours,
        AVG(capacity_factor_pct) as actual_cf_pct,
        
        -- Theoretical CF (simplified model)
        CASE
          WHEN AVG(wind_speed_ms) < 3 THEN 0
          WHEN AVG(wind_speed_ms) < 5 THEN 15
          WHEN AVG(wind_speed_ms) < 8 THEN 40
          WHEN AVG(wind_speed_ms) < 12 THEN 70
          WHEN AVG(wind_speed_ms) < 15 THEN 85
          WHEN AVG(wind_speed_ms) < 20 THEN 95
          WHEN AVG(wind_speed_ms) < 25 THEN 90
          ELSE 0
        END as theoretical_cf_pct,
        
        SUM(CASE WHEN is_icing_event THEN 1 ELSE 0 END) as icing_hours,
        SUM(CASE WHEN is_cutout_wind THEN 1 ELSE 0 END) as cutout_hours
        
      FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_correlation`
      WHERE total_generation_mw IS NOT NULL
      GROUP BY farm_name, wind_bin
    )
    SELECT
      wind_bin,
      SUM(hours) as total_hours,
      AVG(actual_cf_pct) as avg_actual_cf,
      AVG(theoretical_cf_pct) as avg_theoretical_cf,
      AVG(actual_cf_pct) - AVG(theoretical_cf_pct) as cf_deviation,
      SUM(icing_hours) as icing_hours,
      SUM(cutout_hours) as cutout_hours
    FROM wind_bins
    GROUP BY wind_bin
    ORDER BY 
      CASE 
        WHEN wind_bin LIKE '0-%' THEN 1
        WHEN wind_bin LIKE '3-%' THEN 2
        WHEN wind_bin LIKE '5-%' THEN 3
        WHEN wind_bin LIKE '8-%' THEN 4
        WHEN wind_bin LIKE '12-%' THEN 5
        WHEN wind_bin LIKE '15-%' THEN 6
        WHEN wind_bin LIKE '20-%' THEN 7
        ELSE 8
      END
    """
    
    df = client.query(query).to_dataframe()
    
    print("Power Curve Analysis by Wind Speed Bin:\n")
    print(f"{'Wind Bin':30} {'Hours':>10} {'Actual CF':>10} {'Theory CF':>10} {'Deviation':>10}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        deviation_sign = "+" if row['cf_deviation'] > 0 else ""
        print(f"{row['wind_bin']:30} {int(row['total_hours']):>10,} "
              f"{row['avg_actual_cf']:>9.1f}% {row['avg_theoretical_cf']:>9.1f}% "
              f"{deviation_sign}{row['cf_deviation']:>9.1f}%")
    
    print()
    print("Key observations:")
    total_icing = int(df['icing_hours'].sum())
    print(f"  • Total icing hours: {total_icing:,}")
    print(f"  • Largest negative deviation indicates curtailment or performance issues")
    print(f"  • Positive deviation indicates better-than-expected performance")
    print()

def calculate_revenue_impact():
    """Calculate revenue impact from icing and curtailment."""
    
    print("=" * 80)
    print("💰 REVENUE IMPACT ANALYSIS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    WITH weather_gen AS (
      SELECT
        w.farm_name,
        w.hour,
        w.wind_speed_ms,
        w.total_generation_mw,
        w.total_capacity_mw,
        w.capacity_factor_pct,
        w.is_icing_event,
        w.is_cutout_wind,
        
        -- Estimate expected generation (simple model)
        CASE
          WHEN w.wind_speed_ms < 3 THEN 0
          WHEN w.wind_speed_ms < 5 THEN w.total_capacity_mw * 0.15
          WHEN w.wind_speed_ms < 8 THEN w.total_capacity_mw * 0.40
          WHEN w.wind_speed_ms < 12 THEN w.total_capacity_mw * 0.70
          WHEN w.wind_speed_ms < 15 THEN w.total_capacity_mw * 0.85
          WHEN w.wind_speed_ms < 20 THEN w.total_capacity_mw * 0.95
          WHEN w.wind_speed_ms < 25 THEN w.total_capacity_mw * 0.90
          ELSE 0
        END as expected_generation_mw
        
      FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_correlation` w
      WHERE w.total_generation_mw IS NOT NULL
        AND w.hour >= '2024-01-01'
    ),
    
    with_prices AS (
      SELECT
        wg.*,
        -- Get imbalance price (use system sell price as proxy)
        c.systemSellPrice as imbalance_price_gbp_per_mwh,
        
        -- Calculate lost generation
        GREATEST(0, wg.expected_generation_mw - wg.total_generation_mw) as lost_generation_mw,
        
        -- Revenue impact
        GREATEST(0, wg.expected_generation_mw - wg.total_generation_mw) * 
          COALESCE(c.systemSellPrice, 50) as revenue_loss_gbp  -- Default £50/MWh if no price
        
      FROM weather_gen wg
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs` c
        ON DATE(wg.hour) = DATE(c.settlementDate)
        AND EXTRACT(HOUR FROM wg.hour) = CAST(c.settlementPeriod / 2 AS INT64)
    )
    
    SELECT
      'ALL PERIODS' as category,
      COUNT(*) as hours,
      SUM(lost_generation_mw) as total_lost_mw,
      AVG(imbalance_price_gbp_per_mwh) as avg_price,
      SUM(revenue_loss_gbp) as total_revenue_loss_gbp
    FROM with_prices
    
    UNION ALL
    
    SELECT
      'ICING EVENTS' as category,
      COUNT(*) as hours,
      SUM(lost_generation_mw) as total_lost_mw,
      AVG(imbalance_price_gbp_per_mwh) as avg_price,
      SUM(revenue_loss_gbp) as total_revenue_loss_gbp
    FROM with_prices
    WHERE is_icing_event
    
    UNION ALL
    
    SELECT
      'CUT-OUT WIND' as category,
      COUNT(*) as hours,
      SUM(lost_generation_mw) as total_lost_mw,
      AVG(imbalance_price_gbp_per_mwh) as avg_price,
      SUM(revenue_loss_gbp) as total_revenue_loss_gbp
    FROM with_prices
    WHERE is_cutout_wind
    
    UNION ALL
    
    SELECT
      'NORMAL CONDITIONS' as category,
      COUNT(*) as hours,
      SUM(lost_generation_mw) as total_lost_mw,
      AVG(imbalance_price_gbp_per_mwh) as avg_price,
      SUM(revenue_loss_gbp) as total_revenue_loss_gbp
    FROM with_prices
    WHERE NOT is_icing_event AND NOT is_cutout_wind
    
    ORDER BY 
      CASE category
        WHEN 'ALL PERIODS' THEN 1
        WHEN 'ICING EVENTS' THEN 2
        WHEN 'CUT-OUT WIND' THEN 3
        WHEN 'NORMAL CONDITIONS' THEN 4
      END
    """
    
    df = client.query(query).to_dataframe()
    
    print("Revenue Impact Analysis (2024+):\n")
    print(f"{'Category':20} {'Hours':>10} {'Lost MW':>12} {'Avg £/MWh':>10} {'Revenue Loss':>15}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        print(f"{row['category']:20} {int(row['hours']):>10,} "
              f"{row['total_lost_mw']:>12,.0f} "
              f"£{row['avg_price']:>9.2f} "
              f"£{row['total_revenue_loss_gbp']:>14,.0f}")
    
    print()
    
    # Calculate per-farm impact
    if len(df) > 0:
        all_periods = df[df['category'] == 'ALL PERIODS'].iloc[0]
        icing = df[df['category'] == 'ICING EVENTS'].iloc[0]
        
        if all_periods['total_revenue_loss_gbp'] > 0 and icing['hours'] > 0:
            icing_pct = (icing['total_revenue_loss_gbp'] / all_periods['total_revenue_loss_gbp']) * 100
            print(f"Icing events account for {icing_pct:.1f}% of total revenue losses")
            print(f"Avg loss per icing hour: £{icing['total_revenue_loss_gbp'] / icing['hours']:,.0f}")
            print()

def export_dashboard_data():
    """Export sample data for visualization."""
    
    print("=" * 80)
    print("📊 EXPORTING DASHBOARD DATA")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Export last 30 days for a few farms
    query = """
    SELECT *
    FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_correlation`
    WHERE farm_name IN ('Hornsea One', 'Burbo Bank Extension', 'Seagreen Phase 1')
      AND hour >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    ORDER BY farm_name, hour
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        filename = f"weather_generation_dashboard_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Exported {len(df):,} rows to: {filename}")
        print()
        print(f"Sample data (first 5 rows):")
        print(df[['farm_name', 'hour', 'wind_speed_ms', 'total_generation_mw', 'capacity_factor_pct']].head())
    else:
        print("⚠️  No data to export")
    print()

def main():
    """Run complete weather-generation correlation analysis."""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "WEATHER → GENERATION CORRELATION ANALYSIS" + " " * 22 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Analyzes ERA5 weather data vs actual wind farm generation")
    print("17 mapped farms, 8,843 MW capacity, 2024-2025")
    print()
    
    try:
        # Step 1: Create correlation view
        create_weather_generation_view()
        
        # Step 2: Power curve deviation
        analyze_power_curve_deviation()
        
        # Step 3: Revenue impact
        calculate_revenue_impact()
        
        # Step 4: Export dashboard data
        export_dashboard_data()
        
        print("=" * 80)
        print("✅ WEATHER-GENERATION ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print("Created resources:")
        print("  • weather_generation_correlation view (hourly data)")
        print("  • Power curve deviation analysis")
        print("  • Revenue impact calculations")
        print("  • Dashboard CSV export")
        print()
        print("Next steps:")
        print("  1. Visualize in Google Sheets or BI tool")
        print("  2. Refine power curve model with turbine specs")
        print("  3. Add curtailment detection (grid constraints)")
        print("  4. Build automated alerts for icing + low CF")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
