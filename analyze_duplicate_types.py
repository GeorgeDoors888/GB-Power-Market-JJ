#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()

print("🔍 ANALYZING DUPLICATE TYPES\n")
print("=" * 60)

# 1. Check duplicates by drive_id (same file indexed multiple times)
print("\n📋 1. SAME FILE INDEXED MULTIPLE TIMES (by drive_id)")
print("-" * 60)
query1 = """
SELECT 
  COUNT(*) as files_with_duplicates,
  SUM(duplicate_count - 1) as total_duplicate_entries
FROM (
  SELECT 
    drive_id,
    COUNT(*) as duplicate_count
  FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
  GROUP BY drive_id
  HAVING COUNT(*) > 1
)
"""

result = bq.query(query1).result()
for row in result:
    print(f"   Files indexed multiple times: {row.files_with_duplicates:,}")
    print(f"   Extra duplicate entries: {row.total_duplicate_entries:,}")

# 2. Show some examples of duplicated drive_ids
print("\n📝 Examples of files indexed multiple times:")
print("-" * 60)
query2 = """
SELECT 
  drive_id,
  name,
  COUNT(*) as times_indexed,
  MIN(created) as first_created,
  MAX(updated) as last_updated
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
GROUP BY drive_id, name
HAVING COUNT(*) > 1
ORDER BY times_indexed DESC
LIMIT 5
"""

result = bq.query(query2).result()
for row in result:
    print(f"\n   File: {row.name}")
    print(f"   Drive ID: {row.drive_id}")
    print(f"   Times indexed: {row.times_indexed}")
    print(f"   Created: {row.first_created}")
    print(f"   Updated: {row.last_updated}")

# 3. Check for actual content duplicates (same SHA1, different drive_id)
print("\n\n📋 2. ACTUAL DUPLICATE FILES (same content, different files)")
print("-" * 60)
query3 = """
SELECT 
  COUNT(DISTINCT sha1) as unique_content_duplicated,
  SUM(file_count - 1) as duplicate_file_count
FROM (
  SELECT 
    sha1,
    COUNT(DISTINCT drive_id) as file_count
  FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
  WHERE sha1 IS NOT NULL AND sha1 != ''
  GROUP BY sha1
  HAVING COUNT(DISTINCT drive_id) > 1
)
"""

result = bq.query(query3).result()
for row in result:
    if row.unique_content_duplicated:
        print(f"   Unique content pieces that are duplicated: {row.unique_content_duplicated:,}")
        print(f"   Total duplicate files (same content): {row.duplicate_file_count:,}")
    else:
        print("   ✅ No content duplicates found (all files have unique content)")

# 4. Show examples of content duplicates
print("\n📝 Examples of actual duplicate content:")
print("-" * 60)
query4 = """
SELECT 
  sha1,
  COUNT(DISTINCT drive_id) as file_count,
  ARRAY_AGG(DISTINCT name LIMIT 3) as example_names,
  ANY_VALUE(size_bytes) as file_size
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
WHERE sha1 IS NOT NULL AND sha1 != ''
GROUP BY sha1
HAVING COUNT(DISTINCT drive_id) > 1
ORDER BY file_count DESC
LIMIT 5
"""

result = bq.query(query4).result()
found_content_dups = False
for row in result:
    found_content_dups = True
    print(f"\n   SHA1: {row.sha1}")
    print(f"   Number of copies: {row.file_count}")
    print(f"   Size: {row.file_size:,} bytes")
    print(f"   Example names: {', '.join(row.example_names[:3])}")

if not found_content_dups:
    print("   (None found)")

# 5. Check for name duplicates (same name, different locations)
print("\n\n📋 3. SAME FILENAME IN DIFFERENT LOCATIONS")
print("-" * 60)
query5 = """
SELECT 
  name,
  COUNT(DISTINCT drive_id) as file_count,
  COUNT(DISTINCT path) as location_count
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
WHERE name IS NOT NULL
GROUP BY name
HAVING COUNT(DISTINCT drive_id) > 1
ORDER BY file_count DESC
LIMIT 5
"""

result = bq.query(query5).result()
for row in result:
    print(f"\n   Filename: {row.name}")
    print(f"   Number of copies: {row.file_count}")
    print(f"   Number of locations: {row.location_count}")

# Summary
print("\n\n" + "=" * 60)
print("📊 SUMMARY")
print("=" * 60)

query_summary = """
SELECT 
  COUNT(*) as total_entries,
  COUNT(DISTINCT drive_id) as unique_files,
  COUNT(*) - COUNT(DISTINCT drive_id) as indexing_duplicates,
  (
    SELECT COUNT(DISTINCT sha1)
    FROM (
      SELECT sha1, COUNT(DISTINCT drive_id) as cnt
      FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
      WHERE sha1 IS NOT NULL AND sha1 != ''
      GROUP BY sha1
      HAVING cnt > 1
    )
  ) as content_duplicate_groups
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
"""

result = bq.query(query_summary).result()
for row in result:
    print(f"\n   Total entries in database: {row.total_entries:,}")
    print(f"   Unique files (by drive_id): {row.unique_files:,}")
    print(f"   Duplicate entries (same file indexed twice): {row.indexing_duplicates:,}")
    print(f"   Content duplicate groups (different files, same content): {row.content_duplicate_groups or 0:,}")

print("\n✅ Analysis complete!")
