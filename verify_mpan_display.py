#!/usr/bin/env python3
"""
Verify MPAN details are correctly displayed in BESS sheet
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def verify_mpan_details():
    """Read and display MPAN details section"""
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess = sh.worksheet('BESS')
    
    print("=" * 80)
    print("BESS SHEET - MPAN DETAILS VERIFICATION")
    print("=" * 80)
    
    # Read full section (rows 5-10, columns A-J)
    data = bess.get('A5:J10')
    
    print("\n📋 Row 5 (Headers):")
    if len(data) > 0:
        row5 = data[0] + [''] * (10 - len(data[0]))
        for i, val in enumerate(row5):
            if val:
                print(f"   {chr(65+i)}5: {val}")
    
    print("\n📊 Row 6 (Input Data):")
    if len(data) > 1:
        row6 = data[1] + [''] * (10 - len(data[1]))
        for i, val in enumerate(row6):
            if val:
                print(f"   {chr(65+i)}6: {val}")
    
    print("\n📋 Row 9 (MPAN Detail Headers):")
    if len(data) > 4:
        row9 = data[4] + [''] * (10 - len(data[4]))
        for i in range(4, 10):  # E-J
            if i < len(row9):
                print(f"   {chr(65+i)}9: {row9[i]}")
    
    print("\n📊 Row 10 (MPAN Detail Values):")
    if len(data) > 5:
        row10 = data[5] + [''] * (10 - len(data[5]))
        for i in range(4, 10):  # E-J
            if i < len(row10):
                val = row10[i] if row10[i] else '(empty)'
                print(f"   {chr(65+i)}10: {val}")
    
    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    verify_mpan_details()
