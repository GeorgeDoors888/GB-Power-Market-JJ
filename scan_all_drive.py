#!/usr/bin/env python3
"""Paginate through ALL files to see what's really there."""
import sys
sys.path.insert(0, '/app')

from dotenv import load_dotenv
load_dotenv('/app/.env')

from src.auth.google_auth import drive_client
import time

print("Fetching ALL files from Drive (may take a while)...")
print()

client = drive_client()
page_token = None
all_files = []
page_count = 0

while True:
    page_count += 1
    print(f"Fetching page {page_count}...", end=' ')
    
    results = client.files().list(
        pageToken=page_token,
        pageSize=1000,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields="nextPageToken, files(id, name, mimeType, size)"
    ).execute()
    
    files = results.get('files', [])
    all_files.extend(files)
    print(f"Got {len(files)} files (total: {len(all_files)})")
    
    page_token = results.get('nextPageToken')
    if not page_token:
        break
    
    time.sleep(0.1)
    
    # Safety limit
    if page_count >= 10:
        print("Stopping at 10 pages for safety")
        break

print()
print("=" * 80)
print(f"TOTAL FILES: {len(all_files)}")
print("=" * 80)
print()

# Count by type
mime_counts = {}
for f in all_files:
    mt = f.get('mimeType', 'unknown')
    mime_counts[mt] = mime_counts.get(mt, 0) + 1

print("File types:")
for mt, count in sorted(mime_counts.items(), key=lambda x: -x[1])[:20]:
    short_type = mt.split('.')[-1] if '.' in mt else mt.split('/')[-1]
    print(f"  {count:>5} × {short_type}")

# Count PDFs specifically
pdf_count = mime_counts.get('application/pdf', 0)
doc_count = mime_counts.get('application/vnd.google-apps.document', 0)
sheet_count = mime_counts.get('application/vnd.google-apps.spreadsheet', 0)

print()
print(f"📄 PDFs: {pdf_count}")
print(f"📝 Google Docs: {doc_count}")
print(f"📊 Google Sheets: {sheet_count}")
