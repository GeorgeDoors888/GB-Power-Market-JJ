#!/usr/bin/env python3
"""
Inspect the actual schema of our BigQuery tables to understand the data structure
"""

from google.cloud import bigquery
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/georgemajor/GB Power Market JJ/jibber_jabber_key.json"

client = bigquery.Client(project=PROJECT_ID)

print("=" * 80)
print("🔍 INSPECTING TABLE SCHEMAS")
print("=" * 80)
print()

# Get all tables
tables_query = f"""
SELECT table_name
FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
WHERE table_name NOT LIKE '%INFORMATION_SCHEMA%'
LIMIT 20
"""

print("📊 Available tables:")
print("-" * 80)
results = client.query(tables_query).result()
table_list = []
for row in results:
    print(f"   {row.table_name}")
    table_list.append(row.table_name)

print()
print("=" * 80)
print("🔬 INSPECTING KEY TABLE SCHEMAS")
print("=" * 80)

# Inspect specific tables of interest
key_tables = ["generation_fuel_instant", "pn_2025", "fuelinst_sep_oct_2025"]

for table_name in key_tables:
    if table_name in table_list:
        print()
        print(f"📋 Schema for: {table_name}")
        print("-" * 80)
        
        table_ref = client.dataset(DATASET_ID).table(table_name)
        table = client.get_table(table_ref)
        
        for field in table.schema:
            print(f"   {field.name:30} : {field.field_type:15} ({field.mode})")
        
        # Show sample row
        print("\n   Sample data:")
        sample_query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
        LIMIT 1
        """
        sample_result = client.query(sample_query).result()
        for row in sample_result:
            for key, value in row.items():
                print(f"      {key}: {value}")
