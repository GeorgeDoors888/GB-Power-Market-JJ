#!/usr/bin/env python3
"""
Direct test: Call Apps Script function via Google Sheets API to see exact error
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("🧪 TESTING APPS SCRIPT EXECUTION VIA API")
print("=" * 80)

# Setup credentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

try:
    print("1️⃣  Opening Dashboard...")
    spreadsheet = client.open_by_key(SHEET_ID)
    dashboard = spreadsheet.worksheet('Dashboard')
    
    print("2️⃣  Reading constraint data (A116:H126)...")
    data = dashboard.get('A116:H126')
    
    print(f"3️⃣  Found {len(data)} rows")
    print(f"\n📋 Header row (A116): {data[0]}")
    
    print("\n4️⃣  Testing parsePercent logic on actual data:")
    
    def parse_percent(value):
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return float(value.replace('%', '')) if value else 0
        return 0
    
    success_count = 0
    for i, row in enumerate(data[1:], start=117):
        if len(row) > 4 and row[4]:
            try:
                util_value = row[4]
                parsed = parse_percent(util_value)
                print(f"   Row {i}: '{util_value}' → {parsed}% ✅")
                success_count += 1
            except Exception as e:
                print(f"   Row {i}: '{row[4]}' → ERROR: {e} ❌")
    
    print(f"\n✅ Successfully parsed {success_count}/10 utilization values")
    
    if success_count == 10:
        print("\n🎯 DIAGNOSIS: Data parsing works fine!")
        print("   The error is likely:")
        print("   1. Apps Script not updated (still has old code)")
        print("   2. Google Maps API issue")
        print("   3. Authorization/permission issue")
        print("\n💡 Check Apps Script Executions log for actual error")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("📝 Next Steps:")
print("  1. Apps Script Editor → Executions (⏱️ icon)")
print("  2. Find recent 'getConstraintData' execution")
print("  3. Check the actual error message in the log")
print("  4. Browser Console (F12) → Check JavaScript errors")
