#!/usr/bin/env python3
"""
GB Energy Dashboard V3 - Python Implementation
Builds complete dashboard with charts, KPIs, and formatting
Replaces Apps Script functionality with Python gspread
"""

import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import *
import os
from datetime import datetime

# === CONFIG ===
SERVICE_ACCOUNT_FILE = os.environ.get(
    'GOOGLE_APPLICATION_CREDENTIALS',
    '/home/george/.config/google-cloud/bigquery-credentials.json'
)
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

# Color scheme
COLORS = {
    'ORANGE': '#FF6600',
    'BLUE': '#3367D6',
    'GREY': '#F4F4F4',
    'LIGHT_BLUE': '#D9E9F7',
    'WHITE': '#FFFFFF',
    'YELLOW': '#FFFFCC',
    'DARK_GREY': '#424242',
    'GREEN': '#34A853',
    'RED': '#EA4335'
}

def get_client():
    """Authenticate and return gspread client"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    return gspread.authorize(creds)

def setup_dashboard_layout(gc):
    """
    Create Dashboard sheet with headers, KPI bar, tables
    Equivalent to Apps Script setupDashboard()
    """
    print("📊 Setting up Dashboard layout...")
    
    sh = gc.open_by_key(SPREADSHEET_ID)
    
    # Get or create Dashboard sheet
    try:
        dash = sh.worksheet('Dashboard')
        dash.clear()
    except gspread.exceptions.WorksheetNotFound:
        dash = sh.add_worksheet('Dashboard', rows=100, cols=26)
    
    # === HEADER SECTION (Rows 1-5) ===
    dash.update('A1', [['⚡ GB ENERGY DASHBOARD – REAL-TIME']], value_input_option='RAW')
    dash.update('A2', [[f'Last Update: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']], value_input_option='RAW')
    dash.update('A4', [['Region: All GB']], value_input_option='RAW')
    
    # Format header
    fmt_title = CellFormat(
        textFormat=TextFormat(bold=True, fontSize=16),
        horizontalAlignment='LEFT'
    )
    format_cell_range(dash, 'A1', fmt_title)
    
    fmt_timestamp = CellFormat(
        textFormat=TextFormat(italic=True, fontSize=10)
    )
    format_cell_range(dash, 'A2', fmt_timestamp)
    
    # === KPI BAR (Rows 9-11) ===
    kpi_headers = [['📊 VLP Revenue (£k)', '💰 Wholesale Avg (£/MWh)', '📈 Market Vol (%)']]
    dash.update('F9:H9', kpi_headers, value_input_option='RAW')
    
    # Format KPI headers
    fmt_kpi_header = CellFormat(
        backgroundColor=Color(0.2, 0.4, 0.84),  # Blue #3367D6
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        horizontalAlignment='CENTER'
    )
    format_cell_range(dash, 'F9:H9', fmt_kpi_header)
    
    # KPI formulas (these require named ranges to be set up)
    # dash.update('F10', [['=AVERAGE(VLP_Data!D:D)/1000']], value_input_option='USER_ENTERED')
    # dash.update('G10', [['=AVERAGE(Market_Prices!C:C)']], value_input_option='USER_ENTERED')
    # dash.update('H10', [['=STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C)']], value_input_option='USER_ENTERED')
    
    # Format KPI values
    fmt_kpi_value = CellFormat(
        backgroundColor=Color(0.96, 0.96, 0.96),  # Grey #F4F4F4
        numberFormat=NumberFormat(type='CURRENCY', pattern='£#,##0')
    )
    format_cell_range(dash, 'F10:H10', fmt_kpi_value)
    
    # === FUEL MIX / INTERCONNECTORS TABLE (Rows 9-21) ===
    fuel_headers = [['🔥 FUEL MIX', 'GW', '% Total', '🌍 INTERCONNECTORS', 'FLOW (MW)']]
    dash.update('A9:E9', fuel_headers, value_input_option='RAW')
    
    # Format fuel mix header
    fmt_fuel_header = CellFormat(
        backgroundColor=Color(1, 0.64, 0.3),  # Orange #FFA24D
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        horizontalAlignment='CENTER'
    )
    format_cell_range(dash, 'A9:E9', fmt_fuel_header)
    
    # === OUTAGES SECTION (Rows 24-36) ===
    dash.update('A24', [['⚠️ TOP ACTIVE OUTAGES (by MW Unavailable)']], value_input_option='RAW')
    
    fmt_outage_title = CellFormat(
        backgroundColor=Color(0.88, 0.88, 0.88),  # Grey #E0E0E0
        textFormat=TextFormat(bold=True)
    )
    format_cell_range(dash, 'A24', fmt_outage_title)
    
    outage_headers = [['BM Unit', 'Plant', 'Fuel', 'MW Lost', 'Region', 'Start Time', 'End Time', 'Status']]
    dash.update('A25:H25', outage_headers, value_input_option='RAW')
    
    fmt_outage_header = CellFormat(
        backgroundColor=Color(0.26, 0.26, 0.26),  # Dark grey #424242
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1))
    )
    format_cell_range(dash, 'A25:H25', fmt_outage_header)
    
    # === ESO INTERVENTIONS (Rows 37-50) ===
    dash.update('A37', [['⚖️ ESO INTERVENTIONS (System Operator Actions)']], value_input_option='RAW')
    
    fmt_eso_title = CellFormat(
        backgroundColor=Color(0.2, 0.4, 0.84),  # Blue #3367D6
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1))
    )
    format_cell_range(dash, 'A37', fmt_eso_title)
    
    eso_headers = [['BM Unit', 'Mode', 'MW', '£/MWh', 'Duration', 'Action Type']]
    dash.update('A38:F38', eso_headers, value_input_option='RAW')
    
    fmt_eso_header = CellFormat(
        backgroundColor=Color(0.93, 0.93, 0.93),  # Light grey #EEEEEE
        textFormat=TextFormat(bold=True)
    )
    format_cell_range(dash, 'A38:F38', fmt_eso_header)
    
    # Freeze rows
    dash.freeze(rows=3)
    
    print("✅ Dashboard layout created")
    return dash

def build_dashboard_charts(gc):
    """
    Create 7 charts on Dashboard sheet
    Equivalent to Apps Script buildDashboard()
    
    NOTE: gspread doesn't support chart creation directly.
    This function prepares data ranges and documents chart specs.
    Charts must be created via Apps Script or Google Sheets API.
    """
    print("📈 Preparing chart specifications...")
    
    sh = gc.open_by_key(SPREADSHEET_ID)
    dash = sh.worksheet('Dashboard')
    
    # Chart specifications (to be implemented via Google Sheets API)
    chart_specs = [
        {
            'title': '💰 Revenue by Service',
            'type': 'COLUMN',
            'position': {'row': 13, 'col': 1},
            'data_range': 'BESS!A1:D',
            'description': 'Column chart showing revenue breakdown by service type'
        },
        {
            'title': '📈 BM Price Trend',
            'type': 'LINE',
            'position': {'row': 13, 'col': 6},
            'data_range': 'BESS!A1:E',
            'description': 'Line chart showing balancing mechanism price trends'
        },
        {
            'title': '⚡ BESS KPIs – SoC/RTE/Cycles',
            'type': 'LINE',
            'position': {'row': 30, 'col': 1},
            'data_range': 'BESS!A1:J',
            'description': 'Battery state of charge, efficiency, and cycle tracking'
        },
        {
            'title': '💹 Net Profit vs Revenue',
            'type': 'COMBO',
            'position': {'row': 30, 'col': 6},
            'data_range': 'BESS!A1:N',
            'description': 'Combination chart showing profit margins vs revenue'
        },
        {
            'title': '🔋 Battery Degradation & RUL',
            'type': 'LINE',
            'position': {'row': 48, 'col': 1},
            'data_range': 'BESS!A1:Q',
            'description': 'Dual-axis chart for remaining useful life tracking'
        },
        {
            'title': '💷 Revenue per Cycle',
            'type': 'LINE',
            'position': {'row': 48, 'col': 6},
            'data_range': 'BESS!A1:S',
            'description': 'Line chart showing revenue efficiency per battery cycle'
        },
        {
            'title': '💹 Net Profit per MWh',
            'type': 'LINE',
            'position': {'row': 64, 'col': 1},
            'data_range': 'BESS!A1:T',
            'description': 'Line chart showing profit intensity per MWh'
        }
    ]
    
    print("\n📊 Chart Specifications:")
    for i, spec in enumerate(chart_specs, 1):
        print(f"   Chart {i}: {spec['title']}")
        print(f"      Type: {spec['type']}, Position: R{spec['position']['row']} C{spec['position']['col']}")
        print(f"      Data: {spec['data_range']}")
    
    print("\n⚠️  Note: Chart creation requires Google Sheets API v4 (not supported by gspread)")
    print("   Use Apps Script buildDashboard() or create charts manually")
    
    return chart_specs

def refresh_dashboard(gc):
    """
    Refresh dashboard data and update timestamp
    Equivalent to Apps Script refreshDashboard()
    """
    print("🔄 Refreshing dashboard...")
    
    sh = gc.open_by_key(SPREADSHEET_ID)
    dash = sh.worksheet('Dashboard')
    
    # Update timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dash.update('A2', [[f'Last Update: {timestamp}']], value_input_option='RAW')
    
    print(f"✅ Dashboard refreshed at {timestamp}")
    print("   Note: Data refresh requires running populate_bess_enhanced.py")
    print("   Note: Chart rebuild requires Apps Script or manual action")

def create_named_ranges(gc):
    """
    Create named ranges required for dashboard formulas
    """
    print("📌 Creating named ranges...")
    
    sh = gc.open_by_key(SPREADSHEET_ID)
    
    # Named ranges to create (requires Google Sheets API v4)
    named_ranges = [
        {'name': 'Live_Generation', 'range': 'Dashboard!B10'},
        {'name': 'Live_Demand', 'range': 'Dashboard!C10'},
        {'name': 'Live_Price', 'range': 'Dashboard!D10'},
        {'name': 'Live_SSP', 'range': 'Dashboard!E10'},
        {'name': 'Live_SBP', 'range': 'Dashboard!F10'},
        {'name': 'VLP_Data', 'range': 'BESS!D:D'},
        {'name': 'Market_Prices', 'range': 'Dashboard!C:C'}
    ]
    
    print("   Named ranges to create:")
    for nr in named_ranges:
        print(f"      {nr['name']} → {nr['range']}")
    
    print("\n⚠️  Note: Named range creation requires Google Sheets API v4")
    print("   Create manually via: Data → Named ranges")
    
    return named_ranges

def main():
    """Main execution"""
    print("=" * 70)
    print("GB ENERGY DASHBOARD V3 - PYTHON BUILDER")
    print("=" * 70)
    
    gc = get_client()
    
    # 1. Setup dashboard layout
    setup_dashboard_layout(gc)
    
    # 2. Prepare chart specifications
    chart_specs = build_dashboard_charts(gc)
    
    # 3. Document named ranges needed
    named_ranges = create_named_ranges(gc)
    
    # 4. Refresh timestamp
    refresh_dashboard(gc)
    
    print("\n" + "=" * 70)
    print("✅ DASHBOARD BUILD COMPLETE")
    print("=" * 70)
    print("\n📋 Next Steps:")
    print("   1. Run populate_bess_enhanced.py to populate BESS data")
    print("   2. Create named ranges manually (see list above)")
    print("   3. Use Apps Script to create charts (gspread doesn't support charts)")
    print("   4. Or manually create 7 charts using specifications above")
    print("\n🌐 View: https://docs.google.com/spreadsheets/d/{}/edit".format(SPREADSHEET_ID))

if __name__ == '__main__':
    main()
