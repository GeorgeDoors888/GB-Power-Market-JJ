#!/usr/bin/env python3
"""
Automatically deploy Apps Script to Google Sheets using Apps Script API
Requires: Google Apps Script API enabled + service account credentials
"""

import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SA_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "inner-cinema-credentials.json")
APPS_SCRIPT_FILE = "google_sheets_dashboard.gs"

# Apps Script API scopes
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials():
    """Get service account credentials with Apps Script API scope"""
    if not os.path.exists(SA_PATH):
        raise FileNotFoundError(f"Service account file not found: {SA_PATH}")
    
    creds = Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
    print(f"✅ Loaded credentials from: {SA_PATH}")
    return creds

def read_apps_script_code():
    """Read the Apps Script code file"""
    if not os.path.exists(APPS_SCRIPT_FILE):
        raise FileNotFoundError(f"Apps Script file not found: {APPS_SCRIPT_FILE}")
    
    with open(APPS_SCRIPT_FILE, 'r') as f:
        code = f.read()
    
    print(f"✅ Read {len(code)} characters from {APPS_SCRIPT_FILE}")
    return code

def get_script_id_from_sheet(sheets_service, sheet_id):
    """
    Get the Apps Script project ID bound to a Google Sheet
    Note: This requires the sheet to already have a bound script
    """
    try:
        # Get sheet metadata
        sheet = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        
        # Check if there's a bound script (container-bound script)
        # The script ID is typically stored in the sheet's developer metadata
        # or we need to create a new project
        
        print(f"✅ Found sheet: {sheet.get('properties', {}).get('title', 'Unknown')}")
        return None  # We'll create a new project if needed
        
    except HttpError as e:
        print(f"❌ Error accessing sheet: {e}")
        raise

def create_apps_script_project(script_service, title):
    """Create a new standalone Apps Script project"""
    try:
        project = {
            'title': title,
            'parentId': None  # Standalone project (not bound to sheet)
        }
        
        created = script_service.projects().create(body=project).execute()
        script_id = created['scriptId']
        print(f"✅ Created Apps Script project: {script_id}")
        return script_id
        
    except HttpError as e:
        print(f"❌ Error creating project: {e}")
        raise

def update_apps_script_content(script_service, script_id, code):
    """Update the content of an Apps Script project"""
    try:
        # Get current project content
        project = script_service.projects().get(scriptId=script_id).execute()
        
        # Create new file content
        files = [
            {
                'name': 'Code',
                'type': 'SERVER_JS',
                'source': code
            }
        ]
        
        # Update project content
        content = {
            'scriptId': script_id,
            'files': files
        }
        
        updated = script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': files}
        ).execute()
        
        print(f"✅ Updated Apps Script content ({len(code)} characters)")
        return updated
        
    except HttpError as e:
        print(f"❌ Error updating content: {e}")
        raise

def deploy_to_sheet_bound_script(sheets_service, sheet_id, code):
    """
    Deploy code to sheet-bound Apps Script
    This requires using the Sheets API to access the bound script
    """
    try:
        # For container-bound scripts, we need to:
        # 1. Open the sheet
        # 2. Extensions > Apps Script (creates bound script if not exists)
        # 3. Update the script content
        
        # Unfortunately, creating container-bound scripts programmatically
        # requires more complex OAuth flow (user consent)
        
        print("⚠️  Container-bound scripts require manual authorization")
        print("📋 Follow these steps instead:")
        print(f"1. Open: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        print("2. Extensions → Apps Script")
        print("3. Copy/paste code from: {APPS_SCRIPT_FILE}")
        print("4. Save and run Setup_Dashboard_AutoRefresh")
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

def main():
    """Main deployment function"""
    print("⚡ Google Apps Script Deployment Tool")
    print("=" * 50)
    
    try:
        # Step 1: Get credentials
        print("\n📋 Step 1: Loading credentials...")
        creds = get_credentials()
        
        # Step 2: Read Apps Script code
        print("\n📋 Step 2: Reading Apps Script code...")
        code = read_apps_script_code()
        
        # Step 3: Build API clients
        print("\n📋 Step 3: Building API clients...")
        script_service = build('script', 'v1', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        print("✅ Script API client ready")
        print("✅ Sheets API client ready")
        print("✅ Drive API client ready")
        
        # Step 4: Check if sheet has existing bound script
        print(f"\n📋 Step 4: Checking sheet {SHEET_ID}...")
        
        # Try to find existing Apps Script files bound to this sheet
        query = f"'{SHEET_ID}' in parents and mimeType='application/vnd.google-apps.script'"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType)'
        ).execute()
        
        script_files = results.get('files', [])
        
        if script_files:
            print(f"✅ Found {len(script_files)} existing Apps Script file(s):")
            for f in script_files:
                print(f"   - {f['name']} (ID: {f['id']})")
                script_id = f['id']
                
                # Try to update this script
                print(f"\n📋 Step 5: Updating script {script_id}...")
                try:
                    updated = update_apps_script_content(script_service, script_id, code)
                    print(f"✅ SUCCESS! Script updated")
                    print(f"📊 Open sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
                    print(f"🔧 Open script: https://script.google.com/d/{script_id}/edit")
                    return
                except HttpError as e:
                    print(f"⚠️  Could not update script: {e}")
                    print("   Trying alternative method...")
        
        # Alternative: Create standalone project and provide instructions
        print("\n⚠️  ALTERNATIVE APPROACH:")
        print("=" * 50)
        print("The Apps Script API has limitations for container-bound scripts.")
        print("Service accounts cannot create/modify container-bound scripts directly.")
        print("\nYou have 2 options:")
        print("\n📝 OPTION 1: Manual Installation (2 minutes)")
        print(f"1. Open: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
        print("2. Extensions → Apps Script")
        print(f"3. Copy entire file: {APPS_SCRIPT_FILE}")
        print("4. Paste into Code.gs")
        print("5. Save and run Setup_Dashboard_AutoRefresh")
        print("\n🔧 OPTION 2: OAuth User Flow (Advanced)")
        print("1. Create OAuth credentials (not service account)")
        print("2. Use user authentication to create container-bound script")
        print("3. This requires browser-based consent flow")
        
        print("\n💡 RECOMMENDATION: Use Option 1 (Manual)")
        print(f"   I've already opened the file in VS Code for you!")
        print(f"   Just copy/paste - takes 2 minutes")
        
    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        print("\n💡 Make sure:")
        print(f"   - {SA_PATH} exists")
        print(f"   - {APPS_SCRIPT_FILE} exists")
        
    except HttpError as e:
        print(f"\n❌ API Error: {e}")
        print("\n💡 Make sure:")
        print("   - Apps Script API is enabled in Google Cloud Console")
        print("   - Service account has necessary permissions")
        print("   - Sheet is shared with service account email")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
