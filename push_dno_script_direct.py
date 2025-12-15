#!/usr/bin/env python3
"""
Push DNO Map script directly to spreadsheet using Apps Script API
No clasp authentication needed - uses service account
"""

import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SCRIPT_FILE = '/home/george/GB-Power-Market-JJ/dno_map_apps_script.gs'

def main():
    print("🚀 Deploying DNO Map to Google Sheet via Apps Script API...")
    print("=" * 80)
    
    # Authenticate
    print("\n🔐 Authenticating with service account...")
    creds_file = os.path.expanduser('~/inner-cinema-credentials.json')
    
    if not os.path.exists(creds_file):
        print(f"❌ Credentials not found: {creds_file}")
        return
    
    scopes = [
        'https://www.googleapis.com/auth/script.projects',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    
    # Read the script code
    print(f"\n📂 Reading {SCRIPT_FILE}...")
    with open(SCRIPT_FILE, 'r') as f:
        script_code = f.read()
    print(f"   ✅ Loaded {len(script_code)} characters")
    
    # Build services
    script_service = build('script', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Find or create Apps Script project bound to spreadsheet
    print(f"\n🔍 Searching for Apps Script in spreadsheet...")
    
    try:
        query = f"'{SPREADSHEET_ID}' in parents and mimeType='application/vnd.google-apps.script'"
        results = drive_service.files().list(
            q=query,
            fields='files(id, name)',
            supportsAllDrives=True
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            script_id = files[0]['id']
            print(f"   ✅ Found existing script: {files[0]['name']} ({script_id})")
        else:
            print("   ℹ️  No script found, will create via manual steps")
            print("\n" + "=" * 80)
            print("📋 MANUAL STEPS NEEDED (One-time setup):")
            print("=" * 80)
            print(f"\n1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
            print("\n2. Go to: Extensions → Apps Script")
            print("   (This creates the container-bound script)")
            print("\n3. Note the Script ID from the URL")
            print("   (Format: https://script.google.com/...projects/SCRIPT_ID/edit)")
            print("\n4. Run this script again with the Script ID:")
            print(f"   python3 {__file__} SCRIPT_ID")
            print("\n" + "=" * 80)
            return
        
        # Update the script
        print(f"\n📝 Updating script content...")
        
        # Get current project
        project = script_service.projects().getContent(scriptId=script_id).execute()
        
        # Update Code.gs
        files_content = []
        code_updated = False
        
        for file in project.get('files', []):
            if file['name'] == 'Code':
                files_content.append({
                    'name': 'Code',
                    'type': 'SERVER_JS',
                    'source': script_code
                })
                code_updated = True
            else:
                files_content.append(file)
        
        if not code_updated:
            files_content.append({
                'name': 'Code',
                'type': 'SERVER_JS',
                'source': script_code
            })
        
        # Push update
        print("   🚀 Pushing to Apps Script...")
        response = script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': files_content}
        ).execute()
        
        print("   ✅ Script updated successfully!")
        
        print("\n" + "=" * 80)
        print("✅ DEPLOYMENT COMPLETE!")
        print("=" * 80)
        print(f"\n🔗 Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        print(f"🔗 Script Editor: https://script.google.com/home/projects/{script_id}/edit")
        print("\n🗺️  To use the map:")
        print("   1. Refresh the spreadsheet")
        print("   2. Look for menu: 🗺️ DNO Map")
        print("   3. Click: 🗺️ DNO Map → View Interactive Map")
        print("\n" + "=" * 80)
        
    except HttpError as e:
        if 'insufficient authentication scopes' in str(e).lower():
            print("\n⚠️  Service account lacks Apps Script API permissions")
            print("   Using gspread workaround instead...")
            use_gspread_workaround(script_code)
        else:
            print(f"\n❌ Error: {e}")
            raise

def use_gspread_workaround(script_code):
    """Add instructions to sheet as workaround"""
    import gspread
    
    print("\n📝 Adding deployment instructions to sheet...")
    
    creds_file = os.path.expanduser('~/inner-cinema-credentials.json')
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    
    # Create or get Instructions sheet
    try:
        sheet = spreadsheet.worksheet('DNO Map Instructions')
    except:
        sheet = spreadsheet.add_worksheet('DNO Map Instructions', rows=30, cols=10)
    
    # Add instructions
    instructions = [
        ["🗺️ DNO MAP - APPS SCRIPT DEPLOYMENT"],
        [""],
        ["The code is ready! Follow these steps:"],
        [""],
        ["1. Open Extensions → Apps Script"],
        ["2. Delete any existing code in Code.gs"],
        ["3. Copy the code from the file: dno_map_apps_script.gs"],
        ["4. Paste into Code.gs"],
        ["5. Save (Ctrl+S)"],
        ["6. Refresh this spreadsheet"],
        ["7. New menu appears: 🗺️ DNO Map → View Interactive Map"],
        [""],
        [f"Code location: {os.path.abspath(SCRIPT_FILE)}"],
        [f"Code length: {len(script_code)} characters"],
        [""],
        ["Note: The code is also saved in your project directory"]
    ]
    
    sheet.update('A1:J16', instructions)
    
    print("   ✅ Instructions added to sheet")
    print(f"\n📋 View instructions: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # Script ID provided
        script_id = sys.argv[1]
        print(f"Using provided Script ID: {script_id}")
        # TODO: Implement direct update with provided ID
    else:
        main()
