#!/usr/bin/env python3
"""
Create Chart: Latest Day Settlement Period Analysis
From Sheet1 A18:H31 - Demand, Wind, Expected Wind, and SSP
"""

from googleapiclient.discovery import build
import pickle
from datetime import datetime

print("=" * 80)
print("📊 SETTLEMENT PERIOD CHART CREATOR")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Sheet1'
DATA_RANGE = 'Sheet1!A18:H31'

# Load credentials
print("🔑 Loading credentials...")
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

if creds.expired and creds.refresh_token:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
    with open('token.pickle', 'wb') as f:
        pickle.dump(creds, f)

service = build('sheets', 'v4', credentials=creds)
print("✅ Connected to Google Sheets API")
print()

# First, get the sheet ID
print("📖 Getting sheet information...")
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id = None
for sheet in spreadsheet.get('sheets', []):
    if sheet['properties']['title'] == SHEET_NAME:
        sheet_id = sheet['properties']['sheetId']
        break

if sheet_id is None:
    print(f"❌ Sheet '{SHEET_NAME}' not found")
    exit(1)

print(f"✅ Found sheet: {SHEET_NAME} (ID: {sheet_id})")

# Read the data to understand structure
print(f"📊 Reading data from {DATA_RANGE}...")
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=DATA_RANGE
).execute()

values = result.get('values', [])
print(f"✅ Read {len(values)} rows")
print()

# Display structure
if values:
    print("📋 Data Structure:")
    print(f"   Headers (Row 18): {values[0] if len(values) > 0 else 'N/A'}")
    print(f"   Sample Data (Row 19): {values[1] if len(values) > 1 else 'N/A'}")
    print()

# Assuming structure based on your description:
# Column A: Settlement Period (00:00, 00:30, etc.)
# Column B-H: Various data including Demand (GW), Wind Generation (GW), Expected Wind (GW), SSP (£)
# We need to identify which columns contain what

print("=" * 80)
print("🎨 Creating Chart")
print("=" * 80)

# Chart configuration
# Rows 18-31 = indices 17-30 (0-indexed)
# We'll create a combo chart with:
# - Left axis: GW values (Demand, Wind, Expected Wind)
# - Right axis: £ values (SSP)

chart_request = {
    "requests": [{
        "addChart": {
            "chart": {
                "spec": {
                    "title": f"Latest Day Settlement Period Analysis - {datetime.now().strftime('%d %b %Y')}",
                    "subtitle": "Demand, Wind Generation, Expected Wind (GW) & System Sell Price (£/MWh)",
                    "basicChart": {
                        "chartType": "COMBO",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {
                                "position": "BOTTOM_AXIS",
                                "title": "Settlement Period (Time)"
                            },
                            {
                                "position": "LEFT_AXIS",
                                "title": "Generation / Demand (GW)"
                            },
                            {
                                "position": "RIGHT_AXIS",
                                "title": "System Sell Price (£/MWh)"
                            }
                        ],
                        "domains": [{
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 18,  # Row 19 (first data row, skip header)
                                        "endRowIndex": 31,    # Row 31 (last data row)
                                        "startColumnIndex": 0,  # Column A (Settlement Period)
                                        "endColumnIndex": 1
                                    }]
                                }
                            }
                        }],
                        "series": [
                            # Series 1: Demand Generation (GW) - assuming Column B
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheet_id,
                                            "startRowIndex": 18,
                                            "endRowIndex": 31,
                                            "startColumnIndex": 1,  # Column B
                                            "endColumnIndex": 2
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE"
                            },
                            # Series 2: Wind Generation (GW) - assuming Column C
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheet_id,
                                            "startRowIndex": 18,
                                            "endRowIndex": 31,
                                            "startColumnIndex": 2,  # Column C
                                            "endColumnIndex": 3
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE"
                            },
                            # Series 3: Expected Wind Generation (GW) - assuming Column D
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheet_id,
                                            "startRowIndex": 18,
                                            "endRowIndex": 31,
                                            "startColumnIndex": 3,  # Column D
                                            "endColumnIndex": 4
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE",
                                "lineStyle": {
                                    "type": "DASHED"
                                }
                            },
                            # Series 4: System Sell Price (£/MWh) - need to find which column
                            # Assuming Column E, F, G, or H - let's try Column E first
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheet_id,
                                            "startRowIndex": 18,
                                            "endRowIndex": 31,
                                            "startColumnIndex": 4,  # Column E
                                            "endColumnIndex": 5
                                        }]
                                    }
                                },
                                "targetAxis": "RIGHT_AXIS",
                                "type": "COLUMN",
                                "color": {
                                    "red": 1.0,
                                    "green": 0.6,
                                    "blue": 0.0
                                }
                            }
                        ],
                        "headerCount": 1
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sheet_id,
                            "rowIndex": 1,
                            "columnIndex": 10  # Column K
                        },
                        "widthPixels": 800,
                        "heightPixels": 500
                    }
                }
            }
        }
    }]
}

# Create the chart
try:
    print("📈 Creating combo chart...")
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=chart_request
    ).execute()
    
    print("✅ Chart created successfully!")
    print()
    print("=" * 80)
    print("📊 CHART DETAILS")
    print("=" * 80)
    print(f"📍 Location: Sheet1, Row 2, Column K")
    print(f"📏 Size: 800×500 pixels")
    print(f"📅 Data Range: A18:H31 (rows 19-31)")
    print()
    print("📈 Series Created:")
    print("   1. Demand Generation (GW) - Line chart, Left axis")
    print("   2. Wind Generation (GW) - Line chart, Left axis")
    print("   3. Expected Wind Generation (GW) - Dashed line, Left axis")
    print("   4. System Sell Price (£/MWh) - Column chart, Right axis")
    print()
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print()
    print("💡 Notes:")
    print("   • Chart shows latest day data starting from midnight (00:00)")
    print("   • Settlement periods shown on X-axis")
    print("   • Left Y-axis: GW values")
    print("   • Right Y-axis: £/MWh prices")
    print("   • If columns don't match, adjust startColumnIndex in script")
    print()
    
except Exception as e:
    print(f"❌ Error creating chart: {e}")
    print()
    print("🔧 Troubleshooting:")
    print("   1. Check that columns B-E contain the expected data")
    print("   2. Verify data is numeric (not text)")
    print("   3. Ensure headers are in row 18")
    print("   4. Data should be in rows 19-31")
    print()
    print("📋 Expected column structure:")
    print("   A: Settlement Period (00:00, 00:30, etc.)")
    print("   B: Demand Generation (GW)")
    print("   C: Wind Generation (GW)")
    print("   D: Expected Wind Generation (GW)")
    print("   E: System Sell Price (£/MWh)")
    print()
    print("If your columns are different, edit the script and adjust:")
    print("   startColumnIndex values in the chart_request")
    import traceback
    traceback.print_exc()

print("=" * 80)
print("✅ COMPLETE")
print("=" * 80)
