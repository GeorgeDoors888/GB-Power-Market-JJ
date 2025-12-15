#!/usr/bin/env python3
"""Read Live Dashboard sheet to see actual column structure"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SA_PATH = "inner-cinema-credentials.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=creds).spreadsheets()

# Read Live Dashboard
result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live Dashboard!A1:Z10'
).execute()

vals = result.get('values', [])

print("=" * 80)
print("📊 LIVE DASHBOARD - ACTUAL STRUCTURE")
print("=" * 80)

if vals:
    print("\n🔍 HEADER ROW (columns available):")
    header = vals[0]
    for i, col in enumerate(header):
        print(f"  Column {chr(65+i)} (index {i}): {col}")
    
    print("\n📋 FIRST 5 DATA ROWS:")
    for i, row in enumerate(vals[1:6], start=1):
        print(f"\nRow {i+1}:")
        for j, cell in enumerate(row):
            if j < len(header):
                print(f"  {header[j]}: {cell}")
            else:
                print(f"  Column {j}: {cell}")

print("\n" + "=" * 80)
