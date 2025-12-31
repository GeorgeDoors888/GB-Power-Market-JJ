#!/usr/bin/env python3
"""
Ingest NESO Day-Ahead Constraint Limit Data
Downloads and processes NESO's published day-ahead constraint forecasts
Enables forecast vs actual constraint analysis
"""

from google.cloud import bigquery
import pandas as pd
import requests
from datetime import datetime, timedelta
import io

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# NESO Data Portal URLs (these are examples - actual URLs from NESO website)
NESO_DATA_PORTAL = "https://data.nationalgrideso.com"

def create_neso_constraint_forecast_table():
    """Create table for NESO day-ahead constraint forecasts"""

    print("\n📋 Creating NESO day-ahead constraint forecast table...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    schema = [
        bigquery.SchemaField("forecast_date", "DATE", description="Date forecast was published"),
        bigquery.SchemaField("target_date", "DATE", description="Date forecast is for"),
        bigquery.SchemaField("settlement_period", "INTEGER", description="Settlement period (1-50)"),
        bigquery.SchemaField("constraint_boundary", "STRING", description="Transmission boundary (e.g., B6, B7a, Scotland-England)"),
        bigquery.SchemaField("direction", "STRING", description="Flow direction (North-South, South-North)"),
        bigquery.SchemaField("forecast_limit_mw", "FLOAT64", description="Forecast constraint limit (MW)"),
        bigquery.SchemaField("forecast_flow_mw", "FLOAT64", description="Forecast power flow (MW)"),
        bigquery.SchemaField("forecast_margin_mw", "FLOAT64", description="Forecast margin (limit - flow)"),
        bigquery.SchemaField("constraint_expected", "BOOLEAN", description="Whether constraint action expected"),
        bigquery.SchemaField("boundary_type", "STRING", description="Internal or Interconnector"),
        bigquery.SchemaField("voltage_level_kv", "INTEGER", description="Voltage level (400kV, 275kV, etc.)"),
        bigquery.SchemaField("affected_gsp_groups", "STRING", description="GSP groups affected (comma-separated)"),
        bigquery.SchemaField("source_file", "STRING", description="Source data file"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP", description="Data ingestion timestamp"),
    ]

    table_id = f"{PROJECT_ID}.{DATASET}.neso_constraint_forecast_day_ahead"

    table = bigquery.Table(table_id, schema=schema)
    table.description = "NESO day-ahead constraint limit forecasts for transmission boundaries"
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="target_date"
    )
    table.clustering_fields = ["constraint_boundary", "settlement_period"]

    try:
        table = client.create_table(table)
        print(f"✅ Created table: {table_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"⚠️  Table already exists: {table_id}")
            table = client.get_table(table_id)
        else:
            raise

    return table

def load_sample_constraint_forecasts():
    """
    Load sample constraint forecast data

    NOTE: Real implementation would:
    1. Download from NESO Data Portal (https://data.nationalgrideso.com)
    2. Parse Excel/CSV files with constraint limits
    3. Process boundary-specific forecasts

    Common boundaries:
    - B6: Scottish export limit (Scotland → England)
    - B7a: Cheviot constraint (Scotland → England)
    - B8: Harker constraint (Scotland → England via west coast)
    - B14: Beauly-Denny (North Scotland → Central Scotland)
    - B15: East Coast constraint (Northeast → Southeast)
    """

    print("\n📥 Loading sample constraint forecasts...")
    print("   NOTE: Real implementation requires NESO Data Portal integration")

    # Sample data showing typical constraint patterns
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    forecasts = []

    # B6 boundary (Scottish export) - typically constrained during high wind
    for sp in range(1, 51):
        # Morning valley (low constraint)
        if sp <= 12:  # 00:00-06:00
            limit = 4800
            flow = 2500
        # Peak export (high constraint)
        elif sp <= 24:  # 06:00-12:00
            limit = 4800
            flow = 4600  # Near limit
        # Afternoon (moderate)
        elif sp <= 36:  # 12:00-18:00
            limit = 4800
            flow = 4200
        # Evening peak (high constraint)
        else:  # 18:00-00:00
            limit = 4800
            flow = 4700  # Very constrained

        margin = limit - flow
        constrained = margin < 500  # Less than 500 MW margin

        forecasts.append({
            'forecast_date': today.isoformat(),
            'target_date': tomorrow.isoformat(),
            'settlement_period': sp,
            'constraint_boundary': 'B6',
            'direction': 'North-South',
            'forecast_limit_mw': limit,
            'forecast_flow_mw': flow,
            'forecast_margin_mw': margin,
            'constraint_expected': constrained,
            'boundary_type': 'Internal',
            'voltage_level_kv': 400,
            'affected_gsp_groups': 'South Scotland,North Eastern,Yorkshire',
            'source_file': 'sample_data_demonstration',
            'ingested_at': datetime.utcnow().isoformat()
        })

    # B7a boundary (Cheviot) - eastern Scotland export
    for sp in range(1, 51):
        limit = 2200
        # High wind periods = high flow
        if sp in range(18, 26):  # Morning wind peak
            flow = 2100
        elif sp in range(30, 38):  # Afternoon wind
            flow = 2050
        else:
            flow = 1600

        margin = limit - flow

        forecasts.append({
            'forecast_date': today.isoformat(),
            'target_date': tomorrow.isoformat(),
            'settlement_period': sp,
            'constraint_boundary': 'B7a',
            'direction': 'North-South',
            'forecast_limit_mw': limit,
            'forecast_flow_mw': flow,
            'forecast_margin_mw': margin,
            'constraint_expected': margin < 300,
            'boundary_type': 'Internal',
            'voltage_level_kv': 400,
            'affected_gsp_groups': 'South Scotland,North Eastern',
            'source_file': 'sample_data_demonstration',
            'ingested_at': datetime.utcnow().isoformat()
        })

    # B14 boundary (Beauly-Denny, North Scotland internal)
    for sp in range(1, 51):
        limit = 1800
        # Wind farm generation in north Scotland
        if sp in range(20, 30):  # Windy morning
            flow = 1700
        else:
            flow = 1200

        margin = limit - flow

        forecasts.append({
            'forecast_date': today.isoformat(),
            'target_date': tomorrow.isoformat(),
            'settlement_period': sp,
            'constraint_boundary': 'B14',
            'direction': 'North-South',
            'forecast_limit_mw': limit,
            'forecast_flow_mw': flow,
            'forecast_margin_mw': margin,
            'constraint_expected': margin < 200,
            'boundary_type': 'Internal',
            'voltage_level_kv': 275,
            'affected_gsp_groups': 'North Scotland,South Scotland',
            'source_file': 'sample_data_demonstration',
            'ingested_at': datetime.utcnow().isoformat()
        })

    print(f"  Generated {len(forecasts)} sample forecast records")
    print(f"  Boundaries: B6 (Scottish export), B7a (Cheviot), B14 (Beauly-Denny)")
    print(f"  Date: {tomorrow}")

    return forecasts

def ingest_forecasts(forecasts):
    """Load forecast data into BigQuery"""

    print("\n📤 Uploading forecasts to BigQuery...")

    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.neso_constraint_forecast_day_ahead"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_json(forecasts, table_id, job_config=job_config)
    job.result()

    table = client.get_table(table_id)
    print(f"✅ Loaded {len(forecasts)} forecasts")
    print(f"   Total rows in table: {table.num_rows:,}")

def create_forecast_vs_actual_view():
    """Create view comparing forecast constraints vs actual BOALF acceptances"""

    print("\n🔗 Creating forecast vs actual comparison view...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    sql = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.v_constraint_forecast_vs_actual` AS
    WITH forecast AS (
      SELECT
        target_date,
        settlement_period,
        constraint_boundary,
        forecast_limit_mw,
        forecast_flow_mw,
        forecast_margin_mw,
        constraint_expected
      FROM `{PROJECT_ID}.{DATASET}.neso_constraint_forecast_day_ahead`
    ),

    actual AS (
      SELECT
        CAST(acceptanceTime AS DATE) as acceptance_date,
        EXTRACT(HOUR FROM acceptanceTime) * 2 +
          CASE WHEN EXTRACT(MINUTE FROM acceptanceTime) >= 30 THEN 2 ELSE 1 END as settlement_period,
        COUNT(*) as acceptance_count,
        SUM(ABS(levelTo - levelFrom)) as total_volume_mw,
        COUNT(DISTINCT bmUnit) as bmu_count
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE acceptanceTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
      GROUP BY acceptance_date, settlement_period
    )

    SELECT
      f.target_date,
      f.settlement_period,
      f.constraint_boundary,
      f.forecast_limit_mw,
      f.forecast_flow_mw,
      f.forecast_margin_mw,
      f.constraint_expected as forecast_constrained,

      -- Actual constraint activity
      a.acceptance_count,
      a.total_volume_mw as actual_constrained_mw,
      a.bmu_count,

      -- Comparison metrics
      CASE
        WHEN a.acceptance_count IS NULL THEN FALSE
        WHEN a.acceptance_count > 10 THEN TRUE  -- Threshold for "constrained"
        ELSE FALSE
      END as actually_constrained,

      -- Forecast accuracy
      CASE
        WHEN f.constraint_expected = TRUE AND a.acceptance_count > 10 THEN 'Correct: Constrained'
        WHEN f.constraint_expected = FALSE AND (a.acceptance_count IS NULL OR a.acceptance_count <= 10) THEN 'Correct: Not Constrained'
        WHEN f.constraint_expected = TRUE AND (a.acceptance_count IS NULL OR a.acceptance_count <= 10) THEN 'False Positive'
        ELSE 'Missed Constraint'
      END as forecast_accuracy

    FROM forecast f
    LEFT JOIN actual a
      ON f.target_date = a.acceptance_date
      AND f.settlement_period = a.settlement_period
    ORDER BY f.target_date DESC, f.settlement_period, f.constraint_boundary
    """

    job = client.query(sql)
    job.result()

    print(f"✅ Created view: v_constraint_forecast_vs_actual")

def analyze_forecasts():
    """Analyze forecast data"""

    print("\n📊 Analyzing constraint forecasts...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    sql = f"""
    SELECT
      constraint_boundary,
      COUNT(*) as period_count,
      SUM(CASE WHEN constraint_expected THEN 1 ELSE 0 END) as constrained_periods,
      AVG(forecast_limit_mw) as avg_limit_mw,
      AVG(forecast_flow_mw) as avg_flow_mw,
      AVG(forecast_margin_mw) as avg_margin_mw,
      MIN(forecast_margin_mw) as min_margin_mw
    FROM `{PROJECT_ID}.{DATASET}.neso_constraint_forecast_day_ahead`
    GROUP BY constraint_boundary
    ORDER BY constrained_periods DESC
    """

    df = client.query(sql).to_dataframe()

    if len(df) > 0:
        print("\n  Forecast Summary by Boundary:")
        print("  " + "="*90)
        print(f"  {'Boundary':<15} {'Periods':>8} {'Constrained':>12} {'Avg Limit':>12} {'Avg Flow':>12} {'Min Margin':>12}")
        print("  " + "-"*90)
        for _, row in df.iterrows():
            print(f"  {row['constraint_boundary']:<15} {row['period_count']:>8} {row['constrained_periods']:>12} "
                  f"{row['avg_limit_mw']:>12,.0f} {row['avg_flow_mw']:>12,.0f} {row['min_margin_mw']:>12,.0f}")

    return df

def main():
    print("="*80)
    print("NESO DAY-AHEAD CONSTRAINT FORECAST INGESTION")
    print("="*80)
    print("\nPurpose: Ingest NESO's published day-ahead constraint limit forecasts")
    print("Enables: Forecast vs actual constraint analysis, boundary monitoring")
    print("\nKey Boundaries:")
    print("  • B6: Scottish export (Scotland → England)")
    print("  • B7a: Cheviot (eastern Scotland export)")
    print("  • B8: Harker (western Scotland export)")
    print("  • B14: Beauly-Denny (North Scotland internal)")
    print("  • B15: East Coast (Northeast → Southeast)")

    # Create table
    create_neso_constraint_forecast_table()

    # Load sample data
    forecasts = load_sample_constraint_forecasts()

    # Ingest
    ingest_forecasts(forecasts)

    # Create comparison view
    create_forecast_vs_actual_view()

    # Analyze
    df = analyze_forecasts()

    print("\n" + "="*80)
    print("✅ NESO DAY-AHEAD CONSTRAINT FORECAST INGESTION COMPLETE")
    print("="*80)
    print(f"\nData loaded:")
    print(f"  • Table: neso_constraint_forecast_day_ahead")
    print(f"  • View: v_constraint_forecast_vs_actual")
    print(f"  • Forecasts: {len(forecasts)} periods across 3 boundaries")
    print(f"\nQuery examples:")
    print(f"  -- View forecasts")
    print(f"  SELECT * FROM `{PROJECT_ID}.{DATASET}.neso_constraint_forecast_day_ahead`")
    print(f"  WHERE target_date = CURRENT_DATE() + 1;")
    print(f"\n  -- Compare forecast vs actual")
    print(f"  SELECT * FROM `{PROJECT_ID}.{DATASET}.v_constraint_forecast_vs_actual`")
    print(f"  WHERE forecast_accuracy IN ('False Positive', 'Missed Constraint');")
    print(f"\n⚠️  NOTE: This is sample data. Real implementation requires:")
    print(f"     1. NESO Data Portal API integration")
    print(f"     2. Daily automated download of constraint limit files")
    print(f"     3. Parsing of boundary-specific forecasts")
    print(f"     4. Historical backfill from NESO archives")

if __name__ == "__main__":
    main()
