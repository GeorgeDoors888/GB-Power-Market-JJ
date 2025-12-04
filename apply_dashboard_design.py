#!/usr/bin/env python3
"""
GB Energy Dashboard V3 - Professional Layout & Formatting
Applies a clean, modern, and data-driven design to the main 'Dashboard' sheet
based on DASHBOARD_V3_ISSUES_AND_REBUILD_PLAN.md.
"""

import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import *

# --- CONFIGURATION ---
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
DASHBOARD_SHEET_NAME = 'Dashboard'

# --- COLOR & STYLE PALETTE (from rebuild plan) ---
PALETTE = {
    "ORANGE": Color(1.0, 0.64, 0.3),
    "BLUE": Color(0.2, 0.404, 0.839),
    "LIGHT_BLUE": Color(0.89, 0.95, 0.99),
    "LIGHT_GREY": Color(0.93, 0.93, 0.93),
    "KPI_GREY": Color(0.96, 0.96, 0.96),
    "GREEN": Color(0.18, 0.49, 0.20),
    "RED": Color(0.78, 0.16, 0.16),
    "WHITE": Color(1, 1, 1)
}

# --- FORMATTING DEFINITIONS ---
FORMATS = {
    "title": CellFormat(
        backgroundColor=PALETTE["ORANGE"],
        textFormat=TextFormat(bold=True, fontSize=16, foregroundColor=PALETTE["WHITE"]),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE'
    ),
    "timestamp": CellFormat(
        textFormat=TextFormat(italic=True, fontSize=9),
        horizontalAlignment='RIGHT'
    ),
    "kpi_header": CellFormat(
        backgroundColor=PALETTE["BLUE"],
        textFormat=TextFormat(bold=True, fontSize=11, foregroundColor=PALETTE["WHITE"]),
        horizontalAlignment='CENTER'
    ),
    "kpi_value": CellFormat(
        backgroundColor=PALETTE["KPI_GREY"],
        textFormat=TextFormat(bold=True, fontSize=18),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE'
    ),
    "section_header": CellFormat(
        backgroundColor=PALETTE["LIGHT_BLUE"],
        textFormat=TextFormat(bold=True, fontSize=12),
        borders=Borders(bottom=Border("SOLID_THICK", PALETTE["BLUE"]))
    ),
    "table_header": CellFormat(
        textFormat=TextFormat(bold=True, fontSize=10),
        borders=Borders(bottom=Border("SOLID", Color(0,0,0)))
    ),
    "default": CellFormat(textFormat=TextFormat(fontSize=10))
}

def get_client():
    """Authorize and return gspread client."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    return gspread.authorize(creds)

def apply_design(ss):
    """Applies the full dashboard design."""
    print(f"--- Applying V3 Design to '{DASHBOARD_SHEET_NAME}' ---")
    
    try:
        sheet = ss.worksheet(DASHBOARD_SHEET_NAME)
    except gspread.WorksheetNotFound:
        print(f"⚠️ Worksheet '{DASHBOARD_SHEET_NAME}' not found. Creating it.")
        sheet = ss.add_worksheet(title=DASHBOARD_SHEET_NAME, rows=100, cols=26)

    # 1. Clear all existing formatting and content
    print("   1. Clearing existing content and formats...")
    sheet.clear()
    try:
        sheet.unmerge_cells('A1:Z1000')
    except gspread.exceptions.APIError:
        pass # Ignore if no merged cells exist

    # 2. Set basic properties
    set_frozen(sheet, rows=3, cols=1)
    set_column_widths(sheet, [('A', 150), ('B', 150), ('C', 150), ('D', 150), ('E', 150), ('F', 120), ('G', 120), ('H', 120)])
    format_cell_range(sheet, 'A:Z', FORMATS["default"])

    # 3. Write static layout content and formulas
    print("   2. Writing static layout and formulas...")
    sheet.update(range_name='A1', values=[['⚡ GB ENERGY DASHBOARD V3 – REAL-TIME']])
    sheet.update(range_name='A2', values=[['=CONCAT("Live Data: ", TEXT(NOW(), "YYYY-MM-DD HH:mm:ss"))']])
    
    # Dropdown placeholder
    sheet.update(range_name='B3', values=[['Time Range: 1 Year']])
    
    # Section Header
    sheet.update(range_name='A9', values=[['🔥 Fuel Mix & Interconnectors']])
    
    # Create 3 distinct table headers instead of one combined one
    sheet.update(range_name='A10', values=[['Fuel Type', 'Generation (MW)']])
    sheet.update(range_name='C10', values=[['IC Name', 'Flow (MW)', 'Direction']])
    sheet.update(range_name='F10', values=[['VLP Avg. Profit (£/MWh)', 'Wholesale Avg (£/MWh)', 'Market Volatility %']])
    
    # Apply formatting to all three headers
    format_cell_range(sheet, 'A10:B10', FORMATS["table_header"])
    format_cell_range(sheet, 'C10:E10', FORMATS["table_header"])
    format_cell_range(sheet, 'F10:H10', FORMATS["table_header"])

    # Market Analysis Formulas
    sheet.update(range_name='F11', values=[
        ['=IFERROR(AVERAGE(VLP_Data!E:E), 0)', 
         '=IFERROR(AVERAGE(\'Chart Data\'!B:B), 0)', 
         '=IFERROR(STDEV(\'Chart Data\'!B:B)/AVERAGE(\'Chart Data\'!B:B), 0)']
    ])
    
    # Section Header for Outages
    sheet.update(range_name='A24', values=[['⚠️ Active Outages']])
    sheet.update(range_name='A25', values=[['Unit ID', 'Type', 'Start Time', 'End Time', 'MW Unavailable']])
    format_cell_range(sheet, 'A25:E25', FORMATS["table_header"])

    # Section Header for Interventions
    sheet.update(range_name='G24', values=[['⚖️ ESO Interventions']])
    sheet.update(range_name='G25', values=[['Unit', 'Action', 'Volume (MW)', 'Price (£/MWh)', 'Time', 'Cost (£)']])
    format_cell_range(sheet, 'G25:L25', FORMATS["table_header"])
    sheet.update(range_name='G26', values=[['=IFERROR(QUERY(ESO_Actions!A:H, "SELECT A, F, D, E, C, G WHERE D is not null ORDER BY C DESC LIMIT 10"), "No recent actions.")']])
    
    # Section Header for Map
    sheet.update(range_name='M9', values=[['🗺️ Generator Map']])
    
    # 4. Apply formatting and styles
    print("   3. Applying formats and styles...")
    format_cell_ranges(sheet, [
        ('A1:M1', FORMATS["title"]),
        ('A2:M2', FORMATS["timestamp"]),
        ('A9:E9', FORMATS["section_header"]),
        ('F9:H9', FORMATS["section_header"]),
        ('A24:E24', FORMATS["section_header"]),
        ('G24:L24', FORMATS["section_header"]),
        ('M9:T9', FORMATS["section_header"]),
        ('F10:H10', FORMATS["kpi_value"]),
    ])
    
    # Number formats
    format_cell_ranges(sheet, [
        ('F11', CellFormat(numberFormat=NumberFormat(type='CURRENCY', pattern='£#,##0.00'))),
        ('G11', CellFormat(numberFormat=NumberFormat(type='CURRENCY', pattern='£#,##0.00'))),
        ('H11', CellFormat(numberFormat=NumberFormat(type='PERCENT', pattern='0.00%'))),
        ('I26:I35', CellFormat(numberFormat=NumberFormat(type='NUMBER', pattern='#,##0'))),      # Intervention Volume
        ('J26:J35', CellFormat(numberFormat=NumberFormat(type='CURRENCY', pattern='£#,##0.00'))), # Intervention Price
        ('L26:L35', CellFormat(numberFormat=NumberFormat(type='CURRENCY', pattern='£#,##0'))),      # Intervention Cost
    ])

    # Merges - Corrected to be non-overlapping
    sheet.merge_cells('B1:M1')
    sheet.merge_cells('B9:E9')
    sheet.merge_cells('B24:E24')
    sheet.merge_cells('H24:L24')
    sheet.merge_cells('N9:T9')

    # Conditional Formatting
    print("   4. Setting conditional formatting rules...")
    rules = get_conditional_format_rules(sheet)
    rules.clear()
    # Rule for >500 MW interventions
    rules.append(ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('I26:I35', sheet)], # Corrected range for Volume
        booleanRule=BooleanRule(
            condition=BooleanCondition('NUMBER_GREATER', ['500']),
            format=CellFormat(backgroundColor=PALETTE["RED"], textFormat=TextFormat(foregroundColor=PALETTE["WHITE"], bold=True))
        )
    ))
    # Rule for Interconnector Imports
    rules.append(ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('E11:E21', sheet)], # Range for IC Direction
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['Import']),
            format=CellFormat(backgroundColor=PALETTE["LIGHT_BLUE"])
        )
    ))
    # Rule for Interconnector Exports
    rules.append(ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('E11:E21', sheet)], # Range for IC Direction
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['Export']),
            format=CellFormat(backgroundColor=Color(1, 0.8, 0.8)) # Light Red
        )
    ))
    rules.save()

    print("--- ✅ Design application complete! ---")

def main():
    try:
        client = get_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        apply_design(spreadsheet)
        sheet_id = spreadsheet.worksheet(DASHBOARD_SHEET_NAME).id
        print(f"\n🔗 View your new dashboard: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet_id}")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
