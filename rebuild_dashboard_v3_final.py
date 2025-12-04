#!/usr/bin/env python3
"""
rebuild_dashboard_v3_final.py
-----------------------------
MASTER SCRIPT for a complete, atomic rebuild of the GB Energy Dashboard V3.

This script consolidates all steps required to build the dashboard from scratch,
ensuring a clean and correct final state. It performs the following actions:
1. Deletes the old 'Dashboard' sheet.
2. Creates a new, blank 'Dashboard' sheet.
3. Applies the full V3 design, layout, and formatting.
4. Populates all data tables (Fuel Mix, Interconnectors, Outages) from BigQuery.
5. Adds the main data chart and map placeholder.
"""

import gspread
from google.oauth2.service_account import Credentials
import time

# Import functions from the individual build scripts
from apply_dashboard_design import apply_design as apply_v3_design
from populate_dashboard_tables import main as populate_all_tables
from add_chart_and_map import add_chart_and_map

# --- CONFIGURATION ---
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
DASHBOARD_SHEET_NAME = 'Dashboard'

def get_gspread_client():
    """Authorize and return gspread client."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    return gspread.authorize(creds)

def main():
    """Executes the full, end-to-end dashboard rebuild process."""
    print("=" * 70)
    print("🚀 STARTING: Full Rebuild of GB Energy Dashboard V3")
    print("=" * 70)

    try:
        # --- 1. Get Client and Spreadsheet ---
        client = get_gspread_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        print("✅ Successfully connected to Google Sheets.")

        # --- 2. Delete Old Worksheet ---
        print(f"\n--- Step 1: Deleting old '{DASHBOARD_SHEET_NAME}' worksheet ---")
        try:
            worksheet_to_delete = spreadsheet.worksheet(DASHBOARD_SHEET_NAME)
            spreadsheet.del_worksheet(worksheet_to_delete)
            print(f"   ✅ Worksheet '{DASHBOARD_SHEET_NAME}' deleted. Waiting for changes to apply...")
            time.sleep(5)
        except gspread.exceptions.WorksheetNotFound:
            print(f"   ℹ️ Worksheet '{DASHBOARD_SHEET_NAME}' not found. Skipping deletion.")

        # --- 3. Create New Worksheet ---
        print(f"\n--- Step 2: Creating new '{DASHBOARD_SHEET_NAME}' worksheet ---")
        new_sheet = spreadsheet.add_worksheet(title=DASHBOARD_SHEET_NAME, rows=100, cols=26)
        print(f"   ✅ New worksheet created with ID: {new_sheet.id}")
        
        # --- 4. Apply V3 Design ---
        print("\n--- Step 3: Applying V3 Dashboard Design ---")
        apply_v3_design(spreadsheet)
        
        # --- 5. Populate Data Tables ---
        print("\n--- Step 4: Populating Data Tables from BigQuery ---")
        populate_all_tables()
        
        # --- 6. Add Chart and Map ---
        print("\n--- Step 5: Adding Chart and Map ---")
        add_chart_and_map(spreadsheet)

        print("\n" + "=" * 70)
        print("🎉 SUCCESS: Dashboard V3 has been completely rebuilt.")
        print("=" * 70)
        print(f"\n🔗 View the final result: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={new_sheet.id}")

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ CRITICAL ERROR during rebuild: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
