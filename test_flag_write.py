#!/usr/bin/env python3
"""Test writing flags directly to Dashboard"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from googleapiclient.discovery import build
from google.oauth2 import service_account

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

print('Testing flag writing...')

# Write a test row with flags
test_data = [
    ['🇫🇷 TEST France', '999 MW', 'Import']
]

print(f'Writing: {test_data}')

service.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!D7:F7',
    valueInputOption="USER_ENTERED",
    body={"values": test_data}
).execute()

print('Written. Now reading back...')

result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!D7:F7'
).execute()

readback = result.get('values', [])
print(f'Read back: {readback}')

if readback and len(readback) > 0:
    cell = readback[0][0]
    print(f'Cell D7 contains: "{cell}"')
    print(f'Cell bytes: {cell.encode("utf-8")}')
    has_flag = any(ord(c) > 127 for c in cell)
    print(f'Has non-ASCII chars: {has_flag}')
