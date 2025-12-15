#!/usr/bin/env python3
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SA_PATH = '../inner-cinema-credentials.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

vals = sheets.values().get(spreadsheetId=SHEET_ID, range='Live Dashboard!A1:Z60').execute().get('values', [])

print(f'Total rows read: {len(vals)}')
print(f'Header (first 6 cols): {vals[0][:6]}')
print()

# Check first 10 data rows
for i in range(1, min(11, len(vals))):
    row = vals[i]
    sp = row[0] if len(row) > 0 else 'EMPTY'
    gen = row[4] if len(row) > 4 else 'NO_GEN'
    print(f'Row {i+1} (index {i}): SP={sp}, Gen={gen}, row_len={len(row)}')
