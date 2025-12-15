import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- Configuration ---
SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
DASHBOARD_SHEET_NAME = 'GB Live 2'
DATA_SHEET_NAME = 'Data'
CHART_DATA_SHEET_NAME = 'ChartData'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# --- Helper Functions ---
def get_sheet(gc, sheet_name):
    """Safely get a worksheet by name."""
    try:
        return gc.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        print(f"❌ DIAGNOSTIC ERROR: Worksheet '{sheet_name}' not found.")
        return None

def check_cell_value(sheet, cell, label):
    """Check a single cell and print its status."""
    try:
        value = sheet.acell(cell).value
        if value is None or value == '' or value == '0':
            print(f"🟡 {label} ({cell}): Value is '{value}' (Empty or Zero).")
            return False
        print(f"✅ {label} ({cell}): Value is '{value}'.")
        return True
    except gspread.exceptions.CellNotFound:
        print(f"❌ {label} ({cell}): Cell not found.")
        return False

def check_data_sheet(sheet, sheet_name):
    """Check if a data sheet has content."""
    if not sheet:
        return False
    try:
        data = sheet.get_all_records()
        if len(data) > 0:
            print(f"✅ Data Sheet '{sheet_name}': Found {len(data)} rows of data.")
            return True
        else:
            print(f"🟡 Data Sheet '{sheet_name}': Sheet exists but is empty.")
            return False
    except Exception as e:
        print(f"❌ Data Sheet '{sheet_name}': Error reading sheet - {e}")
        return False

def run_diagnostics():
    """Main function to run all diagnostic checks."""
    print("--- Starting GB Live Dashboard Diagnostics ---")
    
    # --- 1. Authentication ---
    print("\n1. Authenticating with Google Sheets API...")
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        print("✅ Authentication successful.")
    except Exception as e:
        print(f"❌ FATAL: Could not authenticate. Error: {e}")
        print("   Please ensure 'inner-cinema-credentials.json' is valid and has Google Sheets API enabled.")
        return

    # --- 2. Access Dashboard Sheet ---
    print(f"\n2. Checking for '{DASHBOARD_SHEET_NAME}' worksheet...")
    dashboard_sheet = get_sheet(gc, DASHBOARD_SHEET_NAME)
    if not dashboard_sheet:
        return

    # --- 3. Check KPI Values ---
    print("\n3. Reading Key Performance Indicator (KPI) values...")
    kpi_cells = {
        'A6': 'VLP Revenue',
        'C6': 'Wholesale Avg',
        'E6': 'Grid Frequency',
        'G6': 'Total Gen',
        'I6': 'Wind Gen',
        'K6': 'Demand'
    }
    kpi_success = all(check_cell_value(dashboard_sheet, cell, label) for cell, label in kpi_cells.items())

    # --- 4. Check for BigQuery Errors ---
    print("\n4. Checking for BigQuery error messages...")
    error_cell = 'A35'
    error_value = dashboard_sheet.acell(error_cell).value
    if error_value and 'BigQuery Error' in error_value:
        print(f"❌ CRITICAL ERROR FOUND in cell {error_cell}:")
        print(f"   '{error_value}'")
    else:
        print(f"✅ No BigQuery error message found in cell {error_cell}.")

    # --- 5. Check Data Sheets ---
    print("\n5. Inspecting hidden data sheets...")
    data_sheet = get_sheet(gc, DATA_SHEET_NAME)
    chart_data_sheet = get_sheet(gc, CHART_DATA_SHEET_NAME)
    
    data_sheet_ok = check_data_sheet(data_sheet, DATA_SHEET_NAME)
    chart_data_sheet_ok = check_data_sheet(chart_data_sheet, CHART_DATA_SHEET_NAME)

    # --- 6. Final Summary ---
    print("\n--- Diagnostic Summary ---")
    if error_value and 'BigQuery Error' in error_value:
        print("🔴 RESULT: FAILED. A critical BigQuery error was found on the sheet.")
        print("   ROOT CAUSE: The Apps Script is failing to execute its BigQuery queries.")
        print(f"   DETAILS: {error_value}")
        print("   NEXT STEP: Resolve the permission or query error shown above.")
    elif not kpi_success:
        print("🟠 RESULT: PARTIAL SUCCESS. The script ran, but some data is missing or zero.")
        print("   ROOT CAUSE: The BigQuery queries are likely returning empty results for some metrics.")
        print("   NEXT STEP: Verify that the BigQuery tables have data for the most recent settlement periods.")
    elif not data_sheet_ok or not chart_data_sheet_ok:
        print("🟠 RESULT: PARTIAL SUCCESS. KPIs are present, but chart data is missing.")
        print("   ROOT CAUSE: The queries for generation mix or intraday trends are failing.")
        print("   NEXT STEP: Check the execution logs in Apps Script for errors in the chart data functions.")
    else:
        print("🟢 RESULT: SUCCESS. All checks passed.")
        print("   The dashboard appears to be populated with data, and no errors were found.")

if __name__ == '__main__':
    run_diagnostics()
