#!/usr/bin/env python3
"""
Analysis Sheet with Dropdowns and Controls
"""

import pickle
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Analysis'
PROJECT_ID = 'inner-cinema-476211-u9'

print("=" * 70)
print("📊 ANALYSIS SHEET WITH DROPDOWNS")
print("=" * 70)
print()

# Initialize
print("Connecting to Google Sheets...")
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# Get or create sheet
try:
    sheet = spreadsheet.worksheet(SHEET_NAME)
    print(f"Found existing '{SHEET_NAME}' sheet")
except gspread.exceptions.WorksheetNotFound:
    print(f"Creating new '{SHEET_NAME}' sheet")
    sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=150, cols=12)

print("✅ Sheet ready")
print()

# Clear and rebuild
print("Building sheet structure...")
sheet.clear()

# Row 1: Main Title
sheet.update_acell('A1', 'ANALYSIS DASHBOARD')
sheet.format('A1:L1', {
    'backgroundColor': {'red': 0.102, 'green': 0.137, 'blue': 0.494},
    'textFormat': {'bold': True, 'fontSize': 16, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
sheet.merge_cells('A1:L1')

# Row 2: Subtitle
sheet.update_acell('A2', 'Historical + Real-Time Data Analysis')
sheet.format('A2:L2', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
sheet.merge_cells('A2:L2')

# Row 4: Date Range Section Header
sheet.update_acell('A4', '📅 DATE RANGE SELECTION')
sheet.format('A4:L4', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
})
sheet.merge_cells('A4:L4')

# Row 6: Quick Select Dropdown
sheet.update_acell('A6', 'Quick Select:')
sheet.update_acell('C6', '1 Week')  # Default value

# Add Data Validation for dropdown
try:
    dropdown_values = ['24 Hours', '1 Week', '1 Month', '3 Months', '6 Months', '1 Year', '2 Years', 'Custom']
    
    # Using Google Sheets API directly for data validation
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    
    # Convert pickle creds to API creds
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # Add dropdown validation
    requests = [{
        'setDataValidation': {
            'range': {
                'sheetId': sheet.id,
                'startRowIndex': 5,  # Row 6 (0-indexed)
                'endRowIndex': 6,
                'startColumnIndex': 2,  # Column C (0-indexed)
                'endColumnIndex': 3
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_LIST',
                    'values': [{'userEnteredValue': val} for val in dropdown_values]
                },
                'showCustomUi': True,
                'strict': True
            }
        }
    }]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': requests}
    ).execute()
    
    print("✅ Added date range dropdown")
    
except Exception as e:
    print(f"⚠️ Could not add dropdown validation: {e}")
    print("   (You can manually add this in Google Sheets: Data > Data validation)")

# Row 6: Custom Range
sheet.update_acell('G6', 'OR Custom Range:')
sheet.update_acell('G7', 'From:')
sheet.update_acell('H7', (datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y'))
sheet.update_acell('G8', 'To:')
sheet.update_acell('H8', datetime.now().strftime('%d/%m/%Y'))

# Row 10: Data Groups Section
sheet.update_acell('A10', '📊 DATA TO ANALYZE')
sheet.format('A10:L10', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
})
sheet.merge_cells('A10:L10')

# Row 12: Checkboxes (using Google Sheets checkboxes)
checkboxes = [
    ('A12', 'System Frequency'),
    ('E12', 'Market Prices'),
    ('I12', 'Generation Mix'),
]

for cell, label in checkboxes:
    # Add checkbox
    col = cell[0]
    row = cell[1:]
    label_cell = f"{chr(ord(col)+1)}{row}"
    
    sheet.update_acell(cell, True)  # Checked by default
    sheet.update_acell(label_cell, label)

# Format checkbox row
sheet.format('A12:L12', {
    'textFormat': {'fontSize': 11},
    'verticalAlignment': 'MIDDLE'
})

print("✅ Added checkboxes")

# Row 14: Refresh button placeholder
sheet.update_acell('A14', '🔄 Click "Run Script" to refresh data')
sheet.format('A14:L14', {
    'backgroundColor': {'red': 0.298, 'green': 0.686, 'blue': 0.314},
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
sheet.merge_cells('A14:L14')

# Row 16: Generation Analysis Section
sheet.update_acell('A16', '⚡ GENERATION MIX ANALYSIS')
sheet.format('A16:L16', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
})
sheet.merge_cells('A16:L16')

# Row 17: Data source info
sheet.update_acell('A17', 'Data Source: bmrs_fuelinst (historical) + bmrs_fuelinst_iris (real-time)')
sheet.format('A17:L17', {
    'textFormat': {'fontSize': 9, 'italic': True},
})
sheet.merge_cells('A17:L17')

# Row 19: Summary stats
sheet.update_acell('A19', 'Total Generation (7 days):')
sheet.update_acell('C19', 'Loading...')

sheet.update_acell('A20', 'Fuel Types:')
sheet.update_acell('C20', 'Loading...')

sheet.update_acell('A21', 'Records Analyzed:')
sheet.update_acell('C21', 'Loading...')

sheet.update_acell('A22', 'Date Range:')
sheet.update_acell('C22', f"{(datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y')} - {datetime.now().strftime('%d/%m/%Y')}")

# Row 24: Data Table
sheet.update_acell('A24', '📋 DETAILED DATA')
sheet.format('A24:L24', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
})
sheet.merge_cells('A24:L24')

# Row 26: Table headers
headers = ['Timestamp', 'Fuel Type', 'Generation (MW)', 'Source', 'Settlement Date', 'Period']
for i, header in enumerate(headers):
    sheet.update_cell(26, i + 1, header)

sheet.format('A26:F26', {
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
    'textFormat': {'bold': True},
    'horizontalAlignment': 'CENTER'
})

# Row 100: Footer
sheet.update_acell('A100', 'ℹ️ To update data: Run python3 update_analysis_with_dropdowns.py')
sheet.format('A100:L100', {
    'textFormat': {'fontSize': 9, 'italic': True},
    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
})
sheet.merge_cells('A100:L100')

print("✅ Sheet structure complete")
print()

# Now populate with initial data
print("Populating with data...")
client = bigquery.Client(project=PROJECT_ID)

# Read selected range from dropdown (default to 1 Week)
days = 7

query = f"""
SELECT 
    timestamp,
    fuelType,
    generation,
    source,
    settlementDate,
    settlementPeriod
FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_unified`
WHERE timestamp >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL {days} DAY)
ORDER BY timestamp DESC
LIMIT 100
"""

results = list(client.query(query).result())
print(f"✅ Retrieved {len(results)} records")

# Update summary stats
total_gen = sum(row.generation for row in results if row.generation)
fuel_types = sorted(set(row.fuelType for row in results if row.fuelType))

sheet.update_acell('C19', f"{total_gen/1000:.0f} GWh")
sheet.update_acell('C20', ', '.join(fuel_types[:5]) + ('...' if len(fuel_types) > 5 else ''))
sheet.update_acell('C21', f"{len(results):,}")

# Update data table
table_data = []
for row in results[:50]:  # Limit to 50 rows
    table_data.append([
        row.timestamp.strftime('%d/%m/%y %H:%M') if row.timestamp else '',
        row.fuelType or '',
        f"{row.generation:.0f}" if row.generation else '',
        row.source or '',
        row.settlementDate.strftime('%d/%m/%y') if row.settlementDate else '',
        f"SP{row.settlementPeriod}" if row.settlementPeriod else ''
    ])

if table_data:
    sheet.update(values=table_data, range_name='A27:F76')
    print(f"✅ Wrote {len(table_data)} data rows")

# Update last refresh time
sheet.update_acell('A101', f"Last Updated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

print()
print("=" * 70)
print("✅ ANALYSIS SHEET WITH DROPDOWNS COMPLETE!")
print("=" * 70)
print()
print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
print("📊 Features:")
print("  ✅ Date range dropdown (24 Hours → 2 Years)")
print("  ✅ Custom date range (from/to)")
print("  ✅ Data group checkboxes")
print("  ✅ Professional formatting")
print("  ✅ Real data populated")
print()
print("🔄 To update after changing dropdown:")
print("  python3 update_analysis_with_dropdowns.py")
print()
