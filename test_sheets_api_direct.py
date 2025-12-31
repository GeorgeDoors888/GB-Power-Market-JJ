#!/usr/bin/env python3
"""
Test Google Sheets API v4 directly (bypassing gspread)
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import time

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def test_direct_api():
    print("🔍 GOOGLE SHEETS API v4 DIRECT TEST")
    print("=" * 60)

    # Step 1: Load credentials
    print("\n1️⃣ Loading service account credentials...")
    try:
        creds = Credentials.from_service_account_file(
            'inner-cinema-credentials.json',
            scopes=SCOPES
        )
        print(f"   ✅ Credentials loaded")
        print(f"   Service account: {creds.service_account_email}")
    except Exception as e:
        print(f"   ❌ Error loading credentials: {e}")
        return

    # Step 2: Build Sheets API service
    print("\n2️⃣ Building Sheets API v4 service...")
    try:
        service = build('sheets', 'v4', credentials=creds)
        print(f"   ✅ Service built")
    except Exception as e:
        print(f"   ❌ Error building service: {e}")
        return

    # Step 3: Get spreadsheet metadata
    print(f"\n3️⃣ Getting spreadsheet metadata...")
    print(f"   Spreadsheet ID: {SPREADSHEET_ID}")

    try:
        start_time = time.time()

        # Get spreadsheet properties
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()

        elapsed = time.time() - start_time

        print(f"   ✅ Retrieved metadata in {elapsed:.2f}s")
        print(f"   Title: {spreadsheet['properties']['title']}")

        # List sheets
        sheets = spreadsheet.get('sheets', [])
        print(f"\n4️⃣ Found {len(sheets)} worksheets:")
        for sheet in sheets:
            props = sheet['properties']
            print(f"      - {props['title']} (ID: {props['sheetId']})")

        # Step 4: Read BtM sheet data
        print("\n5️⃣ Reading BtM sheet data...")

        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='BtM!A1:Z1000'  # Read first 1000 rows
            ).execute()

            values = result.get('values', [])

            if not values:
                print(f"   ⚠️  No data found in BtM sheet")
            else:
                print(f"   ✅ Retrieved {len(values)} rows")

                # Show header
                if values:
                    header = values[0]
                    print(f"\n   📋 Header columns: {header[:5]}..." if len(header) > 5 else f"\n   📋 Header: {header}")

                # Show first data row
                if len(values) > 1:
                    print(f"\n   📊 First data row:")
                    first_row = values[1]
                    for i, (col_name, value) in enumerate(zip(header, first_row)):
                        if i >= 5:
                            break
                        print(f"      {col_name}: {value}")

                print(f"\n   ✅ Successfully read {len(values)-1} data rows from BtM sheet")

        except Exception as e:
            print(f"   ❌ Error reading BtM sheet: {e}")

        print("\n" + "=" * 60)
        print("✅ GOOGLE SHEETS API v4 WORKS - gspread is the problem")
        print("\n💡 Solution: Use Google Sheets API v4 directly instead of gspread")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_api()
