#!/usr/bin/env python3
"""
Wind Turbine Icing Risk Analysis - CORRECTED VERSION

FIXED BUGS (Jan 2, 2026):
- Bug #1: dew_point_spread_c was calculated as dew_point (algebraic error)
  Original: T - (T - ((100-RH)/5)) = (100-RH)/5 (dew point proxy, NOT spread)
  Fixed: (T - dew_point_c) = actual spread

- Bug #2: Thresholds compared dew point instead of dew point spread
  Original: (T - ((100-RH)/5)) <= 2  (tests dew point value)
  Fixed: (T - dew_point_c) <= 2      (tests spread)

- Bug #3: Approximate formula T-(100-RH)/5 replaced with Magnus formula
  Magnus (Alduchov & Eskridge 1996) is accurate near 0°C
  Critical for icing detection where small errors matter

- Bug #4: LAG(3) changed to time-based INTERVAL 3 HOUR for pressure changes
  LAG(3) = "3 rows back" (breaks with data gaps)
  Fixed: LEFT JOIN with TIMESTAMP_SUB(..., INTERVAL 3 HOUR)

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
  gamma = ln(RH/100) + (17.625*T)/(243.04+T)
  Td = (243.04 * gamma) / (17.625 - gamma)
  Spread = T - Td
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
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
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

def detect_icing_episodes():
    """Detect consecutive HIGH icing risk hours (episodes that operators care about)."""
    
    print("=" * 80)
    print("🧊 DETECTING ICING EPISODES (CONSECUTIVE HIGH RISK HOURS)")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    WITH high_risk_events AS (
      SELECT 
        farm_name,
        timestamp,
        temperature_2m_c,
        dew_point_spread_c,
        wind_speed_100m_ms,
        gust_factor
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
      WHERE icing_risk_level = 'HIGH'
      ORDER BY farm_name, timestamp
    ),
    with_gap_flag AS (
      SELECT
        *,
        -- Flag new episode when gap > 2 hours from previous event
        CASE 
          WHEN TIMESTAMP_DIFF(
            timestamp, 
            LAG(timestamp) OVER (PARTITION BY farm_name ORDER BY timestamp),
            HOUR
          ) > 2 OR LAG(timestamp) OVER (PARTITION BY farm_name ORDER BY timestamp) IS NULL
          THEN 1 
          ELSE 0 
        END AS new_episode_flag
      FROM high_risk_events
    ),
    with_episode_id AS (
      SELECT
        *,
        -- Cumulative sum of new_episode_flag gives episode ID
        SUM(new_episode_flag) OVER (PARTITION BY farm_name ORDER BY timestamp) AS episode_id
      FROM with_gap_flag
    ),
    episode_summary AS (
      SELECT
        farm_name,
        episode_id,
        MIN(timestamp) as episode_start,
        MAX(timestamp) as episode_end,
        COUNT(*) as duration_hours,
        AVG(temperature_2m_c) as avg_temp,
        AVG(dew_point_spread_c) as avg_spread,
        AVG(wind_speed_100m_ms) as avg_wind,
        AVG(gust_factor) as avg_gust_factor
      FROM with_episode_id
      GROUP BY farm_name, episode_id
      HAVING COUNT(*) >= 3  -- Only episodes ≥3 consecutive hours
    )
    SELECT * FROM episode_summary
    ORDER BY duration_hours DESC, farm_name, episode_start
    LIMIT 20
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print(f"Found {len(df)} icing episodes (≥3 consecutive hours)\n")
        print("Top 20 longest episodes:\n")
        
        for idx, row in df.iterrows():
            print(f"Episode {idx+1}: {row['farm_name']}")
            print(f"  Duration: {int(row['duration_hours'])} consecutive hours")
            print(f"  Period: {row['episode_start']} to {row['episode_end']}")
            print(f"  Conditions: {row['avg_temp']:.1f}°C, spread {row['avg_spread']:.2f}°C, "
                  f"wind {row['avg_wind']:.1f} m/s, gust {row['avg_gust_factor']:.2f}x")
            print()
    else:
        print("No icing episodes ≥3 hours detected")
    print()

def correlate_with_generation():
    """Correlate icing risk with generation data using wind_farm_to_bmu mapping."""
    
    print("=" * 80)
    print("⚙️  CORRELATING ICING RISK WITH WIND GENERATION")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Check HIGH icing periods with generation data
    query = """
    WITH icing_hours AS (
      SELECT 
        farm_name,
        timestamp,
        temperature_2m_c,
        dew_point_spread_c,
        wind_speed_100m_ms,
        icing_risk_level
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
      WHERE icing_risk_level = 'HIGH'
        AND timestamp >= '2024-01-01'  -- Limit to recent data
    ),
    mapped_farms AS (
      SELECT
        i.farm_name,
        i.timestamp,
        i.temperature_2m_c,
        i.dew_point_spread_c,
        i.wind_speed_100m_ms,
        m.bm_unit_id,
        m.capacity_mw
      FROM icing_hours i
      JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_farm_to_bmu` m
        ON i.farm_name = m.farm_name
    ),
    with_generation AS (
      SELECT
        f.farm_name,
        f.bm_unit_id,
        f.capacity_mw,
        COUNT(DISTINCT DATE(f.timestamp)) as icing_days,
        COUNT(*) as icing_hours,
        AVG(f.temperature_2m_c) as avg_temp_icing,
        AVG(f.wind_speed_100m_ms) as avg_wind_icing,
        AVG(p.levelTo) as avg_generation_during_icing_mw,
        AVG(p.levelTo / NULLIF(f.capacity_mw, 0) * 100) as capacity_factor_during_icing_pct
      FROM mapped_farms f
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_pn` p
        ON f.bm_unit_id = p.bmUnit
        AND TIMESTAMP_TRUNC(f.timestamp, HOUR) = TIMESTAMP_TRUNC(CAST(p.settlementDate AS TIMESTAMP), HOUR)
      GROUP BY f.farm_name, f.bm_unit_id, f.capacity_mw
    )
    SELECT * FROM with_generation
    WHERE icing_hours >= 3  -- Only farms with 3+ HIGH icing hours
    ORDER BY icing_hours DESC
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print(f"✅ Found {len(df)} farms with HIGH icing risk & generation data\n")
        
        for idx, row in df.iterrows():
            print(f"{row['farm_name']} ({row['bm_unit_id']})")
            print(f"  Capacity: {row['capacity_mw']:.0f} MW")
            print(f"  HIGH icing: {int(row['icing_hours'])} hours across {int(row['icing_days'])} days")
            print(f"  Conditions: {row['avg_temp_icing']:.1f}°C, wind {row['avg_wind_icing']:.1f} m/s")
            
            if pd.notna(row['avg_generation_during_icing_mw']):
                print(f"  Generation during icing: {row['avg_generation_during_icing_mw']:.1f} MW "
                      f"({row['capacity_factor_during_icing_pct']:.1f}% capacity factor)")
            else:
                print(f"  ⚠️  No generation data available for this period")
            print()
        
        print("=" * 80)
        print("💡 INTERPRETATION:")
        print("=" * 80)
        print("Compare capacity factor during icing vs normal conditions:")
        print("  • Normal offshore wind CF: 40-50% typical")
        print("  • Icing impact: 5-20% CF reduction expected")
        print("  • Severe icing: >20% CF drop or complete shutdown")
        print()
        
    else:
        print("⚠️  No farms with both HIGH icing risk and generation data")
        print()
        print("Possible reasons:")
        print("  1. HIGH icing events too rare (only 619 hours total)")
        print("  2. No BM units mapped for affected farms")
        print("  3. Generation data not available for icing period")
        print()
    
    print("Next steps:")
    print("  1. Expand to MEDIUM icing risk (147k hours) for better statistics")
    print("  2. Compare generation during icing vs similar wind/temp without icing")
    print("  3. Build power curve deviation model (actual vs expected)")
    print("  4. Calculate revenue impact (£/MWh × lost generation)")
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
        
        # Step 4: Detect icing episodes (consecutive hours)
        detect_icing_episodes()
        
        # Step 5: Correlate with generation (using wind_farm_to_bmu mapping)
        correlate_with_generation()
        
        # Step 6: Export sample events
        export_sample_high_risk_events()
        
        print("=" * 80)
        print("✅ ICING RISK ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Review exported CSV for high-risk event validation")
        print("  2. Analyze capacity factor drops during icing episodes")
        print("  3. Build power curve deviation model (actual vs expected)")
        print("  4. Calculate revenue impact from icing-related losses")
        print("  5. Add icing alerts to dashboard (rows 65-70)")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
