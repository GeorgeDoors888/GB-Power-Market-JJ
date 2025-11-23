#!/usr/bin/env python3
"""Quick script to check BESS sheet structure"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')

print('📊 GOOGLE SHEET: GB Energy Dashboard')
print('='*80)
print(f'Title: {sheet.title}')
print(f'Total Worksheets: {len(sheet.worksheets())}')
print()
print('📑 All Worksheets:')
print('='*80)

for i, ws in enumerate(sheet.worksheets(), 1):
    print(f'{i:2}. {ws.title:<50} ({ws.row_count} rows x {ws.col_count} cols)')

print()
print('='*80)
print('🔍 BESS Sheet - First 20 rows (A1:H20):')
print('='*80)

bess = sheet.worksheet('BESS')
values = bess.get('A1:H20')
for i, row in enumerate(values, 1):
    cells = [str(c)[:40] if c else '' for c in row]
    print(f'{i:2}. {" | ".join(cells)}')
