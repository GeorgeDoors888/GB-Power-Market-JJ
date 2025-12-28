#!/usr/bin/env python3
"""Check fuel and interconnector sparklines use LET formula"""

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

print("=" * 80)
print("🔍 CHECKING LET FORMULA IMPLEMENTATION")
print("=" * 80)

# Check fuel sparkline (D13 = Wind)
print("\n📊 FUEL SPARKLINE (D13 - Wind):\n")
d13 = sheet.acell('D13', value_render_option='FORMULA').value
print(d13[:150] + "..." if len(d13) > 150 else d13)

if '=LET(' in d13:
    print("\n✅ Uses LET formula")
    if 'lo-pad' in d13 and 'hi+pad' in d13:
        print("✅ Has dynamic padding (lo-pad, hi+pad)")
    if 'span*0.15' in d13:
        print("✅ Uses 15% padding calculation")
else:
    print("\n❌ NOT using LET formula")

# Check interconnector sparkline (H13 = ElecLink)
print("\n" + "=" * 80)
print("🔌 INTERCONNECTOR SPARKLINE (H13 - ElecLink):\n")
h13 = sheet.acell('H13', value_render_option='FORMULA').value
print(h13[:150] + "..." if len(h13) > 150 else h13)

if '=LET(' in h13:
    print("\n✅ Uses LET formula")
    if 'lo-pad' in h13 and 'hi+pad' in h13:
        print("✅ Has dynamic padding (lo-pad, hi+pad)")
    if 'span*0.15' in h13:
        print("✅ Uses 15% padding calculation")
else:
    print("\n❌ NOT using LET formula")

print("\n" + "=" * 80)
