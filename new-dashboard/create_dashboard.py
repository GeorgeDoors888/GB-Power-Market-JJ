#!/usr/bin/env python3
"""
Create new Google Sheets dashboard with proper Apps Script setup
Uses Google Sheets API + clasp for version control
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

CREDENTIALS_FILE = "../inner-cinema-credentials.json"
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/script.projects'
]

def create_new_dashboard():
    """Create new spreadsheet with proper structure"""
    
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Create new spreadsheet
    spreadsheet = {
        'properties': {
            'title': 'GB Energy Dashboard V2'
        },
        'sheets': [
            {'properties': {'title': 'Dashboard', 'gridProperties': {'rowCount': 200, 'columnCount': 26}}},
            {'properties': {'title': 'BESS', 'gridProperties': {'rowCount': 100, 'columnCount': 20}}},
            {'properties': {'title': 'Generator Map Data', 'gridProperties': {'rowCount': 1000, 'columnCount': 15}}},
            {'properties': {'title': 'Outages', 'gridProperties': {'rowCount': 500, 'columnCount': 10}}}
        ]
    }
    
    print("📊 Creating new spreadsheet...")
    result = sheets_service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = result['spreadsheetId']
    spreadsheet_url = result['spreadsheetUrl']
    
    print(f"✅ Created: {spreadsheet_url}")
    print(f"   ID: {spreadsheet_id}")
    
    # Share with your account
    permission = {
        'type': 'user',
        'role': 'owner',
        'emailAddress': 'george@upowerenergy.uk'
    }
    
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body=permission,
        transferOwnership=True
    ).execute()
    
    print(f"✅ Transferred ownership to george@upowerenergy.uk")
    
    # Save config
    config = {
        'spreadsheet_id': spreadsheet_id,
        'spreadsheet_url': spreadsheet_url,
        'sheets': {
            'dashboard': 'Dashboard',
            'bess': 'BESS',
            'generator_map': 'Generator Map Data',
            'outages': 'Outages'
        }
    }
    
    with open('dashboard_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Config saved to dashboard_config.json")
    
    return spreadsheet_id, spreadsheet_url

if __name__ == '__main__':
    print("=" * 80)
    print("GB ENERGY DASHBOARD V2 - CLEAN START")
    print("=" * 80)
    print()
    
    spreadsheet_id, url = create_new_dashboard()
    
    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(f"1. Open: {url}")
    print(f"2. Run: clasp create --type sheets --title 'Dashboard Scripts' --parentId '{spreadsheet_id}'")
    print(f"3. This will set up Apps Script with proper version control")
    print()
