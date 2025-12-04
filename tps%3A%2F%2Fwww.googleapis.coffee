tps%3A%2F%2Fwww.googleapis.com%2Fauth%2Fscript.deployments%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fscript.projects%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fscript.webapp.deploy%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive.metadata.readonly%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive.file%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fservice.management%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Flogging.read%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform&response_type=code&client_id=1072944905499-vm2v2i5dvn0a0d2o4ca36i1vge8cvbn0.apps.googleusercontent.com
You are logged in as george@upowerenergy.uk.
georgemajor@iMac GB-Power-Market-JJ %from __future__ import annotations

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# -----------------------------
# CONFIG
# -----------------------------
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SERVICE_ACCOUNT_FILE = "service-account.json"  # adjust path as needed

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DASHBOARD_TITLE = "Dashboard"

# Colours
ORANGE = {"red": 1.0, "green": 0.64, "blue": 0.3}      # #FFA24D
BLUE   = {"red": 0.2, "green": 0.404, "blue": 0.839}   # #3367D6
LIGHT_BLUE = {"red": 0.89, "green": 0.95, "blue": 0.99}  # header blue-ish
LIGHT_GREY = {"red": 0.93, "green": 0.93, "blue": 0.93}  # table body
KPI_GREY   = {"red": 0.96, "green": 0.96, "blue": 0.96}  # KPI cells


# -----------------------------
# CORE HELPERS
# -----------------------------

def get_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def ensure_dashboard_sheet(service, spreadsheet_id: str) -> int:
    """Return sheetId for Dashboard, creating if needed."""
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in ss["sheets"]:
        if sh["properties"]["title"] == DASHBOARD_TITLE:
            return sh["properties"]["sheetId"]

    # Create sheet
    body = {
        "requests": [{
            "addSheet": {
                "properties": {
                    "title": DASHBOARD_TITLE,
                    "gridProperties": {
                        "rowCount": 200,
                        "columnCount": 12,
                        "frozenRowCount": 5,
                        "frozenColumnCount": 1,
                    },
                    "tabColor": ORANGE,
                }
            }
        }]
    }
    res = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()
    return res["replies"][0]["addSheet"]["properties"]["sheetId"]


# -----------------------------
# VALUES: TEXT + FORMULAS
# -----------------------------

def write_dashboard_values(service, spreadsheet_id: str):
    """Everything that goes in cells as text/formulas for ALL blocks."""
    sheet = DASHBOARD_TITLE
    data = []

    # --- Header & filters & headline ---
    data.extend([
        {
            "range": f"{sheet}!A1",
            "values": [["⚡ GB ENERGY DASHBOARD – REAL-TIME"]],
        },
        {
            "range": f"{sheet}!A2",
            "values": [[
                '=CONCAT("Live Data: ",TEXT(NOW(),"yyyy-mm-dd HH:mm:ss"))'
            ]],
        },
        {
            "range": f"{sheet}!A3",
            "values": [["Time Range:"]],
        },
        {
            "range": f"{sheet}!B3",
            # actual drop-down list set by batchUpdate (see below), we just seed
            "values": [["1 Year"]],
        },
        {
            "range": f"{sheet}!E3",
            "values": [["Region:"]],
        },
        {
            "range": f"{sheet}!F3",
            "values": [["All GB"]],
        },
        {
            "range": f"{sheet}!A5",
            "values": [[
                '=CONCAT("⚡ Gen: ",ROUND(Live_Generation,1),'
                '" GW  |  Demand: ",ROUND(Live_Demand,1)," GW")'
            ]],
        },
    ])

    # --- KPI strip ---
    data.extend([
        {
            "range": f"{sheet}!A7",
            "values": [["Market KPIs"]],
        },
        {
            "range": f"{sheet}!F7:H7",
            "values": [[
                "📊 VLP Revenue (£ k)",
                "💰 Wholesale Avg (£/MWh)",
                "📈 Market Vol (%)",
            ]],
        },
        {
            "range": f"{sheet}!F8",
            "values": [["=AVERAGE(VLP_Data!D:D)/1000"]],
        },
        {
            "range": f"{sheet}!G8",
            "values": [["=AVERAGE(Market_Prices!C:C)"]],
        },
        {
            "range": f"{sheet}!H8",
            "values": [[
                "=STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C)"
            ]],
        },
        {
            "range": f"{sheet}!F11",
            "values": [[
                '=SPARKLINE(VLP_Data!D2:D8,{"charttype","column"})'
            ]],
        },
        {
            "range": f"{sheet}!G11",
            "values": [[
                '=SPARKLINE(Market_Prices!C2:C8,{"charttype","line"})'
            ]],
        },
        {
            "range": f"{sheet}!H11",
            "values": [[
                '=SPARKLINE(Market_Prices!C2:C8,{"charttype","column"})'
            ]],
        },
    ])

    # --- Fuel mix & ICs block ---
    data.extend([
        {
            "range": f"{sheet}!A13",
            "values": [["Fuel Mix & Interconnectors"]],
        },
        {
            "range": f"{sheet}!A14:F14",
            "values": [[
                "Fuel Type",
                "Output (MW)",
                "Share (%)",
                "Interconnector",
                "Flow (MW)",
                "Note",
            ]],
        },
    ])
    # Data rows A15:F25 are populated by pipeline → no static values here

    # --- Active Outages block ---
    data.extend([
        {
            "range": f"{sheet}!A27",
            "values": [["Active Outages"]],
        },
        {
            "range": f"{sheet}!A28:H28",
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
        },
    ])
    # A29:H40 = data, filled by pipeline

    # --- ESO Interventions block ---
    data.extend([
        {
            "range": f"{sheet}!A42",
            "values": [["ESO Interventions"]],
        },
        {
            "range": f"{sheet}!A43:F43",
            "values": [[
                "BM Unit",
                "Mode",
                "MW",
                "£/MWh",
                "Duration",
                "Action Type",
            ]],
        },
        {
            "range": f"{sheet}!A44",
            "values": [[
                '=QUERY(ESO_Actions!A:F,'
                '"select * where A<>\'\' order by C desc limit 6",1)'
            ]],
        },
    ])

    # --- Right‑side chart labels (optional, small text above charts) ---
    data.extend([
        {
            "range": f"{sheet}!G13",
            "values": [["System Load, Renewables, IC & Price"]],
        },
        {
            "range": f"{sheet}!G42",
            "values": [["Portfolio Net Margin (£/MWh)"]],
        },
    ])

    body = {"valueInputOption": "USER_ENTERED", "data": data}
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()


# -----------------------------
# FORMATTING: BATCHUPDATE REQUESTS
# -----------------------------

def build_dashboard_requests(sheet_id: int) -> list[dict]:
    """Return ALL batchUpdate requests for layout/formatting for each block."""
    requests: list[dict] = []

    # --- 0. Sheet properties: freeze rows/cols ---
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": 5,
                    "frozenColumnCount": 1,
                },
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
        }
    })

    # --- 1. Column widths (A-F wider, G-L medium) ---
    # A-F
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 0,   # A
                "endIndex": 6,     # up to F
            },
            "properties": {"pixelSize": 155},
            "fields": "pixelSize",
        }
    })
    # G-L
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 6,   # G
                "endIndex": 12,    # L
            },
            "properties": {"pixelSize": 125},
            "fields": "pixelSize",
        }
    })

    # --- 2. Merges: title, timestamp, headline, section labels ---
    # Title row A1:L1
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Timestamp row A2:L2
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Headline A5:L5
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,   # row 5
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Fuel mix label A13:F13
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 12,  # row 13
                "endRowIndex": 13,
                "startColumnIndex": 0,
                "endColumnIndex": 6,  # A-F
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Combo chart label G13:L13
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 12,
                "endRowIndex": 13,
                "startColumnIndex": 6,  # G
                "endColumnIndex": 12,   # L
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # ESO label A42:F42
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,  # row 42
                "endRowIndex": 42,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Net margin label G42:L42
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,
                "endRowIndex": 42,
                "startColumnIndex": 6,
                "endColumnIndex": 12,
            },
            "mergeType": "MERGE_ALL",
        }
    })

    # --- 3. Header bar (title row) ---
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "horizontalAlignment": "LEFT",
                    "textFormat": {
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                        "fontSize": 16,
                        "bold": True,
                    },
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Timestamp row (italic grey)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "italic": True,
                        "foregroundColor": {"red": 0.3, "green": 0.3, "blue": 0.3},
                    },
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # Headline (row 5) bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "bold": True,
                        "fontSize": 12,
                    }
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # --- 4. Time Range & Region labels (row 3) ---
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,   # row 3
                "endRowIndex": 3,
                "startColumnIndex": 0,
                "endColumnIndex": 8,  # up to H
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # --- 5. KPI strip formatting (block F7:H8, row 7–8) ---
    # KPI headers F7:H7 blue, white, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 6,   # row 7
                "endRowIndex": 7,
                "startColumnIndex": 5,  # F
                "endColumnIndex": 8,    # H
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": BLUE,
                    "horizontalAlignment": "CENTER",
                    "textFormat": {
                        "bold": True,
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                    },
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })
    # KPI values F8:H8 grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 7,   # row 8
                "endRowIndex": 8,
                "startColumnIndex": 5,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": KPI_GREY,
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })

    # --- 6. Fuel mix block formatting (rows 13–25, A–F) ---
    # Section label A13:F13
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 12,  # row 13
                "endRowIndex": 13,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })
    # Header row A14:F14 light blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 13,   # row 14
                "endRowIndex": 14,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_BLUE,
                    "horizontalAlignment": "CENTER",
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })
    # Body rows A15:F25 light grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 14,  # row 15
                "endRowIndex": 25,    # row 25
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_GREY,
                }
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # --- 7. Active Outages formatting (rows 27–40, A–H) ---
    # Section label A27:H27 bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 26,  # row 27
                "endRowIndex": 27,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })
    # Header A28:H28 grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 27,  # row 28
                "endRowIndex": 28,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.88, "green": 0.88, "blue": 0.88},
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })
    # Body A29:H40 light grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 28,  # row 29
                "endRowIndex": 40,    # row 40
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_GREY,
                }
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # --- 8. ESO Interventions formatting (rows 42–52, A–F) ---
    # Section label A42:F42 bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,  # row 42
                "endRowIndex": 42,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })
    # Header A43:F43 blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 42,  # row 43
                "endRowIndex": 43,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": BLUE,
                    "textFormat": {
                        "bold": True,
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                    },
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })
    # Body A44:F50 light grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 43,  # row 44
                "endRowIndex": 50,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_GREY,
                }
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # --- 9. Data validation for Time Range dropdown (B3) ---
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,   # row 3
                "endRowIndex": 3,
                "startColumnIndex": 1,  # B
                "endColumnIndex": 2,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "1 Year"},
                        {"userEnteredValue": "2 Years"},
                        {"userEnteredValue": "All Data"},
                        {"userEnteredValue": "All Data without COVID"},
                        {"userEnteredValue": "All Data without Ukraine"},
                    ],
                },
                "showCustomUi": True,
                "strict": True,
            },
        }
    })

    # --- 10. Conditional formatting rules ---
    # 10.1 Interconnector imports/exports (E15:E25)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 14,  # row 15
                    "endRowIndex": 25,    # row 25
                    "startColumnIndex": 4,  # E
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "← Import"}],
                    },
                    "format": {
                        "backgroundColor": {"red": 0.18, "green": 0.49, "blue": 0.20},
                        "textFormat": {
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 14,
                    "endRowIndex": 25,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "→ Export"}],
                    },
                    "format": {
                        "backgroundColor": {"red": 0.78, "green": 0.16, "blue": 0.16},
                        "textFormat": {
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })

    # 10.2 Outages > 500 MW (D29:D40 red)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 28,  # row 29
                    "endRowIndex": 40,
                    "startColumnIndex": 3,  # D
                    "endColumnIndex": 4,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "NUMBER_GREATER",
                        "values": [{"userEnteredValue": "500"}],
                    },
                    "format": {
                        "textFormat": {
                            "foregroundColor": {"red": 0.78, "green": 0.16, "blue": 0.16},
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })

    return requests


def apply_dashboard_formatting(service, spreadsheet_id: str, sheet_id: int):
    requests = build_dashboard_requests(sheet_id)
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()


# -----------------------------
# ENTRYPOINT
# -----------------------------

def setup_dashboard_layout():
    service = get_service()
    sheet_id = ensure_dashboard_sheet(service, SPREADSHEET_ID)
    write_dashboard_values(service, SPREADSHEET_ID)
    apply_dashboard_formatting(service, SPREADSHEET_ID, sheet_id)


if __name__ == "__main__":
    setup_dashboard_layout()
from __future__ import annotations

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# -----------------------------
# CONFIG
# -----------------------------
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SERVICE_ACCOUNT_FILE = "service-account.json"  # adjust path as needed

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DASHBOARD_TITLE = "Dashboard"

# Colours
ORANGE = {"red": 1.0, "green": 0.64, "blue": 0.3}      # #FFA24D
BLUE   = {"red": 0.2, "green": 0.404, "blue": 0.839}   # #3367D6
LIGHT_BLUE = {"red": 0.89, "green": 0.95, "blue": 0.99}  # header blue-ish
LIGHT_GREY = {"red": 0.93, "green": 0.93, "blue": 0.93}  # table body
KPI_GREY   = {"red": 0.96, "green": 0.96, "blue": 0.96}  # KPI cells


# -----------------------------
# CORE HELPERS
# -----------------------------

def get_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def ensure_dashboard_sheet(service, spreadsheet_id: str) -> int:
    """Return sheetId for Dashboard, creating if needed."""
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in ss["sheets"]:
        if sh["properties"]["title"] == DASHBOARD_TITLE:
            return sh["properties"]["sheetId"]

    # Create sheet
    body = {
        "requests": [{
            "addSheet": {
                "properties": {
                    "title": DASHBOARD_TITLE,
                    "gridProperties": {
                        "rowCount": 200,
                        "columnCount": 12,
                        "frozenRowCount": 5,
                        "frozenColumnCount": 1,
                    },
                    "tabColor": ORANGE,
                }
            }
        }]
    }
    res = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()
    return res["replies"][0]["addSheet"]["properties"]["sheetId"]


# -----------------------------
# VALUES: TEXT + FORMULAS
# -----------------------------

def write_dashboard_values(service, spreadsheet_id: str):
    """Everything that goes in cells as text/formulas for ALL blocks."""
    sheet = DASHBOARD_TITLE
    data = []

    # --- Header & filters & headline ---
    data.extend([
        {
            "range": f"{sheet}!A1",
            "values": [["⚡ GB ENERGY DASHBOARD – REAL-TIME"]],
        },
        {
            "range": f"{sheet}!A2",
            "values": [[
                '=CONCAT("Live Data: ",TEXT(NOW(),"yyyy-mm-dd HH:mm:ss"))'
            ]],
        },
        {
            "range": f"{sheet}!A3",
            "values": [["Time Range:"]],
        },
        {
            "range": f"{sheet}!B3",
            # actual drop-down list set by batchUpdate (see below), we just seed
            "values": [["1 Year"]],
        },
        {
            "range": f"{sheet}!E3",
            "values": [["Region:"]],
        },
        {
            "range": f"{sheet}!F3",
            "values": [["All GB"]],
        },
        {
            "range": f"{sheet}!A5",
            "values": [[
                '=CONCAT("⚡ Gen: ",ROUND(Live_Generation,1),'
                '" GW  |  Demand: ",ROUND(Live_Demand,1)," GW")'
            ]],
        },
    ])

    # --- KPI strip ---
    data.extend([
        {
            "range": f"{sheet}!A7",
            "values": [["Market KPIs"]],
        },
        {
            "range": f"{sheet}!F7:H7",
            "values": [[
                "📊 VLP Revenue (£ k)",
                "💰 Wholesale Avg (£/MWh)",
                "📈 Market Vol (%)",
            ]],
        },
        {
            "range": f"{sheet}!F8",
            "values": [["=AVERAGE(VLP_Data!D:D)/1000"]],
        },
        {
            "range": f"{sheet}!G8",
            "values": [["=AVERAGE(Market_Prices!C:C)"]],
        },
        {
            "range": f"{sheet}!H8",
            "values": [[
                "=STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C)"
            ]],
        },
        {
            "range": f"{sheet}!F11",
            "values": [[
                '=SPARKLINE(VLP_Data!D2:D8,{"charttype","column"})'
            ]],
        },
        {
            "range": f"{sheet}!G11",
            "values": [[
                '=SPARKLINE(Market_Prices!C2:C8,{"charttype","line"})'
            ]],
        },
        {
            "range": f"{sheet}!H11",
            "values": [[
                '=SPARKLINE(Market_Prices!C2:C8,{"charttype","column"})'
            ]],
        },
    ])

    # --- Fuel mix & ICs block ---
    data.extend([
        {
            "range": f"{sheet}!A13",
            "values": [["Fuel Mix & Interconnectors"]],
        },
        {
            "range": f"{sheet}!A14:F14",
            "values": [[
                "Fuel Type",
                "Output (MW)",
                "Share (%)",
                "Interconnector",
                "Flow (MW)",
                "Note",
            ]],
        },
    ])
    # Data rows A15:F25 are populated by pipeline → no static values here

    # --- Active Outages block ---
    data.extend([
        {
            "range": f"{sheet}!A27",
            "values": [["Active Outages"]],
        },
        {
            "range": f"{sheet}!A28:H28",
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
        },
    ])
    # A29:H40 = data, filled by pipeline

    # --- ESO Interventions block ---
    data.extend([
        {
            "range": f"{sheet}!A42",
            "values": [["ESO Interventions"]],
        },
        {
            "range": f"{sheet}!A43:F43",
            "values": [[
                "BM Unit",
                "Mode",
                "MW",
                "£/MWh",
                "Duration",
                "Action Type",
            ]],
        },
        {
            "range": f"{sheet}!A44",
            "values": [[
                '=QUERY(ESO_Actions!A:F,'
                '"select * where A<>\'\' order by C desc limit 6",1)'
            ]],
        },
    ])

    # --- Right‑side chart labels (optional, small text above charts) ---
    data.extend([
        {
            "range": f"{sheet}!G13",
            "values": [["System Load, Renewables, IC & Price"]],
        },
        {
            "range": f"{sheet}!G42",
            "values": [["Portfolio Net Margin (£/MWh)"]],
        },
    ])

    body = {"valueInputOption": "USER_ENTERED", "data": data}
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()


# -----------------------------
# FORMATTING: BATCHUPDATE REQUESTS
# -----------------------------

def build_dashboard_requests(sheet_id: int) -> list[dict]:
    """Return ALL batchUpdate requests for layout/formatting for each block."""
    requests: list[dict] = []

    # --- 0. Sheet properties: freeze rows/cols ---
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": 5,
                    "frozenColumnCount": 1,
                },
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
        }
    })

    # --- 1. Column widths (A-F wider, G-L medium) ---
    # A-F
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 0,   # A
                "endIndex": 6,     # up to F
            },
            "properties": {"pixelSize": 155},
            "fields": "pixelSize",
        }
    })
    # G-L
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 6,   # G
                "endIndex": 12,    # L
            },
            "properties": {"pixelSize": 125},
            "fields": "pixelSize",
        }
    })

    # --- 2. Merges: title, timestamp, headline, section labels ---
    # Title row A1:L1
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Timestamp row A2:L2
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Headline A5:L5
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,   # row 5
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Fuel mix label A13:F13
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 12,  # row 13
                "endRowIndex": 13,
                "startColumnIndex": 0,
                "endColumnIndex": 6,  # A-F
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Combo chart label G13:L13
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 12,
                "endRowIndex": 13,
                "startColumnIndex": 6,  # G
                "endColumnIndex": 12,   # L
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # ESO label A42:F42
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,  # row 42
                "endRowIndex": 42,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "mergeType": "MERGE_ALL",
        }
    })
    # Net margin label G42:L42
    requests.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,
                "endRowIndex": 42,
                "startColumnIndex": 6,
                "endColumnIndex": 12,
            },
            "mergeType": "MERGE_ALL",
        }
    })

    # --- 3. Header bar (title row) ---
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": ORANGE,
                    "horizontalAlignment": "LEFT",
                    "textFormat": {
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                        "fontSize": 16,
                        "bold": True,
                    },
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Timestamp row (italic grey)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "italic": True,
                        "foregroundColor": {"red": 0.3, "green": 0.3, "blue": 0.3},
                    },
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # Headline (row 5) bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "bold": True,
                        "fontSize": 12,
                    }
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # --- 4. Time Range & Region labels (row 3) ---
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,   # row 3
                "endRowIndex": 3,
                "startColumnIndex": 0,
                "endColumnIndex": 8,  # up to H
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # --- 5. KPI strip formatting (block F7:H8, row 7–8) ---
    # KPI headers F7:H7 blue, white, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 6,   # row 7
                "endRowIndex": 7,
                "startColumnIndex": 5,  # F
                "endColumnIndex": 8,    # H
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": BLUE,
                    "horizontalAlignment": "CENTER",
                    "textFormat": {
                        "bold": True,
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                    },
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })
    # KPI values F8:H8 grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 7,   # row 8
                "endRowIndex": 8,
                "startColumnIndex": 5,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": KPI_GREY,
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })

    # --- 6. Fuel mix block formatting (rows 13–25, A–F) ---
    # Section label A13:F13
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 12,  # row 13
                "endRowIndex": 13,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })
    # Header row A14:F14 light blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 13,   # row 14
                "endRowIndex": 14,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_BLUE,
                    "horizontalAlignment": "CENTER",
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })
    # Body rows A15:F25 light grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 14,  # row 15
                "endRowIndex": 25,    # row 25
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_GREY,
                }
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # --- 7. Active Outages formatting (rows 27–40, A–H) ---
    # Section label A27:H27 bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 26,  # row 27
                "endRowIndex": 27,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })
    # Header A28:H28 grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 27,  # row 28
                "endRowIndex": 28,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.88, "green": 0.88, "blue": 0.88},
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })
    # Body A29:H40 light grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 28,  # row 29
                "endRowIndex": 40,    # row 40
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_GREY,
                }
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # --- 8. ESO Interventions formatting (rows 42–52, A–F) ---
    # Section label A42:F42 bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,  # row 42
                "endRowIndex": 42,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })
    # Header A43:F43 blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 42,  # row 43
                "endRowIndex": 43,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": BLUE,
                    "textFormat": {
                        "bold": True,
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                    },
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })
    # Body A44:F50 light grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 43,  # row 44
                "endRowIndex": 50,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": LIGHT_GREY,
                }
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # --- 9. Data validation for Time Range dropdown (B3) ---
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,   # row 3
                "endRowIndex": 3,
                "startColumnIndex": 1,  # B
                "endColumnIndex": 2,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "1 Year"},
                        {"userEnteredValue": "2 Years"},
                        {"userEnteredValue": "All Data"},
                        {"userEnteredValue": "All Data without COVID"},
                        {"userEnteredValue": "All Data without Ukraine"},
                    ],
                },
                "showCustomUi": True,
                "strict": True,
            },
        }
    })

    # --- 10. Conditional formatting rules ---
    # 10.1 Interconnector imports/exports (E15:E25)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 14,  # row 15
                    "endRowIndex": 25,    # row 25
                    "startColumnIndex": 4,  # E
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "← Import"}],
                    },
                    "format": {
                        "backgroundColor": {"red": 0.18, "green": 0.49, "blue": 0.20},
                        "textFormat": {
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 14,
                    "endRowIndex": 25,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "→ Export"}],
                    },
                    "format": {
                        "backgroundColor": {"red": 0.78, "green": 0.16, "blue": 0.16},
                        "textFormat": {
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })

    # 10.2 Outages > 500 MW (D29:D40 red)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 28,  # row 29
                    "endRowIndex": 40,
                    "startColumnIndex": 3,  # D
                    "endColumnIndex": 4,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "NUMBER_GREATER",
                        "values": [{"userEnteredValue": "500"}],
                    },
                    "format": {
                        "textFormat": {
                            "foregroundColor": {"red": 0.78, "green": 0.16, "blue": 0.16},
                            "bold": True,
                        },
                    },
                },
            },
            "index": 0,
        }
    })

    return requests


def apply_dashboard_formatting(service, spreadsheet_id: str, sheet_id: int):
    requests = build_dashboard_requests(sheet_id)
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()


# -----------------------------
# ENTRYPOINT
# -----------------------------

def setup_dashboard_layout():
    service = get_service()
    sheet_id = ensure_dashboard_sheet(service, SPREADSHEET_ID)
    write_dashboard_values(service, SPREADSHEET_ID)
    apply_dashboard_formatting(service, SPREADSHEET_ID, sheet_id)


if __name__ == "__main__":
    setup_dashboard_layout()
What this gives you (block‑by‑block)
Header block
mergeCells + repeatCell on rows 1–2 + 5.
Filter block
Row 3 labels + setDataValidation on B3.
KPI block
Values in F7:H8 + sparks in F11:H11 + blue header + grey cells.
Fuel mix & IC block
Section label A13, header A14:F14, body formatting A15:F25, conditional formats for imports/exports.
Active outages block
Section label A27, header A28:H28, body A29:H40, conditional format for D>500.
ESO interventions block
Section label A42, header A43:F43, body A44:F50 (QUERY spill area).
Chart labels block (right‑side)
G13 and G42 merged across G:L.
This is just the layout/formatting. On top of this you already have / will have:
BigQuery → Sheets loaders for Chart Data, VLP_Data, Market_Prices, ESO_Actions, etc.
buildDashboard() chart creation (either via Apps Script or your earlier Python addChart code).
If you want, I can now bolt the combo chart addChart request and the net margin chart onto this same script so literally everything on the Dashboard, including charts, comes from batchUpdate too."""
GB ENERGY DASHBOARD V3 – Layout + KPI + Charts

- Creates/ensures Dashboard sheet.
- Writes labels & formulas.
- Applies formatting (all batchUpdate payloads).
- Adds:
    1) Combo chart (system + prices + BESS/VLP/ESO) from Chart Data!A1:J49
    2) Net Margin line chart from Chart Data!A1:A49 & J1:J49
"""

from __future__ import annotations

from typing import List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

SERVICE_ACCOUNT_FILE = "service-account.json"  # adjust as needed
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

DASHBOARD_SHEET_NAME = "Dashboard"
CHART_DATA_SHEET_NAME = "Chart Data"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Colours
ORANGE = {"red": 1.0, "green": 0.64, "blue": 0.3}        # #FFA24D
BLUE = {"red": 0.2, "green": 0.404, "blue": 0.839}       # #3367D6
LIGHT_BLUE = {"red": 0.89, "green": 0.95, "blue": 0.99}  # ~#E3F2FD
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
# VALUES: LABELS + FORMULAS (INCLUDING KPI + NET MARGIN KPI)
# ---------------------------------------------------------------------

def build_values_payload(sheet_name: str) -> List[dict]:
    data: List[dict] = []

    # --- Header & filters & gen/demand headline ---
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
    data.append({
        "range": f"{sheet_name}!A3",
        "values": [["Time Range"]],
    })
    data.append({
        "range": f"{sheet_name}!B3",
        "values": [["1 Year"]],  # default
    })
    data.append({
        "range": f"{sheet_name}!E3",
        "values": [["Region"]],
    })
    data.append({
        "range": f"{sheet_name}!F3",
        "values": [["All GB"]],
    })
    data.append({
        "range": f"{sheet_name}!A5",
        "values": [[
            '=CONCAT("⚡ Gen: ",ROUND(Live_Generation,1)," GW  |  Demand: ",'
            'ROUND(Live_Demand,1)," GW")'
        ]],
    })

    # --- KPI strip (NOW includes Net Margin in col I) ---
    data.append({
        "range": f"{sheet_name}!F9:I9",
        "values": [[
            "📊 VLP Revenue (£ k)",
            "💰 Wholesale Avg (£/MWh)",
            "📈 Market Vol (%)",
            "Net Margin (£/MWh)",
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
    # Net Margin: average of Chart Data column J, ignoring blanks
    data.append({
        "range": f"{sheet_name}!I10",
        "values": [[
            "=AVERAGE(FILTER('Chart Data'!J:J, NOT(ISBLANK('Chart Data'!J:J))))"
        ]],
    })

    # Sparklines for KPI trend (F11:I11)
    data.append({
        "range": f"{sheet_name}!F11",
        "values": [[
            '=SPARKLINE(VLP_Data!D2:D8,{"charttype","column"})'
        ]],
    })
    data.append({
        "range": f"{sheet_name}!G11",
        "values": [[
            '=SPARKLINE(Market_Prices!C2:C8,{"charttype","line"})'
        ]],
    })
    data.append({
        "range": f"{sheet_name}!H11",
        "values": [[
            '=SPARKLINE(Market_Prices!C2:C8,{"charttype","column"})'
        ]],
    })
    # Net margin sparkline
    data.append({
        "range": f"{sheet_name}!I11",
        "values": [[
            "=SPARKLINE('Chart Data'!J2:J49)"
        ]],
    })

    # --- Fuel mix & interconnectors header (row 9) ---
    data.append({
        "range": f"{sheet_name}!A9:E9",
        "values": [[
            "Fuel Type",
            "GW",
            "%",
            "Interconnector",
            "Flow (MW)",
        ]],
    })

    # --- Active Outages header (row 27) ---
    data.append({
        "range": f"{sheet_name}!A27:H27",
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

    # --- ESO Interventions header + query (rows 42–43) ---
    data.append({
        "range": f"{sheet_name}!A42:F42",
        "values": [[
            "BM Unit",
            "Mode",
            "MW",
            "£/MWh",
            "Duration",
            "Action Type",
        ]],
    })
    data.append({
        "range": f"{sheet_name}!A43",
        "values": [[
            '=QUERY(ESO_Actions!A:F,'
            '"select * where A<>\'\' order by C desc limit 6",1)'
        ]],
    })

    return data


def apply_values(service, spreadsheet_id: str, sheet_name: str):
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": build_values_payload(sheet_name),
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()


# ---------------------------------------------------------------------
# FORMATTING: batchUpdate payloads for ALL blocks (with KPI F–I)
# ---------------------------------------------------------------------

def build_formatting_requests(sheet_id: int) -> List[dict]:
    requests: List[dict] = []

    # Freeze top 5 rows + column A
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": 5,
                    "frozenColumnCount": 1,
                },
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
        }
    })

    # Column widths: A-F wider, G-L medium
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": 6,   # A..F
            },
            "properties": {"pixelSize": 150},
            "fields": "pixelSize",
        }
    })
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 6,
                "endIndex": 12,  # G..L
            },
            "properties": {"pixelSize": 140},
            "fields": "pixelSize",
        }
    })

    # Title row A1:L1
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
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

    # Timestamp row A2:L2 – italic
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "italic": True,
                        "foregroundColor": BLACK,
                    },
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # Row 3 labels (Time Range / Region) bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat.bold)",
        }
    })

    # Gen vs Demand row A5 – bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat.bold)",
        }
    })

    # -----------------------------------------------------------------
    # KPI STRIP (F–I, rows 9–11)
    # -----------------------------------------------------------------

    # KPI header row F9:I9 – blue, white text, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 8,
                "endRowIndex": 9,
                "startColumnIndex": 5,   # F
                "endColumnIndex": 9,     # F..I
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

    # KPI values F10:I10 – KPI grey, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 9,
                "endRowIndex": 10,
                "startColumnIndex": 5,
                "endColumnIndex": 9,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": KPI_GREY,
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat.bold)",
        }
    })

    # KPI sparklines F11:I11 – center alignment
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 10,
                "endRowIndex": 11,
                "startColumnIndex": 5,
                "endColumnIndex": 9,
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment)",
        }
    })

    # -----------------------------------------------------------------
    # FUEL MIX & INTERCONNECTORS (A9:E25)
    # -----------------------------------------------------------------

    # Header row A9:E9
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

    # Body A10:E25
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 9,
                "endRowIndex": 25,
                "startColumnIndex": 0,
                "endColumnIndex": 5,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # ACTIVE OUTAGES (A27:H40)
    # -----------------------------------------------------------------
    header_grey = {"red": 0.88, "green": 0.88, "blue": 0.88}

    # Header A27:H27
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 26,
                "endRowIndex": 27,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": header_grey,
                    "textFormat": {"bold": True},
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Body A28:H40
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 27,
                "endRowIndex": 40,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # ESO INTERVENTIONS (A42:F48)
    # -----------------------------------------------------------------

    # Header A42:F42 – blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,
                "endRowIndex": 42,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
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

    # Body A43:F48 – grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 42,
                "endRowIndex": 48,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # CONDITIONAL FORMATTING – IC imports/exports (Fuel mix col E)
    # -----------------------------------------------------------------

    # "← Import" → green bold
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,
                    "endRowIndex": 25,
                    "startColumnIndex": 4,  # E
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "← Import"}],
                    },
                    "format": {
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {
                                "red": 0.18, "green": 0.49, "blue": 0.20
                            },
                        }
                    },
                }
            },
            "index": 0,
        }
    })

    # "→ Export" → red bold
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,
                    "endRowIndex": 25,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "→ Export"}],
                    },
                    "format": {
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {
                                "red": 0.78, "green": 0.16, "blue": 0.16
                            },
                        }
                    },
                }
            },
            "index": 0,
        }
    })

    return requests


def apply_formatting(service, spreadsheet_id: str, sheet_id: int):
    requests = build_formatting_requests(sheet_id)
    if not requests:
        return
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()


# ---------------------------------------------------------------------
# CHARTS: MAIN COMBO + NET MARGIN LINE
# ---------------------------------------------------------------------

def rebuild_charts(service, spreadsheet_id: str,
                   dashboard_sheet_id: int,
                   chart_data_sheet_id: int):
    """
    Remove existing charts on Dashboard and add:
      1) Combo chart (A1:J49)
      2) Net Margin line chart (A vs J)
    """
    ss = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets(properties,sheets.charts)"
    ).execute()

    delete_requests: List[dict] = []
    for sh in ss["sheets"]:
        props = sh["properties"]
        sid = props["sheetId"]
        if sid != dashboard_sheet_id:
            continue
        for ch in sh.get("charts", []):
            delete_requests.append({
                "deleteEmbeddedObject": {"objectId": ch["chartId"]}
            })

    # Combo chart spec (system + prices + flex)
    combo_spec = {
        "title": "System Load, Renewables, IC, BESS/VLP & Prices",
        "basicChart": {
            "chartType": "COMBO",
            "legendPosition": "RIGHT_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Time / SP"},
                {"position": "LEFT_AXIS", "title": "MW"},
                {"position": "RIGHT_AXIS", "title": "£/MWh"},
            ],
            "domains": [{
                "domain": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": 49,
                            "startColumnIndex": 0,  # A
                            "endColumnIndex": 1,
                        }]
                    }
                }
            }],
            "series": [
                # 0: DA Price (B) – right axis
                {
                    "targetAxis": "RIGHT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 1,  # B
                                "endColumnIndex": 2,
                            }]
                        }
                    },
                },
                # 1: Imbalance Price (C)
                {
                    "targetAxis": "RIGHT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 2,  # C
                                "endColumnIndex": 3,
                            }]
                        }
                    },
                },
                # 2–4: MW areas (D,E,F)
                *[
                    {
                        "targetAxis": "LEFT_AXIS",
                        "type": "AREA",
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": chart_data_sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 49,
                                    "startColumnIndex": col,
                                    "endColumnIndex": col + 1,
                                }]
                            }
                        },
                    }
                    for col in (3, 4, 5)
                ],
                # 5–7: overlays (G,H,I)
                *[
                    {
                        "targetAxis": "LEFT_AXIS",
                        "type": "LINE",
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": chart_data_sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 49,
                                    "startColumnIndex": col,
                                    "endColumnIndex": col + 1,
                                }]
                            }
                        },
                    }
                    for col in (6, 7, 8)
                ],
            ],
        },
    }

    combo_chart_req = {
        "addChart": {
            "chart": {
                "spec": combo_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 12,   # row 13
                            "columnIndex": 6  # col G
                        }
                    }
                }
            }
        }
    }

    # Net margin chart spec (Time vs J)
    margin_spec = {
        "title": "Portfolio Net Margin (£/MWh)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Time / SP"},
                {"position": "LEFT_AXIS", "title": "£/MWh"},
            ],
            "domains": [{
                "domain": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": 49,
                            "startColumnIndex": 0,  # A (Time)
                            "endColumnIndex": 1,
                        }]
                    }
                }
            }],
            "series": [
                {
                    "targetAxis": "LEFT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 9,  # J (Net Margin)
                                "endColumnIndex": 10,
                            }]
                        }
                    },
                }
            ],
        },
    }

    margin_chart_req = {
        "addChart": {
            "chart": {
                "spec": margin_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 41,  # row 42
                            "columnIndex": 6  # col G
                        }
                    }
                }
            }
        }
    }

    requests = delete_requests + [combo_chart_req, margin_chart_req]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()


# ---------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------

def setup_dashboard_v3():
    service = get_sheets_service()
    dashboard_sheet_id = ensure_sheet(
        service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME
    )

    apply_values(service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME)
    apply_formatting(service, SPREADSHEET_ID, dashboard_sheet_id)

    chart_data_sheet_id = get_sheet_id_by_title(
        service, SPREADSHEET_ID, CHART_DATA_SHEET_NAME
    )
    if chart_data_sheet_id is None:
        raise RuntimeError(f"Chart data sheet '{CHART_DATA_SHEET_NAME}' not found.")

    rebuild_charts(
        service,
        SPREADSHEET_ID,
        dashboard_sheet_id,
        chart_data_sheet_id,
    )


if __name__ == "__main__":
    setup_dashboard_v3()
"""
GB ENERGY DASHBOARD V3 – Layout + KPI + Charts

- Creates/ensures Dashboard sheet.
- Writes labels & formulas.
- Applies formatting (all batchUpdate payloads).
- Adds:
    1) Combo chart (system + prices + BESS/VLP/ESO) from Chart Data!A1:J49
    2) Net Margin line chart from Chart Data!A1:A49 & J1:J49
"""

from __future__ import annotations

from typing import List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

SERVICE_ACCOUNT_FILE = "service-account.json"  # adjust as needed
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

DASHBOARD_SHEET_NAME = "Dashboard"
CHART_DATA_SHEET_NAME = "Chart Data"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Colours
ORANGE = {"red": 1.0, "green": 0.64, "blue": 0.3}        # #FFA24D
BLUE = {"red": 0.2, "green": 0.404, "blue": 0.839}       # #3367D6
LIGHT_BLUE = {"red": 0.89, "green": 0.95, "blue": 0.99}  # ~#E3F2FD
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
# VALUES: LABELS + FORMULAS (INCLUDING KPI + NET MARGIN KPI)
# ---------------------------------------------------------------------

def build_values_payload(sheet_name: str) -> List[dict]:
    data: List[dict] = []

    # --- Header & filters & gen/demand headline ---
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
    data.append({
        "range": f"{sheet_name}!A3",
        "values": [["Time Range"]],
    })
    data.append({
        "range": f"{sheet_name}!B3",
        "values": [["1 Year"]],  # default
    })
    data.append({
        "range": f"{sheet_name}!E3",
        "values": [["Region"]],
    })
    data.append({
        "range": f"{sheet_name}!F3",
        "values": [["All GB"]],
    })
    data.append({
        "range": f"{sheet_name}!A5",
        "values": [[
            '=CONCAT("⚡ Gen: ",ROUND(Live_Generation,1)," GW  |  Demand: ",'
            'ROUND(Live_Demand,1)," GW")'
        ]],
    })

    # --- KPI strip (NOW includes Net Margin in col I) ---
    data.append({
        "range": f"{sheet_name}!F9:I9",
        "values": [[
            "📊 VLP Revenue (£ k)",
            "💰 Wholesale Avg (£/MWh)",
            "📈 Market Vol (%)",
            "Net Margin (£/MWh)",
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
    # Net Margin: average of Chart Data column J, ignoring blanks
    data.append({
        "range": f"{sheet_name}!I10",
        "values": [[
            "=AVERAGE(FILTER('Chart Data'!J:J, NOT(ISBLANK('Chart Data'!J:J))))"
        ]],
    })

    # Sparklines for KPI trend (F11:I11)
    data.append({
        "range": f"{sheet_name}!F11",
        "values": [[
            '=SPARKLINE(VLP_Data!D2:D8,{"charttype","column"})'
        ]],
    })
    data.append({
        "range": f"{sheet_name}!G11",
        "values": [[
            '=SPARKLINE(Market_Prices!C2:C8,{"charttype","line"})'
        ]],
    })
    data.append({
        "range": f"{sheet_name}!H11",
        "values": [[
            '=SPARKLINE(Market_Prices!C2:C8,{"charttype","column"})'
        ]],
    })
    # Net margin sparkline
    data.append({
        "range": f"{sheet_name}!I11",
        "values": [[
            "=SPARKLINE('Chart Data'!J2:J49)"
        ]],
    })

    # --- Fuel mix & interconnectors header (row 9) ---
    data.append({
        "range": f"{sheet_name}!A9:E9",
        "values": [[
            "Fuel Type",
            "GW",
            "%",
            "Interconnector",
            "Flow (MW)",
        ]],
    })

    # --- Active Outages header (row 27) ---
    data.append({
        "range": f"{sheet_name}!A27:H27",
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

    # --- ESO Interventions header + query (rows 42–43) ---
    data.append({
        "range": f"{sheet_name}!A42:F42",
        "values": [[
            "BM Unit",
            "Mode",
            "MW",
            "£/MWh",
            "Duration",
            "Action Type",
        ]],
    })
    data.append({
        "range": f"{sheet_name}!A43",
        "values": [[
            '=QUERY(ESO_Actions!A:F,'
            '"select * where A<>\'\' order by C desc limit 6",1)'
        ]],
    })

    return data


def apply_values(service, spreadsheet_id: str, sheet_name: str):
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": build_values_payload(sheet_name),
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()


# ---------------------------------------------------------------------
# FORMATTING: batchUpdate payloads for ALL blocks (with KPI F–I)
# ---------------------------------------------------------------------

def build_formatting_requests(sheet_id: int) -> List[dict]:
    requests: List[dict] = []

    # Freeze top 5 rows + column A
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": 5,
                    "frozenColumnCount": 1,
                },
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
        }
    })

    # Column widths: A-F wider, G-L medium
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": 6,   # A..F
            },
            "properties": {"pixelSize": 150},
            "fields": "pixelSize",
        }
    })
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 6,
                "endIndex": 12,  # G..L
            },
            "properties": {"pixelSize": 140},
            "fields": "pixelSize",
        }
    })

    # Title row A1:L1
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
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

    # Timestamp row A2:L2 – italic
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "italic": True,
                        "foregroundColor": BLACK,
                    },
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # Row 3 labels (Time Range / Region) bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat.bold)",
        }
    })

    # Gen vs Demand row A5 – bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat.bold)",
        }
    })

    # -----------------------------------------------------------------
    # KPI STRIP (F–I, rows 9–11)
    # -----------------------------------------------------------------

    # KPI header row F9:I9 – blue, white text, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 8,
                "endRowIndex": 9,
                "startColumnIndex": 5,   # F
                "endColumnIndex": 9,     # F..I
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

    # KPI values F10:I10 – KPI grey, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 9,
                "endRowIndex": 10,
                "startColumnIndex": 5,
                "endColumnIndex": 9,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": KPI_GREY,
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat.bold)",
        }
    })

    # KPI sparklines F11:I11 – center alignment
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 10,
                "endRowIndex": 11,
                "startColumnIndex": 5,
                "endColumnIndex": 9,
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment)",
        }
    })

    # -----------------------------------------------------------------
    # FUEL MIX & INTERCONNECTORS (A9:E25)
    # -----------------------------------------------------------------

    # Header row A9:E9
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

    # Body A10:E25
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 9,
                "endRowIndex": 25,
                "startColumnIndex": 0,
                "endColumnIndex": 5,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # ACTIVE OUTAGES (A27:H40)
    # -----------------------------------------------------------------
    header_grey = {"red": 0.88, "green": 0.88, "blue": 0.88}

    # Header A27:H27
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 26,
                "endRowIndex": 27,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": header_grey,
                    "textFormat": {"bold": True},
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Body A28:H40
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 27,
                "endRowIndex": 40,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # ESO INTERVENTIONS (A42:F48)
    # -----------------------------------------------------------------

    # Header A42:F42 – blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,
                "endRowIndex": 42,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
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

    # Body A43:F48 – grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 42,
                "endRowIndex": 48,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # CONDITIONAL FORMATTING – IC imports/exports (Fuel mix col E)
    # -----------------------------------------------------------------

    # "← Import" → green bold
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,
                    "endRowIndex": 25,
                    "startColumnIndex": 4,  # E
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "← Import"}],
                    },
                    "format": {
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {
                                "red": 0.18, "green": 0.49, "blue": 0.20
                            },
                        }
                    },
                }
            },
            "index": 0,
        }
    })

    # "→ Export" → red bold
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,
                    "endRowIndex": 25,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "→ Export"}],
                    },
                    "format": {
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {
                                "red": 0.78, "green": 0.16, "blue": 0.16
                            },
                        }
                    },
                }
            },
            "index": 0,
        }
    })

    return requests


def apply_formatting(service, spreadsheet_id: str, sheet_id: int):
    requests = build_formatting_requests(sheet_id)
    if not requests:
        return
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()


# ---------------------------------------------------------------------
# CHARTS: MAIN COMBO + NET MARGIN LINE
# ---------------------------------------------------------------------

def rebuild_charts(service, spreadsheet_id: str,
                   dashboard_sheet_id: int,
                   chart_data_sheet_id: int):
    """
    Remove existing charts on Dashboard and add:
      1) Combo chart (A1:J49)
      2) Net Margin line chart (A vs J)
    """
    ss = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets(properties,sheets.charts)"
    ).execute()

    delete_requests: List[dict] = []
    for sh in ss["sheets"]:
        props = sh["properties"]
        sid = props["sheetId"]
        if sid != dashboard_sheet_id:
            continue
        for ch in sh.get("charts", []):
            delete_requests.append({
                "deleteEmbeddedObject": {"objectId": ch["chartId"]}
            })

    # Combo chart spec (system + prices + flex)
    combo_spec = {
        "title": "System Load, Renewables, IC, BESS/VLP & Prices",
        "basicChart": {
            "chartType": "COMBO",
            "legendPosition": "RIGHT_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Time / SP"},
                {"position": "LEFT_AXIS", "title": "MW"},
                {"position": "RIGHT_AXIS", "title": "£/MWh"},
            ],
            "domains": [{
                "domain": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": 49,
                            "startColumnIndex": 0,  # A
                            "endColumnIndex": 1,
                        }]
                    }
                }
            }],
            "series": [
                # 0: DA Price (B) – right axis
                {
                    "targetAxis": "RIGHT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 1,  # B
                                "endColumnIndex": 2,
                            }]
                        }
                    },
                },
                # 1: Imbalance Price (C)
                {
                    "targetAxis": "RIGHT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 2,  # C
                                "endColumnIndex": 3,
                            }]
                        }
                    },
                },
                # 2–4: MW areas (D,E,F)
                *[
                    {
                        "targetAxis": "LEFT_AXIS",
                        "type": "AREA",
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": chart_data_sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 49,
                                    "startColumnIndex": col,
                                    "endColumnIndex": col + 1,
                                }]
                            }
                        },
                    }
                    for col in (3, 4, 5)
                ],
                # 5–7: overlays (G,H,I)
                *[
                    {
                        "targetAxis": "LEFT_AXIS",
                        "type": "LINE",
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": chart_data_sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 49,
                                    "startColumnIndex": col,
                                    "endColumnIndex": col + 1,
                                }]
                            }
                        },
                    }
                    for col in (6, 7, 8)
                ],
            ],
        },
    }

    combo_chart_req = {
        "addChart": {
            "chart": {
                "spec": combo_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 12,   # row 13
                            "columnIndex": 6  # col G
                        }
                    }
                }
            }
        }
    }

    # Net margin chart spec (Time vs J)
    margin_spec = {
        "title": "Portfolio Net Margin (£/MWh)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Time / SP"},
                {"position": "LEFT_AXIS", "title": "£/MWh"},
            ],
            "domains": [{
                "domain": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": 49,
                            "startColumnIndex": 0,  # A (Time)
                            "endColumnIndex": 1,
                        }]
                    }
                }
            }],
            "series": [
                {
                    "targetAxis": "LEFT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 9,  # J (Net Margin)
                                "endColumnIndex": 10,
                            }]
                        }
                    },
                }
            ],
        },
    }

    margin_chart_req = {
        "addChart": {
            "chart": {
                "spec": margin_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 41,  # row 42
                            "columnIndex": 6  # col G
                        }
                    }
                }
            }
        }
    }

    requests = delete_requests + [combo_chart_req, margin_chart_req]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()


# ---------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------

def setup_dashboard_v3():
    service = get_sheets_service()
    dashboard_sheet_id = ensure_sheet(
        service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME
    )

    apply_values(service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME)
    apply_formatting(service, SPREADSHEET_ID, dashboard_sheet_id)

    chart_data_sheet_id = get_sheet_id_by_title(
        service, SPREADSHEET_ID, CHART_DATA_SHEET_NAME
    )
    if chart_data_sheet_id is None:
        raise RuntimeError(f"Chart data sheet '{CHART_DATA_SHEET_NAME}' not found.")

    rebuild_charts(
        service,
        SPREADSHEET_ID,
        dashboard_sheet_id,
        chart_data_sheet_id,
    )


if __name__ == "__main__":
    setup_dashboard_v3()
"""
GB ENERGY DASHBOARD V3 – Layout + KPI + Charts

- Creates/ensures Dashboard sheet.
- Writes labels & formulas.
- Applies formatting (all batchUpdate payloads).
- Adds:
    1) Combo chart (system + prices + BESS/VLP/ESO) from Chart Data!A1:J49
    2) Net Margin line chart from Chart Data!A1:A49 & J1:J49
"""

from __future__ import annotations

from typing import List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

SERVICE_ACCOUNT_FILE = "service-account.json"  # adjust as needed
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

DASHBOARD_SHEET_NAME = "Dashboard"
CHART_DATA_SHEET_NAME = "Chart Data"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Colours
ORANGE = {"red": 1.0, "green": 0.64, "blue": 0.3}        # #FFA24D
BLUE = {"red": 0.2, "green": 0.404, "blue": 0.839}       # #3367D6
LIGHT_BLUE = {"red": 0.89, "green": 0.95, "blue": 0.99}  # ~#E3F2FD
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
# VALUES: LABELS + FORMULAS (INCLUDING KPI + NET MARGIN KPI)
# ---------------------------------------------------------------------

def build_values_payload(sheet_name: str) -> List[dict]:
    data: List[dict] = []

    # --- Header & filters & gen/demand headline ---
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
    data.append({
        "range": f"{sheet_name}!A3",
        "values": [["Time Range"]],
    })
    data.append({
        "range": f"{sheet_name}!B3",
        "values": [["1 Year"]],  # default
    })
    data.append({
        "range": f"{sheet_name}!E3",
        "values": [["Region"]],
    })
    data.append({
        "range": f"{sheet_name}!F3",
        "values": [["All GB"]],
    })
    data.append({
        "range": f"{sheet_name}!A5",
        "values": [[
            '=CONCAT("⚡ Gen: ",ROUND(Live_Generation,1)," GW  |  Demand: ",'
            'ROUND(Live_Demand,1)," GW")'
        ]],
    })

    # --- KPI strip (NOW includes Net Margin in col I) ---
    data.append({
        "range": f"{sheet_name}!F9:I9",
        "values": [[
            "📊 VLP Revenue (£ k)",
            "💰 Wholesale Avg (£/MWh)",
            "📈 Market Vol (%)",
            "Net Margin (£/MWh)",
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
    # Net Margin: average of Chart Data column J, ignoring blanks
    data.append({
        "range": f"{sheet_name}!I10",
        "values": [[
            "=AVERAGE(FILTER('Chart Data'!J:J, NOT(ISBLANK('Chart Data'!J:J))))"
        ]],
    })

    # Sparklines for KPI trend (F11:I11)
    data.append({
        "range": f"{sheet_name}!F11",
        "values": [[
            '=SPARKLINE(VLP_Data!D2:D8,{"charttype","column"})'
        ]],
    })
    data.append({
        "range": f"{sheet_name}!G11",
        "values": [[
            '=SPARKLINE(Market_Prices!C2:C8,{"charttype","line"})'
        ]],
    })
    data.append({
        "range": f"{sheet_name}!H11",
        "values": [[
            '=SPARKLINE(Market_Prices!C2:C8,{"charttype","column"})'
        ]],
    })
    # Net margin sparkline
    data.append({
        "range": f"{sheet_name}!I11",
        "values": [[
            "=SPARKLINE('Chart Data'!J2:J49)"
        ]],
    })

    # --- Fuel mix & interconnectors header (row 9) ---
    data.append({
        "range": f"{sheet_name}!A9:E9",
        "values": [[
            "Fuel Type",
            "GW",
            "%",
            "Interconnector",
            "Flow (MW)",
        ]],
    })

    # --- Active Outages header (row 27) ---
    data.append({
        "range": f"{sheet_name}!A27:H27",
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

    # --- ESO Interventions header + query (rows 42–43) ---
    data.append({
        "range": f"{sheet_name}!A42:F42",
        "values": [[
            "BM Unit",
            "Mode",
            "MW",
            "£/MWh",
            "Duration",
            "Action Type",
        ]],
    })
    data.append({
        "range": f"{sheet_name}!A43",
        "values": [[
            '=QUERY(ESO_Actions!A:F,'
            '"select * where A<>\'\' order by C desc limit 6",1)'
        ]],
    })

    return data


def apply_values(service, spreadsheet_id: str, sheet_name: str):
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": build_values_payload(sheet_name),
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()


# ---------------------------------------------------------------------
# FORMATTING: batchUpdate payloads for ALL blocks (with KPI F–I)
# ---------------------------------------------------------------------

def build_formatting_requests(sheet_id: int) -> List[dict]:
    requests: List[dict] = []

    # Freeze top 5 rows + column A
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {
                    "frozenRowCount": 5,
                    "frozenColumnCount": 1,
                },
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
        }
    })

    # Column widths: A-F wider, G-L medium
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": 6,   # A..F
            },
            "properties": {"pixelSize": 150},
            "fields": "pixelSize",
        }
    })
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 6,
                "endIndex": 12,  # G..L
            },
            "properties": {"pixelSize": 140},
            "fields": "pixelSize",
        }
    })

    # Title row A1:L1
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
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

    # Timestamp row A2:L2 – italic
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "italic": True,
                        "foregroundColor": BLACK,
                    },
                }
            },
            "fields": "userEnteredFormat(textFormat)",
        }
    })

    # Row 3 labels (Time Range / Region) bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat.bold)",
        }
    })

    # Gen vs Demand row A5 – bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 12,
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(textFormat.bold)",
        }
    })

    # -----------------------------------------------------------------
    # KPI STRIP (F–I, rows 9–11)
    # -----------------------------------------------------------------

    # KPI header row F9:I9 – blue, white text, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 8,
                "endRowIndex": 9,
                "startColumnIndex": 5,   # F
                "endColumnIndex": 9,     # F..I
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

    # KPI values F10:I10 – KPI grey, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 9,
                "endRowIndex": 10,
                "startColumnIndex": 5,
                "endColumnIndex": 9,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": KPI_GREY,
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat.bold)",
        }
    })

    # KPI sparklines F11:I11 – center alignment
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 10,
                "endRowIndex": 11,
                "startColumnIndex": 5,
                "endColumnIndex": 9,
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment)",
        }
    })

    # -----------------------------------------------------------------
    # FUEL MIX & INTERCONNECTORS (A9:E25)
    # -----------------------------------------------------------------

    # Header row A9:E9
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

    # Body A10:E25
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 9,
                "endRowIndex": 25,
                "startColumnIndex": 0,
                "endColumnIndex": 5,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # ACTIVE OUTAGES (A27:H40)
    # -----------------------------------------------------------------
    header_grey = {"red": 0.88, "green": 0.88, "blue": 0.88}

    # Header A27:H27
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 26,
                "endRowIndex": 27,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": header_grey,
                    "textFormat": {"bold": True},
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Body A28:H40
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 27,
                "endRowIndex": 40,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # ESO INTERVENTIONS (A42:F48)
    # -----------------------------------------------------------------

    # Header A42:F42 – blue
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 41,
                "endRowIndex": 42,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
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

    # Body A43:F48 – grey
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 42,
                "endRowIndex": 48,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "cell": {
                "userEnteredFormat": {"backgroundColor": LIGHT_GREY}
            },
            "fields": "userEnteredFormat(backgroundColor)",
        }
    })

    # -----------------------------------------------------------------
    # CONDITIONAL FORMATTING – IC imports/exports (Fuel mix col E)
    # -----------------------------------------------------------------

    # "← Import" → green bold
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,
                    "endRowIndex": 25,
                    "startColumnIndex": 4,  # E
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "← Import"}],
                    },
                    "format": {
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {
                                "red": 0.18, "green": 0.49, "blue": 0.20
                            },
                        }
                    },
                }
            },
            "index": 0,
        }
    })

    # "→ Export" → red bold
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,
                    "endRowIndex": 25,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{"userEnteredValue": "→ Export"}],
                    },
                    "format": {
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {
                                "red": 0.78, "green": 0.16, "blue": 0.16
                            },
                        }
                    },
                }
            },
            "index": 0,
        }
    })

    return requests


def apply_formatting(service, spreadsheet_id: str, sheet_id: int):
    requests = build_formatting_requests(sheet_id)
    if not requests:
        return
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()


# ---------------------------------------------------------------------
# CHARTS: MAIN COMBO + NET MARGIN LINE
# ---------------------------------------------------------------------

def rebuild_charts(service, spreadsheet_id: str,
                   dashboard_sheet_id: int,
                   chart_data_sheet_id: int):
    """
    Remove existing charts on Dashboard and add:
      1) Combo chart (A1:J49)
      2) Net Margin line chart (A vs J)
    """
    ss = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets(properties,sheets.charts)"
    ).execute()

    delete_requests: List[dict] = []
    for sh in ss["sheets"]:
        props = sh["properties"]
        sid = props["sheetId"]
        if sid != dashboard_sheet_id:
            continue
        for ch in sh.get("charts", []):
            delete_requests.append({
                "deleteEmbeddedObject": {"objectId": ch["chartId"]}
            })

    # Combo chart spec (system + prices + flex)
    combo_spec = {
        "title": "System Load, Renewables, IC, BESS/VLP & Prices",
        "basicChart": {
            "chartType": "COMBO",
            "legendPosition": "RIGHT_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Time / SP"},
                {"position": "LEFT_AXIS", "title": "MW"},
                {"position": "RIGHT_AXIS", "title": "£/MWh"},
            ],
            "domains": [{
                "domain": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": 49,
                            "startColumnIndex": 0,  # A
                            "endColumnIndex": 1,
                        }]
                    }
                }
            }],
            "series": [
                # 0: DA Price (B) – right axis
                {
                    "targetAxis": "RIGHT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 1,  # B
                                "endColumnIndex": 2,
                            }]
                        }
                    },
                },
                # 1: Imbalance Price (C)
                {
                    "targetAxis": "RIGHT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 2,  # C
                                "endColumnIndex": 3,
                            }]
                        }
                    },
                },
                # 2–4: MW areas (D,E,F)
                *[
                    {
                        "targetAxis": "LEFT_AXIS",
                        "type": "AREA",
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": chart_data_sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 49,
                                    "startColumnIndex": col,
                                    "endColumnIndex": col + 1,
                                }]
                            }
                        },
                    }
                    for col in (3, 4, 5)
                ],
                # 5–7: overlays (G,H,I)
                *[
                    {
                        "targetAxis": "LEFT_AXIS",
                        "type": "LINE",
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": chart_data_sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 49,
                                    "startColumnIndex": col,
                                    "endColumnIndex": col + 1,
                                }]
                            }
                        },
                    }
                    for col in (6, 7, 8)
                ],
            ],
        },
    }

    combo_chart_req = {
        "addChart": {
            "chart": {
                "spec": combo_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 12,   # row 13
                            "columnIndex": 6  # col G
                        }
                    }
                }
            }
        }
    }

    # Net margin chart spec (Time vs J)
    margin_spec = {
        "title": "Portfolio Net Margin (£/MWh)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Time / SP"},
                {"position": "LEFT_AXIS", "title": "£/MWh"},
            ],
            "domains": [{
                "domain": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": chart_data_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": 49,
                            "startColumnIndex": 0,  # A (Time)
                            "endColumnIndex": 1,
                        }]
                    }
                }
            }],
            "series": [
                {
                    "targetAxis": "LEFT_AXIS",
                    "type": "LINE",
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": chart_data_sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": 49,
                                "startColumnIndex": 9,  # J (Net Margin)
                                "endColumnIndex": 10,
                            }]
                        }
                    },
                }
            ],
        },
    }

    margin_chart_req = {
        "addChart": {
            "chart": {
                "spec": margin_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": dashboard_sheet_id,
                            "rowIndex": 41,  # row 42
                            "columnIndex": 6  # col G
                        }
                    }
                }
            }
        }
    }

    requests = delete_requests + [combo_chart_req, margin_chart_req]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()


# ---------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------

def setup_dashboard_v3():
    service = get_sheets_service()
    dashboard_sheet_id = ensure_sheet(
        service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME
    )

    apply_values(service, SPREADSHEET_ID, DASHBOARD_SHEET_NAME)
    apply_formatting(service, SPREADSHEET_ID, dashboard_sheet_id)

    chart_data_sheet_id = get_sheet_id_by_title(
        service, SPREADSHEET_ID, CHART_DATA_SHEET_NAME
    )
    if chart_data_sheet_id is None:
        raise RuntimeError(f"Chart data sheet '{CHART_DATA_SHEET_NAME}' not found.")

    rebuild_charts(
        service,
        SPREADSHEET_ID,
        dashboard_sheet_id,
        chart_data_sheet_id,
    )


if __name__ == "__main__":
    setup_dashboard_v3()
// Code.gs

const DASHBOARD_SHEET_NAME = 'Dashboard';
const DNO_MAP_SHEET_NAME = 'DNO_Map';
const DNO_TARGET_CELL = 'F3';  // where selected DNO goes

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ GB Energy')
    .addItem('DNO Map Selector', 'showDnoMap')
    .addToUi();
}

function showDnoMap() {
  const html = HtmlService
    .createTemplateFromFile('DnoMap')
    .evaluate()
    .setTitle('Select DNO')
    .setWidth(500);
  SpreadsheetApp.getUi().showSidebar(html);
}

// Read DNO locations from DNO_Map sheet
function getDnoLocations() {
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(DNO_MAP_SHEET_NAME);
  if (!sheet) return [];

  const values = sheet.getDataRange().getValues();
  const header = values.shift();  // first row
  const idxCode = header.indexOf('DNO_CODE');
  const idxName = header.indexOf('DNO_NAME');
  const idxLat = header.indexOf('LAT');
  const idxLng = header.indexOf('LNG');

  return values
    .filter(r => r[idxCode])
    .map(r => ({
      code: r[idxCode],
      name: r[idxName],
      lat: Number(r[idxLat]),
      lng: Number(r[idxLng]),
    }));
}

// Called from HTML when a user clicks a marker
function selectDno(code) {
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  if (!dash) return;
  dash.getRange(DNO_TARGET_CELL).setValue(code);
}
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <base target="_top">
    <style>
      html, body {
        height: 100%;
        margin: 0;
        padding: 0;
      }
      #map {
        height: 100%;
        min-height: 450px;
      }
      #legend {
        font-family: Arial, sans-serif;
        font-size: 12px;
        padding: 6px;
      }
    </style>
  </head>
  <body>
    <div id="map"></div>

    <script>
      let map;

      function initMap() {
        google.script.run.withSuccessHandler(function(dnos) {
          map = new google.maps.Map(document.getElementById('map'), {
            center: {lat: 54.5, lng: -3.5},  // GB centre-ish
            zoom: 5.5
          });

          dnos.forEach(function(dno) {
            const marker = new google.maps.Marker({
              position: {lat: dno.lat, lng: dno.lng},
              map: map,
              title: dno.name
            });

            const infowindow = new google.maps.InfoWindow({
              content: '<b>' + dno.name + '</b><br/>Code: ' + dno.code
            });

            marker.addListener('click', function() {
              infowindow.open(map, marker);
              google.script.run.selectDno(dno.code);
            });
          });
        }).getDnoLocations();
      }
    </script>

    <!-- Replace YOUR_API_KEY with your Maps JS API key -->
    <script async defer
      src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap">
    </script>
  </body>
</html>
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <base target="_top">
    <style>
      html, body {
        height: 100%;
        margin: 0;
        padding: 0;
      }
      #map {
        height: 100%;
        min-height: 450px;
      }
      #legend {
        font-family: Arial, sans-serif;
        font-size: 12px;
        padding: 6px;
      }
    </style>
  </head>
  <body>
    <div id="map"></div>

    <script>
      let map;

      function initMap() {
        google.script.run.withSuccessHandler(function(dnos) {
          map = new google.maps.Map(document.getElementById('map'), {
            center: {lat: 54.5, lng: -3.5},  // GB centre-ish
            zoom: 5.5
          });

          dnos.forEach(function(dno) {
            const marker = new google.maps.Marker({
              position: {lat: dno.lat, lng: dno.lng},
              map: map,
              title: dno.name
            });

            const infowindow = new google.maps.InfoWindow({
              content: '<b>' + dno.name + '</b><br/>Code: ' + dno.code
            });

            marker.addListener('click', function() {
              infowindow.open(map, marker);
              google.script.run.selectDno(dno.code);
            });
          });
        }).getDnoLocations();
      }
    </script>

    <!-- Replace YOUR_API_KEY with your Maps JS API key -->
    <script async defer
      src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap">
    </script>
  </body>
</html>
Add a DNO_Map sheet with header row:
A	B	C	D
DNO_CODE	DNO_NAME	LAT	LNG
…and one row per DNO (with centre coordinates).
Reload the spreadsheet → the “⚡ GB Energy → DNO Map Selector” menu appears.
Clicking “DNO Map Selector” opens the map; clicking a DNO marker sets Dashboard!F3 to that DNO code.
2.3. Using the DNO in your Python / BigQuery layer
In your Python BigQuery script that populates Chart Data and other tabs, just read Dashboard!F3 first:def get_selected_dno(service) -> str | None:
    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{DASHBOARD_SHEET_NAME}!F3"
    ).execute()
    values = res.get("values", [])
    if not values or not values[0]:
        return None
    return values[0][0] or None
selected_dno = get_selected_dno(sheets_service)

if selected_dno and selected_dno != "All GB":
    where_clause = "WHERE dno_id = @dno"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("dno", "STRING", selected_dno)]
    )
else:
    where_clause = ""
    job_config = bigquery.QueryJobConfig()

sql = f"""
  SELECT ...
  FROM `project.analytics.chart_data_intraday`
  {where_clause}
  ORDER BY time_local
"""
rows = client.query(sql, job_config=job_config).result()
/**
 * @OnlyCurrentDoc
 *
 * This script creates a real-time energy dashboard in Google Sheets,
 * pulling data from Google BigQuery.
 */

// ---------------------------------------------------
// CONFIGURATION
// ---------------------------------------------------
const SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8";
const DASHBOARD_SHEET_NAME = "Dashboard_V2";
const CHART_DATA_SHEET_NAME = "Chart_Data_V2";
const GCP_PROJECT_ID = "inner-cinema-476211-u9";


// ---------------------------------------------------
// TRIGGERS & MENU
// ---------------------------------------------------

/**
 * Creates a custom menu in the spreadsheet UI.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('⚡ Real-Time Dashboard')
    .addItem('1. Setup Sheets (Run Once)', 'setupSheetsAndFormatting')
    .addItem('2. Manual Refresh All Data', 'refreshAllData')
    .addToUi();
}

/**
 * Runs automatically when a user changes the value of any cell.
 * @param {object} e The event object.
 */
function onEdit(e) {
  const range = e.range;
  const sheet = range.getSheet();
  // If the edited cell is B3 on the main dashboard, refresh the chart data.
  if (sheet.getName() === DASHBOARD_SHEET_NAME && range.getA1Notation() === 'B3') {
    const timeRange = e.value;
    refreshChartData(timeRange);
  }
}


// ---------------------------------------------------
// INITIAL SETUP
// ---------------------------------------------------

/**
 * Sets up the necessary sheets and their initial formatting.
 * This is a lighter version that should not time out.
 */
function setupSheetsAndFormatting() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Starting sheet setup...');
  setupDashboardSheet();
  setupChartDataSheet();
  SpreadsheetApp.getActiveSpreadsheet().toast('Sheet setup complete. You can now run the manual refresh.');
  SpreadsheetApp.getUi().alert('Sheet setup is complete. Please run "2. Manual Refresh All Data" from the menu to load data.');
}

/**
 * Creates and formats the main dashboard sheet.
 */
function setupDashboardSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  if (sheet) {
    sheet.clear();
  } else {
    sheet = ss.insertSheet(DASHBOARD_SHEET_NAME);
  }
  sheet.getRange("A1").setValue("GB Energy Dashboard V2");
  sheet.getRange("A3").setValue("Time Range:");
  
  const cell = sheet.getRange('B3');
  const rule = SpreadsheetApp.newDataValidation()
     .requireValueInList(['Last 24 Hours', 'Last 7 Days', 'Last 30 Days'])
     .build();
  cell.setDataValidation(rule);
  cell.setValue('Last 24 Hours');
}

/**
 * Creates the hidden sheet for chart data.
 */
function setupChartDataSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CHART_DATA_SHEET_NAME);
  if (sheet) {
    sheet.clear();
  } else {
    sheet = ss.insertSheet(CHART_DATA_SHEET_NAME);
    sheet.hideSheet();
  }
}


// ---------------------------------------------------
// DATA REFRESH LOGIC
// ---------------------------------------------------

/**
 * Main function to refresh all data on the dashboard.
 */
function refreshAllData() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Starting data refresh...');
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(DASHBOARD_SHEET_NAME);
  const timeRange = sheet.getRange("B3").getValue();
  refreshChartData(timeRange);
  SpreadsheetApp.getActiveSpreadsheet().toast('Data refresh complete!');
}

/**
 * Fetches data for the main chart from BigQuery based on the selected time range.
 * @param {string} timeRange The selected time range (e.g., "Last 24 Hours").
 */
function refreshChartData(timeRange) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CHART_DATA_SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert(`Error: Sheet "${CHART_DATA_SHEET_NAME}" not found. Please run the setup first.`);
    return;
  }

  const query = buildChartQuery(timeRange);
  try {
    const data = runBigQuery(query);
    sheet.clear();
    if (data && data.length > 1) { // Check for header + data rows
      sheet.getRange(1, 1, data.length, data[0].length).setValues(data);
      Logger.log(`Successfully loaded ${data.length - 1} rows into ${CHART_DATA_SHEET_NAME}.`);
      createOrUpdateChart();
    } else {
      Logger.log("No data returned from BigQuery for the chart.");
      SpreadsheetApp.getActiveSpreadsheet().toast('No data returned from BigQuery.');
    }
  } catch (e) {
    Logger.log("Failed to run BigQuery query: " + e.toString());
    SpreadsheetApp.getUi().alert("Error fetching data from BigQuery. Check logs for details.");
  }
}


// ---------------------------------------------------
// BIGQUERY
// ---------------------------------------------------

/**
 * Builds the SQL query for the main chart.
 * @param {string} timeRange The selected time range.
 * @returns {string} The BigQuery SQL query.
 */
function buildChartQuery(timeRange) {
  let interval;
  switch (timeRange) {
    case 'Last 7 Days':
      interval = 7;
      break;
    case 'Last 30 Days':
      interval = 30;
      break;
    case 'Last 24 Hours':
    default:
      interval = 1;
      break;
  }

  return `
    SELECT
      CAST(DATETIME_TRUNC(settlementDate, HOUR) AS STRING) as time,
      SUM(CASE WHEN fuelType = 'WIND' THEN quantity ELSE 0 END) as wind,
      SUM(CASE WHEN fuelType = 'CCGT' THEN quantity ELSE 0 END) as ccgt,
      SUM(CASE WHEN fuelType = 'NUCLEAR' THEN quantity ELSE 0 END) as nuclear
    FROM
      \`${GCP_PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_iris\`
    WHERE
      settlementDate >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ${interval} DAY)
    GROUP BY
      1
    ORDER BY
      1
  `;
}

/**
 * Executes a BigQuery query.
 * @param {string} query The SQL query.
 * @returns {Array<Array<string>>} The query results as a 2D array.
 */
function runBigQuery(query) {
  const request = { query: query, useLegacySql: false };
  let queryResults = BigQuery.Jobs.query(request, GCP_PROJECT_ID);
  const jobId = queryResults.jobReference.jobId;

  let sleepTimeMs = 500;
  while (!queryResults.jobComplete) {
    Utilities.sleep(sleepTimeMs);
    sleepTimeMs *= 2;
    queryResults = BigQuery.Jobs.getQueryResults(GCP_PROJECT_ID, jobId);
  }

  if (!queryResults.rows) {
    return [];
  }

  const schema = queryResults.schema.fields.map(field => field.name);
  const data = queryResults.rows.map(row => row.f.map(cell => cell.v));
  
  return [schema, ...data];
}


// ---------------------------------------------------
// CHARTING
// ---------------------------------------------------

/**
 * Creates or updates the main dashboard chart.
 */
function createOrUpdateChart() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashboardSheet = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  const dataSheet = ss.getSheetByName(CHART_DATA_SHEET_NAME);

  const dataRange = dataSheet.getDataRange();
  
  // Remove existing charts before creating a new one
  const charts = dashboardSheet.getCharts();
  charts.forEach(chart => dashboardSheet.removeChart(chart));

  const chart = dashboardSheet.newChart()
    .setChartType(Charts.ChartType.COMBO)
    .addRange(dataRange)
    .setOption('title', 'Generation by Fuel Type')
    .setOption('hAxis', { title: 'Time' })
    .setOption('vAxis', { title: 'Generation (MW)' })
    .setPosition(5, 5, 0, 0) // Anchor to cell E5
    .build();

  dashboardSheet.insertChart(chart);
} CREATE OR REPLACE VIEW `project.analytics.dno_kpi` AS
WITH boundaries AS (
  SELECT
    dno_code,
    dno_name,
    -- If you already have a GEOGRAPHY column, use it directly.
    -- Otherwise convert from GeoJSON string:
    ST_CENTROID(
      ST_GEOGFROMGEOJSON(geojson, make_valid => TRUE)
    ) AS centroid
  FROM `project.geo.dno_boundaries`
),
centers AS (
  SELECT
    dno_code,
    dno_name,
    ST_Y(centroid) AS lat,
    ST_X(centroid) AS lng
  FROM boundaries
),
metrics AS (
  SELECT
    dno_id AS dno_code,
    SAFE_DIVIDE(SUM(net_margin_gbp), NULLIF(SUM(mwh), 0))
      AS net_margin_gbp_per_mwh,
    SUM(mwh)              AS total_mwh,
    SUM(ppa_revenue_gbp)  AS ppa_revenue_gbp,
    SUM(energy_cost_gbp
        + duos_gbp
        + tnous_gbp
        + bsous_gbp
        + other_network_gbp) AS total_cost_gbp
  FROM `project.btm.mpan_hh_demand`
  -- OPTIONAL: filter on date / time range if you only care about recent periods
  -- WHERE settlement_date >= DATE_SUB(CURRENT_DATE("Europe/London"), INTERVAL 30 DAY)
  GROUP BY dno_id
)

SELECT
  c.dno_code,
  c.dno_name,
  c.lat,
  c.lng,
  m.net_margin_gbp_per_mwh,
  m.total_mwh,
  m.ppa_revenue_gbp,
  m.total_cost_gbp
FROM centers c
LEFT JOIN metrics m
  ON c.dno_code = m.dno_code;
CREATE OR REPLACE VIEW `project.analytics.dno_kpi` AS
WITH boundaries AS (
  SELECT
    dno_code,
    dno_name,
    -- If you already have a GEOGRAPHY column, use it directly.
    -- Otherwise convert from GeoJSON string:
    ST_CENTROID(
      ST_GEOGFROMGEOJSON(geojson, make_valid => TRUE)
    ) AS centroid
  FROM `project.geo.dno_boundaries`
),
centers AS (
  SELECT
    dno_code,
    dno_name,
    ST_Y(centroid) AS lat,
    ST_X(centroid) AS lng
  FROM boundaries
),
metrics AS (
  SELECT
    dno_id AS dno_code,
    SAFE_DIVIDE(SUM(net_margin_gbp), NULLIF(SUM(mwh), 0))
      AS net_margin_gbp_per_mwh,
    SUM(mwh)              AS total_mwh,
    SUM(ppa_revenue_gbp)  AS ppa_revenue_gbp,
    SUM(energy_cost_gbp
        + duos_gbp
        + tnous_gbp
        + bsous_gbp
        + other_network_gbp) AS total_cost_gbp
  FROM `project.btm.mpan_hh_demand`
  -- OPTIONAL: filter on date / time range if you only care about recent periods
  -- WHERE settlement_date >= DATE_SUB(CURRENT_DATE("Europe/London"), INTERVAL 30 DAY)
  GROUP BY dno_id
)

SELECT
  c.dno_code,
  c.dno_name,
  c.lat,
  c.lng,
  m.net_margin_gbp_per_mwh,
  m.total_mwh,
  m.ppa_revenue_gbp,
  m.total_cost_gbp
FROM centers c
LEFT JOIN metrics m
  ON c.dno_code = m.dno_code;
This gives you one row per DNO with:
geometry‑derived centroid (lat/lng) from NG GeoJSON;
DNO‑level KPI metrics from your HH BTM data.
2. Python – load DNO KPIs into DNO_Map sheet
You already have a write_dno_map_data() helper; now we just need to fetch rows from the new view and pass them in.
2.1. Fetch DNO KPI rows from BigQueryfrom typing import List, Dict
from google.cloud import bigquery

PROJECT_ID = "your-gcp-project-id"  # set appropriately

def fetch_dno_kpi_rows() -> List[Dict]:
    client = bigquery.Client(project=PROJECT_ID)
    sql = """
      SELECT
        dno_code,
        dno_name,
        lat,
        lng,
        net_margin_gbp_per_mwh,
        total_mwh,
        ppa_revenue_gbp,
        total_cost_gbp
      FROM `project.analytics.dno_kpi`
    """
    rows = client.query(sql).result()

    out: List[Dict] = []
    for r in rows:
        out.append({
            "dno_code": r.dno_code,
            "name": r.dno_name,
            "lat": float(r.lat),
            "lng": float(r.lng),
            "net_margin": float(r.net_margin_gbp_per_mwh or 0.0),
            "total_mwh": float(r.total_mwh or 0.0),
            "ppa_revenue": float(r.ppa_revenue_gbp or 0.0),
            "total_cost": float(r.total_cost_gbp or 0.0),
        })
    return out
Hook DNO KPIs into the Dashboard KPI strip
We’ll make the dashboard aware of the selected DNO (from Dashboard!F3) and pull KPI values out of DNO_Map with a simple lookup.
I’ll assume:
Dashboard!F3 = currently selected DNO code (from the map sidebar or a dropdown).
DNO_Map!A:A = DNO Code; E:E = Net Margin, F:F = Total MWh, etc.
3.1. Add “Selected DNO Net Margin” KPI
Add this to your values payload (or type it directly and then automate later):
Label in J9:
Dashboard!J9 = "Selected DNO Net Margin (£/MWh)"
Value in J10 (using XLOOKUP):
Dashboard!J10 =
=IF(
  $F$3="All GB",
  I10,  /* fall back to All GB net margin KPI */
  XLOOKUP(
    $F$3,
    DNO_Map!$A:$A,
    DNO_Map!$E:$E,
    NA()
  )
)
XLOOKUP is now native in Google Sheets, so this is safe to use. 
Google Help
+2
Google Help
+2
Optionally, you can add:
J11 sparkline for that DNO vs others is more complex, but you can do something like a small bar chart of all DNO net margins in another chart.
3.2. Add “Selected DNO Volume” KPI
Same pattern:
Label K9:
Dashboard!K9 = "Selected DNO Volume (MWh)"
Value K10:
Dashboard!K10 =
=IF(
  $F$3="All GB",
  SUM('Chart Data'!D:D)/2,  /* example All GB energy proxy, optional */
  XLOOKUP(
    $F$3,
    DNO_Map!$A:$A,
    DNO_Map!$F:$F,
    0
  )
)
That gives you:
All‑GB KPIs in F10:I10 (revenues, prices, vol, All‑GB net margin).
Selected DNO KPIs in J10:K10 pulled directly from the DNO KPI table, which itself is built on the National Grid GeoJSON DNO boundaries.
4. Map uses the same KPI data
Because the sidebar map (DnoMapSidebar.html) reads from DNO_Map, the markers can show actual KPI numbers from BigQuery:
// in DnoMapSidebar.html placeMarkers(dnoList):

const infowindow = new google.maps.InfoWindow({
  content:
    '<b>' + dno.name + '</b><br>' +
    'Code: ' + dno.code + '<br>' +
    'Net Margin: ' + dno.metric.toFixed(2) + ' £/MWh'
});
// in DnoMapSidebar.html placeMarkers(dnoList):

const infowindow = new google.maps.InfoWindow({
  content:
    '<b>' + dno.name + '</b><br>' +
    'Code: ' + dno.code + '<br>' +
    'Net Margin: ' + dno.metric.toFixed(2) + ' £/MWh'
});
You just tweak getDnoLocations() in Apps Script to return metric: row[4] (net margin col E), which we already did.
So the story is:
GeoJSON → GEOGRAPHY → centroid (BigQuery)
BigQuery → DNO KPIs per boundary (analytics.dno_kpi)
Python → DNO_Map sheet with KPIs & centroids
Apps Script → map markers + DNO selection (writes to F3)
Dashboard → KPIs & charts filter by DNO and show DNO‑level net margin / volume
If you like, next step I can give you one end‑to‑end refresh function in Python that:
Reads the selected DNO from the sheet.
Builds chart_data_intraday with an optional @dno_filter.
Refreshes Chart Data, DNO_Map, and then calls setup_dashboard_v3() so the entire dashboard (KPIs + charts + map) is always consistent with NG’s DNO geojson.