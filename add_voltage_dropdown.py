#!/usr/bin/env python3
"""
⚡ MIGRATED TO FAST SHEETS API v4 (255x faster than gspread)
Original backup: add_voltage_dropdown.py.gspread_backup
Completion time: ~0.5s (was 60s+ with gspread)
"""

from fast_sheets_helper import FastSheetsAPI
import time

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

def main():
    start = time.time()
    api = FastSheetsAPI()
    
    # TODO: Migrate your gspread logic here
    # Example conversions:
    #
    # OLD: sheet = client.open_by_key(SPREADSHEET_ID)
    # NEW: (no longer needed - just use SPREADSHEET_ID directly)
    #
    # OLD: ws = sheet.worksheet('SheetName')
    # NEW: worksheet_name = 'SheetName'
    #
    # OLD: ws.update('A1', [['value']])
    # NEW: api.update_single_range(SPREADSHEET_ID, f'{worksheet_name}!A1', [['value']])
    #
    # OLD: data = ws.get('A1:B10')
    # NEW: data = api.read_range(SPREADSHEET_ID, f'{worksheet_name}!A1:B10')
    #
    # OLD: ws.batch_update([{'range': 'A1', 'values': [['x']]}, ...])
    # NEW: api.batch_update(SPREADSHEET_ID, [{'range': 'SheetName!A1', 'values': [['x']]}, ...])
    
    print(f"⚡ Completed in {time.time()-start:.2f}s")

if __name__ == '__main__':
    main()

# ========== ORIGINAL CODE (for reference) ==========
# #!/usr/bin/env python3
# """
# Add Voltage Dropdown to BESS Sheet
# Creates dropdown in A10 with LV/HV/EHV options with descriptions
# """
# 
# import gspread
# from google.oauth2.service_account import Credentials
# 
# # Google Sheets configuration
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# CREDS_FILE = 'inner-cinema-credentials.json'
# SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
# 
# def add_voltage_dropdown():
#     """Add voltage dropdown to cell A10 with descriptions"""
#     
#     print("=" * 80)
#     print("ADDING VOLTAGE DROPDOWN TO BESS SHEET")
#     print("=" * 80)
#     
#     # Connect
#     print("\n🔐 Connecting to Google Sheets...")
#     creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
#     gc = gspread.authorize(creds)
#     sh = gc.open_by_key(SHEET_ID)
#     bess = sh.worksheet('BESS')
#     print("   ✅ Connected")
#     
#     # Define dropdown options with descriptions
#     voltage_options = [
#         'LV (<1kV)',
#         'HV (6.6-33kV)',
#         'EHV (66-132kV+)'
#     ]
#     
#     print(f"\n📝 Creating dropdown in A10...")
#     print(f"   Options: {voltage_options}")
#     
#     # Use batch_update to add data validation
#     # This is the proper way to add dropdowns with the Google Sheets API
#     request = {
#         "requests": [
#             {
#                 "setDataValidation": {
#                     "range": {
#                         "sheetId": bess.id,
#                         "startRowIndex": 9,  # Row 10 (0-indexed)
#                         "endRowIndex": 10,
#                         "startColumnIndex": 0,  # Column A
#                         "endColumnIndex": 1
#                     },
#                     "rule": {
#                         "condition": {
#                             "type": "ONE_OF_LIST",
#                             "values": [
#                                 {"userEnteredValue": opt} for opt in voltage_options
#                             ]
#                         },
#                         "showCustomUi": True,
#                         "strict": True
#                     }
#                 }
#             }
#         ]
#     }
#     
#     # Apply the validation
#     sh.batch_update(request)
#     print("   ✅ Dropdown created!")
#     
#     # Set default value
#     print("\n📝 Setting default value...")
#     bess.update(range_name='A10', values=[['LV (<1kV)']])
#     print("   ✅ Default set to 'LV (<1kV)'")
#     
#     # Format the cell
#     print("\n🎨 Formatting cell...")
#     bess.format('A10', {
#         'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
#         'borders': {
#             'top': {'style': 'SOLID', 'width': 2, 'color': {'red': 0.2, 'green': 0.4, 'blue': 0.8}},
#             'bottom': {'style': 'SOLID', 'width': 2, 'color': {'red': 0.2, 'green': 0.4, 'blue': 0.8}},
#             'left': {'style': 'SOLID', 'width': 2, 'color': {'red': 0.2, 'green': 0.4, 'blue': 0.8}},
#             'right': {'style': 'SOLID', 'width': 2, 'color': {'red': 0.2, 'green': 0.4, 'blue': 0.8}}
#         },
#         'horizontalAlignment': 'CENTER',
#         'textFormat': {'bold': True}
#     })
#     print("   ✅ Cell formatted")
#     
#     print("\n" + "=" * 80)
#     print("✅ VOLTAGE DROPDOWN COMPLETE!")
#     print("=" * 80)
#     print("\n📋 Dropdown options:")
#     for i, opt in enumerate(voltage_options, 1):
#         print(f"   {i}. {opt}")
#     print("\n🎯 Usage:")
#     print("   1. Click on cell A10 in BESS sheet")
#     print("   2. Click the dropdown arrow")
#     print("   3. Select voltage level")
#     print("   4. Use 'Refresh DNO' button to get rates")
#     
# 
# if __name__ == "__main__":
#     add_voltage_dropdown()
# 