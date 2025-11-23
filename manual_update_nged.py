#!/usr/bin/env python3
"""
Manual update for MPAN 00801520 / 2412345678904
Based on LLFC 520 (HV) - likely NGED West Midlands
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def manual_update_nged_wm():
    """Manually update with NGED West Midlands info for LLFC 520"""
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess = sh.worksheet('BESS')
    
    print("=" * 80)
    print("MANUAL UPDATE FOR NGED WEST MIDLANDS - LLFC 520 (HV)")
    print("=" * 80)
    
    # Update DNO info in C6:H6
    # NGED West Midlands (WMID)
    dno_row = [[
        'NGED-WM',
        'National Grid Electricity Distribution – West Midlands',
        'WMID',
        'WMID',
        'C',
        'Midlands'
    ]]
    bess.update(dno_row, 'C6:H6')
    print("✅ Updated C6:H6 with NGED-WM info")
    
    # Update B6 with proper MPAN ID (14 for NGED-WM)
    bess.update([['14']], 'B6')
    print("✅ Updated B6 with MPAN ID 14")
    
    # Update A10 voltage to HV
    bess.update([['HV (6.6-33kV)']], 'A10')
    print("✅ Updated A10 to HV voltage")
    
    # Update MPAN details in E10:J10
    # Profile Class 00 = HH metered
    # MTC 801 = Non-Domestic
    # LLFC 520 = HV tariff
    # Loss factor ~2.5% for HV
    details_row = [[
        '00',                    # Profile Class
        '801 (HH Metered)',     # Meter Registration
        'HV',                    # Voltage Level
        'Non-Domestic HH',       # DUoS Charging Class
        '520',                   # Tariff ID (LLFC)
        '1.025'                  # Loss Factor
    ]]
    bess.update(details_row, 'E10:J10')
    print("✅ Updated E10:J10 with MPAN details")
    
    print("\n📊 Updated Information:")
    print("   DNO: NGED West Midlands (NGED-WM)")
    print("   MPAN ID: 14")
    print("   Profile Class: 00 (Half-hourly metered)")
    print("   MTC: 801 (Non-Domestic)")
    print("   LLFC: 520 (HV tariff)")
    print("   Voltage: HV (6.6-33kV)")
    print("   Loss Factor: 1.025 (2.5% line losses)")
    
    print("\n" + "=" * 80)
    print("✅ MANUAL UPDATE COMPLETE!")
    print("=" * 80)
    print("\nNote: Rates (B10:D10) not updated - need to look up LLFC 520 rates")
    print("      for NGED-WM in the appropriate dataset location.")

if __name__ == "__main__":
    manual_update_nged_wm()
