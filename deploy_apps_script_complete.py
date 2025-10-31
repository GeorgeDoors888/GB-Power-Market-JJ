#!/usr/bin/env python3
"""
Complete Apps Script Automation
1. Deploys chart script to Google Sheets
2. Runs createAllCharts function automatically
3. Sets up time-driven trigger (optional)
"""
import os
import json
import time
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
    'https://www.googleapis.com/auth/script.deployments',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials():
    """Get or refresh OAuth2 credentials"""
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing credentials...")
            creds.refresh(Request())
        else:
            print("❌ No valid credentials found!")
            print("Please run authorize_google_docs.py first to create token.pickle")
            return None
        
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
        drive_service = build('drive', 'v3', credentials=creds)
        
        spreadsheet = drive_service.files().get(
            fileId=spreadsheet_id,
            fields='id,name'
        ).execute()
        
        print(f"📊 Found spreadsheet: {spreadsheet.get('name')}")
        
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
            return None
            
    except HttpError as error:
        print(f"❌ Error finding script: {error}")
        return None

def create_bound_script(spreadsheet_id, creds):
    """Create a new bound Apps Script project"""
    try:
        script_service = build('script', 'v1', credentials=creds)
        
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
        
        request = {'files': files}
        
        print("📤 Uploading script code...")
        response = script_service.projects().updateContent(
            scriptId=script_id,
            body=request
        ).execute()
        
        print("✅ Script deployed successfully!")
        return True
        
    except HttpError as error:
        print(f"❌ Error deploying script: {error}")
        return False

def run_function(script_id, function_name, creds):
    """Execute a function in the deployed script"""
    try:
        script_service = build('script', 'v1', credentials=creds)
        
        print(f"▶️  Running function: {function_name}...")
        
        request = {
            'function': function_name,
            'devMode': True
        }
        
        response = script_service.scripts().run(
            scriptId=script_id,
            body=request
        ).execute()
        
        if 'error' in response:
            error = response['error']
            print(f"❌ Script execution error:")
            print(f"   Message: {error.get('message', 'Unknown error')}")
            if 'details' in error:
                print(f"   Details: {error['details']}")
            return False
        else:
            print(f"✅ Function '{function_name}' executed successfully!")
            if 'response' in response:
                result = response['response'].get('result')
                if result:
                    print(f"   Result: {result}")
            return True
            
    except HttpError as error:
        print(f"❌ Error running function: {error}")
        
        # Special handling for permission errors
        if error.resp.status == 403:
            print("\n⚠️  Authorization Required:")
            print("   This is the first run, so you need to authorize the script manually.")
            print("   Please:")
            print(f"   1. Open: https://script.google.com/d/{script_id}/edit")
            print("   2. Select 'createAllCharts' from function dropdown")
            print("   3. Click ▶ Run button")
            print("   4. Grant permissions when prompted")
            print("   5. Charts will be created!")
            return None
        
        return False

def create_trigger(script_id, creds):
    """Create a time-driven trigger for updateCharts function"""
    try:
        script_service = build('script', 'v1', credentials=creds)
        
        print("⏰ Creating time-driven trigger (every 30 minutes)...")
        
        trigger = {
            'triggerFunction': 'updateCharts',
            'timeBased': {
                'everyMinutes': 30
            }
        }
        
        response = script_service.projects().triggers().create(
            scriptId=script_id,
            body=trigger
        ).execute()
        
        print(f"✅ Trigger created: {response.get('triggerId')}")
        return True
        
    except HttpError as error:
        print(f"⚠️  Could not create trigger automatically: {error}")
        print("   You can create it manually in Apps Script editor:")
        print("   Click ⏰ Clock icon → Add Trigger → updateCharts → Every 30 minutes")
        return False

def main():
    """Main execution"""
    print("=" * 70)
    print("🚀 COMPLETE APPS SCRIPT AUTOMATION")
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
            return 1
    print()
    
    # Step 4: Deploy script
    print("🚀 Deploying chart automation script...")
    success = deploy_script(script_id, script_content, creds)
    if not success:
        return 1
    print()
    
    # Step 5: Manual chart creation (API execution requires additional setup)
    print("📊 Script deployed successfully!")
    print("⚠️  Charts need to be created manually (one-time setup)")
    print()
    print("=" * 70)
    print("📋 NEXT STEPS - CREATE CHARTS (2 minutes)")
    print("=" * 70)
    print()
    print("1. Open Apps Script editor:")
    print(f"   https://script.google.com/d/{script_id}/edit")
    print()
    print("2. You should see the deployed code with all functions")
    print()
    print("3. Select 'createAllCharts' from the function dropdown (top)")
    print()
    print("4. Click the ▶ Run button")
    print()
    print("5. Grant permissions when prompted:")
    print("   - Review Permissions")
    print("   - Choose your account")
    print("   - Advanced → Go to Dashboard Charts")
    print("   - Allow")
    print()
    print("6. Wait for execution to complete (check logs)")
    print()
    print("7. Go back to your spreadsheet - you'll see 4 charts!")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print()
    print("=" * 70)
    
    print()
    print("� TIP: After creating charts, you can set up auto-updates:")
    print("   - In Apps Script editor, click ⏰ Clock icon (Triggers)")
    print("   - Add Trigger: updateCharts, Time-driven, Every 30 minutes")
    print()
    print("✅ Script deployment complete!")
    print()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
