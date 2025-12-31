"""
SHEET_IDS_CACHE.py

Worksheet ID cache for fast lookups (Fix #3)
Avoids repeated spreadsheet.get() calls

Usage:
    from SHEET_IDS_CACHE import WORKSHEET_IDS
    range_str = f"'{WORKSHEET_IDS['Live Dashboard v2']}'!A1:B10"
"""

# Main Dashboard Spreadsheet
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SPREADSHEET_NAME = "GB Live 2"

# Worksheet IDs (fetched 2025-12-29)
WORKSHEET_IDS = {
    'DATA': 2004945866,
    'INSTRUCTIONS': 1201966776,
    'Live Dashboard v2': 687718775,
    'Analysis': 225925794,
    'BtM': 115327894,
    'BESS_Event': 1758096144,
    'BtM Calculator': 1979713595,
    'DATA DICTIONARY': 2132067470,
    'Data_Hidden': 1891330986,
    'DropdownData': 486714144,
    'DNO Constraint Costs': 273713365,
    'Test': 1480426095,
    'Constraint Map Data': 2014981863,
    'Constraint Summary': 894048512,
    'DNO Breakdown': None,  # To be populated when created
}

# Apps Script ID (for automation scripts)
APPS_SCRIPT_ID = "1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980"

def get_sheet_id(sheet_name):
    """Get worksheet ID by name"""
    return WORKSHEET_IDS.get(sheet_name)

def get_range_with_id(sheet_name, cell_range):
    """Get full range string using sheet ID"""
    sheet_id = WORKSHEET_IDS.get(sheet_name)
    if sheet_id is None:
        # Fallback to name-based range
        return f"'{sheet_name}'!{cell_range}"
    return f"'{sheet_id}'!{cell_range}"
