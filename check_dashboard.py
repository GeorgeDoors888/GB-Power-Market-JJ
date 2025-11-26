#!/usr/bin/env python3
"""Check current Dashboard structure"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

sheet_id = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
sh = gc.open_by_key(sheet_id)
dashboard = sh.worksheet('Dashboard')

print('Current Dashboard structure:')
data = dashboard.get('A1:H100')
for i, row in enumerate(data[:30], 1):
    if row:
        print(f'Row {i}: {row}')
