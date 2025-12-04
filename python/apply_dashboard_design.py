"""
apply_dashboard_design.py

GB ENERGY DASHBOARD V3 – Layout, KPIs & Charts

This script:
- Ensures the "Dashboard" sheet exists in the target spreadsheet.
- Writes all labels/formulas for the Dashboard:
    * Header, filters (Time Range, Region/DNO)
    * KPI strip (F9:L10 + sparklines)
    * Fuel mix header, Outages header, ESO header
- Applies layout & formatting using spreadsheets.batchUpdate:
    * Column widths, frozen rows/cols
    * Colour scheme: orange header, blue KPI headers, grey tables
    * Conditional formatting for IC imports/exports
- Rebuilds two charts:
    * Combo chart (system + prices + BESS/VLP/ESO) from "Chart Data"!A1:J49
    * Net margin line chart from "Chart Data"!A1:A49 & J1:J49

You normally don't edit this once it's in place; you configure
BigQuery & data loading in populate_dashboard_tables.py instead.
"""

from __future__ import annotations

import os
from typing import List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------
# CONFIG – EDIT THESE IF NEEDED
# ---------------------------------------------------------------------

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "../workspace-credentials.json")

DASHBOARD_SHEET_NAME = "Dashboard V3"
CHART_DATA_SHEET_NAME = "Chart Data"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Colours (RGB 0–1)
ORANGE = {"red": 1.0, "green": 0.64, "blue": 0.3}        # #FFA24D
BLUE = {"red": 0.2, "green": 0.404, "blue": 0.839}       # #3367D6
LIGHT_BLUE = {"red": 0.89, "green": 0.95, "blue": 0.99}  # header blue-ish
LIGHT_GREY = {"red": 0.93, "green": 0.93, "blue": 0.93}  # #EEEEEE
KPI_GREY = {"red": 0.96, "green": 0.96, "blue": 0.96}    # #F4F4F4
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
BLACK = {"red": 0.0, "green": 0.0, "blue": 0.0}


# ---------------------------------------------------------------------
# SERVICE HELPERS
# ---------------------------------------------------------------------

def get_sheets_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def ensure_sheet(service, spreadsheet_id: str, title: str) -> int:
    """Return sheetId for `title`, create if missing."""
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in ss["sheets"]:
        if sh["properties"]["title"] == title:
            return sh["properties"]["sheetId"]

    body = {
        "requests": [{
            "addSheet": {
                "properties": {
                    "title": title,
                    "gridProperties": {
                        "rowCount": 200,
                        "columnCount": 26
                    },
                    "tabColor": ORANGE
                }
            }
        }]
    }
    res = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    return res["replies"][0]["addSheet"]["properties"]["sheetId"]


def get_sheet_id_by_title(service, spreadsheet_id: str, title: str) -> int | None:
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in ss["sheets"]:
        if sh["properties"]["title"] == title:
            return sh["properties"]["sheetId"]
    return None


# ---------------------------------------------------------------------
# VALUES: LABELS + FORMULAS
# ---------------------------------------------------------------------

def build_values_payload(sheet_name: str) -> List[dict]:
    data: List[dict] = []

    # Header + timestamps
    data.append({
        "range": f"{sheet_name}!A1",
        "values": [["⚡ GB ENERGY DASHBOARD – REAL-TIME"]],
    })
    data.append({
        "range": f"{sheet_name}!A2",
        "values": [[
            '=CONCAT("Live Data: ",TEXT(NOW(),"yyyy-mm-dd HH:mm:ss"))'
        ]],
    })
    # Filters
    data.append({
        "range": f"{sheet_name}!A3",
        "values": [["Time Range"]],
    })
    data.append({
        "range": f"{sheet_name}!B3",
        "values": [["1 Year"]],
    })
    data.append({
        "range": f"{sheet_name}!E3",
        "values": [["Region / DNO"]],
    })
    data.append({
        "range": f"{sheet_name}!F3",
        "values": [["All GB"]],
    })
    # Gen vs demand headline
    data.append({
        "range": f"{sheet_name}!A5",
        "values": [[
            '=CONCAT("⚡ Gen: ",ROUND(Live_Generation,1)," GW  |  Demand: ",'
            'ROUND(Live_Demand,1)," GW")'
        ]],
    })

    # KPI strip headers (F–L)
    data.append({
        "range": f"{sheet_name}!F9:L9",
        "values": [[
            "📊 VLP Revenue (£ k)",
            "💰 Wholesale Avg (£/MWh)",
            "📈 Market Vol (%)",
            "All-GB Net Margin (£/MWh)",
            "Selected DNO Net Margin (£/MWh)",
            "Selected DNO Volume (MWh)",
            "Selected DNO Revenue (£k)",
        ]],
    })

    # KPI values
    data.append({
        "range": f"{sheet_name}!F10",
        "values": [["=AVERAGE(VLP_Data!D:D)/1000"]],
    })
    data.append({
        "range": f"{sheet_name}!G10",
        "values": [["=AVERAGE(Market_Prices!C:C)"]],
    })
    data.append({
        "range": f"{sheet_name}!H10",
        "values": [[
            "=STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C)"
        ]],
    })
    # All‑GB net margin from Chart Data column J
    data.append({
        "range": f"{sheet_name}!I10",
        "values": [[
            "=AVERAGE(FILTER('Chart Data'!J:J, NOT(ISBLANK('Chart Data'!J:J))))"
        ]],
    })
    # Selected DNO net margin from DNO_Map
    data.append({
        "range": f"{sheet_name}!J10",
        "values": [[
            '=IF($F$3="All GB", I10, '
            'XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$E:$E, NA()))'
        ]],
    })
    # Selected DNO volume
    data.append({
        "range": f"{sheet_name}!K10",
        "values": [[
            '=IF($F$3="All GB", '
            'SUM(FILTER(\'Chart Data\'!D:D, NOT(ISBLANK(\'Chart Data\'!D:D))))/2, '
            'XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$F:$F, 0))'
        ]],
    })
    # Selected DNO revenue (£k)
    data.append({
        "range": f"{sheet_name}!L10",
        "values": [[
            '=IF($F$3="All GB", SUM(DNO_Map!$G:$G)/1000, '
            'XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$G:$G, 0)/1000)'
        ]],
    })

    # Sparklines for All‑GB KPI trend (F11:I11)
    data.append({
        "range": f"{sheet_name}!F11",
        "values": [['=SPARKLINE(VLP_Data!D2:D8,{"charttype","column"})']],
    })
    data.append({
        "range": f"{sheet_name}!G11",
        "values": [['=SPARKLINE(Market_Prices!C2:C8,{"charttype","line"})']],
    })
    data.append({
        "range": f"{sheet_name}!H11",
        "values": [['=SPARKLINE(Market_Prices!C2:C8,{"charttype","column"})']],
    })
    data.append({
        "range": f"{sheet_name}!I11",
        "values": [["=SPARKLINE('Chart Data'!J2:J49)"]],
    })

    # --- Fuel mix & interconnectors header (row 9, columns A–E) ---
    data.append({
        "range": f"{sheet_name}!A9:E9",
        "values": [["Fuel Type", "GW", "%", "Interconnector", "Flow (MW)"]],
    })

    # --- Active Outages header (row 27) ---
    data.append({
        "range": f"{sheet_name}!A27:H27",
        "values": [["BM Unit", "Plant", "Fuel", "MW Lost", "Region", "Start Time", "End Time", "Status"]],
    })

    # --- ESO Interventions header (row 42) + QUERY formula (row 43) ---
    data.append({
        "range": f"{sheet_name}!A42:F42",
        "values": [["BM Unit", "Mode", "MW", "£/MWh", "Duration (min)", "Action Type"]],
    })
    data.append({
        "range": f"{sheet_name}!A43",
        "values": [['=QUERY(ESO_Actions!A:F,"SELECT * ORDER BY A DESC LIMIT 10",1)']],
    })

    return data


def apply_values(service, spreadsheet_id: str, sheet_name: str):
    payload = build_values_payload(sheet_name)
    body = {"valueInputOption": "USER_ENTERED", "data": payload}
    service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    print(f"   ✅ Values written to {sheet_name}")


# ---------------------------------------------------------------------
# FORMATTING
# ---------------------------------------------------------------------

def build_formatting_requests(sheet_id: int) -> List[dict]:
    reqs = []

    # First, unmerge any existing merged cells
    reqs.append({
        "unmergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 100,
                "startColumnIndex": 0,
                "endColumnIndex": 20
            }
        }
    })

    # Frozen rows + columns
    reqs.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": 3,
                    "frozenColumnCount": 0
                }
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"
        }
    })

    # Column widths
    for col_idx, width_px in [
        (0, 150), (1, 130), (2, 130), (3, 200), (4, 180),
        (5, 130), (6, 130), (7, 130), (8, 130), (9, 130),
        (10, 130), (11, 130)
    ]:
        reqs.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1
                },
                "properties": {"pixelSize": width_px},
                "fields": "pixelSize"
            }
        })

    # Title row (A1:L1) - Orange bg, white bold, merged
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 12},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": WHITE},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat"
        }
    })
    reqs.append({
        "mergeCells": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 12},
            "mergeType": "MERGE_ALL"
        }
    })

    # Timestamp row (A2:L2)
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 12},
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"italic": True, "fontSize": 9},
                    "horizontalAlignment": "RIGHT"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # KPI headers (F9:L9) - Blue bg, white bold
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 8, "endRowIndex": 9, "startColumnIndex": 5, "endColumnIndex": 12},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": BLUE,
                    "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": WHITE},
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # KPI values (F10:L10) - Grey bg, bold large text
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 5, "endColumnIndex": 12},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": KPI_GREY,
                    "textFormat": {"bold": True, "fontSize": 16},
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # Number formats for KPIs
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 5, "endColumnIndex": 6},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "£#,##0.00"}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 6, "endColumnIndex": 7},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "£#,##0.00"}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 7, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.00%"}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # Fuel/IC header (A9:E9) - Light blue bg, bold
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 8, "endRowIndex": 9, "startColumnIndex": 0, "endColumnIndex": 5},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_BLUE,
                    "textFormat": {"bold": True, "fontSize": 10},
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # Outages header (A27:H27) - Light blue bg, bold
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 26, "endRowIndex": 27, "startColumnIndex": 0, "endColumnIndex": 8},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_BLUE,
                    "textFormat": {"bold": True, "fontSize": 10},
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # ESO header (A42:F42) - Light blue bg, bold
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 41, "endRowIndex": 42, "startColumnIndex": 0, "endColumnIndex": 6},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_BLUE,
                    "textFormat": {"bold": True, "fontSize": 10},
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # Conditional formatting: IC imports green
    reqs.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 100, "startColumnIndex": 4, "endColumnIndex": 5}],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "← Import"}]
                    },
                    "format": {
                        "textFormat": {"foregroundColor": {"red": 0.18, "green": 0.49, "blue": 0.20}}
                    }
                }
            },
            "index": 0
        }
    })

    # Conditional formatting: IC exports red
    reqs.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 100, "startColumnIndex": 4, "endColumnIndex": 5}],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "→ Export"}]
                    },
                    "format": {
                        "textFormat": {"foregroundColor": {"red": 0.78, "green": 0.16, "blue": 0.16}}
                    }
                }
            },
            "index": 1
        }
    })

    return reqs


def apply_formatting(service, spreadsheet_id: str, sheet_id: int):
    reqs = build_formatting_requests(sheet_id)
    body = {"requests": reqs}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    print("   ✅ Formatting applied")


# ---------------------------------------------------------------------
# CHARTS
# ---------------------------------------------------------------------

def rebuild_charts(service, spreadsheet_id: str,
                   dashboard_sheet_id: int,
                   chart_data_sheet_id: int):
    """
    Delete existing charts on Dashboard, then create:
    1) Combo chart (system + prices + flex)
    2) Net margin line chart
    """
    # Get existing charts
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    charts_to_delete = []
    for sh in ss["sheets"]:
        if sh["properties"]["sheetId"] == dashboard_sheet_id:
            charts_to_delete = sh.get("charts", [])
            break

    # Delete all charts
    if charts_to_delete:
        del_reqs = [{"deleteEmbeddedObject": {"objectId": c["chartId"]}} for c in charts_to_delete]
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": del_reqs}).execute()
        print(f"   ✅ Deleted {len(charts_to_delete)} existing charts")

    # Build combo chart
    combo_chart_spec = {
        "title": "GB Energy System Overview",
        "basicChart": {
            "chartType": "COMBO",
            "legendPosition": "RIGHT_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Time"},
                {"position": "LEFT_AXIS", "title": "MW / MWh"},
                {"position": "RIGHT_AXIS", "title": "£/MWh"}
            ],
            "domains": [{
                "domain": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 49,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1
                        }]
                    }
                }
            }],
            "series": [
                # Series 0: DA Price (line, right axis)
                {
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 49,
                                "startColumnIndex": 1,
                                "endColumnIndex": 2
                            }]
                        }
                    },
                    "targetAxis": "RIGHT_AXIS",
                    "type": "LINE"
                },
                # Series 1: Imbalance Price (line, right axis)
                {
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 49,
                                "startColumnIndex": 2,
                                "endColumnIndex": 3
                            }]
                        }
                    },
                    "targetAxis": "RIGHT_AXIS",
                    "type": "LINE"
                },
                # Series 2: System Demand (area, left axis)
                {
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 49,
                                "startColumnIndex": 3,
                                "endColumnIndex": 4
                            }]
                        }
                    },
                    "targetAxis": "LEFT_AXIS",
                    "type": "AREA"
                },
                # Series 3: Renewables (area, left axis)
                {
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 49,
                                "startColumnIndex": 4,
                                "endColumnIndex": 5
                            }]
                        }
                    },
                    "targetAxis": "LEFT_AXIS",
                    "type": "AREA"
                },
                # Series 4: IC Flow (line, left axis)
                {
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 49,
                                "startColumnIndex": 5,
                                "endColumnIndex": 6
                            }]
                        }
                    },
                    "targetAxis": "LEFT_AXIS",
                    "type": "LINE"
                },
                # Series 5: BESS (line, left axis)
                {
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 49,
                                "startColumnIndex": 6,
                                "endColumnIndex": 7
                            }]
                        }
                    },
                    "targetAxis": "LEFT_AXIS",
                    "type": "LINE"
                },
                # Series 6: VLP (line, left axis)
                {
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 49,
                                "startColumnIndex": 7,
                                "endColumnIndex": 8
                            }]
                        }
                    },
                    "targetAxis": "LEFT_AXIS",
                    "type": "LINE"
                },
                # Series 7: ESO Actions (line, left axis)
                {
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 49,
                                "startColumnIndex": 8,
                                "endColumnIndex": 9
                            }]
                        }
                    },
                    "targetAxis": "LEFT_AXIS",
                    "type": "LINE"
                }
            ]
        }
    }

    # Build net margin chart
    net_margin_chart_spec = {
        "title": "Portfolio Net Margin (£/MWh)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Time"},
                {"position": "LEFT_AXIS", "title": "£/MWh"}
            ],
            "domains": [{
                "domain": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 49,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1
                        }]
                    }
                }
            }],
            "series": [{
                "series": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 49,
                            "startColumnIndex": 9,
                            "endColumnIndex": 10
                        }]
                    }
                },
                "targetAxis": "LEFT_AXIS",
                "type": "LINE"
            }]
        }
    }

    # Add both charts
    add_chart_reqs = [
        {
            "addChart": {
                "chart": {
                    "spec": combo_chart_spec,
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {"sheetId": dashboard_sheet_id, "rowIndex": 12, "columnIndex": 6},
                            "offsetXPixels": 0,
                            "offsetYPixels": 0,
                            "widthPixels": 800,
                            "heightPixels": 400
                        }
                    }
                }
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": net_margin_chart_spec,
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {"sheetId": dashboard_sheet_id, "rowIndex": 41, "columnIndex": 6},
                            "offsetXPixels": 0,
                            "offsetYPixels": 0,
                            "widthPixels": 600,
                            "heightPixels": 300
                        }
                    }
                }
            }
        }
    ]

    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": add_chart_reqs}).execute()
    print("   ✅ Created 2 charts (combo + net margin)")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def setup_dashboard_v3():
    service = get_sheets_service()
    dashboard_sheet_id = ensure_sheet(service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME)
    chart_data_sheet_id = ensure_sheet(service, SPREADSHEET_ID, CHART_DATA_SHEET_NAME)

    print(f"✅ Dashboard sheet ID: {dashboard_sheet_id}")
    print(f"✅ Chart Data sheet ID: {chart_data_sheet_id}")

    # CRITICAL: Clear the entire Dashboard sheet first to remove V2 content
    print("\n--- Step 0: Clearing existing Dashboard content ---")
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range="Dashboard V3!A1:Z200",
        body={}
    ).execute()
    print("   ✅ Dashboard cleared")

    print("\n--- Step 1: Writing values (labels, formulas, KPIs) ---")
    apply_values(service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME)

    print("\n--- Step 2: Applying formatting (colors, widths, conditional) ---")
    apply_formatting(service, SPREADSHEET_ID, dashboard_sheet_id)

    print("\n--- Step 3: Building charts (combo + net margin) ---")
    rebuild_charts(service, SPREADSHEET_ID, dashboard_sheet_id, chart_data_sheet_id)

    print(f"\n✅ DASHBOARD V3 DESIGN COMPLETE")
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard_sheet_id}")


if __name__ == "__main__":
    setup_dashboard_v3()
