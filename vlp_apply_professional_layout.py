#!/usr/bin/env python3
"""
VLP Dashboard Layout Designer
Creates professional layout matching design specifications
"""

import gspread
from google.oauth2.service_account import Credentials
import time

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Professional color scheme
COLORS = {
    'header_dark': {'red': 0.06, 'green': 0.25, 'blue': 0.42},  # Dark blue #0F405A
    'header_light': {'red': 0.0, 'green': 0.4, 'blue': 0.6},    # Blue #006699
    'accent_orange': {'red': 1.0, 'green': 0.6, 'blue': 0.0},   # Orange #FF9900
    'green_high': {'red': 0.0, 'green': 0.6, 'blue': 0.0},      # Green #009900
    'green_light': {'red': 0.85, 'green': 0.95, 'blue': 0.85},  # Light green
    'red_high': {'red': 0.8, 'green': 0.0, 'blue': 0.0},        # Red #CC0000
    'red_light': {'red': 0.95, 'green': 0.85, 'blue': 0.85},    # Light red
    'yellow': {'red': 1.0, 'green': 0.8, 'blue': 0.0},          # Yellow
    'white': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
    'light_gray': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
    'border_gray': {'red': 0.85, 'green': 0.85, 'blue': 0.85}
}

def get_sheets_client():
    """Initialize Google Sheets client"""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def apply_professional_layout(worksheet):
    """Apply professional design layout"""
    sheet_id = worksheet.id
    
    requests = []
    
    # 1. TICKER SECTION (A1:M3)
    # Merge A1:M1 for ticker
    requests.append({
        'mergeCells': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 1,
                'startColumnIndex': 0,
                'endColumnIndex': 13
            },
            'mergeType': 'MERGE_ALL'
        }
    })
    
    # Format ticker - Large dark blue header
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 1,
                'startColumnIndex': 0,
                'endColumnIndex': 13
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': COLORS['header_dark'],
                    'textFormat': {
                        'foregroundColor': COLORS['white'],
                        'fontSize': 18,
                        'bold': True
                    },
                    'horizontalAlignment': 'CENTER',
                    'verticalAlignment': 'MIDDLE',
                    'padding': {'top': 10, 'bottom': 10}
                }
            },
            'fields': 'userEnteredFormat'
        }
    })
    
    # Row height for ticker
    requests.append({
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': 0,
                'endIndex': 1
            },
            'properties': {'pixelSize': 60},
            'fields': 'pixelSize'
        }
    })
    
    # 2. TIMESTAMP (A2:M2)
    requests.append({
        'mergeCells': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'endRowIndex': 2,
                'startColumnIndex': 0,
                'endColumnIndex': 13
            },
            'mergeType': 'MERGE_ALL'
        }
    })
    
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'endRowIndex': 2,
                'startColumnIndex': 0,
                'endColumnIndex': 13
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': COLORS['light_gray'],
                    'textFormat': {
                        'foregroundColor': COLORS['header_dark'],
                        'fontSize': 10,
                        'italic': True
                    },
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat'
        }
    })
    
    # 3. SPACER ROW (Row 3)
    requests.append({
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': 2,
                'endIndex': 3
            },
            'properties': {'pixelSize': 20},
            'fields': 'pixelSize'
        }
    })
    
    # 4. SECTION HEADER: CURRENT PERIOD (A4:F4)
    requests.append({
        'mergeCells': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 3,
                'endRowIndex': 4,
                'startColumnIndex': 0,
                'endColumnIndex': 6
            },
            'mergeType': 'MERGE_ALL'
        }
    })
    
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 3,
                'endRowIndex': 4,
                'startColumnIndex': 0,
                'endColumnIndex': 6
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': COLORS['header_light'],
                    'textFormat': {
                        'foregroundColor': COLORS['white'],
                        'fontSize': 14,
                        'bold': True
                    },
                    'horizontalAlignment': 'LEFT',
                    'padding': {'left': 10}
                }
            },
            'fields': 'userEnteredFormat'
        }
    })
    
    # 5. CURRENT PERIOD DATA (A5:B14) - Headers
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 4,
                'endRowIndex': 5,
                'startColumnIndex': 0,
                'endColumnIndex': 2
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': COLORS['light_gray'],
                    'textFormat': {
                        'bold': True,
                        'fontSize': 11
                    },
                    'borders': {
                        'bottom': {'style': 'SOLID', 'width': 2, 'color': COLORS['header_light']}
                    }
                }
            },
            'fields': 'userEnteredFormat'
        }
    })
    
    # Alternate row colors for data (A6:B14)
    for i in range(5, 14, 2):
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': i,
                    'endRowIndex': i + 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 2
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': COLORS['light_gray']
                    }
                },
                'fields': 'userEnteredFormat.backgroundColor'
            }
        })
    
    # 6. SPACER ROW (Row 15)
    requests.append({
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': 14,
                'endIndex': 15
            },
            'properties': {'pixelSize': 20},
            'fields': 'pixelSize'
        }
    })
    
    # 7. SECTION HEADER: SERVICE BREAKDOWN (A16:F16)
    requests.append({
        'mergeCells': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 15,
                'endRowIndex': 16,
                'startColumnIndex': 0,
                'endColumnIndex': 6
            },
            'mergeType': 'MERGE_ALL'
        }
    })
    
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 15,
                'endRowIndex': 16,
                'startColumnIndex': 0,
                'endColumnIndex': 6
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': COLORS['header_light'],
                    'textFormat': {
                        'foregroundColor': COLORS['white'],
                        'fontSize': 14,
                        'bold': True
                    },
                    'horizontalAlignment': 'LEFT',
                    'padding': {'left': 10}
                }
            },
            'fields': 'userEnteredFormat'
        }
    })
    
    # 8. SERVICE TABLE HEADERS (A17:E17)
    requests.append({
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
                    'backgroundColor': COLORS['header_dark'],
                    'textFormat': {
                        'foregroundColor': COLORS['white'],
                        'fontSize': 11,
                        'bold': True
                    },
                    'horizontalAlignment': 'CENTER',
                    'borders': {
                        'bottom': {'style': 'SOLID', 'width': 2, 'color': COLORS['white']}
                    }
                }
            },
            'fields': 'userEnteredFormat'
        }
    })
    
    # 9. TOTAL ROW (A26:E26) - Highlight
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 25,
                'endRowIndex': 26,
                'startColumnIndex': 0,
                'endColumnIndex': 5
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': COLORS['accent_orange'],
                    'textFormat': {
                        'foregroundColor': COLORS['white'],
                        'fontSize': 12,
                        'bold': True
                    },
                    'borders': {
                        'top': {'style': 'SOLID', 'width': 3, 'color': COLORS['header_dark']},
                        'bottom': {'style': 'SOLID', 'width': 3, 'color': COLORS['header_dark']}
                    }
                }
            },
            'fields': 'userEnteredFormat'
        }
    })
    
    # 10. PROFIT BY BAND SECTION (K4:N4)
    requests.append({
        'mergeCells': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 3,
                'endRowIndex': 4,
                'startColumnIndex': 10,
                'endColumnIndex': 14
            },
            'mergeType': 'MERGE_ALL'
        }
    })
    
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 3,
                'endRowIndex': 4,
                'startColumnIndex': 10,
                'endColumnIndex': 14
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': COLORS['header_light'],
                    'textFormat': {
                        'foregroundColor': COLORS['white'],
                        'fontSize': 14,
                        'bold': True
                    },
                    'horizontalAlignment': 'LEFT',
                    'padding': {'left': 10}
                }
            },
            'fields': 'userEnteredFormat'
        }
    })
    
    # 11. COLUMN WIDTHS
    column_widths = [
        (0, 1, 150),    # A - Service/Metric names
        (1, 2, 110),    # B - Values
        (2, 3, 110),    # C - Annual
        (3, 4, 70),     # D - Status
        (4, 5, 250),    # E - Description
        (10, 11, 100),  # K - Band
        (11, 12, 80),   # L - Periods
        (12, 13, 100),  # M - Avg Profit
        (13, 14, 100)   # N - Total
    ]
    
    for start, end, width in column_widths:
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': start,
                    'endIndex': end
                },
                'properties': {'pixelSize': width},
                'fields': 'pixelSize'
            }
        })
    
    # 12. FREEZE TOP 4 ROWS
    requests.append({
        'updateSheetProperties': {
            'properties': {
                'sheetId': sheet_id,
                'gridProperties': {
                    'frozenRowCount': 4,
                    'frozenColumnCount': 0
                }
            },
            'fields': 'gridProperties.frozenRowCount,gridProperties.frozenColumnCount'
        }
    })
    
    # Execute all formatting
    if requests:
        worksheet.spreadsheet.batch_update({'requests': requests})
    
    print(f"✅ Applied {len(requests)} formatting rules")

def add_section_headers(worksheet):
    """Add proper section header text"""
    updates = [
        ('A4', [['📊 CURRENT PERIOD DETAILS']]),
        ('A16', [['💰 REVENUE SERVICES BREAKDOWN']]),
        ('K4', [['🎨 PROFIT BY DUOS BAND (7 Days)']]),
        ('A29', [['📈 STACKING SCENARIOS']])
    ]
    
    for cell, value in updates:
        worksheet.update(values=value, range_name=cell)
    
    print("✅ Added section headers")

def main():
    """Main execution"""
    print("=" * 80)
    print("VLP DASHBOARD PROFESSIONAL LAYOUT")
    print("=" * 80)
    print()
    
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    try:
        worksheet = spreadsheet.worksheet('VLP Revenue')
        print(f"✅ Found sheet: VLP Revenue (ID: {worksheet.id})")
        print()
        
        print("🎨 Applying professional layout...")
        apply_professional_layout(worksheet)
        time.sleep(2)
        
        print("📝 Adding section headers...")
        add_section_headers(worksheet)
        
        print()
        print("=" * 80)
        print("✅ PROFESSIONAL LAYOUT COMPLETE")
        print("=" * 80)
        print()
        print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
