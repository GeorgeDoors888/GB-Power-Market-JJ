#!/usr/bin/env python3
"""Read Google Spreadsheet: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle
import os.path

# Load credentials
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

# Build service
sheets_service = build('sheets', 'v4', credentials=creds)

# Spreadsheet ID
spreadsheet_id = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

# Get spreadsheet metadata
spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

print(f"\n{'='*80}")
print(f"📊 Spreadsheet: {spreadsheet['properties']['title']}")
print(f"{'='*80}\n")

print(f"Sheets in this workbook:")
for sheet in spreadsheet['sheets']:
    props = sheet['properties']
    rows = props.get('gridProperties', {}).get('rowCount', '?')
    cols = props.get('gridProperties', {}).get('columnCount', '?')
    print(f"  - {props['title']} ({rows} rows × {cols} cols)")

# Read each sheet
for sheet in spreadsheet['sheets']:
    sheet_name = sheet['properties']['title']
    print(f"\n{'='*80}")
    print(f"📋 Sheet: {sheet_name}")
    print(f"{'='*80}\n")
    
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1:Z100"
    ).execute()
    
    values = result.get('values', [])
    
    if values:
        print(f"Total rows: {len(values)}")
        print(f"\nHeaders: {values[0]}")
        print(f"\nFirst 5 data rows:")
        for i, row in enumerate(values[1:6], 1):
            print(f"  Row {i}: {row}")
    else:
        print("(Empty sheet)")

print(f"\n{'='*80}")
print("✅ Done reading spreadsheet")
print(f"{'='*80}\n")
