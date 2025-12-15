#!/usr/bin/env python3
"""
Test Apps Script getConstraintData() logic locally to identify issues
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

print("🧪 TESTING APPS SCRIPT LOGIC LOCALLY")
print("=" * 80)

# Setup credentials (same as Apps Script uses)
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)

SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

try:
    # Replicate Apps Script logic
    print("1️⃣  Opening spreadsheet...")
    spreadsheet = client.open_by_key(SHEET_ID)
    
    print("2️⃣  Getting Dashboard sheet...")
    dashboard = spreadsheet.worksheet('Dashboard')
    
    print("3️⃣  Reading range A116:H126...")
    boundary_data = dashboard.get('A116:H126')
    
    print(f"4️⃣  Processing {len(boundary_data)} rows...")
    
    constraints = []
    for i, row in enumerate(boundary_data[1:], start=1):  # Skip header
        if len(row) > 0 and row[0]:  # Has boundary ID
            try:
                constraint = {
                    'boundary_id': str(row[0]),
                    'name': str(row[1] if len(row) > 1 else 'Unknown'),
                    'flow_mw': float(row[2]) if len(row) > 2 and row[2] else 0,
                    'limit_mw': float(row[3]) if len(row) > 3 and row[3] else 0,
                    'util_pct': float(row[4]) if len(row) > 4 and row[4] else 0,
                    'margin_mw': float(row[5]) if len(row) > 5 and row[5] else 0,
                    'status': str(row[6]) if len(row) > 6 else 'Unknown',
                    'direction': str(row[7]) if len(row) > 7 else 'N/A'
                }
                constraints.append(constraint)
                print(f"   ✅ Row {i+1}: {constraint['boundary_id']} - {constraint['name']}")
            except Exception as e:
                print(f"   ❌ Row {i+1} error: {e}")
                print(f"      Raw data: {row}")
    
    print(f"\n5️⃣  Result:")
    print(f"   • Successfully parsed: {len(constraints)} constraints")
    
    if len(constraints) > 0:
        print(f"\n📋 Sample constraint data:")
        print(json.dumps(constraints[0], indent=2))
        
        print(f"\n✅ SUCCESS: Data can be parsed correctly")
        print(f"   Apps Script should return: {len(constraints)} constraints")
    else:
        print(f"\n❌ PROBLEM: No constraints parsed!")
        print(f"   Raw data sample: {boundary_data}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
print("\n" + "=" * 80)
print("🔍 Diagnosis:")
print("  • If this script succeeds but map fails → Issue is in Apps Script")
print("  • If this script fails → Issue is in Dashboard data")
print("  • Check Apps Script execution log: Editor → Executions (clock icon)")
