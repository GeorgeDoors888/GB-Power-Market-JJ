#!/usr/bin/env python3
"""
VLP Dashboard - Advanced Charts & Formatting
Creates professional charts using Google Sheets API
"""

from google.oauth2.service_account import Credentials
import gspread
from gspread_formatting import *
import time

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

def get_sheets_client():
    """Initialize Google Sheets client with formatting permissions"""
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def create_profit_sparkline_chart(spreadsheet, worksheet):
    """Create sparkline chart for profit trend"""
    sheet_id = worksheet.id
    
    chart_spec = {
        'title': '24-Hour Profit Trend',
        'basicChart': {
            'chartType': 'LINE',
            'legendPosition': 'BOTTOM_LEGEND',
            'axis': [
                {
                    'position': 'BOTTOM_AXIS',
                    'title': 'Settlement Period'
                },
                {
                    'position': 'LEFT_AXIS',
                    'title': 'Profit (£/MWh)'
                }
            ],
            'domains': [
                {
                    'domain': {
                        'sourceRange': {
                            'sources': [
                                {
                                    'sheetId': sheet_id,
                                    'startRowIndex': 40,
                                    'endRowIndex': 88,
                                    'startColumnIndex': 0,
                                    'endColumnIndex': 1
                                }
                            ]
                        }
                    }
                }
            ],
            'series': [
                {
                    'series': {
                        'sourceRange': {
                            'sources': [
                                {
                                    'sheetId': sheet_id,
                                    'startRowIndex': 40,
                                    'endRowIndex': 88,
                                    'startColumnIndex': 2,
                                    'endColumnIndex': 3
                                }
                            ]
                        }
                    },
                    'targetAxis': 'LEFT_AXIS'
                }
            ],
            'headerCount': 1
        }
    }
    
    request = {
        'addChart': {
            'chart': {
                'spec': chart_spec,
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': sheet_id,
                            'rowIndex': 35,  # Changed from 24 to 35 (below stacking scenarios)
                            'columnIndex': 0
                        },
                        'widthPixels': 600,
                        'heightPixels': 300
                    }
                }
            }
        }
    }
    
    spreadsheet.batch_update({'requests': [request]})

def create_service_breakdown_chart(spreadsheet, worksheet):
    """Create pie chart for service revenue breakdown"""
    sheet_id = worksheet.id
    
    chart_spec = {
        'title': 'Revenue Breakdown by Service',
        'pieChart': {
            'legendPosition': 'RIGHT_LEGEND',
            'domain': {
                'sourceRange': {
                    'sources': [
                        {
                            'sheetId': sheet_id,
                            'startRowIndex': 17,
                            'endRowIndex': 25,
                            'startColumnIndex': 0,
                            'endColumnIndex': 1
                        }
                    ]
                }
            },
            'series': {
                'sourceRange': {
                    'sources': [
                        {
                            'sheetId': sheet_id,
                            'startRowIndex': 17,
                            'endRowIndex': 25,
                            'startColumnIndex': 2,
                            'endColumnIndex': 3
                        }
                    ]
                }
            },
            'pieHole': 0.4  # Donut chart
        }
    }
    
    request = {
        'addChart': {
            'chart': {
                'spec': chart_spec,
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': sheet_id,
                            'rowIndex': 35,  # Changed from 24 to 35
                            'columnIndex': 7   # Changed from 6 to 7 (more right)
                        },
                        'widthPixels': 500,
                        'heightPixels': 300
                    }
                }
            }
        }
    }
    
    spreadsheet.batch_update({'requests': [request]})

def create_duos_band_chart(spreadsheet, worksheet):
    """Create column chart for profit by DUoS band"""
    sheet_id = worksheet.id
    
    chart_spec = {
        'title': 'Average Profit by DUoS Band (7 days)',
        'basicChart': {
            'chartType': 'COLUMN',
            'legendPosition': 'BOTTOM_LEGEND',
            'axis': [
                {
                    'position': 'BOTTOM_AXIS',
                    'title': 'DUoS Band'
                },
                {
                    'position': 'LEFT_AXIS',
                    'title': 'Profit (£/MWh)'
                }
            ],
            'domains': [
                {
                    'domain': {
                        'sourceRange': {
                            'sources': [
                                {
                                    'sheetId': sheet_id,
                                    'startRowIndex': 5,
                                    'endRowIndex': 8,
                                    'startColumnIndex': 10,
                                    'endColumnIndex': 11
                                }
                            ]
                        }
                    }
                }
            ],
            'series': [
                {
                    'series': {
                        'sourceRange': {
                            'sources': [
                                {
                                    'sheetId': sheet_id,
                                    'startRowIndex': 5,
                                    'endRowIndex': 8,
                                    'startColumnIndex': 12,
                                    'endColumnIndex': 13
                                }
                            ]
                        }
                    },
                    'targetAxis': 'LEFT_AXIS',
                    'color': {
                        'red': 0.0,
                        'green': 0.6,
                        'blue': 0.0
                    }
                }
            ],
            'headerCount': 1
        }
    }
    
    request = {
        'addChart': {
            'chart': {
                'spec': chart_spec,
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': sheet_id,
                            'rowIndex': 10,  # Changed from 10 to position below band data
                            'columnIndex': 10
                        },
                        'widthPixels': 400,
                        'heightPixels': 250
                    }
                }
            }
        }
    }
    
    spreadsheet.batch_update({'requests': [request]})

def apply_advanced_formatting(worksheet):
    """Apply advanced color coding and conditional formatting"""
    sheet_id = worksheet.id
    
    # Color scale for profit column (green = high, red = low)
    profit_conditional_format = {
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [
                    {
                        'sheetId': sheet_id,
                        'startRowIndex': 41,
                        'endRowIndex': 89,
                        'startColumnIndex': 2,
                        'endColumnIndex': 3
                    }
                ],
                'gradientRule': {
                    'minpoint': {
                        'color': {'red': 1.0, 'green': 0.4, 'blue': 0.4},
                        'type': 'MIN'
                    },
                    'midpoint': {
                        'color': {'red': 1.0, 'green': 1.0, 'blue': 0.4},
                        'type': 'PERCENTILE',
                        'value': '50'
                    },
                    'maxpoint': {
                        'color': {'red': 0.4, 'green': 1.0, 'blue': 0.4},
                        'type': 'MAX'
                    }
                }
            },
            'index': 0
        }
    }
    
    # Number format for currency
    currency_format = {
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 5,
                'endRowIndex': 14,
                'startColumnIndex': 1,
                'endColumnIndex': 2
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'CURRENCY',
                        'pattern': '£#,##0.00'
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    }
    
    # Bold and center headers
    header_format = {
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 16,
                'endRowIndex': 17,
                'startColumnIndex': 0,
                'endColumnIndex': 5
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                    'textFormat': {
                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                        'fontSize': 11,
                        'bold': True
                    },
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat'
        }
    }
    
    requests = [profit_conditional_format, currency_format, header_format]
    
    worksheet.spreadsheet.batch_update({'requests': requests})

def apply_column_widths(worksheet):
    """Set optimal column widths"""
    sheet_id = worksheet.id
    
    column_widths = [
        {'startIndex': 0, 'endIndex': 1, 'width': 120},   # Service names
        {'startIndex': 1, 'endIndex': 2, 'width': 100},   # Values
        {'startIndex': 2, 'endIndex': 3, 'width': 100},   # Annual
        {'startIndex': 3, 'endIndex': 4, 'width': 60},    # Status
        {'startIndex': 4, 'endIndex': 5, 'width': 200},   # Description
    ]
    
    requests = []
    for col in column_widths:
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': col['startIndex'],
                    'endIndex': col['endIndex']
                },
                'properties': {
                    'pixelSize': col['width']
                },
                'fields': 'pixelSize'
            }
        })
    
    worksheet.spreadsheet.batch_update({'requests': requests})

def main():
    """Main execution for charts and formatting"""
    print("=" * 80)
    print("VLP DASHBOARD - CHARTS & FORMATTING")
    print("=" * 80)
    print()
    
    # Connect to Google Sheets
    print("📊 Connecting to Google Sheets...")
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    try:
        worksheet = spreadsheet.worksheet('VLP Revenue')
        print("✅ Found 'VLP Revenue' sheet")
    except:
        print("❌ 'VLP Revenue' sheet not found. Run vlp_dashboard_python.py first!")
        return
    
    print()
    
    # Apply formatting
    print("🎨 Applying advanced formatting...")
    apply_advanced_formatting(worksheet)
    print("✅ Conditional formatting applied")
    
    apply_column_widths(worksheet)
    print("✅ Column widths optimized")
    
    print()
    
    # Create charts
    print("📈 Creating charts...")
    
    print("   Creating profit trend chart...")
    create_profit_sparkline_chart(spreadsheet, worksheet)
    time.sleep(1)
    
    print("   Creating service breakdown pie chart...")
    create_service_breakdown_chart(spreadsheet, worksheet)
    time.sleep(1)
    
    print("   Creating DUoS band comparison chart...")
    create_duos_band_chart(spreadsheet, worksheet)
    
    print("✅ All charts created")
    print()
    
    print("=" * 80)
    print("✅ CHARTS & FORMATTING COMPLETE")
    print("=" * 80)
    print()
    print(f"🔗 View dashboard: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print()
    print("📊 Charts added:")
    print("   • 24-hour profit trend (line chart)")
    print("   • Service revenue breakdown (donut chart)")
    print("   • DUoS band profitability (column chart)")
    print()
    print("🎨 Formatting applied:")
    print("   • Color gradient on profit values")
    print("   • Currency formatting")
    print("   • Professional headers")
    print("   • Optimized column widths")
    print()

if __name__ == '__main__':
    main()
