#!/usr/bin/env python3
"""
Create BigQuery table for HH DATA storage
Replaces Google Sheets storage with fast BigQuery table
"""

from google.cloud import bigquery
from google.cloud.exceptions import Conflict

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "hh_data_btm_generated"

client = bigquery.Client(project=PROJECT_ID, location="US")

# Define schema
schema = [
    bigquery.SchemaField("timestamp", "DATETIME", mode="REQUIRED"),
    bigquery.SchemaField("settlement_period", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("day_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("demand_kw", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("profile_pct", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("supply_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("scale_value", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("generated_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("generated_by", "STRING", mode="NULLABLE"),
]

# Table reference
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
table = bigquery.Table(table_id, schema=schema)

# Set partitioning (by generated_at date)
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="generated_at"
)

# Set clustering
table.clustering_fields = ["supply_type", "day_type"]

# Set description
table.description = "BtM HH demand profiles from UK Power Networks API. Replaces Google Sheets storage. Auto-cleanup after 90 days."

try:
    table = client.create_table(table)
    print(f"✅ Created table: {table.project}.{table.dataset_id}.{table.table_id}")
    print(f"   Schema: {len(table.schema)} fields")
    print(f"   Partitioned by: {table.time_partitioning.field}")
    print(f"   Clustered by: {', '.join(table.clustering_fields)}")
except Conflict:
    print(f"⚠️  Table {table_id} already exists")
    print("   Use: bq rm -t inner-cinema-476211-u9:uk_energy_prod.hh_data_btm_generated")
    print("   Then re-run this script to recreate")
except Exception as e:
    print(f"❌ Error creating table: {e}")
    raise
