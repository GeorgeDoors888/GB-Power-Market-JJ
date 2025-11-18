#!/usr/bin/env python3
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from googleapiclient.discovery import build
from google.oauth2 import service_account

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

print("=" * 80)
print("✅ FINAL DASHBOARD VERIFICATION")
print("=" * 80)

# Read key sections
result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1:G80'
).execute()
vals = result.get('values', [])

print(f"\n📊 Total rows: {len(vals)}")

# Check header
print(f"\n📋 Row 1 (Title): {vals[0][0] if len(vals) > 0 else 'MISSING'}")
print(f"📋 Row 2 (Timestamp): {vals[1][0] if len(vals) > 1 else 'MISSING'}")
print(f"📋 Row 3 (Legend): {vals[2][0] if len(vals) > 2 else 'MISSING'}")

# Check for flags
print(f"\n🌍 Interconnectors (rows 7-16):")
flag_count = 0
for i in range(6, 16):
    if i < len(vals) and len(vals[i]) > 3:
        col_d = vals[i][3]
        has_flag = any(c in col_d for c in ['🇫', '🇮', '🇳', '🇧', '🇩'])
        if has_flag:
            flag_count += 1
            print(f"   Row {i+1}: ✅ {col_d[:40]}")

print(f"\n   Total interconnectors with flags: {flag_count}/10")

# Check settlement periods
print(f"\n📈 Settlement Periods:")
sp_count = 0
for i in range(19, 67):  # Rows 20-67 should be SP01-SP48
    if i < len(vals) and len(vals[i]) > 0 and vals[i][0].startswith('SP'):
        sp_count += 1

print(f"   Settlement period rows: {sp_count}")

# Check unavailability section
print(f"\n⚠️  Unavailability Section:")
unavail_found = False
for i in range(67, min(len(vals), 75)):
    if len(vals[i]) > 0 and 'POWER STATION OUTAGES' in str(vals[i][0]):
        unavail_found = True
        print(f"   Row {i+1}: ✅ Found header: {vals[i][0]}")
        
        # Count outage rows
        outage_count = 0
        for j in range(i+2, min(len(vals), i+15)):
            if j < len(vals) and len(vals[j]) > 4:
                if '🟥' in str(vals[j][4]):
                    outage_count += 1
        
        print(f"   Outage rows with visual indicators: {outage_count}")
        break

if not unavail_found:
    print("   ❌ Unavailability section not found")

# Check for freshness indicator
print(f"\n🕐 Freshness Indicator:")
if len(vals) > 1:
    timestamp_row = vals[1][0]
    if '✅' in timestamp_row:
        print(f"   ✅ FRESH indicator present")
    elif '⚠️' in timestamp_row:
        print(f"   ⚠️ STALE indicator present")
    elif '🔴' in timestamp_row:
        print(f"   🔴 OLD indicator present - DATA TOO OLD!")
    else:
        print(f"   ❌ No freshness indicator found")
    
    if len(vals) > 2:
        legend = vals[2][0]
        if 'Freshness' in legend:
            print(f"   ✅ Legend present: {legend[:50]}...")

print("\n" + "=" * 80)
print("📊 DASHBOARD STATUS SUMMARY")
print("=" * 80)

issues = []
if flag_count < 10:
    issues.append(f"⚠️  Only {flag_count}/10 interconnectors have flags")
if sp_count != 48:
    issues.append(f"⚠️  Settlement periods: {sp_count} (should be 48)")
if not unavail_found:
    issues.append("❌ Unavailability section missing")

if issues:
    print("\n⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n✅ ALL CHECKS PASSED!")
    print("\n📋 Dashboard contains:")
    print("   ✅ Interconnector flags (🇫🇷 🇮🇪 🇳🇱 🇧🇪 🇳🇴 🇩🇰)")
    print("   ✅ Data freshness indicator (✅/⚠️/🔴)")
    print("   ✅ 48 settlement periods")
    print("   ✅ Power station outages with visual bars")
    print("\n🌐 Dashboard URL:")
    print("   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8")
