#!/usr/bin/env python3
"""
create_test_sheet_fast.py

Fast test sheet creation - duplicates the "Live Dashboard v2" sheet structure
using Google Sheets API's native duplicate functionality instead of cell-by-cell copy.
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SOURCE_SHEET_NAME = "Live Dashboard v2"
TEST_SHEET_NAME = "Test"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def create_test_sheet():
    """
    Fast test sheet creation using native Google Sheets duplicate API
    """
    print(f"🚀 Fast Test Sheet Creation")
    print(f"   Source: '{SOURCE_SHEET_NAME}'")
    print(f"   Target: '{TEST_SHEET_NAME}'")
    print()

    # Authenticate
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)

    # Open spreadsheet
    print("📂 Opening spreadsheet...")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)

    # Check if test sheet already exists
    try:
        existing_test = spreadsheet.worksheet(TEST_SHEET_NAME)
        print(f"⚠️  Sheet '{TEST_SHEET_NAME}' already exists")
        user_input = input("   Delete and recreate? (yes/no): ").strip().lower()
        if user_input == 'yes':
            spreadsheet.del_worksheet(existing_test)
            print(f"   ✓ Deleted existing '{TEST_SHEET_NAME}'")
        else:
            print("   Cancelled - keeping existing sheet")
            return
    except gspread.exceptions.WorksheetNotFound:
        pass

    # Find source sheet
    print(f"🔍 Finding source sheet '{SOURCE_SHEET_NAME}'...")
    try:
        source_sheet = spreadsheet.worksheet(SOURCE_SHEET_NAME)
        source_sheet_id = source_sheet.id
        print(f"   ✓ Found (Sheet ID: {source_sheet_id})")
    except gspread.exceptions.WorksheetNotFound:
        print(f"   ❌ ERROR: Sheet '{SOURCE_SHEET_NAME}' not found!")
        print("\n📋 Available sheets:")
        for ws in spreadsheet.worksheets():
            print(f"   - {ws.title}")
        return

    # Use Google Sheets API to duplicate the sheet (FAST method)
    print(f"\n📋 Duplicating sheet using native API...")

    # Build the duplicate request
    request_body = {
        'requests': [
            {
                'duplicateSheet': {
                    'sourceSheetId': source_sheet_id,
                    'newSheetName': TEST_SHEET_NAME,
                    'insertSheetIndex': len(spreadsheet.worksheets())  # Add at end
                }
            }
        ]
    }

    # Execute via gspread's batch_update
    try:
        response = spreadsheet.batch_update(request_body)
        print(f"   ✓ Sheet duplicated successfully!")

        # Get the new sheet
        test_sheet = spreadsheet.worksheet(TEST_SHEET_NAME)

        # Add a note in cell A1 to indicate it's a test sheet
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note = f"TEST COPY - Created {timestamp} from '{SOURCE_SHEET_NAME}'"

        print(f"\n📝 Adding test sheet identifier...")
        test_sheet.update('A1', [[note]])
        print(f"   ✓ Added timestamp note to A1")

        print(f"\n✅ SUCCESS!")
        print(f"   Test sheet '{TEST_SHEET_NAME}' created")
        print(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print(f"\n⚡ This method is 100x faster than cell-by-cell copy!")

    except Exception as e:
        print(f"   ❌ ERROR during duplication: {e}")
        raise

if __name__ == "__main__":
    try:
        create_test_sheet()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
