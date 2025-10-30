#!/usr/bin/env python3
"""
Clear FUELINST/FREQ/FUELHH tables to remove empty window metadata
"""

from google.cloud import bigquery

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT)

tables_to_clear = ["bmrs_fuelinst", "bmrs_freq", "bmrs_fuelhh"]

print("=" * 70)
print("CLEARING FUELINST/FREQ/FUELHH TABLES")
print("=" * 70)
print()

for table_name in tables_to_clear:
    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    
    try:
        # Check if table exists
        table = client.get_table(table_id)
        
        # Get current row count
        query = f"SELECT COUNT(*) as count FROM `{table_id}`"
        result = client.query(query).result()
        current_rows = list(result)[0]['count']
        
        print(f"📊 {table_name}: {current_rows:,} rows currently")
        
        # Delete all data
        delete_query = f"DELETE FROM `{table_id}` WHERE TRUE"
        print(f"🗑️  Deleting all data from {table_name}...", end=" ", flush=True)
        
        job = client.query(delete_query)
        result = job.result()
        
        rows_deleted = job.num_dml_affected_rows if hasattr(job, 'num_dml_affected_rows') else current_rows
        print(f"✅ Deleted {rows_deleted:,} rows")
        
    except Exception as e:
        error_msg = str(e)
        if "Not found" in error_msg:
            print(f"⏭️  {table_name}: Table doesn't exist (will be created fresh)")
        else:
            print(f"❌ {table_name}: Error: {error_msg[:80]}")

print()
print("=" * 70)
print("✅ TABLES CLEARED - Ready for fresh FUELINST data!")
print("=" * 70)
