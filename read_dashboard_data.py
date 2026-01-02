#!/usr/bin/env python3
"""
Read Wind Forecast Dashboard Data
Connects to Google Sheets and reads all current values to diagnose issues
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# Setup Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

print("🔍 READING WIND FORECAST DASHBOARD")
print("=" * 80)
print()

try:
    # Open spreadsheet
    sh = client.open_by_key(SPREADSHEET_ID)
    
    # List all worksheets
    print("📋 Available Worksheets:")
    print("-" * 80)
    for i, worksheet in enumerate(sh.worksheets(), 1):
        print(f"{i}. {worksheet.title} ({worksheet.row_count} rows × {worksheet.col_count} cols)")
    print()
    
    # Try to find the Wind Data sheet
    sheet_names = [ws.title for ws in sh.worksheets()]
    
    wind_sheet = None
    for name in sheet_names:
        if 'wind' in name.lower() or 'forecast' in name.lower():
            print(f"✅ Found potential wind forecast sheet: '{name}'")
            wind_sheet = sh.worksheet(name)
            break
    
    if not wind_sheet:
        # Default to first sheet
        wind_sheet = sh.get_worksheet(0)
        print(f"⚠️  Using first sheet: '{wind_sheet.title}'")
    
    print()
    print("=" * 80)
    print(f"📊 READING SHEET: {wind_sheet.title}")
    print("=" * 80)
    print()
    
    # Read all data from the sheet
    all_values = wind_sheet.get_all_values()
    
    # Display first 30 rows
    print("First 30 rows of data:")
    print("-" * 80)
    for i, row in enumerate(all_values[:30], 1):
        # Join first 10 columns
        row_display = '\t'.join(str(cell)[:20] for cell in row[:10])
        print(f"Row {i:2d}: {row_display}")
    
    print()
    print("=" * 80)
    print("🔍 SEARCHING FOR #ERROR! VALUES")
    print("=" * 80)
    print()
    
    errors_found = []
    for row_idx, row in enumerate(all_values, 1):
        for col_idx, cell in enumerate(row, 1):
            if '#ERROR!' in str(cell) or '#N/A' in str(cell) or '#REF!' in str(cell):
                col_letter = chr(64 + col_idx) if col_idx <= 26 else f"A{chr(64 + col_idx - 26)}"
                errors_found.append({
                    'Cell': f"{col_letter}{row_idx}",
                    'Row': row_idx,
                    'Col': col_idx,
                    'Error': cell,
                    'Context': ' | '.join(row[max(0, col_idx-2):min(len(row), col_idx+2)])
                })
    
    if errors_found:
        print(f"🔴 Found {len(errors_found)} cells with errors:")
        print("-" * 80)
        for err in errors_found:
            print(f"  {err['Cell']}: {err['Error']}")
            print(f"    Context: {err['Context']}")
            print()
    else:
        print("✅ No #ERROR! values found in sheet")
    
    print()
    print("=" * 80)
    print("📍 KEY CELL VALUES")
    print("=" * 80)
    print()
    
    # Try to read key cells (adjust these based on your layout)
    key_cells = {
        'B3': 'Current Wind MW',
        'B5': 'Capacity at Risk',
        'E5': 'Gen Change Expected',
        'B7': 'WAPE %',
        'E7': 'Revenue Impact',
        'B9': 'Forecast Bias',
        'E9': 'Large Ramp Misses'
    }
    
    for cell_ref, description in key_cells.items():
        try:
            value = wind_sheet.acell(cell_ref).value
            print(f"  {cell_ref} ({description}): {value}")
        except Exception as e:
            print(f"  {cell_ref} ({description}): ERROR - {e}")
    
    print()
    print("=" * 80)
    print("✅ DASHBOARD READ COMPLETE")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error reading dashboard: {e}")
    print()
    print("Possible issues:")
    print("  1. Credentials file 'inner-cinema-credentials.json' not found")
    print("  2. Service account doesn't have access to spreadsheet")
    print("  3. Spreadsheet ID is incorrect")
    print()
    print("To fix:")
    print("  1. Share spreadsheet with service account email")
    print("  2. Verify credentials file exists")
    print("  3. Check spreadsheet ID")
