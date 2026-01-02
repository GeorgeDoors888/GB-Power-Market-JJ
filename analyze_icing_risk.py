#!/usr/bin/env python3
"""
Wind Turbine Icing Risk Analysis - CORRECTED VERSION

FIXED BUGS (Jan 2, 2026):
- Bug #1: dew_point_spread_c was calculated as dew_point (algebraic error)
- Bug #2: Thresholds compared dew point instead of dew point spread
- Bug #3: Approximate formula T-(100-RH)/5 replaced with Magnus formula
- Bug #4: LAG(3) changed to time-based INTERVAL 3 HOUR for pressure changes

Implements icing risk detection using Magnus dew point spread method:
- Temperature: -10°C to +2°C (cold but not extreme)
- Dew point spread: ≤2°C (high humidity, near saturation)
- Wind speed: 6-12 m/s (moderate winds worst for icing)
- Gust factor: >1.3 (turbulent flow enhances icing)

Physical mechanisms:
1. Pressure-induced cooling at blade tips (1-3°C local drop)
2. Supercooled droplet freezing (high RH + subfreezing temps)
3. Blade tip speed amplification (60-90 m/s >> ambient wind)
4. Centrifugal shedding (competing effect at high RPM)

Magnus formula (Alduchov & Eskridge 1996):
  Td = (243.04 * gamma) / (17.625 - gamma)
  where gamma = ln(RH/100) + (17.625*T)/(243.04+T)
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_icing_risk_view():
    """Create BigQuery view for icing risk classification."""
    
    print("=" * 80)
    print("❄️  CREATING ICING RISK VIEW (MAGNUS FORMULA - FIXED)")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk` AS
    WITH base AS (
      SELECT
        farm_name,
        timestamp,
        temperature_2m_c,
        relative_humidity_2m_pct,
        wind_speed_100m_ms,
        wind_gusts_10m_ms,
        surface_pressure_hpa,
        wind_direction_100m_deg,
        
        -- Clamp RH to avoid LN(0) and RH>100 quirks
        LEAST(GREATEST(relative_humidity_2m_pct, 0.1), 100.0) AS rh_clamped
      FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
      WHERE temperature_2m_c < 10
    ),
    dew AS (
      SELECT
        *,
        -- Magnus dew point (°C) - ACCURATE near 0°C
        -- gamma = ln(RH/100) + (a*T)/(b+T)
        -- Td = (b*gamma)/(a-gamma)
        -- Constants: a=17.625, b=243.04 (Alduchov & Eskridge 1996)
        (
          243.04 * (
            LN(rh_clamped / 100.0) + (17.625 * temperature_2m_c) / (243.04 + temperature_2m_c)
          )
        ) / (
          17.625 - (
            LN(rh_clamped / 100.0) + (17.625 * temperature_2m_c) / (243.04 + temperature_2m_c)
          )
        ) AS dew_point_c
      FROM base
    ),
    pressure_3h_ago AS (
      SELECT
        d1.farm_name,
        d1.timestamp,
        d1.surface_pressure_hpa,
        -- Time-based pressure change (not row-based LAG)
        d1.surface_pressure_hpa - d2.surface_pressure_hpa AS pressure_change_3h
      FROM dew d1
      LEFT JOIN dew d2
        ON d1.farm_name = d2.farm_name
        AND d2.timestamp = TIMESTAMP_SUB(d1.timestamp, INTERVAL 3 HOUR)
    )
    SELECT
      d.farm_name,
      d.timestamp,
      
      -- Original weather variables
      d.temperature_2m_c,
      d.relative_humidity_2m_pct,
      d.wind_speed_100m_ms,
      d.wind_gusts_10m_ms,
      d.surface_pressure_hpa,
      d.wind_direction_100m_deg,
      
      -- Derived icing indicators (FIXED: correct spread calculation)
      d.dew_point_c,
      (d.temperature_2m_c - d.dew_point_c) AS dew_point_spread_c,
      
      SAFE_DIVIDE(d.wind_gusts_10m_ms, NULLIF(d.wind_speed_100m_ms, 0)) AS gust_factor,
      
      -- Time-based pressure change (not row-based LAG)
      p.pressure_change_3h,
      
      80.0 AS estimated_blade_tip_speed_ms,
      
      -- Icing risk classification (FIXED: uses dew point SPREAD)
      CASE
        WHEN d.temperature_2m_c BETWEEN -10 AND 2
         AND (d.temperature_2m_c - d.dew_point_c) <= 2
         AND d.wind_speed_100m_ms BETWEEN 6 AND 12
         AND SAFE_DIVIDE(d.wind_gusts_10m_ms, NULLIF(d.wind_speed_100m_ms, 0)) > 1.3
        THEN 'HIGH'
        
        WHEN d.temperature_2m_c BETWEEN -5 AND 5
         AND (d.temperature_2m_c - d.dew_point_c) <= 5
         AND d.wind_speed_100m_ms BETWEEN 4 AND 15
        THEN 'MEDIUM'
        
        ELSE 'LOW'
      END AS icing_risk_level,
      
      -- Operational impact flags (FIXED: spread uses T - Td)
      CASE
        WHEN d.temperature_2m_c < 0
         AND d.relative_humidity_2m_pct > 90
         AND d.wind_speed_100m_ms BETWEEN 6 AND 12
        THEN TRUE ELSE FALSE
      END AS supercooled_droplet_conditions,
      
      CASE
        WHEN d.temperature_2m_c BETWEEN -2 AND 2
         AND (d.temperature_2m_c - d.dew_point_c) <= 1
        THEN TRUE ELSE FALSE
      END AS blade_tip_cooling_risk,
      
      CASE
        WHEN SAFE_DIVIDE(d.wind_gusts_10m_ms, NULLIF(d.wind_speed_100m_ms, 0)) > 1.4
         AND d.temperature_2m_c < 5
        THEN TRUE ELSE FALSE
      END AS turbulent_icing_risk
    FROM dew d
    LEFT JOIN pressure_3h_ago p
      ON d.farm_name = p.farm_name AND d.timestamp = p.timestamp
    """
    
    print("Creating view: wind_icing_risk")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ View created successfully")
    print()
    
    # Test view
    test_query = """
    SELECT 
        COUNT(*) as total_observations,
        COUNT(DISTINCT farm_name) as farms,
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
    """
    
    df = client.query(test_query).to_dataframe()
    print("View validation:")
    print(f"  Total observations: {int(df['total_observations'][0]):,}")
    print(f"  Farms: {int(df['farms'][0])}")
    print(f"  Date range: {df['earliest'][0]} to {df['latest'][0]}")
    print()

def analyze_icing_risk_distribution():
    """Analyze distribution of icing risk levels."""
    
    print("=" * 80)
    print("📊 ICING RISK DISTRIBUTION (21 FARMS, 2020-2025)")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    SELECT 
        icing_risk_level,
        COUNT(*) as hours,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage,
        AVG(temperature_2m_c) as avg_temp,
        AVG(dew_point_spread_c) as avg_dew_point_spread,
        AVG(wind_speed_100m_ms) as avg_wind_speed,
        AVG(gust_factor) as avg_gust_factor
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
    GROUP BY icing_risk_level
    ORDER BY 
        CASE icing_risk_level
            WHEN 'HIGH' THEN 1
            WHEN 'MEDIUM' THEN 2
            WHEN 'LOW' THEN 3
        END
    """
    
    df = client.query(query).to_dataframe()
    
    print("Icing Risk Level Distribution:\n")
    for _, row in df.iterrows():
        print(f"{row['icing_risk_level']:8} {int(row['hours']):>10,} hours ({row['percentage']:>5.2f}%)")
        print(f"         Avg temp: {row['avg_temp']:.1f}°C, Dew point spread: {row['avg_dew_point_spread']:.2f}°C")
        print(f"         Avg wind: {row['avg_wind_speed']:.1f} m/s, Gust factor: {row['avg_gust_factor']:.2f}")
        print()
    
    # High-risk events by farm
    print("=" * 80)
    print("❄️  HIGH ICING RISK BY FARM")
    print("=" * 80)
    print()
    
    query2 = """
    SELECT 
        farm_name,
        COUNT(*) as high_risk_hours,
        MIN(timestamp) as first_high_risk,
        MAX(timestamp) as last_high_risk,
        AVG(temperature_2m_c) as avg_temp,
        AVG(dew_point_spread_c) as avg_spread
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
    WHERE icing_risk_level = 'HIGH'
    GROUP BY farm_name
    ORDER BY high_risk_hours DESC
    """
    
    df2 = client.query(query2).to_dataframe()
    
    if len(df2) > 0:
        print(f"Farms with HIGH icing risk events: {len(df2)}\n")
        for idx, row in df2.head(10).iterrows():
            print(f"{row['farm_name']:30} {int(row['high_risk_hours']):>6,} hours")
            print(f"  First/Last: {row['first_high_risk']} to {row['last_high_risk']}")
            print(f"  Avg: {row['avg_temp']:.1f}°C, Spread: {row['avg_spread']:.2f}°C")
            print()
    else:
        print("⚠️  No HIGH icing risk events detected (possible - UK climate generally mild)")
        print()

def analyze_icing_mechanism_flags():
    """Analyze specific icing mechanism flags."""
    
    print("=" * 80)
    print("🔬 ICING MECHANISM ANALYSIS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    SELECT 
        SUM(CASE WHEN supercooled_droplet_conditions THEN 1 ELSE 0 END) as supercooled_droplet_hours,
        SUM(CASE WHEN blade_tip_cooling_risk THEN 1 ELSE 0 END) as blade_tip_cooling_hours,
        SUM(CASE WHEN turbulent_icing_risk THEN 1 ELSE 0 END) as turbulent_icing_hours,
        COUNT(*) as total_hours
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
    WHERE icing_risk_level IN ('HIGH', 'MEDIUM')
    """
    
    df = client.query(query).to_dataframe()
    
    total = int(df['total_hours'][0])
    supercooled = int(df['supercooled_droplet_hours'][0])
    blade_tip = int(df['blade_tip_cooling_hours'][0])
    turbulent = int(df['turbulent_icing_hours'][0])
    
    print(f"Among {total:,} MEDIUM/HIGH risk hours:")
    print()
    print(f"1️⃣  SUPERCOOLED DROPLET CONDITIONS: {supercooled:,} hours ({supercooled/total*100:.1f}%)")
    print(f"   Criteria: T < 0°C, RH > 90%, Wind 6-12 m/s")
    print(f"   Impact: Instant freezing on blade contact → rapid ice buildup")
    print()
    print(f"2️⃣  BLADE TIP COOLING RISK: {blade_tip:,} hours ({blade_tip/total*100:.1f}%)")
    print(f"   Criteria: T ≈ 0°C (±2°C), Dew point spread ≤ 1°C")
    print(f"   Impact: Pressure drop at blade tip → local temp < 0°C → ice forms")
    print()
    print(f"3️⃣  TURBULENT ICING RISK: {turbulent:,} hours ({turbulent/total*100:.1f}%)")
    print(f"   Criteria: Gust factor > 1.4, T < 5°C")
    print(f"   Impact: High turbulence → uneven ice accretion → imbalance")
    print()

def correlate_with_generation():
    """Correlate icing risk with generation data (if available)."""
    
    print("=" * 80)
    print("⚙️  CORRELATING ICING RISK WITH WIND GENERATION")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Check if we have generation data overlapping with icing risk
    query = """
    WITH icing_periods AS (
      SELECT 
        farm_name,
        DATE(timestamp) as icing_date,
        COUNT(*) as icing_hours
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
      WHERE icing_risk_level = 'HIGH'
      GROUP BY farm_name, icing_date
    ),
    
    generation_data AS (
      SELECT 
        bmUnit,
        CAST(settlementDate AS DATE) as gen_date,
        AVG(levelTo) as avg_generation_mw,
        MAX(levelTo) as max_generation_mw
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_pn`
      WHERE CAST(settlementDate AS DATE) >= '2022-01-01'
      GROUP BY bmUnit, gen_date
    )
    
    SELECT 
        'Analysis not yet possible' as note,
        'Need wind farm to BMU mapping' as action,
        'Use wind_farm_to_bmu table' as solution
    """
    
    df = client.query(query).to_dataframe()
    
    print("⚠️  Generation correlation requires wind farm to BM unit mapping")
    print()
    print("Next steps:")
    print("  1. Join wind_icing_risk with wind_farm_to_bmu (farm → BMU IDs)")
    print("  2. Join with bmrs_pn (BMU → actual generation)")
    print("  3. Compare generation during HIGH icing risk vs normal conditions")
    print("  4. Calculate icing-related yield losses")
    print()
    print("Expected findings:")
    print("  - Power curve deviations during HIGH icing risk")
    print("  - Capacity factor drops (5-20% typical)")
    print("  - False anemometer readings")
    print("  - Turbine shutdowns (safety systems)")
    print()

def export_sample_high_risk_events():
    """Export sample high-risk icing events for documentation."""
    
    print("=" * 80)
    print("📝 EXPORTING SAMPLE HIGH-RISK EVENTS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    SELECT 
        farm_name,
        timestamp,
        temperature_2m_c,
        dew_point_c,
        dew_point_spread_c,
        wind_speed_100m_ms,
        wind_gusts_10m_ms,
        gust_factor,
        surface_pressure_hpa,
        icing_risk_level,
        supercooled_droplet_conditions,
        blade_tip_cooling_risk,
        turbulent_icing_risk
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
    WHERE icing_risk_level = 'HIGH'
    ORDER BY timestamp DESC
    LIMIT 100
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        filename = f"icing_risk_high_events_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Exported {len(df)} HIGH icing risk events to: {filename}")
        print()
        print("Sample events:")
        print(df.head(5).to_string(index=False))
    else:
        print("⚠️  No HIGH icing risk events found")
        print("Note: UK offshore wind farms may have minimal icing risk")
        print("      (warmer maritime climate vs onshore/northern locations)")
    print()

def main():
    """Run complete icing risk analysis."""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "WIND TURBINE ICING RISK ANALYSIS" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Dataset: era5_weather_data_complete (21 farms, 2020-2025)")
    print("Method: Dew point spread + blade tip cooling + turbulence factors")
    print()
    
    try:
        # Step 1: Create view
        create_icing_risk_view()
        
        # Step 2: Analyze distribution
        analyze_icing_risk_distribution()
        
        # Step 3: Analyze mechanisms
        analyze_icing_mechanism_flags()
        
        # Step 4: Correlate with generation (preliminary)
        correlate_with_generation()
        
        # Step 5: Export sample events
        export_sample_high_risk_events()
        
        print("=" * 80)
        print("✅ ICING RISK ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Review exported CSV for high-risk event validation")
        print("  2. Correlate with actual generation drops (requires BMU mapping)")
        print("  3. Add icing risk section to WIND_YIELD_DROPS_UPSTREAM_ANALYSIS.md")
        print("  4. Consider adding icing alerts to dashboard (rows 65-70)")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
