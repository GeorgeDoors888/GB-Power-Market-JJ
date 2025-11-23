#!/usr/bin/env python3
"""
Setup MPAN Details Section in BESS Sheet
Adds detailed MPAN information display when supplement/core are entered
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def setup_mpan_details_section():
    """Setup MPAN details section in E9-J10"""
    
    print("=" * 80)
    print("SETTING UP MPAN DETAILS SECTION")
    print("=" * 80)
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess = sh.worksheet('BESS')
    
    print("\n📝 Setting up headers in row 9 (E9-J9)...")
    
    # Headers for MPAN details (columns E-J, row 9)
    mpan_headers = [
        'Profile Class',
        'Meter Registration',
        'Voltage Level',
        'DUoS Charging Class',
        'Tariff ID',
        'Loss Factor'
    ]
    
    bess.update(range_name='E9:J9', values=[mpan_headers])
    
    # Format headers
    bess.format('E9:J9', {
        'textFormat': {'bold': True, 'fontSize': 9},
        'backgroundColor': {'red': 0.85, 'green': 0.92, 'blue': 1.0},
        'horizontalAlignment': 'CENTER',
        'wrapStrategy': 'WRAP'
    })
    
    print("   ✅ Headers set")
    
    # Clear and format data row (E10-J10)
    print("\n📝 Formatting data row (E10-J10)...")
    bess.update(range_name='E10:J10', values=[['', '', '', '', '', '']])
    
    bess.format('E10:J10', {
        'backgroundColor': {'red': 1.0, 'green': 0.98, 'blue': 0.9},
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE',
        'wrapStrategy': 'WRAP'
    })
    
    print("   ✅ Data row formatted")
    
    print("\n" + "=" * 80)
    print("✅ MPAN DETAILS SECTION SETUP COMPLETE!")
    print("=" * 80)
    print("\n📋 Layout:")
    print("   Row 9 (E-J): Headers")
    print("     E9: Profile Class")
    print("     F9: Meter Registration")
    print("     G9: Voltage Level") 
    print("     H9: DUoS Charging Class")
    print("     I9: Tariff ID")
    print("     J9: Loss Factor")
    print("\n   Row 10 (E-J): Auto-filled data")
    print("     (Will populate when MPAN details entered in I6/J6)")
    

if __name__ == "__main__":
    setup_mpan_details_section()
