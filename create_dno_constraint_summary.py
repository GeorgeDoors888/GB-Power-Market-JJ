#!/usr/bin/env python3
"""
Create DNO-level constraint cost summary for geographic visualization
Uses existing neso_constraint_breakdown tables to aggregate costs by DNO region
No postcode geocoding needed - uses existing DNO boundaries
"""

from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def create_dno_constraint_summary():
    """
    Aggregate constraint breakdown data for DNO-level visualization
    Note: Constraint breakdown is GB-level, not DNO-specific
    This creates a time-series summary for geographic context
    """
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    print('📊 Creating DNO Constraint Summary for Geographic Visualization')
    print('='*80)
    
    # Step 1: Aggregate constraint costs over time
    # Date format varies: some have "2017-04-01T00:00:00", others "2025-03-06"
    # Extract first 10 chars ("2017-04-01") for consistent YYYY-MM-DD format
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.constraint_costs_timeline` AS
    WITH combined_constraints AS (
        -- Union all 9 years of constraint data with explicit CAST to INT64
        SELECT SUBSTR(Date, 1, 10) as date_str,
               CAST(`Reducing largest loss cost` AS INT64) as largest_loss_cost,
               CAST(`Reducing largest loss volume` AS INT64) as largest_loss_volume,
               CAST(`Increasing system inertia cost` AS INT64) as inertia_cost,
               CAST(`Increasing system inertia volume` AS INT64) as inertia_volume,
               CAST(`Voltage constraints cost` AS INT64) as voltage_cost,
               CAST(`Voltage constraints volume` AS INT64) as voltage_volume,
               CAST(`Thermal constraints cost` AS INT64) as thermal_cost,
               CAST(`Thermal constraints volume` AS INT64) as thermal_volume
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2017_2018`
        UNION ALL
        SELECT SUBSTR(Date, 1, 10),
               CAST(`Reducing largest loss cost` AS INT64), CAST(`Reducing largest loss volume` AS INT64),
               CAST(`Increasing system inertia cost` AS INT64), CAST(`Increasing system inertia volume` AS INT64),
               CAST(`Voltage constraints cost` AS INT64), CAST(`Voltage constraints volume` AS INT64),
               CAST(`Thermal constraints cost` AS INT64), CAST(`Thermal constraints volume` AS INT64)
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2018_2019`
        UNION ALL
        SELECT SUBSTR(Date, 1, 10),
               CAST(`Reducing largest loss cost` AS INT64), CAST(`Reducing largest loss volume` AS INT64),
               CAST(`Increasing system inertia cost` AS INT64), CAST(`Increasing system inertia volume` AS INT64),
               CAST(`Voltage constraints cost` AS INT64), CAST(`Voltage constraints volume` AS INT64),
               CAST(`Thermal constraints cost` AS INT64), CAST(`Thermal constraints volume` AS INT64)
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2019_2020`
        UNION ALL
        SELECT SUBSTR(Date, 1, 10),
               CAST(`Reducing largest loss cost` AS INT64), CAST(`Reducing largest loss volume` AS INT64),
               CAST(`Increasing system inertia cost` AS INT64), CAST(`Increasing system inertia volume` AS INT64),
               CAST(`Voltage constraints cost` AS INT64), CAST(`Voltage constraints volume` AS INT64),
               CAST(`Thermal constraints cost` AS INT64), CAST(`Thermal constraints volume` AS INT64)
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2020_2021`
        UNION ALL
        SELECT SUBSTR(Date, 1, 10),
               CAST(`Reducing largest loss cost` AS INT64), CAST(`Reducing largest loss volume` AS INT64),
               CAST(`Increasing system inertia cost` AS INT64), CAST(`Increasing system inertia volume` AS INT64),
               CAST(`Voltage constraints cost` AS INT64), CAST(`Voltage constraints volume` AS INT64),
               CAST(`Thermal constraints cost` AS INT64), CAST(`Thermal constraints volume` AS INT64)
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2021_2022`
        UNION ALL
        SELECT SUBSTR(Date, 1, 10),
               CAST(`Reducing largest loss cost` AS INT64), CAST(`Reducing largest loss volume` AS INT64),
               CAST(`Increasing system inertia cost` AS INT64), CAST(`Increasing system inertia volume` AS INT64),
               CAST(`Voltage constraints cost` AS INT64), CAST(`Voltage constraints volume` AS INT64),
               CAST(`Thermal constraints cost` AS INT64), CAST(`Thermal constraints volume` AS INT64)
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2022_2023`
        UNION ALL
        SELECT SUBSTR(Date, 1, 10),
               CAST(`Reducing largest loss cost` AS INT64), CAST(`Reducing largest loss volume` AS INT64),
               CAST(`Increasing system inertia cost` AS INT64), CAST(`Increasing system inertia volume` AS INT64),
               CAST(`Voltage constraints cost` AS INT64), CAST(`Voltage constraints volume` AS INT64),
               CAST(`Thermal constraints cost` AS INT64), CAST(`Thermal constraints volume` AS INT64)
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2023_2024`
        UNION ALL
        SELECT SUBSTR(Date, 1, 10),
               CAST(`Reducing largest loss cost` AS INT64), CAST(`Reducing largest loss volume` AS INT64),
               CAST(`Increasing system inertia cost` AS INT64), CAST(`Increasing system inertia volume` AS INT64),
               CAST(`Voltage constraints cost` AS INT64), CAST(`Voltage constraints volume` AS INT64),
               CAST(`Thermal constraints cost` AS INT64), CAST(`Thermal constraints volume` AS INT64)
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2024_2025`
        UNION ALL
        SELECT SUBSTR(Date, 1, 10),
               CAST(`Reducing largest loss cost` AS INT64), CAST(`Reducing largest loss volume` AS INT64),
               CAST(`Increasing system inertia cost` AS INT64), CAST(`Increasing system inertia volume` AS INT64),
               CAST(`Voltage constraints cost` AS INT64), CAST(`Voltage constraints volume` AS INT64),
               CAST(`Thermal constraints cost` AS INT64), CAST(`Thermal constraints volume` AS INT64)
        FROM `{PROJECT_ID}.{DATASET}.neso_constraint_breakdown_2025_2026`
    )
    SELECT 
        EXTRACT(YEAR FROM PARSE_DATE('%Y-%m-%d', date_str)) as year,
        EXTRACT(MONTH FROM PARSE_DATE('%Y-%m-%d', date_str)) as month,
        DATE_TRUNC(PARSE_DATE('%Y-%m-%d', date_str), MONTH) as month_start,
        COUNT(*) as days,
        ROUND(SUM(largest_loss_cost), 2) as total_largest_loss_cost,
        ROUND(SUM(inertia_cost), 2) as total_inertia_cost,
        ROUND(SUM(voltage_cost), 2) as total_voltage_cost,
        ROUND(SUM(thermal_cost), 2) as total_thermal_cost,
        ROUND(SUM(largest_loss_cost + inertia_cost + voltage_cost + thermal_cost), 2) as total_constraint_cost,
        ROUND(SUM(largest_loss_volume), 2) as total_largest_loss_volume,
        ROUND(SUM(inertia_volume), 2) as total_inertia_volume,
        ROUND(SUM(voltage_volume), 2) as total_voltage_volume,
        ROUND(SUM(thermal_volume), 2) as total_thermal_volume
    FROM combined_constraints
    GROUP BY year, month, month_start
    ORDER BY year, month
    """
    
    print('⏳ Creating constraint costs timeline...')
    client.query(query).result()
    print('✅ Created constraint_costs_timeline')
    
    # Step 2: Create DNO-level summary (evenly distributed since data is GB-level)
    query_dno = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno` AS
    WITH monthly_costs AS (
        SELECT 
            year,
            month,
            month_start,
            total_constraint_cost,
            total_voltage_cost,
            total_thermal_cost,
            total_inertia_cost
        FROM `{PROJECT_ID}.{DATASET}.constraint_costs_timeline`
    ),
    dno_regions AS (
        SELECT 
            dno_id,
            dno_full_name,
            area_name,
            ST_AREA(boundary) / 1000000 as area_sq_km
        FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    )
    SELECT 
        d.dno_id,
        d.dno_full_name,
        d.area_name,
        d.area_sq_km,
        c.year,
        c.month,
        c.month_start,
        -- Distribute costs evenly across 14 DNOs (simplified approach)
        -- In reality, costs are location-specific but data doesn't specify DNO
        ROUND(c.total_constraint_cost / 14, 2) as allocated_total_cost,
        ROUND(c.total_voltage_cost / 14, 2) as allocated_voltage_cost,
        ROUND(c.total_thermal_cost / 14, 2) as allocated_thermal_cost,
        ROUND(c.total_inertia_cost / 14, 2) as allocated_inertia_cost,
        -- Cost density (£/km²) - illustrative metric
        ROUND((c.total_constraint_cost / 14) / d.area_sq_km, 4) as cost_per_sq_km
    FROM dno_regions d
    CROSS JOIN monthly_costs c
    ORDER BY year, month, dno_full_name
    """
    
    print('⏳ Creating DNO-level constraint cost allocation...')
    client.query(query_dno).result()
    print('✅ Created constraint_costs_by_dno')
    
    # Step 3: Create latest month summary for Sheets visualization
    query_latest = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno_latest` AS
    SELECT 
        dno_id,
        dno_full_name,
        area_name,
        area_sq_km,
        allocated_total_cost as total_cost_gbp,
        allocated_voltage_cost as voltage_cost_gbp,
        allocated_thermal_cost as thermal_cost_gbp,
        allocated_inertia_cost as inertia_cost_gbp,
        cost_per_sq_km
    FROM `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno`
    WHERE month_start = (SELECT MAX(month_start) FROM `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno`)
    ORDER BY total_cost_gbp DESC
    """
    
    print('⏳ Creating latest month DNO summary for visualization...')
    client.query(query_latest).result()
    print('✅ Created constraint_costs_by_dno_latest')
    
    # Verify and display results
    verify_query = """
    SELECT 
        dno_full_name,
        area_name,
        ROUND(area_sq_km, 0) as area_sq_km,
        total_cost_gbp,
        voltage_cost_gbp,
        thermal_cost_gbp,
        cost_per_sq_km
    FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_costs_by_dno_latest`
    ORDER BY total_cost_gbp DESC
    """
    
    df = client.query(verify_query).to_dataframe()
    print('\n📊 Latest Month DNO Constraint Costs:')
    print('='*100)
    print(df.to_string(index=False))
    
    # Timeline summary
    timeline_query = """
    SELECT 
        year,
        COUNT(DISTINCT month) as months,
        SUM(days) as total_days,
        ROUND(SUM(total_constraint_cost), 2) as annual_cost_gbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_costs_timeline`
    GROUP BY year
    ORDER BY year DESC
    """
    
    df_timeline = client.query(timeline_query).to_dataframe()
    print('\n📅 Constraint Costs by Year:')
    print(df_timeline.to_string(index=False))
    
    print('\n✅ COMPLETE: DNO constraint summary ready for Google Sheets visualization')
    print('\nNext Steps:')
    print('1. Open Google Sheets')
    print('2. Data → Data connectors → Connect to BigQuery')
    print('3. Select table: constraint_costs_by_dno_latest')
    print('4. Insert → Chart → Geo chart (choropleth map)')
    print('5. Region: area_name, Value: total_cost_gbp')

if __name__ == '__main__':
    create_dno_constraint_summary()
