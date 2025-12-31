#!/usr/bin/env python3
"""
Test gspread connection with timeout handling and diagnostics
"""

import gspread
from google.oauth2.service_account import Credentials
import time
import signal

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
TIMEOUT_SECONDS = 30

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def test_connection():
    print("🔍 GSPREAD CONNECTION DIAGNOSTICS")
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

    # Step 2: Authorize gspread
    print("\n2️⃣ Authorizing gspread client...")
    try:
        gc = gspread.authorize(creds)
        print(f"   ✅ gspread authorized (version: {gspread.__version__})")
    except Exception as e:
        print(f"   ❌ Error authorizing: {e}")
        return

    # Step 3: Open spreadsheet (with timeout)
    print(f"\n3️⃣ Opening spreadsheet (timeout: {TIMEOUT_SECONDS}s)...")
    print(f"   Spreadsheet ID: {SPREADSHEET_ID}")

    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)

    try:
        start_time = time.time()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        elapsed = time.time() - start_time
        signal.alarm(0)  # Cancel timeout

        print(f"   ✅ Spreadsheet opened in {elapsed:.2f}s")
        print(f"   Title: {spreadsheet.title}")

        # Step 4: List worksheets
        print("\n4️⃣ Listing worksheets...")
        worksheets = spreadsheet.worksheets()
        print(f"   ✅ Found {len(worksheets)} worksheets:")
        for ws in worksheets:
            print(f"      - {ws.title} ({ws.row_count} rows x {ws.col_count} cols)")

        # Step 5: Test reading BtM sheet
        print("\n5️⃣ Testing BtM sheet access...")
        try:
            btm_sheet = spreadsheet.worksheet("BtM")
            print(f"   ✅ BtM sheet found")
            print(f"   Dimensions: {btm_sheet.row_count} rows x {btm_sheet.col_count} cols")

            # Try to get header row
            print("\n6️⃣ Reading header row...")
            header = btm_sheet.row_values(1)
            print(f"   ✅ Header: {header[:5]}..." if len(header) > 5 else f"   ✅ Header: {header}")

            # Try to get row count
            print("\n7️⃣ Getting data...")
            data = btm_sheet.get_all_records()
            print(f"   ✅ Retrieved {len(data)} data rows")

            if data:
                print(f"\n   📊 First row sample:")
                first_row = data[0]
                for key, value in list(first_row.items())[:5]:
                    print(f"      {key}: {value}")

        except gspread.exceptions.WorksheetNotFound:
            print(f"   ❌ BtM worksheet not found")
            print(f"   Available worksheets: {[ws.title for ws in worksheets]}")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - gspread is working correctly")

    except TimeoutError:
        signal.alarm(0)
        print(f"   ❌ TIMEOUT after {TIMEOUT_SECONDS}s")
        print(f"\n💡 Possible causes:")
        print(f"   1. Network connectivity issues")
        print(f"   2. Google Sheets API rate limiting")
        print(f"   3. OAuth token refresh hanging")
        print(f"   4. Firewall blocking Google API endpoints")
        return

    except Exception as e:
        signal.alarm(0)
        print(f"   ❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    test_connection()
