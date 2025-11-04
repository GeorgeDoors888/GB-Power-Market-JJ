#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import drive_client

print("🔍 Checking total files in Drive...\n")

drive = drive_client()

# Quick scan to estimate total files
page_token = None
total_files = 0

for page_num in range(1, 11):  # Check first 10 pages
    try:
        results = drive.files().list(
            pageSize=1000,
            pageToken=page_token,
            fields="nextPageToken, files(id)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora='allDrives',
            q='trashed=false'
        ).execute()
        
        files = results.get('files', [])
        total_files += len(files)
        
        page_token = results.get('nextPageToken')
        if not page_token:
            print(f"✅ Found {total_files:,} total files in Drive")
            break
    except Exception as e:
        print(f"Error: {e}")
        break
else:
    print(f"⏳ At least {total_files:,} files (still counting...)")
    print("   Note: Your Drive has more than 10,000 files")

print(f"\n📊 Currently indexed: 306,413")
if total_files > 0 and total_files <= 10000:
    remaining = total_files - 306413
    if remaining > 0:
        print(f"⏳ Remaining: ~{remaining:,} files")
    else:
        print(f"✅ Indexing may be complete or near complete!")
