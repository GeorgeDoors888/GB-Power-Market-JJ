#!/usr/bin/env python3
"""
Task 6: Create Unified Hourly Features View

Joins all wind farm data sources into single analysis-ready view:
- On-site weather (ERA5): wind, temp, pressure, gusts, direction
- Upstream signals (Task 5): pressure gradients, wind changes, direction shifts
- Icing risk (Magnus formula): HIGH/MEDIUM/LOW classification
- Event detection (Task 4): CALM/STORM/TURBULENCE/ICING/CURTAILMENT flags
- Generation data (Task 7): actual MW, expected MW, CF deviation, revenue loss

Output: wind_unified_features view - foundation for Task 8 lead time calculation
"""

from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_unified_features_view():
    """
    Create comprehensive view joining all data sources.
    
    This is the foundation table for:
    - Task 8: Lead time calculation (correlate upstream → generation)
    - Task 9: Event Explorer dashboard (4-lane timeline)
    - Task 11: Cross-correlation analysis (statistical validation)
    """
    
    print("=" * 80)
    print("🔗 CREATING UNIFIED HOURLY FEATURES VIEW")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.wind_unified_features` AS
    WITH on_site_weather AS (
      SELECT
        farm_name,
        timestamp as hour,
        temperature_2m_c,
        relative_humidity_2m_pct,
        wind_speed_100m_ms,
        wind_direction_100m_deg,
        wind_gusts_10m_ms,
        surface_pressure_hpa,
        precipitation_mm,
        cloud_cover_pct,
        SAFE_DIVIDE(wind_gusts_10m_ms, NULLIF(wind_speed_100m_ms, 0)) as gust_factor
      FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
    ),
    upstream_signals AS (
      SELECT
        farm_name,
        timestamp as hour,
        upstream_distance_km,
        pressure_gradient_hpa_per_km,
        temperature_gradient_c_per_km,
        wind_speed_change_ms,
        wind_gust_change_ms,
        wind_direction_shift_deg,
        upstream_pressure_hpa,
        upstream_wind_speed_ms,
        upstream_wind_direction_deg
      FROM `inner-cinema-476211-u9.uk_energy_prod.era5_upstream_features`
      WHERE upstream_distance_km = 100  -- Focus on 100km for primary analysis
    ),
    icing_risk AS (
      SELECT
        farm_name,
        timestamp as hour,
        icing_risk_level,
        dew_point_c,
        dew_point_spread_c,
        supercooled_droplet_conditions,
        blade_tip_cooling_risk,
        turbulent_icing_risk
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk`
    ),
    generation_data AS (
      SELECT
        farm_name,
        hour,
        capacity_mw,
        actual_mw,
        expected_mw,
        deviation_mw,
        capacity_factor_pct,
        expected_cf_pct,
        cf_deviation_pct,
        -- Calculate lost generation and revenue (not in table)
        CASE WHEN deviation_mw < 0 THEN ABS(deviation_mw) ELSE 0 END as lost_mw,
        CASE WHEN deviation_mw < 0 THEN ABS(deviation_mw) * 60.0 ELSE 0 END as revenue_loss_estimate_gbp  -- £60/MWh typical
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_generation_hourly`
    ),
    event_flags AS (
      -- Create hourly event flags from wind_events_detected
      SELECT
        e.farm_name,
        h.hour,
        MAX(CASE WHEN e.event_type = 'CALM' AND h.hour BETWEEN e.start_ts AND e.end_ts THEN 1 ELSE 0 END) as is_calm_event,
        MAX(CASE WHEN e.event_type = 'STORM' AND h.hour BETWEEN e.start_ts AND e.end_ts THEN 1 ELSE 0 END) as is_storm_event,
        MAX(CASE WHEN e.event_type = 'DIRECTION_SHIFT' AND h.hour BETWEEN e.start_ts AND e.end_ts THEN 1 ELSE 0 END) as is_direction_shift_event,
        MAX(CASE WHEN e.event_type = 'TURBULENCE' AND h.hour BETWEEN e.start_ts AND e.end_ts THEN 1 ELSE 0 END) as is_turbulence_event,
        MAX(CASE WHEN e.event_type = 'ICING' AND h.hour BETWEEN e.start_ts AND e.end_ts THEN 1 ELSE 0 END) as is_icing_event,
        MAX(CASE WHEN e.event_type = 'CURTAILMENT' AND h.hour BETWEEN e.start_ts AND e.end_ts THEN 1 ELSE 0 END) as is_curtailment_event,
        STRING_AGG(DISTINCT CASE WHEN h.hour BETWEEN e.start_ts AND e.end_ts THEN e.event_id END) as active_event_ids,
        STRING_AGG(DISTINCT CASE WHEN h.hour BETWEEN e.start_ts AND e.end_ts THEN e.severity_level END) as event_severity_levels
      FROM `inner-cinema-476211-u9.uk_energy_prod.wind_events_detected` e
      CROSS JOIN (
        SELECT DISTINCT farm_name, timestamp as hour 
        FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
      ) h
      WHERE e.farm_name = h.farm_name
      GROUP BY e.farm_name, h.hour
    )
    SELECT
      -- Core identifiers
      w.farm_name,
      w.hour,
      
      -- On-site weather (current conditions)
      w.temperature_2m_c,
      w.relative_humidity_2m_pct,
      w.wind_speed_100m_ms,
      w.wind_direction_100m_deg,
      w.wind_gusts_10m_ms,
      w.gust_factor,
      w.surface_pressure_hpa,
      w.precipitation_mm,
      w.cloud_cover_pct,
      
      -- Upstream signals (100km west, 6-12h lead time potential)
      u.pressure_gradient_hpa_per_km,
      u.temperature_gradient_c_per_km,
      u.wind_speed_change_ms,
      u.wind_gust_change_ms,
      u.wind_direction_shift_deg,
      u.upstream_pressure_hpa,
      u.upstream_wind_speed_ms,
      u.upstream_wind_direction_deg,
      
      -- Icing risk (Magnus formula)
      i.icing_risk_level,
      i.dew_point_c,
      i.dew_point_spread_c,
      i.supercooled_droplet_conditions,
      i.blade_tip_cooling_risk,
      i.turbulent_icing_risk,
      
      -- Generation performance
      g.capacity_mw,
      g.actual_mw,
      g.expected_mw,
      g.deviation_mw,
      g.capacity_factor_pct,
      g.expected_cf_pct,
      g.cf_deviation_pct,
      g.lost_mw,
      g.revenue_loss_estimate_gbp,
      
      -- Event flags (from Task 4 event detection)
      COALESCE(ef.is_calm_event, 0) as is_calm_event,
      COALESCE(ef.is_storm_event, 0) as is_storm_event,
      COALESCE(ef.is_direction_shift_event, 0) as is_direction_shift_event,
      COALESCE(ef.is_turbulence_event, 0) as is_turbulence_event,
      COALESCE(ef.is_icing_event, 0) as is_icing_event,
      COALESCE(ef.is_curtailment_event, 0) as is_curtailment_event,
      ef.active_event_ids,
      ef.event_severity_levels,
      
      -- Composite flags for quick filtering
      CASE 
        WHEN COALESCE(ef.is_calm_event, 0) = 1 
          OR COALESCE(ef.is_storm_event, 0) = 1
          OR COALESCE(ef.is_direction_shift_event, 0) = 1
          OR COALESCE(ef.is_turbulence_event, 0) = 1
          OR COALESCE(ef.is_icing_event, 0) = 1
          OR COALESCE(ef.is_curtailment_event, 0) = 1
        THEN TRUE 
        ELSE FALSE 
      END as has_any_event,
      
      -- Derived features for analysis
      CASE
        WHEN w.wind_speed_100m_ms < 6 THEN 'CALM'
        WHEN w.wind_speed_100m_ms BETWEEN 6 AND 12 THEN 'MODERATE'
        WHEN w.wind_speed_100m_ms > 12 THEN 'HIGH'
        ELSE 'UNKNOWN'
      END as wind_regime,
      
      CASE
        WHEN ABS(u.pressure_gradient_hpa_per_km) > 0.01 THEN 'STRONG_GRADIENT'
        WHEN ABS(u.pressure_gradient_hpa_per_km) > 0.005 THEN 'MODERATE_GRADIENT'
        ELSE 'WEAK_GRADIENT'
      END as pressure_gradient_category,
      
      CASE
        WHEN g.cf_deviation_pct < -50 THEN 'SEVERE_UNDERPERFORMANCE'
        WHEN g.cf_deviation_pct < -30 THEN 'HIGH_UNDERPERFORMANCE'
        WHEN g.cf_deviation_pct < -15 THEN 'MODERATE_UNDERPERFORMANCE'
        WHEN g.cf_deviation_pct < -5 THEN 'SLIGHT_UNDERPERFORMANCE'
        WHEN g.cf_deviation_pct < 5 THEN 'NORMAL'
        ELSE 'OVERPERFORMANCE'
      END as performance_category
      
    FROM on_site_weather w
    LEFT JOIN upstream_signals u
      ON w.farm_name = u.farm_name AND w.hour = u.hour
    LEFT JOIN icing_risk i
      ON w.farm_name = i.farm_name AND w.hour = i.hour
    LEFT JOIN generation_data g
      ON w.farm_name = g.farm_name AND w.hour = g.hour
    LEFT JOIN event_flags ef
      ON w.farm_name = ef.farm_name AND w.hour = ef.hour
    """
    
    print("Creating wind_unified_features view...")
    print()
    print("Joining:")
    print("  • era5_weather_data_complete (on-site weather)")
    print("  • era5_upstream_features (100km upstream signals)")
    print("  • wind_icing_risk (Magnus formula icing risk)")
    print("  • wind_generation_hourly (actual vs expected generation)")
    print("  • wind_events_detected (event classification flags)")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ View created: wind_unified_features")
    print()
    
    # Validation summary
    summary_query = """
    SELECT
      COUNT(*) as total_observations,
      COUNT(DISTINCT farm_name) as farms,
      MIN(hour) as earliest,
      MAX(hour) as latest,
      
      -- Data completeness
      COUNT(temperature_2m_c) as has_weather,
      COUNT(pressure_gradient_hpa_per_km) as has_upstream,
      COUNT(icing_risk_level) as has_icing_risk,
      COUNT(actual_mw) as has_generation,
      SUM(CASE WHEN has_any_event THEN 1 ELSE 0 END) as hours_with_events,
      
      -- Event distribution
      SUM(is_calm_event) as calm_event_hours,
      SUM(is_storm_event) as storm_event_hours,
      SUM(is_turbulence_event) as turbulence_event_hours,
      SUM(is_icing_event) as icing_event_hours,
      
      -- Performance distribution
      AVG(capacity_factor_pct) as avg_cf_pct,
      AVG(cf_deviation_pct) as avg_cf_deviation_pct,
      SUM(lost_mw) as total_lost_mw,
      SUM(revenue_loss_estimate_gbp) as total_revenue_loss_gbp
      
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_unified_features`
    """
    
    df = client.query(summary_query).to_dataframe()
    
    print("=" * 80)
    print("📊 VIEW VALIDATION SUMMARY")
    print("=" * 80)
    print()
    
    print(f"Total observations: {int(df['total_observations'][0]):,}")
    print(f"Farms: {int(df['farms'][0])}")
    print(f"Date range: {df['earliest'][0]} to {df['latest'][0]}")
    print()
    
    print("Data Completeness:")
    print(f"  Weather data: {int(df['has_weather'][0]):,} hours ({int(df['has_weather'][0])/int(df['total_observations'][0])*100:.1f}%)")
    print(f"  Upstream signals: {int(df['has_upstream'][0]):,} hours ({int(df['has_upstream'][0])/int(df['total_observations'][0])*100:.1f}%)")
    print(f"  Icing risk: {int(df['has_icing_risk'][0]):,} hours ({int(df['has_icing_risk'][0])/int(df['total_observations'][0])*100:.1f}%)")
    print(f"  Generation data: {int(df['has_generation'][0]):,} hours ({int(df['has_generation'][0])/int(df['total_observations'][0])*100:.1f}%)")
    print()
    
    print("Event Distribution:")
    print(f"  Hours with any event: {int(df['hours_with_events'][0]):,} ({int(df['hours_with_events'][0])/int(df['total_observations'][0])*100:.2f}%)")
    print(f"  CALM event hours: {int(df['calm_event_hours'][0]):,}")
    print(f"  STORM event hours: {int(df['storm_event_hours'][0]):,}")
    print(f"  TURBULENCE event hours: {int(df['turbulence_event_hours'][0]):,}")
    print(f"  ICING event hours: {int(df['icing_event_hours'][0]):,}")
    print()
    
    if df['avg_cf_pct'][0] is not None:
        print("Generation Performance:")
        print(f"  Avg capacity factor: {df['avg_cf_pct'][0]:.1f}%")
        print(f"  Avg CF deviation: {df['avg_cf_deviation_pct'][0]:.1f}%")
        print(f"  Total lost generation: {int(df['total_lost_mw'][0]):,} MW")
        print(f"  Total revenue loss: £{int(df['total_revenue_loss_gbp'][0]):,}")
        print()

def analyze_feature_correlations():
    """Analyze correlations between upstream signals and generation impact."""
    
    print("=" * 80)
    print("📈 UPSTREAM SIGNAL vs GENERATION CORRELATION PREVIEW")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Sample correlation analysis for events
    query = """
    SELECT
      wind_regime,
      pressure_gradient_category,
      performance_category,
      COUNT(*) as hours,
      AVG(cf_deviation_pct) as avg_cf_deviation,
      AVG(pressure_gradient_hpa_per_km) as avg_pressure_gradient,
      AVG(wind_speed_change_ms) as avg_wind_speed_change
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_unified_features`
    WHERE actual_mw IS NOT NULL
      AND has_any_event = TRUE
    GROUP BY wind_regime, pressure_gradient_category, performance_category
    HAVING COUNT(*) >= 10  -- Only patterns with 10+ hours
    ORDER BY hours DESC
    LIMIT 20
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print("Top 20 patterns (event hours only):\n")
        
        for idx, row in df.iterrows():
            print(f"{idx+1}. {row['wind_regime']} + {row['pressure_gradient_category']}")
            print(f"   → {row['performance_category']}")
            print(f"   Hours: {int(row['hours']):,}, CF deviation: {row['avg_cf_deviation']:.1f}%")
            print(f"   Avg ΔP: {row['avg_pressure_gradient']:.4f} hPa/km, Wind change: {row['avg_wind_speed_change']:.2f} m/s")
            print()
    else:
        print("⚠️  No event patterns found (possible if generation data missing)")
        print()
    
    print("=" * 80)
    print("💡 INTERPRETATION:")
    print("=" * 80)
    print()
    print("This preview shows which combinations of:")
    print("  • Wind regime (CALM/MODERATE/HIGH)")
    print("  • Pressure gradient (WEAK/MODERATE/STRONG)")
    print("  • Performance (SEVERE/HIGH/MODERATE underperformance)")
    print()
    print("...occur most frequently during events.")
    print()
    print("Task 8 will calculate precise lead times by:")
    print("  1. Lagging upstream signals (t-1h, t-2h, ..., t-12h)")
    print("  2. Cross-correlating with generation drops")
    print("  3. Finding optimal lag = lead time")
    print()

def export_sample_unified_data():
    """Export sample unified features for inspection."""
    
    print("=" * 80)
    print("📝 EXPORTING SAMPLE UNIFIED FEATURES")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Export sample with events for documentation
    query = """
    SELECT
      farm_name,
      hour,
      wind_speed_100m_ms,
      gust_factor,
      surface_pressure_hpa,
      pressure_gradient_hpa_per_km,
      wind_speed_change_ms,
      icing_risk_level,
      capacity_factor_pct,
      expected_cf_pct,
      cf_deviation_pct,
      is_calm_event,
      is_storm_event,
      is_turbulence_event,
      active_event_ids,
      performance_category
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_unified_features`
    WHERE has_any_event = TRUE
      AND actual_mw IS NOT NULL
    ORDER BY ABS(cf_deviation_pct) DESC
    LIMIT 100
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        filename = f"unified_features_sample_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Exported {len(df)} sample unified feature rows to: {filename}")
        print()
        print("Sample (top 5 worst CF deviations):")
        print(df.head(5)[['farm_name', 'hour', 'wind_speed_100m_ms', 'cf_deviation_pct', 
                          'is_calm_event', 'is_storm_event', 'performance_category']].to_string(index=False))
    else:
        print("⚠️  No unified features with events and generation found")
    print()

def main():
    """Run complete unified features creation."""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "TASK 6: UNIFIED HOURLY FEATURES" + " " * 23 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Goal: Join all data sources into single analysis-ready view")
    print("Purpose: Foundation for lead time calculation and dashboards")
    print()
    print("Data Sources:")
    print("  • On-site weather: wind, temp, pressure, gusts, direction")
    print("  • Upstream signals: pressure gradients, wind changes (100km west)")
    print("  • Icing risk: Magnus formula HIGH/MEDIUM/LOW classification")
    print("  • Event flags: CALM/STORM/TURBULENCE/ICING/CURTAILMENT")
    print("  • Generation: actual MW, expected MW, CF deviation, revenue loss")
    print()
    
    try:
        # Step 1: Create unified view
        create_unified_features_view()
        
        # Step 2: Analyze correlations
        analyze_feature_correlations()
        
        # Step 3: Export sample data
        export_sample_unified_data()
        
        print("=" * 80)
        print("✅ TASK 6 COMPLETE: UNIFIED FEATURES VIEW CREATED")
        print("=" * 80)
        print()
        print("Created Resources:")
        print("  • wind_unified_features view: Comprehensive hourly data")
        print("  • Sample export CSV: Top 100 event hours with worst CF deviations")
        print()
        print("View Includes:")
        print("  • 50+ columns spanning weather, upstream, icing, events, generation")
        print("  • Composite flags: has_any_event, wind_regime, performance_category")
        print("  • Ready for direct analysis without complex joins")
        print()
        print("Ready For:")
        print("  • Task 8: Lead time calculation (lag upstream → correlate with generation)")
        print("  • Task 9: Streamlit Event Explorer (4-lane timeline visualization)")
        print("  • Task 11: Cross-correlation analysis (scipy statistical validation)")
        print()
        print("Next: Task 8 - Calculate event onset timing and lead times")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
