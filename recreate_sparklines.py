#!/usr/bin/env python3
"""
Recreate the 6 sparkline bar charts in Live Dashboard v2
"""

import gspread
from google.oauth2 import service_account

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SA_FILE = 'inner-cinema-credentials.json'

# Sparkline formulas
sparklines = [
    ('N14', 'BM Avg Price', '=SPARKLINE(Data_Hidden!B27:AW27,{"charttype","bar"})'),
    ('N16', 'Vol-Wtd Avg', '=SPARKLINE(Data_Hidden!B28:AW28,{"charttype","bar"})'),
    ('N18', 'MID Price', '=SPARKLINE(Data_Hidden!B29:AW29,{"charttype","bar"})'),
    ('R14', 'BM-MID Spread', '=SPARKLINE(Data_Hidden!B32:AW32,{"charttype","bar"})'),
    ('R16', 'Sys Sell', '=SPARKLINE(Data_Hidden!B31:AW31,{"charttype","bar"})'),
    ('R18', 'Sys Buy', '=SPARKLINE(Data_Hidden!B30:AW30,{"charttype","bar"})'),
]

print("🔧 Connecting to Google Sheets...")
creds = service_account.Credentials.from_service_account_file(
    SA_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
dashboard = spreadsheet.worksheet('Live Dashboard v2')
print("✅ Connected\n")

print("📊 Creating sparkline bar charts...\n")
success_count = 0

for cell, label, formula in sparklines:
    try:
        dashboard.update(values=[[formula]], range_name=cell, raw=False)  # New gspread API
        print(f"  ✅ {cell} ({label})")
        success_count += 1
    except Exception as e:
        print(f"  ❌ {cell} ({label}): {str(e)[:80]}")

print(f"\n🎉 Created {success_count}/6 sparklines!")
print("\nOpen Live Dashboard v2 to verify the sparklines are displaying:")
print("https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=687718775")
