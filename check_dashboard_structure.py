#!/usr/bin/env python3
"""
Check current Dashboard structure to diagnose flag issue
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

# Read Dashboard rows 7-17 to see current structure
result = sheets.values().get(spreadsheetId=SHEET_ID, range='Dashboard!A7:F17').execute()
vals = result.get('values', [])

print('📊 CURRENT DASHBOARD STRUCTURE (Rows 7-17):')
print('=' * 100)
print(f"{'Row':<5} | {'Col A':<30} | {'Col B':<20} | {'Col C':<20} | {'Col D':<30} | {'Col E':<20}")
print('=' * 100)

for i, row in enumerate(vals, start=7):
    cols = row + [''] * (6 - len(row))  # Pad to 6 columns
    print(f"{i:<5} | {cols[0]:<30} | {cols[1]:<20} | {cols[2]:<20} | {cols[3]:<30} | {cols[4]:<20}")

print('\n' + '=' * 100)
print('\n🔍 ISSUE DIAGNOSIS:')
print("The flags are showing as '🇫 🇫' (broken) instead of '🇫🇷' (complete)")
print("This happens when the flag emoji is split across cells or has extra spaces")
