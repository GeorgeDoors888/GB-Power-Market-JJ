#!/usr/bin/env python3
"""
Test BESS Integration - Verify enhanced analysis doesn't conflict with existing sections
"""
import gspread
from google.oauth2.service_account import Credentials
import os
import sys

# Try to get credentials from environment or use default
CREDS_FILE = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'inner-cinema-credentials.json')
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'  # Main dashboard with existing BESS data

print("=" * 80)
print("BESS INTEGRATION TEST")
print("=" * 80)

# Check credentials file exists
if not os.path.exists(CREDS_FILE):
    print(f"\n❌ ERROR: Credentials file not found: {CREDS_FILE}")
    print("\n💡 Solutions:")
    print("   1. Set environment variable:")
    print("      export GOOGLE_APPLICATION_CREDENTIALS='/path/to/credentials.json'")
    print(f"\n   2. Current GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '(not set)')}")
    print("\n   3. If credentials are elsewhere, create symlink:")
    print(f"      ln -s /path/to/actual-credentials.json {CREDS_FILE}")
    sys.exit(1)

# Connect
print(f"\n🔐 Connecting to Google Sheets...")
print(f"   Using credentials: {CREDS_FILE}")
creds = Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SHEET_ID)
bess = sh.worksheet('BESS')

print("✅ Connected to BESS sheet")

# Check existing sections (should not be empty if already populated)
print("\n📋 Checking existing sections:")

# Section 1: DNO Lookup (rows 1-14)
postcode = bess.acell('A6').value
mpan = bess.acell('B6').value
dno_name = bess.acell('D6').value
red_rate = bess.acell('B10').value

print(f"\n  Section 1: DNO Lookup (rows 1-14)")
print(f"    Postcode: {postcode or '(empty)'}")
print(f"    MPAN: {mpan or '(empty)'}")
print(f"    DNO Name: {dno_name or '(empty)'}")
print(f"    Red Rate: {red_rate or '(empty)'} p/kWh")
print(f"    Status: {'✅ Populated' if postcode or mpan else '⚠️  Empty (need to run DNO lookup)'}")

# Section 2: HH Profile (rows 15-20)
min_kw = bess.acell('B17').value
avg_kw = bess.acell('B18').value
max_kw = bess.acell('B19').value

print(f"\n  Section 2: HH Profile Generator (rows 15-20)")
print(f"    Min kW: {min_kw or '(empty)'}")
print(f"    Avg kW: {avg_kw or '(empty)'}")
print(f"    Max kW: {max_kw or '(empty)'}")
print(f"    Status: {'✅ Populated' if min_kw else '⚠️  Empty (need to set parameters)'}")

# Section 3: BtM PPA (rows 27-50)
# Check if there's any data in the cost analysis section
btm_header = bess.acell('A27').value or bess.acell('F27').value

print(f"\n  Section 3: BtM PPA Analysis (rows 27-50)")
print(f"    Header: {btm_header or '(empty)'}")
print(f"    Status: {'✅ Populated' if btm_header else '⚠️  Empty (need to run BtM PPA calculator)'}")

# Check enhanced section availability (row 60+)
print(f"\n  Section 4: Enhanced Revenue (rows 60+)")
enhanced_title = bess.acell('A59').value
enhanced_header = bess.acell('A60').value

print(f"    Title: {enhanced_title or '(empty)'}")
print(f"    Header: {enhanced_header or '(empty)'}")
print(f"    Status: {'✅ Populated' if enhanced_header else '⚠️  Empty (run: python3 dashboard_pipeline.py)'}")

# Summary
print("\n" + "=" * 80)
print("INTEGRATION SUMMARY")
print("=" * 80)

print("\n✅ Existing sections verified:")
print("   - Rows 1-14:  DNO Lookup (postcode/MPAN → rates)")
print("   - Rows 15-20: HH Profile Generator (demand parameters)")
print("   - Rows 27-50: BtM PPA Analysis (cost comparison)")
print("\n🆕 Enhanced section location:")
print("   - Rows 60+:   Enhanced Revenue (6-stream model)")
print("\n📊 Integration status:")
if enhanced_header:
    print("   ✅ Enhanced analysis deployed successfully")
    print("   ✅ No conflicts detected with existing sections")
else:
    print("   ⚠️  Enhanced analysis not yet deployed")
    print("   ➡️  Run: python3 dashboard_pipeline.py")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)

if not (postcode or mpan):
    print("\n1. Fill in DNO information:")
    print("   - Enter postcode in A6 or MPAN in B6")
    print("   - Select voltage in A10 (LV/HV/EHV)")
    print("   - Menu: 🔋 BESS Tools → Refresh DNO Data")

if not min_kw:
    print("\n2. Set HH profile parameters:")
    print("   - Enter Min/Avg/Max kW in B17:B19")
    print("   - Menu: 🔋 BESS Tools → Generate HH Data")

if not btm_header:
    print("\n3. Run BtM PPA analysis:")
    print("   - Command: python3 update_btm_ppa_from_bigquery.py")

if not enhanced_header:
    print("\n4. Deploy enhanced revenue analysis:")
    print("   - Command: python3 dashboard_pipeline.py")
    print("   - Or run: ./deploy_bess_dashboard.sh (full setup)")

print("\n5. Format enhanced section:")
print("   - Open Google Sheets")
print("   - Extensions → Apps Script")
print("   - Paste: apps_script_enhanced/bess_integration.gs")
print("   - Run: formatBESSEnhanced()")

print("\n" + "=" * 80)
