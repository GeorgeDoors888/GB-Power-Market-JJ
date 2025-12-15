#!/usr/bin/env python3
"""
Builds the 'BESS_Event' calculator sheet layout in Google Sheets.
Run this once to set up the structure, formulas, and formatting.
"""

import os
import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
# Update this path to where your JSON key file is located
SERVICE_ACCOUNT_FILE = r"/home/george/.config/google-cloud/bigquery-credentials.json"

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "BESS_Event"

# --------------------------------------------------------------------
# AUTH
# --------------------------------------------------------------------
def get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        # Fallback for testing or if user hasn't updated path yet
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
             return gspread.authorize(Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=scopes))
        print(f"⚠️ Warning: Service account file not found at {SERVICE_ACCOUNT_FILE}")
        print("Please update SERVICE_ACCOUNT_FILE in the script.")
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    return gspread.authorize(creds)

# --------------------------------------------------------------------
# BUILD LAYOUT
# --------------------------------------------------------------------
def build_layout():
    gc = get_client()
    ss = gc.open_by_key(SPREADSHEET_ID)

    try:
        ws = ss.worksheet(SHEET_NAME)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=SHEET_NAME, rows=100, cols=20)

    print(f"Building layout in '{SHEET_NAME}'...")

    # 1. Define Data (Rows)
    # [Col A, Col B, Col C]
    data = [
        ["Input / Parameter", "Value", "Note"],                                     # Row 2 (1-based in list, but we'll write to A2)
        ["Discharged MWh", 1.0, "(MWh this SP)"],                                   # Row 3
        ["Settlement Period hours", 0.5, "(0.5 for GB SP)"],                        # Row 4
        ["", "", ""],                                                               # Row 5
        ["Energy Route", "BM", "(BM, PPA, Wholesale, ESO Util, BtM Avoided)"],      # Row 6
        ["", "", ""],                                                               # Row 7
        ["BM price (£/MWh)", 220, ""],                                              # Row 8
        ["PPA price (£/MWh)", 150, ""],                                             # Row 9
        ["Wholesale price (£/MWh)", 130, ""],                                       # Row 10
        ["ESO utilisation price (£/MWh)", 180, ""],                                 # Row 11
        ["Full import cost (£/MWh)", 140, "(energy + DUoS + levies)"],              # Row 12
        ["", "", ""],                                                               # Row 13
        ["CM revenue (equiv £/MWh)", 5, "(CM £/kW/year converted to £/MWh)"],       # Row 14
        ["Availability £/MW/h", 10, "(ESO/DSO availability rate)"],                 # Row 15
        ["", "", ""],                                                               # Row 16
        ["Charging cost £/MWh (net)", 120, "(all-in cost per discharged MWh incl. efficiency)"], # Row 17
        ["", "", ""],                                                               # Row 18
        ["---- CHP parameters ----", "", ""],                                       # Row 19
        ["CHP Fuel Cost (£/MWh_el)", 80, "(Gas cost / electrical efficiency)"],     # Row 20
        ["CHP Heat Value (£/MWh_th)", 20, "(Value of heat captured)"],              # Row 21
        ["CHP Marginal Cost (£/MWh)", 60, "(Derived: Fuel - Heat Value)"],          # Row 22
        ["", "", ""],                                                               # Row 23
        ["---- SoC parameters ----", "", ""],                                       # Row 24
        ["SoC at start (MWh)", 3.0, "(state of charge at SP start)"],               # Row 25
        ["SoC minimum (MWh)", 1.0, ""],                                             # Row 26
        ["SoC maximum (MWh)", 5.0, ""],                                             # Row 27
        ["Max charge power (MW)", 2.5, ""],                                         # Row 28
        ["Max discharge power (MW)", 2.5, ""],                                      # Row 29
        ["Round-trip efficiency (%)", 0.85, ""],                                    # Row 30
        ["", "", ""],                                                               # Row 31
        ["---- Derived values ----", "", ""],                                       # Row 32
        ["Discharge power (MW)", "", ""],                                           # Row 33
        ["SoC at end (MWh)", "", ""],                                               # Row 34
        ["Energy revenue (£)", "", ""],                                             # Row 35
        ["CM revenue (£)", "", ""],                                                 # Row 36
        ["Availability revenue (£)", "", ""],                                       # Row 37
        ["Total stacked revenue (£)", "", ""],                                      # Row 38
        ["Charging cost (£)", "", ""],                                              # Row 39
        ["Margin on this 1 MWh (£)", "", ""]                                        # Row 40
    ]

    # Write data starting at A2
    ws.update(range_name="A2", values=data)

    # 2. Set Formulas
    # Note: gspread update_cell or update with raw=False interprets strings starting with = as formulas
    
    formulas = [
        ("B33", '=IF(B4=0, 0, B3/B4)'),
        ("B34", '=B25 - B3'),
        ("B35", '=B3 * SWITCH(B6, "BM", B8, "PPA", B9, "Wholesale", B10, "ESO Util", B11, "BtM Avoided", B12, 0)'),
        ("B36", '=B3 * B14'),
        ("B37", '=B33 * B15 * B4'),
        ("B38", '=SUM(B35:B37)'),
        ("B39", '=B3 * B17'),
        ("B40", '=B38 - B39')
    ]

    for cell, formula in formulas:
        ws.update_acell(cell, formula)

    # 3. Formatting (Bold Headers)
    # Using batch_update for formatting
    requests = [
        # Bold Header Row (A2:C2)
        {
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 3},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}},
                "fields": "userEnteredFormat(textFormat,backgroundColor)"
            }
        },
        # Bold Section Headers (A19, A24, A32)
        {
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": 18, "endRowIndex": 19, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat(textFormat)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": 23, "endRowIndex": 24, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat(textFormat)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": 31, "endRowIndex": 32, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat(textFormat)"
            }
        },
        # Number Formats
        # Currency (£) for Prices (B8:B17) and CHP (B20:B22) and Revenues (B35:B40)
        {
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": 7, "endRowIndex": 17, "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "£#,##0.00"}}},
                "fields": "userEnteredFormat(numberFormat)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": 19, "endRowIndex": 22, "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "£#,##0.00"}}},
                "fields": "userEnteredFormat(numberFormat)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": 34, "endRowIndex": 40, "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "£#,##0.00"}}},
                "fields": "userEnteredFormat(numberFormat)"
            }
        },
        # Percent (B30)
        {
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": 29, "endRowIndex": 30, "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
                "fields": "userEnteredFormat(numberFormat)"
            }
        }
    ]
    
    ss.batch_update({"requests": requests})

    # 4. Data Validation (Dropdown)
    # Requires gspread >= 5.0.0
    try:
        ws.add_validation(
            "B6",
            gspread.utils.ValidationCondition(
                type="ONE_OF_LIST",
                values=["BM", "PPA", "Wholesale", "ESO Util", "BtM Avoided"],
                showCustomUi=True
            )
        )
    except AttributeError:
        print("⚠️  Note: Your gspread version might be too old for add_validation. Please update gspread or add the dropdown manually.")
    except Exception as e:
        print(f"⚠️  Could not add validation: {e}")

    # Set column widths
    ws.set_basic_filter("A2:C40") # Just to reset view, actually set_column_width is better
    # gspread doesn't have direct set_column_width in all versions, using batch_update
    
    width_requests = [
        {"updateDimensionProperties": {"range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 250}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 120}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 300}, "fields": "pixelSize"}}
    ]
    ss.batch_update({"requests": width_requests})

    print("✅ BESS_Event sheet built successfully.")

if __name__ == "__main__":
    build_layout()
