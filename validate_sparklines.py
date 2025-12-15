#!/usr/bin/env python3
"""
Validate that sparkline formulas are present in Google Sheets after manual entry
Run this AFTER manually pasting formulas from sparkline_formulas_to_paste.txt
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'

def validate_sparklines():
    """Check that all sparkline formulas are present"""
    print("=" * 80)
    print("🔍 VALIDATING SPARKLINE FORMULAS")
    print("=" * 80)
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).worksheet('GB Live')
    
    # Fuel types (Column C)
    fuel_labels = [
        '💨 Wind', '🔥 CCGT', '⚛️ Nuclear', '🌱 Biomass', '❓ Other',
        '💧 Pumped', '🌊 Hydro', '🔥 OCGT', '⚫ Coal', '🛢️ Oil'
    ]
    
    # Interconnectors (Column F)
    ic_labels = [
        '🇫🇷 France', '🇮🇪 Ireland', '🇳🇱 Netherlands', '🏴 East-West', '🇧🇪 Belgium (Nemo)',
        '🇧🇪 Belgium (Elec)', '🇫🇷 IFA2', '🇳🇴 Norway (NSL)', '🇩🇰 Viking Link', '🇮🇪 Greenlink'
    ]
    
    print("\n📊 COLUMN C - FUEL TYPE SPARKLINES:")
    c_count = 0
    for idx, row in enumerate(range(11, 21)):
        a_val = sheet.cell(row, 1).value  # Fuel name
        c_val = sheet.cell(row, 3).value  # Sparkline
        
        if c_val and '=SPARKLINE' in str(c_val) and 'Data_Hidden' in str(c_val):
            print(f"   ✅ Row {row} ({fuel_labels[idx]}): Formula present")
            c_count += 1
        else:
            print(f"   ❌ Row {row} ({fuel_labels[idx]}): {c_val}")
    
    print(f"\n📊 COLUMN F - INTERCONNECTOR SPARKLINES:")
    f_count = 0
    for idx, row in enumerate(range(11, 21)):
        d_val = sheet.cell(row, 4).value  # IC name
        f_val = sheet.cell(row, 6).value  # Sparkline
        
        if f_val and '=SPARKLINE' in str(f_val) and 'Data_Hidden' in str(f_val):
            print(f"   ✅ Row {row} ({ic_labels[idx]}): Formula present")
            f_count += 1
        else:
            print(f"   ❌ Row {row} ({ic_labels[idx]}): {f_val}")
    
    print("\n" + "=" * 80)
    print("📈 VALIDATION SUMMARY:")
    print("=" * 80)
    print(f"   Column C (Fuel): {c_count}/10 formulas present")
    print(f"   Column F (IC):   {f_count}/10 formulas present")
    
    if c_count == 10 and f_count == 10:
        print("\n✅ SUCCESS! All 20 sparkline formulas are present!")
        print("\n📋 Next steps:")
        print("   1. Open Google Sheet in browser to verify charts display")
        print("   2. Run: python3 update_bg_live_dashboard.py")
        print("   3. Confirm formulas persist after update (columns A-B, D-E change, C, F stay)")
        return True
    else:
        print(f"\n❌ INCOMPLETE: {20 - c_count - f_count} formulas missing")
        print("\n📋 Action required:")
        print("   1. Open sparkline_formulas_to_paste.txt")
        print("   2. Copy-paste missing formulas into Google Sheets")
        print("   3. Run this validation script again")
        return False

if __name__ == '__main__':
    validate_sparklines()
