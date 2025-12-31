#!/usr/bin/env python3
"""
Dashboard Layout Restructure
Reorganizes into 3 trader-focused sections with headers and visual separation
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def restructure_dashboard():
    """Add section headers and reorganize KPIs into logical groups"""

    print("\n🎨 Restructuring dashboard layout...")

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'inner-cinema-credentials.json', scope)

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet('Live Dashboard v2')

    # Insert section headers
    print("  Adding section headers...")

    # SECTION 1: MARKET SIGNALS (Row 11)
    sheet.update(values=[["", "⚡ MARKET SIGNALS"]], range_name='K11:L11')
    sheet.format('K11:L11', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 12
        },
        'horizontalAlignment': 'LEFT'
    })

    # Add subtitle
    sheet.update(values=[["", "Real-time price, frequency, and generation indicators"]], range_name='K12:L12')
    sheet.format('K12:L12', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'italic': True, 'fontSize': 9},
        'horizontalAlignment': 'LEFT'
    })

    print("    ✅ Section 1: Market Signals (rows 11-12)")

    # SECTION 2: ASSET READINESS (Row 23)
    sheet.update(values=[["", "🔋 ASSET READINESS"]], range_name='K23:L23')
    sheet.format('K23:L23', {
        'backgroundColor': {'red': 1, 'green': 0.6, 'blue': 0},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 12
        },
        'horizontalAlignment': 'LEFT'
    })

    sheet.update(values=[["", "Battery performance, CHP economics, and technical metrics"]], range_name='K24:L24')
    sheet.format('K24:L24', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'italic': True, 'fontSize': 9},
        'horizontalAlignment': 'LEFT'
    })

    print("    ✅ Section 2: Asset Readiness (rows 23-24)")

    # SECTION 3: TRADING OUTCOMES (Row 37)
    sheet.update(values=[["", "⚠️ TRADING OUTCOMES & RISK"]], range_name='K37:L37')
    sheet.format('K37:L37', {
        'backgroundColor': {'red': 0.8, 'green': 0.2, 'blue': 0.2},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 12
        },
        'horizontalAlignment': 'LEFT'
    })

    sheet.update(values=[["", "Risk metrics, tail events, and delivery performance"]], range_name='K38:L38')
    sheet.format('K38:L38', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'italic': True, 'fontSize': 9},
        'horizontalAlignment': 'LEFT'
    })

    print("    ✅ Section 3: Trading Outcomes (rows 37-38)")

    # SECTION 4: CONSTRAINT INTELLIGENCE (Row 46)
    sheet.update(values=[["", "🗺️ CONSTRAINT INTELLIGENCE"]], range_name='K46:L46')
    sheet.format('K46:L46', {
        'backgroundColor': {'red': 0.4, 'green': 0.2, 'blue': 0.6},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 12
        },
        'horizontalAlignment': 'LEFT'
    })

    sheet.update(values=[["", "Geographic constraint costs and transmission bottlenecks"]], range_name='K47:L47')
    sheet.format('K47:L47', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'italic': True, 'fontSize': 9},
        'horizontalAlignment': 'LEFT'
    })

    print("    ✅ Section 4: Constraint Intelligence (rows 46-47)")

    # Add navigation guide at top
    print("\n  Adding navigation guide...")

    nav_text = [
        ["", "📊 GB POWER MARKET LIVE DASHBOARD"],
        ["", "Real-time energy market intelligence for trading and asset optimization"],
        ["", ""],
        ["", "Navigate: ⚡Market Signals → 🔋Asset Readiness → ⚠️Trading Outcomes → 🗺️Constraints"]
    ]

    sheet.update(values=nav_text, range_name='K1:L4')

    # Format title
    sheet.format('K1:L1', {
        'backgroundColor': {'red': 0.1, 'green': 0.1, 'blue': 0.1},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 16
        },
        'horizontalAlignment': 'CENTER'
    })

    # Format subtitle
    sheet.format('K2:L2', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'fontSize': 10
        },
        'horizontalAlignment': 'CENTER'
    })

    # Format navigation
    sheet.format('K4:L4', {
        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
        'textFormat': {'fontSize': 9, 'italic': True},
        'horizontalAlignment': 'CENTER'
    })

    print("    ✅ Navigation guide added (rows 1-4)")

    # Add footer with last updated timestamp
    print("\n  Adding footer...")

    footer_text = [
        ["", ""],
        ["", "💡 Dashboard auto-refreshes every 5 minutes via realtime_dashboard_updater.py"],
        ["", "📧 Email alerts sent when thresholds breached (SIP >£100, Frequency <49.8Hz)"],
        ["", "🔗 Data sources: BigQuery (inner-cinema-476211-u9.uk_energy_prod) + IRIS real-time pipeline"]
    ]

    sheet.update(values=footer_text, range_name='K60:L63')

    sheet.format('K60:L63', {
        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
        'textFormat': {'fontSize': 8, 'italic': True},
        'horizontalAlignment': 'LEFT'
    })

    print("    ✅ Footer added (rows 60-63)")

    print("\n✅ Dashboard restructure complete")

def main():
    print("="*80)
    print("DASHBOARD LAYOUT RESTRUCTURE")
    print("="*80)
    print("\nReorganizing into trader-focused sections:")
    print("  1. ⚡ Market Signals - Prices, frequency, generation")
    print("  2. 🔋 Asset Readiness - Battery/CHP performance")
    print("  3. ⚠️ Trading Outcomes - Risk metrics, VaR, delivery")
    print("  4. 🗺️ Constraint Intelligence - Geographic bottlenecks")

    restructure_dashboard()

    print("\n" + "="*80)
    print("✅ RESTRUCTURE COMPLETE")
    print("="*80)
    print(f"\nDashboard URL:")
    print(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("\nLayout:")
    print("  Rows 1-4:   Title & Navigation")
    print("  Rows 11-22: ⚡ Market Signals (13 KPIs)")
    print("  Rows 23-35: 🔋 Asset Readiness (Battery/CHP)")
    print("  Rows 37-45: ⚠️ Trading Outcomes (Risk)")
    print("  Rows 46-58: 🗺️ Constraint Intelligence (Regional)")
    print("  Rows 60-63: Footer & Info")

if __name__ == "__main__":
    main()
