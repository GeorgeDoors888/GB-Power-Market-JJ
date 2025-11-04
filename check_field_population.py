#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()
print("📊 Field Population Check:")
print("=" * 60)

query = """
SELECT 
  COUNT(*) as total,
  COUNT(doc_id) as has_doc_id,
  COUNT(drive_id) as has_drive_id,
  COUNT(name) as has_name,
  COUNT(path) as has_path,
  COUNT(mime_type) as has_mime_type,
  COUNT(sha1) as has_sha1,
  COUNT(size_bytes) as has_size_bytes,
  COUNT(created) as has_created,
  COUNT(updated) as has_updated,
  COUNT(web_view_link) as has_web_view_link,
  COUNT(owners) as has_owners
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
"""

result = bq.query(query).result()
for row in result:
    total = row.total
    print(f"\nTotal rows: {total:,}\n")
    for field in row.keys():
        if field != 'total':
            value = row[field]
            pct = (value / total * 100) if total > 0 else 0
            field_name = field.replace('has_', '')
            print(f"  {field_name:20} {value:>8,} ({pct:>5.1f}%)")

# Now check if we can identify duplicates by other means
print("\n\n📋 Duplicate Detection Without SHA1:")
print("=" * 60)

# Check if duplicates have identical metadata
query2 = """
SELECT 
  drive_id,
  name,
  COUNT(*) as times_indexed,
  COUNT(DISTINCT size_bytes) as unique_sizes,
  COUNT(DISTINCT updated) as unique_update_times,
  COUNT(DISTINCT mime_type) as unique_mime_types,
  ARRAY_AGG(DISTINCT CAST(size_bytes AS STRING) LIMIT 3) as sizes,
  ARRAY_AGG(DISTINCT CAST(updated AS STRING) LIMIT 3) as update_times
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
GROUP BY drive_id, name
HAVING COUNT(*) > 1
LIMIT 10
"""

print("\nSample of duplicate entries with metadata comparison:")
print("-" * 60)
result = bq.query(query2).result()
for row in result:
    print(f"\n  File: {row.name}")
    print(f"  Times indexed: {row.times_indexed}")
    print(f"  Unique sizes: {row.unique_sizes} - {row.sizes}")
    print(f"  Unique update times: {row.unique_update_times} - {row.update_times}")
    print(f"  Unique MIME types: {row.unique_mime_types}")

print("\n✅ Analysis complete!")
