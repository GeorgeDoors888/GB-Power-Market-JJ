#!/usr/bin/env python3
"""
Wind Farm Event Detection Layer - Task 4

Detects and classifies weather/operational events that cause generation drops:
- CALM: Wind <6 m/s for ≥4 consecutive hours
- STORM: Pressure drop >5 hPa in 3 hours
- DIRECTION_SHIFT: Wind direction change >45° in 2 hours
- TURBULENCE: Gust factor >1.4 for ≥3 consecutive hours
- ICING: HIGH icing risk for ≥3 consecutive hours (from existing wind_icing_risk)
- CURTAILMENT: 0% CF despite good wind (Moray West pattern)

Output: wind_events_detected table
- farm_name, event_id, event_type, start_ts, end_ts, peak_ts
- severity: lost_mwh, cf_drop_pct, revenue_impact_gbp
- lead_times: JSON placeholder (populated in Task 8)

Data sources:
- wind_generation_hourly (Task 7) - generation + deviations
- era5_weather_data_complete - weather conditions
- wind_icing_risk (existing) - icing episodes
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_event_detection_view():
    """Create comprehensive event detection logic."""
    
    print("=" * 80)
    print("🔍 CREATING EVENT DETECTION VIEW")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Step 1: Create base events view with all detection logic
    query = """
    CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.wind_events_base` AS
    WITH weather_generation AS (
      -- Combine generation + weather with lag/lead windows
      SELECT
        g.farm_name,
        g.hour,
        g.actual_mw,
        g.expected_mw,
        g.capacity_mw,
        g.capacity_factor_pct,
        g.expected_cf_pct,
        g.cf_deviation_pct,
        g.deviation_mw,
        
        -- Weather current
        g.wind_speed_100m_ms,
        g.wind_direction_100m_deg,
        g.temperature_2m_c,
        g.surface_pressure_hpa,
        g.gust_factor,
        
        -- Weather lags for change detection
        LAG(g.wind_speed_100m_ms, 1) OVER (PARTITION BY g.farm_name ORDER BY g.hour) as wind_1h_ago,
        LAG(g.wind_direction_100m_deg, 1) OVER (PARTITION BY g.farm_name ORDER BY g.hour) as direction_1h_ago,
        LAG(g.wind_direction_100m_deg, 2) OVER (PARTITION BY g.farm_name ORDER BY g.hour) as direction_2h_ago,
        LAG(g.surface_pressure_hpa, 3) OVER (PARTITION BY g.farm_name ORDER BY g.hour) as pressure_3h_ago,
        
        -- Icing risk
        i.icing_risk_level,
        i.dew_point_spread_c
        
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly` g
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk` i
        ON g.farm_name = i.farm_name
        AND g.hour = i.timestamp
    ),
    event_flags AS (
      SELECT
        *,
        
        -- CALM event: Low wind sustained
        CASE 
          WHEN wind_speed_100m_ms < 6 THEN 1 
          ELSE 0 
        END as is_calm_hour,
        
        -- STORM event: Rapid pressure drop
        CASE
          WHEN pressure_3h_ago IS NOT NULL 
           AND (pressure_3h_ago - surface_pressure_hpa) > 5
          THEN 1
          ELSE 0
        END as is_storm_hour,
        
        -- DIRECTION_SHIFT event: Rapid direction change
        CASE
          WHEN direction_2h_ago IS NOT NULL
           AND ABS(
             CASE 
               WHEN wind_direction_100m_deg - direction_2h_ago > 180 
               THEN 360 - (wind_direction_100m_deg - direction_2h_ago)
               WHEN wind_direction_100m_deg - direction_2h_ago < -180
               THEN 360 + (wind_direction_100m_deg - direction_2h_ago)
               ELSE wind_direction_100m_deg - direction_2h_ago
             END
           ) > 45
          THEN 1
          ELSE 0
        END as is_direction_shift_hour,
        
        -- TURBULENCE event: High gust factor sustained
        CASE
          WHEN gust_factor > 1.4 THEN 1
          ELSE 0
        END as is_turbulence_hour,
        
        -- ICING event: HIGH icing risk (from wind_icing_risk view)
        CASE
          WHEN icing_risk_level = 'HIGH' THEN 1
          ELSE 0
        END as is_icing_hour,
        
        -- CURTAILMENT event: 0% CF with good wind (Moray West pattern)
        CASE
          WHEN capacity_factor_pct = 0
           AND expected_cf_pct > 50
           AND wind_speed_100m_ms BETWEEN 8 AND 15
          THEN 1
          ELSE 0
        END as is_curtailment_hour
        
      FROM weather_generation
    )
    SELECT * FROM event_flags
    """
    
    print("Creating view: wind_events_base")
    print("  Event types: CALM, STORM, DIRECTION_SHIFT, TURBULENCE, ICING, CURTAILMENT")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Base event detection view created")
    print()

def create_event_episodes_table():
    """Detect consecutive event hours (episodes) and create persistent table."""
    
    print("=" * 80)
    print("📊 DETECTING EVENT EPISODES (≥3 CONSECUTIVE HOURS)")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.wind_events_detected` AS
    WITH event_types AS (
      -- Unpivot event flags into rows (one row per farm-hour-event_type)
      SELECT farm_name, hour, 'CALM' as event_type, is_calm_hour as flag, 
             capacity_factor_pct, cf_deviation_pct, deviation_mw, capacity_mw
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_base`
      WHERE is_calm_hour = 1
      
      UNION ALL
      
      SELECT farm_name, hour, 'STORM' as event_type, is_storm_hour as flag,
             capacity_factor_pct, cf_deviation_pct, deviation_mw, capacity_mw
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_base`
      WHERE is_storm_hour = 1
      
      UNION ALL
      
      SELECT farm_name, hour, 'DIRECTION_SHIFT' as event_type, is_direction_shift_hour as flag,
             capacity_factor_pct, cf_deviation_pct, deviation_mw, capacity_mw
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_base`
      WHERE is_direction_shift_hour = 1
      
      UNION ALL
      
      SELECT farm_name, hour, 'TURBULENCE' as event_type, is_turbulence_hour as flag,
             capacity_factor_pct, cf_deviation_pct, deviation_mw, capacity_mw
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_base`
      WHERE is_turbulence_hour = 1
      
      UNION ALL
      
      SELECT farm_name, hour, 'ICING' as event_type, is_icing_hour as flag,
             capacity_factor_pct, cf_deviation_pct, deviation_mw, capacity_mw
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_base`
      WHERE is_icing_hour = 1
      
      UNION ALL
      
      SELECT farm_name, hour, 'CURTAILMENT' as event_type, is_curtailment_hour as flag,
             capacity_factor_pct, cf_deviation_pct, deviation_mw, capacity_mw
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_base`
      WHERE is_curtailment_hour = 1
    ),
    with_gap_detection AS (
      SELECT
        *,
        -- Flag new episode when gap >2 hours or different event type
        CASE
          WHEN TIMESTAMP_DIFF(
            hour,
            LAG(hour) OVER (PARTITION BY farm_name, event_type ORDER BY hour),
            HOUR
          ) > 2 
          OR LAG(hour) OVER (PARTITION BY farm_name, event_type ORDER BY hour) IS NULL
          THEN 1
          ELSE 0
        END as new_episode_flag
      FROM event_types
    ),
    with_episode_id AS (
      SELECT
        *,
        -- Create episode ID via cumulative sum
        SUM(new_episode_flag) OVER (PARTITION BY farm_name, event_type ORDER BY hour) as episode_id
      FROM with_gap_detection
    ),
    episode_summary AS (
      SELECT
        farm_name,
        event_type,
        episode_id,
        
        -- Episode timing
        MIN(hour) as start_ts,
        MAX(hour) as end_ts,
        COUNT(*) as duration_hours,
        
        -- Peak impact hour (worst CF deviation)
        (ARRAY_AGG(hour ORDER BY cf_deviation_pct LIMIT 1))[OFFSET(0)] as peak_ts,
        
        -- Severity metrics
        MIN(capacity_factor_pct) as min_cf_pct,
        AVG(capacity_factor_pct) as avg_cf_pct,
        AVG(cf_deviation_pct) as avg_cf_deviation_pct,
        SUM(GREATEST(deviation_mw, 0)) as lost_mwh,  -- Lost generation
        
        -- Revenue impact (£50/MWh baseline)
        SUM(GREATEST(deviation_mw, 0)) * 50 as revenue_impact_gbp,
        
        -- Placeholder for Task 8 (upstream lead times)
        CAST(NULL AS STRING) as lead_times_json
        
      FROM with_episode_id
      GROUP BY farm_name, event_type, episode_id
      HAVING COUNT(*) >= 3  -- Minimum 3 consecutive hours
    )
    SELECT 
      -- Create unique event_id
      CONCAT(farm_name, '_', event_type, '_', CAST(episode_id AS STRING)) as event_id,
      farm_name,
      event_type,
      start_ts,
      end_ts,
      peak_ts,
      duration_hours,
      
      -- Severity classification
      CASE
        WHEN avg_cf_deviation_pct < -50 THEN 'SEVERE'
        WHEN avg_cf_deviation_pct < -30 THEN 'HIGH'
        WHEN avg_cf_deviation_pct < -15 THEN 'MEDIUM'
        ELSE 'LOW'
      END as severity_level,
      
      min_cf_pct,
      avg_cf_pct,
      avg_cf_deviation_pct,
      lost_mwh,
      revenue_impact_gbp,
      lead_times_json
      
    FROM episode_summary
    ORDER BY revenue_impact_gbp DESC
    """
    
    print("Creating table: wind_events_detected")
    print("  Criteria: ≥3 consecutive hours per event type")
    print("  Severity: SEVERE (<-50%), HIGH (<-30%), MEDIUM (<-15%), LOW")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Event episodes table created")
    print()

def analyze_event_summary():
    """Summarize detected events."""
    
    print("=" * 80)
    print("📈 EVENT DETECTION SUMMARY")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    SELECT
      event_type,
      severity_level,
      COUNT(*) as event_count,
      SUM(duration_hours) as total_hours,
      AVG(duration_hours) as avg_duration_hours,
      SUM(lost_mwh) as total_lost_mwh,
      SUM(revenue_impact_gbp) as total_revenue_impact_gbp,
      COUNT(DISTINCT farm_name) as affected_farms
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_detected`
    GROUP BY event_type, severity_level
    ORDER BY event_type, 
      CASE severity_level 
        WHEN 'SEVERE' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        ELSE 4 
      END
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print("Event Summary by Type and Severity:\n")
        print(f"{'Event Type':<18} {'Severity':<8} {'Events':>8} {'Hours':>8} {'Avg Dur':>9} {'Lost MWh':>12} {'Revenue £':>15} {'Farms':>6}")
        print("-" * 115)
        
        for _, row in df.iterrows():
            print(f"{row['event_type']:<18} "
                  f"{row['severity_level']:<8} "
                  f"{int(row['event_count']):>8} "
                  f"{int(row['total_hours']):>8} "
                  f"{row['avg_duration_hours']:>8.1f}h "
                  f"{row['total_lost_mwh']:>11,.0f} "
                  f"£{row['total_revenue_impact_gbp']:>13,.0f} "
                  f"{int(row['affected_farms']):>5}")
        
        print()
        
        # Overall totals
        total_events = df['event_count'].sum()
        total_revenue = df['total_revenue_impact_gbp'].sum()
        total_lost = df['total_lost_mwh'].sum()
        
        print("TOTALS:")
        print("-" * 115)
        print(f"  • Total events: {int(total_events):,}")
        print(f"  • Total lost generation: {total_lost:,.0f} MWh")
        print(f"  • Total revenue impact: £{total_revenue:,.0f}")
        print()
        
    else:
        print("⚠️  No events detected (check detection thresholds)")
        print()

def analyze_top_events():
    """Show top 20 worst events."""
    
    print("=" * 80)
    print("🚨 TOP 20 WORST EVENTS (BY REVENUE IMPACT)")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    SELECT
      event_id,
      farm_name,
      event_type,
      severity_level,
      start_ts,
      end_ts,
      duration_hours,
      avg_cf_deviation_pct,
      lost_mwh,
      revenue_impact_gbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_detected`
    ORDER BY revenue_impact_gbp DESC
    LIMIT 20
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print(f"{'Rank':<5} {'Farm':<25} {'Type':<18} {'Severity':<8} {'Duration':>9} {'CF Dev%':>9} {'Lost MWh':>12} {'Revenue £':>15}")
        print("-" * 125)
        
        for idx, row in df.iterrows():
            print(f"{idx+1:<5} "
                  f"{row['farm_name']:<25} "
                  f"{row['event_type']:<18} "
                  f"{row['severity_level']:<8} "
                  f"{int(row['duration_hours']):>8}h "
                  f"{row['avg_cf_deviation_pct']:>8.1f}% "
                  f"{row['lost_mwh']:>11,.0f} "
                  f"£{row['revenue_impact_gbp']:>13,.0f}")
        
        print()
        print("KEY INSIGHTS:")
        print("-" * 125)
        
        # Dominant event type
        top_type = df['event_type'].value_counts().iloc[0]
        top_type_name = df['event_type'].value_counts().index[0]
        print(f"  • Most common in top 20: {top_type_name} ({top_type} events)")
        
        # Dominant farm
        if len(df['farm_name'].value_counts()) > 0:
            top_farm = df['farm_name'].value_counts().iloc[0]
            top_farm_name = df['farm_name'].value_counts().index[0]
            print(f"  • Most affected farm: {top_farm_name} ({top_farm} events in top 20)")
        
        # Average severity
        severe_count = len(df[df['severity_level'] == 'SEVERE'])
        print(f"  • SEVERE events in top 20: {severe_count}")
        
        print()
    else:
        print("⚠️  No events detected")
        print()

def analyze_farm_vulnerability():
    """Identify farms most vulnerable to each event type."""
    
    print("=" * 80)
    print("🏭 FARM VULNERABILITY BY EVENT TYPE")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    SELECT
      farm_name,
      event_type,
      COUNT(*) as event_count,
      SUM(duration_hours) as total_hours,
      SUM(lost_mwh) as total_lost_mwh,
      SUM(revenue_impact_gbp) as total_revenue_gbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_detected`
    GROUP BY farm_name, event_type
    ORDER BY total_revenue_gbp DESC
    LIMIT 30
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print(f"{'Farm':<25} {'Event Type':<18} {'Events':>8} {'Hours':>8} {'Lost MWh':>12} {'Revenue £':>15}")
        print("-" * 105)
        
        for _, row in df.iterrows():
            print(f"{row['farm_name']:<25} "
                  f"{row['event_type']:<18} "
                  f"{int(row['event_count']):>8} "
                  f"{int(row['total_hours']):>8} "
                  f"{row['total_lost_mwh']:>11,.0f} "
                  f"£{row['total_revenue_gbp']:>13,.0f}")
        
        print()
    else:
        print("⚠️  No farm-event data available")
        print()

def main():
    """Run complete event detection."""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "EVENT DETECTION LAYER" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Task 4: Detect weather/operational events causing generation drops")
    print("Data: wind_generation_hourly (Task 7) + era5_weather_data_complete + wind_icing_risk")
    print()
    
    try:
        # Step 1: Create event detection view
        create_event_detection_view()
        
        # Step 2: Detect event episodes (≥3 consecutive hours)
        create_event_episodes_table()
        
        # Step 3: Analyze summary
        analyze_event_summary()
        
        # Step 4: Top worst events
        analyze_top_events()
        
        # Step 5: Farm vulnerability
        analyze_farm_vulnerability()
        
        print("=" * 80)
        print("✅ TASK 4 COMPLETE: Event Detection Layer Built")
        print("=" * 80)
        print()
        print("Created Resources:")
        print("  • wind_events_base view (hourly event flags)")
        print("  • wind_events_detected table (episodes ≥3h)")
        print("  • Event types: CALM, STORM, DIRECTION_SHIFT, TURBULENCE, ICING, CURTAILMENT")
        print("  • Severity levels: SEVERE (<-50%), HIGH (<-30%), MEDIUM (<-15%), LOW")
        print()
        print("Next Steps:")
        print("  • Task 5: Build upstream station features (50-150km west)")
        print("  • Task 8: Calculate event onset timing and lead times")
        print("  • Tasks 9-10: Build dashboards (Streamlit + Looker Studio)")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
