#!/usr/bin/env python3
"""
Fix Live Dashboard v2 - Connect Sparklines to Live Data
Replaces static arrays with dynamic data from BigQuery views
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
PROJECT_ID = "inner-cinema-476211-u9"

def fix_live_dashboard_sparklines():
    """Replace static sparkline data with live formulas"""
    
    # Connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    sheet = spreadsheet.worksheet('Live Dashboard v2')
    
    print("=" * 80)
    print("🔧 FIXING LIVE DASHBOARD V2 SPARKLINES")
    print("=" * 80)
    print()
    
    # Get current data to understand what the sparklines should show
    print("Current sparklines in row 7:")
    print("  C7: System price trend")
    print("  E7: Frequency deviation")
    print("  G7: Total demand")
    print("  I7: Wind generation")
    print("  K7: Demand again")
    print()
    
    # Create a data row for live updates
    print("Creating data source row...")
    
    # Row 20: Data from BigQuery (will be populated by separate script)
    # For now, create the sparkline formulas that reference this data
    
    # Update sparklines to use data from a data row (row 20)
    sparkline_formulas = {
        'C7': '=IF(ISBLANK(C20:AV20),"",SPARKLINE(C20:AV20,{"charttype","column";"color","#e74c3c";"highcolor","#e74c3c"}))',
        'E7': '=IF(ISBLANK(C21:AV21),"",SPARKLINE(C21:AV21,{"charttype","column";"color","#2ecc71";"negcolor","#e74c3c";"axis",true}))',
        'G7': '=IF(ISBLANK(C22:AV22),"",SPARKLINE(C22:AV22,{"charttype","column";"color","#f39c12"}))',
        'I7': '=IF(ISBLANK(C23:AV23),"",SPARKLINE(C23:AV23,{"charttype","column";"color","#2ecc71"}))',
        'K7': '=IF(ISBLANK(C24:AV24),"",SPARKLINE(C24:AV24,{"charttype","column";"color","#3498db"}))'
    }
    
    print("Updating sparkline formulas...")
    for cell, formula in sparkline_formulas.items():
        sheet.update_acell(cell, formula)
        print(f"  ✅ {cell}: Now references live data")
    
    print()
    print("Setting up data source rows (20-24)...")
    
    # Add labels for data rows
    labels = {
        'A20': 'System Price (£/MWh)',
        'A21': 'Frequency (Hz dev from 50)',
        'A22': 'Total Demand (MW)',
        'A23': 'Wind Generation (MW)',
        'A24': 'Net Demand (MW)'
    }
    
    for cell, label in labels.items():
        sheet.update_acell(cell, label)
    
    print()
    print("=" * 80)
    print("✅ SPARKLINES FIXED - NOW NEED DATA SOURCE")
    print("=" * 80)
    print()
    print("Next step: Create script to populate rows 20-24 with latest settlement period data")
    print("This should query BigQuery every 30 minutes for:")
    print("  - bmrs_costs (system prices)")
    print("  - bmrs_freq (frequency)")
    print("  - bmrs_fuelinst (generation mix)")
    print()
    print(f"View: https://docs.google.com/spreadsheets/d/{SHEET_ID}")

if __name__ == "__main__":
    fix_live_dashboard_sparklines()
