#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import drive_client

print("🔍 Scanning ALL files in Drive (complete scan)...\n")

drive = drive_client()

page_token = None
total_files = 0
file_types = {}
max_pages = 250  # Up to 250,000 files

for page_num in range(1, max_pages + 1):
    try:
        results = drive.files().list(
            pageSize=1000,
            pageToken=page_token,
            fields="nextPageToken, files(id, mimeType)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora='allDrives'
        ).execute()
        
        files = results.get('files', [])
        total_files += len(files)
        
        for file in files:
            mime = file.get('mimeType', 'unknown')
            file_types[mime] = file_types.get(mime, 0) + 1
        
        if page_num % 10 == 0:
            print(f"Progress: {total_files:,} files scanned...")
        
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

# Files matching current filter
current_filter_types = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.google-apps.document',
    'application/vnd.google-apps.spreadsheet',
    'application/vnd.google-apps.presentation'
]

filtered_count = sum(file_types.get(t, 0) for t in current_filter_types)
print(f"✅ Files matching current filter: {filtered_count:,}")
print(f"❌ Files EXCLUDED by filter: {total_files - filtered_count:,}\n")

print("Top 30 file types:")
sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:30]
for mime, count in sorted_types:
    type_name = mime.split('/')[-1] if '/' in mime else mime
    in_filter = "✅" if mime in current_filter_types else "  "
    print(f"{in_filter} {count:>7,} × {type_name}")

folders = file_types.get('application/vnd.google-apps.folder', 0)
print(f"\n📁 Total folders: {folders:,}")
print(f"📄 Total files (excluding folders): {total_files - folders:,}")
