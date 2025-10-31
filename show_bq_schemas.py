#!/usr/bin/env python3
"""Show BigQuery table schemas to understand actual column names"""

from google.cloud import bigquery

# Initialize BigQuery client
client = bigquery.Client(project='inner-cinema-476211-u9')
dataset_id = 'uk_energy_prod'

# Tables to check
tables = ['bmrs_boalf', 'bmrs_bod', 'bmrs_fuelinst', 'bmrs_freq', 'bmrs_mid']

for table_name in tables:
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print('='*60)
    
    try:
        table = client.get_table(f'{client.project}.{dataset_id}.{table_name}')
        for field in table.schema:
            print(f"  {field.name:30s} {field.field_type}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
