#!/usr/bin/env python3
"""
Fix Live Dashboard v2 Sparklines - Convert from Hardcoded to Dynamic

The sparklines in row 7 currently have hardcoded arrays like:
  =SPARKLINE({5.44,5.495,5.23,...}, {...})

They need to reference Data_Hidden sheet instead:
  =SPARKLINE(Data_Hidden!C2:AX2, {...})

This script updates all sparklines to pull from Data_Hidden dynamically.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SA_FILE = 'inner-cinema-credentials.json'

# Sparkline configuration
# Row 7 has sparklines in columns C, E, G, I, K
# Each corresponds to a KPI showing 48-period history

SPARKLINE_MAPPING = {
    'C7': {
        'label': 'Wholesale Price (£/MWh)',
        'data_row': 2,  # Row 2 in Data_Hidden
        'color': '#e74c3c',
        'charttype': 'column'
    },
    'E7': {
        'label': 'Grid Frequency Deviation (%)',
        'data_row': 3,
        'color': '#3498db',
        'charttype': 'line'
    },
    'G7': {
        'label': 'Total Generation (MW)',
        'data_row': 4,
        'color': '#2ecc71',
        'charttype': 'line'
    },
    'I7': {
        'label': 'Wind Generation (MW)',
        'data_row': 5,
        'color': '#9b59b6',
        'charttype': 'line'
    },
    'K7': {
        'label': 'Demand (MW)',
        'data_row': 6,
        'color': '#f39c12',
        'charttype': 'line'
    }
}

def fix_sparklines():
    """Update sparkline formulas to reference Data_Hidden sheet"""
    
    print("\n" + "=" * 80)
    print("🔧 FIXING LIVE DASHBOARD V2 SPARKLINES")
    print("=" * 80)
    
    # Connect to Google Sheets
    print("\n📊 Connecting to Google Sheets...")
    scope = ['https://spreadsheets.google.com/feeds', 
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SA_FILE, scope)
    client = gspread.authorize(creds)
    
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.sheet1
    
    print(f"✅ Connected to: {spreadsheet.title}")
    
    # Check if Data_Hidden exists
    print("\n🔍 Checking for Data_Hidden sheet...")
    try:
        data_hidden = spreadsheet.worksheet('Data_Hidden')
        print(f"✅ Found Data_Hidden sheet")
        
        # Verify it has data
        row2 = data_hidden.row_values(2)
        if len(row2) >= 48:
            print(f"✅ Data_Hidden has {len(row2)} columns of data")
        else:
            print(f"⚠️  Data_Hidden only has {len(row2)} columns (expected 48)")
    except:
        print("❌ ERROR: Data_Hidden sheet not found!")
        print("   Run 'python3 update_gb_live_complete.py' first to create it.")
        return
    
    # Update each sparkline
    print("\n📝 Updating sparkline formulas...")
    print("-" * 80)
    
    for cell, config in SPARKLINE_MAPPING.items():
        print(f"\n{cell}: {config['label']}")
        
        # Get current formula
        current = sheet.acell(cell, value_render_option='FORMULA').value
        if current:
            print(f"   Current: {current[:60]}...")
        else:
            print(f"   Current: (empty)")
        
        # Build new formula
        # Data_Hidden row with 48 columns (A=1, B=2, ..., AV=48)
        # Formula: =SPARKLINE(Data_Hidden!A{row}:AV{row}, {...})
        data_row = config['data_row']
        
        new_formula = (
            f"=SPARKLINE(Data_Hidden!A{data_row}:AV{data_row}, "
            f'{{\"charttype\",\"{config["charttype"]}\";'
            f'\"color\",\"{config["color"]}\";'
            f'\"highcolor\",\"{config["color"]}\";'
            f'\"negcolor\",\"#c0392b\"}})'
        )
        
        print(f"   New:     {new_formula}")
        
        # Update the cell
        try:
            sheet.update_acell(cell, new_formula)
            print(f"   ✅ Updated successfully")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ SPARKLINE FIX COMPLETE")
    print("=" * 80)
    print("\nSparklines in row 7 now reference Data_Hidden sheet.")
    print("They will update automatically every 5 minutes when the cron job runs.")
    print("\nView dashboard:")
    print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")

if __name__ == '__main__':
    fix_sparklines()
