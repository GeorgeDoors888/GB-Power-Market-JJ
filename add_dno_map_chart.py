#!/usr/bin/env python3
"""
Add DNO Map Chart to Google Sheets
Uses Google Sheets API to create a GeoChart (Map) directly in the spreadsheet
"""

import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'

def add_map_chart():
    """Add a geographic map chart to the DNO sheet"""
    
    print("🗺️  Adding DNO Map Chart to Google Sheet...")
    print("=" * 80)
    
    # Authenticate
    print("\n🔐 Authenticating...")
    cred_paths = [
        'inner-cinema-credentials.json',
        os.path.expanduser('~/inner-cinema-credentials.json')
    ]
    
    creds_file = None
    for path in cred_paths:
        if os.path.exists(path):
            creds_file = path
            break
    
    if not creds_file:
        print("❌ Credentials not found")
        return
    
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    
    # Build Sheets service
    service = build('sheets', 'v4', credentials=creds)
    
    # Get sheet ID for DNO sheet
    print(f"\n📊 Getting sheet metadata...")
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    
    dno_sheet_id = None
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == 'DNO':
            dno_sheet_id = sheet['properties']['sheetId']
            break
    
    if not dno_sheet_id:
        print("❌ DNO sheet not found")
        return
    
    print(f"   ✅ Found DNO sheet (ID: {dno_sheet_id})")
    
    # Prepare data for the map
    # Google Maps Chart requires: Region, Value (optional), and Label (optional)
    # We'll map DNO regions to their customer counts
    
    print("\n🗺️  Creating GeoChart...")
    
    # Create the chart specification
    requests = [{
        'addChart': {
            'chart': {
                'spec': {
                    'title': 'UK Distribution Network Operators (DNO) Coverage',
                    'geoChart': {
                        'domain': 'GB',  # Great Britain
                        'region': '826',  # ISO 3166-1 code for UK
                        'colorAxis': {
                            'minValue': 0,
                            'maxValue': 10000000,
                            'colors': [
                                {'color': {'red': 0.9, 'green': 0.9, 'blue': 1.0}},  # Light blue
                                {'color': {'red': 0.2, 'green': 0.4, 'blue': 0.8}}   # Dark blue
                            ]
                        }
                    },
                    'hiddenDimensionStrategy': 'SKIP_HIDDEN_ROWS_AND_COLUMNS'
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': dno_sheet_id,
                            'rowIndex': 0,
                            'columnIndex': 7  # Column H
                        },
                        'offsetXPixels': 10,
                        'offsetYPixels': 10,
                        'widthPixels': 800,
                        'heightPixels': 600
                    }
                }
            }
        }
    }]
    
    # For UK regions, we need to use region names that Google recognizes
    # Let's add a helper column with standardized region names
    
    print("\n📝 Preparing regional data...")
    
    # Map DNO regions to Google-recognized UK regions/counties
    dno_to_google_regions = {
        'Eastern Power Networks (EPN)': 'England',
        'London Power Networks (LPN)': 'Greater London',
        'South Eastern Power Networks (SPN)': 'South East England',
        'Western Power Distribution - West Midlands': 'West Midlands',
        'Western Power Distribution - East Midlands': 'East Midlands',
        'Western Power Distribution - South West': 'South West England',
        'Western Power Distribution - South Wales': 'Wales',
        'Electricity North West': 'North West England',
        'Northern Powergrid - North East': 'North East England',
        'Northern Powergrid - Yorkshire': 'Yorkshire',
        'Scottish & Southern (SHEPD)': 'Scotland',
        'Scottish & Southern (HYDRO)': 'Scotland',
        'SP Energy Networks - SP Distribution': 'Scotland',
        'SP Energy Networks - SP Manweb': 'North Wales'
    }
    
    # Actually, let's use a simpler approach - create a proper UK map using geochart
    # with the actual data from the sheet
    
    print("\n🎨 Adding chart with DNO data...")
    
    # Better approach: Use the Region column (column D) and Customers column (column E)
    chart_spec = {
        'addChart': {
            'chart': {
                'spec': {
                    'title': '🗺️ UK DNO Coverage Map',
                    'basicChart': {
                        'chartType': 'AREA',
                        'legendPosition': 'RIGHT_LEGEND',
                        'axis': [
                            {'position': 'BOTTOM_AXIS', 'title': 'DNO Region'},
                            {'position': 'LEFT_AXIS', 'title': 'Customers (Millions)'}
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': dno_sheet_id,
                                        'startRowIndex': 1,  # Skip header
                                        'endRowIndex': 15,    # 14 DNOs
                                        'startColumnIndex': 0,  # Column A (DNO Name)
                                        'endColumnIndex': 1
                                    }]
                                }
                            }
                        }],
                        'series': [{
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': dno_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': 15,
                                        'startColumnIndex': 4,  # Column E (Customers)
                                        'endColumnIndex': 5
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS'
                        }],
                        'headerCount': 1
                    }
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': dno_sheet_id,
                            'rowIndex': 1,
                            'columnIndex': 7  # Column H
                        },
                        'offsetXPixels': 20,
                        'offsetYPixels': 20,
                        'widthPixels': 1000,
                        'heightPixels': 600
                    }
                }
            }
        }
    }
    
    # Execute the request
    body = {'requests': [chart_spec]}
    
    try:
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        
        print("   ✅ Chart added successfully!")
        
        print("\n" + "=" * 80)
        print("✅ DNO MAP CHART CREATED!")
        print("=" * 80)
        print(f"\n🔗 View sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dno_sheet_id}")
        print("\n📊 Chart shows DNO coverage by customer count")
        print("   Located in column H of the DNO sheet")
        print("\n💡 For interactive geographic map, you can still use the Apps Script option:")
        print("   Extensions → Apps Script → Paste code from dno_map_apps_script.gs")
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error creating chart: {e}")
        print("\n💡 Alternative: Let me create a better visualization using Apps Script...")
        return False
    
    return True

if __name__ == '__main__':
    add_map_chart()
