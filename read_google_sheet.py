#!/usr/bin/env python3
"""
Read Google Sheet data using Sheets API with OAuth credentials
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
TOKEN_FILE = "apps_script_token.pickle"
CREDENTIALS_FILE = "oauth_credentials.json"

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_oauth_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing OAuth token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def main():
    print("=" * 70)
    print("📊 READING GOOGLE SHEET DATA")
    print("=" * 70)
    print()
    
    creds = get_oauth_credentials()
    service = build('sheets', 'v4', credentials=creds)
    
    # Get list of sheets
    print("📋 Getting sheet metadata...")
    spreadsheet = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheets = spreadsheet.get('sheets', [])
    
    print(f"✅ Found {len(sheets)} sheets:")
    for sheet in sheets:
        props = sheet.get('properties', {})
        name = props.get('title', 'Unknown')
        row_count = props.get('gridProperties', {}).get('rowCount', 0)
        col_count = props.get('gridProperties', {}).get('columnCount', 0)
        print(f"  - {name}: {row_count} rows x {col_count} cols")
    print()
    
    # Read Live Dashboard
    print("=" * 70)
    print("📊 LIVE DASHBOARD DATA")
    print("=" * 70)
    print()
    
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='Live Dashboard!A1:J10'
        ).execute()
        
        values = result.get('values', [])
        if values:
            print(f"First 10 rows of Live Dashboard:")
            print()
            for i, row in enumerate(values):
                # Pad row to ensure consistent formatting
                padded_row = row + [''] * (10 - len(row))
                print(f"Row {i+1}: {' | '.join(str(cell)[:15] for cell in padded_row)}")
        else:
            print("❌ No data found in Live Dashboard")
        print()
    except Exception as e:
        print(f"❌ Error reading Live Dashboard: {e}")
        print()
    
    # Read Chart Data
    print("=" * 70)
    print("📈 CHART DATA")
    print("=" * 70)
    print()
    
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='Chart Data!A1:J10'
        ).execute()
        
        values = result.get('values', [])
        if values:
            print(f"First 10 rows of Chart Data:")
            print()
            for i, row in enumerate(values):
                padded_row = row + [''] * (10 - len(row))
                print(f"Row {i+1}: {' | '.join(str(cell)[:15] for cell in padded_row)}")
        else:
            print("❌ No data found in Chart Data")
        print()
    except Exception as e:
        print(f"❌ Error reading Chart Data: {e}")
        print()
    
    # Read Audit Log (last 10 entries)
    print("=" * 70)
    print("📝 AUDIT LOG (LAST 10 ENTRIES)")
    print("=" * 70)
    print()
    
    try:
        # First get the full range to find last row
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='Audit_Log!A:E'
        ).execute()
        
        values = result.get('values', [])
        if values:
            print(f"Total audit entries: {len(values)}")
            print()
            print("Most recent 10 entries:")
            print()
            # Show last 10 rows (or all if less than 10)
            recent = values[-10:] if len(values) > 10 else values
            for i, row in enumerate(recent):
                padded_row = row + [''] * (5 - len(row))
                print(f"{' | '.join(str(cell)[:20] for cell in padded_row)}")
        else:
            print("❌ No audit log entries")
        print()
    except Exception as e:
        print(f"❌ Error reading Audit Log: {e}")
        print()
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print()
    print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
    print()

if __name__ == "__main__":
    main()
