#!/usr/bin/env python3
"""
Read current Dashboard layout from Google Sheets to capture user's formatting changes
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

print("📖 READING CURRENT DASHBOARD LAYOUT...")
print("=" * 100)

# Read full Dashboard content
result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1:F50'
).execute()

vals = result.get('values', [])

print(f"\n✅ Read {len(vals)} rows from Dashboard")
print("\n" + "=" * 100)
print("CURRENT DASHBOARD STRUCTURE:")
print("=" * 100)

# Display row by row
for i, row in enumerate(vals, start=1):
    cols = row + [''] * (6 - len(row))  # Pad to 6 columns
    
    # Show non-empty rows with all columns
    if any(col.strip() for col in cols):
        col_display = " | ".join([f"Col {chr(65+j)}: '{cols[j][:40]}...'" if len(cols[j]) > 40 else f"Col {chr(65+j)}: '{cols[j]}'" for j in range(6)])
        print(f"\nRow {i:2d}:")
        print(f"  {col_display}")

print("\n" + "=" * 100)
print("\n📊 ANALYZING LAYOUT...")

# Identify key sections
header_end = 0
fuel_start = 0
fuel_end = 0
ic_start = 0
other_gen_start = 0
outage_start = 0

for i, row in enumerate(vals, start=1):
    if not row:
        continue
    
    row_text = ' '.join(row).upper()
    
    if 'FUEL BREAKDOWN' in row_text:
        fuel_start = i
        print(f"✅ Fuel Breakdown header found at row {i}")
    
    if 'INTERCONNECTOR' in row_text and not ic_start:
        ic_start = i
        print(f"✅ Interconnectors header found at row {i}")
    
    if 'OTHER GENERATOR' in row_text or 'ADDITIONAL GENERATOR' in row_text:
        other_gen_start = i
        print(f"✅ Other Generators section found at row {i}")
    
    if 'OUTAGE' in row_text and i > 50:
        outage_start = i
        print(f"✅ Outages section found at row {i}")

print("\n" + "=" * 100)
print("📋 SECTION SUMMARY:")
print("=" * 100)
print(f"Header Section: Rows 1-{fuel_start-1 if fuel_start else 7}")
print(f"Fuel Breakdown: Row {fuel_start} onwards")
print(f"Interconnectors: Row {ic_start} onwards (Column D)")
if other_gen_start:
    print(f"Other Generators: Row {other_gen_start} onwards")
if outage_start:
    print(f"Outages: Row {outage_start} onwards")

print("\n" + "=" * 100)
print("💾 SAVING STRUCTURE TO FILE...")

# Save to JSON for reference
structure = {
    'total_rows': len(vals),
    'sections': {
        'header_end': fuel_start - 1 if fuel_start else 7,
        'fuel_start': fuel_start,
        'interconnector_start': ic_start,
        'other_generators_start': other_gen_start,
        'outage_start': outage_start
    },
    'data': vals[:30]  # Save first 30 rows
}

with open('dashboard_current_structure.json', 'w') as f:
    json.dump(structure, f, indent=2)

print("✅ Structure saved to dashboard_current_structure.json")

# Check for formatting details
print("\n" + "=" * 100)
print("🎨 CHECKING FORMATTING DETAILS...")
print("=" * 100)

# Get formatting information
try:
    sheet_result = sheets.get(spreadsheetId=SHEET_ID, ranges=['Dashboard!A1:F50'], includeGridData=True).execute()
    
    if 'sheets' in sheet_result and len(sheet_result['sheets']) > 0:
        grid_data = sheet_result['sheets'][0].get('data', [])
        
        if grid_data and len(grid_data) > 0:
            row_data = grid_data[0].get('rowData', [])
            
            print(f"✅ Retrieved formatting for {len(row_data)} rows")
            
            # Check for merged cells, colors, etc.
            for i, row in enumerate(row_data[:20], start=1):
                if 'values' not in row:
                    continue
                
                for j, cell in enumerate(row['values']):
                    if 'effectiveFormat' in cell:
                        fmt = cell['effectiveFormat']
                        
                        # Check for background color
                        if 'backgroundColor' in fmt:
                            bg = fmt['backgroundColor']
                            if any(bg.get(c, 1) < 0.9 for c in ['red', 'green', 'blue']):
                                print(f"  Row {i}, Col {chr(65+j)}: Has background color")
                        
                        # Check for bold
                        if 'textFormat' in fmt and fmt['textFormat'].get('bold'):
                            cell_value = cell.get('formattedValue', '')
                            if cell_value:
                                print(f"  Row {i}, Col {chr(65+j)}: Bold text '{cell_value[:30]}'")
except Exception as e:
    print(f"⚠️ Could not retrieve detailed formatting: {e}")

print("\n" + "=" * 100)
print("✅ DASHBOARD STRUCTURE CAPTURED")
print("=" * 100)
