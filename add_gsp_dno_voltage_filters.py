#!/usr/bin/env python3
"""
Add GSP, DNO, and Voltage Level filters to Search interface
Quick patch to add critical missing filters
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDS_FILE = "inner-cinema-credentials.json"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# GSP Regions (14 in GB)
GSP_REGIONS = [
    "_A - Eastern",
    "_B - East Midlands",
    "_C - London",
    "_D - Merseyside and North Wales",
    "_E - Midlands",
    "_F - Northern",
    "_G - North Western",
    "_H - Southern",
    "_J - South Eastern",
    "_K - South Wales",
    "_L - South Western",
    "_M - Yorkshire",
    "_N - Southern Scotland",
    "_P - Northern Scotland"
]

# DNO Operators
DNO_OPERATORS = [
    "Electricity North West (ENWL)",
    "Northern Powergrid Northeast (NPGN)",
    "Northern Powergrid Yorkshire (NPGY)",
    "Scottish Power Energy Networks - Manweb (SPM)",
    "Scottish Power Energy Networks - Distribution (SPD)",
    "Scottish & Southern Electricity Networks - Hydro (SSEH)",
    "Scottish & Southern Electricity Networks - Southern (SSES)",
    "UK Power Networks - Eastern (EPN)",
    "UK Power Networks - London (LPN)",
    "UK Power Networks - South Eastern (SPN)",
    "NGED West Midlands (WMID) - formerly WPD",
    "NGED East Midlands (EMID) - formerly WPD",
    "NGED South Wales (SWALES) - formerly WPD",
    "NGED South West (SWEST) - formerly WPD"
]

# Voltage Levels
VOLTAGE_LEVELS = [
    "LV (<1 kV)",
    "HV (11 kV)",
    "HV (33 kV)",
    "EHV (66 kV)",
    "EHV (132 kV)",
    "Transmission (275 kV)",
    "Transmission (400 kV)"
]

def format_dropdown_list(items):
    """Format with None, All at top, rest sorted"""
    sorted_items = sorted(set(items), key=lambda x: str(x).lower())
    return ["None", "All"] + sorted_items

def main():
    print("=" * 80)
    print("🔧 ADDING GSP, DNO, VOLTAGE FILTERS TO SEARCH SHEET")
    print("=" * 80)
    print()

    # Connect to Google Sheets
    credentials = Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(credentials)
    wb = gc.open_by_key(SHEET_ID)
    sheet = wb.worksheet('Search')

    print("1️⃣ Adding new filter rows...")

    # Insert 3 new rows after row 14 (Project Status)
    # New rows will be 15, 16, 17

    # Add labels and default values
    new_rows = [
        ['GSP Region:', 'None'],
        ['DNO Operator:', 'None'],
        ['Voltage Level:', 'None']
    ]

    sheet.insert_rows(new_rows, 15)
    print("   ✅ Inserted 3 new filter rows (15-17)")

    # Move search buttons from row 16 to row 19
    print("\n2️⃣ Moving search buttons to row 19...")
    sheet.update(values=[['🔍 Search', '🧹 Clear', 'ℹ️ Help', '📊 Generate Report']], range_name='A19:D19')
    print("   ✅ Buttons moved")

    # Update results section headers (now starting at row 21)
    print("\n3️⃣ Updating results section...")
    results_header = [
        ['', '', '', '', '', '', '', '', '', '', ''],
        ['📊 SEARCH RESULTS', '', 'Last Search:', '', '', 'Results:', '0'],
        ['', '', '', '', '', '', '', '', '', '', ''],
        [
            'Record Type', 'Identifier (ID)', 'Name', 'Role',
            'Organization', 'Extra Info', 'Capacity (MW)', 'Fuel Type',
            'Status', 'Dataset Source', 'Match Score'
        ]
    ]
    sheet.update(values=results_header, range_name='A21:K24')
    print("   ✅ Results section updated (now rows 21-24)")

    # Get or create SearchDropdowns sheet
    print("\n4️⃣ Updating dropdown data...")
    try:
        dropdown_sheet = wb.worksheet('SearchDropdowns')
    except:
        dropdown_sheet = wb.add_worksheet(title='SearchDropdowns', rows=500, cols=10)

    # Format dropdown lists
    gsp_list = format_dropdown_list(GSP_REGIONS)
    dno_list = format_dropdown_list(DNO_OPERATORS)
    voltage_list = format_dropdown_list(VOLTAGE_LEVELS)

    # Write to new columns (H, I, J)
    dropdown_sheet.update(values=[[x] for x in gsp_list], range_name='H1:H50')
    dropdown_sheet.update(values=[[x] for x in dno_list], range_name='I1:I50')
    dropdown_sheet.update(values=[[x] for x in voltage_list], range_name='J1:J50')

    print(f"   ✅ Loaded {len(gsp_list)} GSP regions")
    print(f"   ✅ Loaded {len(dno_list)} DNO operators")
    print(f"   ✅ Loaded {len(voltage_list)} voltage levels")

    # Apply data validations
    print("\n5️⃣ Applying dropdown validations...")

    sheet_id = sheet.id

    requests = [
        # B15: GSP Region
        {
            'setDataValidation': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 14,
                    'endRowIndex': 15,
                    'startColumnIndex': 1,
                    'endColumnIndex': 2
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_RANGE',
                        'values': [{'userEnteredValue': f'=SearchDropdowns!H1:H{len(gsp_list)}'}]
                    },
                    'showCustomUi': True,
                    'strict': False
                }
            }
        },
        # B16: DNO Operator
        {
            'setDataValidation': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 15,
                    'endRowIndex': 16,
                    'startColumnIndex': 1,
                    'endColumnIndex': 2
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_RANGE',
                        'values': [{'userEnteredValue': f'=SearchDropdowns!I1:I{len(dno_list)}'}]
                    },
                    'showCustomUi': True,
                    'strict': False
                }
            }
        },
        # B17: Voltage Level
        {
            'setDataValidation': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 16,
                    'endRowIndex': 17,
                    'startColumnIndex': 1,
                    'endColumnIndex': 2
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_RANGE',
                        'values': [{'userEnteredValue': f'=SearchDropdowns!J1:J{len(voltage_list)}'}]
                    },
                    'showCustomUi': True,
                    'strict': False
                }
            }
        }
    ]

    wb.batch_update({'requests': requests})
    print("   ✅ Validations applied")

    # Update frozen rows (now need to freeze to row 24)
    print("\n6️⃣ Updating frozen rows...")
    freeze_request = {
        'updateSheetProperties': {
            'properties': {
                'sheetId': sheet_id,
                'gridProperties': {'frozenRowCount': 24}
            },
            'fields': 'gridProperties.frozenRowCount'
        }
    }
    wb.batch_update({'requests': [freeze_request]})
    print("   ✅ Frozen rows updated to 24")

    print()
    print("=" * 80)
    print("✅ GSP, DNO, VOLTAGE FILTERS ADDED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("📋 New Search Criteria Layout:")
    print("   Row 15: GSP Region (14 regions)")
    print("   Row 16: DNO Operator (14 DNOs)")
    print("   Row 17: Voltage Level (7 levels)")
    print("   Row 19: [Buttons]")
    print("   Row 24: Results table headers")
    print("   Row 25+: Results data")
    print()
    print("🔄 Next Steps:")
    print("   1. Update search_interface.gs to read B15-B17")
    print("   2. Update advanced_search_tool_enhanced.py to filter by GSP/DNO/voltage")
    print("   3. Test search with new filters")
    print()

if __name__ == "__main__":
    main()
