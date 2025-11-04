#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()

print("🗑️  Removing duplicate entries...\n")
print("This keeps the most recent version of each file.\n")

# Use a DELETE query that works with streaming buffer by using MERGE
# Instead we'll create a new table with deduplicated data
query = """
CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_insights.documents_dedup` AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT 
    *,
    ROW_NUMBER() OVER (PARTITION BY drive_id ORDER BY indexed_at DESC) as row_num
  FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
)
WHERE row_num = 1
"""

print("⏳ Creating deduplicated table...")
job = bq.query(query)
job.result()

print("✅ Deduplicated table created: documents_dedup\n")

# Check counts
result = bq.query("""
SELECT 
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.documents`) as old_count,
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.documents_dedup`) as new_count
""").result()

for row in result:
    print(f"📊 Original table: {row.old_count:,} rows")
    print(f"📊 Deduplicated table: {row.new_count:,} rows")
    print(f"🗑️  Removed: {row.old_count - row.new_count:,} duplicates")

print("\n✅ To use the clean table, you can:")
print("   1. Keep both tables (documents = raw, documents_dedup = clean)")
print("   2. Or rename documents_dedup to documents")
