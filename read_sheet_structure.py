#!/usr/bin/env python3
"""
Read GB Live Dashboard structure to determine correct cell locations
"""
from google.oauth2 import service_account
import gspread

SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SA_FILE = '/home/george/inner-cinema-credentials.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = service_account.Credentials.from_service_account_file(SA_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

print("=" * 80)
print("📊 GB LIVE DASHBOARD STRUCTURE ANALYSIS")
print("=" * 80)

# Read header area (rows 1-10)
print("\n🔍 HEADER SECTION (Rows 1-10):")
print("-" * 80)
for row in range(1, 11):
    cells = sheet.range(f'A{row}:K{row}')
    values = [cell.value if cell.value else '' for cell in cells]
    if any(values):
        print(f"Row {row:2d}: {' | '.join(f'{v[:20]:20s}' for v in values[:11])}")

# Read KPI section (rows 5-10)
print("\n💡 KEY METRICS SECTION (Rows 5-10, detailed):")
print("-" * 80)
for row in range(5, 11):
    for col_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
        cell = sheet.acell(f'{col_letter}{row}')
        if cell.value:
            bg_color = cell.format.backgroundColor if hasattr(cell, 'format') else 'unknown'
            print(f"  {col_letter}{row}: '{cell.value}' (bg: {bg_color})")

# Read generation mix section
print("\n⚡ GENERATION MIX SECTION (Rows 10-20):")
print("-" * 80)
for row in range(10, 21):
    cells = sheet.range(f'A{row}:F{row}')
    values = [cell.value if cell.value else '' for cell in cells]
    if any(values):
        print(f"Row {row:2d}: {' | '.join(str(v)[:15] for v in values)}")

# Specifically check for "Last Updated" text
print("\n🔎 SEARCHING FOR 'Updated:' TIMESTAMP:")
print("-" * 80)
all_cells = sheet.get_all_values()
for row_idx, row in enumerate(all_cells[:20], 1):
    for col_idx, value in enumerate(row[:15], 1):
        if value and 'Updated' in str(value):
            col_letter = chr(64 + col_idx)
            print(f"  Found at {col_letter}{row_idx}: '{value}'")

# Check specific cells mentioned in your error
print("\n🎯 SPECIFIC CELLS CHECK:")
print("-" * 80)
check_cells = ['A2', 'B2', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'B7', 'B10', 'C10']
for cell_addr in check_cells:
    cell = sheet.acell(cell_addr)
    print(f"  {cell_addr}: '{cell.value}'")

print("\n" + "=" * 80)
print("✅ ANALYSIS COMPLETE")
print("=" * 80)
