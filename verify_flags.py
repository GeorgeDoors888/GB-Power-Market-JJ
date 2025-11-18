#!/usr/bin/env python3
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

result = sheets.values().get(spreadsheetId=SHEET_ID, range='Dashboard!D8:E17').execute()
vals = result.get('values', [])

print('✅ INTERCONNECTOR FLAGS VERIFICATION:')
print('=' * 80)
for i, row in enumerate(vals, start=8):
    ic_name = row[0] if len(row) > 0 else ''
    flow = row[1] if len(row) > 1 else ''
    
    # Check if flag is complete
    flag_chars = [c for c in ic_name if ord(c) > 127000]
    flag_count = len(flag_chars)
    
    status = '✅ COMPLETE' if flag_count >= 2 else '❌ BROKEN'
    print(f'Row {i}: {status} - {ic_name:40s} {flow}')
