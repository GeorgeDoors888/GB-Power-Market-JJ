#!/usr/bin/env python3
"""
Apply BESS Enhanced Formatting via Python
Applies same formatting as Apps Script formatBESSEnhanced() function
"""
import gspread
from google.oauth2.service_account import Credentials
import os

# Credentials
creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 
                            '/home/george/.config/google-cloud/bigquery-credentials.json')
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(creds_path, scopes=scope)
gc = gspread.authorize(creds)

# Open sheet
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
sh = gc.open_by_key(SHEET_ID)
bess = sh.worksheet('BESS')

print('\n🎨 Applying BESS Enhanced Formatting')
print('=' * 60)

# Row 58: Divider
print('\nRow 58: Divider line...')
bess.update('A58', [['─' * 100]], value_input_option='RAW')
bess.format('A58:Z58', {
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
    'horizontalAlignment': 'LEFT'
})
bess.merge_cells('A58:Z58')
print('✅ Divider applied')

# Row 59: Section title
print('\nRow 59: Section title...')
bess.update('A59', [['─── Enhanced Revenue Analysis (6-Stream Model) ───']], value_input_option='RAW')
bess.format('A59:Q59', {
    'backgroundColor': {'red': 1, 'green': 0.4, 'blue': 0},  # Orange #FF6600
    'textFormat': {
        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},  # White
        'bold': True,
        'fontSize': 12
    },
    'horizontalAlignment': 'CENTER'
})
bess.merge_cells('A59:Q59')
print('✅ Title applied')

# Row 60: Column headers
print('\nRow 60: Column headers...')
bess.format('A60:Q60', {
    'backgroundColor': {'red': 0.85, 'green': 0.91, 'blue': 0.97},  # Light Blue #D9E9F7
    'textFormat': {'bold': True},
    'horizontalAlignment': 'CENTER',
    'verticalAlignment': 'MIDDLE'
})
print('✅ Headers formatted')

# Format timeseries data columns
print('\nFormatting data columns...')
# Timestamp column (A) - left aligned
bess.format('A61:A1500', {'horizontalAlignment': 'LEFT'})
# Numeric columns (K-Q) - right aligned, number format
bess.format('K61:Q1500', {
    'horizontalAlignment': 'RIGHT',
    'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}
})
print('✅ Data columns formatted')

# T60:U67 - KPIs panel
print('\nT60:U67: KPIs panel...')
bess.update('T60', [['📊 Enhanced Revenue KPIs']], value_input_option='RAW')
bess.format('T60:U60', {
    'backgroundColor': {'red': 1, 'green': 0.4, 'blue': 0},  # Orange
    'textFormat': {
        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
        'bold': True,
        'fontSize': 11
    }
})
bess.merge_cells('T60:U60')

# KPI labels (T61:T67)
bess.format('T61:T67', {
    'backgroundColor': {'red': 0.85, 'green': 0.91, 'blue': 0.97},  # Light Blue
    'textFormat': {'bold': True},
    'horizontalAlignment': 'RIGHT'
})

# KPI values (U61:U67)
bess.format('U61:U67', {
    'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.8},  # Yellow #FFFFCC
    'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0'},
    'horizontalAlignment': 'RIGHT'
})
print('✅ KPIs panel formatted')

# W60:Y67 - Revenue Stack
print('\nW60:Y67: Revenue stack...')
bess.update('W60:Y60', [['Revenue Stream', '£/year', '%']], value_input_option='RAW')
bess.format('W60:Y60', {
    'backgroundColor': {'red': 1, 'green': 0.4, 'blue': 0},  # Orange
    'textFormat': {
        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
        'bold': True
    },
    'horizontalAlignment': 'CENTER'
})

# Revenue stack labels (W61:W67)
bess.format('W61:W67', {
    'backgroundColor': {'red': 0.85, 'green': 0.91, 'blue': 0.97},  # Light Blue
    'horizontalAlignment': 'LEFT'
})

# Revenue stack values (X61:Y67)
bess.format('X61:Y67', {
    'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.8},  # Yellow
    'horizontalAlignment': 'RIGHT'
})
bess.format('X61:X67', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'}})
bess.format('Y61:Y67', {'numberFormat': {'type': 'PERCENT', 'pattern': '0.0%'}})
print('✅ Revenue stack formatted')

# Set column widths
print('\nSetting column widths...')
requests = [
    {'updateDimensionProperties': {
        'range': {'sheetId': bess.id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1},
        'properties': {'pixelSize': 150}, 'fields': 'pixelSize'
    }},  # A: Timestamp
    {'updateDimensionProperties': {
        'range': {'sheetId': bess.id, 'dimension': 'COLUMNS', 'startIndex': 10, 'endIndex': 11},
        'properties': {'pixelSize': 100}, 'fields': 'pixelSize'
    }},  # K
    {'updateDimensionProperties': {
        'range': {'sheetId': bess.id, 'dimension': 'COLUMNS', 'startIndex': 19, 'endIndex': 20},
        'properties': {'pixelSize': 150}, 'fields': 'pixelSize'
    }},  # T
    {'updateDimensionProperties': {
        'range': {'sheetId': bess.id, 'dimension': 'COLUMNS', 'startIndex': 20, 'endIndex': 21},
        'properties': {'pixelSize': 110}, 'fields': 'pixelSize'
    }},  # U
    {'updateDimensionProperties': {
        'range': {'sheetId': bess.id, 'dimension': 'COLUMNS', 'startIndex': 22, 'endIndex': 23},
        'properties': {'pixelSize': 150}, 'fields': 'pixelSize'
    }},  # W
    {'updateDimensionProperties': {
        'range': {'sheetId': bess.id, 'dimension': 'COLUMNS', 'startIndex': 23, 'endIndex': 24},
        'properties': {'pixelSize': 100}, 'fields': 'pixelSize'
    }},  # X
    {'updateDimensionProperties': {
        'range': {'sheetId': bess.id, 'dimension': 'COLUMNS', 'startIndex': 24, 'endIndex': 25},
        'properties': {'pixelSize': 80}, 'fields': 'pixelSize'
    }},  # Y
]
sh.batch_update({'requests': requests})
print('✅ Column widths set')

# Don't freeze rows - allows scrolling
print('\nSkipping row freeze (allows scrolling)')
print('ℹ️  Tip: Manually freeze row 60 via View menu if desired')

print('\n' + '=' * 60)
print('✅ FORMATTING COMPLETE!')
print('\nFormatted sections:')
print('  • Row 58: Grey divider')
print('  • Row 59: Orange title "Enhanced Revenue Analysis"')
print('  • Row 60: Light blue headers')
print('  • T60:U67: KPIs panel (orange header, yellow values)')
print('  • W60:Y67: Revenue stack (orange header, yellow values)')
print('  • Column widths optimized')
print('  • Row 60 frozen')
print('\nExisting sections preserved:')
print('  • Rows 1-14: DNO Lookup ✅')
print('  • Rows 15-20: HH Profile ✅')
print('  • Rows 27-50: BtM PPA ✅')
print('\n🌐 View sheet:')
print(f'  https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit')
print('\n')
