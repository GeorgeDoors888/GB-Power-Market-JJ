#!/usr/bin/env python3
"""
Read Summary sheet to understand chart data
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'inner-cinema-credentials.json'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# Get Summary sheet
summary_sheet = spreadsheet.worksheet("Summary")

# Read header row
headers = summary_sheet.row_values(1)
print("📊 SUMMARY SHEET STRUCTURE:\n")
print("Headers (row 1):")
for idx, header in enumerate(headers[:10], 1):
    if header:
        print(f"  Column {idx} ({chr(64+idx)}): {header}")

print("\n" + "="*60)
print("SAMPLE DATA (first 5 rows):\n")

# Read first 5 data rows
data = summary_sheet.get('A1:E6')
for row_idx, row in enumerate(data, 1):
    print(f"Row {row_idx}: {row}")
