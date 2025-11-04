#!/usr/bin/env python3
"""
Quick progress checker - shows extraction status
Run this anytime to see how many documents have been processed
"""
import sys
sys.path.insert(0, '/app/src')
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/secrets/sa.json"

from auth.google_auth import bq_client

client = bq_client()
dataset = "uk_energy_insights"

print("\n" + "="*80)
print("📊 EXTRACTION PROGRESS")
print("="*80)

# Count chunks created
query = f"SELECT COUNT(*) as count FROM `{client.project}.{dataset}.chunks`"
result = list(client.query(query).result())[0]
chunks = result.count

# Count documents processed
query_docs = f"SELECT COUNT(DISTINCT doc_id) as docs FROM `{client.project}.{dataset}.chunks`"
result_docs = list(client.query(query_docs).result())[0]
docs_processed = result_docs.docs

# Total documents to process
total = 140434

print(f"\n✅ Documents processed: {docs_processed:,} / {total:,}")
print(f"📊 Progress: {(docs_processed/total*100):.2f}%")
print(f"📦 Text chunks created: {chunks:,}")

if docs_processed > 0:
    avg_chunks = chunks / docs_processed
    print(f"📏 Average chunks per document: {avg_chunks:.1f}")
    
    remaining = total - docs_processed
    print(f"\n⏳ Remaining documents: {remaining:,}")
    print(f"⏳ Remaining percentage: {(remaining/total*100):.1f}%")

print("\n" + "="*80)
print("💡 Run this script again anytime to check progress")
print("="*80 + "\n")
