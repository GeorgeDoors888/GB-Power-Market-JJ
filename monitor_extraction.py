#!/usr/bin/env python3
"""
Monitor extraction progress in real-time
Shows chunks being created in BigQuery
"""
import os
import time
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/georgemajor/Overarch Jibber Jabber/gridsmart_service_account.json"

client = bigquery.Client(project="inner-cinema-476211-u9")
dataset = "uk_energy_insights"

print("🔍 MONITORING TEXT EXTRACTION PROGRESS")
print("=" * 80)
print("\nPress Ctrl+C to stop monitoring\n")

last_count = 0
start_time = time.time()

try:
    while True:
        # Count chunks
        query = f"SELECT COUNT(*) as count FROM `{client.project}.{dataset}.chunks`"
        result = list(client.query(query).result())[0]
        count = result.count
        
        # Count unique documents processed
        query_docs = f"SELECT COUNT(DISTINCT doc_id) as docs FROM `{client.project}.{dataset}.chunks`"
        result_docs = list(client.query(query_docs).result())[0]
        docs_processed = result_docs.docs
        
        # Calculate rate
        elapsed = time.time() - start_time
        new_chunks = count - last_count
        
        if elapsed > 0:
            chunks_per_sec = count / elapsed
            docs_per_min = (docs_processed / elapsed) * 60 if docs_processed > 0 else 0
        else:
            chunks_per_sec = 0
            docs_per_min = 0
        
        # Display progress
        print(f"\r📊 Chunks: {count:,} | 📄 Docs: {docs_processed:,}/140,434 | "
              f"⚡ {chunks_per_sec:.1f} chunks/s | 🎯 {docs_per_min:.1f} docs/min | "
              f"⏱️  {elapsed/3600:.1f}h elapsed", end="", flush=True)
        
        last_count = count
        time.sleep(5)  # Update every 5 seconds
        
except KeyboardInterrupt:
    print("\n\n✅ Monitoring stopped")
    print(f"\n📈 FINAL STATS:")
    print(f"   Total chunks: {count:,}")
    print(f"   Documents processed: {docs_processed:,} / 140,434")
    print(f"   Time elapsed: {elapsed/3600:.2f} hours")
    if docs_processed > 0:
        avg_chunks_per_doc = count / docs_processed
        print(f"   Average chunks per document: {avg_chunks_per_doc:.1f}")
