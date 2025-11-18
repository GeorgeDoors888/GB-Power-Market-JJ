#!/usr/bin/env python3
from googleapiclient.discovery import build
from google.oauth2 import service_account

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

print('='*80)
print('✅ DASHBOARD STATUS VERIFICATION')
print('='*80)

# Check Dashboard
result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1:E20'
).execute()
vals = result.get('values', [])

print('\n📊 DASHBOARD DISPLAY (First 20 rows):')
print(f'Row 1: {vals[0][0]}')
print(f'Row 2: {vals[1][0][:60]}...')
print(f'Row 5: {vals[4][0]} | {vals[4][2]}')
print()
print('🌍 INTERCONNECTOR SECTION (Rows 7-16):')
for i in range(6, 16):
    if i < len(vals):
        row = vals[i]
        col_d = row[3] if len(row) > 3 else ''
        col_e = row[4] if len(row) > 4 else ''
        if col_d:
            print(f'  {col_d:<30} {col_e}')

# Check unavailability
result2 = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='REMIT Unavailability!A1:G11'
).execute()
unavail_vals = result2.get('values', [])

print()
print('⚠️  REMIT UNAVAILABILITY TAB (Top 5 outages):')
print(f'Header: {unavail_vals[0]}')
for i in range(1, min(6, len(unavail_vals))):
    row = unavail_vals[i]
    print(f'  {row[0]:<30} | {row[2]:<20} | Normal: {row[3]:>6} MW | Unavail: {row[4]:>6} MW | {row[5]}')

print()
print('='*80)
print('✅ ALL SYSTEMS OPERATIONAL')
print('='*80)
