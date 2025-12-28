#!/usr/bin/env python3
"""
Programmatically create Geo Chart (choropleth) in Google Sheets
Uses Sheets API to add chart to the DNO Constraint Costs sheet
Visualizes constraint costs by DNO region with color gradient

Spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
"""

import gspread
from google.oauth2.service_account import Credentials

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'DNO Constraint Costs'

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials():
    """Load service account credentials"""
    try:
        creds = Credentials.from_service_account_file(
            'inner-cinema-credentials.json',
            scopes=SCOPES
        )
        return creds
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None

def create_geo_chart(spreadsheet, worksheet):
    """Create choropleth geo chart using Sheets API"""
    print('\n📊 Creating Geo Chart (Choropleth)...')
    
    # Chart configuration
    chart_request = {
        'addChart': {
            'chart': {
                'spec': {
                    'title': 'UK DNO Constraint Costs by Region (Latest Month)',
                    'geoChart': {
                        'domain': {
                            'sourceRange': {
                                'sources': [{
                                    'sheetId': worksheet.id,
                                    'startRowIndex': 0,
                                    'endRowIndex': 15,  # Header + 14 DNO regions
                                    'startColumnIndex': 2,  # Column C (area_name)
                                    'endColumnIndex': 3
                                }]
                            }
                        },
                        'series': {
                            'sourceRange': {
                                'sources': [{
                                    'sheetId': worksheet.id,
                                    'startRowIndex': 0,
                                    'endRowIndex': 15,
                                    'startColumnIndex': 4,  # Column E (total_cost_gbp)
                                    'endColumnIndex': 5
                                }]
                            }
                        },
                        'region': 'GB',  # United Kingdom
                        'resolution': 'provinces',  # Region-level detail
                        'colorAxis': {
                            'minValue': 0,
                            'colors': [
                                {'color': {'red': 0.9, 'green': 0.9, 'blue': 1.0}},  # Light blue (low)
                                {'color': {'red': 0.0, 'green': 0.5, 'blue': 0.8}},  # Medium blue
                                {'color': {'red': 0.0, 'green': 0.2, 'blue': 0.6}}   # Dark blue (high)
                            ]
                        }
                    },
                    'titleTextFormat': {
                        'fontSize': 14,
                        'bold': True
                    }
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': worksheet.id,
                            'rowIndex': 1,
                            'columnIndex': 10  # Column K (next to data)
                        },
                        'offsetXPixels': 20,
                        'offsetYPixels': 20,
                        'widthPixels': 600,
                        'heightPixels': 400
                    }
                }
            }
        }
    }
    
    # Execute batch update
    try:
        spreadsheet.batch_update({'requests': [chart_request]})
        print('✅ Geo chart created successfully')
        return True
    except Exception as e:
        print(f'❌ Error creating chart: {e}')
        print('   Falling back to manual chart creation instructions')
        return False

def create_cost_breakdown_chart(spreadsheet, worksheet):
    """Create stacked column chart for cost breakdown by DNO"""
    print('\n📊 Creating Cost Breakdown Chart...')
    
    chart_request = {
        'addChart': {
            'chart': {
                'spec': {
                    'title': 'Constraint Cost Breakdown by DNO Region',
                    'basicChart': {
                        'chartType': 'COLUMN',
                        'stackedType': 'STACKED',
                        'legendPosition': 'RIGHT_LEGEND',
                        'axis': [
                            {
                                'position': 'BOTTOM_AXIS',
                                'title': 'DNO Region'
                            },
                            {
                                'position': 'LEFT_AXIS',
                                'title': 'Cost (£M)'
                            }
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': worksheet.id,
                                        'startRowIndex': 1,  # Skip header
                                        'endRowIndex': 15,
                                        'startColumnIndex': 2,  # area_name
                                        'endColumnIndex': 3
                                    }]
                                }
                            }
                        }],
                        'series': [
                            {
                                'series': {
                                    'sourceRange': {
                                        'sources': [{
                                            'sheetId': worksheet.id,
                                            'startRowIndex': 0,
                                            'endRowIndex': 15,
                                            'startColumnIndex': 5,  # voltage_cost_gbp
                                            'endColumnIndex': 6
                                        }]
                                    }
                                },
                                'targetAxis': 'LEFT_AXIS',
                                'color': {'red': 1.0, 'green': 0.6, 'blue': 0.0}  # Orange
                            },
                            {
                                'series': {
                                    'sourceRange': {
                                        'sources': [{
                                            'sheetId': worksheet.id,
                                            'startRowIndex': 0,
                                            'endRowIndex': 15,
                                            'startColumnIndex': 6,  # thermal_cost_gbp
                                            'endColumnIndex': 7
                                        }]
                                    }
                                },
                                'targetAxis': 'LEFT_AXIS',
                                'color': {'red': 0.8, 'green': 0.0, 'blue': 0.0}  # Red
                            },
                            {
                                'series': {
                                    'sourceRange': {
                                        'sources': [{
                                            'sheetId': worksheet.id,
                                            'startRowIndex': 0,
                                            'endRowIndex': 15,
                                            'startColumnIndex': 7,  # inertia_cost_gbp
                                            'endColumnIndex': 8
                                        }]
                                    }
                                },
                                'targetAxis': 'LEFT_AXIS',
                                'color': {'red': 0.2, 'green': 0.8, 'blue': 0.2}  # Green
                            }
                        ]
                    },
                    'titleTextFormat': {
                        'fontSize': 14,
                        'bold': True
                    }
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': worksheet.id,
                            'rowIndex': 18,
                            'columnIndex': 0
                        },
                        'offsetXPixels': 20,
                        'offsetYPixels': 20,
                        'widthPixels': 800,
                        'heightPixels': 400
                    }
                }
            }
        }
    }
    
    try:
        spreadsheet.batch_update({'requests': [chart_request]})
        print('✅ Cost breakdown chart created successfully')
        return True
    except Exception as e:
        print(f'❌ Error creating breakdown chart: {e}')
        return False

def main():
    print('🎨 Creating Geo Charts in Google Sheets')
    print('='*80)
    print(f'Spreadsheet: {SPREADSHEET_ID}')
    print(f'Sheet Name: {SHEET_NAME}')
    print('='*80)
    
    # Load credentials
    creds = get_credentials()
    if not creds:
        return
    
    # Initialize gspread client
    gc = gspread.authorize(creds)
    
    # Open spreadsheet
    print(f'\n📂 Opening spreadsheet...')
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        print(f'✅ Opened: {spreadsheet.title}')
    except Exception as e:
        print(f'❌ Error opening spreadsheet: {e}')
        return
    
    # Get worksheet
    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        print(f'✅ Found sheet: {SHEET_NAME} (ID: {worksheet.id})')
    except gspread.exceptions.WorksheetNotFound:
        print(f'❌ Sheet "{SHEET_NAME}" not found')
        print('   Run: python3 add_bigquery_to_sheets.py first')
        return
    
    # Create geo chart
    geo_success = create_geo_chart(spreadsheet, worksheet)
    
    # Create cost breakdown chart
    breakdown_success = create_cost_breakdown_chart(spreadsheet, worksheet)
    
    print('\n' + '='*80)
    if geo_success and breakdown_success:
        print('✅ SUCCESS: Both charts created successfully')
    elif geo_success:
        print('⚠️  PARTIAL: Geo chart created, breakdown chart failed')
    elif breakdown_success:
        print('⚠️  PARTIAL: Breakdown chart created, geo chart failed')
    else:
        print('❌ FAILED: Could not create charts automatically')
        print('\nManual Steps:')
        print('1. Open: https://docs.google.com/spreadsheets/d/{}/edit#gid={}'.format(
            SPREADSHEET_ID, worksheet.id))
        print('2. Select range A1:E15 (area_name + total_cost_gbp columns)')
        print('3. Insert → Chart → Geo chart')
        print('4. Configure: Region=area_name, Value=total_cost_gbp')
    print('='*80)
    
    print(f'\nView Sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}')

if __name__ == '__main__':
    main()
