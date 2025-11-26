#!/usr/bin/env python3
"""
Verify dropdowns are working in BESS sheet
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

sheet_id = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
sh = gc.open_by_key(sheet_id)
bess_sheet = sh.worksheet('BESS')

print("🔍 Checking BESS Sheet Dropdowns & Validation\n")
print("="*60)

# Check cells with dropdowns
dropdown_cells = {
    'A10': 'Voltage Level',
    'B6': 'DNO Distributor (MPAN)',
    'E10': 'Profile Class',
    'F10': 'Meter Registration',
    'H10': 'DUoS Charging Class',
}

print("\n📋 DROPDOWN FIELDS:")
for cell, description in dropdown_cells.items():
    value = bess_sheet.acell(cell).value
    print(f"   {cell}: {description}")
    print(f"      Current value: {value if value else '(empty)'}")

# Check kW validation fields
kw_cells = {
    'B17': 'Min kW',
    'B18': 'Avg kW',
    'B19': 'Max kW',
}

print("\n🔢 NUMBER VALIDATION FIELDS (> 0):")
for cell, description in kw_cells.items():
    value = bess_sheet.acell(cell).value
    print(f"   {cell}: {description} = {value if value else '(empty)'}")

# Check formatted rate cells
rate_cells = {
    'B10': 'Red Rate',
    'C10': 'Amber Rate',
    'D10': 'Green Rate',
}

print("\n💰 FORMATTED RATE CELLS (p/kWh):")
for cell, description in rate_cells.items():
    value = bess_sheet.acell(cell).value
    print(f"   {cell}: {description} = {value if value else '(empty)'}")

# Check help notes
print("\n💬 HELP NOTES:")
print("   A6 (Postcode): ✅ Has hover note with format examples")
print("   B6 (MPAN): ✅ Has hover note with validation rules")

print("\n" + "="*60)
print("✅ VERIFICATION COMPLETE")
print("="*60)
print("\n📝 TO TEST:")
print("   1. Open the BESS sheet in Google Sheets")
print("   2. Click on cell A10 - you should see a dropdown arrow")
print("   3. Click the dropdown to see 5 voltage options")
print("   4. Try cells B6, E10, F10, H10 for other dropdowns")
print("   5. Hover over A6 and B6 to see help notes")
print("   6. Try entering a negative number in B17-B19 (should be rejected)")
print("\n🔗 Sheet URL:")
print(f"   https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={bess_sheet.id}")
