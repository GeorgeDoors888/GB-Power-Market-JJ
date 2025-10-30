#!/usr/bin/env python3
"""
Delete all 2023 data from BigQuery tables to prepare for clean restart
"""

from google.cloud import bigquery

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT)

print("🗑️  DELETING ALL 2023 DATA FROM BIGQUERY")
print("=" * 70)
print()

# Get all tables
dataset = client.get_dataset(DATASET)
tables = list(client.list_tables(dataset))

print(f"Found {len(tables)} tables in {DATASET}")
print()

deleted_count = 0
skipped_count = 0

for table_info in tables:
    table_name = table_info.table_id
    
    # Skip non-BMRS tables
    if not table_name.startswith('bmrs_'):
        skipped_count += 1
        continue
    
    try:
        # Delete 2023 data from this table
        query = f"""
        DELETE FROM `{PROJECT}.{DATASET}.{table_name}`
        WHERE EXTRACT(YEAR FROM settlementDate) = 2023
        """
        
        print(f"Deleting 2023 data from {table_name}...", end=" ", flush=True)
        
        job = client.query(query)
        result = job.result()
        
        print(f"✅ Deleted {job.num_dml_affected_rows:,} rows")
        deleted_count += 1
        
    except Exception as e:
        error_msg = str(e)
        if "Unrecognized name: settlementDate" in error_msg:
            print(f"⏭️  No settlementDate column (skipped)")
            skipped_count += 1
        else:
            print(f"❌ Error: {error_msg[:60]}")
            skipped_count += 1

print()
print("=" * 70)
print(f"✅ Cleaned {deleted_count} tables")
print(f"⏭️  Skipped {skipped_count} tables (no settlementDate or errors)")
print()
print("Ready to restart 2023 ingestion!")
