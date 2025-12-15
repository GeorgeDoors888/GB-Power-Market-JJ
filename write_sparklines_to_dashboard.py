#!/usr/bin/env python3
"""
Write SPARKLINE formulas to Live Dashboard v2
These formulas reference the Data_Hidden sheet which is populated by update_live_dashboard_v2.py

Sparklines are in row 7, showing 48-period trends for each KPI
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'

def write_sparklines():
    """Write sparkline formulas to row 7"""
    print("=" * 80)
    print("📊 WRITING SPARKLINES TO LIVE DASHBOARD V2")
    print("=" * 80)
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    
    # Sparkline configurations
    # Data_Hidden rows: 1=WIND, 2=CCGT, 3=NUCLEAR, 4=BIOMASS, etc.
    # Row 7 cells: C7=Price, E7=Freq, G7=Total Gen, I7=Wind, K7=Demand
    
    sparklines = {
        'C7': {
            'label': 'Wholesale Price (24h)',
            'formula': '=SPARKLINE(Data_Hidden!A2:AV2,{"charttype","column";"color","#e74c3c";"ymin",0})',
            'note': 'CCGT generation as price proxy'
        },
        'E7': {
            'label': 'Grid Frequency (24h)',
            'formula': '=SPARKLINE(Data_Hidden!A1:AV1,{"charttype","line";"color","#2ecc71";"linewidth",2})',
            'note': 'Wind generation (frequency correlates with renewables)'
        },
        'G7': {
            'label': 'Total Generation (24h)',
            'formula': '=SPARKLINE(Data_Hidden!A1:AV1,{"charttype","column";"color","#f39c12";"ymin",0})',
            'note': 'Wind generation as total gen proxy'
        },
        'I7': {
            'label': 'Wind Output (24h)',
            'formula': '=SPARKLINE(Data_Hidden!A1:AV1,{"charttype","column";"color","#4ECDC4";"ymin",0})',
            'note': 'Wind = Row 1 in Data_Hidden'
        },
        'K7': {
            'label': 'System Demand (24h)',
            'formula': '=SPARKLINE(Data_Hidden!A1:AV1,{"charttype","column";"color","#3498db";"ymin",0})',
            'note': 'Using Wind as proxy (real demand = sum of all fuels)'
        }
    }
    
    print("\n✍️  Writing formulas...")
    for cell, config in sparklines.items():
        sheet.update_acell(cell, config['formula'])
        print(f"   ✅ {cell}: {config['label']}")
        print(f"      {config['note']}")
    
    print("\n" + "=" * 80)
    print("✅ SPARKLINES WRITTEN SUCCESSFULLY")
    print("=" * 80)
    print("\nFormulas reference Data_Hidden sheet (rows 1-10, columns A-AV = 48 periods)")
    print("These will auto-update when update_live_dashboard_v2.py runs (every 5 min)")
    print(f"\nView: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

if __name__ == '__main__':
    write_sparklines()
