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

# Read entire Dashboard
result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1:G100'
).execute()
vals = result.get('values', [])

print(f'Total rows in Dashboard: {len(vals)}')
print()
print('Last 20 rows (should show unavailability):')
print('-' * 80)

for i in range(max(0, len(vals)-20), len(vals)):
    row = vals[i]
    padded = row + [''] * (7 - len(row))
    print(f'Row {i+1:3d}: {padded}')
