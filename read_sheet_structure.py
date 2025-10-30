#!/usr/bin/env python3
"""Read and display current sheet structure"""
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('jibber_jabber_key.json', scopes=SCOPES)
gc = gspread.authorize(creds)

sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
worksheet = sheet.worksheet('Sheet1')

# Get all values
all_values = worksheet.get_all_values()

print('=' * 100)
print('CURRENT SHEET STRUCTURE - First 35 rows × All columns')
print('=' * 100)
print(f'Total rows: {len(all_values)}')
print(f'Total columns: {len(all_values[0]) if all_values else 0}')
print()

# Show all rows with all columns
for i, row in enumerate(all_values[:35], 1):
    # Pad row to show at least 5 columns
    padded_row = row + [''] * (5 - len(row))
    cols = padded_row[:5]
    
    # Format the row display
    col_a = cols[0][:40] if cols[0] else ''
    col_b = cols[1][:30] if cols[1] else ''
    col_c = cols[2][:35] if cols[2] else ''
    col_d = cols[3][:30] if cols[3] else ''
    col_e = cols[4][:30] if cols[4] else ''
    
    print(f'Row {i:2d}: A: {col_a:40s} | B: {col_b:30s} | C: {col_c:35s}')
    if col_d or col_e:
        print(f'        D: {col_d:30s} | E: {col_e:30s}')

print()
print('=' * 100)
print('KEY CELLS TO CHECK:')
print('=' * 100)
important_cells = {
    'B1': 'Last Updated',
    'B2': 'Settlement Date',
    'B3': 'Settlement Period',
    'A4': 'Header Row',
    'B5': 'Total Generation',
    'B6': 'Renewables',
    'B7': 'Fossil Fuels',
    'B8': 'Net Imports',
    'B9': 'Grid Status/Biomass',
    'A10': 'Fuel Type Header',
    'B11': 'WIND',
    'B12': 'NUCLEAR',
    'A23': 'Interconnector Header',
    'A24': 'First Interconnector',
    'B24': 'First IC Value',
}

for cell, description in important_cells.items():
    value = worksheet.acell(cell).value
    print(f'{cell:4s} ({description:25s}): {value}')
