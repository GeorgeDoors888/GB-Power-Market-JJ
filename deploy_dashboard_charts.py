#!/usr/bin/env python3
"""
Deploy Dashboard Charts via Apps Script API
Automatically installs chart creation code to Google Sheets
"""

import os
import json
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
APPS_SCRIPT_FILE = "dashboard_charts.gs"
TOKEN_FILE = "apps_script_token.pickle"
CREDENTIALS_FILE = "oauth_credentials.json"

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.container.ui',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

print("📊 Dashboard Charts Deployment via Apps Script API")
print("=" * 60)

def get_oauth_credentials():
    """Get OAuth credentials with user consent"""
    creds = None
    
    # Check for existing token
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
                print("2. Select project: jibber-jabber-knowledge")
                print("3. Create OAuth 2.0 Client ID (Desktop app)")
                print("4. Download JSON as 'oauth_credentials.json'")
                print("5. Place in this directory")
                return None
            
            print("🔐 Starting OAuth flow (browser will open)...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print("✅ OAuth token saved")
    
    return creds

def read_apps_script_code():
    """Read the Apps Script code from file"""
    # Use the updated V2 version that reads from ChartData sheet
    script_file = Path(__file__).parent / 'dashboard_charts_v2.gs'
    if not script_file.exists():
        print(f"❌ Apps Script file not found: {script_file}")
        return None
    
    with open(script_file, 'r') as f:
        return f.read()

def find_existing_script(drive_service, sheet_id):
    """Find existing Apps Script files bound to the sheet"""
    try:
        # Query for Apps Script files with this sheet as parent
        query = f"'{sheet_id}' in parents and mimeType='application/vnd.google-apps.script'"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, createdTime)'
        ).execute()
        
        files = results.get('files', [])
        if files:
            print(f"✅ Found {len(files)} existing Apps Script(s)")
            for f in files:
                print(f"   • {f['name']} (ID: {f['id']})")
            return files[0]['id']  # Return first one
        
        return None
    except Exception as e:
        print(f"⚠️  Could not search for existing scripts: {e}")
        return None

def update_existing_script(script_service, script_id, code):
    """Update an existing Apps Script project"""
    try:
        print(f"📝 Updating existing script: {script_id}")
        
        # Get current project to preserve manifest
        try:
            project = script_service.projects().get(scriptId=script_id).execute()
            manifest_content = None
            
            # Extract existing manifest
            for file in project.get('files', []):
                if file['name'] == 'appsscript':
                    manifest_content = file['source']
                    break
        except:
            manifest_content = None
        
        # Prepare files
        files = [
            {
                'name': 'Code',
                'type': 'SERVER_JS',
                'source': code
            }
        ]
        
        # Add manifest if we have it, otherwise create basic one
        if manifest_content:
            files.append({
                'name': 'appsscript',
                'type': 'JSON',
                'source': manifest_content
            })
        else:
            files.append({
                'name': 'appsscript',
                'type': 'JSON',
                'source': json.dumps({
                    'timeZone': 'Europe/London',
                    'dependencies': {},
                    'exceptionLogging': 'STACKDRIVER',
                    'runtimeVersion': 'V8'
                })
            })
        
        # Update content
        response = script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': files}
        ).execute()
        
        print("✅ Script updated successfully")
        return script_id
        
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return None

def create_container_bound_script(script_service, drive_service, sheet_id, code):
    """Create a new container-bound Apps Script"""
    try:
        print("📝 Creating new container-bound script...")
        
        # Create project
        project = {
            'title': 'Dashboard Charts',
            'parentId': sheet_id
        }
        
        created = script_service.projects().create(body=project).execute()
        script_id = created['scriptId']
        print(f"✅ Created script: {script_id}")
        
        # Update content
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
                    'runtimeVersion': 'V8',
                    'oauthScopes': [
                        'https://www.googleapis.com/auth/spreadsheets.currentonly'
                    ]
                })
            }
        ]
        
        script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': files}
        ).execute()
        
        print("✅ Script content deployed")
        return script_id
        
    except Exception as e:
        print(f"❌ Creation failed: {e}")
        return None

def execute_chart_creation(script_service, script_id):
    """Execute the createDashboardCharts function"""
    try:
        print("\n🚀 Executing createDashboardCharts()...")
        
        request = {
            'function': 'createDashboardCharts',
            'devMode': False
        }
        
        response = script_service.scripts().run(
            scriptId=script_id,
            body=request
        ).execute()
        
        if 'error' in response:
            error = response['error']
            print(f"❌ Execution error: {error.get('details', [{}])[0].get('errorMessage', 'Unknown error')}")
            return False
        
        print("✅ Charts created successfully!")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not execute function: {e}")
        print("   You can run it manually:")
        print(f"   1. Open: https://script.google.com/d/{script_id}/edit")
        print("   2. Select function: createDashboardCharts")
        print("   3. Click Run ▶️")
        return False

def main():
    try:
        # Step 1: Get OAuth credentials
        print("\n📋 Step 1: Getting OAuth credentials...")
        creds = get_oauth_credentials()
        
        if not creds:
            print("\n❌ Cannot proceed without OAuth credentials")
            return
        
        print("✅ OAuth authentication successful")
        
        # Step 2: Read chart code
        print("\n📋 Step 2: Reading chart code...")
        code = read_apps_script_code()
        
        if not code:
            return
        
        # Step 3: Build API clients
        print("\n📋 Step 3: Building API clients...")
        script_service = build('script', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        print("✅ API clients ready")
        
        # Step 4: Find or create script
        print("\n📋 Step 4: Finding existing Apps Script...")
        script_id = find_existing_script(drive_service, SHEET_ID)
        
        if script_id:
            # Update existing
            script_id = update_existing_script(script_service, script_id, code)
        else:
            # Create new
            print("📝 No existing script found, creating new one...")
            script_id = create_container_bound_script(
                script_service, drive_service, SHEET_ID, code
            )
        
        if not script_id:
            print("\n❌ Failed to deploy script")
            return
        
        # Step 5: Execute chart creation
        print("\n📋 Step 5: Creating charts...")
        success = execute_chart_creation(script_service, script_id)
        
        # Final summary
        print("\n" + "=" * 60)
        if success:
            print("✅ DEPLOYMENT COMPLETE!")
            print(f"\n📊 View Dashboard:")
            print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0")
            print(f"\n🔧 View Script:")
            print(f"   https://script.google.com/d/{script_id}/edit")
            print(f"\n✨ Charts created:")
            print("   1. ⚡ 24-Hour Generation Trend (Line)")
            print("   2. 🥧 Current Generation Mix (Pie)")
            print("   3. 📊 Stacked Generation (Area)")
            print("   4. 📊 Top Sources (Column)")
        else:
            print("⚠️  DEPLOYMENT PARTIAL")
            print(f"\n📊 View Dashboard:")
            print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0")
            print(f"\n🔧 Manual Step Required:")
            print(f"   1. Dashboard menu → 🔄 Create/Update Charts")
            print(f"   OR")
            print(f"   2. Open: https://script.google.com/d/{script_id}/edit")
            print(f"   3. Run: createDashboardCharts()")
        
        print("=" * 60)
        
    except HttpError as e:
        print(f"\n❌ API Error: {e}")
        
        if "403" in str(e):
            print("\n💡 Permission Error - Try this:")
            print("   1. Make sure Apps Script API is enabled:")
            print("      https://console.cloud.google.com/apis/library/script.googleapis.com")
            print("   2. Delete apps_script_token.pickle and try again")
            print("   3. Grant all permissions when browser opens")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
