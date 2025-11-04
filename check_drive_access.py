#!/usr/bin/env python3
"""Check what the service account can see in Drive."""
import sys
sys.path.insert(0, '/app')

from dotenv import load_dotenv
load_dotenv('/app/.env')

from src.auth.google_auth import drive_client

print("Checking Drive access...")
print()

client = drive_client()

# Check 1: All files (no filter)
print("=" * 80)
print("ALL FILES (no filter, first 100)")
print("=" * 80)
results = client.files().list(
    pageSize=100,
    fields="nextPageToken, files(id, name, mimeType, parents, shared, ownedByMe)"
).execute()
files = results.get('files', [])
print(f"Found: {len(files)} files")
print(f"Next page token: {results.get('nextPageToken', 'None (all files retrieved)')}")
print()

# Check file types
mime_counts = {}
for f in files:
    mt = f.get('mimeType', 'unknown')
    mime_counts[mt] = mime_counts.get(mt, 0) + 1

print("File types:")
for mt, count in sorted(mime_counts.items(), key=lambda x: -x[1]):
    print(f"  - {mt}: {count}")
print()

# Check 2: PDFs specifically
print("=" * 80)
print("PDFs ONLY")
print("=" * 80)
pdf_results = client.files().list(
    q="mimeType='application/pdf' and trashed=false",
    pageSize=100,
    fields="nextPageToken, files(id, name, size, parents)"
).execute()
pdfs = pdf_results.get('files', [])
print(f"PDFs found: {len(pdfs)}")
if pdfs:
    print("First 10 PDFs:")
    for f in pdfs[:10]:
        print(f"  - {f.get('name')} (size: {f.get('size', 0)} bytes)")
print()

# Check 3: Check if we're looking at a Shared Drive
print("=" * 80)
print("SHARED DRIVES")
print("=" * 80)
try:
    drives_results = client.drives().list(pageSize=10).execute()
    drives = drives_results.get('drives', [])
    print(f"Shared Drives accessible: {len(drives)}")
    for d in drives:
        print(f"  - {d.get('name')} (ID: {d.get('id')})")
except Exception as e:
    print(f"Could not list shared drives: {e}")
print()

# Check 4: List with corpora=allDrives
print("=" * 80)
print("ALL DRIVES (including Shared Drives)")
print("=" * 80)
try:
    all_results = client.files().list(
        corpora='allDrives',
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        pageSize=100,
        fields="nextPageToken, files(id, name, mimeType, driveId)"
    ).execute()
    all_files = all_results.get('files', [])
    print(f"Total files (all drives): {len(all_files)}")
    
    # Count by drive
    drive_counts = {}
    for f in all_files:
        drive_id = f.get('driveId', 'My Drive')
        drive_counts[drive_id] = drive_counts.get(drive_id, 0) + 1
    
    print("Files per drive:")
    for drive_id, count in drive_counts.items():
        print(f"  - {drive_id}: {count} files")
except Exception as e:
    print(f"Error accessing all drives: {e}")
