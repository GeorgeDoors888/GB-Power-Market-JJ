#!/usr/bin/env python3
"""
Deploy BigQuery view v_bess_cashflow_inputs using Python
Alternative to: bq query --use_legacy_sql=false < bigquery_views/v_bess_cashflow_inputs.sql
"""
from google.cloud import bigquery
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
VIEW_NAME = "v_bess_cashflow_inputs"

print("=" * 80)
print("DEPLOY BIGQUERY VIEW: v_bess_cashflow_inputs")
print("=" * 80)

# Read SQL from file
sql_file = "bigquery_views/v_bess_cashflow_inputs.sql"
print(f"\n📂 Reading SQL from: {sql_file}")

try:
    with open(sql_file, 'r') as f:
        sql = f.read()
    print(f"✅ SQL loaded ({len(sql)} characters)")
except FileNotFoundError:
    print(f"❌ File not found: {sql_file}")
    print("\n💡 The view SQL doesn't exist yet.")
    print("   This is expected - the enhanced model queries raw tables directly.")
    print("   The view is optional for optimization.")
    exit(0)

# Connect to BigQuery
client = bigquery.Client(project=PROJECT_ID, location="US")
print(f"\n🔐 Connected to BigQuery project: {PROJECT_ID}")

# Create or replace view
view_id = f"{PROJECT_ID}.{DATASET}.{VIEW_NAME}"
print(f"\n🔨 Creating view: {view_id}")

try:
    query_job = client.query(sql)
    query_job.result()  # Wait for completion
    print(f"✅ View created successfully!")
    
    # Verify it exists
    view = client.get_table(view_id)
    print(f"\n📊 View details:")
    print(f"   Full ID: {view.full_table_id}")
    print(f"   Created: {view.created}")
    print(f"   Type: {view.table_type}")
    
except Exception as e:
    print(f"❌ Error creating view: {e}")
    exit(1)

print("\n" + "=" * 80)
print("✅ DEPLOYMENT COMPLETE")
print("=" * 80)
print("\nNext step: Run the pipeline")
print("  python3 dashboard_pipeline.py")
