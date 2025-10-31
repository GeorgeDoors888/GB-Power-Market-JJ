#!/usr/bin/env python3
"""
Automatic Apps Script Deployment
Deploys chart automation script to Google Sheets using Apps Script API
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

# Configuration
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SCRIPT_FILE = "google_apps_script_charts.js"

# Apps Script API scope
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials():
    """Get or refresh OAuth2 credentials"""
    creds = None
    
    # Try to load existing credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are invalid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing credentials...")
            creds.refresh(Request())
        else:
            print("❌ No valid credentials found!")
            print("Please run authorize_google_docs.py first to create token.pickle")
            return None
        
        # Save refreshed credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def read_script_file():
    """Read the Apps Script JavaScript file"""
    if not os.path.exists(SCRIPT_FILE):
        print(f"❌ Script file not found: {SCRIPT_FILE}")
        return None
    
    with open(SCRIPT_FILE, 'r') as f:
        script_content = f.read()
    
    return script_content

def get_container_script_id(spreadsheet_id, creds):
    """Get the bound script ID for a Google Sheet"""
    try:
        # Use Drive API to get the spreadsheet's container
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Get spreadsheet metadata
        spreadsheet = drive_service.files().get(
            fileId=spreadsheet_id,
            fields='id,name,capabilities'
        ).execute()
        
        print(f"📊 Found spreadsheet: {spreadsheet.get('name')}")
        
        # List files to find bound script
        # Bound scripts have the same name as spreadsheet but are script files
        query = f"mimeType='application/vnd.google-apps.script' and '{spreadsheet_id}' in parents and trashed=false"
        
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=10
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            script_id = files[0]['id']
            print(f"✅ Found bound script: {script_id}")
            return script_id
        else:
            print("⚠️  No bound script found. Creating new one...")
            return None
            
    except HttpError as error:
        print(f"❌ Error finding script: {error}")
        return None

def create_bound_script(spreadsheet_id, creds):
    """Create a new bound Apps Script project"""
    try:
        script_service = build('script', 'v1', credentials=creds)
        
        # Create a new script project bound to the spreadsheet
        request = {
            'title': 'Dashboard Charts',
            'parentId': spreadsheet_id
        }
        
        script_project = script_service.projects().create(body=request).execute()
        script_id = script_project['scriptId']
        
        print(f"✅ Created new script project: {script_id}")
        return script_id
        
    except HttpError as error:
        print(f"❌ Error creating script: {error}")
        return None

def deploy_script(script_id, script_content, creds):
    """Deploy the Apps Script code"""
    try:
        script_service = build('script', 'v1', credentials=creds)
        
        # Prepare the script content
        # Apps Script API expects files in a specific format
        script_manifest = {
            "timeZone": "Europe/London",
            "dependencies": {},
            "exceptionLogging": "STACKDRIVER",
            "runtimeVersion": "V8"
        }
        
        files = [
            {
                "name": "Code",
                "type": "SERVER_JS",
                "source": script_content
            },
            {
                "name": "appsscript",
                "type": "JSON",
                "source": json.dumps(script_manifest, indent=2)
            }
        ]
        
        request = {
            'files': files
        }
        
        # Update the script project
        print("📤 Uploading script code...")
        response = script_service.projects().updateContent(
            scriptId=script_id,
            body=request
        ).execute()
        
        print("✅ Script deployed successfully!")
        return True
        
    except HttpError as error:
        print(f"❌ Error deploying script: {error}")
        if hasattr(error, 'content'):
            print(f"Details: {error.content}")
        return False

def main():
    """Main execution"""
    print("=" * 70)
    print("🚀 AUTOMATIC APPS SCRIPT DEPLOYMENT")
    print("=" * 70)
    print()
    
    # Step 1: Get credentials
    print("🔐 Loading credentials...")
    creds = get_credentials()
    if not creds:
        return 1
    
    print("✅ Credentials loaded\n")
    
    # Step 2: Read script file
    print(f"📖 Reading script file: {SCRIPT_FILE}...")
    script_content = read_script_file()
    if not script_content:
        return 1
    
    print(f"✅ Script file loaded ({len(script_content)} characters)\n")
    
    # Step 3: Get or create bound script
    print(f"🔍 Looking for bound script in spreadsheet...")
    script_id = get_container_script_id(SPREADSHEET_ID, creds)
    
    if not script_id:
        print("📝 Creating new bound script...")
        script_id = create_bound_script(SPREADSHEET_ID, creds)
        if not script_id:
            print("❌ Failed to create script")
            return 1
    
    print()
    
    # Step 4: Deploy script
    print("🚀 Deploying chart automation script...")
    success = deploy_script(script_id, script_content, creds)
    
    if not success:
        print("\n❌ DEPLOYMENT FAILED")
        return 1
    
    # Success!
    print("\n" + "=" * 70)
    print("✅ APPS SCRIPT DEPLOYED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("📋 Next Steps:")
    print("1. Open your spreadsheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print()
    print("2. Go to: Extensions → Apps Script")
    print()
    print("3. You should see the deployed code")
    print()
    print("4. Run the 'createAllCharts' function:")
    print("   - Select 'createAllCharts' from function dropdown")
    print("   - Click ▶ Run button")
    print("   - Grant permissions when prompted")
    print()
    print("5. Go back to spreadsheet and see your 4 charts!")
    print()
    print("6. (Optional) Set up trigger:")
    print("   - Click ⏰ Clock icon in Apps Script")
    print("   - Add Trigger: updateCharts, Time-driven, Every 30 minutes")
    print()
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
