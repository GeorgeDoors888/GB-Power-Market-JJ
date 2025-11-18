#!/usr/bin/env python3
"""Verify the corrected Dashboard layout"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SA_PATH = "inner-cinema-credentials.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=creds).spreadsheets()

result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A19:D30'
).execute()

vals = result.get('values', [])

print("=" * 80)
print("📊 DASHBOARD SETTLEMENT PERIOD SECTION - CORRECTED")
print("=" * 80)

for i, row in enumerate(vals, start=19):
    if i == 19:
        print(f"\nRow {i} (HEADER): {row}")
    elif i == 20:
        print(f"Row {i} (blank): {row if row else '(empty)'}")
    elif i == 21:
        print(f"\nRow {i} (COLUMNS): {' | '.join(row[:4])}")
    elif i <= 25:
        print(f"Row {i}: {' | '.join([str(c) for c in row[:4]])}")

print("\n" + "=" * 80)
print("✅ Columns should be: SP | Time | Generation (GW) | Demand (GW)")
print("=" * 80)
