#!/usr/bin/env python3
"""
Fix Analysis sheet layout:
- Date range selector at top (A2:B3)
- Party Role fields starting at A5
- Date pickers on B2:B3
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)

analysis_sheet = sh.worksheet('Analysis')
sheet_id = analysis_sheet.id

print("🔧 Fixing Analysis sheet layout...\n")

# Clear the messed up area
analysis_sheet.batch_clear(['B5:D15'])

# Set up proper layout
updates = [
    # Title
    {'range': 'A1', 'values': [['Analysis']]},

    # Date range selector (rows 2-3)
    {'range': 'A2', 'values': [['From Date:']]},
    {'range': 'B2', 'values': [[(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')]]},
    {'range': 'A3', 'values': [['To Date:']]},
    {'range': 'B3', 'values': [[datetime.now().strftime('%Y-%m-%d')]]},

    # Party Role fields (starting row 5)
    {'range': 'A5', 'values': [['Party Role:']]},
    {'range': 'A6', 'values': [['BMU IDs:']]},
    {'range': 'A7', 'values': [['Unit Names:']]},
    {'range': 'A8', 'values': [['Generation Type:']]},
    {'range': 'A9', 'values': [['Lead Party:']]},
]

# Apply updates
for update in updates:
    analysis_sheet.update(update['values'], update['range'])

print("✅ Layout fixed")

# Format headers (bold)
analysis_sheet.format('A1', {
    'textFormat': {'bold': True, 'fontSize': 14}
})

analysis_sheet.format('A2:A3', {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
})

analysis_sheet.format('A5:A9', {
    'textFormat': {'bold': True},
})

print("✅ Formatting applied")

# Add date validation to B2:B3
requests = [
    {
        'setDataValidation': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,  # Row 2
                'endRowIndex': 3,    # Row 3
                'startColumnIndex': 1,  # Column B
                'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'DATE_IS_VALID'
                },
                'showCustomUi': True,
                'strict': True,
                'inputMessage': 'Click to select date from calendar'
            }
        }
    }
]

sh.batch_update({'requests': requests})

print("✅ Date pickers added to B2:B3")
print("\n📋 Final layout:")
print("   A1: Analysis (title)")
print("   A2: From Date:  | B2: [DATE PICKER]")
print("   A3: To Date:    | B3: [DATE PICKER]")
print("   A5: Party Role: | B5: [dropdown input]")
print("   A6: BMU IDs:    | B6: [input]")
print("   A7: Unit Names: | B7: [input]")
print("   A8: Generation Type: | B8: [dropdown input]")
print("   A9: Lead Party: | B9: [input]")
print("\n🎉 COMPLETE!")
