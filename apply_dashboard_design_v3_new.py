#!/usr/bin/env python3
"""
apply_dashboard_design_v3_new.py

Major rewrite of the Dashboard layout for "GB ENERGY DASHBOARD V3".

This script:
- Ensures the "Dashboard" sheet exists.
- Writes all labels/formulas for the Dashboard (header, filters, KPI strip, Outages, ESO).
- Applies formatting using spreadsheets.batchUpdate (column widths, colours, conditional formats).
- Builds two charts:
    1) Combo chart (system + prices + BESS/VLP/ESO) from "Chart Data"!A1:J49.
    2) Net Margin line chart from "Chart Data"!A1:A49 and J1:J49.

It is idempotent: re-running will re-apply the design each time.
"""

from typing import List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SERVICE_ACCOUNT_FILE = "workspace-credentials.json"

DASHBOARD_SHEET_NAME = "Dashboard"
CHART_DATA_SHEET_NAME = "Chart Data"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Colours
ORANGE = {"red": 1.0, "green": 0.64, "blue": 0.3}
BLUE = {"red": 0.2, "green": 0.404, "blue": 0.839}
LIGHT_BLUE = {"red": 0.89, "green": 0.95, "blue": 0.99}
LIGHT_GREY = {"red": 0.93, "green": 0.93, "blue": 0.93}
KPI_GREY = {"red": 0.96, "green": 0.96, "blue": 0.96}
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
BLACK = {"red": 0.0, "green": 0.0, "blue": 0.0}
GREEN = {"red": 0.18, "green": 0.49, "blue": 0.20}
RED = {"red": 0.78, "green": 0.16, "blue": 0.16}


# ---------------------------------------------------------------------
# SERVICE HELPERS
# ---------------------------------------------------------------------

def get_sheets_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
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
    res = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    return res["replies"][0]["addSheet"]["properties"]["sheetId"]


def get_sheet_id_by_title(service, spreadsheet_id: str, title: str) -> int:
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in ss["sheets"]:
        if sh["properties"]["title"] == title:
            return sh["properties"]["sheetId"]
    return None


# ---------------------------------------------------------------------
# VALUES: LABELS + FORMULAS (INCLUDING KPI + DNO KPIs)
# ---------------------------------------------------------------------

def build_values_payload(sheet_name: str) -> List[dict]:
    data = []

    # --- Header & filters & gen/demand headline ---
    data.append({
        "range": f"{sheet_name}!A1",
        "values": [["⚡ GB ENERGY DASHBOARD V3 – REAL-TIME"]],
    })
    data.append({
        "range": f"{sheet_name}!A2",
        "values": [['=CONCAT("Live Data: ",TEXT(NOW(),"yyyy-mm-dd HH:mm:ss"))']],
    })
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
    data.append({
        "range": f"{sheet_name}!A5",
        "values": [['=CONCAT("⚡ Gen: ",ROUND(Live_Generation,1)," GW  |  Demand: ",ROUND(Live_Demand,1)," GW")']],
    })

    # --- KPI strip (F–L, rows 9–11) ---
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
    data.append({"range": f"{sheet_name}!F10", "values": [["=AVERAGE(VLP_Data!D:D)/1000"]]})
    data.append({"range": f"{sheet_name}!G10", "values": [["=AVERAGE(Market_Prices!C:C)"]]})
    data.append({"range": f"{sheet_name}!H10", "values": [["=STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C)"]]})
    data.append({"range": f"{sheet_name}!I10", "values": [["=AVERAGE(FILTER('Chart Data'!J:J, NOT(ISBLANK('Chart Data'!J:J))))"]]})
    data.append({"range": f"{sheet_name}!J10", "values": [['=IF($F$3="All GB", I10, XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$E:$E, NA()))']]})
    data.append({"range": f"{sheet_name}!K10", "values": [['=IF($F$3="All GB", SUM(FILTER(\'Chart Data\'!D:D, NOT(ISBLANK(\'Chart Data\'!D:D))))/2, XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$F:$F, 0))']]})
    data.append({"range": f"{sheet_name}!L10", "values": [['=IF($F$3="All GB", SUM(DNO_Map!$G:$G)/1000, XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$G:$G, 0)/1000)']]})

    # Sparklines for All‑GB KPI trend (F11:I11)
    data.append({"range": f"{sheet_name}!F11", "values": [['=SPARKLINE(VLP_Data!D2:D8,{"charttype","column"})']]})
    data.append({"range": f"{sheet_name}!G11", "values": [['=SPARKLINE(Market_Prices!C2:C8,{"charttype","line"})']]})
    data.append({"range": f"{sheet_name}!H11", "values": [['=SPARKLINE(Market_Prices!C2:C8,{"charttype","column"})']]})
    data.append({"range": f"{sheet_name}!I11", "values": [["=SPARKLINE('Chart Data'!J2:J49)"]]})

    # --- Fuel mix & interconnectors header (row 9, columns A–E) ---
    data.append({
        "range": f"{sheet_name}!A9:E9",
        "values": [["Fuel Type", "GW", "%", "Interconnector", "Flow (MW)"]],
    })

    # --- System Statistics (rows 13-16) ---
    data.append({
        "range": f"{sheet_name}!A13",
        "values": [["📊 MARKET STATISTICS"]],
    })
    data.append({
        "range": f"{sheet_name}!A14:E14",
        "values": [["Metric", "Last Hour", "Last 24h", "Last Week", "Last Month"]],
    })
    data.append({
        "range": f"{sheet_name}!A15",
        "values": [["Avg Price (£/MWh)"]],
    })
    data.append({
        "range": f"{sheet_name}!B15",
        "values": [['=AVERAGE(FILTER(Market_Prices!C:C, Market_Prices!A:A>=NOW()-1/24))']],
    })
    data.append({
        "range": f"{sheet_name}!C15",
        "values": [['=AVERAGE(FILTER(Market_Prices!C:C, Market_Prices!A:A>=NOW()-1))']],
    })
    data.append({
        "range": f"{sheet_name}!D15",
        "values": [['=AVERAGE(FILTER(Market_Prices!C:C, Market_Prices!A:A>=NOW()-7))']],
    })
    data.append({
        "range": f"{sheet_name}!E15",
        "values": [['=AVERAGE(FILTER(Market_Prices!C:C, Market_Prices!A:A>=NOW()-30))']],
    })
    data.append({
        "range": f"{sheet_name}!A16",
        "values": [["Max Price (£/MWh)"]],
    })
    data.append({
        "range": f"{sheet_name}!B16",
        "values": [['=MAX(FILTER(Market_Prices!C:C, Market_Prices!A:A>=NOW()-1/24))']],
    })
    data.append({
        "range": f"{sheet_name}!C16",
        "values": [['=MAX(FILTER(Market_Prices!C:C, Market_Prices!A:A>=NOW()-1))']],
    })
    data.append({
        "range": f"{sheet_name}!D16",
        "values": [['=MAX(FILTER(Market_Prices!C:C, Market_Prices!A:A>=NOW()-7))']],
    })
    data.append({
        "range": f"{sheet_name}!E16",
        "values": [['=MAX(FILTER(Market_Prices!C:C, Market_Prices!A:A>=NOW()-30))']],
    })

    # --- Grid Frequency Stats (rows 13-16, columns G-K) ---
    data.append({
        "range": f"{sheet_name}!G13",
        "values": [["⚡ GRID FREQUENCY"]],
    })
    data.append({
        "range": f"{sheet_name}!G14:K14",
        "values": [["Metric", "Current", "Last Hour Avg", "Min (24h)", "Max (24h)"]],
    })
    data.append({
        "range": f"{sheet_name}!G15",
        "values": [["Frequency (Hz)"]],
    })
    data.append({
        "range": f"{sheet_name}!H15",
        "values": [["50.00"]],  # Placeholder - needs real data
    })

    # --- Revenue Breakdown (rows 18-23) ---
    data.append({
        "range": f"{sheet_name}!A18",
        "values": [["💰 REVENUE BREAKDOWN (Last 7 Days)"]],
    })
    data.append({
        "range": f"{sheet_name}!A19:C19",
        "values": [["Revenue Stream", "£k", "% of Total"]],
    })
    data.append({
        "range": f"{sheet_name}!A20:A23",
        "values": [["Wholesale Trading"], ["Capacity Market"], ["Balancing Mechanism"], ["Ancillary Services"]],
    })
    data.append({
        "range": f"{sheet_name}!B20",
        "values": [['=SUM(VLP_Data!D:D)/1000']],
    })

    # --- Active Outages section (row 26 header, row 27 column headers, row 28 data) ---
    data.append({
        "range": f"{sheet_name}!A26",
        "values": [["⚠️ ACTIVE OUTAGES"]],
    })
    data.append({
        "range": f"{sheet_name}!A27:H27",
        "values": [["BM Unit", "Plant", "Fuel", "MW Lost", "Region", "Start Time", "End Time", "Status"]],
    })

    # --- ESO Interventions section (row 40 header, row 41 column headers, row 42 QUERY) ---
    data.append({
        "range": f"{sheet_name}!A40",
        "values": [["🔧 ESO BALANCING ACTIONS (Last 24 Hours)"]],
    })
    data.append({
        "range": f"{sheet_name}!A41:F41",
        "values": [["BM Unit", "Mode", "MW", "£/MWh", "Duration (min)", "Action Type"]],
    })
    data.append({
        "range": f"{sheet_name}!A42",
        "values": [['=QUERY(ESO_Actions!A:F,"SELECT * ORDER BY A DESC LIMIT 10",1)']],
    })

    return data


def apply_values(service, spreadsheet_id: str, sheet_name: str):
    payload = build_values_payload(sheet_name)
    body = {"valueInputOption": "USER_ENTERED", "data": payload}
    service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    print(f"   ✅ Values written to {sheet_name}")


# ---------------------------------------------------------------------
# FORMATTING: batchUpdate payloads for ALL blocks
# ---------------------------------------------------------------------

def build_formatting_requests(sheet_id: int) -> List[dict]:
    reqs = []

    # First, unmerge any existing merged cells to avoid conflicts
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

    # Column widths
    reqs.append({
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 150},
            "fields": "pixelSize"
        }
    })
    for col in range(1, 12):
        reqs.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": col, "endIndex": col+1},
                "properties": {"pixelSize": 130},
                "fields": "pixelSize"
            }
        })

    # Freeze only rows 3 (not columns to avoid merge conflicts)
    reqs.append({
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 3}},
            "fields": "gridProperties.frozenRowCount"
        }
    })

    # Title row (A1:L1) - Orange bg, white bold text
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 12},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "textFormat": {"bold": True, "fontSize": 16, "foregroundColor": WHITE},
                    "horizontalAlignment": "CENTER",
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

    # --- Market Statistics section headers (A13, G13) - Orange bg ---
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 12},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": WHITE},
                    "horizontalAlignment": "LEFT"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # --- Statistics table headers (A14:E14) - Light blue ---
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 13, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 11},
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

    # --- Revenue Breakdown header (A18) - Orange ---
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 17, "endRowIndex": 18, "startColumnIndex": 0, "endColumnIndex": 6},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": WHITE},
                    "horizontalAlignment": "LEFT"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # --- Active Outages header (A26) - Orange bold ---
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 25, "endRowIndex": 26, "startColumnIndex": 0, "endColumnIndex": 8},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": WHITE},
                    "horizontalAlignment": "LEFT"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # --- Outages column headers (A27:H27) - Light blue ---
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

    # --- ESO Actions header (A40) - Orange bold ---
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 39, "endRowIndex": 40, "startColumnIndex": 0, "endColumnIndex": 6},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": WHITE},
                    "horizontalAlignment": "LEFT"
                }
            },
            "fields": "userEnteredFormat"
        }
    })

    # --- ESO Actions column headers (A41:F41) - Light blue ---
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 40, "endRowIndex": 41, "startColumnIndex": 0, "endColumnIndex": 6},
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

    # Conditional formatting for IC flows (E10:E25)
    reqs.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 25, "startColumnIndex": 4, "endColumnIndex": 5}],
                "booleanRule": {
                    "condition": {"type": "TEXT_CONTAINS", "values": [{"userEnteredValue": "Import"}]},
                    "format": {"backgroundColor": GREEN}
                }
            },
            "index": 0
        }
    })
    reqs.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 25, "startColumnIndex": 4, "endColumnIndex": 5}],
                "booleanRule": {
                    "condition": {"type": "TEXT_CONTAINS", "values": [{"userEnteredValue": "Export"}]},
                    "format": {"backgroundColor": RED}
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
    print(f"   ✅ Formatting applied")


# ---------------------------------------------------------------------
# CHARTS: MAIN COMBO + NET MARGIN LINE
# ---------------------------------------------------------------------

def rebuild_charts(service, spreadsheet_id: str, dashboard_sheet_id: int, chart_data_sheet_id: int):
    """Delete existing charts, then create combo + net margin charts."""
    
    # Get existing charts
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing_chart_ids = []
    for sheet in ss["sheets"]:
        if sheet["properties"]["sheetId"] == dashboard_sheet_id:
            if "charts" in sheet:
                for chart in sheet["charts"]:
                    existing_chart_ids.append(chart["chartId"])
    
    # Delete existing charts
    delete_reqs = [{"deleteEmbeddedObject": {"objectId": cid}} for cid in existing_chart_ids]
    if delete_reqs:
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": delete_reqs}).execute()
        print(f"   ✅ Deleted {len(existing_chart_ids)} existing charts")

    # Create combo chart
    combo_chart_req = {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "GB Energy System Overview",
                    "basicChart": {
                        "chartType": "COMBO",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "Time"},
                            {"position": "LEFT_AXIS", "title": "MW / GW"},
                            {"position": "RIGHT_AXIS", "title": "£/MWh"}
                        ],
                        "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 0, "endColumnIndex": 1}]}}}],
                        "series": [
                            {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 3, "endColumnIndex": 4}]}}, "targetAxis": "LEFT_AXIS", "type": "LINE"},
                            {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 4, "endColumnIndex": 5}]}}, "targetAxis": "LEFT_AXIS", "type": "LINE"},
                            {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 5, "endColumnIndex": 6}]}}, "targetAxis": "LEFT_AXIS", "type": "LINE"},
                            {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 6, "endColumnIndex": 7}]}}, "targetAxis": "LEFT_AXIS", "type": "COLUMN"},
                            {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 1, "endColumnIndex": 2}]}}, "targetAxis": "RIGHT_AXIS", "type": "LINE"},
                            {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 2, "endColumnIndex": 3}]}}, "targetAxis": "RIGHT_AXIS", "type": "LINE"}
                        ],
                        "headerCount": 1
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {"sheetId": dashboard_sheet_id, "rowIndex": 12, "columnIndex": 0},
                        "widthPixels": 800,
                        "heightPixels": 400
                    }
                }
            }
        }
    }

    # Create net margin chart
    margin_chart_req = {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Portfolio Net Margin (£/MWh)",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "Time"},
                            {"position": "LEFT_AXIS", "title": "£/MWh"}
                        ],
                        "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 0, "endColumnIndex": 1}]}}}],
                        "series": [
                            {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 1, "endRowIndex": 49, "startColumnIndex": 9, "endColumnIndex": 10}]}}, "targetAxis": "LEFT_AXIS", "type": "LINE"}
                        ],
                        "headerCount": 1
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {"sheetId": dashboard_sheet_id, "rowIndex": 12, "columnIndex": 9},
                        "widthPixels": 400,
                        "heightPixels": 400
                    }
                }
            }
        }
    }

    chart_reqs = [combo_chart_req, margin_chart_req]
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": chart_reqs}).execute()
    print(f"   ✅ Created 2 charts (combo + net margin)")


# ---------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------

def setup_dashboard_v3():
    print("=" * 70)
    print("🚀 APPLYING GB ENERGY DASHBOARD V3 DESIGN")
    print("=" * 70)
    
    service = get_sheets_service()
    
    dashboard_sheet_id = ensure_sheet(service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME)
    chart_data_sheet_id = ensure_sheet(service, SPREADSHEET_ID, CHART_DATA_SHEET_NAME)
    
    print(f"✅ Dashboard sheet ID: {dashboard_sheet_id}")
    print(f"✅ Chart Data sheet ID: {chart_data_sheet_id}")
    
    print("\n--- Step 1: Writing values (labels, formulas, KPIs) ---")
    apply_values(service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME)
    
    print("\n--- Step 2: Applying formatting (colors, widths, conditional) ---")
    apply_formatting(service, SPREADSHEET_ID, dashboard_sheet_id)
    
    print("\n--- Step 3: Building charts (combo + net margin) ---")
    rebuild_charts(service, SPREADSHEET_ID, dashboard_sheet_id, chart_data_sheet_id)
    
    print("\n" + "=" * 70)
    print("✅ DASHBOARD V3 DESIGN COMPLETE")
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard_sheet_id}")
    print("=" * 70)


if __name__ == '__main__':
    setup_dashboard_v3()
