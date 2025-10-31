#!/usr/bin/env python3
"""
Restore Sheet1 to Clean Layout
- Simple header in rows 1-3
- Chart area starts at row 18
- Warnings at row 30+
- Data table at row 18+
"""

import pickle
from googleapiclient.discovery import build
from datetime import datetime

SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

print("🔧 Restoring Sheet1 to Clean Layout")
print("=" * 60)

# Load credentials
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

service = build('sheets', 'v4', credentials=creds)

# Clean, minimal header for Sheet1
header_data = [
    ['UK POWER MARKET DASHBOARD'],  # A1
    [''],  # A2 - blank
    [f'Last Updated: {datetime.now().strftime("%d/%m/%Y %H:%M")}'],  # A3
    [''],  # A4 - blank
    [''],  # A5 - blank
    ['Quick Links:'],  # A6
    ['• Latest Day Analysis → "Latest Day Data" sheet'],  # A7
    ['• Full BI Dashboard → "Analysis BI Enhanced" sheet'],  # A8
    [''],  # A9 - blank
    [''],  # A10 - blank
    [''],  # A11 - blank
    [''],  # A12 - blank
    [''],  # A13 - blank
    [''],  # A14 - blank
    [''],  # A15 - blank
    [''],  # A16 - blank
    ['📊 LATEST DAY ANALYSIS - Chart & Data Below'],  # A17
]

print("📝 Writing clean header (rows 1-17)...")
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Sheet1!A1:A17',
    valueInputOption='RAW',
    body={'values': header_data}
).execute()

# Format header
print("🎨 Formatting header...")
requests = [
    # Title (A1) - Large, bold, blue
    {
        'repeatCell': {
            'range': {
                'sheetId': 0,
                'startRowIndex': 0,
                'endRowIndex': 1,
                'startColumnIndex': 0,
                'endColumnIndex': 5
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7},
                    'textFormat': {
                        'bold': True,
                        'fontSize': 16,
                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                    },
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    },
    # Last Updated (A3) - Gray, italic
    {
        'repeatCell': {
            'range': {
                'sheetId': 0,
                'startRowIndex': 2,
                'endRowIndex': 3,
                'startColumnIndex': 0,
                'endColumnIndex': 3
            },
            'cell': {
                'userEnteredFormat': {
                    'textFormat': {
                        'italic': True,
                        'fontSize': 9,
                        'foregroundColor': {'red': 0.5, 'green': 0.5, 'blue': 0.5}
                    }
                }
            },
            'fields': 'userEnteredFormat(textFormat)'
        }
    },
    # Quick Links section (A6-A8) - Light blue background
    {
        'repeatCell': {
            'range': {
                'sheetId': 0,
                'startRowIndex': 5,
                'endRowIndex': 8,
                'startColumnIndex': 0,
                'endColumnIndex': 3
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 1.0},
                    'textFormat': {'fontSize': 10}
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
        }
    },
    # Section header (A17) - Bold, gray background
    {
        'repeatCell': {
            'range': {
                'sheetId': 0,
                'startRowIndex': 16,
                'endRowIndex': 17,
                'startColumnIndex': 0,
                'endColumnIndex': 8
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85},
                    'textFormat': {'bold': True, 'fontSize': 12}
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
        }
    }
]

service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()

print("✅ Sheet1 restored to clean layout!")
print()
print("Structure:")
print("  Rows 1-17:  Clean header with quick links")
print("  Row 18+:    Latest Day chart and data (from create_latest_day_chart.py)")
print("  Row 30+:    System warnings")
print()
print("Next: Run add_chart_only.py to add the chart")
