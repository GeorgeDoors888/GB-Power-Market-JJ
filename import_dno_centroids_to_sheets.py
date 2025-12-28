#!/usr/bin/env python3
"""
Import DNO centroids to Google Sheets and configure interactive GeoChart
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv

# Setup
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scopes)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')

print('📊 Importing DNO Centroids to Google Sheets...')
print('='*80)

# Read CSV
print('\n📥 Reading dno_centroids.csv...')
with open('dno_centroids.csv', 'r') as f:
    reader = csv.reader(f)
    data = list(reader)

print(f'   Loaded {len(data)-1} DNO centroids')

# Create or clear DNO_CENTROIDS sheet
print('\n📝 Creating DNO_CENTROIDS tab...')
try:
    sheet = spreadsheet.worksheet('DNO_CENTROIDS')
    sheet.clear()
    print('   Cleared existing DNO_CENTROIDS tab')
except:
    sheet = spreadsheet.add_worksheet(title='DNO_CENTROIDS', rows=20, cols=6)
    print('   Created new DNO_CENTROIDS tab')

# Write data (A1:E15)
print('\n✍️  Writing data to sheet...')
sheet.update('A1:E15', data)

# Add header for value column
sheet.update('F1', [['value']])

# Add value formula in F2
print('📐 Adding value formula...')
formula = '=IF(\'Dashboard V3\'!$B$10="", 0, IF(A2=\'Dashboard V3\'!$B$10, 1, 0))'
sheet.update('F2', [[formula]], value_input_option='USER_ENTERED')

print(f'   Formula: {formula}')

# Copy formula down to F15
print('📋 Copying formula down to F15...')
for row in range(3, 16):
    formula_row = f'=IF(\'Dashboard V3\'!$B$10="", 0, IF(A{row}=\'Dashboard V3\'!$B$10, 1, 0))'
    sheet.update(f'F{row}', [[formula_row]], value_input_option='USER_ENTERED')

# Format header row
print('🎨 Formatting header row...')
sheet.format('A1:F1', {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
    'horizontalAlignment': 'CENTER'
})

print('\n✅ DNO_CENTROIDS tab created and configured!')
print('\n📊 Data preview:')
for i, row in enumerate(data[:5], 1):
    print(f'   {i}. {row[0]:6s} {row[1][:30]:30s} {row[2]:8s} {row[3]:8s}')

print('\n📊 Next steps:')
print('   1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
print('   2. Go to DNO_CENTROIDS tab')
print('   3. Select data range A1:F15')
print('   4. Insert → Chart')
print('   5. Chart type: Geo chart')
print('   6. Display mode: Markers')
print('   7. Setup:')
print('      - Latitude: Column C (lat)')
print('      - Longitude: Column D (lon)')
print('      - Color: Column F (value)')
print('      - Size: Column E (size) - optional')
print('   8. Test: Change Dashboard V3 cell B10 to DNO ID (ENWL, NPG, UKPN, etc.)')
print('\n🎨 The marker for the selected DNO will be highlighted!')
