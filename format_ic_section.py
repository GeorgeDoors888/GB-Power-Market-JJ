#!/usr/bin/env python3
"""
Format Interconnector Section for Better Sparkline Visibility
- Increase row heights for rows 13-22
- Increase column H width (Flow Trend sparklines)
- Makes sparkline bars much more visible
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'

def format_interconnector_section():
    """Format the interconnector section for better visibility"""
    print("=" * 80)
    print("📐 FORMATTING INTERCONNECTOR SECTION")
    print("=" * 80)
    print()
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    # Get sheet ID (needed for batch update)
    sheet_id = sheet.id
    
    print("✍️  Applying formatting...")
    
    # Prepare batch update requests
    requests = []
    
    # 1. Increase row heights for interconnector rows (13-22)
    requests.append({
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': 12,  # Row 13 (0-indexed)
                'endIndex': 22     # Row 22 (exclusive)
            },
            'properties': {
                'pixelSize': 40  # Increased from default ~21 to 40
            },
            'fields': 'pixelSize'
        }
    })
    
    # 2. Increase column H width (Flow Trend sparklines)
    requests.append({
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': 7,  # Column H (0-indexed, H=7)
                'endIndex': 8     # Just column H (exclusive)
            },
            'properties': {
                'pixelSize': 150  # Increased from default ~100 to 150
            },
            'fields': 'pixelSize'
        }
    })
    
    # 3. Center align column H content
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 12,  # Row 13
                'endRowIndex': 22,    # Row 22
                'startColumnIndex': 7,  # Column H
                'endColumnIndex': 8
            },
            'cell': {
                'userEnteredFormat': {
                    'horizontalAlignment': 'CENTER',
                    'verticalAlignment': 'MIDDLE'
                }
            },
            'fields': 'userEnteredFormat(horizontalAlignment,verticalAlignment)'
        }
    })
    
    # Execute batch update
    body = {'requests': requests}
    spreadsheet.batch_update(body)
    
    print(f"   ✅ Increased row heights: Rows 13-22 = 40px (was ~21px)")
    print(f"   ✅ Increased column width: Column H = 150px (was ~100px)")
    print(f"   ✅ Aligned sparklines: Center/Middle")
    
    print()
    print("=" * 80)
    print("✅ FORMATTING COMPLETE")
    print("=" * 80)
    print()
    print("Sparkline bars should now be MUCH more visible!")
    print("  • Row height: ~2x larger")
    print("  • Column width: ~1.5x wider")
    print("  • Cell area for sparklines: ~3x bigger")
    print()
    print(f"View: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

if __name__ == '__main__':
    format_interconnector_section()
