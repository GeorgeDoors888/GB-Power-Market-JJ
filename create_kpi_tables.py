#!/usr/bin/env python3
"""Create BigQuery tables for BM KPIs"""
import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")

# Market KPIs schema
market_schema = [
    bigquery.SchemaField("start_date", "DATE"),
    bigquery.SchemaField("end_date", "DATE"),
    bigquery.SchemaField("computation_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("total_bm_cashflow", "FLOAT"),
    bigquery.SchemaField("total_accepted_mwh", "FLOAT"),
    bigquery.SchemaField("system_direction_mwh", "FLOAT"),
    bigquery.SchemaField("ewap_overall", "FLOAT"),
    bigquery.SchemaField("dispatch_intensity", "FLOAT"),
    bigquery.SchemaField("top1_share", "FLOAT"),
    bigquery.SchemaField("top5_share", "FLOAT"),
    bigquery.SchemaField("workhorse_index", "FLOAT"),
]

# Stack KPIs schema
stack_schema = [
    bigquery.SchemaField("bmu_name", "STRING"),
    bigquery.SchemaField("start_date", "DATE"),
    bigquery.SchemaField("end_date", "DATE"),
    bigquery.SchemaField("computation_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("stack_depth", "FLOAT"),
    bigquery.SchemaField("defensive_share", "FLOAT"),
    bigquery.SchemaField("offered_flex_mw", "FLOAT"),
    bigquery.SchemaField("indicative_spread", "FLOAT"),
]

# BMU KPIs schema
bmu_schema = [
    bigquery.SchemaField("bmu_name", "STRING"),
    bigquery.SchemaField("start_date", "DATE"),
    bigquery.SchemaField("end_date", "DATE"),
    bigquery.SchemaField("computation_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("net_bm_revenue", "FLOAT"),
    bigquery.SchemaField("discharge_revenue", "FLOAT"),
    bigquery.SchemaField("charge_revenue", "FLOAT"),
    bigquery.SchemaField("offer_mwh", "FLOAT"),
    bigquery.SchemaField("bid_mwh", "FLOAT"),
    bigquery.SchemaField("net_mwh", "FLOAT"),
    bigquery.SchemaField("ewap", "FLOAT"),
    bigquery.SchemaField("active_sps", "INTEGER"),
    bigquery.SchemaField("active_sp_ratio", "FLOAT"),
    bigquery.SchemaField("acceptance_count", "INTEGER"),
    bigquery.SchemaField("granularity", "FLOAT"),
    bigquery.SchemaField("morning_share", "FLOAT"),
]

tables = [
    ("bm_market_kpis", market_schema, "start_date"),
    ("bm_stack_kpis", stack_schema, "start_date"),
    ("bm_bmu_kpis", bmu_schema, "start_date"),
]

for table_name, schema, partition_field in tables:
    table_id = f"inner-cinema-476211-u9.uk_energy_prod.{table_name}"
    
    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field=partition_field
    )
    
    try:
        client.create_table(table)
        print(f"✅ Created {table_name}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"ℹ️  {table_name} already exists")
        else:
            print(f"❌ Failed to create {table_name}: {e}")

print("✅ All KPI tables ready")
