#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()

print("🗑️  Removing duplicate entries...\n")

# Create deduplicated table using updated timestamp
query = """
CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_insights.documents_clean` AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT 
    *,
    ROW_NUMBER() OVER (PARTITION BY drive_id ORDER BY updated DESC) as row_num
  FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
)
WHERE row_num = 1
"""

print("⏳ Creating clean table...")
job = bq.query(query)
job.result()

print("✅ Clean table created!\n")

# Check counts
result = bq.query("""
SELECT 
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.documents`) as old_count,
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`) as new_count
""").result()

for row in result:
    print(f"📊 Original table: {row.old_count:,} rows (with duplicates)")
    print(f"📊 Clean table: {row.new_count:,} rows (unique files)")
    print(f"🗑️  Removed: {row.old_count - row.new_count:,} duplicates\n")

# Get breakdown of clean data
print("📄 File Type Breakdown (Clean Data):")
result2 = bq.query("""
SELECT mime_type, COUNT(*) as count 
FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean` 
GROUP BY mime_type 
ORDER BY count DESC 
LIMIT 10
""").result()

for row in result2:
    type_name = row.mime_type.split("/")[-1] if "/" in row.mime_type else row.mime_type
    print(f"  {row.count:>7,} × {type_name}")

print("\n✅ Use 'documents_clean' table for queries to avoid duplicates")
