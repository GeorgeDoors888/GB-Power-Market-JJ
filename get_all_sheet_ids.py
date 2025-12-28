#!/usr/bin/env python3
"""
Get all sheet IDs for hardcoding (one-time lookup)
Run this ONCE, copy IDs to your scripts
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

print("🔍 Fetching all sheet IDs (this takes ~66s, but only once!)...\n")

creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
service = build('sheets', 'v4', credentials=creds)

# Fetch metadata with fields filter (faster)
meta = service.spreadsheets().get(
    spreadsheetId=SPREADSHEET_ID,
    fields='sheets.properties(sheetId,title,index)'
).execute()

print("✅ Sheet IDs found! Copy these to your Python scripts:\n")
print("="*60)
print("\n# Google Sheets - Sheet IDs (for fast API calls)")
print(f"SPREADSHEET_ID = '{SPREADSHEET_ID}'")

for sheet in sorted(meta['sheets'], key=lambda s: s['properties']['index']):
    title = sheet['properties']['title']
    sheet_id = sheet['properties']['sheetId']
    var_name = title.upper().replace(' ', '_').replace('-', '_')
    print(f"{var_name}_SHEET_ID = {sheet_id}  # {title}")

print("\n" + "="*60)
print("\n💡 Usage Example:")
print("""
from googleapiclient.discovery import build

# Hardcoded IDs (no API call needed!)
ANALYSIS_SHEET_ID = 225925794
DROPDOWNDATA_SHEET_ID = 486714144

# Use directly in batchUpdate
requests = [{
    'updateSheetProperties': {
        'properties': {
            'sheetId': ANALYSIS_SHEET_ID,
            'title': 'Analysis'
        },
        'fields': 'title'
    }
}]

service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()
""")

print("\n⚡ Speed Benefit:")
print("   Before: 66s per .get() call")
print("   After:  0s (no API call!)")
print("   Speedup: ∞ (infinite)!")
