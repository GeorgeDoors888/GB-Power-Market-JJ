#!/usr/bin/env python3
"""
Fix date pickers for Live Outages sheet
"""

import sys
from google.oauth2 import service_account
import gspread
from datetime import datetime, timedelta

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'

def main():
    print("🔄 Adding date pickers to Live Outages sheet...")
    
    creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet('Live Outages')
    
    # Clear E7 and G7 (remove BM Units that shouldn't be there)
    sheet.update('E7', [['']])
    sheet.update('G7', [['']])
    
    print("✅ Cleared E7 and G7")
    
    # Add date validation for E7 (Start Date)
    sheet.spreadsheet.batch_update({
        'requests': [
            {
                'setDataValidation': {
                    'range': {
                        'sheetId': sheet.id,
                        'startRowIndex': 6,  # Row 7
                        'endRowIndex': 7,
                        'startColumnIndex': 4,  # Column E
                        'endColumnIndex': 5
                    },
                    'rule': {
                        'condition': {
                            'type': 'DATE_IS_VALID'
                        },
                        'showCustomUi': True,
                        'strict': False
                    }
                }
            },
            {
                'setDataValidation': {
                    'range': {
                        'sheetId': sheet.id,
                        'startRowIndex': 6,  # Row 7
                        'endRowIndex': 7,
                        'startColumnIndex': 6,  # Column G
                        'endColumnIndex': 7
                    },
                    'rule': {
                        'condition': {
                            'type': 'DATE_IS_VALID'
                        },
                        'showCustomUi': True,
                        'strict': False
                    }
                }
            }
        ]
    })
    
    print("✅ Added date pickers to E7 (Start Date) and G7 (End Date)")
    
    # Format E7 and G7 as date cells
    sheet.format('E7:G7', {
        'numberFormat': {
            'type': 'DATE',
            'pattern': 'yyyy-mm-dd'
        },
        'horizontalAlignment': 'LEFT'
    })
    
    print("✅ Formatted E7 and G7 as date cells")
    
    # Set default date range (last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    sheet.update([[start_date.strftime('%Y-%m-%d')]], 'E7')
    sheet.update([[end_date.strftime('%Y-%m-%d')]], 'G7')
    
    print(f"✅ Set default date range: {start_date} to {end_date}")
    
    print("=" * 80)
    print("✅ DATE PICKERS ADDED SUCCESSFULLY")
    print("=" * 80)
    print("\n📝 Now users can:")
    print("   1. Click E7 to select Start Date (date picker will appear)")
    print("   2. Click G7 to select End Date (date picker will appear)")
    print("   3. Dates are formatted as YYYY-MM-DD")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
