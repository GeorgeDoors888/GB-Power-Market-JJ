#!/usr/bin/env python3
"""
Populate BESS Sheet with Sample Data
Sets up DNO, voltage, MPAN, and postcode for testing
"""

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

# Sample data for a BESS site in West Midlands
SAMPLE_DATA = {
    'postcode': 'B1 1AA',  # Birmingham city center
    'mpan': '1405566778899',  # NGED West Midlands
    'dno_name': 'NGED West Midlands',
    'voltage': 'HV'
}

def populate_bess_sheet():
    """Populate BESS sheet with sample data"""
    
    print('\n📝 POPULATING BESS SHEET WITH SAMPLE DATA')
    print('='*80)
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scope)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SHEET_ID)
    
    # Get or create BESS sheet
    try:
        bess_sheet = ss.worksheet('BESS')
    except:
        bess_sheet = ss.add_worksheet('BESS', rows=100, cols=20)
        print('   ✅ Created BESS sheet')
    
    # Set headers and data
    print('\n📋 Setting headers...')
    headers = [
        ['Postcode', 'MPAN ID', 'DNO', 'DNO ID', 'Region', 'Contact'],
        ['', '', '', '', '', ''],
        ['', '', '', '', '', ''],
        ['Voltage', 'Red Rate', 'Amber Rate', 'Green Rate', '', '']
    ]
    bess_sheet.update(values=headers, range_name='A1:F4')
    
    # Set sample data
    print('📝 Setting sample data...')
    data = [
        [SAMPLE_DATA['postcode'], SAMPLE_DATA['mpan'], SAMPLE_DATA['dno_name'], '14', 'West Midlands', 'ngedwestmidlands.com'],
        ['', '', '', '', '', ''],
        ['', '', '', '', '', ''],
        [SAMPLE_DATA['voltage'], '', '', '', '', '']
    ]
    bess_sheet.update(values=data, range_name='A6:F9')
    
    # Format headers
    print('🎨 Formatting...')
    bess_sheet.format('A1:F1', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })
    
    bess_sheet.format('A4:D4', {
        'textFormat': {'bold': True, 'fontSize': 11},
        'backgroundColor': {'red': 0.81, 'green': 0.89, 'blue': 0.95},
        'horizontalAlignment': 'CENTER'
    })
    
    # Add voltage dropdown
    print('📝 Adding voltage dropdown...')
    voltage_options = ['LV', 'HV', 'EHV']
    request = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": bess_sheet.id,
                        "startRowIndex": 8,  # Row 9 (0-indexed)
                        "endRowIndex": 9,
                        "startColumnIndex": 0,  # Column A
                        "endColumnIndex": 1
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": opt} for opt in voltage_options
                            ]
                        },
                        "showCustomUi": True,
                        "strict": True
                    }
                }
            }
        ]
    }
    ss.batch_update(request)
    
    print('\n✅ BESS sheet populated!')
    print('\nSample data:')
    print(f'   Postcode: {SAMPLE_DATA["postcode"]}')
    print(f'   MPAN: {SAMPLE_DATA["mpan"]}')
    print(f'   DNO: {SAMPLE_DATA["dno_name"]}')
    print(f'   Voltage: {SAMPLE_DATA["voltage"]}')
    print(f'\n🔗 View: https://docs.google.com/spreadsheets/d/{SHEET_ID}/')
    print('='*80 + '\n')

if __name__ == '__main__':
    populate_bess_sheet()
