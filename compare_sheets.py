#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import difflib

print("=" * 80)
print("GOOGLE SHEETS COMPARISON: Live Dashboard v2 vs Test")
print("=" * 80)

# Connect
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
spreadsheet = client.open_by_key(SPREADSHEET_ID)

print("\n✅ Connected to spreadsheet")

# Get sheets
live = spreadsheet.worksheet("Live Dashboard v2")
test = spreadsheet.worksheet("Test ")  # Note: trailing space!

print(f"✅ Found 'Live Dashboard v2' (Sheet ID: {live.id})")
print(f"✅ Found 'Test' (Sheet ID: {test.id})")

# Export
print("\n📥 Exporting sheets...")
live_data = live.get_all_values()
test_data = test.get_all_values()

# Convert to CSV strings
import io
live_csv_io = io.StringIO()
test_csv_io = io.StringIO()

writer = csv.writer(live_csv_io)
writer.writerows(live_data)
live_csv = live_csv_io.getvalue()

writer = csv.writer(test_csv_io)
writer.writerows(test_data)
test_csv = test_csv_io.getvalue()

with open('/tmp/live_dashboard.csv', 'w') as f:
    f.write(live_csv)
with open('/tmp/test_dashboard.csv', 'w') as f:
    f.write(test_csv)

print("✅ Exported to:")
print("   /tmp/live_dashboard.csv")
print("   /tmp/test_dashboard.csv")

# Search for 323385
print(f"\n🔍 Searching for '323385'...")
live_has = '323385' in live_csv
test_has = '323385' in test_csv

if live_has:
    print("✅ Found in Live Dashboard v2")
    # Find line
    for i, line in enumerate(live_csv.split('\n'), 1):
        if '323385' in line:
            print(f"   Line {i}: {line[:100]}...")
            break
else:
    print("❌ NOT in Live Dashboard v2")

if test_has:
    print("✅ Found in Test")
    # Find line
    for i, line in enumerate(test_csv.split('\n'), 1):
        if '323385' in line:
            print(f"   Line {i}: {line[:100]}...")
            break
else:
    print("❌ NOT in Test")

# Quick diff
print(f"\n📊 File sizes:")
print(f"   Live: {len(live_csv):,} bytes")
print(f"   Test: {len(test_csv):,} bytes")
print(f"   Difference: {abs(len(test_csv) - len(live_csv)):,} bytes")

if live_csv == test_csv:
    print("\n✅ SHEETS ARE IDENTICAL")
else:
    print("\n⚠️  SHEETS ARE DIFFERENT")
    print("\nGenerating diff report...")

    live_lines = live_csv.split('\n')
    test_lines = test_csv.split('\n')

    differ = difflib.unified_diff(live_lines[:50], test_lines[:50],
                                   lineterm='',
                                   fromfile='Live Dashboard v2',
                                   tofile='Test',
                                   n=0)

    diff_lines = list(differ)
    if diff_lines:
        print("\nFirst 50 rows differences:")
        for line in diff_lines[:30]:
            print(line)

print("\n" + "=" * 80)
print("COMPLETE")
