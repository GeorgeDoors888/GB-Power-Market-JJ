#!/usr/bin/env python3
"""
Clear Duplicate Outages from Dashboard

Problem: Multiple scripts writing to outage section causing duplicates
Solution: Clear all outage data, let update_outages_enhanced.py be the single source
"""

import gspread
from google.oauth2.service_account import Credentials

def main():
    print("🧹 CLEARING DUPLICATE OUTAGES FROM DASHBOARD")
    print("=" * 60)
    
    # Connect to Google Sheets
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
    dashboard = sh.worksheet('Dashboard')
    
    print("✅ Connected to Dashboard")
    
    # Read current state
    data = dashboard.get('A23:H60')
    print(f"📊 Found {len(data)} rows of data starting at row 23")
    
    # Find TOTAL rows
    total_rows = []
    for i, row in enumerate(data, start=23):
        if row and len(row) > 0 and 'TOTAL' in str(row[0]):
            total_rows.append(i)
            print(f"   Found TOTAL at row {i}")
    
    if len(total_rows) > 1:
        print(f"\n⚠️  Multiple TOTAL rows detected: {total_rows}")
        print(f"   This indicates multiple scripts writing to the same section")
    
    # Clear everything from row 23 onwards (keep header at row 22)
    print(f"\n🧹 Clearing rows 23-60 (columns A-H)")
    clear_data = [['' for _ in range(8)] for _ in range(38)]  # 38 rows (23-60)
    dashboard.update('A23:H60', clear_data, value_input_option='USER_ENTERED')
    
    print("✅ Cleared duplicate outage data")
    print("\n📝 Next steps:")
    print("   1. Run: python3 update_outages_enhanced.py")
    print("   2. Check for Apps Script triggers in Google Sheets")
    print("   3. Disable any conflicting outage update triggers")

if __name__ == '__main__':
    main()
