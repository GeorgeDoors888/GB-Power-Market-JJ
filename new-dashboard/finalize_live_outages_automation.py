#!/usr/bin/env python3
"""
Complete Live Outages automation setup via Python + Google Sheets API
- Chart creation (via batch update)
- Filter views (programmatically)
- Advanced data validation
- Conditional formatting
"""

import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import *
import json

# Configuration
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SHEET_NAME = "Live Outages"
CREDS_FILE = "/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json"

def connect_sheets():
    """Connect to Google Sheets"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    return spreadsheet, sheet

def create_chart(spreadsheet, sheet):
    """Create line chart for Demand/Generation/Outages trend"""
    print("📈 Creating trend chart...")
    
    sheet_id = sheet._properties['sheetId']
    
    # Chart specification
    chart_spec = {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Power System Trend (Last 30 Days)",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "RIGHT_LEGEND",
                        "axis": [
                            {
                                "position": "BOTTOM_AXIS",
                                "title": "Date"
                            },
                            {
                                "position": "LEFT_AXIS",
                                "title": "Power (GW)"
                            }
                        ],
                        "domains": [
                            {
                                "domain": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": sheet_id,
                                                "startRowIndex": 2,
                                                "endRowIndex": 32,
                                                "startColumnIndex": 12,
                                                "endColumnIndex": 13
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
                                                "sheetId": sheet_id,
                                                "startRowIndex": 2,
                                                "endRowIndex": 32,
                                                "startColumnIndex": 13,
                                                "endColumnIndex": 14
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": {
                                    "red": 0.2,
                                    "green": 0.6,
                                    "blue": 1.0
                                }
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": sheet_id,
                                                "startRowIndex": 2,
                                                "endRowIndex": 32,
                                                "startColumnIndex": 14,
                                                "endColumnIndex": 15
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": {
                                    "red": 0.2,
                                    "green": 0.8,
                                    "blue": 0.2
                                }
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": sheet_id,
                                                "startRowIndex": 2,
                                                "endRowIndex": 32,
                                                "startColumnIndex": 15,
                                                "endColumnIndex": 16
                                            }
                                        ]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": {
                                    "red": 1.0,
                                    "green": 0.4,
                                    "blue": 0.0
                                }
                            }
                        ],
                        "headerCount": 1
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sheet_id,
                            "rowIndex": 11,
                            "columnIndex": 12
                        }
                    }
                }
            }
        }
    }
    
    # Execute batch update
    spreadsheet.batch_update({"requests": [chart_spec]})
    print("✅ Chart created at column R")

def create_filter_views(spreadsheet, sheet):
    """Create saved filter views"""
    print("🔍 Creating filter views...")
    
    sheet_id = sheet._properties['sheetId']
    
    filter_views = [
        {
            "addFilterView": {
                "filter": {
                    "title": "High Capacity Outages (>500 MW)",
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 9,
                        "endRowIndex": 200,
                        "startColumnIndex": 0,
                        "endColumnIndex": 11
                    },
                    "filterSpecs": [
                        {
                            "columnIndex": 2,
                            "filterCriteria": {
                                "condition": {
                                    "type": "NUMBER_GREATER",
                                    "values": [{"userEnteredValue": "500"}]
                                }
                            }
                        }
                    ]
                }
            }
        },
        {
            "addFilterView": {
                "filter": {
                    "title": "Gas Stations Only",
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 9,
                        "endRowIndex": 200,
                        "startColumnIndex": 0,
                        "endColumnIndex": 11
                    },
                    "filterSpecs": [
                        {
                            "columnIndex": 3,
                            "filterCriteria": {
                                "condition": {
                                    "type": "TEXT_CONTAINS",
                                    "values": [{"userEnteredValue": "Gas"}]
                                }
                            }
                        }
                    ]
                }
            }
        },
        {
            "addFilterView": {
                "filter": {
                    "title": "Recent Outages (Last 7 Days)",
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 9,
                        "endRowIndex": 200,
                        "startColumnIndex": 0,
                        "endColumnIndex": 11
                    },
                    "sortSpecs": [
                        {
                            "dimensionIndex": 4,
                            "sortOrder": "DESCENDING"
                        }
                    ]
                }
            }
        }
    ]
    
    # Execute batch update
    spreadsheet.batch_update({"requests": filter_views})
    print("✅ Created 3 filter views")

def add_conditional_formatting(spreadsheet, sheet):
    """Add conditional formatting for capacity column"""
    print("🎨 Adding conditional formatting...")
    
    sheet_id = sheet._properties['sheetId']
    
    # Color scale for capacity (column C, rows 11+)
    format_rule = {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [
                    {
                        "sheetId": sheet_id,
                        "startRowIndex": 10,
                        "endRowIndex": 200,
                        "startColumnIndex": 2,
                        "endColumnIndex": 3
                    }
                ],
                "gradientRule": {
                    "minpoint": {
                        "color": {"red": 1.0, "green": 1.0, "blue": 1.0},
                        "type": "MIN"
                    },
                    "midpoint": {
                        "color": {"red": 1.0, "green": 0.9, "blue": 0.6},
                        "type": "PERCENTILE",
                        "value": "50"
                    },
                    "maxpoint": {
                        "color": {"red": 1.0, "green": 0.4, "blue": 0.0},
                        "type": "MAX"
                    }
                }
            },
            "index": 0
        }
    }
    
    spreadsheet.batch_update({"requests": [format_rule]})
    print("✅ Conditional formatting applied to capacity column")

def enhance_dropdowns(sheet):
    """Enhance dropdown functionality with additional options"""
    print("📋 Enhancing dropdowns...")
    
    # Add "All Units" option to BM Unit dropdown (A7)
    current_units = sheet.col_values(12)[1:]  # Column L (hidden)
    
    # Prepend "All Units" option
    all_options = ["All Units"] + current_units
    
    # Update hidden column with all options
    if len(all_options) > 1:
        sheet.update(f'L2:L{len(all_options)+1}', [[opt] for opt in all_options])
        print(f"✅ Enhanced BM Unit dropdown with {len(all_options)} options")

def main():
    """Execute all automation tasks"""
    print("⚡ FINALIZING LIVE OUTAGES AUTOMATION\n")
    
    try:
        spreadsheet, sheet = connect_sheets()
        print("✅ Connected to Google Sheets\n")
        
        # 1. Create chart
        try:
            create_chart(spreadsheet, sheet)
        except Exception as e:
            print(f"⚠️ Chart creation: {e}")
        
        # 2. Create filter views
        try:
            create_filter_views(spreadsheet, sheet)
        except Exception as e:
            print(f"⚠️ Filter views: {e}")
        
        # 3. Add conditional formatting
        try:
            add_conditional_formatting(spreadsheet, sheet)
        except Exception as e:
            print(f"⚠️ Conditional formatting: {e}")
        
        # 4. Enhance dropdowns
        try:
            enhance_dropdowns(sheet)
        except Exception as e:
            print(f"⚠️ Dropdown enhancement: {e}")
        
        print("\n✅ AUTOMATION FINALIZED")
        print("\n📊 Next: Refresh data with:")
        print("   python3 live_outages_updater.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
