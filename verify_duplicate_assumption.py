#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()

print("🔍 VERIFYING DUPLICATE ASSUMPTION")
print("=" * 70)

# First, check if SHA1 is even populated
print("\n1. Checking SHA1 field population:")
print("-" * 70)
query1 = """
SELECT 
  COUNT(*) as total_rows,
  COUNT(sha1) as rows_with_sha1,
  COUNT(DISTINCT sha1) as unique_sha1_values,
  ROUND(COUNT(sha1) * 100.0 / COUNT(*), 2) as percent_populated
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
"""

result = bq.query(query1).result()
for row in result:
    print(f"   Total rows: {row.total_rows:,}")
    print(f"   Rows with SHA1: {row.rows_with_sha1:,}")
    print(f"   Unique SHA1 values: {row.unique_sha1_values:,}")
    print(f"   SHA1 populated: {row.percent_populated}%")

# Check for duplicates by drive_id with different SHA1 values
print("\n\n2. Files with same drive_id but DIFFERENT SHA1:")
print("-" * 70)
print("   (This would indicate the file content actually changed)")
query2 = """
SELECT 
  drive_id,
  name,
  COUNT(*) as index_count,
  COUNT(DISTINCT sha1) as unique_sha1_count,
  ARRAY_AGG(DISTINCT sha1 IGNORE NULLS LIMIT 5) as sha1_values
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
GROUP BY drive_id, name
HAVING COUNT(*) > 1 AND COUNT(DISTINCT sha1) > 1
LIMIT 10
"""

result = bq.query(query2).result()
found_any = False
for row in result:
    found_any = True
    print(f"\n   File: {row.name}")
    print(f"   Drive ID: {row.drive_id}")
    print(f"   Indexed: {row.index_count} times")
    print(f"   Different SHA1 values: {row.unique_sha1_count}")
    print(f"   SHA1s: {row.sha1_values[:3]}")

if not found_any:
    print("   ✅ None found - all duplicate entries have the same SHA1")

# Check for same drive_id with same SHA1 (true indexing duplicates)
print("\n\n3. Files with same drive_id AND same SHA1:")
print("-" * 70)
print("   (These are truly duplicate index entries)")
query3 = """
SELECT 
  COUNT(*) as files_with_same_content
FROM (
  SELECT 
    drive_id,
    name,
    COUNT(*) as index_count,
    COUNT(DISTINCT sha1) as unique_sha1_count
  FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
  WHERE sha1 IS NOT NULL
  GROUP BY drive_id, name
  HAVING COUNT(*) > 1 AND COUNT(DISTINCT sha1) = 1
)
"""

result = bq.query(query3).result()
for row in result:
    print(f"   Files with identical content indexed multiple times: {row.files_with_same_content:,}")

# Check for different drive_ids with same SHA1 (actual duplicate files)
print("\n\n4. DIFFERENT files (different drive_id) with SAME SHA1:")
print("-" * 70)
print("   (This would indicate actual duplicate content across different files)")
query4 = """
SELECT 
  sha1,
  COUNT(DISTINCT drive_id) as different_files,
  ARRAY_AGG(DISTINCT name LIMIT 5) as file_names,
  ANY_VALUE(size_bytes) as size
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
WHERE sha1 IS NOT NULL AND sha1 != ''
GROUP BY sha1
HAVING COUNT(DISTINCT drive_id) > 1
ORDER BY different_files DESC
LIMIT 10
"""

result = bq.query(query4).result()
found_any = False
for row in result:
    found_any = True
    print(f"\n   SHA1: {row.sha1[:20]}...")
    print(f"   Different files with this content: {row.different_files}")
    print(f"   Size: {row.size:,} bytes")
    print(f"   Names: {', '.join(row.file_names[:3])}")

if not found_any:
    print("   ✅ None found - no different files share the same content")

# Final verification
print("\n\n" + "=" * 70)
print("📊 FINAL VERIFICATION")
print("=" * 70)

query5 = """
WITH file_groups AS (
  SELECT 
    drive_id,
    COUNT(*) as entry_count,
    COUNT(DISTINCT sha1) as unique_hashes
  FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
  WHERE sha1 IS NOT NULL
  GROUP BY drive_id
  HAVING COUNT(*) > 1
)
SELECT
  SUM(CASE WHEN unique_hashes = 1 THEN 1 ELSE 0 END) as same_content_dups,
  SUM(CASE WHEN unique_hashes > 1 THEN 1 ELSE 0 END) as changed_content_dups,
  COUNT(*) as total_duplicate_files
FROM file_groups
"""

result = bq.query(query5).result()
for row in result:
    print(f"\n   Files indexed multiple times (total): {row.total_duplicate_files:,}")
    print(f"   - With SAME content (true duplicates): {row.same_content_dups:,}")
    print(f"   - With CHANGED content (file was modified): {row.changed_content_dups:,}")

print("\n✅ Verification complete!")
