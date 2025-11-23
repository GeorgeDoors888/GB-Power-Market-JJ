#!/usr/bin/env python3
"""
Reset BESS Sheet Layout
Fixes formatting for DNO Refresh and HH Data Generator sections
"""

import gspread
from google.oauth2.service_account import Credentials

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def reset_bess_layout():
    """Reset BESS sheet to correct layout for DNO and HH Data"""
    
    print("=" * 80)
    print("RESETTING BESS SHEET LAYOUT")
    print("=" * 80)
    
    # Connect
    print("\n🔐 Connecting to Google Sheets...")
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess = sh.worksheet('BESS')
    print("   ✅ Connected")
    
    # Clear existing content in rows 1-20 to start fresh
    print("\n🗑️  Clearing rows 1-20...")
    bess.batch_clear(['A1:H20'])
    
    # ROW 1-3: Title/Header space
    print("\n📝 Setting up header section...")
    bess.update(range_name='A1:H1', values=[['BESS - Battery Energy Storage System', '', '', '', '', '', '', '']])
    bess.format('A1:H1', {
        'textFormat': {'bold': True, 'fontSize': 14},
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })
    
    # ROW 4: Status messages (initially empty)
    print("📝 Setting up status row...")
    bess.update(range_name='A4:H4', values=[['Status updates appear here', '', '', '', '', '', '', '']])
    bess.format('A4:H4', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'italic': True}
    })
    
    # ROW 5: Headers for DNO section
    print("📝 Setting up DNO section headers...")
    headers_row5 = [['Postcode', 'MPAN ID', 'DNO Key', 'DNO Name', 'Short Code', 'Market Part.', 'GSP Group ID', 'GSP Group']]
    bess.update(range_name='A5:H5', values=headers_row5)
    bess.format('A5:H5', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1.0},
        'horizontalAlignment': 'CENTER'
    })
    
    # ROW 6: DNO Information (INPUT cells A6, B6 / OUTPUT cells C6-H6)
    print("📝 Setting up DNO information row...")
    row6_data = [['', '', '', '', '', '', '', '']]  # Empty - will be filled by user/script
    bess.update(range_name='A6:H6', values=row6_data)
    
    # Format INPUT cells (A6, B6) - white background, editable
    bess.format('A6:B6', {
        'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
        'borders': {
            'top': {'style': 'SOLID', 'width': 2},
            'bottom': {'style': 'SOLID', 'width': 2},
            'left': {'style': 'SOLID', 'width': 2},
            'right': {'style': 'SOLID', 'width': 2}
        }
    })
    
    # Format OUTPUT cells (C6-H6) - light yellow background
    bess.format('C6:H6', {
        'backgroundColor': {'red': 1.0, 'green': 0.95, 'blue': 0.8}
    })
    
    # ROW 7-8: Spacing
    bess.update(range_name='A7:H8', values=[['', '', '', '', '', '', '', ''], ['', '', '', '', '', '', '', '']])
    
    # ROW 9: Voltage & DUoS Rates
    print("📝 Setting up voltage and rates row...")
    headers_row9 = [['Voltage Level', 'Red Rate (p/kWh)', 'Amber Rate (p/kWh)', 'Green Rate (p/kWh)', '', '', '', '']]
    bess.update(range_name='A9:H9', values=headers_row9)
    bess.format('A9:D9', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1.0},
        'horizontalAlignment': 'CENTER'
    })
    
    # ROW 10: Voltage and Rates data
    print("📝 Setting up voltage/rates data row...")
    row10_data = [['', '', '', '', '', '', '', '']]  # Empty - will be filled
    bess.update(range_name='A10:H10', values=row10_data)
    
    # Format A10 as INPUT (voltage dropdown)
    bess.format('A10', {
        'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
        'borders': {
            'top': {'style': 'SOLID', 'width': 2},
            'bottom': {'style': 'SOLID', 'width': 2},
            'left': {'style': 'SOLID', 'width': 2},
            'right': {'style': 'SOLID', 'width': 2}
        }
    })
    
    # Format B10-D10 as OUTPUT (rates)
    bess.format('B10:D10', {
        'backgroundColor': {'red': 1.0, 'green': 0.95, 'blue': 0.8}
    })
    
    # Add data validation for voltage (LV/HV/EHV) - using batch_update
    # Note: Manual dropdown setup in Google Sheets is more reliable
    # We'll just add a note in the cell for now
    print("   ℹ️  Note: Add voltage dropdown manually (LV/HV/EHV) to cell A10")
    
    # ROW 11: Time bands header
    print("📝 Setting up time bands section...")
    bess.update(range_name='A11:C11', values=[['Weekday Times:', '', '']])
    bess.format('A11', {'textFormat': {'bold': True}})
    
    # ROW 12: Time band labels
    time_labels = [['RED (Peak)', 'AMBER (Mid)', 'GREEN (Off-Peak)']]
    bess.update(range_name='A12:C12', values=time_labels)
    bess.format('A12:C12', {
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    bess.format('A12', {'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}})
    bess.format('B12', {'backgroundColor': {'red': 1.0, 'green': 0.9, 'blue': 0.7}})
    bess.format('C12', {'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}})
    
    # ROWS 13-14: Time band details (will be filled by script)
    time_placeholder = [
        ['', '', ''],
        ['', '', '']
    ]
    bess.update(range_name='A13:C14', values=time_placeholder)
    
    # ROW 15: HH Profile Parameters header
    print("📝 Setting up HH profile parameters...")
    bess.update(range_name='A15:H15', values=[['', '', '', '', '', '', '', '']])
    bess.update(range_name='A16:B16', values=[['HH Profile Parameters:', '']])
    bess.format('A16:B16', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 1.0}
    })
    
    # ROWS 17-19: Parameter labels and values
    params = [
        ['Min kW', '500'],
        ['Avg kW', '1500'],
        ['Max kW', '2500']
    ]
    bess.update(range_name='A17:B19', values=params)
    
    # Format labels (column A)
    bess.format('A17:A19', {
        'textFormat': {'bold': True},
        'horizontalAlignment': 'RIGHT'
    })
    
    # Format INPUT values (column B) - white background, editable
    bess.format('B17:B19', {
        'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
        'horizontalAlignment': 'CENTER',
        'borders': {
            'top': {'style': 'SOLID', 'width': 2},
            'bottom': {'style': 'SOLID', 'width': 2},
            'left': {'style': 'SOLID', 'width': 2},
            'right': {'style': 'SOLID', 'width': 2}
        }
    })
    
    # ROW 20: Spacing / Summary area (will be filled by HH generator)
    bess.update(range_name='A20:H20', values=[['', '', '', '', '', '', '', '']])
    
    print("\n" + "=" * 80)
    print("✅ BESS SHEET LAYOUT RESET COMPLETE!")
    print("=" * 80)
    print("\n📋 Summary of changes:")
    print("   Row 1:     Title header")
    print("   Row 4:     Status messages")
    print("   Row 5-6:   DNO lookup (INPUT: A6, B6 | OUTPUT: C6-H6)")
    print("   Row 9-10:  Voltage & rates (INPUT: A10 | OUTPUT: B10-D10)")
    print("   Row 11-14: Time bands (auto-filled by DNO lookup)")
    print("   Row 17-19: HH parameters (INPUT: B17-B19)")
    print("   Row 20+:   HH generation summary (auto-filled)")
    print("\n🎯 Next steps:")
    print("   1. Type postcode in A6 (e.g., 'SW2 5UP')")
    print("   2. Select voltage in A10 (LV/HV/EHV)")
    print("   3. Click 'Refresh DNO' button")
    print("   4. Edit B17-B19 if needed")
    print("   5. Click 'Generate HH Data' button")
    
    return bess


if __name__ == "__main__":
    reset_bess_layout()
