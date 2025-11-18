#!/usr/bin/env python3
"""Show the exact Dashboard layout to verify no duplicates"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SA_PATH = "inner-cinema-credentials.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=creds).spreadsheets()

result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A18:F75'
).execute()

vals = result.get('values', [])

print("=" * 80)
print("📊 DASHBOARD LAYOUT - SETTLEMENT PERIOD SECTION")
print("=" * 80)

for i, row in enumerate(vals[:55], start=18):
    # Format row nicely
    row_str = '\t'.join([str(cell)[:30] if cell else '' for cell in row[:6]])
    
    # Highlight key rows
    if i == 19:
        print(f"\nRow {i} (HEADER): {row_str}")
    elif i == 21:
        print(f"\nRow {i} (COLUMNS): {row_str}")
    elif i in [22, 23, 45, 46, 67, 68, 69]:
        print(f"Row {i}: {row_str}")
    elif i in [70, 71]:
        print(f"Row {i} (separator): {row_str}")
    elif i == 72:
        print(f"\nRow {i} (OUTAGES HEADER): {row_str}")

print("\n" + "=" * 80)
print("✅ Check complete - verify no duplicate SP47/SP48 entries")
print("=" * 80)
