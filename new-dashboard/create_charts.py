#!/usr/bin/env python3
"""
Create Charts for Dashboard V2
Uses Google Sheets API to programmatically insert charts
"""

import gspread
from google.oauth2 import service_account
import time

# Configuration
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
SA_FILE = '../inner-cinema-credentials.json'

print("=" * 80)
print("📊 CREATING CHARTS FOR DASHBOARD V2")
print("=" * 80)
print()

# Authenticate
creds = service_account.Credentials.from_service_account_file(
    SA_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

print("✅ Connected to spreadsheet")
print()

# Chart 1: System Prices (Line Chart)
print("📈 Creating Price Chart...")
try:
    chart_prices_sheet = spreadsheet.worksheet('Chart_Prices')
    daily_data_sheet = spreadsheet.worksheet('Daily_Chart_Data')
    
    # Chart configuration
    chart_spec = {
        "title": "Market Prices (£/MWh)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {
                    "position": "BOTTOM_AXIS",
                    "title": "Settlement Period"
                },
                {
                    "position": "LEFT_AXIS",
                    "title": "Price (£/MWh)"
                }
            ],
            "domains": [
                {
                    "domain": {
                        "sourceRange": {
                            "sources": [
                                {
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
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
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
                                    "startColumnIndex": 2,
                                    "endColumnIndex": 3
                                }
                            ]
                        }
                    },
                    "targetAxis": "LEFT_AXIS"
                }
            ]
        }
    }
    
    # Add chart to Chart_Prices sheet
    request = {
        "addChart": {
            "chart": {
                "spec": chart_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": chart_prices_sheet.id,
                            "rowIndex": 0,
                            "columnIndex": 0
                        }
                    }
                }
            }
        }
    }
    
    spreadsheet.batch_update({"requests": [request]})
    print("   ✅ Price Chart created")
    time.sleep(1)
    
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Chart 2: Demand vs Generation
print("📈 Creating Demand/Generation Chart...")
try:
    chart_demand_sheet = spreadsheet.worksheet('Chart_Demand_Gen')
    
    chart_spec = {
        "title": "Demand vs Generation (MW)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {
                    "position": "BOTTOM_AXIS",
                    "title": "Settlement Period"
                },
                {
                    "position": "LEFT_AXIS",
                    "title": "MW"
                }
            ],
            "domains": [
                {
                    "domain": {
                        "sourceRange": {
                            "sources": [
                                {
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
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
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
                                    "startColumnIndex": 3,
                                    "endColumnIndex": 4
                                }
                            ]
                        }
                    },
                    "targetAxis": "LEFT_AXIS"
                },
                {
                    "series": {
                        "sourceRange": {
                            "sources": [
                                {
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
                                    "startColumnIndex": 4,
                                    "endColumnIndex": 5
                                }
                            ]
                        }
                    },
                    "targetAxis": "LEFT_AXIS"
                }
            ]
        }
    }
    
    request = {
        "addChart": {
            "chart": {
                "spec": chart_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": chart_demand_sheet.id,
                            "rowIndex": 0,
                            "columnIndex": 0
                        }
                    }
                }
            }
        }
    }
    
    spreadsheet.batch_update({"requests": [request]})
    print("   ✅ Demand/Generation Chart created")
    time.sleep(1)
    
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Chart 3: Interconnector Imports
print("📈 Creating Interconnector Chart...")
try:
    chart_ic_sheet = spreadsheet.worksheet('Chart_IC_Import')
    
    chart_spec = {
        "title": "Interconnector Imports (MW)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {
                    "position": "BOTTOM_AXIS",
                    "title": "Settlement Period"
                },
                {
                    "position": "LEFT_AXIS",
                    "title": "Import (MW)"
                }
            ],
            "domains": [
                {
                    "domain": {
                        "sourceRange": {
                            "sources": [
                                {
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
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
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
                                    "startColumnIndex": 5,
                                    "endColumnIndex": 6
                                }
                            ]
                        }
                    },
                    "targetAxis": "LEFT_AXIS"
                }
            ]
        }
    }
    
    request = {
        "addChart": {
            "chart": {
                "spec": chart_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": chart_ic_sheet.id,
                            "rowIndex": 0,
                            "columnIndex": 0
                        }
                    }
                }
            }
        }
    }
    
    spreadsheet.batch_update({"requests": [request]})
    print("   ✅ Interconnector Chart created")
    time.sleep(1)
    
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Chart 4: Frequency
print("📈 Creating Frequency Chart...")
try:
    chart_freq_sheet = spreadsheet.worksheet('Chart_Frequency')
    
    chart_spec = {
        "title": "System Frequency (Hz)",
        "basicChart": {
            "chartType": "LINE",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {
                    "position": "BOTTOM_AXIS",
                    "title": "Settlement Period"
                },
                {
                    "position": "LEFT_AXIS",
                    "title": "Frequency (Hz)"
                }
            ],
            "domains": [
                {
                    "domain": {
                        "sourceRange": {
                            "sources": [
                                {
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
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
                                    "sheetId": daily_data_sheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": 50,
                                    "startColumnIndex": 6,
                                    "endColumnIndex": 7
                                }
                            ]
                        }
                    },
                    "targetAxis": "LEFT_AXIS"
                }
            ]
        }
    }
    
    request = {
        "addChart": {
            "chart": {
                "spec": chart_spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": chart_freq_sheet.id,
                            "rowIndex": 0,
                            "columnIndex": 0
                        }
                    }
                }
            }
        }
    }
    
    spreadsheet.batch_update({"requests": [request]})
    print("   ✅ Frequency Chart created")
    
except Exception as e:
    print(f"   ❌ Failed: {e}")

print()
print("=" * 80)
print("✅ CHART CREATION COMPLETE")
print("=" * 80)
print()
print("View charts: https://docs.google.com/spreadsheets/d/" + SPREADSHEET_ID)
