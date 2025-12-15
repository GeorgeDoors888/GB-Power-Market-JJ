#!/usr/bin/env python3
"""
Update existing Apps Script using the script ID
Script ID: 1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx
"""

import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
SCRIPT_ID = "1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx"
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
    """Get service account credentials"""
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
    
    print(f"✅ Read {len(code):,} characters from {APPS_SCRIPT_FILE}")
    return code

def get_script_info(script_service, script_id):
    """Get information about the Apps Script project"""
    try:
        project = script_service.projects().get(scriptId=script_id).execute()
        print(f"✅ Found script: {project.get('title', 'Untitled')}")
        print(f"   Created: {project.get('createTime', 'Unknown')}")
        print(f"   Updated: {project.get('updateTime', 'Unknown')}")
        return project
    except HttpError as e:
        print(f"❌ Error getting script info: {e}")
        raise

def get_script_content(script_service, script_id):
    """Get current content of the Apps Script"""
    try:
        content = script_service.projects().getContent(scriptId=script_id).execute()
        files = content.get('files', [])
        print(f"✅ Current script has {len(files)} file(s):")
        for f in files:
            print(f"   - {f['name']} ({f['type']}): {len(f.get('source', ''))} chars")
        return content
    except HttpError as e:
        print(f"❌ Error getting content: {e}")
        raise

def update_script_content(script_service, script_id, code):
    """Update the Apps Script content"""
    try:
        # Prepare the new files
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
                }, indent=2)
            }
        ]
        
        # Update the content
        updated = script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': files}
        ).execute()
        
        print(f"✅ Successfully updated script content!")
        print(f"   Files updated: {len(updated.get('files', []))}")
        return updated
        
    except HttpError as e:
        print(f"❌ Error updating content: {e}")
        print(f"\n📋 Error details:")
        print(f"   Status: {e.resp.status}")
        print(f"   Reason: {e.resp.reason}")
        if hasattr(e, 'error_details'):
            print(f"   Details: {e.error_details}")
        raise

def main():
    """Main deployment function"""
    print("🚀 Apps Script Deployment - Update Existing Script")
    print("=" * 60)
    print(f"📝 Script ID: {SCRIPT_ID}")
    print(f"📊 Sheet ID: {SHEET_ID}")
    print("=" * 60)
    
    try:
        # Step 1: Get credentials
        print("\n📋 Step 1: Loading credentials...")
        creds = get_credentials()
        
        # Step 2: Read code
        print("\n📋 Step 2: Reading Apps Script code...")
        code = read_apps_script_code()
        
        # Step 3: Build API client
        print("\n📋 Step 3: Building Apps Script API client...")
        script_service = build('script', 'v1', credentials=creds)
        print("✅ API client ready")
        
        # Step 4: Get script info
        print(f"\n📋 Step 4: Getting info for script {SCRIPT_ID}...")
        project = get_script_info(script_service, SCRIPT_ID)
        
        # Step 5: Get current content
        print(f"\n📋 Step 5: Getting current script content...")
        current = get_script_content(script_service, SCRIPT_ID)
        
        # Step 6: Update content
        print(f"\n📋 Step 6: Updating script content...")
        print(f"   Uploading {len(code):,} characters...")
        updated = update_script_content(script_service, SCRIPT_ID, code)
        
        # Success!
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Apps Script has been updated!")
        print("=" * 60)
        print(f"\n🔗 Links:")
        print(f"   Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
        print(f"   Script: https://script.google.com/d/{SCRIPT_ID}/edit")
        
        print(f"\n📝 Next steps:")
        print(f"   1. Refresh your Google Sheet (Cmd+R or F5)")
        print(f"   2. Check for menu: ⚡ Power Market")
        print(f"   3. Click: ⚡ Power Market → 🚀 One-Click Setup")
        print(f"   4. Authorize when prompted (safe - your own script)")
        print(f"   5. Wait 10-30 seconds for setup to complete")
        print(f"\n✅ Dashboard will auto-refresh every 5 minutes!")
        
    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        
    except HttpError as e:
        print(f"\n❌ API Error: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   - Make sure Apps Script API is enabled")
        print(f"   - Verify service account has access to script")
        print(f"   - Check script ID is correct: {SCRIPT_ID}")
        print(f"\n🔧 Try this:")
        print(f"   1. Open: https://script.google.com/d/{SCRIPT_ID}/edit")
        print(f"   2. Share → Add service account email with Editor access")
        print(f"   3. Service account email is in: {SA_PATH}")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
