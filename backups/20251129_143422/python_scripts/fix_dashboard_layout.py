#!/usr/bin/env python3
"""
fix_dashboard_layout.py
-----------------------
Complete cleanup and proper layout fix:
1. Clear all conflicting automation outputs
2. Set up proper chart zones without interference
3. Fix Top 12 Outages section (NOT Top 50+)
4. Remove ESO/MARKET/FORECAST sections
5. Ensure date pickers work correctly
6. Fix all formatting consistency issues
"""

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from gspread_formatting import (
    format_cell_range, CellFormat, Color, TextFormat,
    set_column_widths, set_row_height
)
try:
    from gspread_formatting import HorizontalAlignment
except ImportError:
    class HorizontalAlignment:
        CENTER = 'CENTER'
        LEFT = 'LEFT'
        RIGHT = 'RIGHT'

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD = "Dashboard"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

print("=" * 70)
print("🔧 FIXING DASHBOARD LAYOUT & REMOVING CONFLICTS")
print("=" * 70)
print()

# Connect
creds = Credentials.from_service_account_file("inner-cinema-credentials.json", scopes=SCOPES)
gc = gspread.authorize(creds)
service = build('sheets', 'v4', credentials=creds)
sh = gc.open_by_key(SPREADSHEET_ID)
dash = sh.worksheet(DASHBOARD)

# Get sheet ID
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id = None
for sheet in sheet_metadata.get('sheets', []):
    if sheet['properties']['title'] == DASHBOARD:
        sheet_id = sheet['properties']['sheetId']
        break

print("✅ Connected to Dashboard sheet")

# ---------------------------------------------------------------------------
# COLORS
# ---------------------------------------------------------------------------
COLORS = {
    "orange": Color(1.0, 0.55, 0.0),
    "blue": Color(0.0, 0.30, 0.59),
    "green": Color(0.26, 0.63, 0.28),
    "red": Color(0.90, 0.22, 0.21),
    "gray": Color(0.96, 0.96, 0.96),
    "white": Color(1, 1, 1),
    "chart_zone": Color(1.0, 0.95, 0.90)
}

# ---------------------------------------------------------------------------
# STEP 1: CLEAR ALL PROBLEM ROWS (30-100)
# ---------------------------------------------------------------------------
print("🧹 Clearing conflicting rows 30-100...")
dash.batch_clear(["A30:Z100"])
print("   ✅ Cleared rows 30-100")

# ---------------------------------------------------------------------------
# STEP 2: SET UP PROPER CHART ZONES
# ---------------------------------------------------------------------------
print("📊 Setting up chart zones...")

chart_zone_fmt = CellFormat(
    backgroundColor=COLORS["chart_zone"],
    textFormat=TextFormat(bold=True, italic=True, foregroundColor=COLORS["orange"], fontSize=11),
    horizontalAlignment=HorizontalAlignment.CENTER
)

# Zone 1: Fuel Mix Pie (A20:F40)
dash.update([["📊 CHART: Fuel Mix (Doughnut/Pie) - A20:F40"]], "A20")
format_cell_range(dash, "A20:F20", chart_zone_fmt)
dash.update([["[Chart will be inserted here via Apps Script]"]], "A22")

# Zone 2: Interconnector Flows (G20:L40)
dash.update([["📊 CHART: Interconnector Flows (Multi-line) - G20:L40"]], "G20")
format_cell_range(dash, "G20:L20", chart_zone_fmt)
dash.update([["[Chart will be inserted here via Apps Script]"]], "G22")

# Zone 3: Demand vs Generation (A45:F65)
dash.update([["📊 CHART: Demand vs Generation 48h (Stacked Area) - A45:F65"]], "A45")
format_cell_range(dash, "A45:F45", chart_zone_fmt)
dash.update([["[Chart will be inserted here via Apps Script]"]], "A47")

# Zone 4: System Prices (G45:L65)
dash.update([["📊 CHART: System Prices SSP/SBP/MID (3-Line) - G45:L65"]], "G45")
format_cell_range(dash, "G45:L45", chart_zone_fmt)
dash.update([["[Chart will be inserted here via Apps Script]"]], "G47")

# Zone 5: Financial KPIs (A70:L88)
dash.update([["📊 CHART: Financial KPIs BOD/BID/Imbalance (Column) - A70:L88"]], "A70")
format_cell_range(dash, "A70:L70", chart_zone_fmt)
dash.update([["[Chart will be inserted here via Apps Script]"]], "A72")

print("   ✅ All 5 chart zones marked")

# ---------------------------------------------------------------------------
# STEP 3: TOP 12 OUTAGES SECTION (A90:H105)
# ---------------------------------------------------------------------------
print("⚠️  Creating Top 12 Outages section...")

# Header
dash.update([["⚠️  TOP 12 ACTIVE OUTAGES (by MW Unavailable)"]], "A90")
outage_hdr_fmt = CellFormat(
    backgroundColor=COLORS["red"],
    textFormat=TextFormat(bold=True, foregroundColor=COLORS["white"], fontSize=12),
    horizontalAlignment=HorizontalAlignment.CENTER
)
format_cell_range(dash, "A90:H90", outage_hdr_fmt)

# Column headers
outage_cols = [["BM Unit", "Plant", "Fuel", "MW Lost", "Region", "Start Time", "End Time", "Status"]]
dash.update(outage_cols, "A91")
outage_col_hdr = CellFormat(
    backgroundColor=Color(1.0, 0.85, 0.85),  # Light red
    textFormat=TextFormat(bold=True)
)
format_cell_range(dash, "A91:H91", outage_col_hdr)

# Add note about automation
dash.update([["(Auto-updated every 10 minutes by update_outages_enhanced.py)"]], "A92")
note_fmt = CellFormat(
    textFormat=TextFormat(italic=True, fontSize=9, foregroundColor=COLORS["gray"])
)
format_cell_range(dash, "A92", note_fmt)

print("   ✅ Top 12 Outages section created (A90:H105)")

# ---------------------------------------------------------------------------
# STEP 4: FIX DATE PICKERS (H3, J3) - Force valid date validation
# ---------------------------------------------------------------------------
print("📅 Fixing date pickers...")

# Use Google Sheets API to set proper date validation
requests = []

# H3 - Start Date
requests.append({
    "setDataValidation": {
        "range": {
            "sheetId": sheet_id,
            "startRowIndex": 2,
            "endRowIndex": 3,
            "startColumnIndex": 7,  # H
            "endColumnIndex": 8
        },
        "rule": {
            "condition": {
                "type": "DATE_IS_VALID",
                "values": []
            },
            "showCustomUi": True,
            "strict": False,
            "inputMessage": "Select a start date"
        }
    }
})

# J3 - End Date
requests.append({
    "setDataValidation": {
        "range": {
            "sheetId": sheet_id,
            "startRowIndex": 2,
            "endRowIndex": 3,
            "startColumnIndex": 9,  # J
            "endColumnIndex": 10
        },
        "rule": {
            "condition": {
                "type": "DATE_IS_VALID",
                "values": []
            },
            "showCustomUi": True,
            "strict": False,
            "inputMessage": "Select an end date"
        }
    }
})

body = {"requests": requests}
service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body=body
).execute()

# Update labels and add sample dates
dash.update([["📅 Start Date:"]], "G3")
dash.update([["📅 End Date:"]], "I3")
dash.update([["2025-11-01"]], "H3")  # Sample date
dash.update([["2025-11-29"]], "J3")  # Sample date

print("   ✅ Date pickers fixed (H3, J3)")

# ---------------------------------------------------------------------------
# STEP 5: REMOVE ANY REMAINING ESO/MARKET/FORECAST HEADERS
# ---------------------------------------------------------------------------
print("🗑️  Removing unwanted sections...")
# Already cleared in step 1, but double-check rows 100-120
dash.batch_clear(["A100:Z120"])
print("   ✅ Removed any ESO/Market/Forecast sections")

# ---------------------------------------------------------------------------
# STEP 6: ENSURE FILTER BAR IS PROPERLY FORMATTED
# ---------------------------------------------------------------------------
print("🔍 Verifying filter bar...")
filter_fmt = CellFormat(
    backgroundColor=COLORS["gray"],
    textFormat=TextFormat(bold=True, fontSize=10),
    horizontalAlignment=HorizontalAlignment.CENTER
)
format_cell_range(dash, "A3:L3", filter_fmt)
set_row_height(dash, "3", 35)

# Labels
dash.update([["⏱️ Time Range:"]], "A3")
dash.update([["🗺️ Region:"]], "C3")
dash.update([["🔔 Alerts:"]], "E3")

print("   ✅ Filter bar verified")

# ---------------------------------------------------------------------------
# STEP 7: CREATE INSTRUCTION NOTES
# ---------------------------------------------------------------------------
print("📝 Adding usage notes...")

dash.update([["📌 DASHBOARD NOTES:"]], "A110")
notes_hdr_fmt = CellFormat(
    backgroundColor=COLORS["blue"],
    textFormat=TextFormat(bold=True, foregroundColor=COLORS["white"]),
    horizontalAlignment=HorizontalAlignment.LEFT
)
format_cell_range(dash, "A110:L110", notes_hdr_fmt)

notes = [
    ["• Chart zones (rows 20-88) are reserved - automation should NOT write here"],
    ["• Top 12 Outages section (rows 90-105) - auto-updated every 10 min"],
    ["• Full outage history is in the 'Outages' sheet (searchable/filterable)"],
    ["• Date pickers in H3 & J3 filter historical data (click cells to see calendar)"],
    ["• Chart creation: Use Apps Script with ranges specified in CHART_SPECS.md"],
    ["• Automation scripts should only update: Rows 10-18 (data), Row 2 (timestamp), Rows 93-104 (outages)"]
]
dash.update(notes, "A111")

print("   ✅ Usage notes added")

# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("✅ DASHBOARD LAYOUT FIXED!")
print("=" * 70)
print()
print("📋 New Layout:")
print("   • Rows 1-2: Title & timestamp")
print("   • Row 3: Filter bar with dropdowns & date pickers")
print("   • Row 5: KPI strip")
print("   • Rows 9-18: Live data tables (Fuel Mix, Interconnectors, Financial)")
print("   • Rows 20-40: Chart zones (Fuel Mix & Interconnectors)")
print("   • Rows 45-65: Chart zones (Demand & Prices)")
print("   • Rows 70-88: Chart zone (Financial KPIs)")
print("   • Rows 90-105: Top 12 Outages (auto-updated)")
print("   • Rows 110+: Usage notes")
print()
print("🔧 Next Steps:")
print("   1. Update automation scripts to write ONLY to:")
print("      - Rows 10-18 (data)")
print("      - Row 2 (timestamp)")
print("      - Rows 93-104 (outages - max 12 rows)")
print("   2. Test date pickers by clicking H3 and J3")
print("   3. Create charts using Apps Script (see CHART_SPECS.md)")
print()
print("🌐 View dashboard:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
