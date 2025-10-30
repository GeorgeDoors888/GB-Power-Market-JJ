#!/usr/bin/env python3
"""Verify A2 and B2 cells"""
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('jibber_jabber_key.json', scopes=SCOPES)
gc = gspread.authorize(creds)

sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
worksheet = sheet.worksheet('Sheet1')

print('=' * 80)
print('VERIFYING A2 AND B2 CELLS')
print('=' * 80)
print()

print('A2 (Last Updated):')
a2_value = worksheet.acell('A2').value
print(f'  {a2_value}')
print()

print('B2 (System Description):')
b2_value = worksheet.acell('B2').value
print(f'  Length: {len(b2_value)} characters')
print(f'  First 200 chars: {b2_value[:200]}...')
print()

# Check if it contains expected text
if 'Automated Energy Intelligence Engine' in b2_value:
    print('✅ B2 contains expected description')
else:
    print('❌ B2 does not contain expected description')

if '29 October 2025' in a2_value or 'October 2025' in a2_value:
    print('✅ A2 contains expected date format')
else:
    print('❌ A2 does not contain expected date format')
