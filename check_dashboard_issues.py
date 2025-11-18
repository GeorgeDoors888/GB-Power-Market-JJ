#!/usr/bin/env python3
"""Check Dashboard for interconnector and unavailability issues"""

from googleapiclient.discovery import build
from google.oauth2 import service_account

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

print('=' * 80)
print('📊 DASHBOARD ISSUES CHECK')
print('=' * 80)

# Read multiple ranges
ranges = [
    'Dashboard!A1:E17',  # Header through fuel/IC section
    'Dashboard!D7:E17',  # Interconnector columns
    'Live_Raw_Interconnectors!A1:D12',  # IC data source
    'Unavailability!A1:G10',  # Unavailability data
    'Dashboard!A18:G30'  # Settlement period section
]

result = service.spreadsheets().values().batchGet(
    spreadsheetId=SHEET_ID,
    ranges=ranges
).execute()

ranges_data = result.get('valueRanges', [])

print('\n🔥 FUEL & INTERCONNECTOR SECTION (Rows 1-17):')
for i, row in enumerate(ranges_data[0].get('values', []), 1):
    print(f'Row {i:2d}: {row}')

print('\n🌍 INTERCONNECTOR COLUMNS D-E (Rows 7-17):')
ic_cols = ranges_data[1].get('values', [])
print(f"Found {len(ic_cols)} rows in D7:E17")
for i, row in enumerate(ic_cols, 7):
    print(f'Row {i:2d}: {row}')

print('\n📡 LIVE_RAW_INTERCONNECTORS TAB:')
ic_data = ranges_data[2].get('values', [])
print(f"Found {len(ic_data)} rows")
for i, row in enumerate(ic_data):
    if i == 0:
        print(f'Header: {row}')
    else:
        print(f'IC {i}: {row}')

print('\n⚠️  UNAVAILABILITY TAB:')
unavail_data = ranges_data[3].get('values', [])
print(f"Found {len(unavail_data)} rows")
for i, row in enumerate(unavail_data):
    print(f'Row {i}: {row}')

print('\n📈 SETTLEMENT PERIOD SECTION (Rows 18-30):')
sp_data = ranges_data[4].get('values', [])
for i, row in enumerate(sp_data, 18):
    print(f'Row {i:2d}: {row}')

print('\n' + '=' * 80)
print('🔍 ISSUES IDENTIFIED:')
print('=' * 80)

issues = []

# Check interconnector display
if not ic_cols or len(ic_cols) == 0:
    issues.append("❌ No interconnector data in Dashboard columns D-E")
elif all(not row or len(row) < 2 for row in ic_cols):
    issues.append("❌ Interconnector columns D-E are empty")
else:
    # Check if showing numbers instead of names
    has_names = False
    for row in ic_cols:
        if len(row) >= 1 and any(flag in str(row[0]) for flag in ['🇫🇷', '🇧🇪', '🇩🇰', '🇮🇪', '🇳🇱', '🇳🇴']):
            has_names = True
            break
    if not has_names:
        issues.append("⚠️  Interconnectors showing numbers/MW instead of country names with flags")

# Check unavailability data
if len(unavail_data) <= 1:
    issues.append("❌ Unavailability tab has no data (only header or empty)")
else:
    # Check if showing duplicate/incorrect data
    unique_rows = set()
    for row in unavail_data[1:]:  # Skip header
        if len(row) >= 4:
            unique_rows.add(tuple(row[:4]))
    
    if len(unique_rows) == 1 and len(unavail_data) > 2:
        issues.append(f"⚠️  Unavailability showing {len(unavail_data)-1} duplicate rows (same data repeated)")

if issues:
    for issue in issues:
        print(issue)
else:
    print("✅ No major issues found")
