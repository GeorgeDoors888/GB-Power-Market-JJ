#!/usr/bin/env python3
"""Check current Dashboard state and remove analysis section"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SA_PATH = "inner-cinema-credentials.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=creds).spreadsheets()

print("=" * 80)
print("🔍 CHECKING DASHBOARD STATE")
print("=" * 80)

# Read Dashboard
result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1:E40'
).execute()

vals = result.get('values', [])

print("\nRows 1-40:")
for i, row in enumerate(vals, start=1):
    first_cell = row[0] if row and len(row) > 0 else "(empty)"
    if i <= 10:
        print(f"Row {i:2d}: {first_cell[:60]}")
    elif "SETTLEMENT" in str(first_cell).upper() or "ANALYSIS" in str(first_cell).upper():
        print(f"Row {i:2d}: {first_cell[:60]}")

print("\n" + "=" * 80)
print("🔧 REMOVING ANALYSIS SECTION (REVERTING)")
print("=" * 80)

# Clear rows 6-26 (where analysis was added)
print("\nClearing rows 6-26...")

try:
    sheets.values().clear(
        spreadsheetId=SHEET_ID,
        range='Dashboard!A6:H26'
    ).execute()
    
    print("✅ Analysis section removed")
    print("\n📊 Now run redesign_dashboard_layout.py to restore clean layout")
    
except Exception as e:
    print(f"❌ Error: {e}")
