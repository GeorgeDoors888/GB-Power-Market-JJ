#!/usr/bin/env python3
"""
Format Enhanced Dashboard
Applies professional formatting to the Dashboard sheet
"""

import pickle
import gspread
from pathlib import Path

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
TOKEN_FILE = Path("token.pickle")

print("🎨 Formatting Enhanced Dashboard...")

# Authenticate
with open(TOKEN_FILE, 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
ss = gc.open_by_key(SPREADSHEET_ID)
dashboard = ss.worksheet('Dashboard')

print("📏 Current dashboard size:", dashboard.row_count, "x", dashboard.col_count)

# Apply Formatting
print("🎨 Applying professional formatting...")

# Format header (Row 1)
dashboard.format('A1:F1', {
    'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.6},
    'textFormat': {
        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
        'fontSize': 16,
        'bold': True
    },
    'horizontalAlignment': 'CENTER'
})

# Format subheader (Row 2)
dashboard.format('A2:F2', {
    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
    'textFormat': {'fontSize': 10, 'italic': True},
    'horizontalAlignment': 'CENTER'
})

# Format section headers (Metrics, Generation Mix, Trend)
section_format = {
    'backgroundColor': {'red': 0.4, 'green': 0.5, 'blue': 0.7},
    'textFormat': {
        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
        'fontSize': 12,
        'bold': True
    }
}

dashboard.format('A4:F4', section_format)  # CURRENT METRICS
dashboard.format('A8:F8', section_format)  # GENERATION BY FUEL TYPE

# Format table header (Row 10)
dashboard.format('A10:F10', {
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
    'textFormat': {'bold': True},
    'horizontalAlignment': 'CENTER'
})

# Format KPI cells (Rows 5-6)
dashboard.format('A5:C5', {
    'backgroundColor': {'red': 0.95, 'green': 0.98, 'blue': 1},
    'textFormat': {'fontSize': 11, 'bold': True}
})
dashboard.format('D5:F5', {
    'backgroundColor': {'red': 1, 'green': 0.98, 'blue': 0.9},
    'textFormat': {'fontSize': 11, 'bold': True}
})
dashboard.format('A6:C6', {
    'backgroundColor': {'red': 0.95, 'green': 0.98, 'blue': 1},
    'textFormat': {'fontSize': 11, 'bold': True}
})
dashboard.format('D6:F6', {
    'backgroundColor': {'red': 1, 'green': 0.98, 'blue': 0.9},
    'textFormat': {'fontSize': 11, 'bold': True}
})

# Adjust column widths using batch_update
print("📐 Adjusting column widths...")
requests = []
requests.append({
    "updateDimensionProperties": {
        "range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
        "properties": {"pixelSize": 250},
        "fields": "pixelSize"
    }
})
requests.append({
    "updateDimensionProperties": {
        "range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
        "properties": {"pixelSize": 150},
        "fields": "pixelSize"
    }
})
requests.append({
    "updateDimensionProperties": {
        "range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3},
        "properties": {"pixelSize": 120},
        "fields": "pixelSize"
    }
})
requests.append({
    "updateDimensionProperties": {
        "range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4},
        "properties": {"pixelSize": 200},
        "fields": "pixelSize"
    }
})

ss.batch_update({"requests": requests})

# Add borders to data table (assuming it starts at row 10)
print("🖼️  Adding borders...")
dashboard.format('A10:D30', {
    'borders': {
        'top': {'style': 'SOLID'},
        'bottom': {'style': 'SOLID'},
        'left': {'style': 'SOLID'},
        'right': {'style': 'SOLID'}
    }
})

print("✅ Dashboard formatting complete!")
print(f"\n🔗 View Dashboard:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard.id}")
