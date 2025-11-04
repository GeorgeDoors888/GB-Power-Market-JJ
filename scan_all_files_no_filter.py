#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import drive_client

print("🔍 Scanning ALL files in Drive (no filter)...\n")

drive = drive_client()

# Count ALL files (no MIME type filter)
page_token = None
total_files = 0
file_types = {}
max_pages = 50  # Check up to 50,000 files

for page_num in range(1, max_pages + 1):
    try:
        results = drive.files().list(
            pageSize=1000,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora='allDrives'
        ).execute()
        
        files = results.get('files', [])
        total_files += len(files)
        
        for file in files:
            mime = file.get('mimeType', 'unknown')
            file_types[mime] = file_types.get(mime, 0) + 1
        
        print(f"Page {page_num}: {len(files)} files (total: {total_files:,})")
        
        page_token = results.get('nextPageToken')
        if not page_token:
            print(f"\n✅ Reached end of Drive at page {page_num}")
            break
    except Exception as e:
        print(f"Error on page {page_num}: {e}")
        break

print(f"\n{'='*80}")
print(f"TOTAL FILES IN DRIVE: {total_files:,}")
print(f"{'='*80}\n")

print("File types (top 20):")
sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:20]
for mime, count in sorted_types:
    type_name = mime.split('/')[-1] if '/' in mime else mime
    print(f"  {count:>7,} × {type_name}")

# Count folders vs files
folders = file_types.get('application/vnd.google-apps.folder', 0)
actual_files = total_files - folders
print(f"\n📁 Folders: {folders:,}")
print(f"📄 Actual files: {actual_files:,}")
