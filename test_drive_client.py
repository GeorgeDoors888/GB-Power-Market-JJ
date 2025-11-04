#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

from src.auth.google_auth import drive_client
import os

print("Testing Drive access with updated google_auth.py...")
print(f"DRIVE_SERVICE_ACCOUNT: {os.getenv('DRIVE_SERVICE_ACCOUNT', 'Not set')}")
print()

try:
    client = drive_client()
    results = client.files().list(pageSize=10, fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])
    print(f"✅ Drive client working! Found {len(files)} files")
    for f in files[:5]:
        print(f"   - {f['name']} ({f.get('mimeType', 'unknown')})")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
