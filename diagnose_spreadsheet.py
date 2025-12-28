#!/usr/bin/env python3
"""Read Live Dashboard v2 to diagnose sparkline issues"""

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
    
    print("=" * 80)
    print("🔍 LIVE DASHBOARD v2 - SPARKLINE DIAGNOSTIC")
    print("=" * 80)
    
    # Check PYTHON_MANAGED flag
    aa1 = sheet.acell('AA1').value
    print(f"\n✅ AA1 (PYTHON_MANAGED flag): '{aa1}'")
    
    # Check row 4 (should be empty or old sparklines)
    print(f"\n📊 ROW 4 (OLD - should be empty):")
    row4_cells = ['C4', 'E4', 'G4', 'I4']
    for cell in row4_cells:
        value = sheet.acell(cell, value_render_option='FORMULA').value
        display = value[:80] if value else '(empty)'
        print(f"  {cell}: {display}")
    
    # Check row 6 (KPI values)
    print(f"\n📊 ROW 6 (KPI VALUES):")
    row6_range = sheet.range('C6:K6')
    row6_values = [cell.value for cell in row6_range]
    print(f"  C6-K6: {row6_values}")
    
    # Check row 7 (NEW sparklines - merged 7-8)
    print(f"\n📊 ROW 7 (NEW SPARKLINES - merged with row 8):")
    row7_cells = ['C7', 'E7', 'G7', 'I7']
    for cell in row7_cells:
        formula = sheet.acell(cell, value_render_option='FORMULA').value
        if formula:
            # Show first 100 chars of formula
            display = formula[:100] + '...' if len(formula) > 100 else formula
            print(f"  {cell}: {display}")
        else:
            print(f"  {cell}: (empty) ❌")
    
    # Check merge status of rows 7-8
    print(f"\n🔄 MERGE STATUS:")
    print(f"  Checking if C7-C8, E7-E8, G7-G8, I7-I8 are merged...")
    # Note: gspread doesn't easily expose merge info, checking values instead
    row8_cells = ['C8', 'E8', 'G8', 'I8']
    for cell in row8_cells:
        value = sheet.acell(cell).value
        print(f"  {cell}: '{value}' (should be empty if merged)")
    
    # Check Data_Hidden exists
    print(f"\n📁 DATA_HIDDEN SHEET:")
    try:
        data_hidden = ss.worksheet('Data_Hidden')
        print(f"  ✅ Data_Hidden sheet exists")
        
        # Check row 22-25 headers
        a22 = data_hidden.acell('A22').value
        a23 = data_hidden.acell('A23').value
        a24 = data_hidden.acell('A24').value
        a25 = data_hidden.acell('A25').value
        print(f"  A22: '{a22}'")
        print(f"  A23: '{a23}'")
        print(f"  A24: '{a24}'")
        print(f"  A25: '{a25}'")
        
        # Check if data exists in B22-B25
        b22 = data_hidden.acell('B22').value
        b23 = data_hidden.acell('B23').value
        b24 = data_hidden.acell('B24').value
        b25 = data_hidden.acell('B25').value
        print(f"  B22 (Wholesale): '{b22}'")
        print(f"  B23 (Frequency): '{b23}'")
        print(f"  B24 (Total Gen): '{b24}'")
        print(f"  B25 (Wind): '{b25}'")
        
    except Exception as e:
        print(f"  ❌ Error accessing Data_Hidden: {e}")
    
    # Check interconnectors G13:H22
    print(f"\n🔌 INTERCONNECTORS (G13:H22):")
    for row in range(13, 23):
        g_cell = sheet.acell(f'G{row}').value
        h_formula = sheet.acell(f'H{row}', value_render_option='FORMULA').value
        if h_formula:
            display = h_formula[:60] + '...' if len(h_formula) > 60 else h_formula
            print(f"  G{row}: {g_cell} | H{row}: {display}")
    
    # Check Active Outages G27:K41
    print(f"\n⚠️  ACTIVE OUTAGES (G27:K41) - First 5 rows:")
    outages = sheet.range('G27:K31')  # First 5 rows
    for i in range(5):
        row_data = [outages[i*5 + j].value for j in range(5)]
        print(f"  Row {27+i}: {row_data}")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
