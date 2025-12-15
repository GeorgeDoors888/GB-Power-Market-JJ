#!/usr/bin/env python3
"""
Read charts from Dashboard sheet in Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'inner-cinema-credentials.json'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open the spreadsheet
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# Get Dashboard sheet
dashboard = spreadsheet.worksheet("Dashboard")

# Get all charts metadata
service = build('sheets', 'v4', credentials=creds)
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()

print("📊 CHARTS IN DASHBOARD SHEET:\n")
for sheet in sheet_metadata['sheets']:
    if sheet['properties']['title'] == 'Dashboard':
        if 'charts' in sheet:
            for idx, chart in enumerate(sheet.get('charts', []), 1):
                spec = chart.get('spec', {})
                title = spec.get('title', 'Untitled')
                position = chart.get('position', {}).get('overlayPosition', {}).get('anchorCell', {})
                row = position.get('rowIndex', 0) + 1
                col_idx = position.get('columnIndex', 0)
                col = chr(65 + col_idx) if col_idx < 26 else f"{chr(64 + col_idx//26)}{chr(65 + col_idx%26)}"
                
                print(f"Chart {idx}: {title}")
                print(f"  Position: {col}{row}")
                
                # Get chart type
                if 'basicChart' in spec:
                    chart_type = spec['basicChart'].get('chartType', 'UNKNOWN')
                    print(f"  Type: {chart_type}")
                    
                    # Get data ranges
                    basic = spec['basicChart']
                    if 'series' in basic:
                        for series_idx, series_obj in enumerate(basic.get('series', [])):
                            series_data = series_obj.get('series', {}).get('sourceRange', {}).get('sources', [])
                            if series_data:
                                source = series_data[0]
                                sheet_id = source.get('sheetId')
                                start_row = source.get('startRowIndex', 0)
                                end_row = source.get('endRowIndex', 0)
                                start_col = source.get('startColumnIndex', 0)
                                end_col = source.get('endColumnIndex', 0)
                                
                                # Find sheet name by ID
                                source_sheet = 'Unknown'
                                for s in sheet_metadata['sheets']:
                                    if s['properties']['sheetId'] == sheet_id:
                                        source_sheet = s['properties']['title']
                                        break
                                
                                print(f"  Series {series_idx+1}: {source_sheet} rows {start_row+1}-{end_row} cols {start_col}-{end_col-1}")
                
                print()
        else:
            print("No charts found in Dashboard sheet")
        break
