from google.cloud import bigquery

client = bigquery.Client(project='inner-cinema-476211-u9')

print('🔍 CHECKING BIGQUERY SCHEMAS FOR UNIQUENESS CONSTRAINTS')
print('=' * 70)
print()

# Check a few key tables to see if they have any uniqueness constraints
tables_to_check = ['bmrs_bod', 'bmrs_fuelinst', 'bmrs_freq']

for table_id in tables_to_check:
    try:
        table_ref = client.dataset('uk_energy_prod').table(table_id)
        table_obj = client.get_table(table_ref)
        
        print(f'{table_id.upper()}:')
        print(f'  Table type: {table_obj.table_type}')
        print(f'  Clustering fields: {table_obj.clustering_fields or "None"}')
        print(f'  Partitioning: {table_obj.time_partitioning or "None"}')
        print(f'  Primary key: N/A (BigQuery does not enforce primary keys)')
        
        # Show key columns that could form a unique constraint
        date_cols = []
        period_cols = []
        
        for field in table_obj.schema:
            if 'date' in field.name.lower() or 'time' in field.name.lower():
                date_cols.append(field.name)
            if 'period' in field.name.lower() or 'settlement' in field.name.lower():
                period_cols.append(field.name)
        
        print(f'  Date/Time columns: {date_cols}')
        print(f'  Period columns: {period_cols}')
        print()
    except Exception as e:
        print(f'{table_id}: Error - {e}')
        print()

print('=' * 70)
print('KEY FINDINGS:')
print('=' * 70)
print()
print('❌ BigQuery does NOT enforce uniqueness constraints')
print('❌ No primary keys or unique indexes')
print('❌ Tables allow duplicate rows')
print()
print('The script uses WRITE_APPEND mode which:')
print('  - Adds new rows to existing table')
print('  - Does NOT check for duplicates')
print('  - Does NOT prevent duplicate inserts')
print()
print('If we load the same date range twice:')
print('  ⚠️  All rows will be inserted again (duplicates created)')
