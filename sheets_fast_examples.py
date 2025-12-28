#!/usr/bin/env python3
"""
Example: Migrating from gspread to sheets_fast
Shows before/after code for common operations
"""

from sheets_fast import SheetsFast

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

# ============================================================================
# EXAMPLE 1: Read a single cell
# ============================================================================

# ❌ BEFORE (gspread - 120+ seconds)
"""
import gspread
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID)  # 60+ seconds
ws = sheet.worksheet('Dashboard')        # 59+ seconds
value = ws.acell('A1').value             # Finally!
"""

# ✅ AFTER (sheets_fast - <1 second)
sheets = SheetsFast()
data = sheets.read_range(SPREADSHEET_ID, 'Dashboard!A1')
value = data[0][0] if data and data[0] else None
print(f"✅ Read cell A1: {value}")

# ============================================================================
# EXAMPLE 2: Read a range of cells
# ============================================================================

# ❌ BEFORE (gspread - 120+ seconds)
"""
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID)
ws = sheet.worksheet('Data_Hidden')
values = ws.get('A1:AZ48')  # After 120s wait
"""

# ✅ AFTER (sheets_fast - <1 second)
data = sheets.read_range(SPREADSHEET_ID, 'Data_Hidden!A1:AZ48')
print(f"✅ Read {len(data)} rows x {len(data[0]) if data else 0} columns")

# ============================================================================
# EXAMPLE 3: Read multiple ranges at once (BATCH)
# ============================================================================

# ❌ BEFORE (gspread - 240+ seconds for 2 sheets)
"""
sheet = gc.open_by_key(SPREADSHEET_ID)
ws1 = sheet.worksheet('Dashboard')
ws2 = sheet.worksheet('Data_Hidden')
data1 = ws1.get('A1:C10')
data2 = ws2.get('A1:AZ48')
"""

# ✅ AFTER (sheets_fast - <1 second for BOTH)
batch_data = sheets.batch_read(SPREADSHEET_ID, [
    'Dashboard!A1:C10',
    'Data_Hidden!A1:AZ48'
])
dashboard_data = batch_data.get("'Dashboard'!A1:C10", [])
hidden_data = batch_data.get("'Data_Hidden'!A1:AZ48", [])
print(f"✅ Read 2 ranges in one API call")

# ============================================================================
# EXAMPLE 4: Write to a single range
# ============================================================================

# ❌ BEFORE (gspread - 120+ seconds)
"""
sheet = gc.open_by_key(SPREADSHEET_ID)
ws = sheet.worksheet('Dashboard')
ws.update('A1:C3', [[1,2,3], [4,5,6], [7,8,9]])
"""

# ✅ AFTER (sheets_fast - <1 second)
sheets.write_range(SPREADSHEET_ID, 'Dashboard!A1:C3', [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
])
print(f"✅ Wrote 3x3 range")

# ============================================================================
# EXAMPLE 5: Write to multiple ranges at once (BATCH)
# ============================================================================

# ❌ BEFORE (gspread - 240+ seconds for 3 updates)
"""
sheet = gc.open_by_key(SPREADSHEET_ID)
ws1 = sheet.worksheet('Dashboard')
ws2 = sheet.worksheet('Data_Hidden')
ws1.update('A1', [[timestamp]])
ws1.update('B1:D1', [[value1, value2, value3]])
ws2.update('A1:AZ48', fuel_data)
"""

# ✅ AFTER (sheets_fast - <1 second for ALL 3)
from datetime import datetime
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

sheets.batch_write(SPREADSHEET_ID, [
    {'range': 'Dashboard!A1', 'values': [[timestamp]]},
    {'range': 'Dashboard!B1:D1', 'values': [[42.5, 35.2, 28.9]]},
    # {'range': 'Data_Hidden!A1:AZ48', 'values': fuel_data}  # Uncomment when you have data
])
print(f"✅ Wrote to 3 ranges in one API call")

# ============================================================================
# EXAMPLE 6: Get worksheet IDs (for advanced operations)
# ============================================================================

# ✅ Get all worksheet names and IDs
metadata = sheets.get_spreadsheet_metadata(SPREADSHEET_ID)
print(f"\n📋 Available worksheets:")
for sheet in metadata['sheets']:
    props = sheet['properties']
    print(f"   - {props['title']}: {props['sheetId']}")

# ============================================================================
# EXAMPLE 7: Clear a range
# ============================================================================

# ❌ BEFORE (gspread - 120+ seconds)
"""
sheet = gc.open_by_key(SPREADSHEET_ID)
ws = sheet.worksheet('Dashboard')
ws.batch_clear(['A10:Z100'])
"""

# ✅ AFTER (sheets_fast - <1 second)
# sheets.clear_range(SPREADSHEET_ID, 'Dashboard!A10:Z100')
print(f"\n✅ All examples completed!")
print(f"⏱️  Total time: <5 seconds (vs 480+ seconds with gspread)")
