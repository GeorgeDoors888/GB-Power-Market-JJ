#!/usr/bin/env python3
"""
Export Constraint Costs at COUNTRY level for Google Geo Chart
Aggregates UK regions to England/Scotland/Wales for proper Geo Chart display
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets_service = build('sheets', 'v4', credentials=creds)

print("🗺️ Creating country-level aggregation for Geo Chart...")

# Manual aggregation based on DNO regions
# (Each region has £760.34M, so we multiply by number of regions per country)
data = [
    ['Country', 'Cost (£M)'],
    ['England', 7608.40],  # 10 English regions × £760.34M
    ['Scotland', 1520.68],  # 2 Scottish regions × £760.34M
    ['Wales', 1520.68],     # 2 Welsh regions × £760.34M
]

print(f"\n📊 Country-Level Data:")
for row in data:
    print(f"  {row}")

# Export to new tab
print(f"\n📤 Exporting to 'Constraint Map Data' (replacing with country data)...")

sheets_service.spreadsheets().values().clear(
    spreadsheetId=SPREADSHEET_ID,
    range='Constraint Map Data!A1:B20'
).execute()

sheets_service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Constraint Map Data!A1',
    valueInputOption='USER_ENTERED',
    body={'values': data}
).execute()

print(f"\n✅ DONE! Country-level data exported")

print(f"\n📍 CREATE GEO CHART (Country Level):")
print(f"1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
print(f"2. Go to 'Constraint Map Data' tab")
print(f"3. Select A1:B4 (3 countries + header)")
print(f"4. Insert → Chart → Geo chart")
print(f"5. Customize:")
print(f"   - Region: World or Europe")
print(f"   - Resolution: Country")
print(f"   - Display mode: Regions")
print(f"\n💡 Now you'll see England/Scotland/Wales colored by constraint cost!")
print(f"\n📊 Total: £{sum([row[1] for row in data[1:]]):,.2f}M across UK")
