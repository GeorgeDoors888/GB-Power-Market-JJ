#!/usr/bin/env python3
"""
Create NESO Constraint Cost Aggregations
Creates unified view and aggregation tables for constraint cost analysis
"""

from google.cloud import bigquery
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_unified_view(client):
    """Create unified view combining all FY tables"""
    print("Creating unified constraint view...")

    with open('create_constraint_unified_view.sql', 'r') as f:
        sql = f.read()

    job = client.query(sql)
    job.result()
    print(f"✅ Created view: v_neso_constraints_unified")

def create_monthly_summary(client):
    """Create monthly aggregation table"""
    print("\nCreating monthly summary table...")

    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.constraint_costs_monthly` AS
    SELECT
      financial_year,
      year,
      month,
      CONCAT(CAST(year AS STRING), '-', LPAD(CAST(month AS STRING), 2, '0')) as year_month,

      -- Cost aggregations
      SUM(thermal_cost_gbp) as thermal_cost_gbp,
      SUM(voltage_cost_gbp) as voltage_cost_gbp,
      SUM(largest_loss_cost_gbp) as largest_loss_cost_gbp,
      SUM(inertia_cost_gbp) as inertia_cost_gbp,
      SUM(total_cost_gbp) as total_cost_gbp,

      -- Volume aggregations
      SUM(thermal_volume_mwh) as thermal_volume_mwh,
      SUM(voltage_volume_mwh) as voltage_volume_mwh,
      SUM(largest_loss_volume_mwh) as largest_loss_volume_mwh,
      SUM(inertia_volume_mwh) as inertia_volume_mwh,
      SUM(total_volume_mwh) as total_volume_mwh,

      -- Average prices (£/MWh)
      SAFE_DIVIDE(SUM(thermal_cost_gbp), ABS(SUM(thermal_volume_mwh))) as thermal_price_per_mwh,
      SAFE_DIVIDE(SUM(voltage_cost_gbp), ABS(SUM(voltage_volume_mwh))) as voltage_price_per_mwh,
      SAFE_DIVIDE(SUM(largest_loss_cost_gbp), ABS(SUM(largest_loss_volume_mwh))) as loss_price_per_mwh,
      SAFE_DIVIDE(SUM(inertia_cost_gbp), ABS(SUM(inertia_volume_mwh))) as inertia_price_per_mwh,
      SAFE_DIVIDE(SUM(total_cost_gbp), ABS(SUM(total_volume_mwh))) as avg_price_per_mwh,

      -- Day counts
      COUNT(DISTINCT constraint_date) as days_in_period

    FROM `{PROJECT_ID}.{DATASET}.v_neso_constraints_unified`
    GROUP BY financial_year, year, month, year_month
    ORDER BY year_month DESC;
    """

    job = client.query(sql)
    result = job.result()
    rows = sum(1 for _ in result)
    print(f"✅ Created table: constraint_costs_monthly ({rows} rows)")

def create_annual_summary(client):
    """Create annual aggregation table"""
    print("\nCreating annual summary table...")

    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.constraint_costs_annual` AS
    SELECT
      financial_year,
      MIN(constraint_date) as period_start,
      MAX(constraint_date) as period_end,

      -- Cost aggregations
      SUM(thermal_cost_gbp) as thermal_cost_gbp,
      SUM(voltage_cost_gbp) as voltage_cost_gbp,
      SUM(largest_loss_cost_gbp) as largest_loss_cost_gbp,
      SUM(inertia_cost_gbp) as inertia_cost_gbp,
      SUM(total_cost_gbp) as total_cost_gbp,

      -- Volume aggregations
      SUM(thermal_volume_mwh) as thermal_volume_mwh,
      SUM(voltage_volume_mwh) as voltage_volume_mwh,
      SUM(largest_loss_volume_mwh) as largest_loss_volume_mwh,
      SUM(inertia_volume_mwh) as inertia_volume_mwh,
      SUM(total_volume_mwh) as total_volume_mwh,

      -- Average prices
      SAFE_DIVIDE(SUM(thermal_cost_gbp), ABS(SUM(thermal_volume_mwh))) as thermal_price_per_mwh,
      SAFE_DIVIDE(SUM(voltage_cost_gbp), ABS(SUM(voltage_volume_mwh))) as voltage_price_per_mwh,
      SAFE_DIVIDE(SUM(largest_loss_cost_gbp), ABS(SUM(largest_loss_volume_mwh))) as loss_price_per_mwh,
      SAFE_DIVIDE(SUM(inertia_cost_gbp), ABS(SUM(inertia_volume_mwh))) as inertia_price_per_mwh,
      SAFE_DIVIDE(SUM(total_cost_gbp), ABS(SUM(total_volume_mwh))) as avg_price_per_mwh,

      -- Breakdown percentages
      ROUND(100.0 * SUM(thermal_cost_gbp) / SUM(total_cost_gbp), 1) as thermal_pct,
      ROUND(100.0 * SUM(voltage_cost_gbp) / SUM(total_cost_gbp), 1) as voltage_pct,
      ROUND(100.0 * SUM(largest_loss_cost_gbp) / SUM(total_cost_gbp), 1) as loss_pct,
      ROUND(100.0 * SUM(inertia_cost_gbp) / SUM(total_cost_gbp), 1) as inertia_pct,

      COUNT(DISTINCT constraint_date) as days_in_period

    FROM `{PROJECT_ID}.{DATASET}.v_neso_constraints_unified`
    GROUP BY financial_year
    ORDER BY financial_year DESC;
    """

    job = client.query(sql)
    result = job.result()
    rows = sum(1 for _ in result)
    print(f"✅ Created table: constraint_costs_annual ({rows} rows)")

def create_trend_summary(client):
    """Create timeline for Sheets dashboard"""
    print("\nCreating trend summary for dashboard...")

    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.constraint_trend_summary` AS
    SELECT
      constraint_date,
      financial_year,

      -- Daily costs by type
      thermal_cost_gbp,
      voltage_cost_gbp,
      largest_loss_cost_gbp,
      inertia_cost_gbp,
      total_cost_gbp,

      -- Daily volumes by type
      thermal_volume_mwh,
      voltage_volume_mwh,
      largest_loss_volume_mwh,
      inertia_volume_mwh,
      total_volume_mwh,

      -- Daily average prices
      SAFE_DIVIDE(thermal_cost_gbp, ABS(thermal_volume_mwh)) as thermal_price_per_mwh,
      SAFE_DIVIDE(voltage_cost_gbp, ABS(voltage_volume_mwh)) as voltage_price_per_mwh,
      SAFE_DIVIDE(largest_loss_cost_gbp, ABS(largest_loss_volume_mwh)) as loss_price_per_mwh,
      SAFE_DIVIDE(inertia_cost_gbp, ABS(inertia_volume_mwh)) as inertia_price_per_mwh,
      SAFE_DIVIDE(total_cost_gbp, ABS(total_volume_mwh)) as avg_price_per_mwh,

      -- 7-day moving averages
      AVG(total_cost_gbp) OVER (ORDER BY constraint_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as cost_7d_avg,
      AVG(total_volume_mwh) OVER (ORDER BY constraint_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as volume_7d_avg,
      AVG(SAFE_DIVIDE(total_cost_gbp, ABS(total_volume_mwh))) OVER (ORDER BY constraint_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as price_7d_avg,

      -- 30-day moving averages
      AVG(total_cost_gbp) OVER (ORDER BY constraint_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as cost_30d_avg,

      -- Dominant constraint type
      CASE
        WHEN thermal_cost_gbp > voltage_cost_gbp
         AND thermal_cost_gbp > largest_loss_cost_gbp
         AND thermal_cost_gbp > inertia_cost_gbp THEN 'Thermal'
        WHEN voltage_cost_gbp > thermal_cost_gbp
         AND voltage_cost_gbp > largest_loss_cost_gbp
         AND voltage_cost_gbp > inertia_cost_gbp THEN 'Voltage'
        WHEN largest_loss_cost_gbp > thermal_cost_gbp
         AND largest_loss_cost_gbp > voltage_cost_gbp
         AND largest_loss_cost_gbp > inertia_cost_gbp THEN 'Loss'
        WHEN inertia_cost_gbp > thermal_cost_gbp
         AND inertia_cost_gbp > voltage_cost_gbp
         AND inertia_cost_gbp > largest_loss_cost_gbp THEN 'Inertia'
        ELSE 'Mixed'
      END as dominant_constraint

    FROM `{PROJECT_ID}.{DATASET}.v_neso_constraints_unified`
    ORDER BY constraint_date DESC;
    """

    job = client.query(sql)
    result = job.result()
    rows = sum(1 for _ in result)
    print(f"✅ Created table: constraint_trend_summary ({rows} rows)")

def show_sample_data(client):
    """Display sample data from new tables"""
    print("\n" + "="*80)
    print("SAMPLE DATA - Last 5 days")
    print("="*80)

    sql = f"""
    SELECT
      constraint_date,
      ROUND(total_cost_gbp, 0) as cost_gbp,
      ROUND(total_volume_mwh, 0) as volume_mwh,
      ROUND(avg_price_per_mwh, 2) as price_per_mwh,
      dominant_constraint
    FROM `{PROJECT_ID}.{DATASET}.constraint_trend_summary`
    ORDER BY constraint_date DESC
    LIMIT 5;
    """

    result = client.query(sql).result()
    for row in result:
        print(f"{row.constraint_date} | £{row.cost_gbp:>10,.0f} | {row.volume_mwh:>8,.0f} MWh | £{row.price_per_mwh:>6.2f}/MWh | {row.dominant_constraint}")

    print("\n" + "="*80)
    print("ANNUAL TOTALS (Last 5 Financial Years)")
    print("="*80)

    sql = f"""
    SELECT
      financial_year,
      ROUND(total_cost_gbp / 1000000, 1) as cost_millions,
      ROUND(thermal_pct, 1) as thermal_pct,
      ROUND(voltage_pct, 1) as voltage_pct,
      days_in_period
    FROM `{PROJECT_ID}.{DATASET}.constraint_costs_annual`
    ORDER BY financial_year DESC
    LIMIT 5;
    """

    result = client.query(sql).result()
    for row in result:
        print(f"FY{row.financial_year}-{str(row.financial_year+1)[-2:]} | £{row.cost_millions:>6.1f}M | Thermal: {row.thermal_pct:>4.1f}% | Voltage: {row.voltage_pct:>4.1f}% | {row.days_in_period} days")

def main():
    try:
        print(f"Connecting to BigQuery: {PROJECT_ID}.{DATASET}")
        client = bigquery.Client(project=PROJECT_ID, location="US")

        # Create unified view
        create_unified_view(client)

        # Create aggregation tables
        create_monthly_summary(client)
        create_annual_summary(client)
        create_trend_summary(client)

        # Show sample data
        show_sample_data(client)

        print("\n✅ ALL CONSTRAINT AGGREGATIONS CREATED SUCCESSFULLY")
        print(f"\nNew tables/views:")
        print(f"  - v_neso_constraints_unified (view - 3,358 rows)")
        print(f"  - constraint_costs_monthly (table)")
        print(f"  - constraint_costs_annual (table)")
        print(f"  - constraint_trend_summary (table - daily data for Sheets)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
