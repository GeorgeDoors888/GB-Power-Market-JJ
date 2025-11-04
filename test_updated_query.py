#!/usr/bin/env python3
"""Test updated Drive query."""
import sys
sys.path.insert(0, '/app')

from dotenv import load_dotenv
load_dotenv('/app/.env')

from src.auth.google_auth import drive_client
import os

query = os.getenv('DRIVE_CRAWL_Q')
print(f"Testing query (first 150 chars):")
print(f"  {query[:150]}...")

client = drive_client()
results = client.files().list(
    q=query,
    pageSize=50,
    fields="files(id, name, mimeType)"
).execute()
files = results.get('files', [])

print(f"\n✅ Found {len(files)} files matching the query!")

# Count by MIME type
mime_types = {}
for f in files:
    mt = f.get('mimeType', 'unknown')
    mime_types[mt] = mime_types.get(mt, 0) + 1

print("\nFile types breakdown:")
for mt, count in sorted(mime_types.items(), key=lambda x: -x[1]):
    print(f"  - {mt}: {count} files")

print("\nFirst 10 files:")
for i, f in enumerate(files[:10], 1):
    print(f"  {i}. {f['name'][:50]} ({f.get('mimeType', '?').split('.')[-1]})")
