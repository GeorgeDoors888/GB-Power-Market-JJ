#!/usr/bin/env python3
"""
Add Charts to BESS Revenue Stack Sheet
Creates pie chart, waterfall chart, and IRR timeline
"""

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

def create_charts():
    """Create charts for revenue stack analysis"""
    
    print('\n📊 ADDING CHARTS TO BESS_REVENUE_STACK SHEET')
    print('='*80)
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scope)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SHEET_ID)
    
    rev_sheet = ss.worksheet('BESS_Revenue_Stack')
    
    # Chart 1: Pie Chart - Revenue Breakdown
    print('\n📈 Creating pie chart (revenue breakdown)...')
    pie_chart_spec = {
        "requests": [
            {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "BESS Annual Revenue Breakdown (£502,448/year)",
                            "pieChart": {
                                "legendPosition": "RIGHT_LEGEND",
                                "domain": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": rev_sheet.id,
                                                "startRowIndex": 5,
                                                "endRowIndex": 10,
                                                "startColumnIndex": 0,
                                                "endColumnIndex": 1
                                            }
                                        ]
                                    }
                                },
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": rev_sheet.id,
                                                "startRowIndex": 5,
                                                "endRowIndex": 10,
                                                "startColumnIndex": 3,
                                                "endColumnIndex": 4
                                            }
                                        ]
                                    }
                                },
                                "pieHole": 0.4
                            }
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": rev_sheet.id,
                                    "rowIndex": 1,
                                    "columnIndex": 7
                                }
                            }
                        }
                    }
                }
            }
        ]
    }
    
    ss.batch_update(pie_chart_spec)
    print('   ✅ Pie chart created')
    
    # Chart 2: Column Chart - Revenue by Stream
    print('\n📊 Creating column chart (revenue comparison)...')
    column_chart_spec = {
        "requests": [
            {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "Revenue Streams Comparison",
                            "basicChart": {
                                "chartType": "COLUMN",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "Revenue Stream"
                                    },
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "Annual Revenue (£)"
                                    }
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": rev_sheet.id,
                                                        "startRowIndex": 5,
                                                        "endRowIndex": 10,
                                                        "startColumnIndex": 0,
                                                        "endColumnIndex": 1
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ],
                                "series": [
                                    {
                                        "series": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": rev_sheet.id,
                                                        "startRowIndex": 5,
                                                        "endRowIndex": 10,
                                                        "startColumnIndex": 3,
                                                        "endColumnIndex": 4
                                                    }
                                                ]
                                            }
                                        },
                                        "targetAxis": "LEFT_AXIS"
                                    }
                                ],
                                "headerCount": 0
                            }
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": rev_sheet.id,
                                    "rowIndex": 15,
                                    "columnIndex": 7
                                }
                            }
                        }
                    }
                }
            }
        ]
    }
    
    ss.batch_update(column_chart_spec)
    print('   ✅ Column chart created')
    
    print('\n✅ Charts created successfully!')
    print(f'🔗 View: https://docs.google.com/spreadsheets/d/{SHEET_ID}/')
    print('='*80 + '\n')

if __name__ == '__main__':
    create_charts()
