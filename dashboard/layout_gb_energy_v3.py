#!/usr/bin/env python3
"""
Dashboard V3 Layout Builder
Complete Python implementation of GB Energy Dashboard V3
"""

from __future__ import annotations
from typing import List
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'inner-cinema-credentials.json'
DASHBOARD_SHEET_NAME = "Dashboard"

# Color palette (RGB 0-1)
ORANGE = {"red": 1.0, "green": 0.64, "blue": 0.3}      # #FFA24D
BLUE = {"red": 0.2, "green": 0.404, "blue": 0.839}     # #3367D6
LIGHT_BLUE = {"red": 0.89, "green": 0.95, "blue": 0.99}  # #E3F2FD
LIGHT_GREY = {"red": 0.93, "green": 0.93, "blue": 0.93}  # #EEEEEE
KPI_GREY = {"red": 0.96, "green": 0.96, "blue": 0.96}    # #F4F4F4
GREEN = {"red": 0.18, "green": 0.49, "blue": 0.20}       # #2E7D32
RED = {"red": 0.78, "green": 0.16, "blue": 0.16}         # #C62828
WHITE = {"red": 1, "green": 1, "blue": 1}


def get_client():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def get_or_create_sheet(gc, spreadsheet_id: str, title: str) -> tuple:
    """Get sheet or create if doesn't exist. Returns (worksheet, sheet_id)"""
    ss = gc.open_by_key(spreadsheet_id)
    
    try:
        worksheet = ss.worksheet(title)
        sheet_id = worksheet.id
        print(f'✅ Found existing sheet: {title} (ID: {sheet_id})')
        return worksheet, sheet_id
    except:
        # Create new sheet
        worksheet = ss.add_worksheet(
            title=title,
            rows=200,
            cols=26
        )
        sheet_id = worksheet.id
        print(f'✅ Created new sheet: {title} (ID: {sheet_id})')
        return worksheet, sheet_id


def write_layout_values(gc, spreadsheet_id: str):
    """Write all formulas and static values to Dashboard"""
    ss = gc.open_by_key(spreadsheet_id)
    sheet = ss.worksheet(DASHBOARD_SHEET_NAME)
    
    print('\n📝 Writing layout values...')
    
    data: List[dict] = []

    # Title and timestamp (A1-A2)
    data.extend([
        {
            "range": "A1",
            "values": [["⚡ GB ENERGY DASHBOARD – REAL-TIME"]],
        },
        {
            "range": "A2",
            "values": [['=CONCAT("Live Data: ",TEXT(NOW(),"yyyy-mm-dd HH:mm:ss"))']],
        },
    ])

    # Filters (A4-B5)
    data.extend([
        {"range": "A4", "values": [["Region:"]]},
        {"range": "B4", "values": [["All GB"]]},
        {"range": "B3", "values": [["1 Year"]]},  # Time range dropdown seed
        {"range": "A5", "values": [[
            '=CONCAT("⚡ Gen: ",ROUND(IFERROR(SUM(A10:A20),0),1)," GW  |  Demand: ",'
            'ROUND(IFERROR(SUM(B10:B20),0),1)," GW")'
        ]]},
    ])

    # KPI bar (F9-H11)
    data.extend([
        {
            "range": "F9:H9",
            "values": [[
                "📊 VLP Revenue (£k)",
                "💰 Wholesale Avg (£/MWh)",
                "📈 Market Vol (%)",
            ]],
        },
        {"range": "F10", "values": [["=IFERROR(AVERAGE(VLP_Data!E:E)/1000,0)"]]},
        {"range": "G10", "values": [["=IFERROR(AVERAGE(Market_Prices!B:B),0)"]]},
        {"range": "H10", "values": [["=IFERROR(STDEV(Market_Prices!B:B)/AVERAGE(Market_Prices!B:B),0)"]]},
        {"range": "F11", "values": [['=SPARKLINE(VLP_Data!E2:E8,{"charttype","column"})']]},
        {"range": "G11", "values": [['=SPARKLINE(Market_Prices!B2:B8,{"charttype","line"})']]},
        {"range": "H11", "values": [['=SPARKLINE(Market_Prices!B2:B8,{"charttype","column"})']]},
    ])

    # Fuel mix & interconnectors header (A9-E9)
    data.append({
        "range": "A9:E9",
        "values": [[
            "Fuel Type",
            "GW",
            "%",
            "Interconnector",
            "Flow (MW)",
        ]],
    })

    # Active Outages header (A24-H24)
    data.append({
        "range": "A24:H24",
        "values": [[
            "BM Unit",
            "Plant",
            "Fuel",
            "MW Lost",
            "Region",
            "Start Time",
            "End Time",
            "Status",
        ]],
    })

    # ESO Interventions header (A37-F37)
    data.append({
        "range": "A37:F37",
        "values": [[
            "BM Unit",
            "Mode",
            "MW",
            "£/MWh",
            "Duration",
            "Action Type",
        ]],
    })

    # ESO table formula (A38)
    data.append({
        "range": "A38",
        "values": [[
            '=IFERROR(QUERY(ESO_Actions!A:F,"select * where A<>\'\' order by C desc limit 6",1),"No data")'
        ]],
    })

    # Batch update all values
    for item in data:
        sheet.update(values=item["values"], range_name=item["range"])
    
    print(f'   ✅ Wrote {len(data)} value ranges')


def apply_layout_formatting(gc, spreadsheet_id: str, sheet_id: int):
    """Apply all formatting: colors, widths, conditional rules"""
    ss = gc.open_by_key(spreadsheet_id)
    
    print('\n🎨 Applying formatting...')
    
    requests = []

    # Column widths
    requests += [
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,   # A
                    "endIndex": 5,     # A-E
                },
                "properties": {"pixelSize": 150},
                "fields": "pixelSize",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 5,   # F
                    "endIndex": 8,     # F-H
                },
                "properties": {"pixelSize": 120},
                "fields": "pixelSize",
            }
        },
    ]

    # Freeze rows only (no columns due to potential merged cells)
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": 3,
                }
            },
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # Title row A1:H1 – orange + white text
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "textFormat": {
                        "foregroundColor": WHITE,
                        "fontSize": 16,
                        "bold": True,
                    },
                    "horizontalAlignment": "LEFT",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # KPI headers F9:H9 – blue + white
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 8,   # row 9
                "endRowIndex": 9,
                "startColumnIndex": 5,  # F
                "endColumnIndex": 8,    # H
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": BLUE,
                    "textFormat": {
                        "foregroundColor": WHITE,
                        "bold": True,
                    },
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # KPI values F10:H10 – KPI grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 9,  # row 10
                "endRowIndex": 10,
                "startColumnIndex": 5,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": KPI_GREY,
                    "textFormat": {"bold": True},
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Fuel mix header A9:E9 – light blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 8,
                "endRowIndex": 9,
                "startColumnIndex": 0,
                "endColumnIndex": 5,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_BLUE,
                    "textFormat": {"bold": True},
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Active Outages header A24:H24 – light blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 23,  # row 24
                "endRowIndex": 24,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_BLUE,
                    "textFormat": {"bold": True},
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # ESO Interventions header A37:F37 – light blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 36,  # row 37
                "endRowIndex": 37,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_BLUE,
                    "textFormat": {"bold": True},
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Table blocks light grey
    def grey_block(start_row, end_row, start_col, end_col):
        return {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row,
                    "endRowIndex": end_row,
                    "startColumnIndex": start_col,
                    "endColumnIndex": end_col,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": LIGHT_GREY,
                    }
                },
                "fields": "userEnteredFormat(backgroundColor)",
            }
        }

    # Fuel mix table (A10:E21)
    requests.append(grey_block(9, 21, 0, 5))
    # Active outages table (A25:H35)
    requests.append(grey_block(24, 35, 0, 8))
    # ESO interventions table (A38:F43)
    requests.append(grey_block(37, 43, 0, 6))

    # Conditional formatting: Interconnector imports (green)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,
                    "endRowIndex": 21,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "← Import"}],
                    },
                    "format": {
                        "backgroundColor": GREEN,
                        "textFormat": {
                            "foregroundColor": WHITE,
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })

    # Conditional formatting: Interconnector exports (red)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,
                    "endRowIndex": 21,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "→ Export"}],
                    },
                    "format": {
                        "backgroundColor": RED,
                        "textFormat": {
                            "foregroundColor": WHITE,
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })

    # Conditional formatting: >500 MW in Active Outages (D column)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 24,  # row 25
                    "endRowIndex": 35,    # row 35
                    "startColumnIndex": 3,  # D
                    "endColumnIndex": 4,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "NUMBER_GREATER",
                        "values": [{"userEnteredValue": "500"}],
                    },
                    "format": {
                        "backgroundColor": RED,
                        "textFormat": {
                            "foregroundColor": WHITE,
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })

    # Conditional formatting: >500 MW in ESO Interventions (C column)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 37,  # row 38
                    "endRowIndex": 43,    # row 43
                    "startColumnIndex": 2,  # C
                    "endColumnIndex": 3,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "NUMBER_GREATER",
                        "values": [{"userEnteredValue": "500"}],
                    },
                    "format": {
                        "backgroundColor": RED,
                        "textFormat": {
                            "foregroundColor": WHITE,
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })

    # Execute batch update
    ss.batch_update({'requests': requests})
    print(f'   ✅ Applied {len(requests)} formatting rules')


def setup_gb_dashboard_v3(spreadsheet_id: str):
    """Main entry point: create/update Dashboard V3"""
    gc = get_client()
    
    print('=' * 70)
    print('⚡ GB ENERGY DASHBOARD V3 - LAYOUT BUILDER')
    print('=' * 70)
    
    # Get or create Dashboard sheet
    worksheet, sheet_id = get_or_create_sheet(gc, spreadsheet_id, DASHBOARD_SHEET_NAME)
    
    # Write values
    write_layout_values(gc, spreadsheet_id)
    
    # Apply formatting
    apply_layout_formatting(gc, spreadsheet_id, sheet_id)
    
    print('\n✅ Dashboard V3 layout complete!')
    print(f'   View: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_id}')


if __name__ == "__main__":
    setup_gb_dashboard_v3(SPREADSHEET_ID)
