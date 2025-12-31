#!/usr/bin/env python3
"""
Fast layout comparison - only fetches column/row dimensions and merges
Avoids slow includeGridData by using specific field masks
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
import time

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
TEST_SHEET_ID = 1837760869
LIVE_SHEET_ID = 687718775

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = build('sheets', 'v4', credentials=creds)

print('🔍 Fast Layout Comparison\n')

# Fetch only dimensions and merges (no cell data)
# Use fields mask to get ONLY what we need - this is the key optimization
print('📥 Fetching Test and Live layouts (fields mask optimized)...')
start = time.time()

response = service.spreadsheets().get(
    spreadsheetId=SPREADSHEET_ID,
    ranges=['Test', 'Live Dashboard v2'],
    includeGridData=True,
    fields='sheets(data(columnMetadata/pixelSize,rowMetadata/pixelSize),merges,properties(sheetId,title))'
).execute()

elapsed = time.time() - start
print(f'✅ Loaded in {elapsed:.2f}s (avoiding full metadata serialization)\n')

# Parse Test and Live
test_sheet = None
live_sheet = None

for sheet in response['sheets']:
    sheet_id = sheet['properties']['sheetId']
    if sheet_id == TEST_SHEET_ID:
        test_sheet = sheet
    elif sheet_id == LIVE_SHEET_ID:
        live_sheet = sheet

if not test_sheet or not live_sheet:
    print('❌ Could not find Test or Live sheets')
    exit(1)

# Extract layouts
def extract_layout(sheet):
    data = sheet.get('data', [{}])[0]

    col_widths = {}
    for i, col in enumerate(data.get('columnMetadata', [])):
        col_widths[i] = col.get('pixelSize', 100)

    row_heights = {}
    for i, row in enumerate(data.get('rowMetadata', [])):
        row_heights[i] = row.get('pixelSize', 21)

    merges = sheet.get('merges', [])

    return col_widths, row_heights, merges

test_cols, test_rows, test_merges = extract_layout(test_sheet)
live_cols, live_rows, live_merges = extract_layout(live_sheet)

print('='*80)
print('📋 CHANGES: Test → Live Dashboard v2')
print('='*80)

# Column changes
col_changes = []
for col_idx in range(26):  # A-Z
    test_w = test_cols.get(col_idx, 100)
    live_w = live_cols.get(col_idx, 100)
    if test_w != live_w:
        col_letter = chr(65 + col_idx)
        col_changes.append((col_letter, col_idx, live_w, test_w))

# Row changes (only check first 100 rows for speed)
row_changes = []
for row_idx in range(100):
    test_h = test_rows.get(row_idx, 21)
    live_h = live_rows.get(row_idx, 21)
    if test_h != live_h:
        row_changes.append((row_idx + 1, live_h, test_h))

# Merge changes
def merge_key(m):
    return f"{m.get('startRowIndex',0)},{m.get('endRowIndex',0)},{m.get('startColumnIndex',0)},{m.get('endColumnIndex',0)}"

test_merge_set = {merge_key(m) for m in test_merges}
live_merge_set = {merge_key(m) for m in live_merges}

added = [m for m in test_merges if merge_key(m) not in live_merge_set]
removed = [m for m in live_merges if merge_key(m) not in test_merge_set]

# Display
print(f'\n🔢 COLUMN WIDTH CHANGES ({len(col_changes)}):')
for col_letter, col_idx, live_w, test_w in col_changes[:15]:
    if test_w == 0:
        print(f'  🔴 Column {col_letter}: HIDDEN (was {live_w}px)')
    elif live_w == 0:
        print(f'  🟢 Column {col_letter}: SHOWN {test_w}px (was hidden)')
    else:
        arrow = '→' if test_w > live_w else '←'
        print(f'  📏 Column {col_letter}: {live_w}px {arrow} {test_w}px')
if len(col_changes) > 15:
    print(f'  ... and {len(col_changes)-15} more')

print(f'\n📐 ROW HEIGHT CHANGES ({len(row_changes)}):')
for row_num, live_h, test_h in row_changes[:15]:
    if test_h == 0:
        print(f'  🔴 Row {row_num}: HIDDEN (was {live_h}px)')
    elif live_h == 0:
        print(f'  🟢 Row {row_num}: SHOWN {test_h}px (was hidden)')
    else:
        arrow = '↕' if abs(test_h - live_h) > 10 else '→'
        print(f'  📏 Row {row_num}: {live_h}px {arrow} {test_h}px')
if len(row_changes) > 15:
    print(f'  ... and {len(row_changes)-15} more')

print(f'\n🔗 CELL MERGE CHANGES:')
print(f'  ➕ Added in Test: {len(added)}')
for m in added[:10]:
    sr = m.get('startRowIndex', 0) + 1
    er = m.get('endRowIndex', 0)
    sc = chr(65 + m.get('startColumnIndex', 0))
    ec = chr(65 + m.get('endColumnIndex', 0) - 1)
    print(f'     • {sc}{sr}:{ec}{er}')
if len(added) > 10:
    print(f'     ... and {len(added)-10} more')

print(f'  ➖ Removed from Test: {len(removed)}')
for m in removed[:10]:
    sr = m.get('startRowIndex', 0) + 1
    er = m.get('endRowIndex', 0)
    sc = chr(65 + m.get('startColumnIndex', 0))
    ec = chr(65 + m.get('endColumnIndex', 0) - 1)
    print(f'     • {sc}{sr}:{ec}{er}')
if len(removed) > 10:
    print(f'     ... and {len(removed)-10} more')

total = len(col_changes) + len(row_changes) + len(added) + len(removed)
print(f'\n📊 TOTAL: {total} changes')
print('='*80)

if total > 0:
    print('\n💡 To apply these changes to Live Dashboard v2:')
    print('   python3 replicate_test_to_live.py --apply')
