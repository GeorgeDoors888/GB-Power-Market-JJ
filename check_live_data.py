#!/usr/bin/env python3
"""Quick check to see what data is in the Google Sheet"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SHEET_ID = os.getenv('SHEET_ID', '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
CREDS_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'inner-cinema-credentials.json')

# Connect to Google Sheets
creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets = build('sheets', 'v4', credentials=creds).spreadsheets()

print("\n" + "="*80)
print("📊 GOOGLE SHEET DATA CHECK")
print("="*80)

# Get list of tabs
meta = sheets.get(spreadsheetId=SHEET_ID, includeGridData=False).execute()
print(f"\n✅ Sheet ID: {SHEET_ID}")
print(f"✅ Sheet Title: {meta.get('properties', {}).get('title', 'Unknown')}")
print(f"\n📑 Available Tabs:")
for sheet in meta.get('sheets', []):
    title = sheet['properties']['title']
    print(f"   - {title}")

# Check Live Dashboard data
print("\n" + "-"*80)
print("📈 LIVE DASHBOARD TAB - Sample Data (First 5 rows):")
print("-"*80)

result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live Dashboard!A1:J6'
).execute()

values = result.get('values', [])
if values:
    for i, row in enumerate(values):
        if i == 0:
            # Header row
            print("\n" + " | ".join(f"{str(v):>15}" for v in row))
            print("-" * 170)
        else:
            print(" | ".join(f"{str(v):>15}" for v in row))
else:
    print("❌ No data found in Live Dashboard tab")

# Check for named range
print("\n" + "-"*80)
print("🏷️  NAMED RANGES:")
print("-"*80)
named_ranges = meta.get('namedRanges', [])
if named_ranges:
    for nr in named_ranges:
        name = nr.get('name', 'Unknown')
        range_info = nr.get('range', {})
        sheet_id = range_info.get('sheetId')
        start_row = range_info.get('startRowIndex', 0) + 1
        end_row = range_info.get('endRowIndex', 0)
        start_col = range_info.get('startColumnIndex', 0) + 1
        end_col = range_info.get('endColumnIndex', 0)
        
        # Find sheet name
        sheet_name = "Unknown"
        for s in meta.get('sheets', []):
            if s['properties']['sheetId'] == sheet_id:
                sheet_name = s['properties']['title']
                break
        
        print(f"   ✅ {name}")
        print(f"      Range: {sheet_name}!R{start_row}C{start_col}:R{end_row}C{end_col}")
        print(f"      (Rows {start_row}-{end_row}, Columns {start_col}-{end_col})")
else:
    print("   ❌ No named ranges found")

# Check last update time from one of the raw tabs
print("\n" + "-"*80)
print("🕐 LAST UPDATE INFO:")
print("-"*80)

# Get first row of prices to see if there's recent data
result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Prices!A2:C2'
).execute()

values = result.get('values', [])
if values and len(values[0]) > 0:
    sp = values[0][0] if len(values[0]) > 0 else "N/A"
    ssp = values[0][1] if len(values[0]) > 1 else "N/A"
    sbp = values[0][2] if len(values[0]) > 2 else "N/A"
    print(f"   Settlement Period 1: SSP=£{ssp}/MWh, SBP=£{sbp}/MWh")
    print(f"   ✅ Data appears to be loaded")
else:
    print("   ⚠️  No pricing data found - may need to refresh")

print("\n" + "="*80)
print("🔗 VIEW SHEET: https://docs.google.com/spreadsheets/d/{}/edit".format(SHEET_ID))
print("="*80 + "\n")
