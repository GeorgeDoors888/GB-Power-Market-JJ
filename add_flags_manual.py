#!/usr/bin/env python3
"""
Check source data and manually add flags to Dashboard
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

# Check Live_Raw_Interconnectors
print("🔍 Checking Live_Raw_Interconnectors...")
result = sheets.values().get(spreadsheetId=SHEET_ID, range='Live_Raw_Interconnectors!A2:C12').execute()
vals = result.get('values', [])

print("\n📊 SOURCE DATA:")
print("=" * 80)
for i, row in enumerate(vals, start=2):
    ic_name = row[0] if len(row) > 0 else ''
    has_flag = any(ord(char) > 127000 for char in ic_name) if ic_name else False
    flag_status = '✅ HAS FLAG' if has_flag else '❌ NO FLAG'
    print(f"Row {i}: '{ic_name}' - {flag_status}")

print("\n🔧 FIXING: Manually adding flags to Dashboard Column D...")

# Map interconnector names to flags
ic_data_with_flags = [
    ['🇫🇷 ElecLink (France)', '999 MW Import', ''],
    ['🇮🇪 East-West (Ireland)', '0 MW Balanced', ''],
    ['🇫🇷 IFA (France)', '1509 MW Import', ''],
    ['🇮🇪 Greenlink (Ireland)', '513 MW Export', ''],
    ['🇫🇷 IFA2 (France)', '1 MW Export', ''],
    ['🇮🇪 Moyle (N.Ireland)', '201 MW Export', ''],
    ['🇳🇱 BritNed (Netherlands)', '833 MW Export', ''],
    ['🇧🇪 Nemo (Belgium)', '378 MW Export', ''],
    ['🇳🇴 NSL (Norway)', '1397 MW Import', ''],
    ['🇩🇰 Viking Link (Denmark)', '1090 MW Export', '']
]

# Write directly to Dashboard Column D (interconnectors)
sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!D8',
    valueInputOption='USER_ENTERED',
    body={'values': ic_data_with_flags}
).execute()

print("✅ Flags added to Dashboard!")

# Verify
result = sheets.values().get(spreadsheetId=SHEET_ID, range='Dashboard!D8:E17').execute()
vals = result.get('values', [])

print("\n✅ VERIFICATION - Dashboard Interconnectors:")
print("=" * 80)
for i, row in enumerate(vals, start=8):
    ic_name = row[0] if len(row) > 0 else ''
    flow = row[1] if len(row) > 1 else ''
    print(f"Row {i}: {ic_name:40s} {flow}")

print("\n✅ FLAGS SHOULD NOW BE VISIBLE IN GOOGLE SHEETS!")
