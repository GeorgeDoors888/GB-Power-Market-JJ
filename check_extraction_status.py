#!/usr/bin/env python3
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")
from src.auth.google_auth import bq_client

bq = bq_client()

print("📊 TEXT EXTRACTION STATUS")
print("=" * 70)

# Check documents_clean
query1 = "SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`"
result = bq.query(query1).result()
for row in result:
    total_docs = row.total
    print(f"\n1. Documents available for extraction: {row.total:,}")

# Check how many have been chunked (text extracted)
query2 = "SELECT COUNT(DISTINCT doc_id) as chunked FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`"
try:
    result = bq.query(query2).result()
    for row in result:
        chunked = row.chunked
        remaining = total_docs - chunked
        progress = (chunked / total_docs * 100) if total_docs > 0 else 0
        print(f"2. Documents with text extracted: {chunked:,}")
        print(f"3. Remaining to extract: {remaining:,}")
        print(f"4. Progress: {progress:.1f}%")
except Exception as e:
    print(f"2. Chunks table error: {e}")
    chunked = 0
    remaining = total_docs

# Check total chunks
query3 = "SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`"
try:
    result = bq.query(query3).result()
    for row in result:
        print(f"5. Total text chunks created: {row.total:,}")
        if chunked > 0:
            avg_chunks = row.total / chunked
            print(f"6. Average chunks per document: {avg_chunks:.1f}")
except Exception as e:
    print(f"5. Chunks count error: {e}")

# Check chunk embeddings
query4 = "SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_insights.chunk_embeddings`"
try:
    result = bq.query(query4).result()
    for row in result:
        print(f"7. Embeddings created: {row.total:,}")
except Exception as e:
    print(f"7. Embeddings error: {e}")

print("\n" + "=" * 70)

# If text extraction hasn't started or is minimal, explain
if chunked < 100:
    print("\n⚠️  TEXT EXTRACTION NOT STARTED OR MINIMAL")
    print("   You have 153,201 files indexed but text not yet extracted.")
    print("   Run: python -m src.cli extract")
elif remaining > 0:
    print(f"\n⏳ TEXT EXTRACTION IN PROGRESS")
    print(f"   {remaining:,} documents remaining to process")
