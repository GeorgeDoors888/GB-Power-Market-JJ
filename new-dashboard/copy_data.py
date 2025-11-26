#!/usr/bin/env python3
"""
Copy key data from original dashboard to new V2 dashboard
Preserves: KPIs, generation types, interconnectors, BESS structure
"""

import gspread
from google.oauth2 import service_account

CREDS_FILE = "../inner-cinema-credentials.json"
OLD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
NEW_SHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
BESS_SHEET_ID = "1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx"

def copy_data():
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    
    print("=" * 80)
    print("COPYING DATA TO NEW DASHBOARD")
    print("=" * 80)
    
    # Open sheets
    old_sheet = gc.open_by_key(OLD_SHEET_ID)
    new_sheet = gc.open_by_key(NEW_SHEET_ID)
    bess_sheet = gc.open_by_key(BESS_SHEET_ID)
    
    old_dashboard = old_sheet.worksheet('Dashboard')
    new_dashboard = new_sheet.sheet1
    new_dashboard.update_title('Dashboard')
    
    print("\n📊 Copying Dashboard structure...")
    
    # Copy key sections
    sections = {
        'KPIs': ('A1:H10', 'Generation types, demand, frequency'),
        'Interconnectors': ('A20:F30', 'Interconnector flows'),
        'Constraints': ('A116:H126', 'Transmission constraints'),
        'Outages': ('A130:E150', 'Current outages')
    }
    
    for name, (range_ref, desc) in sections.items():
        print(f"\n   Copying {name} ({desc})...")
        try:
            data = old_dashboard.get(range_ref)
            if data:
                new_dashboard.update(range_ref, data)
                print(f"   ✅ {name}: {len(data)} rows")
        except Exception as e:
            print(f"   ⚠️  {name}: {e}")
    
    print("\n📊 Setting up BESS sheet...")
    
    # Create BESS sheet structure
    try:
        bess_ws = bess_sheet.sheet1
        bess_data = bess_ws.get('A1:T100')
        
        # Create BESS sheet in new dashboard
        try:
            new_bess = new_sheet.worksheet('BESS')
        except:
            new_bess = new_sheet.add_worksheet(title='BESS', rows=100, cols=20)
        
        if bess_data:
            new_bess.update('A1', bess_data)
            print(f"   ✅ BESS data: {len(bess_data)} rows copied")
            
    except Exception as e:
        print(f"   ⚠️  BESS: {e}")
    
    print("\n" + "=" * 80)
    print("COPY COMPLETE")
    print("=" * 80)
    print(f"\n🔗 New Dashboard: https://docs.google.com/spreadsheets/d/{NEW_SHEET_ID}")
    print("\nNext: Set up automated data refresh")

if __name__ == '__main__':
    copy_data()
