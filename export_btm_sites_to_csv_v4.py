#!/usr/bin/env python3
"""
Export BtM Sites from Google Sheets to CSV (using Sheets API v4 directly)
Bypasses gspread library which has timeout issues
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
import time

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
BtM_SHEET_NAME = "BtM"
OUTPUT_CSV = "btm_sites.csv"

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def main():
    print("🔐 Authenticating with Google Sheets API v4...")

    # Load service account credentials
    try:
        creds = Credentials.from_service_account_file(
            'inner-cinema-credentials.json',
            scopes=SCOPES
        )
        print(f"✅ Credentials loaded")
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return

    # Build Sheets API service
    print(f"📊 Building Sheets API service...")
    try:
        service = build('sheets', 'v4', credentials=creds)
        print(f"✅ Service built")
    except Exception as e:
        print(f"❌ Error building service: {e}")
        return

    # Read BtM sheet data
    print(f"\n📖 Reading '{BtM_SHEET_NAME}' sheet...")
    print(f"   (This may take 1-2 minutes due to Google API response time)")

    try:
        start_time = time.time()

        # Read all data from BtM sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{BtM_SHEET_NAME}!A:Z'  # Read columns A-Z
        ).execute()

        elapsed = time.time() - start_time

        values = result.get('values', [])

        if not values:
            print("❌ No data found in sheet")
            return

        print(f"✅ Retrieved {len(values)} rows in {elapsed:.2f}s")

        # Convert to DataFrame
        # Check if first row is empty (might be a formatting row)
        header = values[0] if values[0] and any(values[0]) else None

        if not header or not any(header):
            # First row is empty, try second row
            print("   ⚠️  First row is empty, checking row 2...")
            header = values[1] if len(values) > 1 else None
            data_rows = values[2:] if len(values) > 2 else []
        else:
            data_rows = values[1:]

        if not header:
            print("   ❌ Cannot find header row")
            return

        # Clean header (remove empty values, generate column names if needed)
        cleaned_header = []
        for i, col in enumerate(header):
            if col and str(col).strip():
                cleaned_header.append(str(col).strip())
            else:
                cleaned_header.append(f"Column_{i+1}")

        # Pad rows that are shorter than header
        max_cols = len(cleaned_header)
        padded_rows = []
        for row in data_rows:
            padded_row = row + [''] * (max_cols - len(row))
            padded_rows.append(padded_row)

        df = pd.DataFrame(padded_rows, columns=cleaned_header)

        # Display columns found
        print(f"\n📋 Columns found ({len(df.columns)}): {list(df.columns)}")

        # Check for required columns
        required_cols = ['site_name', 'postcode', 'dno', 'capacity_mw']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"\n⚠️  Missing expected columns: {missing_cols}")
            print(f"📋 Available columns: {list(df.columns)}")
            print("\n💡 Will export all available columns")

        # Remove completely empty rows
        df = df.dropna(how='all')

        # Export to CSV
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ Exported {len(df)} rows to {OUTPUT_CSV}")

        # Show preview
        print("\n📊 Preview (first 5 rows):")
        print(df.head().to_string(index=False, max_colwidth=30))

        # Summary stats
        print(f"\n📈 Summary:")
        print(f"   Total rows: {len(df)}")
        print(f"   Total columns: {len(df.columns)}")

        # Show column types
        print(f"\n📋 Column data types:")
        for col in df.columns[:10]:  # Show first 10 columns
            non_empty = df[col].astype(str).str.strip().replace('', pd.NA).dropna()
            print(f"   {col}: {len(non_empty)} non-empty values")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
