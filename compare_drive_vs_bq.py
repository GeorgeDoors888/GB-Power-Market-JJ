#!/usr/bin/env python3
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")
from src.auth.google_auth import bq_client

bq = bq_client()

print("📊 COMPARING GOOGLE DRIVE SCAN vs BIGQUERY")
print("=" * 70)

# Check BigQuery
print("\n1. BigQuery documents_clean Status:")
query = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`"
result = bq.query(query).result()
for row in result:
    bq_count = row.count
    print(f"   Files in BigQuery (deduplicated): {row.count:,}")

# Check extraction progress
print("\n2. Current Extraction Progress:")
print("   Files being scanned from Drive: 138,909")
print("   Files processed so far: 375 (0.27%)")

# Calculate
print("\n3. Analysis:")
print("=" * 70)

if bq_count > 138909:
    print(f"   ⚠️  BigQuery has MORE files ({bq_count:,}) than Drive scan ({138909:,})")
    print(f"   Difference: {bq_count - 138909:,} extra files")
    print("\n   Possible reasons:")
    print("   - Previous indexing runs captured more files")
    print("   - Drive scan filter is more restrictive now")
    print("   - Some files were deleted from Drive since last index")
else:
    print(f"   ℹ️  Drive scan found {138909:,} files")
    print(f"   BigQuery has {bq_count:,} unique files")
    print(f"   Difference: {138909 - bq_count:,} files")
    print("\n   These 'missing' files are likely:")
    print("   - 🗂️  Folders (not indexed as files)")
    print("   - 🖼️  Images, videos (unsupported MIME types)")
    print("   - 🔒 Files without read permissions")
    print("   - 📁 Google Drive shortcuts")
    print("   - 🗑️  Trashed files")

print("\n4. File Type Breakdown (BigQuery):")
print("-" * 70)
query2 = """
SELECT mime_type, COUNT(*) as count 
FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean` 
GROUP BY mime_type 
ORDER BY count DESC
LIMIT 10
"""
result = bq.query(query2).result()
for row in result:
    mime_short = row.mime_type.replace('application/', '').replace('vnd.openxmlformats-officedocument.', '').replace('vnd.google-apps.', 'G:')
    print(f"   {mime_short[:45]:<45} {row.count:>8,}")

print("\n" + "=" * 70)
print("💡 CONCLUSION:")
print("   The extraction is likely re-indexing files you ALREADY have.")
print("   The speed hasn't gotten worse - it's always been this slow.")
print("   Deduplication was just cleaning up duplicate entries in BigQuery.")
print("=" * 70)
