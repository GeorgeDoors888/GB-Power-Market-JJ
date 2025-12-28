#!/usr/bin/env python3
"""
Apply Test sheet formatting to Live Dashboard v2
Adds sparkline labels, headers, and live data displays
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

def main():
    # Connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    client = gspread.authorize(creds)

    SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    live = spreadsheet.worksheet("Live Dashboard v2")

    print("=" * 90)
    print("APPLYING TEST SHEET FORMATTING TO LIVE DASHBOARD V2")
    print("=" * 90)

    # Batch update all changes at once for efficiency
    updates = []

    # 1. Section Headers
    print("\n📋 Adding Section Headers...")
    updates.extend([
        {'range': 'L10', 'values': [['SYSTEM PRICES']]},
        {'range': 'H12', 'values': [['Todays Import/Export']]},
        {'range': 'J12', 'values': [['Live Data']]},
    ])

    # 2. Sparkline column headers (already done, but ensure consistency)
    print("📊 Setting Sparkline Headers...")
    updates.extend([
        {'range': 'M13', 'values': [['sparkline  Avg Accept Price']]},
        {'range': 'M15', 'values': [['sparkline  Vol-Wtd Avg']]},
        {'range': 'M17', 'values': [['sparkline Market Index']]},
        {'range': 'Q13', 'values': [['sparkline BM–MID Spread']]},
        {'range': 'Q15', 'values': [['sparkline Sys–VLP Spread']]},
        {'range': 'Q17', 'values': [['sparkline Supp–VLP Spread']]},
    ])

    # 3. Live value labels (left column)
    print("📍 Setting Live Value Labels...")
    updates.extend([
        {'range': 'L13', 'values': [['Live Avg Accepted Price']]},
    ])

    # 4. Live value displays (formulas referencing BM KPIs section)
    print("🔗 Linking Live Values to BM KPIs data...")
    updates.extend([
        {'range': 'L14', 'values': [['=AB14']]},  # Avg Accept Price from AB14
        {'range': 'L16', 'values': [['=AC14']]},  # Vol-Wtd Avg from AC14
        {'range': 'L18', 'values': [['=AD14']]},  # MID Index from AD14
    ])

    # 5. Add sparkline formulas (using Data_Hidden row 27 which has settlement period data)
    print("✨ Creating Sparkline Formulas...")
    # Sparklines showing data from 00:00 (settlement period 1 = column B) onwards
    # Row 27 in Data_Hidden contains BM_Avg_Price by settlement period

    # For testing, let's add sparklines in column N (next to M labels)
    updates.extend([
        # Avg Accept Price sparkline (M14) - shows today's settlement periods
        {'range': 'N13', 'values': [['=SPARKLINE(Data_Hidden!B27:AW27,{"charttype","line";"linewidth",2;"color1","#4285F4"})']]},

        # Vol-Wtd Avg sparkline (could use row 28 if available)
        {'range': 'N15', 'values': [['=SPARKLINE(Data_Hidden!B28:AW28,{"charttype","line";"linewidth",2;"color1","#34A853"})']]},

        # Market Index sparkline (could use row 29 if available)
        {'range': 'N17', 'values': [['=SPARKLINE(Data_Hidden!B29:AW29,{"charttype","line";"linewidth",2;"color1","#FBBC04"})']]},
    ])

    # 6. Spread sparklines in column R (next to Q labels)
    updates.extend([
        # BM-MID Spread sparkline
        {'range': 'R13', 'values': [['=SPARKLINE(Data_Hidden!B30:AW30,{"charttype","line";"linewidth",2;"color1","#EA4335"})']]},

        # Sys-VLP Spread sparkline
        {'range': 'R15', 'values': [['=SPARKLINE(Data_Hidden!B31:AW31,{"charttype","line";"linewidth",2;"color1","#9334E6"})']]},

        # Supp-VLP Spread sparkline
        {'range': 'R17', 'values': [['=SPARKLINE(Data_Hidden!B32:AW32,{"charttype","line";"linewidth",2;"color1","#FF6D00"})']]},
    ])

    # Execute batch update
    print("\n⚡ Executing batch update...")
    live.batch_update(updates)

    print("✅ All updates applied successfully!")

    # Wait a moment for changes to propagate
    time.sleep(2)

    # Verification
    print("\n" + "=" * 90)
    print("📋 VERIFICATION")
    print("=" * 90)

    print("\n1️⃣ Headers:")
    print(f"   L10: '{live.acell('L10').value}'")
    print(f"   H12: '{live.acell('H12').value}'")
    print(f"   J12: '{live.acell('J12').value}'")

    print("\n2️⃣ Sparkline Labels:")
    print(f"   M13: '{live.acell('M13').value}'")
    print(f"   M15: '{live.acell('M15').value}'")
    print(f"   M17: '{live.acell('M17').value}'")
    print(f"   Q13: '{live.acell('Q13').value}'")
    print(f"   Q15: '{live.acell('Q15').value}'")
    print(f"   Q17: '{live.acell('Q17').value}'")

    print("\n3️⃣ Live Value Display:")
    print(f"   L13: '{live.acell('L13').value}' (label)")
    print(f"   L14: '{live.acell('L14').value}' (should show price)")

    print("\n4️⃣ Sparkline Formulas:")
    n13_formula = live.acell('N13', value_render_option='FORMULA').value
    print(f"   N13: {n13_formula[:60] if n13_formula else '(no formula)'}...")

    print("\n" + "=" * 90)
    print("✅ FORMATTING APPLICATION COMPLETE")
    print("=" * 90)
    print("\n📝 Next Steps:")
    print("   1. Manually merge cells M13:O13 for 'sparkline Avg Accept Price'")
    print("   2. Manually merge cells M15:O15 for 'sparkline Vol-Wtd Avg'")
    print("   3. Manually merge cells M17:O17 for 'sparkline Market Index'")
    print("   4. Manually merge cells Q13:S13 for 'sparkline BM–MID Spread'")
    print("   5. Manually merge cells Q15:S15 for 'sparkline Sys–VLP Spread'")
    print("   6. Manually merge cells Q17:S17 for 'sparkline Supp–VLP Spread'")
    print("   7. Adjust sparkline data sources in N13, N15, N17, R13, R15, R17")
    print("      based on actual Data_Hidden sheet structure")

if __name__ == "__main__":
    main()
