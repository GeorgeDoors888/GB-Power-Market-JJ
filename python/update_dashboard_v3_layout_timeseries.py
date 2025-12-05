#!/usr/bin/env python3
"""
update_dashboard_v3_layout_timeseries.py

- Shrinks the KPI/sparkline rows on 'Dashboard V3' (rows 16-19 to 50px)
- Adds a richer dropdown on B3 (view / time range)
- Inserts extra rows from A39 downwards for readability (15 rows for 3 charts)
- Adds 3 charts (wind, demand+IC, prices) starting below row 39

Assumptions:
- SPREADSHEET_ID is your GB dashboard sheet
- Sheet 'Dashboard V3' exists
- Sheet 'Chart Data' exists and has columns:
    A: Settlement period (1-48)
    B: System demand (MW)
    C: Expected wind (MW)
    D: Delivered wind (MW)
    E: Interconnector net import (MW)
    G: Day-ahead price (£/MWh)
    H: Imbalance price (£/MWh)
"""

from __future__ import annotations
from typing import Any, Dict, List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- CONFIG -----------------------------------------------------------

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD_SHEET_NAME = "Dashboard V3"
CHART_DATA_SHEET_NAME = "Chart Data"

SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"  # FIXED: Was service-account.json
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# --- HELPERS ----------------------------------------------------------

def get_sheets_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def get_sheet_id(service, sheet_name: str) -> int:
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for sh in meta["sheets"]:
        if sh["properties"]["title"] == sheet_name:
            return sh["properties"]["sheetId"]
    raise ValueError(f"Sheet '{sheet_name}' not found")


# --- REQUEST BUILDERS -------------------------------------------------

def build_shrink_sparkline_rows_request(dashboard_sheet_id: int) -> Dict[str, Any]:
    """
    Make rows 16-19 shorter (50px instead of 80px).
    UI rows 16-19 => 0-based indices 15-19
    """
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": dashboard_sheet_id,
                "dimension": "ROWS",
                "startIndex": 15,   # row 16
                "endIndex": 19,     # up to row 19 (exclusive)
            },
            "properties": {
                "pixelSize": 50    # ADJUSTED: 50px instead of 24px
            },
            "fields": "pixelSize",
        }
    }


def build_insert_rows_for_timeseries_request(dashboard_sheet_id: int,
                                             start_row_ui: int = 39,
                                             num_rows: int = 15) -> Dict[str, Any]:
    """
    Insert extra rows starting at A<start_row_ui> to give the charts room.
    
    ADJUSTED: 15 rows instead of 30 (5 rows per chart)
    """
    start_index = start_row_ui - 1  # convert to 0-based
    end_index = start_index + num_rows

    return {
        "insertDimension": {
            "range": {
                "sheetId": dashboard_sheet_id,
                "dimension": "ROWS",
                "startIndex": start_index,
                "endIndex": end_index,
            },
            "inheritFromBefore": True,
        }
    }


def build_view_dropdown_request(dashboard_sheet_id: int) -> Dict[str, Any]:
    """
    Set a richer data validation on B3:
      - Today – Auto Refresh
      - Today – Manual
      - Last 7 Days
      - Last 30 Days
      - Year to Date
    UI cell B3 => rowIndex=2, colIndex=1
    """
    values = [
        "Today – Auto Refresh",
        "Today – Manual",
        "Last 7 Days",
        "Last 30 Days",
        "Year to Date",
    ]
    return {
        "setDataValidation": {
            "range": {
                "sheetId": dashboard_sheet_id,
                "startRowIndex": 2,   # row 3
                "endRowIndex": 3,
                "startColumnIndex": 1,  # col B
                "endColumnIndex": 2,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in values],
                },
                "strict": True,
                "showCustomUi": True,
            },
        }
    }


def build_label_view_cell_request(dashboard_sheet_id: int) -> Dict[str, Any]:
    """
    Put a simple label 'View:' into A3 to make the dropdown clearer.
    """
    return {
        "updateCells": {
            "range": {
                "sheetId": dashboard_sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 0,
                "endColumnIndex": 1,
            },
            "rows": [
                {
                    "values": [
                        {
                            "userEnteredValue": {"stringValue": "View:"},
                            "userEnteredFormat": {
                                "textFormat": {
                                    "bold": True,
                                },
                                "horizontalAlignment": "RIGHT",
                            },
                        }
                    ]
                }
            ],
            "fields": "userEnteredValue,userEnteredFormat(textFormat,horizontalAlignment)",
        }
    }


def build_wind_chart_request(dashboard_sheet_id: int,
                             chart_data_sheet_id: int) -> Dict[str, Any]:
    """
    Chart 1: Expected vs Delivered Wind – Today
    Uses Chart Data A (SP), C (expected wind), D (delivered wind)
    Anchored roughly at A39
    
    FIXED: Data rows 2-49 (48 SPs) => indices 1-49 (not 1-98)
    """
    start_row = 1   # Row 2 (0-based)
    end_row = 49    # Row 49 (exclusive, so includes row 48)

    return {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Expected vs Delivered Wind – Today",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {
                                "position": "BOTTOM_AXIS",
                                "title": "Settlement Period",
                            },
                            {
                                "position": "LEFT_AXIS",
                                "title": "MW",
                            },
                        ],
                        "domains": [
                            {
                                "domain": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 0,  # Col A
                                                "endColumnIndex": 1,
                                            }
                                        ]
                                    }
                                }
                            }
                        ],
                        "series": [
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 2,  # Col C: expected wind
                                                "endColumnIndex": 3,
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE",
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 3,  # Col D: delivered wind
                                                "endColumnIndex": 4,
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE",
                            },
                        ],
                    },
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 38,
                            "columnIndex": 0
                        },
                        "offsetXPixels": 0,
                        "offsetYPixels": 0
                    }
                },
            }
        }
    }


def build_demand_ic_chart_request(dashboard_sheet_id: int,
                                  chart_data_sheet_id: int) -> Dict[str, Any]:
    """
    Chart 2: Demand & Interconnectors – Today
    Uses Chart Data A (time), B (system demand), E (IC net import)
    Anchored around I39 (col 8)
    
    FIXED: Data rows 2-49
    """
    start_row = 1
    end_row = 49

    return {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Demand & Interconnectors – Today",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {
                                "position": "BOTTOM_AXIS",
                                "title": "Settlement Period",
                            },
                            {
                                "position": "LEFT_AXIS",
                                "title": "MW",
                            },
                        ],
                        "domains": [
                            {
                                "domain": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 0,  # Col A
                                                "endColumnIndex": 1,
                                            }
                                        ]
                                    }
                                }
                            }
                        ],
                        "series": [
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 1,  # Col B: demand
                                                "endColumnIndex": 2,
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE",
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 4,  # Col E: IC net import
                                                "endColumnIndex": 5,
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE",
                            },
                        ],
                    },
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 38,
                            "columnIndex": 8
                        },
                        "offsetXPixels": 0,
                        "offsetYPixels": 0
                    }
                },
            }
        }
    }


def build_prices_chart_request(dashboard_sheet_id: int,
                               chart_data_sheet_id: int) -> Dict[str, Any]:
    """
    Chart 3: Market Prices – Today
    Uses Chart Data A (time), G (Day-ahead price), H (Imbalance price)
    Anchored around A44 (after 5 rows gap)
    
    FIXED: Data rows 2-49, anchor adjusted to A44
    """
    start_row = 1
    end_row = 49

    return {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Market Prices – Today",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {
                                "position": "BOTTOM_AXIS",
                                "title": "Settlement Period",
                            },
                            {
                                "position": "LEFT_AXIS",
                                "title": "£/MWh",
                            },
                        ],
                        "domains": [
                            {
                                "domain": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 0,  # Col A
                                                "endColumnIndex": 1,
                                            }
                                        ]
                                    }
                                }
                            }
                        ],
                        "series": [
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 6,  # Col G: DA price
                                                "endColumnIndex": 7,
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE",
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": chart_data_sheet_id,
                                                "startRowIndex": start_row,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": 7,  # Col H: Imbalance price
                                                "endColumnIndex": 8,
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE",
                            },
                        ],
                    },
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 43,
                            "columnIndex": 0
                        },
                        "offsetXPixels": 0,
                        "offsetYPixels": 0
                    }
                },
            }
        }
    }


# --- MAIN -------------------------------------------------------------

def main():
    print("\n🎨 Updating Dashboard V3 Layout for Timeseries Charts")
    print("="*60)
    
    service = get_sheets_service()

    print("\n📍 Getting sheet IDs...")
    try:
        dashboard_id = get_sheet_id(service, DASHBOARD_SHEET_NAME)
        chart_data_id = get_sheet_id(service, CHART_DATA_SHEET_NAME)
        print(f"   Dashboard V3 ID: {dashboard_id}")
        print(f"   Chart Data ID: {chart_data_id}")
    except ValueError as e:
        print(f"   ❌ Error: {e}")
        print("\n   Run python/populate_chart_data.py first to create Chart Data sheet")
        return

    requests: List[Dict[str, Any]] = []

    print("\n📝 Building update requests...")
    
    # 1) Shrink rows 16-19 to 50px
    print("   - Shrink sparkline rows (16-19) to 50px")
    requests.append(build_shrink_sparkline_rows_request(dashboard_id))

    # 2) Insert 15 rows from row 39 (5 rows per chart)
    print("   - Insert 15 rows at row 39")
    requests.append(build_insert_rows_for_timeseries_request(
        dashboard_id, start_row_ui=39, num_rows=15
    ))

    # 3) Label A3 and set dropdown on B3
    print("   - Add 'View:' label to A3")
    requests.append(build_label_view_cell_request(dashboard_id))
    print("   - Add time range dropdown to B3")
    requests.append(build_view_dropdown_request(dashboard_id))

    # 4) Add three charts
    print("   - Add Wind chart at A39")
    requests.append(build_wind_chart_request(dashboard_id, chart_data_id))
    print("   - Add Demand+IC chart at I39")
    requests.append(build_demand_ic_chart_request(dashboard_id, chart_data_id))
    print("   - Add Prices chart at A44")
    requests.append(build_prices_chart_request(dashboard_id, chart_data_id))

    print("\n⚡ Executing batch update...")
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()

    print("\n✅ Dashboard V3 layout updated successfully!")
    print("\n📊 Changes applied:")
    print("   • Sparkline rows reduced to 50px")
    print("   • 15 rows inserted at row 39")
    print("   • View dropdown added to B3")
    print("   • 3 timeseries charts added:")
    print("     - Wind (A39)")
    print("     - Demand & IC (I39)")
    print("     - Prices (A44)")
    print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard_id}")


if __name__ == "__main__":
    main()
