#!/usr/bin/env python3
"""Read ACTUAL Dashboard data from Google Sheets - no assumptions"""
from googleapiclient.discovery import build
from google.oauth2 import service_account
import sys
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

print('='*80)
print('READING ACTUAL DASHBOARD - WHAT USER SEES IN BROWSER')
print('='*80)

# Read Dashboard
result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1:G70'
).execute()
vals = result.get('values', [])

print(f'\nTotal rows: {len(vals)}\n')
print('ACTUAL DASHBOARD CONTENT (First 35 rows):')
print('-'*80)
for i, row in enumerate(vals[:35], 1):
    # Pad to 7 columns
    padded = row + [''] * (7 - len(row))
    print(f'Row {i:2d}: A={padded[0][:40]:<40} | D={padded[3][:30]:<30} | E={padded[4][:20]:<20}')

print('\n' + '='*80)
print('CHECKING SPECIFIC ISSUES:')
print('='*80)

# Check for flags
has_flags = False
flag_chars = ['🇫', '🇧', '🇩', '🇮', '🇳']
for i, row in enumerate(vals[6:17], 7):
    for cell in row:
        if any(flag in str(cell) for flag in flag_chars):
            has_flags = True
            print(f'✅ Found flag in row {i}: {cell[:50]}')
            break

if not has_flags:
    print('❌ NO FLAGS FOUND in rows 7-17 (interconnector section)')
    print('   Showing what IS there:')
    for i, row in enumerate(vals[6:17], 7):
        if len(row) > 3:
            print(f'   Row {i}: Column D = "{row[3]}"')

# Check unavailability in settlement periods
print('\n🔍 Checking Settlement Period section (rows 18-30):')
for i, row in enumerate(vals[17:30], 18):
    print(f'Row {i:2d}: {row}')

sys.stdout.flush()
