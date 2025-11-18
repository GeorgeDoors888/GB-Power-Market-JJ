#!/usr/bin/env python3
"""
Verify Dashboard layout after fix
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

# Read Dashboard rows 7-17
result = sheets.values().get(spreadsheetId=SHEET_ID, range='Dashboard!A7:E17').execute()
vals = result.get('values', [])

print('✅ DASHBOARD STRUCTURE (Rows 7-17):')
print('=' * 100)
print(f"{'Row':<5} | {'Fuel Breakdown (Col A)':<35} | {'(Col B)':<15} | {'Interconnectors (Col D)':<35} | {'(Col E)':<20}")
print('=' * 100)

for i, row in enumerate(vals, start=7):
    cols = row + [''] * (5 - len(row))
    print(f"{i:<5} | {cols[0]:<35} | {cols[1]:<15} | {cols[3]:<35} | {cols[4]:<20}")

print('=' * 100)
print('\n✅ VERIFICATION:')
print('1. Fuel section should show: WIND, CCGT, BIOMASS, NUCLEAR, NPSHYD, OTHER, OCGT')
print('2. Interconnectors should show country flags: 🇫🇷 🇮🇪 🇳🇱 🇧🇪 🇳🇴 🇩🇰')
print('3. NO "INT*" entries in fuel section (INTFR, INTNSL, etc. should be GONE)')
print('4. NO negative values in fuel section')
