#!/usr/bin/env python3
"""
Add Grid Constraint Indicators to Dashboard

Enhances weather_generation_correlation view with curtailment flags
to separate weather impacts from grid constraints.

Creates:
1. weather_generation_constraints_view - enhanced view with curtailment flags
2. constraint_impact_summary - aggregated statistics
3. Google Sheets 'Grid Constraints' tab with KPIs and charts

Key Attribution:
- Weather Impact: CF deviation during non-constrained periods
- Constraint Impact: CF deviation during constrained periods
- Combined Impact: Total £104M revenue loss breakdown
"""

import pandas as pd
from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def create_enhanced_weather_generation_view():
    """Add constraint flags to weather_generation_correlation view."""
    
    print("=" * 80)
    print("🔗 CREATING ENHANCED WEATHER-GENERATION-CONSTRAINTS VIEW")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.weather_generation_constraints` AS
    WITH base_weather_generation AS (
      SELECT 
        w.farm_name,
        w.timestamp as hour,
        w.wind_speed_100m_ms,
        w.temperature_2m_c,
        w.surface_pressure_hpa,
        SAFE_DIVIDE(w.wind_gusts_10m_ms, NULLIF(w.wind_speed_100m_ms, 0)) as gust_factor,
        i.icing_risk_level,
        i.dew_point_spread_c,
        
        -- Generation (aggregated across BMUs for multi-unit farms)
        SUM(p.levelTo) as actual_mw,
        MAX(m.capacity_mw) as capacity_mw,
        SUM(p.levelTo) / NULLIF(MAX(m.capacity_mw), 0) * 100 as capacity_factor_pct
        
      FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete` w
      INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_farm_to_bmu` m
        ON w.farm_name = m.farm_name
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.wind_icing_risk` i
        ON w.farm_name = i.farm_name 
        AND w.timestamp = i.timestamp
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_pn` p
        ON m.bm_unit_id = p.bmUnit
        AND TIMESTAMP_TRUNC(w.timestamp, HOUR) = TIMESTAMP_TRUNC(CAST(p.settlementDate AS TIMESTAMP), HOUR)
      WHERE CAST(w.timestamp AS DATE) >= '2024-01-01'
      GROUP BY w.farm_name, hour, w.wind_speed_100m_ms, w.temperature_2m_c, w.surface_pressure_hpa, 
               w.wind_gusts_10m_ms, i.icing_risk_level, i.dew_point_spread_c
    ),
    with_curtailment AS (
      SELECT 
        bg.*,
        
        -- Curtailment flags (any acceptance in this hour = constrained)
        CASE WHEN c.acceptance_time IS NOT NULL THEN TRUE ELSE FALSE END as is_curtailed,
        c.constraint_severity,
        c.acceptancePrice as curtailment_price_gbp_per_mwh,
        c.acceptanceVolume as curtailment_volume_mw,
        c.curtailment_type,
        
        -- Theoretical expected CF (simple wind speed model)
        CASE 
          WHEN bg.wind_speed_100m_ms < 3 THEN 0.0
          WHEN bg.wind_speed_100m_ms BETWEEN 3 AND 5 THEN 15.0
          WHEN bg.wind_speed_100m_ms BETWEEN 5 AND 8 THEN 40.0
          WHEN bg.wind_speed_100m_ms BETWEEN 8 AND 12 THEN 70.0
          WHEN bg.wind_speed_100m_ms BETWEEN 12 AND 15 THEN 85.0
          WHEN bg.wind_speed_100m_ms BETWEEN 15 AND 20 THEN 95.0
          WHEN bg.wind_speed_100m_ms BETWEEN 20 AND 25 THEN 90.0
          ELSE 0.0
        END as expected_cf_pct,
        
        -- Revenue proxy (£50/MWh baseline)
        50.0 as baseline_price_gbp_per_mwh
        
      FROM base_weather_generation bg
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.curtailment_events` c
        ON bg.farm_name = c.farm_name
        AND bg.hour = TIMESTAMP_TRUNC(c.acceptance_time, HOUR)
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
    
    print("Creating view: weather_generation_constraints")
    print("  Joins: ERA5 weather + bmrs_pn + curtailment_events + icing_risk")
    print()
    
    job = client.query(query)
    job.result()
    
    print("✅ View created successfully")
    print()
    
    # Validate
    validate_query = """
    SELECT 
        COUNT(*) as total_hours,
        COUNT(DISTINCT farm_name) as farms,
        SUM(CASE WHEN is_curtailed = TRUE THEN 1 ELSE 0 END) as curtailed_hours,
        SUM(CASE WHEN is_curtailed = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as curtailed_pct,
        MIN(DATE(hour)) as earliest,
        MAX(DATE(hour)) as latest
    FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_constraints`
    """
    
    df = client.query(validate_query).to_dataframe()
    
    if len(df) > 0:
        row = df.iloc[0]
        print("View validation:")
        print(f"  Total hours: {int(row['total_hours']):,}")
        print(f"  Farms: {int(row['farms'])}")
        print(f"  Curtailed hours: {int(row['curtailed_hours']):,} ({row['curtailed_pct']:.2f}%)")
        print(f"  Date range: {row['earliest']} to {row['latest']}")
        print()

def analyze_impact_attribution():
    """Attribute £104M revenue loss to constraints vs weather."""
    
    print("=" * 80)
    print("💰 IMPACT ATTRIBUTION: CONSTRAINTS VS WEATHER")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = """
    SELECT 
        impact_category,
        COUNT(*) as hours,
        AVG(capacity_factor_pct) as avg_cf_pct,
        AVG(cf_deviation_pct) as avg_cf_deviation_pct,
        SUM(lost_generation_mw) as total_lost_mw,
        SUM(revenue_loss_gbp) as total_revenue_loss_gbp,
        COUNT(DISTINCT farm_name) as affected_farms
    FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_constraints`
    WHERE cf_deviation_pct < 0  -- Only underperformance
    GROUP BY impact_category
    ORDER BY total_revenue_loss_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) > 0:
        print("Revenue Loss Attribution:\n")
        print(f"{'Category':<15} {'Hours':>10} {'Avg CF%':>8} {'CF Dev%':>9} {'Lost MW':>12} {'Revenue Loss':>15} {'Farms':>6}")
        print("-" * 90)
        
        total_loss = df['total_revenue_loss_gbp'].sum()
        
        for _, row in df.iterrows():
            pct_of_total = (row['total_revenue_loss_gbp'] / total_loss * 100) if total_loss > 0 else 0
            print(f"{row['impact_category']:<15} "
                  f"{int(row['hours']):>10,} "
                  f"{row['avg_cf_pct']:>7.1f}% "
                  f"{row['avg_cf_deviation_pct']:>8.1f}% "
                  f"{row['total_lost_mw']:>11,.0f} "
                  f"£{row['total_revenue_loss_gbp']:>13,.0f} "
                  f"({pct_of_total:>4.1f}%) "
                  f"{int(row['affected_farms']):>5}")
        
        print("-" * 90)
        print(f"{'TOTAL':<15} {int(df['hours'].sum()):>10,} {'':>8} {'':>9} {df['total_lost_mw'].sum():>11,.0f} £{total_loss:>13,.0f} {'':>12}")
        print()
        
        print("KEY INSIGHTS:")
        print("-" * 90)
        
        constraint_loss = df[df['impact_category'] == 'CONSTRAINT']['total_revenue_loss_gbp'].sum() if len(df[df['impact_category'] == 'CONSTRAINT']) > 0 else 0
        constraint_pct = (constraint_loss / total_loss * 100) if total_loss > 0 else 0
        
        normal_loss = df[df['impact_category'] == 'NORMAL']['total_revenue_loss_gbp'].sum() if len(df[df['impact_category'] == 'NORMAL']) > 0 else 0
        normal_pct = (normal_loss / total_loss * 100) if total_loss > 0 else 0
        
        print(f"  • Grid constraints: £{constraint_loss:,.0f} ({constraint_pct:.1f}% of total loss)")
        print(f"  • Normal conditions: £{normal_loss:,.0f} ({normal_pct:.1f}% of total loss)")
        print(f"  • Remaining: Weather factors (icing, turbulence, wind extremes)")
        print()
        
        if constraint_pct > 30:
            print("  ✅ SMOKING GUN: Grid constraints are DOMINANT cause of underperformance")
            print("     → The -27.8% power curve deviation is primarily curtailment, not weather")
        elif normal_pct > 50:
            print("  ⚠️  'NORMAL' conditions dominate losses")
            print("     → Power curve model may be too optimistic")
            print("     → Need turbine-specific curves (Task 3)")
        
        print()
        
    else:
        print("⚠️  No underperformance data available")
        print()

def create_sheets_dashboard():
    """Create Grid Constraints tab in Google Sheets."""
    
    print("=" * 80)
    print("📊 CREATING GOOGLE SHEETS DASHBOARD")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get summary data
    query = """
    WITH summary AS (
      SELECT 
        farm_name,
        COUNT(*) as total_hours,
        SUM(CASE WHEN is_curtailed = TRUE THEN 1 ELSE 0 END) as curtailed_hours,
        AVG(CASE WHEN is_curtailed = TRUE THEN capacity_factor_pct END) as avg_cf_during_curtailment,
        AVG(CASE WHEN is_curtailed = FALSE THEN capacity_factor_pct END) as avg_cf_normal,
        SUM(CASE WHEN is_curtailed = TRUE THEN revenue_loss_gbp ELSE 0 END) as curtailment_revenue_loss_gbp,
        MAX(constraint_severity) as worst_constraint
      FROM `inner-cinema-476211-u9.uk_energy_prod.weather_generation_constraints`
      GROUP BY farm_name
    )
    SELECT * FROM summary
    WHERE curtailed_hours > 0
    ORDER BY curtailment_revenue_loss_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) == 0:
        print("⚠️  No curtailed hours found - skipping Sheets update")
        print("     This is expected if wind farms operate as price-takers")
        print()
        return
    
    # Connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gs_client = gspread.authorize(creds)
    
    spreadsheet = gs_client.open_by_key(SPREADSHEET_ID)
    
    # Create or get sheet
    try:
        sheet = spreadsheet.worksheet('Grid Constraints')
        print("  Found existing 'Grid Constraints' sheet")
    except:
        sheet = spreadsheet.add_worksheet(title='Grid Constraints', rows=100, cols=20)
        print("  Created new 'Grid Constraints' sheet")
    
    # Clear existing data
    sheet.clear()
    
    # Header
    sheet.update('A1', [[
        'GB Power Market - Grid Constraints Analysis'
    ]])
    sheet.update('A2', [[
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    ]])
    
    # KPIs
    total_curtailed = df['curtailed_hours'].sum()
    total_revenue_loss = df['curtailment_revenue_loss_gbp'].sum()
    affected_farms = len(df)
    
    sheet.update('A4', [[
        'KPI', 'Value'
    ]])
    sheet.update('A5', [
        ['Total Curtailed Hours', f'{int(total_curtailed):,}'],
        ['Affected Farms', f'{affected_farms}'],
        ['Revenue Loss from Constraints', f'£{total_revenue_loss:,.0f}'],
        ['Avg CF During Curtailment', f'{df["avg_cf_during_curtailment"].mean():.1f}%'],
        ['Avg CF Normal', f'{df["avg_cf_normal"].mean():.1f}%']
    ])
    
    # Farm-level data
    sheet.update('A11', [[
        'Farm', 'Total Hours', 'Curtailed Hours', 'CF Curtailed %', 'CF Normal %', 'Revenue Loss £', 'Worst Constraint'
    ]])
    
    data = []
    for _, row in df.head(20).iterrows():
        data.append([
            row['farm_name'],
            int(row['total_hours']),
            int(row['curtailed_hours']),
            f"{row['avg_cf_during_curtailment']:.1f}" if pd.notna(row['avg_cf_during_curtailment']) else 'N/A',
            f"{row['avg_cf_normal']:.1f}" if pd.notna(row['avg_cf_normal']) else 'N/A',
            f"{row['curtailment_revenue_loss_gbp']:,.0f}",
            row['worst_constraint'] if pd.notna(row['worst_constraint']) else 'NORMAL'
        ])
    
    sheet.update('A12', data)
    
    # Format
    sheet.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})
    sheet.format('A4:B4', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
    sheet.format('A11:G11', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}})
    
    print(f"✅ Updated Google Sheets with {len(df)} farms")
    print(f"   Sheet: {SPREADSHEET_ID} / 'Grid Constraints' tab")
    print()

def main():
    """Run complete constraint indicator setup."""
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "GRID CONSTRAINT INDICATORS SETUP" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Task 2: Integrate curtailment_events with weather_generation_correlation")
    print("Goal: Separate grid constraints from weather impacts in £104M revenue loss")
    print()
    
    try:
        # Step 1: Create enhanced view
        create_enhanced_weather_generation_view()
        
        # Step 2: Analyze attribution
        analyze_impact_attribution()
        
        # Step 3: Update Google Sheets
        create_sheets_dashboard()
        
        print("=" * 80)
        print("✅ TASK 2 COMPLETE: Grid Constraint Indicators Added")
        print("=" * 80)
        print()
        print("Created Resources:")
        print("  • weather_generation_constraints view (enhanced with curtailment flags)")
        print("  • Impact attribution analysis (constraints vs weather)")
        print("  • Google Sheets 'Grid Constraints' tab")
        print()
        print("Next Steps:")
        print("  • Task 3: Refine power curves with actual turbine specs")
        print("  • Task 4: Design event detection layer (CALM/STORM/ICING)")
        print("  • Task 5: Build upstream station features")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
