#!/usr/bin/env python3
"""Check for Apps Script projects bound to the spreadsheet"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SA_PATH = "inner-cinema-credentials.json"

# For Apps Script API
SCRIPT_SCOPES = [
    'https://www.googleapis.com/auth/script.projects.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

try:
    creds = Credentials.from_service_account_file(SA_PATH, scopes=SCRIPT_SCOPES)
    
    # Try Drive API to get container info
    drive = build('drive', 'v3', credentials=creds)
    
    print("=" * 80)
    print("🔍 CHECKING FOR APPS SCRIPT INTERFERENCE")
    print("=" * 80)
    
    # Get file metadata
    file = drive.files().get(
        fileId=SHEET_ID,
        fields='id,name,createdTime,modifiedTime,owners,capabilities'
    ).execute()
    
    print("\n📄 Spreadsheet Info:")
    print(f"   Name: {file.get('name')}")
    print(f"   Created: {file.get('createdTime')}")
    print(f"   Modified: {file.get('modifiedTime')}")
    print(f"   Owners: {[o.get('emailAddress') for o in file.get('owners', [])]}")
    
    # Check for bound scripts (they would be in the same folder typically)
    print("\n🔍 Checking for bound Apps Script project...")
    
    # Try to list files that might be scripts
    results = drive.files().list(
        q=f"'{SHEET_ID}' in parents and mimeType='application/vnd.google-apps.script'",
        fields="files(id, name, mimeType)"
    ).execute()
    
    script_files = results.get('files', [])
    
    if script_files:
        print(f"\n⚠️  FOUND {len(script_files)} Apps Script project(s):")
        for sf in script_files:
            print(f"   - {sf.get('name')} (ID: {sf.get('id')})")
    else:
        print("\n✅ No bound Apps Script projects found")
    
    # Check Sheets API for any data validation or protected ranges
    sheets = build('sheets', 'v4', credentials=creds)
    
    spreadsheet = sheets.spreadsheets().get(
        spreadsheetId=SHEET_ID,
        fields='sheets(properties,protectedRanges,data)'
    ).execute()
    
    print("\n📊 Checking Dashboard sheet for interference...")
    
    for sheet in spreadsheet.get('sheets', []):
        props = sheet.get('properties', {})
        if props.get('title') == 'Dashboard':
            print(f"\n   Sheet ID: {props.get('sheetId')}")
            print(f"   Grid properties: {props.get('gridProperties')}")
            
            # Check for protected ranges
            protected = sheet.get('protectedRanges', [])
            if protected:
                print(f"\n   ⚠️  FOUND {len(protected)} protected range(s):")
                for pr in protected:
                    print(f"      - Range: {pr.get('range')}")
                    print(f"        Warning: {pr.get('warningOnly')}")
            else:
                print("\n   ✅ No protected ranges")
    
    print("\n" + "=" * 80)
    print("✅ Apps Script check complete")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error checking Apps Script: {e}")
    print("\nℹ️  This might be because the service account doesn't have Apps Script API access")
    print("   which is normal. The Dashboard layout looks correct from your paste.")
