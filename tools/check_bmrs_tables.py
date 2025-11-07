#!/usr/bin/env python3
"""
Quick script to check available BMRS tables and their schemas
"""
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json'

bq = bigquery.Client(project='inner-cinema-476211-u9')

print("📊 Available BMRS Tables in uk_energy_prod:\n")

# List all tables
tables = list(bq.list_tables('uk_energy_prod'))

bmrs_tables = [t for t in tables if t.table_id.startswith('bmrs_')]

for table in sorted(bmrs_tables, key=lambda x: x.table_id):
    # Get row count
    query = f"SELECT COUNT(*) as cnt FROM `inner-cinema-476211-u9.uk_energy_prod.{table.table_id}`"
    result = bq.query(query).result()
    count = list(result)[0]['cnt']
    
    print(f"✓ {table.table_id:30s} {count:>15,} rows")

print("\n" + "="*60)
print("Key tables for dashboard:")
print("="*60)

# Check specific tables
check_tables = ['bmrs_mid', 'bmrs_indgen_iris', 'bmrs_boalf', 'bmrs_bod']

for table_name in check_tables:
    if table_name in [t.table_id for t in bmrs_tables]:
        print(f"\n📋 {table_name}:")
        table = bq.get_table(f'inner-cinema-476211-u9.uk_energy_prod.{table_name}')
        print(f"   Columns: {', '.join([f.name for f in table.schema[:10]])}")
        if len(table.schema) > 10:
            print(f"   ... and {len(table.schema) - 10} more")
