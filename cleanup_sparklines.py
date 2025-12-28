#!/usr/bin/env python3
"""Clear old sparklines and 'None' text from spreadsheet"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDS_PATH = os.path.expanduser('~/inner-cinema-credentials.json')

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
gc = gspread.authorize(creds)

try:
    ss = gc.open_by_key(SPREADSHEET_ID)
    sheet = ss.worksheet('Live Dashboard v2')
    
    print("🧹 Cleaning up old sparklines and 'None' text...")
    
    # Clear old I4 sparkline (only remaining old one)
    print("  Clearing I4 (old sparkline)...")
    sheet.update_acell('I4', '')
    
    # Clear 'None' text from row 8 (merged cells should be empty)
    print("  Clearing row 8 'None' text (C8, E8, G8, I8)...")
    batch_data = [
        {'range': 'C8', 'values': [['']]},
        {'range': 'E8', 'values': [['']]},
        {'range': 'G8', 'values': [['']]},
        {'range': 'I8', 'values': [['']]}
    ]
    sheet.batch_update(batch_data)
    
    print("\n✅ Cleanup complete!")
    print("\n📊 Current state:")
    
    # Verify row 7 sparklines still exist
    for cell in ['C7', 'E7', 'G7', 'I7']:
        formula = sheet.acell(cell, value_render_option='FORMULA').value
        if formula and 'SPARKLINE' in formula:
            print(f"  ✅ {cell}: Has sparkline")
        else:
            print(f"  ❌ {cell}: Missing sparkline!")
    
    # Verify row 8 is now empty
    row8_values = sheet.range('C8:I8')
    empty_count = sum(1 for cell in row8_values if not cell.value or cell.value == '')
    print(f"  Row 8: {empty_count}/7 cells empty")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
