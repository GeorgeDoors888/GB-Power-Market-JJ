#!/usr/bin/env python3
"""
Apply Test layout changes to Live Dashboard v2
Uses batchUpdate with minimal response data for maximum speed
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

print('🔄 Applying Test Layout → Live Dashboard v2\n')

# Step 1: Fast fetch with fields mask (only dimensions + merges)
print('📥 Fetching layouts...')
start = time.time()

response = service.spreadsheets().get(
    spreadsheetId=SPREADSHEET_ID,
    ranges=['Test', 'Live Dashboard v2'],
    includeGridData=True,
    fields='sheets(data(columnMetadata/pixelSize,rowMetadata/pixelSize),merges,properties(sheetId,title))'
).execute()

fetch_time = time.time() - start
print(f'✅ Fetched in {fetch_time:.2f}s\n')

# Parse sheets
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

# Build batch update requests
requests = []

# Column width changes
for col_idx in range(max(max(test_cols.keys()), max(live_cols.keys())) + 1):
    test_w = test_cols.get(col_idx, 100)
    live_w = live_cols.get(col_idx, 100)
    if test_w != live_w:
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': LIVE_SHEET_ID,
                    'dimension': 'COLUMNS',
                    'startIndex': col_idx,
                    'endIndex': col_idx + 1
                },
                'properties': {'pixelSize': test_w},
                'fields': 'pixelSize'
            }
        })

# Row height changes
for row_idx in range(max(max(test_rows.keys()), max(live_rows.keys())) + 1):
    test_h = test_rows.get(row_idx, 21)
    live_h = live_rows.get(row_idx, 21)
    if test_h != live_h:
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': LIVE_SHEET_ID,
                    'dimension': 'ROWS',
                    'startIndex': row_idx,
                    'endIndex': row_idx + 1
                },
                'properties': {'pixelSize': test_h},
                'fields': 'pixelSize'
            }
        })

# Merge changes
def merge_key(m):
    return f"{m.get('startRowIndex',0)},{m.get('endRowIndex',0)},{m.get('startColumnIndex',0)},{m.get('endColumnIndex',0)}"

test_merge_set = {merge_key(m): m for m in test_merges}
live_merge_set = {merge_key(m): m for m in live_merges}

# Remove merges that exist in Live but not in Test
for key, m in live_merge_set.items():
    if key not in test_merge_set:
        requests.append({
            'unmergeCells': {
                'range': {
                    'sheetId': LIVE_SHEET_ID,
                    'startRowIndex': m.get('startRowIndex', 0),
                    'endRowIndex': m.get('endRowIndex', 0),
                    'startColumnIndex': m.get('startColumnIndex', 0),
                    'endColumnIndex': m.get('endColumnIndex', 0)
                }
            }
        })

# Add merges that exist in Test but not in Live
for key, m in test_merge_set.items():
    if key not in live_merge_set:
        requests.append({
            'mergeCells': {
                'range': {
                    'sheetId': LIVE_SHEET_ID,
                    'startRowIndex': m.get('startRowIndex', 0),
                    'endRowIndex': m.get('endRowIndex', 0),
                    'startColumnIndex': m.get('startColumnIndex', 0),
                    'endColumnIndex': m.get('endColumnIndex', 0)
                },
                'mergeType': 'MERGE_ALL'
            }
        })

if not requests:
    print('✅ No changes needed - Test and Live are identical')
    exit(0)

print(f'📝 Prepared {len(requests)} update requests')
print(f'   • Column changes: {sum(1 for r in requests if "updateDimensionProperties" in r and r["updateDimensionProperties"]["range"]["dimension"] == "COLUMNS")}')
print(f'   • Row changes: {sum(1 for r in requests if "updateDimensionProperties" in r and r["updateDimensionProperties"]["range"]["dimension"] == "ROWS")}')
print(f'   • Merges added: {sum(1 for r in requests if "mergeCells" in r)}')
print(f'   • Merges removed: {sum(1 for r in requests if "unmergeCells" in r)}')

# Step 2: Apply with batchUpdate (minimal response)
print(f'\n🚀 Applying changes to Live Dashboard v2...')
start = time.time()

body = {
    'requests': requests,
    'includeSpreadsheetInResponse': False,  # KEY: Don't echo full spreadsheet back
    'responseRanges': [],  # KEY: Don't return any data
    'responseIncludeGridData': False  # KEY: No grid data in response
}

result = service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body=body
).execute()

apply_time = time.time() - start
print(f'✅ Applied in {apply_time:.2f}s\n')

print('='*80)
print('✅ SUCCESS: Live Dashboard v2 updated')
print('='*80)
print(f'   Total time: {fetch_time + apply_time:.2f}s')
print(f'   • Fetch: {fetch_time:.2f}s')
print(f'   • Apply: {apply_time:.2f}s')
print(f'   • Changes: {len(requests)}')
print(f'\n🔗 https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={LIVE_SHEET_ID}')
