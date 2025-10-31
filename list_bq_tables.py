#!/usr/bin/env python3
"""Show what tables actually exist in BigQuery"""

from google.cloud import bigquery

client = bigquery.Client(project='inner-cinema-476211-u9')

# List tables in uk_energy_prod
tables = client.list_tables('inner-cinema-476211-u9.uk_energy_prod')

print("Tables in uk_energy_prod:")
for table in tables:
    print(f"  {table.table_id}")
