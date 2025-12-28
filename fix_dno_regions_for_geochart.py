#!/usr/bin/env python3
"""
Fix DNO region names to be Google Sheets geo chart compatible
Maps DNO areas to UK postcodes/cities that Google recognizes
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'DNO Constraint Costs'
PROJECT_ID = 'inner-cinema-476211-u9'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery.readonly'
]

# Map DNO areas to Google-recognized UK locations (major cities in each DNO area)
DNO_TO_GEOCHART_LOCATION = {
    'London': 'GB-LND',  # London region code
    'South East England': 'GB-SEE',  # South East England
    'East England': 'GB-EE',  # East of England
    'Southern England': 'GB-SO',  # South England
    'South West England': 'GB-SW',  # South West England
    'South Wales': 'GB-WLS',  # Wales
    'North Wales, Merseyside and Cheshire': 'GB-NW',  # North West England
    'West Midlands': 'GB-WM',  # West Midlands
    'East Midlands': 'GB-EM',  # East Midlands
    'Yorkshire': 'GB-YH',  # Yorkshire and the Humber
    'North East England': 'GB-NE',  # North East England
    'North West England': 'GB-NW',  # North West England
    'South and Central Scotland': 'GB-SCT',  # Scotland
    'North Scotland': 'GB-SCT',  # Scotland
}

def update_sheet_with_location_codes():
    """Update existing sheet to add location codes column"""
    print('🗺️  Fixing DNO regions for Google Sheets geo chart')
    print('='*80)
    
    # Connect to Sheets
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)
    
    print(f'✅ Opened sheet: {SHEET_NAME}')
    
    # Get current data
    all_values = worksheet.get_all_values()
    headers = all_values[0]
    data_rows = all_values[1:]
    
    # Find area_name column (column C = index 2)
    area_col_idx = 2
    
    # Add "Location Code" header if not exists
    if 'Location Code' not in headers:
        headers.insert(3, 'Location Code')
        worksheet.update([headers], 'A1')
        print('✅ Added "Location Code" column')
    
    # Update each row with location code
    updates = []
    for idx, row in enumerate(data_rows, start=2):  # Start at row 2 (skip header)
        area_name = row[area_col_idx] if len(row) > area_col_idx else ''
        location_code = DNO_TO_GEOCHART_LOCATION.get(area_name, 'GB')
        
        # Update column D (index 3) with location code
        cell = f'D{idx}'
        updates.append({'range': cell, 'values': [[location_code]]})
    
    # Batch update
    if updates:
        worksheet.batch_update(updates)
        print(f'✅ Updated {len(updates)} location codes')
    
    # Add instruction note
    instruction_cell = 'M2'
    instruction = '''GEO CHART SETUP:
1. Select D2:D15 (Location Code column) + F2:F15 (Total Cost)
2. Insert → Chart → Geo chart
3. Chart Editor → Geo → Region: United Kingdom
4. Display mode: Regions
5. Color scale: Light blue (min) to Dark blue (max)

NOTE: This shows UK REGIONS (not exact DNO boundaries).
For accurate DNO polygons, use: dno_constraint_map.html'''
    
    worksheet.update([[instruction]], instruction_cell)
    worksheet.format('M2', {
        'textFormat': {'bold': True},
        'wrapStrategy': 'WRAP',
        'verticalAlignment': 'TOP'
    })
    
    print('✅ Added geo chart instructions')
    print('\n' + '='*80)
    print('✅ COMPLETE: Sheet updated with UK location codes')
    print('='*80)
    print(f'\nView: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=273713365')
    print('\nNEXT STEPS:')
    print('1. Select cells D2:D15 (Location Code)')
    print('2. Hold Ctrl and select F2:F15 (Total Cost)')
    print('3. Insert → Chart → Geo chart')
    print('4. Set Region to: United Kingdom')
    print('\n⚠️  IMPORTANT: Geo chart will show UK regions (not exact DNO boundaries)')

if __name__ == '__main__':
    update_sheet_with_location_codes()
