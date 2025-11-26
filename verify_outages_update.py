#!/usr/bin/env python3
"""
Quick Dashboard Verification
Checks that row 44 and outages section are properly formatted
"""

import pickle
from pathlib import Path
import gspread

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
DASHBOARD_SHEET = 'Dashboard'
TOKEN_FILE = Path(__file__).parent / 'token.pickle'

def verify_dashboard():
    """Verify the dashboard outages section and row 44"""
    print("🔍 Verifying Dashboard...")
    
    # Connect
    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)
    
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    dashboard = spreadsheet.worksheet(DASHBOARD_SHEET)
    
    # Read row 44 (totals row)
    print("\n📊 Row 44 (Totals):")
    row_44 = dashboard.row_values(44)
    if row_44:
        print(f"   {row_44[0]}")
        
        # Check formatting
        if "MW" in row_44[0] and "GW" in row_44[0]:
            print("   ✅ Contains MW and GW")
        if "Count:" in row_44[0]:
            print("   ✅ Contains outage count")
        if "Status:" in row_44[0]:
            print("   ✅ Contains status indicator")
    else:
        print("   ⚠️ Row 44 is empty")
    
    # Read outages section (rows 31-42)
    print("\n🔴 Outages Section (Rows 31-42):")
    outages = []
    for row_num in range(31, 43):
        row = dashboard.row_values(row_num)
        if row and any(row):  # If row has content
            outages.append((row_num, row))
    
    print(f"   Found {len(outages)} outages displayed")
    
    if outages:
        print("\n   Sample outages:")
        for i, (row_num, row) in enumerate(outages[:3]):
            name = row[0] if len(row) > 0 else "N/A"
            unit = row[1] if len(row) > 1 else "N/A"
            capacity = row[4] if len(row) > 4 else "N/A"
            pct = row[6] if len(row) > 6 else "N/A"
            print(f"   {i+1}. {name[:40]:40s} | {capacity[:20]:20s} | {pct}")
    else:
        print("   No outages currently displayed")
    
    # Check formatting
    print("\n✅ Formatting Checks:")
    
    format_checks = {
        "Emojis present": False,
        "MW formatting": False,
        "Percentage formatting": False,
        "Visual bars": False
    }
    
    for row_num, row in outages[:5]:  # Check first 5 rows
        if any('🔴' in str(cell) or '⚠️' in str(cell) or '🟡' in str(cell) or '🟢' in str(cell) for cell in row):
            format_checks["Emojis present"] = True
        if any('MW' in str(cell) for cell in row):
            format_checks["MW formatting"] = True
        if any('%' in str(cell) for cell in row):
            format_checks["Percentage formatting"] = True
        if any('🟥' in str(cell) or '⬜' in str(cell) for cell in row):
            format_checks["Visual bars"] = True
    
    for check, status in format_checks.items():
        icon = "✅" if status else "⚠️"
        print(f"   {icon} {check}")
    
    print("\n" + "=" * 70)
    print("🌐 View Dashboard:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("=" * 70)

if __name__ == "__main__":
    verify_dashboard()
