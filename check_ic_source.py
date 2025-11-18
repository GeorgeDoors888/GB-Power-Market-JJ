#!/usr/bin/env python3
"""
Check source interconnector data and fix duplicate flags
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

# Check Live_Raw_Interconnectors
result = sheets.values().get(spreadsheetId=SHEET_ID, range='Live_Raw_Interconnectors!A1:C15').execute()
vals = result.get('values', [])

print('🔍 LIVE_RAW_INTERCONNECTORS DATA:')
print('=' * 100)
for i, row in enumerate(vals, start=1):
    print(f'Row {i}: {row}')

print('\n' + '=' * 100)

# Check what's in Dashboard now
dash_result = sheets.values().get(spreadsheetId=SHEET_ID, range='Dashboard!D8:E17').execute()
dash_vals = dash_result.get('values', [])

print('\n📊 CURRENT DASHBOARD INTERCONNECTORS (D8:E17):')
print('=' * 100)
for i, row in enumerate(dash_vals, start=8):
    print(f'Row {i}: {row}')
