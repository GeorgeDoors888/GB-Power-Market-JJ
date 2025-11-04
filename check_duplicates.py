#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()

print("🔍 Checking for duplicates...\n")

# Check total unique file IDs vs total rows
query = """
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT drive_id) as unique_files
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
"""

result = bq.query(query).result()
for row in result:
    print(f"📊 Total rows: {row.total_rows:,}")
    print(f"📊 Unique files: {row.unique_files:,}")
    duplicates = row.total_rows - row.unique_files
    print(f"🔄 Duplicates: {duplicates:,}\n")
    
    if duplicates > 0:
        print("ℹ️  Files were indexed twice (old filter + new filter)")
        print("   Real total: ~{:,} unique files".format(row.unique_files))
