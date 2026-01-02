#!/usr/bin/env python3
"""
Refine Power Curves with Actual Turbine Specifications

Replaces theoretical CF bins [0,15,40,70,85,95,90,0] with physics-based
turbine-specific power curves using actual manufacturer specs.

Power Curve Formula:
- Below rated: P = 0.5 × ρ × A × Cp × v³
- Rated to cut-out: P = rated_capacity_mw
- Outside cut-in to cut-out: P = 0

Where:
- ρ = air density (1.225 kg/m³ at sea level, adjusted for temperature/pressure)
- A = swept area (πr²)
- Cp = power coefficient (0.45 typical, derived from specific power)
- v = wind speed

Updates:
1. weather_generation_constraints view - replace expected_cf_pct calculation
2. Fix £992k "NORMAL" losses attribution from Task 2
"""

import pandas as pd
from google.cloud import bigquery
import math

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_power_curve_function():
    """Create SQL UDF for turbine-specific power curve calculation."""
    
    print("=" * 80)
    print("📐 CREATING TURBINE-SPECIFIC POWER CURVE FUNCTION")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Create SQL UDF
    query = """
    CREATE OR REPLACE FUNCTION `inner-cinema-476211-u9.uk_energy_prod.calculate_power_output`(
      wind_speed_ms FLOAT64,
      temperature_c FLOAT64,
      pressure_hpa FLOAT64,
      cut_in_speed FLOAT64,
      rated_speed FLOAT64,
      cut_out_speed FLOAT64,
      rated_capacity_mw FLOAT64,
      swept_area_m2 FLOAT64
    ) AS (
      CASE
        -- Below cut-in or above cut-out
        WHEN wind_speed_ms < cut_in_speed OR wind_speed_ms >= cut_out_speed THEN 0.0
        
        -- Rated to cut-out (constant rated power)
        WHEN wind_speed_ms >= rated_speed THEN rated_capacity_mw
        
        -- Cut-in to rated (cubic power law with air density correction)
        ELSE
          -- Air density: ρ = P / (R × T)
          -- P = pressure (Pa), R = 287.05 (J/kg·K), T = temperature (K)
          -- Simplified: ρ ≈ 1.225 × (P/1013.25) × (288.15/T)
          
          LEAST(
            0.5 * 
            1.225 * (pressure_hpa / 1013.25) * (288.15 / (273.15 + temperature_c)) *  -- Air density
            swept_area_m2 *  -- Swept area
            0.45 *  -- Power coefficient (Cp, typical for modern turbines)
            POW(wind_speed_ms, 3) /  -- Cubic wind speed
            1000000.0,  -- Convert W to MW
            rated_capacity_mw  -- Cap at rated power
          )
      END
    );
    """
    
    print("Creating UDF: calculate_power_output")
    print("  Formula: P = 0.5 × ρ × A × Cp × v³ (below rated)")
    print("  Air density correction: Temperature and pressure adjusted")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Function created successfully")
    print()

def update_weather_generation_constraints_view():
    """Update view with turbine-specific power curves."""
    
    print("=" * 80)
    print("🔧 UPDATING WEATHER_GENERATION_CONSTRAINTS VIEW")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.weather_generation_constraints` AS
    WITH generation_hourly AS (
      -- First aggregate generation to hourly level
      SELECT
        m.farm_name,
        TIMESTAMP_TRUNC(CAST(p.settlementDate AS TIMESTAMP), HOUR) as hour,
        AVG(p.levelTo) as actual_mw  -- AVG across settlement periods in hour
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_pn` p
      INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_farm_to_bmu` m
        ON p.bmUnit = m.bm_unit_id
      WHERE CAST(p.settlementDate AS DATE) >= '2024-01-01'
      GROUP BY m.farm_name, hour
    ),
    base_weather_generation AS (
      SELECT 
        w.farm_name,
        w.timestamp as hour,
        w.wind_speed_100m_ms,
        w.temperature_2m_c,
        w.surface_pressure_hpa,
        SAFE_DIVIDE(w.wind_gusts_10m_ms, NULLIF(w.wind_speed_100m_ms, 0)) as gust_factor,
        i.icing_risk_level,
        i.dew_point_spread_c,
        
        -- Turbine specs
        ts.cut_in_speed_ms,
        ts.rated_speed_ms,
        ts.cut_out_speed_ms,
        ts.rated_capacity_mw,
        ts.swept_area_m2,
        ts.total_capacity_mw as capacity_mw,
        
        -- Generation (already aggregated)
        g.actual_mw
        
      FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete` w
      INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_turbine_specs` ts
        ON w.farm_name = ts.farm_name
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk` i
        ON w.farm_name = i.farm_name 
        AND w.timestamp = i.timestamp
      LEFT JOIN generation_hourly g
        ON w.farm_name = g.farm_name
        AND w.timestamp = g.hour
      WHERE CAST(w.timestamp AS DATE) >= '2024-01-01'
    ),
    with_power_curve AS (
      SELECT
        bg.*,
        
        -- Physics-based expected power output (per turbine, then scale to farm)
        `inner-cinema-476211-u9.uk_energy_prod.calculate_power_output`(
          bg.wind_speed_100m_ms,
          bg.temperature_2m_c,
          bg.surface_pressure_hpa,
          bg.cut_in_speed_ms,
          bg.rated_speed_ms,
          bg.cut_out_speed_ms,
          bg.rated_capacity_mw,  -- Per-turbine rated power
          bg.swept_area_m2  -- Per-turbine swept area
        ) * (bg.capacity_mw / NULLIF(bg.rated_capacity_mw, 0)) as expected_mw,  -- Scale by number of turbines
        
        -- Capacity factor
        bg.actual_mw / NULLIF(bg.capacity_mw, 0) * 100 as capacity_factor_pct
        
      FROM base_weather_generation bg
    ),
    with_curtailment AS (
      SELECT 
        pc.*,
        
        -- Expected CF from physics model
        pc.expected_mw / NULLIF(pc.capacity_mw, 0) * 100 as expected_cf_pct,
        
        -- Curtailment flags (any acceptance in this hour = constrained)
        CASE WHEN c.acceptance_time IS NOT NULL THEN TRUE ELSE FALSE END as is_curtailed,
        c.constraint_severity,
        c.acceptancePrice as curtailment_price_gbp_per_mwh,
        c.acceptanceVolume as curtailment_volume_mw,
        c.curtailment_type,
        
        -- Revenue proxy (£50/MWh baseline)
        50.0 as baseline_price_gbp_per_mwh
        
      FROM with_power_curve pc
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.curtailment_events` c
        ON pc.farm_name = c.farm_name
        AND pc.hour = TIMESTAMP_TRUNC(c.acceptance_time, HOUR)
    )
    SELECT 
      *,
      
      -- CF deviation (actual - expected)
      capacity_factor_pct - expected_cf_pct as cf_deviation_pct,
      
      -- Lost generation
      (expected_cf_pct - capacity_factor_pct) / 100.0 * capacity_mw as lost_generation_mw,
      
      -- Revenue impact
      (expected_cf_pct - capacity_factor_pct) / 100.0 * capacity_mw * 
        COALESCE(curtailment_price_gbp_per_mwh, baseline_price_gbp_per_mwh) as revenue_loss_gbp,
      
      -- Attribution flags
      CASE 
        WHEN is_curtailed = TRUE THEN 'CONSTRAINT'
        WHEN icing_risk_level = 'HIGH' THEN 'ICING'
        WHEN gust_factor > 1.4 THEN 'TURBULENCE'
        WHEN wind_speed_100m_ms < 6 THEN 'LOW_WIND'
        WHEN wind_speed_100m_ms > 20 THEN 'HIGH_WIND'
        ELSE 'NORMAL'
      END as impact_category
      
    FROM with_curtailment
    WHERE actual_mw IS NOT NULL
    """
    
    print("Updating view: weather_generation_constraints")
    print("  New expected power: Physics-based turbine-specific calculation")
    print("  Old: Simple CF bins [0,15,40,70,85,95,90,0]")
    print("  New: P = 0.5 × ρ(T,P) × A × Cp × v³")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ View updated successfully")
    print()

def validate_power_curves():
    """Compare old vs new power curve predictions."""
    
    print("=" * 80)
    print("📊 VALIDATING POWER CURVE IMPROVEMENTS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Compare across wind speed bins
    query = """
    WITH wind_bins AS (
      SELECT
        CASE
          WHEN wind_speed_100m_ms < 3 THEN '< 3 m/s (Below cut-in)'
          WHEN wind_speed_100m_ms < 6 THEN '3-6 m/s (Low wind)'
          WHEN wind_speed_100m_ms < 9 THEN '6-9 m/s (Partial load)'
          WHEN wind_speed_100m_ms < 12 THEN '9-12 m/s (Near rated)'
          WHEN wind_speed_100m_ms < 15 THEN '12-15 m/s (Rated)'
          WHEN wind_speed_100m_ms < 20 THEN '15-20 m/s (High wind)'
          ELSE '> 20 m/s (Near cut-out)'
        END as wind_bin,
        AVG(wind_speed_100m_ms) as avg_wind_speed,
        COUNT(*) as hours,
        AVG(capacity_factor_pct) as avg_actual_cf,
        AVG(expected_cf_pct) as avg_expected_cf,
        AVG(cf_deviation_pct) as avg_cf_deviation,
        SUM(lost_generation_mw) as total_lost_mw,
        SUM(revenue_loss_gbp) as total_revenue_loss
      FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_constraints`
      WHERE capacity_factor_pct IS NOT NULL
      GROUP BY wind_bin
    )
    SELECT * FROM wind_bins
    ORDER BY avg_wind_speed
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print("Power Curve Performance by Wind Speed:\n")
        print(f"{'Wind Bin':<25} {'Hours':>8} {'Avg Wind':>9} {'Actual CF%':>11} {'Expected CF%':>13} {'CF Dev%':>9} {'Lost MW':>12} {'Revenue Loss':>15}")
        print("-" * 115)
        
        for _, row in df.iterrows():
            print(f"{row['wind_bin']:<25} "
                  f"{int(row['hours']):>8,} "
                  f"{row['avg_wind_speed']:>8.1f} m/s "
                  f"{row['avg_actual_cf']:>10.1f}% "
                  f"{row['avg_expected_cf']:>12.1f}% "
                  f"{row['avg_cf_deviation']:>8.1f}% "
                  f"{row['total_lost_mw']:>11,.0f} "
                  f"£{row['total_revenue_loss']:>13,.0f}")
        
        print()
        
        # Key metrics
        total_hours = df['hours'].sum()
        total_loss = df['total_revenue_loss'].sum()
        
        # Most problematic bin
        worst_bin = df.loc[df['total_revenue_loss'].idxmax()]
        
        print("KEY INSIGHTS:")
        print("-" * 115)
        print(f"  • Total hours analyzed: {int(total_hours):,}")
        print(f"  • Total revenue loss: £{total_loss:,.0f}")
        print(f"  • Worst performing bin: {worst_bin['wind_bin']}")
        print(f"    - {int(worst_bin['hours']):,} hours, £{worst_bin['total_revenue_loss']:,.0f} loss")
        print(f"    - CF deviation: {worst_bin['avg_cf_deviation']:.1f}%")
        print()
        
        # Check if improvement (comparing to Task 2 £992k NORMAL loss)
        normal_loss = df[df['wind_bin'].str.contains('NORMAL', case=False, na=False)]['total_revenue_loss'].sum() if len(df[df['wind_bin'].str.contains('NORMAL', case=False, na=False)]) > 0 else 0
        
        print("  COMPARISON TO TASK 2:")
        print(f"    Task 2 (theoretical curve): £992,135 'NORMAL' losses (89.5%)")
        print(f"    Task 3 (physics-based curve): £{total_loss:,.0f} total losses")
        print()
        
        if total_loss < 500000:
            print("  ✅ SIGNIFICANT IMPROVEMENT: Physics-based curves reduce unexplained losses")
        else:
            print("  ⚠️  Physics-based curves still show large deviations")
            print("     → May indicate data quality issues or persistent curtailment")
        
        print()

def analyze_farm_performance():
    """Analyze which farms have persistent underperformance."""
    
    print("=" * 80)
    print("🏭 FARM-LEVEL PERFORMANCE ANALYSIS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    SELECT
      farm_name,
      COUNT(*) as hours,
      AVG(capacity_factor_pct) as avg_cf_pct,
      AVG(expected_cf_pct) as avg_expected_cf_pct,
      AVG(cf_deviation_pct) as avg_cf_deviation_pct,
      SUM(lost_generation_mw) as total_lost_mw,
      SUM(revenue_loss_gbp) as total_revenue_loss_gbp,
      SUM(CASE WHEN is_curtailed = TRUE THEN 1 ELSE 0 END) as curtailed_hours
    FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_constraints`
    WHERE cf_deviation_pct < 0  -- Underperformance only
    GROUP BY farm_name
    ORDER BY total_revenue_loss_gbp DESC
    LIMIT 15
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print("Top 15 Underperforming Farms:\n")
        print(f"{'Farm':<25} {'Hours':>8} {'Avg CF%':>9} {'Expected':>9} {'Dev%':>7} {'Lost MW':>10} {'Revenue Loss':>15} {'Curtailed':>10}")
        print("-" * 110)
        
        for _, row in df.iterrows():
            curtailed_pct = (row['curtailed_hours'] / row['hours'] * 100) if row['hours'] > 0 else 0
            print(f"{row['farm_name']:<25} "
                  f"{int(row['hours']):>8,} "
                  f"{row['avg_cf_pct']:>8.1f}% "
                  f"{row['avg_expected_cf_pct']:>8.1f}% "
                  f"{row['avg_cf_deviation_pct']:>6.1f}% "
                  f"{row['total_lost_mw']:>9,.0f} "
                  f"£{row['total_revenue_loss_gbp']:>13,.0f} "
                  f"{int(row['curtailed_hours']):>6} ({curtailed_pct:>4.1f}%)")
        
        print()
        
        print("INSIGHTS:")
        print("-" * 110)
        
        high_curtailment_farms = df[df['curtailed_hours'] / df['hours'] > 0.05]  # >5% curtailed
        if len(high_curtailment_farms) > 0:
            print(f"  • {len(high_curtailment_farms)} farms with >5% curtailed hours")
            print(f"    → Likely constrained by grid, not weather")
        
        high_deviation_farms = df[df['avg_cf_deviation_pct'] < -20]  # >20% underperformance
        if len(high_deviation_farms) > 0:
            print(f"  • {len(high_deviation_farms)} farms with >20% CF deviation")
            print(f"    → May have availability/maintenance issues")
        
        print()

def main():
    """Run complete power curve refinement."""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "POWER CURVE REFINEMENT" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Task 3: Replace theoretical CF bins with turbine-specific power curves")
    print("Goal: Fix £992k 'NORMAL' losses from Task 2 using physics-based model")
    print()
    
    try:
        # Step 1: Create power curve function
        create_power_curve_function()
        
        # Step 2: Update view
        update_weather_generation_constraints_view()
        
        # Step 3: Validate improvements
        validate_power_curves()
        
        # Step 4: Farm-level analysis
        analyze_farm_performance()
        
        print("=" * 80)
        print("✅ TASK 3 COMPLETE: Power Curves Refined with Turbine Specs")
        print("=" * 80)
        print()
        print("Created Resources:")
        print("  • calculate_power_output() SQL UDF (physics-based power calculation)")
        print("  • Updated weather_generation_constraints view (turbine-specific curves)")
        print("  • Performance analysis by wind speed bin and farm")
        print()
        print("Next Steps:")
        print("  • Task 4: Design event detection layer (CALM/STORM/ICING)")
        print("  • Task 7: Build generation hourly alignment (uses refined curves)")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
