#!/usr/bin/env python3
"""
Simple Refresh Trigger - Just click to refresh!

This script writes a trigger to your Google Sheet to request a refresh.
Much simpler than trying to get custom menus to work.

Usage:
    python3 trigger_refresh.py
"""

import pickle
import gspread
from datetime import datetime

# Load credentials
with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

# Connect to sheet
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
sheet = spreadsheet.worksheet('Analysis BI Enhanced')

# Write trigger
timestamp = datetime.utcnow().isoformat() + 'Z'
trigger_value = f'REFRESH_REQUESTED:{timestamp}'

print(f"🔄 Triggering refresh...")
print(f"   Writing to cell M5: {trigger_value}")

sheet.update_acell('M5', trigger_value)
sheet.update_acell('L5', '⏳ Refreshing...')

# Format cells
sheet.format('L5', {
    'backgroundColor': {'red': 1.0, 'green': 0.98, 'blue': 0.77}  # Yellow
})

print(f"✅ Refresh triggered!")
print(f"")
print(f"The Python watcher will detect this and run the update.")
print(f"Watch cell L5 for status:")
print(f"   ⏳ Refreshing... → ✅ Up to date")
print(f"")
print(f"Or just run the update directly:")
print(f"   python3 update_analysis_bi_enhanced.py")
