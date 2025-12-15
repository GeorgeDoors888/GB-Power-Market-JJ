#!/usr/bin/env python3
"""
Update EXISTING Apps Script using OAuth
This updates the script that's already attached to your sheet
"""

import os
import json
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration - UPDATE THE EXISTING SCRIPT
EXISTING_SCRIPT_ID = "1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx"  # Your OLD script
APPS_SCRIPT_FILE = "google_sheets_dashboard.gs"
TOKEN_FILE = "apps_script_token.pickle"
CREDENTIALS_FILE = "oauth_credentials.json"

SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/spreadsheets',
]

def get_oauth_credentials():
    """Get OAuth credentials"""
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
        print("✅ OAuth credentials saved")
    
    return creds

def main():
    print("=" * 70)
    print("🔄 UPDATING EXISTING APPS SCRIPT")
    print("=" * 70)
    print(f"Script ID: {EXISTING_SCRIPT_ID}")
    print()
    
    # Get credentials
    print("📋 Step 1: Getting OAuth credentials...")
    creds = get_oauth_credentials()
    if not creds:
        return
    print("✅ OAuth authentication successful")
    print()
    
    # Read Apps Script code
    print("📋 Step 2: Reading corrected Apps Script code...")
    if not os.path.exists(APPS_SCRIPT_FILE):
        print(f"❌ File not found: {APPS_SCRIPT_FILE}")
        return
    
    with open(APPS_SCRIPT_FILE, 'r') as f:
        code = f.read()
    print(f"✅ Read {len(code)} characters")
    print()
    
    # Build API client
    print("📋 Step 3: Connecting to Apps Script API...")
    service = build('script', 'v1', credentials=creds)
    print("✅ Connected")
    print()
    
    # Get current script content
    print("📋 Step 4: Getting current script...")
    try:
        project = service.projects().get(scriptId=EXISTING_SCRIPT_ID).execute()
        print(f"✅ Found script: {project.get('title', 'Untitled')}")
        print()
    except HttpError as e:
        print(f"❌ Error accessing script: {e}")
        print()
        print("Possible issues:")
        print("  - Script ID is wrong")
        print("  - You don't have permission to edit this script")
        print("  - Script was deleted")
        return
    
    # Update script content
    print("📋 Step 5: Updating script content...")
    
    # Get the current content to preserve file structure
    try:
        content = service.projects().getContent(scriptId=EXISTING_SCRIPT_ID).execute()
        
        # Find the main code file (usually named Code, Enhanced_Automation, or similar)
        files = content.get('files', [])
        main_file = None
        
        for f in files:
            if f.get('type') == 'SERVER_JS':
                main_file = f
                break
        
        if not main_file:
            print("❌ No SERVER_JS file found in script")
            return
        
        print(f"✅ Found main file: {main_file.get('name')}")
        
        # Update the main file with new code
        main_file['source'] = code
        
        # Keep other files unchanged
        new_files = files
        
        # Update the script
        request = {
            'files': new_files
        }
        
        updated = service.projects().updateContent(
            scriptId=EXISTING_SCRIPT_ID,
            body=request
        ).execute()
        
        print("✅ Successfully updated script content!")
        print()
        
        print("=" * 70)
        print("🎉 SUCCESS!")
        print("=" * 70)
        print()
        print("📊 Your Google Sheet now has the corrected code!")
        print()
        print("Next steps:")
        print("  1. Go to your Google Sheet")
        print("  2. Refresh the page (Cmd+R or F5)")
        print("  3. Look for menu: ⚡ Power Market")
        print("  4. Click: ⚡ Power Market → 🚀 One-Click Setup")
        print("  5. Authorize when prompted")
        print("  6. Wait 10-30 seconds")
        print("  7. Done! Auto-refresh enabled")
        print()
        print(f"🔗 Sheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit")
        print(f"🔗 Script: https://script.google.com/d/{EXISTING_SCRIPT_ID}/edit")
        print()
        
    except HttpError as e:
        print(f"❌ Error updating script: {e}")
        print()
        if "403" in str(e):
            print("Permission denied. Make sure:")
            print("  - You're logged in as upowerenergy.uk")
            print("  - You have edit access to this script")

if __name__ == "__main__":
    main()
