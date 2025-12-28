#!/usr/bin/env python3
"""
Add report generation dropdowns to Analysis sheet based on data categories
Each category produces relevant reports and graphs
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
ANALYSIS_SHEET_ID = 225925794

print("🔧 Adding Report Category dropdowns to Analysis sheet...\n")

creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
service = build('sheets', 'v4', credentials=creds)

# First, expand DropdownData sheet to 10 columns
print("📐 Expanding DropdownData sheet...\n")
metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
dropdown_sheet_id = None
for sheet in metadata['sheets']:
    if sheet['properties']['title'] == 'DropdownData':
        dropdown_sheet_id = sheet['properties']['sheetId']
        break

if dropdown_sheet_id:
    expand_request = {
        'updateSheetProperties': {
            'properties': {
                'sheetId': dropdown_sheet_id,
                'gridProperties': {'columnCount': 10}
            },
            'fields': 'gridProperties.columnCount'
        }
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [expand_request]}
    ).execute()
    print("✅ DropdownData expanded to 10 columns")

# Report categories matching data categories
report_categories = [
    'All',
    '⚡ Generation & Fuel Mix',
    '💰 Balancing Mechanism (Trading)',
    '💷 Pricing & Settlement',
    '📡 System Operations',
    '🔌 Grid Infrastructure',
    '📋 Reference Data',
    '📊 Analytics & Derived',
    '🗂️ REMIT & Compliance'
]

# Report types for each category
report_types = [
    'All',
    'Summary Dashboard',
    'Trend Analysis (7 days)',
    'Trend Analysis (30 days)',
    'Detailed Table',
    'Time Series Chart',
    'Distribution Chart',
    'Comparison Report',
    'Top 10 Ranking',
    'Export to CSV'
]

# Graph types
graph_types = [
    'All',
    'Line Chart (Time Series)',
    'Bar Chart (Comparison)',
    'Stacked Area Chart',
    'Scatter Plot',
    'Heatmap',
    'Histogram',
    'Box Plot',
    'Sparkline Summary'
]

print("📝 Setting up Analysis sheet structure...\n")

# Update sheet layout
# Row 1: Title
# Row 4: Date pickers (already exists)
# Row 5-9: Filter dropdowns (already exists)
# Row 11: Report Category (NEW)
# Row 12: Report Type (NEW)
# Row 13: Graph Type (NEW)
# Row 14: Generate Button placeholder
# Row 16+: Results area

updates = [
    # Headers for new report section
    {'range': 'A11', 'values': [['Report Category:']]},
    {'range': 'A12', 'values': [['Report Type:']]},
    {'range': 'A13', 'values': [['Graph Type:']]},
    {'range': 'A14', 'values': [['Generate Report:']]},
    {'range': 'B14', 'values': [['[Click to Generate]']]},
    {'range': 'A16', 'values': [['📊 Report Results']]},
]

for update in updates:
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"Analysis!{update['range']}",
        valueInputOption='RAW',
        body={'values': update['values']}
    ).execute()

print("✅ Headers added")

# Create DropdownData sheet entries for report options
print("📝 Adding report options to DropdownData sheet...\n")

# Read current DropdownData to find next available column
current_data = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='DropdownData!A1:Z1'
).execute()

next_col_index = len(current_data.get('values', [[]])[0]) if current_data.get('values') else 5

# Column letters
def col_letter(index):
    result = ""
    while index >= 0:
        result = chr(65 + (index % 26)) + result
        index = index // 26 - 1
    return result

cat_col = col_letter(next_col_index)
type_col = col_letter(next_col_index + 1)
graph_col = col_letter(next_col_index + 2)

print(f"   Using columns: {cat_col} (categories), {type_col} (types), {graph_col} (graphs)")

# Write report options to DropdownData
report_data_headers = [[
    'Report Categories',
    'Report Types',
    'Graph Types'
]]

max_rows = max(len(report_categories), len(report_types), len(graph_types))
report_data = []
for i in range(max_rows):
    row = [
        report_categories[i] if i < len(report_categories) else '',
        report_types[i] if i < len(report_types) else '',
        graph_types[i] if i < len(graph_types) else ''
    ]
    report_data.append(row)

all_data = report_data_headers + report_data

service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=f'DropdownData!{cat_col}1:{graph_col}{len(all_data)}',
    valueInputOption='RAW',
    body={'values': all_data}
).execute()

print(f"✅ Added {len(report_categories)} categories, {len(report_types)} report types, {len(graph_types)} graph types")

# Create dropdowns in Analysis sheet
print("\n🔧 Creating report dropdowns...\n")

requests = [
    # B11: Report Category
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 10, 'endRowIndex': 11,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!{cat_col}2:{cat_col}{len(report_categories)+1}'
                    }]
                },
                'showCustomUi': True,
                'strict': True
            }
        }
    },
    # B12: Report Type
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 11, 'endRowIndex': 12,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!{type_col}2:{type_col}{len(report_types)+1}'
                    }]
                },
                'showCustomUi': True,
                'strict': True
            }
        }
    },
    # B13: Graph Type
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 12, 'endRowIndex': 13,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!{graph_col}2:{graph_col}{len(graph_types)+1}'
                    }]
                },
                'showCustomUi': True,
                'strict': True
            }
        }
    }
]

service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()

print("✅ Dropdowns created")

# Set default values
print("📝 Setting defaults...\n")

defaults = [
    ['⚡ Generation & Fuel Mix'],  # B11
    ['Summary Dashboard'],         # B12
    ['Line Chart (Time Series)']   # B13
]

service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Analysis!B11:B13',
    valueInputOption='RAW',
    body={'values': defaults}
).execute()

# Format headers
print("🎨 Applying formatting...\n")

format_requests = [
    # Bold headers
    {
        'repeatCell': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 10, 'endRowIndex': 14,
                'startColumnIndex': 0, 'endColumnIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                }
            },
            'fields': 'userEnteredFormat(textFormat,backgroundColor)'
        }
    },
    # Generate button styling
    {
        'repeatCell': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 13, 'endRowIndex': 14,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'cell': {
                'userEnteredFormat': {
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.2},
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(textFormat,backgroundColor,horizontalAlignment)'
        }
    },
    # Results header
    {
        'repeatCell': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 15, 'endRowIndex': 16,
                'startColumnIndex': 0, 'endColumnIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'textFormat': {'bold': True, 'fontSize': 12},
                    'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1.0}
                }
            },
            'fields': 'userEnteredFormat(textFormat,backgroundColor)'
        }
    }
]

service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': format_requests}
).execute()

print("\n✅ COMPLETE - Report dropdowns added!")
print("\n📋 Analysis Sheet Structure:")
print("   Row 4:  Date Range (From/To)")
print("   Row 5:  Party Role filter")
print("   Row 6:  BMU IDs filter")
print("   Row 7:  Unit Names filter")
print("   Row 8:  Generation Type filter")
print("   Row 9:  Lead Party filter")
print("   Row 11: Report Category (⚡ Generation, 💰 Trading, etc.)")
print("   Row 12: Report Type (Dashboard, Trend, Table, etc.)")
print("   Row 13: Graph Type (Line, Bar, Heatmap, etc.)")
print("   Row 14: Generate Button")
print("   Row 16: Results area")
print("\n🎯 Next: Create Apps Script to generate reports on button click!")
