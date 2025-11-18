#!/usr/bin/env python3
"""Diagnose Dashboard interconnector and unavailability display issues"""

from googleapiclient.discovery import build
from google.oauth2 import service_account

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

print('=' * 80)
print('📊 DASHBOARD DIAGNOSIS')
print('=' * 80)

# First, list all sheets
sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
sheets = sheet_metadata.get('sheets', [])

print('\n📋 AVAILABLE SHEETS:')
for sheet in sheets:
    title = sheet['properties']['title']
    print(f"  - {title}")

# Read multiple ranges (without Unavailability tab)
ranges = [
    'Dashboard!A1:E20',  # Header through fuel/IC section + SP header
    'Live_Raw_Interconnectors!A1:D12',  # IC data source
    'Dashboard!D20:G30'  # Check unavailability columns in SP section
]

result = service.spreadsheets().values().batchGet(
    spreadsheetId=SHEET_ID,
    ranges=ranges
).execute()

ranges_data = result.get('valueRanges', [])

print('\n🔥 DASHBOARD HEADER & FUEL/IC SECTION (A1:E20):')
dashboard_vals = ranges_data[0].get('values', [])
for i, row in enumerate(dashboard_vals, 1):
    # Pad row to show empty columns
    padded_row = row + [''] * (5 - len(row))
    print(f'Row {i:2d}: A="{padded_row[0]}" | B="{padded_row[1]}" | C="{padded_row[2]}" | D="{padded_row[3]}" | E="{padded_row[4]}"')

print('\n📡 LIVE_RAW_INTERCONNECTORS TAB:')
ic_data = ranges_data[1].get('values', [])
print(f"Total rows: {len(ic_data)}")
for i, row in enumerate(ic_data):
    if i == 0:
        print(f'Header: {row}')
    else:
        print(f'Row {i}: {row}')

print('\n⚠️  UNAVAILABILITY COLUMNS IN SP SECTION (D20:G30):')
unavail_cols = ranges_data[2].get('values', [])
print(f"Total rows: {len(unavail_cols)}")
for i, row in enumerate(unavail_cols, 20):
    print(f'Row {i:2d}: {row}')

print('\n' + '=' * 80)
print('🔍 ISSUE ANALYSIS:')
print('=' * 80)

# Check interconnector display in Dashboard
ic_found = False
for i, row in enumerate(dashboard_vals[6:17], 7):  # Rows 7-17
    if len(row) >= 4:  # Column D
        col_d = str(row[3]) if len(row) > 3 else ''
        col_e = str(row[4]) if len(row) > 4 else ''
        if any(flag in col_d for flag in ['🇫🇷', '🇧🇪', '🇩🇰', '🇮🇪', '🇳🇱', '🇳🇴']):
            ic_found = True
            print(f"✅ Row {i}: Found interconnector with flag: {col_d}")
            break

if not ic_found:
    print("❌ ISSUE: No interconnector names with flags found in Dashboard D7:D17")
    print("   Expected format: '🇫🇷 IFA (France)' with MW values")
    print("   Actual: Columns D-E appear to contain other data or are empty")

# Check if unavailability data is misplaced in SP section
unavail_in_sp = False
for row in unavail_cols:
    if len(row) >= 2:
        col_d = str(row[0]) if row else ''
        if 'Normal' in col_d or 'MW' in col_d:
            unavail_in_sp = True
            break

if unavail_in_sp:
    print("❌ ISSUE: Unavailability data is displaying in SP section (columns D-G)")
    print("   This should be in a separate section, not overlapping settlement periods")

print('\n💡 RECOMMENDED FIXES:')
print('   1. Run update_dashboard_display.py to refresh interconnector display')
print('   2. Check Live_Raw_Interconnectors has current data')
print('   3. Verify unavailability section layout in Dashboard')
