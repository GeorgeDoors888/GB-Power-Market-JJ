#!/usr/bin/env python3
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from googleapiclient.discovery import build
from google.oauth2 import service_account

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

print('Checking Live_Raw_Interconnectors tab (SOURCE DATA):')
print('='*80)

result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Interconnectors!A1:D12'
).execute()
vals = result.get('values', [])

for i, row in enumerate(vals):
    print(f'Row {i}: {row}')
    if i > 0 and len(row) > 0:
        # Check if flags are actually there
        cell_bytes = row[0].encode('utf-8')
        print(f'  Bytes: {cell_bytes[:50]}')
        has_flag = any(ord(c) > 127 for c in row[0][:10])
        print(f'  Has non-ASCII: {has_flag}')
