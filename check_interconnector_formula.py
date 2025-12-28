#!/usr/bin/env python3
"""Check interconnector H13 full formula"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDS_PATH = os.path.expanduser('~/inner-cinema-credentials.json')

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
gc = gspread.authorize(creds)

ss = gc.open_by_key(SPREADSHEET_ID)
sheet = ss.worksheet('Live Dashboard v2')

print("🔌 INTERCONNECTOR H13 FULL FORMULA:\n")
h13 = sheet.acell('H13', value_render_option='FORMULA').value
print(h13)
print("\n" + "="*80)

# Check if it contains "column"
if 'column' in h13:
    print("✅ Uses COLUMN chart (bar chart)")
elif 'line' in h13:
    print("❌ Still using LINE chart")
elif 'winloss' in h13:
    print("❌ Still using WINLOSS chart")

# Check for colors
if '#8A2BE2' in h13:
    print("✅ Has purple color (#8A2BE2)")
if '#DC143C' in h13:
    print("✅ Has red negcolor (#DC143C)")
