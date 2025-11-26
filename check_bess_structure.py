#!/usr/bin/env python3
"""
Check BESS sheet structure for dropdown implementation
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

sheet_id = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
sh = gc.open_by_key(sheet_id)
bess_sheet = sh.worksheet('BESS')

# Get current data
print('Current BESS sheet structure:')
print('A6 (Postcode):', bess_sheet.acell('A6').value)
print('B6 (MPAN):', bess_sheet.acell('B6').value)
print('A10 (Voltage):', bess_sheet.acell('A10').value)

# Get range of data to understand layout
data = bess_sheet.get('A1:H20')
print('\nFirst 20 rows:')
for i, row in enumerate(data, 1):
    if row:  # Skip empty rows
        print(f"Row {i}: {row}")
