#!/usr/bin/env python3
"""
Deploy Enhanced Dashboard Apps Script (v2)
Deploys the new dashboard functions with charts, auto-refresh, and normalization
"""

import pickle
import os
from googleapiclient.discovery import build

# Configuration
SCRIPT_ID = '19d9ooPFGTrzRERacvirLsL-LLWzAwGbUfc7WV-4SFhfF59pefOj8vvkA'  # Current Apps Script
TOKEN_FILE = 'apps_script_token.pickle'

def load_credentials():
    """Load saved OAuth credentials"""
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"Token file not found: {TOKEN_FILE}\nRun setup_oauth_for_upower.py first")
    
    with open(TOKEN_FILE, 'rb') as f:
        return pickle.load(f)

def read_dashboard_code():
    """Read the new dashboard code from Downloads"""
    code_file = os.path.expanduser('~/Downloads/gb_energy_dashboard_functions_v2.gs')
    
    if not os.path.exists(code_file):
        raise FileNotFoundError(f"Dashboard code not found: {code_file}")
    
    with open(code_file, 'r', encoding='utf-8') as f:
        return f.read()

def deploy_dashboard():
    """Deploy the enhanced dashboard to Apps Script"""
    print("🚀 Deploying Enhanced Dashboard v2 to Apps Script...")
    print(f"📝 Script ID: {SCRIPT_ID}")
    
    # Load credentials
    creds = load_credentials()
    service = build('script', 'v1', credentials=creds)
    
    # Read the new dashboard code
    print("\n📂 Reading dashboard code from Downloads...")
    code = read_dashboard_code()
    print(f"✅ Loaded {len(code)} characters of code")
    
    # Get current script content to preserve other files
    print("\n🔍 Fetching current script content...")
    try:
        current = service.projects().getContent(scriptId=SCRIPT_ID).execute()
        print(f"✅ Found {len(current.get('files', []))} existing files")
    except Exception as e:
        print(f"⚠️  Warning: Could not fetch current content: {e}")
        current = {'files': []}
    
    # Prepare the new content
    files = []
    
    # Add the new dashboard code
    files.append({
        'name': 'DashboardFunctions',
        'type': 'SERVER_JS',
        'source': code
    })
    
    # Preserve appsscript.json if it exists
    for file in current.get('files', []):
        if file.get('name') == 'appsscript':
            print(f"✅ Preserving existing appsscript.json")
            files.append(file)
    
    # If no appsscript.json exists, create a basic one
    if not any(f.get('name') == 'appsscript' for f in files):
        print("📝 Creating new appsscript.json")
        files.append({
            'name': 'appsscript',
            'type': 'JSON',
            'source': '''{
  "timeZone": "Europe/London",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/script.container.ui",
    "https://www.googleapis.com/auth/script.scriptapp"
  ]
}'''
        })
    
    # Update the script
    print(f"\n🔄 Updating Apps Script with {len(files)} files...")
    request = {'files': files}
    
    try:
        response = service.projects().updateContent(
            scriptId=SCRIPT_ID,
            body=request
        ).execute()
        
        print("\n✅ Successfully deployed Enhanced Dashboard v2!")
        print(f"✅ Updated {len(response.get('files', []))} files")
        
        print("\n📋 Deployment Summary:")
        print("   • Dashboard Functions with chart creation")
        print("   • Auto-refresh trigger (15 minutes)")
        print("   • Data normalization and flag fixing")
        print("   • Custom menu (Dashboard → Setup/Refresh/etc.)")
        print("   • Audit logging to Audit_Log sheet")
        
        print("\n📝 Next Steps:")
        print("1. Open your Google Sheet:")
        print("   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit")
        print("\n2. Reload the page to see the new 'Dashboard' menu")
        print("\n3. Click: Dashboard → Setup (rename+sync+chart+trigger)")
        print("   This will:")
        print("   • Rename/create the Dashboard sheet")
        print("   • Normalize data")
        print("   • Create Market Overview chart")
        print("   • Set up 15-minute auto-refresh")
        print("\n4. Check the 'Dashboard' sheet for the new chart!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error deploying script: {e}")
        if hasattr(e, 'content'):
            print(f"Details: {e.content}")
        return False

if __name__ == '__main__':
    try:
        success = deploy_dashboard()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        exit(1)
