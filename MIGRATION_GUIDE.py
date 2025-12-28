#!/usr/bin/env python3
"""
QUICK REFERENCE: FastSheetsAPI vs gspread
Use this as a cheat sheet when migrating scripts
"""

# ============================================================
# GSPREAD (OLD - SLOW 60s+) - COMMENTED OUT
# ============================================================

# OLD METHOD - AVOID! (All code below commented to prevent execution)
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials

creds = ServiceAccountCredentials.from_json_keyfile_name(
    'inner-cinema-credentials.json',
    ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
)
client = gspread.authorize(creds)
sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')  # ⚠️ HANGS 60s+
ws = sheet.worksheet('Dashboard')  # ⚠️ 1s+ delay

# Read operations (1s+ each)
value = ws.acell('A1').value
range_data = ws.get('A1:B10')
all_data = ws.get_all_values()

# Write operations (1s+ each)
ws.update('A1', [['Hello']])
ws.update_cell(1, 1, 'Hello')
ws.batch_update([
    {'range': 'A1', 'values': [['x']]},
    {'range': 'B1', 'values': [['y']]}
])
"""

# ============================================================
# FASTSHEETSAPI (NEW - FAST 0.5s) - EXAMPLES
# ============================================================

"""
# NEW METHOD - USE THIS!
from fast_sheets_helper import FastSheetsAPI

api = FastSheetsAPI()  # 0.05s
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

# Read operations (0.5-0.7s each)
range_data = api.read_range(SPREADSHEET_ID, 'Dashboard!A1:B10')
single_cell = api.read_range(SPREADSHEET_ID, 'Dashboard!A1')
# Note: Returns 2D list, so access as: single_cell[0][0]

# Write operations (0.3-0.4s each)
api.update_single_range(SPREADSHEET_ID, 'Dashboard!A1', [['Hello']])

# Batch operations (0.2-0.3s for multiple)
api.batch_update(SPREADSHEET_ID, [
    {'range': 'Dashboard!A1', 'values': [['x']]},
    {'range': 'Dashboard!B1', 'values': [['y']]},
    {'range': 'Dashboard!C1', 'values': [['z']]}
])

# Append rows (0.4s)
api.append_rows(SPREADSHEET_ID, 'Dashboard!A1:B1', [
    ['Row 1 Col A', 'Row 1 Col B'],
    ['Row 2 Col A', 'Row 2 Col B']
])

# Clear range (0.3s)
api.clear_range(SPREADSHEET_ID, 'Dashboard!A1:B10')
"""

# ============================================================
# MIGRATION PATTERNS (examples commented)
# ============================================================

# Pattern 1: Simple read
# OLD: value = ws.get('A1')
# NEW: value = api.read_range(SPREADSHEET_ID, 'SheetName!A1')

# Pattern 2: Simple write
# OLD: ws.update('A1', [['value']])
# NEW: api.update_single_range(SPREADSHEET_ID, 'SheetName!A1', [['value']])

# Pattern 3: Batch update
# OLD: ws.batch_update([{'range': 'A1', 'values': [['x']]}])
# NEW: api.batch_update(SPREADSHEET_ID, [{'range': 'Sheet!A1', 'values': [['x']]}])
#      ⚠️ Note: Must include sheet name in range!

# Pattern 4: Read with error handling
"""
# OLD:
try:
    data = ws.get('A1:B10')
except gspread.exceptions.APIError as e:
    print(f"Error: {e}")
    
# NEW:
try:
    data = api.read_range(SPREADSHEET_ID, 'Sheet!A1:B10')
except Exception as e:
    print(f"Error: {e}")
"""

# Pattern 5: Loop with updates (IMPORTANT - use batch!)
"""
# OLD (VERY SLOW - 1s per iteration):
for i, value in enumerate(values):
    ws.update(f'A{i+1}', [[value]])
    
# NEW (FAST - 0.3s for all):
updates = [
    {'range': f'Sheet!A{i+1}', 'values': [[value]]}
    for i, value in enumerate(values)
]
api.batch_update(SPREADSHEET_ID, updates)
"""

# ============================================================
# COMMON GOTCHAS
# ============================================================

# GOTCHA 1: Range format must include sheet name
# ❌ WRONG: api.read_range(SPREADSHEET_ID, 'A1:B10')
# ✅ RIGHT: api.read_range(SPREADSHEET_ID, 'SheetName!A1:B10')

# GOTCHA 2: Values must be 2D list (even for single cell)
# ❌ WRONG: api.update_single_range(SPREADSHEET_ID, 'Sheet!A1', 'value')
# ✅ RIGHT: api.update_single_range(SPREADSHEET_ID, 'Sheet!A1', [['value']])

# GOTCHA 3: Read returns 2D list
# data = api.read_range(SPREADSHEET_ID, 'Sheet!A1')
# ❌ WRONG: print(data)  # Will print [['value']]
# ✅ RIGHT: print(data[0][0])  # Will print 'value'

# GOTCHA 4: Empty cells
# data = api.read_range(SPREADSHEET_ID, 'Sheet!A1:B10')
# If B5 is empty, data[4] might be ['value'] not ['value', '']
# Always check len(row) before accessing indexes

# ============================================================
# PERFORMANCE COMPARISON
# ============================================================

"""
Operation              | gspread | FastSheetsAPI | Speedup
-----------------------|---------|---------------|--------
Initialize client      | 60s+    | 0.05s         | 1200x
Read single cell       | 61s     | 0.57s         | 107x
Write single cell      | 61s     | 0.32s         | 191x
Batch update (6 cells) | 61s     | 0.23s         | 265x
Update 100 cells       | 100s+   | 0.30s         | 333x
Read 1000 cells        | 61s     | 0.75s         | 81x
"""

# ============================================================
# TESTING YOUR MIGRATION
# ============================================================

if __name__ == '__main__':
    from fast_sheets_helper import FastSheetsAPI
    import time
    
    # Test read
    start = time.time()
    api = FastSheetsAPI()
    data = api.read_range(
        '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
        'Live Dashboard v2!A6'
    )
    print(f"✅ Read in {time.time()-start:.2f}s: {data}")
    
    # Test write
    start = time.time()
    result = api.update_single_range(
        '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
        'Live Dashboard v2!Z99',
        [['FastAPI Test']]
    )
    print(f"✅ Write in {time.time()-start:.2f}s: {result.get('totalUpdatedCells')} cells")
    
    print("\n⚡ If both operations completed in <1s each, migration successful!")
