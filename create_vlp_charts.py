#!/usr/bin/env python3
"""
Create VLP Dashboard Charts - Automate chart creation via gspread
Part of automated dashboard pipeline: vlp_dashboard_simple.py → format_vlp_dashboard.py → THIS SCRIPT
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Load config
with open('vlp_prerequisites.json', 'r') as f:
    config = json.load(f)

SPREADSHEET_ID = config['SPREADSHEET_ID']
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

def get_sheets_client():
    """Authorize Google Sheets API"""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
    return gspread.authorize(creds)

def create_revenue_stack_chart():
    """Chart 1: Revenue Stack (stacked column chart on Dashboard)"""
    
    print('📊 Creating Revenue Stack chart...')
    
    gc = get_sheets_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    dash = ss.worksheet('Dashboard')
    dash_id = dash.id
    
    # Chart spec: Stacked column chart of revenue breakdown (A5:B10)
    chart_spec = {
        'title': 'Revenue Breakdown',
        'basicChart': {
            'chartType': 'COLUMN',
            'stackedType': 'STACKED',
            'legendPosition': 'RIGHT_LEGEND',
            'axis': [
                {'position': 'BOTTOM_AXIS', 'title': 'Revenue Line'},
                {'position': 'LEFT_AXIS', 'title': 'Value (£)'}
            ],
            'domains': [
                {
                    'domain': {
                        'sourceRange': {
                            'sources': [{
                                'sheetId': dash_id,
                                'startRowIndex': 4,
                                'endRowIndex': 10,
                                'startColumnIndex': 0,
                                'endColumnIndex': 1
                            }]
                        }
                    }
                }
            ],
            'series': [
                {
                    'series': {
                        'sourceRange': {
                            'sources': [{
                                'sheetId': dash_id,
                                'startRowIndex': 4,
                                'endRowIndex': 10,
                                'startColumnIndex': 1,
                                'endColumnIndex': 2
                            }]
                        }
                    },
                    'targetAxis': 'LEFT_AXIS'
                }
            ]
        }
    }
    
    # Position chart at G4 (column 6, row 3 in 0-indexed)
    position = {
        'overlayPosition': {
            'anchorCell': {
                'sheetId': dash_id,
                'rowIndex': 3,
                'columnIndex': 6
            }
        }
    }
    
    # Add chart via API
    request = {
        'addChart': {
            'chart': {
                'spec': chart_spec,
                'position': position
            }
        }
    }
    
    ss.batch_update({'requests': [request]})
    print('   ✅ Revenue Stack chart created')

def create_soc_chart():
    """Chart 2: State of Charge Over Time (line chart on Dashboard)"""
    
    print('📊 Creating SoC chart...')
    
    gc = get_sheets_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    dash = ss.worksheet('Dashboard')
    bess = ss.worksheet('BESS_VLP')
    dash_id = dash.id
    bess_id = bess.id
    
    # Chart spec: Line chart of SoC (BESS_VLP sheet, columns A vs N)
    chart_spec = {
        'title': 'Battery State of Charge',
        'basicChart': {
            'chartType': 'LINE',
            'legendPosition': 'RIGHT_LEGEND',
            'axis': [
                {'position': 'BOTTOM_AXIS', 'title': 'Time'},
                {'position': 'LEFT_AXIS', 'title': 'SoC (MWh)'}
            ],
            'domains': [
                {
                    'domain': {
                        'sourceRange': {
                            'sources': [{
                                'sheetId': bess_id,
                                'startRowIndex': 1,  # Skip header
                                'endRowIndex': 500,  # Adjust based on data
                                'startColumnIndex': 0,  # Column A (settlementDate)
                                'endColumnIndex': 1
                            }]
                        }
                    }
                }
            ],
            'series': [
                {
                    'series': {
                        'sourceRange': {
                            'sources': [{
                                'sheetId': bess_id,
                                'startRowIndex': 1,
                                'endRowIndex': 500,
                                'startColumnIndex': 13,  # Column N (soc_end)
                                'endColumnIndex': 14
                            }]
                        }
                    },
                    'targetAxis': 'LEFT_AXIS'
                }
            ]
        }
    }
    
    # Position chart at G15 (column 6, row 14 in 0-indexed)
    position = {
        'overlayPosition': {
            'anchorCell': {
                'sheetId': dash_id,
                'rowIndex': 14,
                'columnIndex': 6
            }
        }
    }
    
    request = {
        'addChart': {
            'chart': {
                'spec': chart_spec,
                'position': position
            }
        }
    }
    
    ss.batch_update({'requests': [request]})
    print('   ✅ SoC chart created')

def create_battery_actions_chart():
    """Chart 3: Battery Charge/Discharge Actions (column chart on Dashboard)"""
    
    print('📊 Creating Battery Actions chart...')
    
    gc = get_sheets_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    dash = ss.worksheet('Dashboard')
    bess = ss.worksheet('BESS_VLP')
    dash_id = dash.id
    bess_id = bess.id
    
    # Chart spec: Column chart of bm_accepted_mwh (positive = discharge, negative = charge)
    chart_spec = {
        'title': 'Battery Charge/Discharge Actions',
        'basicChart': {
            'chartType': 'COLUMN',
            'legendPosition': 'NO_LEGEND',  # Changed from 'NONE'
            'axis': [
                {'position': 'BOTTOM_AXIS', 'title': 'Time'},
                {'position': 'LEFT_AXIS', 'title': 'MWh (+ discharge, - charge)'}
            ],
            'domains': [
                {
                    'domain': {
                        'sourceRange': {
                            'sources': [{
                                'sheetId': bess_id,
                                'startRowIndex': 1,
                                'endRowIndex': 500,
                                'startColumnIndex': 0,  # Column A
                                'endColumnIndex': 1
                            }]
                        }
                    }
                }
            ],
            'series': [
                {
                    'series': {
                        'sourceRange': {
                            'sources': [{
                                'sheetId': bess_id,
                                'startRowIndex': 1,
                                'endRowIndex': 500,
                                'startColumnIndex': 2,  # Column C (bm_accepted_mwh)
                                'endColumnIndex': 3
                            }]
                        }
                    },
                    'targetAxis': 'LEFT_AXIS'
                }
            ]
        }
    }
    
    # Position chart at M4 (column 12, row 3 in 0-indexed)
    position = {
        'overlayPosition': {
            'anchorCell': {
                'sheetId': dash_id,
                'rowIndex': 3,
                'columnIndex': 12
            }
        }
    }
    
    request = {
        'addChart': {
            'chart': {
                'spec': chart_spec,
                'position': position
            }
        }
    }
    
    ss.batch_update({'requests': [request]})
    print('   ✅ Battery Actions chart created')

def create_margin_chart():
    """Chart 4: Per-SP Gross Margin (line chart on Dashboard)"""
    
    print('📊 Creating Gross Margin chart...')
    
    gc = get_sheets_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    dash = ss.worksheet('Dashboard')
    bess = ss.worksheet('BESS_VLP')
    dash_id = dash.id
    bess_id = bess.id
    
    # Chart spec: Line chart of gross_margin_sp
    chart_spec = {
        'title': 'Gross Margin per Settlement Period',
        'basicChart': {
            'chartType': 'LINE',
            'legendPosition': 'NO_LEGEND',  # Changed from 'NONE'
            'axis': [
                {'position': 'BOTTOM_AXIS', 'title': 'Time'},
                {'position': 'LEFT_AXIS', 'title': 'Margin (£)'}
            ],
            'domains': [
                {
                    'domain': {
                        'sourceRange': {
                            'sources': [{
                                'sheetId': bess_id,
                                'startRowIndex': 1,
                                'endRowIndex': 500,
                                'startColumnIndex': 0,  # Column A
                                'endColumnIndex': 1
                            }]
                        }
                    }
                }
            ],
            'series': [
                {
                    'series': {
                        'sourceRange': {
                            'sources': [{
                                'sheetId': bess_id,
                                'startRowIndex': 1,
                                'endRowIndex': 500,
                                'startColumnIndex': 11,  # Column L (gross_margin_sp)
                                'endColumnIndex': 12
                            }]
                        }
                    },
                    'targetAxis': 'LEFT_AXIS'
                }
            ]
        }
    }
    
    # Position chart at M15 (column 12, row 14 in 0-indexed)
    position = {
        'overlayPosition': {
            'anchorCell': {
                'sheetId': dash_id,
                'rowIndex': 14,
                'columnIndex': 12
            }
        }
    }
    
    request = {
        'addChart': {
            'chart': {
                'spec': chart_spec,
                'position': position
            }
        }
    }
    
    ss.batch_update({'requests': [request]})
    print('   ✅ Gross Margin chart created')

def main():
    """Create all charts"""
    
    print('📊 VLP DASHBOARD CHARTS')
    print('=' * 60)
    
    create_revenue_stack_chart()
    create_soc_chart()
    create_battery_actions_chart()
    create_margin_chart()
    
    print(f'\n✅ COMPLETE! 4 charts created on Dashboard')
    print(f'   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/')

if __name__ == '__main__':
    main()
