#!/usr/bin/env python3
"""Check Battery Revenue Analysis sheet data"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_PATH = '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json'
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
client = gspread.authorize(credentials)

sheet = client.open_by_key(SPREADSHEET_ID)
worksheets = sheet.worksheets()

print('Available sheets:')
for ws in worksheets:
    print(f'  - {ws.title} (ID: {ws.id}, {ws.row_count} rows x {ws.col_count} cols)')

# Check Battery Revenue Analysis sheet
try:
    battery_sheet = sheet.worksheet('Battery Revenue Analysis')
    print(f'\n✅ Battery Revenue Analysis sheet found')
    print(f'   Row count: {battery_sheet.row_count}')
    print(f'   Col count: {battery_sheet.col_count}')
    
    # Read first 20 rows to check data
    data = battery_sheet.get_all_values()[:20]
    print(f'\n📊 First 20 rows of data:')
    for i, row in enumerate(data, 1):
        # Show full row if short, otherwise first 8 columns
        if len(row) <= 8:
            print(f'   Row {i}: {row}')
        else:
            print(f'   Row {i}: {row[:8]}...')
    
    # Check if there's recent data
    print(f'\n📅 Checking for recent dates...')
    for i, row in enumerate(data, 1):
        if row and len(row) > 0 and '2025' in str(row[0]):
            print(f'   Row {i}: Date found - {row[0]}')
            
except Exception as e:
    print(f'\n❌ Error reading Battery Revenue Analysis: {e}')
    import traceback
    traceback.print_exc()
