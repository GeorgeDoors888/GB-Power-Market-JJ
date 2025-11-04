#!/usr/bin/env python3
"""Test Drive API access."""

from google.oauth2 import service_account
from googleapiclient.discovery import build

credentials = service_account.Credentials.from_service_account_file(
    "/secrets/sa.json",
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)

drive_service = build("drive", "v3", credentials=credentials, cache_discovery=False)

try:
    # Try to list files
    results = drive_service.files().list(
        pageSize=10, 
        fields="files(id, name, mimeType)"
    ).execute()
    files = results.get("files", [])
    
    print(f"✅ Drive API access working!")
    print(f"   Service Account: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com")
    print(f"   Found {len(files)} files")
    
    if files:
        print("\n   Sample files:")
        for f in files[:5]:
            print(f"     - {f.get('name')} ({f.get('mimeType', 'unknown')})")
    else:
        print("\n   ⚠️  No files found. The service account may need to be granted access to Drive files.")
        print("   To grant access:")
        print("   1. Share your Drive files/folders with: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com")
        print("   2. Or make files publicly accessible within your organization")
        
except Exception as e:
    print(f"❌ Drive API access failed:")
    print(f"   Error: {e}")
    print(f"\n   The service account may not have Drive API enabled or lacks permissions.")
