#!/usr/bin/env python3
"""
Deploy DNO Lookup to Apps Script via API
Requires the Apps Script project ID
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import sys

def deploy_to_apps_script(script_id):
    """Deploy DNO lookup code to Apps Script via API"""
    
    print("=" * 80)
    print("⚡ Deploying to Apps Script via API")
    print("=" * 80)
    
    # Read the DNO lookup code
    with open('bess_dno_lookup.gs', 'r') as f:
        dno_code = f.read()
    
    print(f"✅ Loaded DNO lookup code ({len(dno_code)} chars)")
    
    # Authenticate
    SCOPES = [
        'https://www.googleapis.com/auth/script.projects',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json', 
        scopes=SCOPES
    )
    
    script_service = build('script', 'v1', credentials=creds)
    print("✅ Authenticated with Apps Script API")
    
    # Get current project
    try:
        project = script_service.projects().get(scriptId=script_id).execute()
        print(f"✅ Found project: {project.get('title', 'Untitled')}")
        print(f"   Current files: {len(project.get('files', []))}")
        
        # Show current files
        for f in project.get('files', []):
            print(f"   - {f.get('name')} ({f.get('type')})")
        
    except Exception as e:
        print(f"❌ Cannot access script: {e}")
        print("\n💡 Make sure:")
        print("   1. Script ID is correct")
        print("   2. Script is shared with service account email:")
        print("      inner-cinema-476211-u9@appspot.gserviceaccount.com")
        return False
    
    # Prepare new files (add DNO lookup, keep existing)
    existing_files = project.get('files', [])
    new_files = []
    
    # Always need manifest file
    manifest_exists = False
    
    # Keep existing files
    for f in existing_files:
        new_files.append({
            'name': f['name'],
            'type': f['type'],
            'source': f['source']
        })
        if f['name'] == 'appsscript':
            manifest_exists = True
    
    # Add manifest if missing
    if not manifest_exists:
        manifest = {
            'name': 'appsscript',
            'type': 'JSON',
            'source': '''{
  "timeZone": "Europe/London",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8"
}'''
        }
        new_files.append(manifest)
        print("   ℹ️  Adding manifest file (appsscript.json)")
    
    # Add DNO lookup as new file
    new_files.append({
        'name': 'DNO_Lookup',
        'type': 'SERVER_JS',
        'source': dno_code
    })
    
    print(f"\n📝 Deploying {len(new_files)} files:")
    for f in new_files:
        print(f"   - {f['name']}")
    
    # Deploy
    try:
        response = script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': new_files}
        ).execute()
        
        print(f"\n✅ Deployment successful!")
        print(f"   Files in project: {len(response.get('files', []))}")
        
        print("\n🔄 Next: Reload your spreadsheet to see new menu")
        print("   Menu: 🔌 DNO Lookup will appear")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        
        if '403' in str(e) or 'permission' in str(e).lower():
            print("\n💡 Permission issue:")
            print("   Share the Apps Script project with:")
            print("   inner-cinema-476211-u9@appspot.gserviceaccount.com")
            print("   Role: Editor")
        
        return False

def find_script_id_interactive():
    """Help user find their script ID"""
    
    print("\n" + "=" * 80)
    print("📋 How to Find Your Apps Script ID")
    print("=" * 80)
    
    print("\n1. Open your Google Sheet")
    print("   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit")
    
    print("\n2. Go to: Extensions → Apps Script")
    
    print("\n3. In the Apps Script editor, click: ⚙️ Project Settings (left sidebar)")
    
    print("\n4. Copy the 'Script ID' (under 'IDs' section)")
    print("   It looks like: 1AbC...xYz (33 characters)")
    
    print("\n5. Run this script with the ID:")
    print("   python3 deploy_dno_to_apps_script.py YOUR_SCRIPT_ID")
    
    print("\n" + "=" * 80)
    print("🔐 IMPORTANT: Share the script with service account")
    print("=" * 80)
    print("\nBefore deployment, share your Apps Script with:")
    print("   Email: inner-cinema-476211-u9@appspot.gserviceaccount.com")
    print("   Role: Editor")
    print("\nHow to share:")
    print("   1. In Apps Script editor, click 'Share' (top right)")
    print("   2. Add the email above")
    print("   3. Set permission to 'Editor'")
    print("   4. Click 'Done'")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Missing script ID")
        find_script_id_interactive()
        sys.exit(1)
    
    script_id = sys.argv[1]
    
    if len(script_id) < 20:
        print("❌ Invalid script ID (too short)")
        print("   Script IDs are ~33 characters long")
        find_script_id_interactive()
        sys.exit(1)
    
    print(f"Script ID: {script_id}")
    
    success = deploy_to_apps_script(script_id)
    
    sys.exit(0 if success else 1)
