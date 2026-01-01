#!/usr/bin/env python3
"""
Create Analysis Sheet Database Structure
Creates 4 tabs for party categorization system:
- Categories: BSC/CUSC role definitions
- Parties: List of all parties (Elexon signatories)
- Party_Category: Link table (many-to-many relationships)
- Party_Wide: Boolean flags view (TRUE/FALSE for each category)
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"  # Main dashboard
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# BSC/CUSC Categories (19 roles)
CATEGORIES = [
    {"id": 1, "name": "Generator", "description": "Physical electricity generator (BSC/CUSC signatory)", "code": "GEN"},
    {"id": 2, "name": "Supplier", "description": "Licensed electricity supplier (BSC Party)", "code": "SUP"},
    {"id": 3, "name": "Network Operator", "description": "Transmission or distribution network operator", "code": "NO"},
    {"id": 4, "name": "Interconnector", "description": "Cross-border electricity interconnector", "code": "INT"},
    {"id": 5, "name": "Virtual Lead Party", "description": "Virtual aggregated unit (batteries, flexible assets)", "code": "VLP"},
    {"id": 6, "name": "Storage Operator", "description": "Energy storage facility operator (batteries, pumped hydro)", "code": "STO"},
    {"id": 7, "name": "Distribution System Operator", "description": "DSO (UKPN, SSEN, etc.)", "code": "DSO"},
    {"id": 8, "name": "Transmission System Operator", "description": "National Energy System Operator (NESO)", "code": "TSO"},
    {"id": 9, "name": "Non-Physical Trader", "description": "Trading without physical generation/demand", "code": "NPT"},
    {"id": 10, "name": "Party Agent", "description": "Agent acting on behalf of BSC parties", "code": "PA"},
    {"id": 11, "name": "Data Aggregator", "description": "Aggregates metering data for settlement", "code": "DA"},
    {"id": 12, "name": "Meter Operator", "description": "Installs and maintains electricity meters", "code": "MOP"},
    {"id": 13, "name": "Data Collector", "description": "Collects meter readings (HH/NHH)", "code": "DC"},
    {"id": 14, "name": "Licensed Distributor", "description": "Distribution license holder (DNO)", "code": "LDSO"},
    {"id": 15, "name": "Supplier Agent", "description": "Agent providing services to suppliers", "code": "SA"},
    {"id": 16, "name": "Half Hourly Data Collector", "description": "HH metering data collection", "code": "HHDC"},
    {"id": 17, "name": "Non Half Hourly Data Collector", "description": "NHH metering data collection", "code": "NHHDC"},
    {"id": 18, "name": "Meter Administrator", "description": "Meter asset management", "code": "MA"},
    {"id": 19, "name": "Balancing Mechanism Unit", "description": "Registered BM unit for balancing services", "code": "BMU"}
]

def create_analysis_sheets():
    """Create all Analysis sheet tabs"""

    print("🔐 Authenticating with Google Sheets...")
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)

    print(f"📊 Opening spreadsheet: {SHEET_ID}")
    wb = gc.open_by_key(SHEET_ID)

    # Create Categories tab
    print("\n1️⃣ Creating Categories tab...")
    create_categories_tab(wb)

    # Create Parties tab
    print("\n2️⃣ Creating Parties tab...")
    create_parties_tab(wb)

    # Create Party_Category link table
    print("\n3️⃣ Creating Party_Category tab...")
    create_party_category_tab(wb)

    # Create Party_Wide boolean view
    print("\n4️⃣ Creating Party_Wide tab...")
    create_party_wide_tab(wb)

    print("\n✅ All Analysis tabs created successfully!")
    print("\nNext steps:")
    print("1. Populate Parties tab with Elexon BSC signatories")
    print("2. Query NESO APIs for generator/interconnector data")
    print("3. Build Party_Category links")
    print("4. Formulas in Party_Wide will auto-populate")

def create_categories_tab(wb):
    """Create Categories tab with BSC/CUSC role definitions"""

    # Check if tab exists
    try:
        sheet = wb.worksheet('Categories')
        print("   ⚠️  Categories tab exists, clearing...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print("   ➕ Creating new Categories tab...")
        sheet = wb.add_worksheet(title='Categories', rows=100, cols=10)

    # Headers
    headers = [['Category ID', 'Category Name', 'Description', 'Code', 'BSC/CUSC', 'Active', 'Notes']]
    sheet.update('A1:G1', headers)

    # Format headers
    sheet.format('A1:G1', {
        'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
        'horizontalAlignment': 'CENTER'
    })

    # Write categories
    data = []
    for cat in CATEGORIES:
        data.append([
            cat['id'],
            cat['name'],
            cat['description'],
            cat['code'],
            'BSC' if cat['id'] <= 15 else 'CUSC',  # Rough split
            'TRUE',
            ''
        ])

    sheet.update(f'A2:G{len(data)+1}', data)

    # Auto-resize columns
    sheet.columns_auto_resize(0, 6)

    # Freeze header row
    sheet.freeze(rows=1)

    print(f"   ✅ Categories tab created with {len(CATEGORIES)} categories")

def create_parties_tab(wb):
    """Create Parties tab for Elexon BSC signatories"""

    try:
        sheet = wb.worksheet('Parties')
        print("   ⚠️  Parties tab exists, clearing...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print("   ➕ Creating new Parties tab...")
        sheet = wb.add_worksheet(title='Parties', rows=1000, cols=15)

    # Headers
    headers = [[
        'Party ID',
        'Party Name',
        'Short Name',
        'Categories',  # Comma-separated list (formula)
        'Registration Date',
        'Status',
        'BSC Party ID',
        'Company Number',
        'Address',
        'Contact',
        'Website',
        'Is Generator',
        'Is Supplier',
        'Is Storage',
        'Notes'
    ]]
    sheet.update('A1:O1', headers)

    # Format headers
    sheet.format('A1:O1', {
        'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
        'horizontalAlignment': 'CENTER'
    })

    # Sample data (will be populated from Elexon API)
    sample_data = [
        ['P001', 'Example Generator Ltd', 'ExGen', '', '2020-01-15', 'Active', 'EGEN', '12345678', '', '', '', '', '', '', 'Sample data'],
        ['P002', 'Example Supplier PLC', 'ExSup', '', '2019-06-20', 'Active', 'ESUP', '87654321', '', '', '', '', '', '', 'Sample data'],
    ]
    sheet.update('A2:O3', sample_data)

    # Freeze header row
    sheet.freeze(rows=1)

    # Auto-resize columns
    sheet.columns_auto_resize(0, 14)

    print(f"   ✅ Parties tab created (ready for data import)")

def create_party_category_tab(wb):
    """Create Party_Category link table (many-to-many)"""

    try:
        sheet = wb.worksheet('Party_Category')
        print("   ⚠️  Party_Category tab exists, clearing...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print("   ➕ Creating new Party_Category tab...")
        sheet = wb.add_worksheet(title='Party_Category', rows=5000, cols=8)

    # Headers
    headers = [[
        'Party ID',
        'Category Name',
        'Source',  # Manual, Elexon API, NESO API, etc.
        'Confidence',  # High, Medium, Low
        'Verified',  # TRUE/FALSE
        'Added Date',
        'Added By',
        'Notes'
    ]]
    sheet.update('A1:H1', headers)

    # Format headers
    sheet.format('A1:H1', {
        'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
        'horizontalAlignment': 'CENTER'
    })

    # Sample data
    sample_data = [
        ['P001', 'Generator', 'Elexon API', 'High', 'TRUE', '2025-12-30', 'System', ''],
        ['P001', 'Balancing Mechanism Unit', 'NESO API', 'High', 'TRUE', '2025-12-30', 'System', ''],
        ['P002', 'Supplier', 'Elexon API', 'High', 'TRUE', '2025-12-30', 'System', ''],
    ]
    sheet.update('A2:H4', sample_data)

    # Data validation for Category Name (dropdown from Categories tab)
    # Note: Using batch_update for data validation (format() doesn't support dataValidation)
    try:
        validation_rule = {
            'setDataValidation': {
                'range': {
                    'sheetId': sheet.id,
                    'startRowIndex': 1,
                    'endRowIndex': 5000,
                    'startColumnIndex': 1,
                    'endColumnIndex': 2
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_RANGE',
                        'values': [{'userEnteredValue': '=Categories!$B$2:$B$20'}]
                    },
                    'strict': True,
                    'showCustomUi': True
                }
            }
        }
        sheet.spreadsheet.batch_update({'requests': [validation_rule]})
    except Exception as e:
        print(f"   ⚠️  Data validation skipped: {e}")

    # Freeze header row
    sheet.freeze(rows=1)

    # Auto-resize columns
    sheet.columns_auto_resize(0, 7)

    print(f"   ✅ Party_Category link table created")

def create_party_wide_tab(wb):
    """Create Party_Wide boolean flags view"""

    try:
        sheet = wb.worksheet('Party_Wide')
        print("   ⚠️  Party_Wide tab exists, clearing...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print("   ➕ Creating new Party_Wide tab...")
        sheet = wb.add_worksheet(title='Party_Wide', rows=1000, cols=30)

    # Build headers: Party ID + all category names as columns
    category_names = [cat['name'] for cat in CATEGORIES]
    headers = [['Party ID', 'Party Name'] + category_names + ['Total Categories']]

    sheet.update(f'A1:{chr(65+len(headers[0])-1)}1', headers)

    # Format headers
    sheet.format(f'A1:{chr(65+len(headers[0])-1)}1', {
        'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
        'horizontalAlignment': 'CENTER'
    })

    # Sample formulas (row 2 as template)
    # Party ID and Name lookup from Parties tab
    formulas_row2 = [
        ['P001', '=VLOOKUP(A2,Parties!A:B,2,FALSE)']
    ]

    # Add formula for each category column (check if Party_Category has this combination)
    for i, cat in enumerate(CATEGORIES):
        col_letter = chr(67 + i)  # Start from column C
        formula = f'=IF(COUNTIFS(Party_Category!$A:$A,$A2,Party_Category!$B:$B,{col_letter}$1)>0,"TRUE","FALSE")'
        formulas_row2[0].append(formula)

    # Total categories formula
    end_col = chr(67 + len(CATEGORIES) - 1)
    total_formula = f'=COUNTIF(C2:{end_col}2,"TRUE")'
    formulas_row2[0].append(total_formula)

    sheet.update(f'A2:{chr(65+len(formulas_row2[0])-1)}2', formulas_row2)

    # Freeze header row and first two columns
    sheet.freeze(rows=1, cols=2)

    # Auto-resize columns
    sheet.columns_auto_resize(0, len(headers[0])-1)

    # Conditional formatting for TRUE/FALSE
    sheet.format('C2:Z1000', {
        'horizontalAlignment': 'CENTER'
    })

    print(f"   ✅ Party_Wide boolean view created with {len(CATEGORIES)} category columns")
    print(f"   📋 Formula template in row 2 (copy down for more parties)")

if __name__ == '__main__':
    try:
        create_analysis_sheets()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
