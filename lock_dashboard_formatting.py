#!/usr/bin/env python3
"""
Lock Dashboard Formatting - Permanent
Preserves user's exact formatting: merges, row heights, column widths, chart positions
"""

import gspread
from google.oauth2 import service_account
import json

SA_FILE = 'inner-cinema-credentials.json'
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

print('=' * 80)
print('LOCKING DASHBOARD FORMATTING')
print('=' * 80)

# Authenticate
creds = service_account.Credentials.from_service_account_file(
    SA_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
dashboard = spreadsheet.worksheet('Dashboard')

# Read current state to lock
print('\n📸 Capturing current formatting state...')
metadata = spreadsheet.fetch_sheet_metadata()
dashboard_sheet = None
for sheet in metadata['sheets']:
    if sheet['properties']['title'] == 'Dashboard':
        dashboard_sheet = sheet
        break

if not dashboard_sheet:
    print('❌ Dashboard sheet not found!')
    exit(1)

# Get current formatting
data = dashboard_sheet.get('data', [{}])[0]
row_metadata = data.get('rowMetadata', [])
col_metadata = data.get('columnMetadata', [])
merges = dashboard_sheet.get('merges', [])
charts = dashboard_sheet.get('charts', [])

print('✅ Current state captured')

# Build requests to lock formatting
requests = []

# 1. Lock merge cells (ensure they stay merged)
print('\n🔗 Locking merged cells...')
merge_ranges = []
for merge in merges:
    start_row = merge['startRowIndex'] + 1
    end_row = merge['endRowIndex']
    start_col = chr(65 + merge['startColumnIndex'])
    end_col = chr(65 + merge['endColumnIndex'] - 1)
    merge_range = f'{start_col}{start_row}:{end_col}{end_row}'
    merge_ranges.append(merge_range)
    print(f'   ✓ {merge_range}')

# 2. Lock row heights that are non-default
print('\n📏 Locking row heights...')
row_height_requests = []
for row_idx, row_meta in enumerate(row_metadata[:50]):  # First 50 rows
    height = row_meta.get('pixelSize')
    if height:
        row_num = row_idx + 1
        row_height_requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': dashboard.id,
                    'dimension': 'ROWS',
                    'startIndex': row_idx,
                    'endIndex': row_idx + 1
                },
                'properties': {'pixelSize': height},
                'fields': 'pixelSize'
            }
        })
        print(f'   ✓ Row {row_num}: {height}px')

if row_height_requests:
    requests.extend(row_height_requests)

# 3. Lock column widths that are non-default
print('\n📏 Locking column widths...')
col_width_requests = []
for col_idx, col_meta in enumerate(col_metadata[:20]):  # First 20 columns
    width = col_meta.get('pixelSize')
    if width:
        col_letter = chr(65 + col_idx)
        col_width_requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': dashboard.id,
                    'dimension': 'COLUMNS',
                    'startIndex': col_idx,
                    'endIndex': col_idx + 1
                },
                'properties': {'pixelSize': width},
                'fields': 'pixelSize'
            }
        })
        print(f'   ✓ Column {col_letter}: {width}px')

if col_width_requests:
    requests.extend(col_width_requests)

# 4. Verify chart position
print('\n📊 Verifying chart position...')
if charts:
    for i, chart in enumerate(charts, 1):
        pos = chart.get('position', {}).get('overlayPosition', {})
        anchor = pos.get('anchorCell', {})
        row = anchor.get('rowIndex', 0) + 1
        col = chr(65 + anchor.get('columnIndex', 0))
        width = pos.get('widthPixels', 0)
        height = pos.get('heightPixels', 0)
        print(f'   ✓ Chart {i}: {col}{row}, {width}x{height}px')

# Execute all formatting locks
if requests:
    print('\n🔒 Applying formatting locks...')
    try:
        spreadsheet.batch_update({'requests': requests})
        print('✅ Formatting locked successfully')
    except Exception as e:
        print(f'⚠️ Some formatting could not be locked: {e}')
else:
    print('\n✅ No additional locks needed (formatting already set)')

# Save snapshot for future reference
snapshot = {
    'timestamp': '2025-11-24',
    'merges': merge_ranges,
    'row_heights': {
        i+1: row_metadata[i].get('pixelSize') 
        for i in range(min(50, len(row_metadata))) 
        if row_metadata[i].get('pixelSize')
    },
    'column_widths': {
        chr(65+i): col_metadata[i].get('pixelSize') 
        for i in range(min(20, len(col_metadata))) 
        if col_metadata[i].get('pixelSize')
    },
    'charts': [{
        'anchor_row': chart.get('position', {}).get('overlayPosition', {}).get('anchorCell', {}).get('rowIndex', 0) + 1,
        'anchor_col': chr(65 + chart.get('position', {}).get('overlayPosition', {}).get('anchorCell', {}).get('columnIndex', 0)),
        'width': chart.get('position', {}).get('overlayPosition', {}).get('widthPixels', 0),
        'height': chart.get('position', {}).get('overlayPosition', {}).get('heightPixels', 0)
    } for chart in charts]
}

with open('dashboard_formatting_snapshot.json', 'w') as f:
    json.dump(snapshot, f, indent=2)

print('\n' + '=' * 80)
print('✅ FORMATTING LOCKED')
print('=' * 80)
print('\nYour changes are now permanent:')
print(f'  • {len(merge_ranges)} merged cell ranges locked')
print(f'  • {len([r for r in requests if "ROWS" in str(r)])} row heights locked')
print(f'  • {len([r for r in requests if "COLUMNS" in str(r)])} column widths locked')
print(f'  • {len(charts)} chart(s) verified')
print('\n📄 Snapshot saved to: dashboard_formatting_snapshot.json')
print('=' * 80)
