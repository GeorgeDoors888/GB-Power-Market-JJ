#!/usr/bin/env python3
"""
Replace ALL files in the Apps Script with just the corrected code
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

EXISTING_SCRIPT_ID = "1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx"
APPS_SCRIPT_FILE = "google_sheets_dashboard.gs"
TOKEN_FILE = "apps_script_token.pickle"
CREDENTIALS_FILE = "oauth_credentials.json"

SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
]

def get_oauth_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing OAuth token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def main():
    print("=" * 70)
    print("🔄 REPLACING ALL APPS SCRIPT FILES WITH CORRECTED CODE")
    print("=" * 70)
    print()
    
    # Get credentials
    creds = get_oauth_credentials()
    
    # Read corrected code
    print("📋 Reading corrected Apps Script code...")
    with open(APPS_SCRIPT_FILE, 'r') as f:
        code = f.read()
    print(f"✅ Read {len(code)} characters")
    print()
    
    # Build API client
    service = build('script', 'v1', credentials=creds)
    
    # Get current script
    print("📋 Getting current script files...")
    content = service.projects().getContent(scriptId=EXISTING_SCRIPT_ID).execute()
    current_files = content.get('files', [])
    
    print(f"Current files ({len(current_files)}):")
    for f in current_files:
        print(f"  - {f.get('name')} ({f.get('type')})")
    print()
    
    # Create new file list with ONLY our corrected code
    print("📋 Replacing with single corrected file...")
    new_files = [
        {
            'name': 'Code',
            'type': 'SERVER_JS',
            'source': code
        },
        {
            'name': 'appsscript',
            'type': 'JSON',
            'source': json.dumps({
                "timeZone": "Europe/London",
                "dependencies": {},
                "exceptionLogging": "STACKDRIVER",
                "runtimeVersion": "V8",
                "oauthScopes": [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/script.external_request"
                ]
            }, indent=2)
        }
    ]
    
    # Update
    request = {'files': new_files}
    
    print("📋 Updating script...")
    try:
        updated = service.projects().updateContent(
            scriptId=EXISTING_SCRIPT_ID,
            body=request
        ).execute()
        
        print("✅ Successfully replaced all files!")
        print()
        print("New structure:")
        for f in updated.get('files', []):
            print(f"  - {f.get('name')} ({f.get('type')})")
        print()
        
        print("=" * 70)
        print("🎉 SUCCESS!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Refresh your Google Sheet (Cmd+R)")
        print("  2. Wait 5-10 seconds")
        print("  3. Click: ⚡ Power Market → ⚡ One-Click Setup")
        print()
        
    except HttpError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import json
    main()
