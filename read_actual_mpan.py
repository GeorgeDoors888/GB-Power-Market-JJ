#!/usr/bin/env python3
"""
Read current BESS sheet data with actual MPAN entries
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def read_bess_sheet():
    """Read BESS sheet with actual MPAN data"""
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess = sh.worksheet('BESS')
    
    print("=" * 80)
    print("BESS SHEET - CURRENT DATA")
    print("=" * 80)
    
    # Read rows 5-10
    data = bess.get('A5:J10')
    
    print("\n📋 Row 5 (Headers):")
    if len(data) > 0:
        row5 = data[0] + [''] * (10 - len(data[0]))
        print("   " + " | ".join([f"{chr(65+i)}: {row5[i][:20]:<20}" for i in range(10) if row5[i]]))
    
    print("\n📊 Row 6 (Data):")
    if len(data) > 1:
        row6 = data[1] + [''] * (10 - len(data[1]))
        for i in range(10):
            if row6[i]:
                print(f"   {chr(65+i)}6: {row6[i]}")
    
    print("\n📋 Row 9 (MPAN Headers):")
    if len(data) > 4:
        row9 = data[4] + [''] * (10 - len(data[4]))
        print("   " + " | ".join([f"{chr(65+i)}: {row9[i][:20]:<20}" for i in range(4, 10) if i < len(row9) and row9[i]]))
    
    print("\n📊 Row 10 (MPAN Values):")
    if len(data) > 5:
        row10 = data[5] + [''] * (10 - len(data[5]))
        for i in range(4, 10):
            if i < len(row10):
                val = row10[i] if row10[i] else '(empty)'
                print(f"   {chr(65+i)}10: {val}")
    
    print("\n" + "=" * 80)
    print("KEY MPAN DATA:")
    print("=" * 80)
    if len(data) > 1:
        row6 = data[1] + [''] * (10 - len(data[1]))
        print(f"\n📍 Supplement (I6): {row6[8] if len(row6) > 8 else 'Not found'}")
        print(f"📍 MPAN Core (J6): {row6[9] if len(row6) > 9 else 'Not found'}")
        
        # Parse the supplement/MPAN data
        supplement = row6[8] if len(row6) > 8 else ''
        mpan_core = row6[9] if len(row6) > 9 else ''
        
        if supplement:
            print(f"\n🔍 PARSING SUPPLEMENT: {supplement}")
            if len(supplement) >= 8:
                print(f"   Profile Class: {supplement[:2]}")
                print(f"   MTC: {supplement[2:5]}")
                print(f"   LLFC: {supplement[5:8]}")
                if len(supplement) > 8:
                    print(f"   Additional: {supplement[8:]}")
        
        if mpan_core:
            print(f"\n🔍 PARSING MPAN CORE: {mpan_core}")
            if len(mpan_core) == 13:
                print(f"   Distributor ID: {mpan_core[:2]}")
                print(f"   Unique ID: {mpan_core[2:]}")

if __name__ == "__main__":
    read_bess_sheet()
