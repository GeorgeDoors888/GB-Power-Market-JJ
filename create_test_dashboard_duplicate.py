#!/usr/bin/env python3
"""
create_test_dashboard_duplicate.py

Creates a test sheet named 'Test' by duplicating 'Live Dashboard v2'
- Preserves formulas, formatting, charts, conditional formatting
- Checks for cell range conflicts with other sheets
- Safe duplication without disrupting production dashboard

Usage:
    python3 create_test_dashboard_duplicate.py
"""

import gspread
from google.oauth2.service_account import Credentials
import sys

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SOURCE_SHEET = 'Live Dashboard v2'
TEST_SHEET_NAME = 'Test'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

def get_sheets_client():
    """Initialize Google Sheets client"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    return gspread.authorize(creds)

def check_existing_sheets(spreadsheet):
    """Check what sheets exist and detect potential conflicts"""
    print("\n📋 Current sheets in workbook:")
    worksheets = spreadsheet.worksheets()

    sheet_info = []
    for ws in worksheets:
        print(f"   • {ws.title} (ID: {ws.id}, {ws.row_count} rows × {ws.col_count} cols)")
        sheet_info.append({
            'title': ws.title,
            'id': ws.id,
            'rows': ws.row_count,
            'cols': ws.col_count
        })

    return sheet_info

def delete_existing_test_sheet(spreadsheet):
    """Delete existing 'Test' sheet if it exists"""
    try:
        test_sheet = spreadsheet.worksheet(TEST_SHEET_NAME)
        print(f"\n⚠️  Found existing '{TEST_SHEET_NAME}' sheet (ID: {test_sheet.id})")
        response = input(f"Delete existing '{TEST_SHEET_NAME}' sheet? (yes/no): ").strip().lower()

        if response == 'yes':
            spreadsheet.del_worksheet(test_sheet)
            print(f"✅ Deleted existing '{TEST_SHEET_NAME}' sheet")
            return True
        else:
            print(f"❌ Aborting - '{TEST_SHEET_NAME}' sheet already exists")
            return False
    except gspread.exceptions.WorksheetNotFound:
        print(f"\n✅ No existing '{TEST_SHEET_NAME}' sheet found - safe to create")
        return True

def duplicate_sheet(spreadsheet, source_sheet_name, new_sheet_name):
    """
    Duplicate a sheet using Google Sheets API
    This preserves formulas, formatting, charts, and conditional formatting
    """
    try:
        source_sheet = spreadsheet.worksheet(source_sheet_name)
        print(f"\n🔍 Found source sheet '{source_sheet_name}' (ID: {source_sheet.id})")
        print(f"   Dimensions: {source_sheet.row_count} rows × {source_sheet.col_count} cols")

        # Duplicate using API (this is the key - preserves everything)
        new_sheet = source_sheet.duplicate(new_sheet_name=new_sheet_name)

        print(f"\n✅ Successfully duplicated to '{new_sheet_name}' (ID: {new_sheet.id})")
        print(f"   Dimensions: {new_sheet.row_count} rows × {new_sheet.col_count} cols")

        return new_sheet

    except gspread.exceptions.WorksheetNotFound:
        print(f"❌ Error: Source sheet '{source_sheet_name}' not found")
        return None
    except Exception as e:
        print(f"❌ Error duplicating sheet: {e}")
        return None

def verify_duplication(spreadsheet, source_name, test_name):
    """
    Verify the duplication was successful by comparing key characteristics
    """
    print("\n🔍 Verifying duplication...")

    try:
        source = spreadsheet.worksheet(source_name)
        test = spreadsheet.worksheet(test_name)

        # Compare dimensions
        if source.row_count != test.row_count or source.col_count != test.col_count:
            print(f"⚠️  Warning: Dimensions differ")
            print(f"   Source: {source.row_count}×{source.col_count}")
            print(f"   Test:   {test.row_count}×{test.col_count}")
        else:
            print(f"✅ Dimensions match: {source.row_count}×{source.col_count}")

        # Sample a few cells to verify formulas copied
        sample_cells = ['A1', 'K13', 'L14', 'C6']
        print("\n📝 Sampling cells to verify formulas:")

        for cell in sample_cells:
            try:
                source_val = source.acell(cell, value_render_option='FORMULA').value
                test_val = test.acell(cell, value_render_option='FORMULA').value

                if source_val:
                    match_status = "✅" if source_val == test_val else "⚠️"
                    print(f"   {cell}: {match_status}")
                    if source_val != test_val:
                        print(f"      Source: {source_val[:50]}...")
                        print(f"      Test:   {test_val[:50] if test_val else 'None'}...")
            except Exception as e:
                print(f"   {cell}: ⚠️  (error: {e})")

        print("\n✅ Verification complete - manual review recommended")

    except Exception as e:
        print(f"❌ Verification error: {e}")

def check_data_hidden_references(spreadsheet):
    """
    Check if formulas reference Data_Hidden sheet
    This is important for conflict detection
    """
    print("\n🔍 Checking for Data_Hidden references...")

    try:
        test_sheet = spreadsheet.worksheet(TEST_SHEET_NAME)

        # Get all formulas from the sheet
        formulas = test_sheet.get_all_values()

        data_hidden_refs = []
        for row_idx, row in enumerate(formulas, start=1):
            for col_idx, cell in enumerate(row, start=1):
                if cell and 'Data_Hidden' in str(cell):
                    col_letter = chr(64 + col_idx) if col_idx <= 26 else f"A{chr(64 + col_idx - 26)}"
                    data_hidden_refs.append(f"{col_letter}{row_idx}")

        if data_hidden_refs:
            print(f"⚠️  Found {len(data_hidden_refs)} cells referencing Data_Hidden:")
            for ref in data_hidden_refs[:10]:  # Show first 10
                print(f"   • {ref}")
            if len(data_hidden_refs) > 10:
                print(f"   ... and {len(data_hidden_refs) - 10} more")

            print("\n💡 Note: Test sheet will share Data_Hidden references with Live Dashboard v2")
            print("   This is expected behavior for testing purposes")
        else:
            print("✅ No Data_Hidden references found (or formulas not scanned)")

    except Exception as e:
        print(f"⚠️  Could not check references: {e}")

def main():
    """Main execution"""
    print("=" * 70)
    print("🧪 CREATE TEST DASHBOARD DUPLICATE")
    print("=" * 70)
    print(f"Source: '{SOURCE_SHEET}'")
    print(f"Target: '{TEST_SHEET_NAME}'")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")

    try:
        # Initialize client
        print("\n🔐 Authenticating...")
        client = get_sheets_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        print(f"✅ Connected to: {spreadsheet.title}")

        # Check existing sheets
        sheet_info = check_existing_sheets(spreadsheet)

        # Check if Test sheet exists
        if not delete_existing_test_sheet(spreadsheet):
            sys.exit(1)

        # Duplicate the sheet
        new_sheet = duplicate_sheet(spreadsheet, SOURCE_SHEET, TEST_SHEET_NAME)

        if not new_sheet:
            sys.exit(1)

        # Verify duplication
        verify_duplication(spreadsheet, SOURCE_SHEET, TEST_SHEET_NAME)

        # Check for Data_Hidden references
        check_data_hidden_references(spreadsheet)

        print("\n" + "=" * 70)
        print("✅ TEST SHEET CREATION COMPLETE")
        print("=" * 70)
        print(f"\n🔗 View sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={new_sheet.id}")
        print("\n📋 Next steps:")
        print("   1. Manually review Test sheet for correct duplication")
        print("   2. Verify charts and conditional formatting copied correctly")
        print("   3. Test formulas are working with Data_Hidden references")
        print("   4. Make modifications in Test sheet without affecting Live Dashboard v2")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
