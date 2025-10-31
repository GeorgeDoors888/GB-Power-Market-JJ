#!/usr/bin/env python3
"""
Add Chart to Sheet1 WITHOUT Modifying Existing Data
This script ONLY creates/updates the chart - it does not touch any cells
"""

from googleapiclient.discovery import build
import pickle

print("📊 Adding Chart to Sheet1 (Preserving All Existing Data)")
print("=" * 70)

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

# Load credentials
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
service = build('sheets', 'v4', credentials=creds)

# Get sheet IDs
print("\n🔍 Finding sheets...")
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet1_id = None
data_sheet_id = None

sheets_found = spreadsheet.get('sheets', [])
print(f"   Found {len(sheets_found)} sheets in spreadsheet")

for sheet in sheets_found:
    title = sheet['properties']['title']
    sid = sheet['properties']['sheetId']
    print(f"   - {title} (ID: {sid})")
    if title == 'Sheet1':
        sheet1_id = sid
        print(f"      ✅ Matched Sheet1! sheet1_id = {sheet1_id}")
    elif title == 'Latest Day Data':
        data_sheet_id = sid
        print(f"      ✅ Matched Latest Day Data! data_sheet_id = {data_sheet_id}")

print(f"\nAfter loop: sheet1_id = {sheet1_id}, data_sheet_id = {data_sheet_id}")

if sheet1_id is None:  # Proper None check
    print("❌ Error: Could not find Sheet1")
    exit(1)

if data_sheet_id is None:  # Proper None check
    print("❌ Error: Could not find 'Latest Day Data' sheet")
    print("   Please run: python create_latest_day_chart.py first")
    exit(1)

print(f"✅ Sheet1 ID: {sheet1_id}")
print(f"✅ Latest Day Data sheet ID: {data_sheet_id}")

# Get data sheet row count
data_result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='Latest Day Data!A:A'
).execute()
data_rows = len(data_result.get('values', []))
print(f"✅ Data rows: {data_rows}")

# Delete existing charts in Sheet1
print("\n🗑️  Removing old charts from Sheet1...")
try:
    delete_requests = []
    for sheet in spreadsheet.get('sheets', []):
        if sheet['properties']['title'] == 'Sheet1':
            for chart in sheet.get('charts', []):
                delete_requests.append({
                    'deleteEmbeddedObject': {
                        'objectId': chart['chartId']
                    }
                })
    
    if delete_requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': delete_requests}
        ).execute()
        print(f"   ✅ Deleted {len(delete_requests)} old chart(s)")
    else:
        print("   ℹ️  No existing charts to delete")
except Exception as e:
    print(f"   ⚠️  Could not delete old charts: {e}")

# Create new chart at Row 18
print("\n📈 Creating new chart...")

chart_request = {
    'addChart': {
        'chart': {
            'spec': {
                'title': 'Latest Day Settlement Periods',
                'basicChart': {
                    'chartType': 'COMBO',
                    'legendPosition': 'RIGHT_LEGEND',
                    'axis': [
                        {
                            'position': 'BOTTOM_AXIS',
                            'title': 'Time'
                        },
                        {
                            'position': 'LEFT_AXIS',
                            'title': 'MW / £/MWh'
                        }
                    ],
                    'series': [
                        # Demand (MW) - Blue line
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': data_rows,
                                        'startColumnIndex': 2,  # Column C
                                        'endColumnIndex': 3
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'LINE',
                            'lineStyle': {'width': 2},
                            'color': {'red': 0.2, 'green': 0.5, 'blue': 0.9}
                        },
                        # Wind (MW) - Green line
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': data_rows,
                                        'startColumnIndex': 3,  # Column D
                                        'endColumnIndex': 4
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'LINE',
                            'lineStyle': {'width': 2},
                            'color': {'red': 0.1, 'green': 0.7, 'blue': 0.3}
                        },
                        # Expected Wind (MW) - Gray thin line
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': data_rows,
                                        'startColumnIndex': 4,  # Column E
                                        'endColumnIndex': 5
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'LINE',
                            'lineStyle': {'width': 1},
                            'color': {'red': 0.7, 'green': 0.7, 'blue': 0.7}
                        },
                        # System Sell Price (£/MWh) - Orange columns
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': data_rows,
                                        'startColumnIndex': 5,  # Column F
                                        'endColumnIndex': 6
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'COLUMN',
                            'color': {'red': 1.0, 'green': 0.6, 'blue': 0.0}
                        }
                    ],
                    'headerCount': 1,
                    'domains': [{
                        'domain': {
                            'sourceRange': {
                                'sources': [{
                                    'sheetId': data_sheet_id,
                                    'startRowIndex': 1,
                                    'endRowIndex': data_rows,
                                    'startColumnIndex': 1,  # Column B (Time)
                                    'endColumnIndex': 2
                                }]
                            }
                        }
                    }]
                }
            },
            'position': {
                'overlayPosition': {
                    'anchorCell': {
                        'sheetId': sheet1_id,
                        'rowIndex': 17,  # Row 18 (0-indexed = 17)
                        'columnIndex': 0  # Column A
                    },
                    'offsetXPixels': 0,
                    'offsetYPixels': 0,
                    'widthPixels': 800,
                    'heightPixels': 400
                }
            }
        }
    }
}

try:
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [chart_request]}
    ).execute()
    print("   ✅ Chart created successfully at Row 18!")
except Exception as e:
    print(f"   ❌ Error creating chart: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ COMPLETE")
print("=" * 70)
print(f"\n📊 Chart added to Sheet1 at Row 18")
print(f"📍 All existing data preserved")
print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=0")
print("\n💡 The chart overlays on top of existing content")
print("   You can move it by dragging in the spreadsheet")
