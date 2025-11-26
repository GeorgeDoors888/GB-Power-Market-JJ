#!/usr/bin/env python3
"""
Lock down Dashboard sheet - protect from manual edits
Only allow automated scripts to update
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')

print('🔒 LOCKING DOWN DASHBOARD SHEET')
print('=' * 80)

# Get the Dashboard sheet
dashboard = spreadsheet.worksheet('Dashboard')

print('\n📋 Current Dashboard structure:')
print('   Rows 1-6: Title, metrics, current KPIs')
print('   Rows 7-17: Fuel breakdown + Interconnectors')
print('   Rows 18-29: Chart area')
print('   Rows 30-54: Outages section')
print('   Rows 55+: Reserved/empty')

# Note: gspread doesn't have direct sheet protection API
# We need to use Google Sheets API v4 for protection
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds_api = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds_api)

# Get sheet ID
sheet_id = dashboard.id

print(f'\n🔍 Dashboard sheet ID: {sheet_id}')

# Create protection request
# This will protect the entire sheet with a warning (anyone can edit but gets warned)
requests = [{
    'addProtectedRange': {
        'protectedRange': {
            'range': {
                'sheetId': sheet_id
            },
            'description': 'Dashboard is auto-updated by scripts. Manual edits will be overwritten every 5-10 minutes.',
            'warningOnly': True  # Shows warning but allows edits
        }
    }
}]

body = {
    'requests': requests
}

print('\n🔒 Applying protection...')
response = service.spreadsheets().batchUpdate(
    spreadsheetId='12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8',
    body=body
).execute()

print('\n✅ DASHBOARD LOCKED!')
print('=' * 80)
print('\n📝 Protection Details:')
print('   Type: Warning-based (allows edits with confirmation)')
print('   Message: "Dashboard is auto-updated by scripts. Manual edits will be overwritten."')
print('   Scope: Entire Dashboard sheet')
print('\n⚠️  Users will see a warning when trying to edit')
print('   They can proceed but changes will be lost on next auto-update (5-10 min)')
print('\n🔓 To unlock: File → Data → Sheet and range protections → Remove')
