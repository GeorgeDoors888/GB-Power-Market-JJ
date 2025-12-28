#!/usr/bin/env python3
"""Add live values to column L for market metrics"""

from fast_sheets import FastSheets

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

print("Adding formulas to column L for live values...")

sheets = FastSheets('inner-cinema-credentials.json', use_cache=True)

# Add formulas to pull current values from Data_Hidden column W
updates = [
    {
        'range': 'Live Dashboard v2!L14',
        'values': [['=Data_Hidden!W27']]  # Avg Accepted Price (BM_Avg_Price)
    },
    {
        'range': 'Live Dashboard v2!L16',
        'values': [['=Data_Hidden!W28']]  # Vol-Wtd Avg (BM_Vol_Wtd)
    },
    {
        'range': 'Live Dashboard v2!L18',
        'values': [['=Data_Hidden!W29']]  # Market Index (MID_Price)
    }
]

# Use USER_ENTERED so formulas work
sheets.batch_update(SPREADSHEET_ID, updates, value_input_option='USER_ENTERED', queue=False)

print("✅ Done! Column L now shows live values:")
print("   L14: =Data_Hidden!W27 (Avg Accepted Price)")
print("   L16: =Data_Hidden!W28 (Vol-Wtd Avg)")
print("   L18: =Data_Hidden!W29 (Market Index)")
