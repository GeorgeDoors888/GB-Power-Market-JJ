#!/usr/bin/env python3
"""
Deploy Apps Script to Google Sheets using OAuth (User Authentication)
This allows creating container-bound scripts programmatically

Setup:
1. Enable Apps Script API in Google Cloud Console
2. Create OAuth 2.0 credentials (Desktop app)
3. Download credentials.json
4. Run this script - it will open browser for authorization
"""

import os
import json
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
APPS_SCRIPT_FILE = "google_sheets_dashboard.gs"
TOKEN_FILE = "apps_script_token.pickle"
CREDENTIALS_FILE = "oauth_credentials.json"  # Download from Google Cloud Console

# OAuth scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.container.ui',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def get_oauth_credentials():
    """Get OAuth credentials with user consent"""
    creds = None
    
    # Check if we have saved credentials
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing OAuth token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"❌ OAuth credentials file not found: {CREDENTIALS_FILE}")
                print("\n📋 Setup OAuth Credentials:")
                print("1. Go to: https://console.cloud.google.com/apis/credentials")
                print("2. Create OAuth 2.0 Client ID (Desktop app)")
                print("3. Download JSON as 'oauth_credentials.json'")
                print("4. Place in this directory")
                return None
            
            print("🔐 Starting OAuth flow (browser will open)...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print("✅ OAuth credentials saved")
    
    return creds

def read_apps_script_code():
    """Read the Apps Script code file"""
    if not os.path.exists(APPS_SCRIPT_FILE):
        raise FileNotFoundError(f"Apps Script file not found: {APPS_SCRIPT_FILE}")
    
    with open(APPS_SCRIPT_FILE, 'r') as f:
        code = f.read()
    
    print(f"✅ Read {len(code)} characters from {APPS_SCRIPT_FILE}")
    return code

def create_container_bound_script(script_service, drive_service, sheet_id, code):
    """
    Create a container-bound Apps Script attached to the Google Sheet
    """
    try:
        # Create a new Apps Script project bound to the sheet
        project = {
            'title': 'GB Power Market Dashboard',
            'parentId': sheet_id  # Bind to sheet
        }
        
        created = script_service.projects().create(body=project).execute()
        script_id = created['scriptId']
        print(f"✅ Created container-bound script: {script_id}")
        
        # Update the script content
        files = [
            {
                'name': 'Code',
                'type': 'SERVER_JS',
                'source': code
            },
            {
                'name': 'appsscript',
                'type': 'JSON',
                'source': json.dumps({
                    'timeZone': 'Europe/London',
                    'dependencies': {},
                    'exceptionLogging': 'STACKDRIVER',
                    'runtimeVersion': 'V8'
                })
            }
        ]
        
        script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': files}
        ).execute()
        
        print(f"✅ Updated script content")
        return script_id
        
    except HttpError as e:
        print(f"❌ Error creating container-bound script: {e}")
        print("\n⚠️  Container-bound script creation requires:")
        print("   - OAuth credentials (not service account)")
        print("   - User consent via browser")
        print("   - Apps Script API enabled")
        raise

def update_existing_script(script_service, script_id, code):
    """Update an existing Apps Script project"""
    try:
        files = [
            {
                'name': 'Code',
                'type': 'SERVER_JS',
                'source': code
            }
        ]
        
        script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': files}
        ).execute()
        
        print(f"✅ Updated script {script_id}")
        return True
        
    except HttpError as e:
        print(f"❌ Error updating script: {e}")
        return False

def find_existing_script(drive_service, sheet_id):
    """Find existing Apps Script files bound to the sheet"""
    try:
        # Search for Apps Script files that are children of the sheet
        query = f"'{sheet_id}' in parents and mimeType='application/vnd.google-apps.script'"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, parents)'
        ).execute()
        
        files = results.get('files', [])
        return files
        
    except HttpError as e:
        print(f"⚠️  Error searching for scripts: {e}")
        return []

def main():
    """Main deployment function with OAuth"""
    print("🚀 Google Apps Script Deployment (OAuth)")
    print("=" * 50)
    
    try:
        # Step 1: Get OAuth credentials
        print("\n📋 Step 1: Getting OAuth credentials...")
        creds = get_oauth_credentials()
        
        if not creds:
            print("\n❌ Cannot proceed without OAuth credentials")
            print("   See setup instructions above")
            return
        
        print("✅ OAuth authentication successful")
        
        # Step 2: Read Apps Script code
        print("\n📋 Step 2: Reading Apps Script code...")
        code = read_apps_script_code()
        
        # Step 3: Build API clients
        print("\n📋 Step 3: Building API clients...")
        script_service = build('script', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        # Step 4: Find or create script
        print(f"\n📋 Step 4: Checking for existing scripts...")
        existing_scripts = find_existing_script(drive_service, SHEET_ID)
        
        if existing_scripts:
            print(f"✅ Found {len(existing_scripts)} existing script(s)")
            for script_file in existing_scripts:
                script_id = script_file['id']
                print(f"   Updating: {script_file['name']} ({script_id})")
                
                if update_existing_script(script_service, script_id, code):
                    print(f"\n✅ SUCCESS! Script deployed")
                    print(f"📊 Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
                    print(f"🔧 Script: https://script.google.com/d/{script_id}/edit")
                    print(f"\n📝 Next steps:")
                    print(f"1. Refresh your Google Sheet")
                    print(f"2. Menu '⚡ Power Market' should appear")
                    print(f"3. Click: ⚡ Power Market → 🚀 One-Click Setup")
                    return
        
        # No existing script - try to create one
        print("\n📋 Step 5: Creating new container-bound script...")
        script_id = create_container_bound_script(
            script_service, drive_service, SHEET_ID, code
        )
        
        print(f"\n✅ SUCCESS! Script created and deployed")
        print(f"📊 Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
        print(f"🔧 Script: https://script.google.com/d/{script_id}/edit")
        print(f"\n📝 Next steps:")
        print(f"1. Refresh your Google Sheet")
        print(f"2. Menu '⚡ Power Market' should appear")
        print(f"3. Click: ⚡ Power Market → 🚀 One-Click Setup")
        
    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        
    except HttpError as e:
        print(f"\n❌ API Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Make sure Apps Script API is enabled")
        print("   - Check OAuth credentials are valid")
        print("   - Verify you have edit access to the sheet")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
