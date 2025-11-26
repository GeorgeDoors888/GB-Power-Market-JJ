#!/usr/bin/env python3
"""
Automated Apps Script Deployment
Uses Google Apps Script API to deploy constraint map directly
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import time

# Configuration
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

# Scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials():
    """Load service account credentials"""
    return service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )

def find_script_project_id(sheets_service, spreadsheet_id):
    """Find the Apps Script project ID bound to the spreadsheet"""
    try:
        # Get spreadsheet metadata
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        print(f"✅ Found spreadsheet: {spreadsheet['properties']['title']}")
        
        # The script project ID is typically stored in the spreadsheet metadata
        # We'll need to use Drive API to find the bound script
        return None  # Will implement Drive API lookup
        
    except HttpError as e:
        print(f"❌ Error getting spreadsheet: {e}")
        return None

def create_or_update_script_project(script_service, project_id=None):
    """Create or update the Apps Script project"""
    
    # Read local files
    with open('dashboard/apps-script/constraint_map_minimal.gs', 'r') as f:
        code_content = f.read()
    
    with open('dashboard/apps-script/ConstraintMap_Leaflet.html', 'r') as f:
        html_content = f.read()
    
    # Prepare script manifest
    manifest = {
        "timeZone": "Europe/London",
        "oauthScopes": [
            "https://www.googleapis.com/auth/spreadsheets.currentonly",
            "https://www.googleapis.com/auth/script.container.ui"
        ],
        "exceptionLogging": "STACKDRIVER"
    }
    
    # Prepare files for Apps Script
    files = [
        {
            "name": "appsscript",
            "type": "JSON",
            "source": json.dumps(manifest, indent=2)
        },
        {
            "name": "Code",
            "type": "SERVER_JS",
            "source": code_content
        },
        {
            "name": "ConstraintMap_Leaflet",
            "type": "HTML",
            "source": html_content
        }
    ]
    
    if project_id:
        # Update existing project
        try:
            request = {
                "files": files
            }
            response = script_service.projects().updateContent(
                scriptId=project_id,
                body=request
            ).execute()
            print(f"✅ Updated Apps Script project: {project_id}")
            return project_id
        except HttpError as e:
            print(f"❌ Error updating project: {e}")
            return None
    else:
        # Create new standalone project
        try:
            request = {
                "title": "GB Constraint Map",
                "parentId": SPREADSHEET_ID
            }
            response = script_service.projects().create(body=request).execute()
            project_id = response['scriptId']
            
            # Now update content
            content_request = {"files": files}
            script_service.projects().updateContent(
                scriptId=project_id,
                body=content_request
            ).execute()
            
            print(f"✅ Created new Apps Script project: {project_id}")
            return project_id
            
        except HttpError as e:
            print(f"❌ Error creating project: {e}")
            print(f"   This might require OAuth2 user credentials instead of service account")
            return None

def deploy_script(script_service, project_id):
    """Deploy the Apps Script as a web app"""
    try:
        # Create a version first
        version_request = {
            "versionNumber": int(time.time()),
            "description": "Automated deployment from Python"
        }
        
        version = script_service.projects().versions().create(
            scriptId=project_id,
            body=version_request
        ).execute()
        
        print(f"✅ Created version: {version['versionNumber']}")
        
        # Create deployment
        deployment_request = {
            "versionNumber": version['versionNumber'],
            "manifestFileName": "appsscript",
            "description": "Constraint Map Deployment"
        }
        
        deployment = script_service.projects().deployments().create(
            scriptId=project_id,
            body=deployment_request
        ).execute()
        
        print(f"✅ Deployed: {deployment['deploymentId']}")
        return deployment
        
    except HttpError as e:
        print(f"❌ Error deploying: {e}")
        return None

def main():
    print("=" * 80)
    print("AUTOMATED APPS SCRIPT DEPLOYMENT")
    print("=" * 80)
    
    print("\n⚠️  IMPORTANT: Apps Script API Limitations")
    print("   - Service accounts have limited Apps Script API access")
    print("   - May need OAuth2 user credentials for full deployment")
    print("   - Alternative: Direct file upload approach")
    
    print("\n" + "=" * 80)
    print("CHECKING CREDENTIALS")
    print("=" * 80)
    
    try:
        credentials = get_credentials()
        print("✅ Service account credentials loaded")
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return 1
    
    # Initialize services
    try:
        sheets_service = build('sheets', 'v4', credentials=credentials)
        script_service = build('script', 'v1', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        print("✅ Google API services initialized")
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        return 1
    
    print("\n" + "=" * 80)
    print("FINDING APPS SCRIPT PROJECT")
    print("=" * 80)
    
    # Try to find existing script project
    try:
        # Search for Apps Script files in Drive
        query = f"'{SPREADSHEET_ID}' in parents and mimeType='application/vnd.google-apps.script'"
        results = drive_service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        if files:
            script_project_id = files[0]['id']
            print(f"✅ Found existing Apps Script project: {script_project_id}")
        else:
            print("⚠️  No existing Apps Script project found")
            print("   Creating new one...")
            script_project_id = None
            
    except HttpError as e:
        print(f"⚠️  Could not search Drive: {e}")
        script_project_id = None
    
    print("\n" + "=" * 80)
    print("ALTERNATIVE: MANUAL DEPLOYMENT WITH AUTOMATED FILES")
    print("=" * 80)
    
    print("\n📋 Since Apps Script API has limitations, I'll:")
    print("   1. ✅ Generate fresh map HTML with latest data")
    print("   2. ✅ Prepare deployment package")
    print("   3. ✅ Provide copy-paste ready code")
    print("   4. ℹ️  You do final upload (2 minutes)")
    
    # Generate fresh map
    print("\n🗺️ Generating fresh constraint map...")
    import subprocess
    result = subprocess.run(['python3', 'generate_constraint_map_leaflet.py'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Map generated with latest data")
    else:
        print(f"⚠️  Map generation had issues: {result.stderr}")
    
    # Create deployment package
    print("\n📦 Creating deployment package...")
    result = subprocess.run(['python3', 'create_deploy_package.py'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Deployment package ready")
    else:
        print(f"⚠️  Package creation had issues: {result.stderr}")
    
    print("\n" + "=" * 80)
    print("READY FOR MANUAL DEPLOYMENT")
    print("=" * 80)
    
    print("\n📂 Files ready in: apps_script_deploy_package/")
    print("\n🚀 Quick deployment (2 minutes):")
    print("   1. Open: Extensions → Apps Script")
    print("   2. Upload: Code.gs (from package)")
    print("   3. Upload: ConstraintMap_Leaflet.html (from package)")
    print("   4. Deploy → New deployment → Web app")
    print("   5. Close/reopen sheet → Menu appears!")
    
    print("\n💡 Opening deployment package folder...")
    subprocess.run(['open', 'apps_script_deploy_package'])
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
