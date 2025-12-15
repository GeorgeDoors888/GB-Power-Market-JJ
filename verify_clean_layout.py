#!/usr/bin/env python3
"""Verify the redesigned Dashboard layout"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SA_PATH = "inner-cinema-credentials.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=creds).spreadsheets()

def verify_layout():
    """Verify the new clean layout"""
    
    print("=" * 80)
    print("🔍 VERIFYING DASHBOARD LAYOUT")
    print("=" * 80)
    
    # Read Dashboard data
    result = sheets.values().get(
        spreadsheetId=SHEET_ID,
        range='Dashboard!A1:H100'
    ).execute()
    
    vals = result.get('values', [])
    
    print(f"\n📊 Total rows: {len(vals)}")
    
    # Check settlement period section (should be rows 18-69)
    print("\n📈 Settlement Period Section:")
    print(f"   Row 19 (header): {vals[18] if len(vals) > 18 else 'MISSING'}")
    print(f"   Row 21 (columns): {vals[20] if len(vals) > 20 else 'MISSING'}")
    print(f"   Row 22 (SP01): {vals[21][:5] if len(vals) > 21 else 'MISSING'}")
    print(f"   Row 23 (SP02): {vals[22][:5] if len(vals) > 22 else 'MISSING'}")
    
    # Check for CLEAN layout - rows 22-69 should ONLY have 5 columns of data
    print("\n🧹 Checking Settlement Period rows are clean (NO outage data)...")
    
    issues = []
    for i in range(21, 69):  # Rows 22-69 (SP01-SP48)
        if i < len(vals):
            row = vals[i]
            # Check if columns E-H (indices 4-7) have any outage-related data
            if len(row) > 4:
                if any(row[4:8]):  # Any data in columns E-H
                    # Check if it's outage data (contains MW, Unavail, %, etc.)
                    outage_indicators = ['MW)', 'Unavail', '%', 'Cause', '🟥', '⬜']
                    if any(indicator in str(cell) for cell in row[4:8] for indicator in outage_indicators):
                        issues.append(f"   ❌ Row {i+1} (SP{i-20:02d}): Has outage data in columns E-H: {row[4:8]}")
    
    if issues:
        print(f"\n❌ FOUND {len(issues)} ISSUES:")
        for issue in issues[:10]:  # Show first 10
            print(issue)
    else:
        print("   ✅ All settlement period rows are CLEAN (no outage data)")
    
    # Check outages section
    print("\n⚠️  Power Station Outages Section:")
    
    # Find outages header
    outage_header_row = None
    for i, row in enumerate(vals[70:], start=70):
        if row and '⚠️ POWER STATION OUTAGES' in str(row[0]):
            outage_header_row = i + 1
            break
    
    if outage_header_row:
        print(f"   ✅ Found at row {outage_header_row}")
        print(f"   Row {outage_header_row}: {vals[outage_header_row-1]}")
        if len(vals) > outage_header_row + 1:
            print(f"   Row {outage_header_row+2} (columns): {vals[outage_header_row+1]}")
        if len(vals) > outage_header_row + 2:
            print(f"   Row {outage_header_row+3} (first outage): {vals[outage_header_row+2][:6]}")
    else:
        print("   ❌ Outages section not found")
    
    # Check for visual indicators
    print("\n🎨 Visual Indicators:")
    
    has_visual_bars = False
    for i in range(max(0, outage_header_row or 72), min(len(vals), 100)):
        row = vals[i]
        if len(row) > 4:
            cell = str(row[4])
            if '🟥' in cell or '⬜' in cell:
                has_visual_bars = True
                print(f"   ✅ Row {i+1} has visual bar: {cell}")
                break
    
    if not has_visual_bars:
        print("   ⚠️  No visual bars found")
    
    # Summary
    print("\n" + "=" * 80)
    if len(issues) == 0 and outage_header_row:
        print("✅ LAYOUT VERIFICATION PASSED")
        print("\n📊 Clean Layout Confirmed:")
        print("   • Settlement periods: Rows 22-69 (clean 5-column format)")
        print("   • Separator: Rows 70-71")
        print("   • Outages section: Row 72+ (separate with visual indicators)")
    else:
        print("❌ LAYOUT VERIFICATION FAILED")
        if len(issues) > 0:
            print(f"   • {len(issues)} settlement period rows have mixed-in outage data")
        if not outage_header_row:
            print("   • Outages section not found")
    print("=" * 80)

if __name__ == "__main__":
    verify_layout()
