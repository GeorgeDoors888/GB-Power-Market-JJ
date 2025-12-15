#!/usr/bin/env python3
"""
Test Google Sheets API and BESS_VLP sheet access
"""

import gspread
from google.oauth2.service_account import Credentials

# Test Google Sheets API access
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

# Try to access the spreadsheet
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

print('✅ Google Sheets API: Connected')
print(f'   Spreadsheet: {spreadsheet.title}')

# Check if BESS_VLP sheet exists
try:
    sheet = spreadsheet.worksheet('BESS_VLP')
    print(f'✅ BESS_VLP sheet found (ID: {sheet.id})')
    
    # Check what's in B4
    b4_value = sheet.acell('B4').value
    print(f'   Cell B4 contains: "{b4_value}"')
    
    # Check structure
    a1 = sheet.acell('A1').value
    print(f'   Cell A1 (title): "{a1}"')
    
    # Check row 10 (results area)
    row10 = sheet.row_values(10)
    if row10:
        print(f'   Row 10 has {len(row10)} values: {row10[:3]}...')
    else:
        print('   Row 10 is empty (expected - awaiting lookup)')
    
    # Check reference table
    row20 = sheet.row_values(20)
    if row20:
        print(f'✅ Reference table populated: {len(row20)} columns')
        print(f'   First DNO: MPAN {row20[0]}, {row20[1]}')
    
except Exception as e:
    print(f'❌ BESS_VLP sheet error: {e}')
    import traceback
    traceback.print_exc()

print('\n📋 All sheets in spreadsheet:')
for ws in spreadsheet.worksheets():
    print(f'   - {ws.title} (ID: {ws.id})')
