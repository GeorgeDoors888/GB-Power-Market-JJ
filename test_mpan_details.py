#!/usr/bin/env python3
"""
Test MPAN details population by adding supplement and LLFC to sheet
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

def add_test_mpan_data():
    """Add test supplement and LLFC to trigger MPAN details extraction"""
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess = sh.worksheet('BESS')
    
    print("Adding test MPAN data to sheet...")
    
    # Add supplement 'A' (LV) and LLFC '0840' (LV)
    bess.update(range_name='I6', values=[['A']])
    bess.update(range_name='J6', values=[['0840']])
    
    print("✅ Added:")
    print("   I6: A (LV supplement)")
    print("   J6: 0840 (LV LLFC)")
    print("\nNow run: python3 dno_lookup_python.py")

if __name__ == "__main__":
    add_test_mpan_data()
