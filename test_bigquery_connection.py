#!/usr/bin/env python3
"""Test BigQuery connection and list available tables"""
import os
from google.cloud import bigquery

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('~/.config/google-cloud/bigquery-credentials.json')

client = bigquery.Client(project='inner-cinema-476211-u9')

print("Testing BigQuery Connection...")
print(f"Project: {client.project}")

# List datasets
print("\nAvailable Datasets:")
for dataset in client.list_datasets():
    print(f"  - {dataset.dataset_id}")

# List tables in uk_energy_prod
print("\nTables in uk_energy_prod:")
dataset_ref = client.dataset('uk_energy_prod')
for table in client.list_tables(dataset_ref):
    print(f"  - {table.table_id}")
    
print("\n✅ Connection successful!")
