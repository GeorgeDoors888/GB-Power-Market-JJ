#!/usr/bin/env python3
"""
Read current BESS sheet data to see updated MPAN information
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def read_current_mpan_data():
    """Read and display current MPAN data from sheet"""
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess = sh.worksheet('BESS')
    
    print("=" * 80)
    print("READING CURRENT BESS SHEET DATA")
    print("=" * 80)
    
    # Read rows 5-10
    data = bess.get('A5:J10')
    
    print("\n📋 Row 5 (Headers):")
    if len(data) > 0:
        print("   " + " | ".join(data[0]))
    
    print("\n📊 Row 6 (Current Data):")
    if len(data) > 1:
        row6 = data[1] + [''] * (10 - len(data[1]))
        print(f"   A6 (Postcode): {row6[0]}")
        print(f"   B6 (MPAN ID): {row6[1]}")
        print(f"   I6 (Supplement): {row6[8]}")
        print(f"   J6 (MPAN Core): {row6[9]}")
    
    print("\n📋 Row 9 (MPAN Detail Headers):")
    if len(data) > 4:
        row9 = data[4] + [''] * (10 - len(data[4]))
        print(f"   E9-J9: {' | '.join(row9[4:10])}")
    
    print("\n📊 Row 10 (MPAN Detail Values):")
    if len(data) > 5:
        row10 = data[5] + [''] * (10 - len(data[5]))
        print(f"   E10: {row10[4]} (Profile Class)")
        print(f"   F10: {row10[5]} (Meter Registration)")
        print(f"   G10: {row10[6]} (Voltage Level)")
        print(f"   H10: {row10[7]} (DUoS Charging Class)")
        print(f"   I10: {row10[8]} (Tariff ID)")
        print(f"   J10: {row10[9]} (Loss Factor)")
    
    print("\n" + "=" * 80)
    
    # Parse the actual MPAN data
    if len(data) > 1:
        supplement = data[1][8] if len(data[1]) > 8 else ''
        mpan_core = data[1][9] if len(data[1]) > 9 else ''
        
        print("\n🔍 MPAN DATA ANALYSIS:")
        print(f"   Supplement (I6): '{supplement}'")
        print(f"   MPAN Core (J6): '{mpan_core}'")
        
        if supplement:
            print(f"\n   ℹ️  Supplement '{supplement}' breakdown:")
            if len(supplement) >= 2:
                profile_class = supplement[:2]
                mtc = supplement[2:5] if len(supplement) >= 5 else ''
                llfc = supplement[5:9] if len(supplement) >= 9 else ''
                print(f"      Profile Class: {profile_class}")
                print(f"      MTC (Meter Timeswitch Code): {mtc}")
                print(f"      LLFC: {llfc}")
        
        if mpan_core:
            print(f"\n   ℹ️  MPAN Core '{mpan_core}' is {len(mpan_core)} digits")
            if len(mpan_core) >= 2:
                distributor_id = mpan_core[:2]
                print(f"      Distributor ID: {distributor_id}")
    
    print("=" * 80)

if __name__ == "__main__":
    read_current_mpan_data()
