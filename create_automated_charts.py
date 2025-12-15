#!/usr/bin/env python3
"""
Automated Chart Generator for GB Power Market Analysis
Creates charts automatically in Google Sheets from analysis data
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from datetime import datetime
import json

print("=" * 80)
print("📊 AUTOMATED CHART GENERATOR")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Analysis BI Enhanced'

# Load credentials (OAuth, not service account)
print("🔑 Loading credentials...")
try:
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    
    # Refresh if expired
    if creds.expired and creds.refresh_token:
        print("🔄 Token expired, refreshing...")
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        with open('token.pickle', 'wb') as f:
            pickle.dump(creds, f)
    
    print("✅ Credentials loaded")
except Exception as e:
    print(f"❌ Error loading credentials: {e}")
    exit(1)

# Build service
print("🔌 Connecting to Google Sheets API...")
try:
    service = build('sheets', 'v4', credentials=creds)
    print("✅ Connected")
except Exception as e:
    print(f"❌ Error connecting: {e}")
    exit(1)

print()
print("=" * 80)
print("📈 Creating Charts")
print("=" * 80)

# Get sheet ID
try:
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
except Exception as e:
    print(f"❌ Error finding sheet: {e}")
    exit(1)

print()

# Chart definitions
charts_to_create = [
    {
        "name": "Bid-Offer Spread Trend",
        "type": "LINE",
        "description": "Time series of bid-offer spreads",
        "data_range": {
            "dates": {"startRow": 10, "endRow": 100, "startCol": 0, "endCol": 1},  # Column A
            "values": {"startRow": 10, "endRow": 100, "startCol": 3, "endCol": 4}  # Column D (spread)
        },
        "axes": {
            "bottom": "Date",
            "left": "Spread (£/MWh)"
        }
    },
    {
        "name": "Generation Mix Distribution",
        "type": "PIE",
        "description": "Fuel type breakdown",
        "data_range": {
            "labels": {"startRow": 10, "endRow": 30, "startCol": 0, "endCol": 1},  # Fuel types
            "values": {"startRow": 10, "endRow": 30, "startCol": 1, "endCol": 2}   # Generation
        }
    },
    {
        "name": "Intraday Spread Pattern",
        "type": "COLUMN",
        "description": "Average spread by settlement period",
        "data_range": {
            "categories": {"startRow": 10, "endRow": 58, "startCol": 0, "endCol": 1},  # Periods 1-48
            "values": {"startRow": 10, "endRow": 58, "startCol": 1, "endCol": 2}       # Avg spread
        },
        "axes": {
            "bottom": "Settlement Period",
            "left": "Average Spread (£/MWh)"
        }
    },
    {
        "name": "Demand Profile",
        "type": "AREA",
        "description": "Daily demand pattern",
        "data_range": {
            "time": {"startRow": 10, "endRow": 100, "startCol": 0, "endCol": 1},
            "demand": {"startRow": 10, "endRow": 100, "startCol": 1, "endCol": 2}
        },
        "axes": {
            "bottom": "Time",
            "left": "Demand (MW)"
        }
    }
]

# Function to create a chart
def create_chart(chart_config, sheet_id, position_index):
    """Create a chart in Google Sheets"""
    
    chart_type = chart_config["type"]
    name = chart_config["name"]
    
    print(f"📊 Creating: {name} ({chart_type})")
    
    # Build chart spec based on type
    if chart_type == "LINE":
        domains = [{
            "domain": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": chart_config["data_range"]["dates"]["startRow"],
                        "endRowIndex": chart_config["data_range"]["dates"]["endRow"],
                        "startColumnIndex": chart_config["data_range"]["dates"]["startCol"],
                        "endColumnIndex": chart_config["data_range"]["dates"]["endCol"]
                    }]
                }
            }
        }]
        
        series = [{
            "series": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": chart_config["data_range"]["values"]["startRow"],
                        "endRowIndex": chart_config["data_range"]["values"]["endRow"],
                        "startColumnIndex": chart_config["data_range"]["values"]["startCol"],
                        "endColumnIndex": chart_config["data_range"]["values"]["endCol"]
                    }]
                }
            },
            "targetAxis": "LEFT_AXIS"
        }]
        
        chart_spec = {
            "title": name,
            "basicChart": {
                "chartType": chart_type,
                "legendPosition": "BOTTOM_LEGEND",
                "axis": [
                    {"position": "BOTTOM_AXIS", "title": chart_config["axes"]["bottom"]},
                    {"position": "LEFT_AXIS", "title": chart_config["axes"]["left"]}
                ],
                "domains": domains,
                "series": series,
                "headerCount": 1
            }
        }
    
    elif chart_type == "PIE":
        domains = [{
            "domain": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": chart_config["data_range"]["labels"]["startRow"],
                        "endRowIndex": chart_config["data_range"]["labels"]["endRow"],
                        "startColumnIndex": chart_config["data_range"]["labels"]["startCol"],
                        "endColumnIndex": chart_config["data_range"]["labels"]["endCol"]
                    }]
                }
            }
        }]
        
        series = [{
            "series": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": chart_config["data_range"]["values"]["startRow"],
                        "endRowIndex": chart_config["data_range"]["values"]["endRow"],
                        "startColumnIndex": chart_config["data_range"]["values"]["startCol"],
                        "endColumnIndex": chart_config["data_range"]["values"]["endCol"]
                    }]
                }
            }
        }]
        
        chart_spec = {
            "title": name,
            "pieChart": {
                "legendPosition": "RIGHT_LEGEND",
                "domain": domains[0]["domain"],
                "series": series[0]["series"],
                "threeDimensional": False
            }
        }
    
    elif chart_type in ["COLUMN", "AREA"]:
        domains = [{
            "domain": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": chart_config["data_range"]["categories"]["startRow"],
                        "endRowIndex": chart_config["data_range"]["categories"]["endRow"],
                        "startColumnIndex": chart_config["data_range"]["categories"]["startCol"],
                        "endColumnIndex": chart_config["data_range"]["categories"]["endCol"]
                    }]
                }
            }
        }]
        
        series = [{
            "series": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": chart_config["data_range"]["values"]["startRow"],
                        "endRowIndex": chart_config["data_range"]["values"]["endRow"],
                        "startColumnIndex": chart_config["data_range"]["values"]["startCol"],
                        "endColumnIndex": chart_config["data_range"]["values"]["endCol"]
                    }]
                }
            },
            "targetAxis": "LEFT_AXIS"
        }]
        
        chart_spec = {
            "title": name,
            "basicChart": {
                "chartType": chart_type,
                "legendPosition": "BOTTOM_LEGEND",
                "axis": [
                    {"position": "BOTTOM_AXIS", "title": chart_config["axes"]["bottom"]},
                    {"position": "LEFT_AXIS", "title": chart_config["axes"]["left"]}
                ],
                "domains": domains,
                "series": series,
                "headerCount": 1
            }
        }
    
    # Position chart
    # Stack charts vertically with offset
    anchor_row = 2 + (position_index * 20)
    anchor_col = 10  # Column K (beyond data columns)
    
    chart_request = {
        "requests": [{
            "addChart": {
                "chart": {
                    "spec": chart_spec,
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {
                                "sheetId": sheet_id,
                                "rowIndex": anchor_row,
                                "columnIndex": anchor_col
                            },
                            "offsetXPixels": 0,
                            "offsetYPixels": 0,
                            "widthPixels": 600,
                            "heightPixels": 400
                        }
                    }
                }
            }
        }]
    }
    
    return chart_request

# Create all charts
print()
charts_created = 0
charts_failed = 0

for idx, chart_config in enumerate(charts_to_create):
    try:
        request = create_chart(chart_config, sheet_id, idx)
        
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=request
        ).execute()
        
        print(f"   ✅ {chart_config['name']} created")
        charts_created += 1
        
    except HttpError as e:
        print(f"   ❌ Failed: {e}")
        charts_failed += 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
        charts_failed += 1

print()
print("=" * 80)
print("📊 CHART GENERATION COMPLETE")
print("=" * 80)
print()
print(f"✅ Charts created: {charts_created}")
if charts_failed > 0:
    print(f"❌ Charts failed: {charts_failed}")
print()
print(f"📄 View spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
print()
print("💡 Next steps:")
print("   1. Open spreadsheet to view charts")
print("   2. Adjust chart positions if needed")
print("   3. Customize colors and formatting")
print("   4. Configure data ranges to match your actual data")
print()
