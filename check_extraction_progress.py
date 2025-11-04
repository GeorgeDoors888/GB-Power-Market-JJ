#!/usr/bin/env python3
"""
Simple extraction progress checker - runs on UpCloud server
"""
import os
import sys
sys.path.insert(0, '/app/src')

# Set environment variable for container
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/secrets/sa.json"

from auth.google_auth import bq_client

client = bq_client()
dataset = "uk_energy_insights"

print("🔍 CHECKING EXTRACTION PROGRESS")
print("=" * 80)

# Count chunks
query = f"SELECT COUNT(*) as count FROM `{client.project}.{dataset}.chunks`"
result = list(client.query(query).result())[0]
chunks = result.count

# Count unique documents processed
query_docs = f"SELECT COUNT(DISTINCT doc_id) as docs FROM `{client.project}.{dataset}.chunks`"
result_docs = list(client.query(query_docs).result())[0]
docs = result_docs.docs

# Total to process
query_total = f"""
SELECT COUNT(*) as total FROM `{client.project}.{dataset}.documents_clean`
WHERE mime_type IN (
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'
)
"""
result_total = list(client.query(query_total).result())[0]
total = result_total.total

print(f"\n📊 Chunks created: {chunks:,}")
print(f"📄 Documents processed: {docs:,} / {total:,}")
print(f"📈 Progress: {(docs/total*100):.1f}%")

if docs > 0:
    avg_chunks = chunks / docs
    print(f"📏 Average chunks per document: {avg_chunks:.1f}")
    
    remaining = total - docs
    print(f"\n⏳ Remaining documents: {remaining:,}")
    
print("\n✅ Extraction is running in background on server")
print("💡 Run this script again to check progress")
