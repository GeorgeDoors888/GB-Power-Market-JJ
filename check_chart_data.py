#!/usr/bin/env python3
"""
Check and create ChartData sheet for dashboard charts
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Setup credentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)

# Open spreadsheet
spreadsheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')

# List all sheets
print('\n📋 Current sheets in your dashboard:')
print('=' * 60)
for sheet in spreadsheet.worksheets():
    print(f'  • {sheet.title} (ID: {sheet.id}, {sheet.row_count} rows)')

print('\n🔍 Checking for ChartData sheet...')

try:
    chart_data_sheet = spreadsheet.worksheet('ChartData')
    print('✅ ChartData sheet exists!')
    print(f'   Rows: {chart_data_sheet.row_count}')
    print(f'   Cols: {chart_data_sheet.col_count}')
    
    # Check if it has data
    data = chart_data_sheet.get_all_values()
    if len(data) > 1:
        print(f'   Data rows: {len(data) - 1}')
    else:
        print('   ⚠️  No data in ChartData sheet!')
        
except gspread.exceptions.WorksheetNotFound:
    print('❌ ChartData sheet NOT found!')
    print('\n🔧 Need to run enhance_dashboard_layout.py to create it')
