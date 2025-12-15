#!/usr/bin/env python3
"""
Deploy DNO Map Apps Script to Google Spreadsheet
Uses Apps Script API to update the script content
"""

import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Configuration
SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SCRIPT_FILE = 'dno_map_apps_script.gs'

def deploy_apps_script():
    """Deploy the Apps Script code to the spreadsheet"""
    
    print("🚀 Deploying DNO Map Apps Script...")
    print("=" * 80)
    
    # Authenticate
    print("\n🔐 Authenticating...")
    cred_paths = [
        'inner-cinema-credentials.json',
        os.path.expanduser('~/inner-cinema-credentials.json'),
        os.path.expanduser('~/.config/gcloud/inner-cinema-credentials.json')
    ]
    
    creds_file = None
    for path in cred_paths:
        if os.path.exists(path):
            creds_file = path
            break
    
    if not creds_file:
        print("❌ ERROR: Credentials file not found")
        return
    
    scopes = [
        'https://www.googleapis.com/auth/script.projects',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    
    # Build Apps Script service
    print("🔧 Building Apps Script service...")
    script_service = build('script', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Get the spreadsheet's bound script ID
    print(f"\n📊 Finding Apps Script for spreadsheet {SPREADSHEET_ID}...")
    
    try:
        # Search for container-bound script
        query = f"'{SPREADSHEET_ID}' in parents and mimeType='application/vnd.google-apps.script'"
        results = drive_service.files().list(
            q=query,
            fields='files(id, name)',
            supportsAllDrives=True
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print("⚠️  No Apps Script project found. Creating new one...")
            # Create a new bound script
            spreadsheet_service = build('sheets', 'v4', credentials=creds)
            spreadsheet = spreadsheet_service.spreadsheets().get(
                spreadsheetId=SPREADSHEET_ID
            ).execute()
            
            print("   Creating container-bound script...")
            # Note: Direct creation via API is complex, using workaround
            print("\n" + "=" * 80)
            print("⚠️  MANUAL STEP REQUIRED:")
            print("=" * 80)
            print("\n1. Open: https://docs.google.com/spreadsheets/d/" + SPREADSHEET_ID)
            print("\n2. Go to: Extensions → Apps Script")
            print("\n3. This will create the script project automatically")
            print("\n4. Copy the script ID from the URL (after /projects/)")
            print("\n5. Re-run this script")
            return
        
        script_id = files[0]['id']
        script_name = files[0]['name']
        print(f"   ✅ Found script: {script_name} (ID: {script_id})")
        
        # Read the Apps Script code
        print(f"\n📂 Reading {SCRIPT_FILE}...")
        with open(SCRIPT_FILE, 'r') as f:
            script_code = f.read()
        
        print(f"   ✅ Loaded {len(script_code)} characters")
        
        # Get current project content
        print("\n📥 Getting current project content...")
        try:
            project = script_service.projects().getContent(
                scriptId=script_id
            ).execute()
            
            print(f"   ✅ Current project has {len(project.get('files', []))} files")
            
            # Update the Code.gs file
            print("\n📝 Updating Code.gs...")
            
            files_content = []
            code_updated = False
            
            for file in project.get('files', []):
                if file['name'] == 'Code':
                    # Update existing Code.gs
                    files_content.append({
                        'name': 'Code',
                        'type': 'SERVER_JS',
                        'source': script_code
                    })
                    code_updated = True
                    print("   ✅ Updating existing Code.gs")
                else:
                    # Keep other files unchanged
                    files_content.append(file)
            
            if not code_updated:
                # Add new Code.gs if it doesn't exist
                files_content.append({
                    'name': 'Code',
                    'type': 'SERVER_JS',
                    'source': script_code
                })
                print("   ✅ Creating new Code.gs")
            
            # Push the updated content
            print("\n🚀 Pushing updated content...")
            request_body = {
                'files': files_content
            }
            
            response = script_service.projects().updateContent(
                scriptId=script_id,
                body=request_body
            ).execute()
            
            print("   ✅ Content updated successfully!")
            
            # Success message
            print("\n" + "=" * 80)
            print("✅ DEPLOYMENT COMPLETE!")
            print("=" * 80)
            print("\n📊 Apps Script deployed to spreadsheet")
            print(f"🔗 Script Editor: https://script.google.com/home/projects/{script_id}/edit")
            print(f"🔗 Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
            print("\n🗺️  To use the map:")
            print("   1. Refresh the spreadsheet in your browser")
            print("   2. Look for new menu: 🗺️ DNO Map")
            print("   3. Click: 🗺️ DNO Map → View Interactive Map")
            print("\n" + "=" * 80)
            
        except Exception as e:
            if 'insufficient authentication scopes' in str(e).lower():
                print(f"\n❌ ERROR: Insufficient permissions")
                print("   Service account needs Apps Script API access")
                print("\n   Alternative: Manual deployment")
                print("=" * 80)
                manual_deploy_instructions()
            else:
                raise
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n   Falling back to manual deployment instructions...")
        print("=" * 80)
        manual_deploy_instructions()

def manual_deploy_instructions():
    """Print manual deployment instructions"""
    print("\n📋 MANUAL DEPLOYMENT STEPS:")
    print("=" * 80)
    print("\n1. Open spreadsheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print("\n2. Go to: Extensions → Apps Script")
    print("\n3. Delete any existing code in Code.gs")
    print("\n4. Copy ALL content from: dno_map_apps_script.gs")
    print("\n5. Paste into Code.gs in the Apps Script editor")
    print("\n6. Click Save (💾 icon or Ctrl+S)")
    print("\n7. Close Apps Script editor")
    print("\n8. Refresh spreadsheet in browser")
    print("\n9. New menu appears: 🗺️ DNO Map")
    print("\n10. Click: 🗺️ DNO Map → View Interactive Map")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    deploy_apps_script()
