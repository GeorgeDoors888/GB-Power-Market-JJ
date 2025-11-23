#!/usr/bin/env python3
"""
Automated Apps Script Installer for BESS Sheet
Automatically deploys DNO lookup functionality via Google Apps Script API
"""

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import sys

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

def install_apps_script_automated():
    """Fully automated Apps Script installation"""
    
    print("=" * 80)
    print("🚀 Automated Apps Script Installation")
    print("=" * 80)
    
    # Read the Apps Script content
    try:
        with open('bess_dno_lookup.gs', 'r') as f:
            script_content = f.read()
        print("✅ Loaded script file: bess_dno_lookup.gs")
    except FileNotFoundError:
        print("❌ Error: bess_dno_lookup.gs not found")
        return False
    
    # Authenticate
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/script.projects'
    ]
    
    try:
        creds = Credentials.from_service_account_file(
            'inner-cinema-credentials.json', 
            scopes=SCOPES
        )
        print("✅ Authenticated with Google APIs")
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Connect to Google Sheets
    try:
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        print(f"✅ Connected to sheet: {sh.title}")
    except Exception as e:
        print(f"❌ Sheet connection error: {e}")
        return False
    
    # Build Apps Script API service
    try:
        script_service = build('script', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        print("✅ API services initialized")
    except Exception as e:
        print(f"❌ API service error: {e}")
        return False
    
    # Find the Apps Script project
    try:
        query = f"'{SHEET_ID}' in parents and mimeType='application/vnd.google-apps.script'"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, createdTime)'
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print("\n⚠️ No Apps Script project found")
            print("\n📋 ONE-TIME SETUP REQUIRED:")
            print("=" * 80)
            print("\nStep 1: Create the script container (takes 10 seconds)")
            print(f"   → Open: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
            print("   → Click: Extensions → Apps Script")
            print("   → Wait for editor to open")
            print("   → Close the Apps Script tab")
            print("\nStep 2: Run this script again")
            print("   → python3 install_apps_script_auto.py")
            print("\n" + "=" * 80)
            return False
        
        script_id = files[0]['id']
        print(f"✅ Found Apps Script: {files[0]['name']}")
        print(f"   Script ID: {script_id}")
        
    except Exception as e:
        print(f"❌ Error finding script: {e}")
        return False
    
    # Update script content
    try:
        print("\n📝 Deploying DNO lookup script...")
        
        # Prepare the files
        files_to_update = [{
            'name': 'Code',
            'type': 'SERVER_JS',
            'source': script_content
        }]
        
        # Update the project
        response = script_service.projects().updateContent(
            scriptId=script_id,
            body={'files': files_to_update}
        ).execute()
        
        print("✅ Script deployed successfully!")
        print(f"   Files: {len(response.get('files', []))}")
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        if "403" in str(e):
            print("\n⚠️ Permission issue - service account may need Apps Script API enabled")
            print("   Try manual installation from bess_dno_lookup.gs")
        return False
    
    # Update BESS sheet with success message
    try:
        bess_ws = sh.worksheet("BESS")
        
        success_msg = [[
            '✅ DNO LOOKUP INSTALLED',
            'Reload sheet → See menu: 🔌 DNO Lookup',
            'Enter MPAN (10-23) in B6 → Click Refresh',
            'Select voltage in A9 → Rates auto-fill B9:D9',
            '',
            '',
            '',
            ''
        ]]
        
        bess_ws.update(success_msg, 'A4:H4')
        bess_ws.format('A4:H4', {
            'backgroundColor': {'red': 0.5, 'green': 0.9, 'blue': 0.5},
            'textFormat': {'bold': True, 'fontSize': 11}
        })
        
        print("✅ Updated BESS sheet with instructions")
        
    except Exception as e:
        print(f"⚠️ Could not update sheet: {e}")
    
    # Success summary
    print("\n" + "=" * 80)
    print("🎉 INSTALLATION COMPLETE!")
    print("=" * 80)
    
    print("\n📋 What was installed:")
    print("   • Menu: 🔌 DNO Lookup (4 items)")
    print("   • Function: Auto-lookup DNO by MPAN ID")
    print("   • Function: Auto-populate DUoS rates")
    print("   • Function: Instructions dialog")
    
    print("\n🔄 Next Steps:")
    print("   1. Reload your spreadsheet")
    print(f"      → https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
    print("   2. You'll see: 🔌 DNO Lookup in the menu bar")
    print("   3. First use: Grant permissions when prompted")
    
    print("\n🎯 Quick Start Guide:")
    print("   • Enter MPAN ID (10-23) in cell B6")
    print("     Example: 12 for London, 23 for Yorkshire")
    print("   • Menu: 🔌 DNO Lookup → 🔄 Refresh DNO Data")
    print("   • Result: C6-H6 auto-fill with DNO details")
    print("   • Select voltage in A9 dropdown (LV/HV/EHV)")
    print("   • Result: B9-D9 show Red/Amber/Green DUoS rates")
    
    print("\n📊 MPAN Quick Reference:")
    print("   10=Eastern, 11=E.Mids, 12=London, 13=Mersey, 14=W.Mids")
    print("   15=N.East, 16=N.West, 17=N.Scotland, 18=S.Scotland")
    print("   19=S.Eastern, 20=Southern, 21=S.Wales, 22=S.Western, 23=Yorkshire")
    
    print("\n" + "=" * 80)
    return True

if __name__ == "__main__":
    success = install_apps_script_automated()
    sys.exit(0 if success else 1)
