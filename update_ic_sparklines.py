#!/usr/bin/env python3
"""
Update Interconnector Sparklines to use Data_Hidden sheet
Column H rows 13-22 need SPARKLINE formulas referencing Data_Hidden rows 11-20
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'

def update_ic_sparklines():
    """Write interconnector sparkline formulas"""
    print("=" * 80)
    print("📊 UPDATING INTERCONNECTOR SPARKLINES")
    print("=" * 80)
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    
    # IC mapping: Dashboard row -> Data_Hidden row
    # Dashboard rows 13-22 = Data_Hidden rows 11-20
    ic_config = [
        (13, 11, '🇫🇷 ElecLink'),
        (14, 12, '🇮🇪 East-West'),
        (15, 13, '🇫🇷 IFA'),
        (16, 14, '🇮🇪 Greenlink'),
        (17, 15, '🇫🇷 IFA2'),
        (18, 16, '🇮🇪 Moyle'),
        (19, 17, '🇳🇱 BritNed'),
        (20, 18, '🇧🇪 Nemo'),
        (21, 19, '🇳🇴 NSL'),
        (22, 20, '🇩🇰 Viking Link')
    ]
    
    print("\n✍️  Writing formulas to column H...")
    for dash_row, data_row, name in ic_config:
        # Sparkline formula referencing Data_Hidden (data in MW)
        # No fixed scale - let sparkline auto-scale to data range for PROPORTIONAL bars
        # Positive = import (green), Negative = export (red)
        formula = f'=SPARKLINE(Data_Hidden!A{data_row}:AV{data_row},{{"charttype","column";"color","#2ecc71";"negcolor","#e74c3c";"axis",true}})'
        
        cell = f'H{dash_row}'
        sheet.update_acell(cell, formula)
        print(f'   ✅ {cell}: {name}')
    
    print("\n" + "=" * 80)
    print("✅ INTERCONNECTOR SPARKLINES UPDATED")
    print("=" * 80)
    print("\nSparklines now show:")
    print("  🟢 Green bars = Import (positive MW)")
    print("  🔴 Red bars = Export (negative MW)")
    print(f"\nView: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

if __name__ == '__main__':
    update_ic_sparklines()
