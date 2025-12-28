#!/usr/bin/env python3
"""
Deploy Sparklines to Live Dashboard v2
Adds sparklines to KPI row and generation mix section
"""

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def deploy_kpi_sparklines():
    """Add sparklines to KPI row (row 4)"""
    print("🎯 Deploying KPI Sparklines to Live Dashboard v2...")
    print()

    # Authenticate
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SPREADSHEET_ID)

    # Get sheets
    dashboard = ss.worksheet('Live Dashboard v2')

    # Check if Data_Hidden exists
    try:
        data_hidden = ss.worksheet('Data_Hidden')
        print("✅ Found 'Data_Hidden' sheet")
    except gspread.exceptions.WorksheetNotFound:
        print("⚠️ 'Data_Hidden' sheet not found - run dashboard updater first")
        return False

    print()
    print("📊 Adding KPI Sparklines (Row 4):")

    # KPI Sparkline configurations
    # Row 4, columns B, D, F, G
    kpi_configs = [
        {
            'cell': 'B4',
            'dataRow': 22,
            'label': '📉 Wholesale Price',
            'color': '#e74c3c',
            'chartType': 'column'
        },
        {
            'cell': 'D4',
            'dataRow': 23,
            'label': '💓 Grid Frequency',
            'color': '#2ecc71',
            'chartType': 'line'
        },
        {
            'cell': 'F4',
            'dataRow': 24,
            'label': '🏭 Total Generation',
            'color': '#f39c12',
            'chartType': 'column'
        },
        {
            'cell': 'G4',
            'dataRow': 25,
            'label': '🌬️ Wind Output',
            'color': '#4ECDC4',
            'chartType': 'column'
        }
    ]

    # Add each sparkline
    for config in kpi_configs:
        formula = (
            f'=SPARKLINE(Data_Hidden!$B${config["dataRow"]}:$AW${config["dataRow"]}, '
            f'{{"charttype","{config["chartType"]}";"color","{config["color"]}"}})'
        )

        dashboard.update_acell(config['cell'], formula)
        print(f"   ✅ {config['cell']}: {config['label']}")

    print()
    print("✅ KPI Sparklines deployed!")
    return True


def deploy_generation_sparklines():
    """Add sparklines to generation mix section (rows 13-22, column D)"""
    print()
    print("🔋 Deploying Generation Mix Sparklines:")
    print()

    # Authenticate
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SPREADSHEET_ID)

    dashboard = ss.worksheet('Live Dashboard v2')

    # Sparklines for each fuel type showing 48-period trend
    fuel_sparklines = [
        {'row': 13, 'dataRow': 1, 'color': '#4ECDC4', 'fuel': 'Wind'},
        {'row': 14, 'dataRow': 3, 'color': '#FFA07A', 'fuel': 'Nuclear'},
        {'row': 15, 'dataRow': 2, 'color': '#FF6B6B', 'fuel': 'CCGT'},
        {'row': 16, 'dataRow': 4, 'color': '#52B788', 'fuel': 'Biomass'},
        {'row': 17, 'dataRow': 5, 'color': '#F7DC6F', 'fuel': 'Hydro'},
        {'row': 18, 'dataRow': 6, 'color': '#45B7D1', 'fuel': 'Other'},
        {'row': 19, 'dataRow': 7, 'color': '#E76F51', 'fuel': 'OCGT'},
        {'row': 20, 'dataRow': 8, 'color': '#264653', 'fuel': 'Coal'},
        {'row': 21, 'dataRow': 9, 'color': '#85C1E9', 'fuel': 'Oil'},
        {'row': 22, 'dataRow': 10, 'color': '#BB8FCE', 'fuel': 'PS'},
    ]

    for config in fuel_sparklines:
        formula = (
            f'=SPARKLINE(Data_Hidden!A{config["dataRow"]}:AV{config["dataRow"]}, '
            f'{{"charttype","line";"linewidth",2;"color","{config["color"]}";"ymin",0}})'
        )

        dashboard.update_acell(f'D{config["row"]}', formula)
        print(f"   ✅ Row {config['row']}: {config['fuel']} sparkline")

    # Merge D-E columns for each row to give sparklines more space
    print()
    print("📐 Merging columns D-E for sparkline width...")

    for config in fuel_sparklines:
        row = config['row']
        try:
            dashboard.merge_cells(f'D{row}:E{row}')
        except Exception as e:
            # Already merged or error - skip
            pass

    print()
    print("✅ Generation Mix Sparklines deployed!")
    return True


def main():
    """Deploy all sparklines"""
    print("=" * 60)
    print("⚡ SPARKLINE DEPLOYMENT - Live Dashboard v2")
    print("=" * 60)
    print()

    try:
        # Deploy KPI sparklines
        kpi_success = deploy_kpi_sparklines()

        if not kpi_success:
            print()
            print("⚠️ Run dashboard updater first to create Data_Hidden sheet:")
            print("   python3 update_live_dashboard_v2.py")
            return

        # Deploy generation sparklines
        gen_success = deploy_generation_sparklines()

        if kpi_success and gen_success:
            print()
            print("=" * 60)
            print("✅ ALL SPARKLINES DEPLOYED SUCCESSFULLY!")
            print("=" * 60)
            print()
            print("📊 View dashboard:")
            print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
            print()
            print("🔄 Next: Refresh dashboard data to populate sparklines:")
            print("   python3 update_live_dashboard_v2.py")

    except Exception as e:
        print(f"❌ Deployment error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check credentials file exists: inner-cinema-credentials.json")
        print("2. Verify spreadsheet ID is correct")
        print("3. Ensure you have edit permissions")


if __name__ == "__main__":
    main()
