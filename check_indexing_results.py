#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

load_dotenv("/app/.env")
sys.path.insert(0, "/app")

from src.auth.google_auth import bq_client
from collections import Counter

bq = bq_client()
project = os.environ["GCP_PROJECT"]
dataset = os.environ["BQ_DATASET"]

# Query documents table
query = f"""
SELECT 
    mime_type,
    COUNT(*) as count
FROM `{project}.{dataset}.documents`
GROUP BY mime_type
ORDER BY count DESC
"""

print("📊 BigQuery Indexing Results\n")
print("="*80)

results = bq.query(query).result()
total = 0
by_type = {}

for row in results:
    mime_type = row.mime_type
    count = row.count
    total += count
    by_type[mime_type] = count
    
    # Friendly names
    type_name = mime_type.split('/')[-1] if '/' in mime_type else mime_type
    print(f"  {count:>5} × {type_name}")

print("="*80)
print(f"\n✅ TOTAL DOCUMENTS INDEXED: {total:,}")

# Count key types
pdfs = by_type.get('application/pdf', 0)
gsheets = by_type.get('application/vnd.google-apps.spreadsheet', 0)
gdocs = by_type.get('application/vnd.google-apps.document', 0)

print(f"\n📄 PDFs: {pdfs:,}")
print(f"📊 Google Sheets: {gsheets:,}")
print(f"📝 Google Docs: {gdocs:,}")
