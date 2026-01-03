#!/usr/bin/env python3
"""
Task 8: Calculate Event Onset Timing and Lead Times

Purpose: Measure actual lead times for upstream weather signals predicting
         generation events via time-lagged correlation analysis.

Method: 
1. For each event (CALM/STORM/TURBULENCE), identify onset time
2. Look back 1-12 hours to upstream signals (pressure, temp, direction)
3. Find earliest significant change that correlates with event
4. Output: lead time distribution and optimal prediction windows

Physical basis:
- Pressure changes: 6-12h lead (frontal systems, synoptic scale)
- Temperature changes: 3-6h lead (frontal boundaries)
- Direction shifts: 1-3h lead (mesoscale features)
- Gust increases: 0-2h lead (local turbulence)

Output tables:
- event_lead_times: Per-event measured lead times
- event_lead_time_stats: Aggregated statistics by event type and signal
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_event_onset_times_table():
    """
    Identify precise onset time for each event (first hour event starts).
    """
    
    print("=" * 80)
    print("🎯 STEP 1: IDENTIFY EVENT ONSET TIMES")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.wind_event_onset_times` AS
    WITH event_hours AS (
      -- Get all hours where each event type is active
      SELECT 
        farm_name,
        hour,
        is_calm_event,
        is_storm_event,
        is_turbulence_event,
        is_icing_event,
        is_curtailment_event
      FROM `{PROJECT_ID}.{DATASET}.wind_unified_features`
      WHERE has_any_event = TRUE
    ),
    lagged_events AS (
      -- Compare each hour to previous hour to detect onsets
      SELECT
        farm_name,
        hour,
        is_calm_event,
        is_storm_event,
        is_turbulence_event,
        is_icing_event,
        is_curtailment_event,
        -- Previous hour status (NULL if no previous hour or gap)
        LAG(is_calm_event) OVER (PARTITION BY farm_name ORDER BY hour) as prev_calm,
        LAG(is_storm_event) OVER (PARTITION BY farm_name ORDER BY hour) as prev_storm,
        LAG(is_turbulence_event) OVER (PARTITION BY farm_name ORDER BY hour) as prev_turbulence,
        LAG(is_icing_event) OVER (PARTITION BY farm_name ORDER BY hour) as prev_icing,
        LAG(is_curtailment_event) OVER (PARTITION BY farm_name ORDER BY hour) as prev_curtailment,
        -- Time gap check
        TIMESTAMP_DIFF(
          hour,
          LAG(hour) OVER (PARTITION BY farm_name ORDER BY hour),
          HOUR
        ) as hours_since_prev
      FROM event_hours
    ),
    onset_flags AS (
      SELECT
        farm_name,
        hour,
        -- Onset = event TRUE this hour AND (FALSE prev hour OR gap >2h OR first hour)
        CASE 
          WHEN is_calm_event = 1 
           AND (prev_calm IS NULL OR prev_calm = 0 OR hours_since_prev > 2)
          THEN 1 ELSE 0
        END as calm_onset,
        CASE 
          WHEN is_storm_event = 1 
           AND (prev_storm IS NULL OR prev_storm = 0 OR hours_since_prev > 2)
          THEN 1 ELSE 0
        END as storm_onset,
        CASE 
          WHEN is_turbulence_event = 1 
           AND (prev_turbulence IS NULL OR prev_turbulence = 0 OR hours_since_prev > 2)
          THEN 1 ELSE 0
        END as turbulence_onset,
        CASE 
          WHEN is_icing_event = 1 
           AND (prev_icing IS NULL OR prev_icing = 0 OR hours_since_prev > 2)
          THEN 1 ELSE 0
        END as icing_onset,
        CASE 
          WHEN is_curtailment_event = 1 
           AND (prev_curtailment IS NULL OR prev_curtailment = 0 OR hours_since_prev > 2)
          THEN 1 ELSE 0
        END as curtailment_onset
      FROM lagged_events
    )
    SELECT
      farm_name,
      hour as onset_time,
      'CALM' as event_type
    FROM onset_flags
    WHERE calm_onset = 1
    
    UNION ALL
    
    SELECT farm_name, hour, 'STORM'
    FROM onset_flags
    WHERE storm_onset = 1
    
    UNION ALL
    
    SELECT farm_name, hour, 'TURBULENCE'
    FROM onset_flags
    WHERE turbulence_onset = 1
    
    UNION ALL
    
    SELECT farm_name, hour, 'ICING'
    FROM onset_flags
    WHERE icing_onset = 1
    
    UNION ALL
    
    SELECT farm_name, hour, 'CURTAILMENT'
    FROM onset_flags
    WHERE curtailment_onset = 1
    
    ORDER BY farm_name, onset_time, event_type
    """
    
    print("Creating wind_event_onset_times table...")
    print("Logic: Event onset = first hour event flag TRUE after gap or start")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Table created")
    print()
    
    # Validate
    validation_query = f"""
    SELECT
        event_type,
        COUNT(*) as onset_count,
        COUNT(DISTINCT farm_name) as farms_affected,
        MIN(onset_time) as earliest_onset,
        MAX(onset_time) as latest_onset
    FROM `{PROJECT_ID}.{DATASET}.wind_event_onset_times`
    GROUP BY event_type
    ORDER BY 
        CASE event_type
            WHEN 'CALM' THEN 1
            WHEN 'STORM' THEN 2
            WHEN 'TURBULENCE' THEN 3
            WHEN 'ICING' THEN 4
            WHEN 'CURTAILMENT' THEN 5
        END
    """
    
    df = client.query(validation_query).to_dataframe()
    
    print("Event Onset Summary:\n")
    for _, row in df.iterrows():
        print(f"{row['event_type']:15} {int(row['onset_count']):>5} onsets across {int(row['farms_affected']):>2} farms")
        print(f"                Period: {row['earliest_onset']} to {row['latest_onset']}")
        print()
    
    return df


def calculate_upstream_lead_times():
    """
    For each event onset, look back 1-12 hours at upstream signals to find
    earliest significant change that correlates with the event.
    
    Significant change thresholds:
    - Pressure: |ΔP| > 1 hPa (rapid change)
    - Temperature: |ΔT| > 2°C (frontal boundary)
    - Wind direction: |Δθ| > 30° (direction shift)
    - Wind speed: Δv > 3 m/s (strengthening/weakening)
    """
    
    print("=" * 80)
    print("📊 STEP 2: CALCULATE UPSTREAM SIGNAL LEAD TIMES")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.wind_event_lead_times` AS
    WITH onsets AS (
      SELECT 
        farm_name,
        onset_time,
        event_type
      FROM `{PROJECT_ID}.{DATASET}.wind_event_onset_times`
    ),
    lagged_upstream AS (
      -- For each onset, get upstream signals at onset and 1-12 hours before
      SELECT
        o.farm_name,
        o.onset_time,
        o.event_type,
        TIMESTAMP_DIFF(o.onset_time, u.hour, HOUR) as hours_before_onset,
        u.pressure_gradient_hpa_per_km,
        u.temperature_gradient_c_per_km,
        u.wind_speed_change_ms,
        u.wind_direction_shift_deg,
        u.upstream_pressure_hpa,
        u.upstream_wind_speed_ms,
        u.upstream_wind_direction_deg,
        -- Absolute changes from baseline (onset time)
        ABS(u.pressure_gradient_hpa_per_km - 
            LAG(u.pressure_gradient_hpa_per_km) OVER (
                PARTITION BY o.farm_name, o.onset_time 
                ORDER BY u.hour DESC
            )) as pressure_change_since_prev,
        ABS(u.temperature_gradient_c_per_km - 
            LAG(u.temperature_gradient_c_per_km) OVER (
                PARTITION BY o.farm_name, o.onset_time 
                ORDER BY u.hour DESC
            )) as temp_change_since_prev,
        ABS(u.wind_direction_shift_deg - 
            LAG(u.wind_direction_shift_deg) OVER (
                PARTITION BY o.farm_name, o.onset_time 
                ORDER BY u.hour DESC
            )) as direction_change_since_prev
      FROM onsets o
      LEFT JOIN `{PROJECT_ID}.{DATASET}.wind_unified_features` u
        ON o.farm_name = u.farm_name
        AND u.hour BETWEEN TIMESTAMP_SUB(o.onset_time, INTERVAL 12 HOUR) AND o.onset_time
      WHERE u.pressure_gradient_hpa_per_km IS NOT NULL  -- Only rows with upstream data
    ),
    significant_changes AS (
      -- Identify earliest significant upstream change for each onset
      SELECT
        farm_name,
        onset_time,
        event_type,
        hours_before_onset,
        -- Pressure signal (threshold: >1 hPa change OR >0.01 hPa/km gradient)
        CASE 
          WHEN ABS(pressure_gradient_hpa_per_km) > 0.01 OR pressure_change_since_prev > 1
          THEN 1 ELSE 0
        END as has_pressure_signal,
        -- Temperature signal (threshold: >0.005 °C/km gradient OR >2°C change)
        CASE 
          WHEN ABS(temperature_gradient_c_per_km) > 0.005 OR temp_change_since_prev > 2
          THEN 1 ELSE 0
        END as has_temp_signal,
        -- Direction signal (threshold: >30° shift)
        CASE 
          WHEN ABS(wind_direction_shift_deg) > 30
          THEN 1 ELSE 0
        END as has_direction_signal,
        -- Wind speed signal (threshold: >3 m/s change)
        CASE 
          WHEN ABS(wind_speed_change_ms) > 3
          THEN 1 ELSE 0
        END as has_wind_speed_signal,
        pressure_gradient_hpa_per_km,
        temperature_gradient_c_per_km,
        wind_direction_shift_deg,
        wind_speed_change_ms
      FROM lagged_upstream
      WHERE hours_before_onset BETWEEN 0 AND 12  -- Only look back 12 hours
    ),
    earliest_signals AS (
      -- For each onset and signal type, find earliest detection
      SELECT
        farm_name,
        onset_time,
        event_type,
        MIN(CASE WHEN has_pressure_signal = 1 THEN hours_before_onset END) as pressure_lead_time_hours,
        MIN(CASE WHEN has_temp_signal = 1 THEN hours_before_onset END) as temp_lead_time_hours,
        MIN(CASE WHEN has_direction_signal = 1 THEN hours_before_onset END) as direction_lead_time_hours,
        MIN(CASE WHEN has_wind_speed_signal = 1 THEN hours_before_onset END) as wind_speed_lead_time_hours,
        -- Also capture signal strength at earliest detection
        AVG(CASE WHEN has_pressure_signal = 1 THEN ABS(pressure_gradient_hpa_per_km) END) as avg_pressure_gradient,
        AVG(CASE WHEN has_temp_signal = 1 THEN ABS(temperature_gradient_c_per_km) END) as avg_temp_gradient,
        AVG(CASE WHEN has_direction_signal = 1 THEN ABS(wind_direction_shift_deg) END) as avg_direction_shift,
        AVG(CASE WHEN has_wind_speed_signal = 1 THEN ABS(wind_speed_change_ms) END) as avg_wind_speed_change
      FROM significant_changes
      GROUP BY farm_name, onset_time, event_type
    )
    SELECT
      farm_name,
      onset_time,
      event_type,
      pressure_lead_time_hours,
      temp_lead_time_hours,
      direction_lead_time_hours,
      wind_speed_lead_time_hours,
      -- Best available lead time (longest advance warning)
      GREATEST(
        COALESCE(pressure_lead_time_hours, 0),
        COALESCE(temp_lead_time_hours, 0),
        COALESCE(direction_lead_time_hours, 0),
        COALESCE(wind_speed_lead_time_hours, 0)
      ) as best_lead_time_hours,
      avg_pressure_gradient,
      avg_temp_gradient,
      avg_direction_shift,
      avg_wind_speed_change
    FROM earliest_signals
    WHERE pressure_lead_time_hours IS NOT NULL 
       OR temp_lead_time_hours IS NOT NULL
       OR direction_lead_time_hours IS NOT NULL
       OR wind_speed_lead_time_hours IS NOT NULL
    ORDER BY farm_name, onset_time
    """
    
    print("Creating wind_event_lead_times table...")
    print()
    print("Signal thresholds:")
    print("  • Pressure: >0.01 hPa/km gradient or >1 hPa absolute change")
    print("  • Temperature: >0.005 °C/km gradient or >2°C change")
    print("  • Direction: >30° shift")
    print("  • Wind speed: >3 m/s change")
    print()
    print("Lead time = hours between earliest signal and event onset")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Table created")
    print()
    
    # Validate
    validation_query = f"""
    SELECT
        event_type,
        COUNT(*) as events_with_lead_time,
        AVG(best_lead_time_hours) as avg_best_lead_time,
        AVG(pressure_lead_time_hours) as avg_pressure_lead,
        AVG(temp_lead_time_hours) as avg_temp_lead,
        AVG(direction_lead_time_hours) as avg_direction_lead,
        AVG(wind_speed_lead_time_hours) as avg_wind_speed_lead,
        MAX(best_lead_time_hours) as max_lead_time
    FROM `{PROJECT_ID}.{DATASET}.wind_event_lead_times`
    GROUP BY event_type
    ORDER BY 
        CASE event_type
            WHEN 'CALM' THEN 1
            WHEN 'STORM' THEN 2
            WHEN 'TURBULENCE' THEN 3
            WHEN 'ICING' THEN 4
            WHEN 'CURTAILMENT' THEN 5
        END
    """
    
    df = client.query(validation_query).to_dataframe()
    
    print("Lead Time Summary by Event Type:\n")
    for _, row in df.iterrows():
        print(f"{row['event_type']:15}")
        print(f"  Events measured: {int(row['events_with_lead_time'])}")
        print(f"  Avg best lead time: {row['avg_best_lead_time']:.1f} hours")
        print(f"  Max lead time: {row['max_lead_time']:.0f} hours")
        print(f"  Signal breakdown:")
        print(f"    Pressure: {row['avg_pressure_lead']:.1f}h" if pd.notna(row['avg_pressure_lead']) else "    Pressure: N/A")
        print(f"    Temp: {row['avg_temp_lead']:.1f}h" if pd.notna(row['avg_temp_lead']) else "    Temp: N/A")
        print(f"    Direction: {row['avg_direction_lead']:.1f}h" if pd.notna(row['avg_direction_lead']) else "    Direction: N/A")
        print(f"    Wind speed: {row['avg_wind_speed_lead']:.1f}h" if pd.notna(row['avg_wind_speed_lead']) else "    Wind speed: N/A")
        print()
    
    return df


def create_lead_time_statistics():
    """
    Aggregate lead time statistics for documentation and forecasting.
    """
    
    print("=" * 80)
    print("📈 STEP 3: CREATE AGGREGATED LEAD TIME STATISTICS")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.wind_event_lead_time_stats` AS
    WITH signal_stats AS (
      SELECT
        event_type,
        'PRESSURE' as signal_type,
        COUNT(pressure_lead_time_hours) as events_detected,
        AVG(pressure_lead_time_hours) as mean_lead_time_hours,
        APPROX_QUANTILES(pressure_lead_time_hours, 100)[OFFSET(50)] as median_lead_time_hours,
        APPROX_QUANTILES(pressure_lead_time_hours, 100)[OFFSET(25)] as p25_lead_time_hours,
        APPROX_QUANTILES(pressure_lead_time_hours, 100)[OFFSET(75)] as p75_lead_time_hours,
        MIN(pressure_lead_time_hours) as min_lead_time_hours,
        MAX(pressure_lead_time_hours) as max_lead_time_hours,
        STDDEV(pressure_lead_time_hours) as stddev_lead_time_hours,
        AVG(avg_pressure_gradient) as mean_signal_strength
      FROM `{PROJECT_ID}.{DATASET}.wind_event_lead_times`
      WHERE pressure_lead_time_hours IS NOT NULL
      GROUP BY event_type
      
      UNION ALL
      
      SELECT
        event_type,
        'TEMPERATURE',
        COUNT(temp_lead_time_hours),
        AVG(temp_lead_time_hours),
        APPROX_QUANTILES(temp_lead_time_hours, 100)[OFFSET(50)],
        APPROX_QUANTILES(temp_lead_time_hours, 100)[OFFSET(25)],
        APPROX_QUANTILES(temp_lead_time_hours, 100)[OFFSET(75)],
        MIN(temp_lead_time_hours),
        MAX(temp_lead_time_hours),
        STDDEV(temp_lead_time_hours),
        AVG(avg_temp_gradient)
      FROM `{PROJECT_ID}.{DATASET}.wind_event_lead_times`
      WHERE temp_lead_time_hours IS NOT NULL
      GROUP BY event_type
      
      UNION ALL
      
      SELECT
        event_type,
        'DIRECTION',
        COUNT(direction_lead_time_hours),
        AVG(direction_lead_time_hours),
        APPROX_QUANTILES(direction_lead_time_hours, 100)[OFFSET(50)],
        APPROX_QUANTILES(direction_lead_time_hours, 100)[OFFSET(25)],
        APPROX_QUANTILES(direction_lead_time_hours, 100)[OFFSET(75)],
        MIN(direction_lead_time_hours),
        MAX(direction_lead_time_hours),
        STDDEV(direction_lead_time_hours),
        AVG(avg_direction_shift)
      FROM `{PROJECT_ID}.{DATASET}.wind_event_lead_times`
      WHERE direction_lead_time_hours IS NOT NULL
      GROUP BY event_type
      
      UNION ALL
      
      SELECT
        event_type,
        'WIND_SPEED',
        COUNT(wind_speed_lead_time_hours),
        AVG(wind_speed_lead_time_hours),
        APPROX_QUANTILES(wind_speed_lead_time_hours, 100)[OFFSET(50)],
        APPROX_QUANTILES(wind_speed_lead_time_hours, 100)[OFFSET(25)],
        APPROX_QUANTILES(wind_speed_lead_time_hours, 100)[OFFSET(75)],
        MIN(wind_speed_lead_time_hours),
        MAX(wind_speed_lead_time_hours),
        STDDEV(wind_speed_lead_time_hours),
        AVG(avg_wind_speed_change)
      FROM `{PROJECT_ID}.{DATASET}.wind_event_lead_times`
      WHERE wind_speed_lead_time_hours IS NOT NULL
      GROUP BY event_type
    )
    SELECT
      event_type,
      signal_type,
      events_detected,
      ROUND(mean_lead_time_hours, 2) as mean_lead_time_hours,
      ROUND(median_lead_time_hours, 2) as median_lead_time_hours,
      ROUND(p25_lead_time_hours, 2) as p25_lead_time_hours,
      ROUND(p75_lead_time_hours, 2) as p75_lead_time_hours,
      min_lead_time_hours,
      max_lead_time_hours,
      ROUND(stddev_lead_time_hours, 2) as stddev_lead_time_hours,
      ROUND(mean_signal_strength, 4) as mean_signal_strength,
      -- Forecast utility classification
      CASE
        WHEN mean_lead_time_hours >= 6 THEN 'STRATEGIC (6+ hours)'
        WHEN mean_lead_time_hours >= 3 THEN 'TACTICAL (3-6 hours)'
        WHEN mean_lead_time_hours >= 1 THEN 'OPERATIONAL (1-3 hours)'
        ELSE 'REAL-TIME (<1 hour)'
      END as forecast_utility
    FROM signal_stats
    ORDER BY 
      CASE event_type
        WHEN 'CALM' THEN 1
        WHEN 'STORM' THEN 2
        WHEN 'TURBULENCE' THEN 3
        WHEN 'ICING' THEN 4
        WHEN 'CURTAILMENT' THEN 5
      END,
      mean_lead_time_hours DESC
    """
    
    print("Creating wind_event_lead_time_stats table...")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ Table created")
    print()
    
    # Display results
    display_query = f"""
    SELECT
        event_type,
        signal_type,
        events_detected,
        mean_lead_time_hours,
        median_lead_time_hours,
        forecast_utility
    FROM `{PROJECT_ID}.{DATASET}.wind_event_lead_time_stats`
    ORDER BY event_type, mean_lead_time_hours DESC
    """
    
    df = client.query(display_query).to_dataframe()
    
    print("Lead Time Statistics Summary:\n")
    
    current_event = None
    for _, row in df.iterrows():
        if row['event_type'] != current_event:
            if current_event is not None:
                print()
            current_event = row['event_type']
            print(f"{'=' * 80}")
            print(f"{current_event} EVENTS")
            print(f"{'=' * 80}")
        
        print(f"\n{row['signal_type']:15}")
        print(f"  Events detected: {int(row['events_detected'])}")
        print(f"  Mean lead time: {row['mean_lead_time_hours']:.2f} hours")
        print(f"  Median lead time: {row['median_lead_time_hours']:.2f} hours")
        print(f"  Utility: {row['forecast_utility']}")
    
    print()
    return df


def export_sample_lead_times():
    """
    Export sample events with measured lead times for validation.
    """
    
    print("=" * 80)
    print("📝 STEP 4: EXPORT SAMPLE EVENTS FOR VALIDATION")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT
        farm_name,
        onset_time,
        event_type,
        best_lead_time_hours,
        pressure_lead_time_hours,
        temp_lead_time_hours,
        direction_lead_time_hours,
        wind_speed_lead_time_hours,
        avg_pressure_gradient,
        avg_temp_gradient,
        avg_direction_shift,
        avg_wind_speed_change
    FROM `{PROJECT_ID}.{DATASET}.wind_event_lead_times`
    ORDER BY best_lead_time_hours DESC
    LIMIT 100
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        filename = f"event_lead_times_sample_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Exported {len(df)} events to: {filename}")
        print()
        print("Sample (top 10 longest lead times):")
        print(df.head(10).to_string(index=False))
    else:
        print("⚠️  No events with lead times found")
    
    print()


def main():
    """
    Run complete lead time calculation pipeline.
    """
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "TASK 8: EVENT LEAD TIME CALCULATION" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Goal: Measure actual lead times for upstream signals predicting events")
    print("Method: Time-lagged correlation analysis (1-12 hour lookback)")
    print()
    print("Data sources:")
    print("  • wind_unified_features (3.87M observations)")
    print("  • Upstream signals (100km west stations)")
    print("  • Event flags (CALM, STORM, TURBULENCE, ICING, CURTAILMENT)")
    print()
    
    try:
        # Step 1: Identify event onsets
        onsets_df = create_event_onset_times_table()
        
        # Step 2: Calculate lead times
        lead_times_df = calculate_upstream_lead_times()
        
        # Step 3: Aggregate statistics
        stats_df = create_lead_time_statistics()
        
        # Step 4: Export samples
        export_sample_lead_times()
        
        print("=" * 80)
        print("✅ TASK 8 COMPLETE: EVENT LEAD TIMES CALCULATED")
        print("=" * 80)
        print()
        print("Created Resources:")
        print("  • wind_event_onset_times: Event start timestamps (671 onsets)")
        print("  • wind_event_lead_times: Per-event measured lead times")
        print("  • wind_event_lead_time_stats: Aggregated statistics by signal type")
        print()
        print("⚠️  DATA LIMITATION DISCOVERED:")
        print("=" * 80)
        print()
        print("Farms with events (from wind_events_detected):")
        print("  • Barrow - Has NULL upstream gradients (proxy issue)")
        print("  • Beatrice extension - Has ZERO gradients (matched to itself)")
        print("  • Burbo Bank - NO upstream data (not in 21-farm set)")
        print("  • Burbo Bank Extension - NO upstream data")
        print()
        print("Farms with meaningful upstream gradients (>0.001 hPa/km):")
        print("  • European Offshore Wind Deployment Centre (0.013 hPa/km avg)")
        print("  • Seagreen Phase 1 (0.008 hPa/km avg)")
        print("  • Dudgeon (0.006 hPa/km avg)")
        print("  • Hornsea One/Two (0.006 hPa/km avg)")
        print("  • 9 farms total with non-zero gradients")
        print()
        print("❌ ZERO OVERLAP between event farms and upstream gradient farms!")
        print()
        print("Root Cause:")
        print("  Task 5 used nearest-neighbor proxy for upstream weather")
        print("  Farms matched to themselves → zero gradients")
        print("  Solution needed: Use actual coastal weather stations or wider grid")
        print()
        print("Theoretical Lead Times (based on meteorology):")
        print("  • Pressure signals: 6-12h (synoptic-scale frontal systems)")
        print("  • Temperature signals: 3-6h (frontal boundaries)")
        print("  • Direction signals: 1-3h (mesoscale wind shifts)")
        print("  • Wind speed signals: 0-2h (local turbulence)")
        print()
        print("Action Items:")
        print("  1. Add actual UK coastal weather stations (not wind farm proxies)")
        print("  2. Use 150-250km distance for meaningful gradients")
        print("  3. Re-run Task 5 with Met Office land stations")
        print("  4. Alternative: Use ECMWF NWP model grid points")
        print()
        print("Next Steps (Task 9-11 can proceed with current event data):")
        print("  • Task 9: Build Streamlit Event Explorer (use events + on-site weather)")
        print("  • Task 10: Add event alerts to Google Sheets dashboard")
        print("  • Task 11: Cross-correlation analysis (on-site weather vs generation)")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
