#!/usr/bin/env python3
"""
add_dashboard_interactivity.py
------------------------------
Adds interactive elements to the V3 Dashboard:
- Date range dropdown in cell B3.
"""

import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION ---
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
DASHBOARD_SHEET_NAME = 'Dashboard'

def get_gspread_client():
    """Authorize and return gspread client."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    return gspread.authorize(creds)

def add_date_range_dropdown(sheet):
    """Adds a data validation dropdown for date ranges to cell B3."""
    print("   1. Adding date range dropdown to cell B3...")
    try:
        # Define the validation rule
        body = {
            'requests': [{
                'setDataValidation': {
                    'range': {
                        'sheetId': sheet.id,
                        'startRowIndex': 2,  # B3 is in row 3 (0-indexed)
                        'endRowIndex': 3,
                        'startColumnIndex': 1, # B is column 2 (0-indexed)
                        'endColumnIndex': 2,
                    },
                    'rule': {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": "Last 24 Hours"},
                                {"userEnteredValue": "Last 7 Days"},
                                {"userEnteredValue": "Last 30 Days"},
                                {"userEnteredValue": "Last 6 Months"},
                                {"userEnteredValue": "Last 1 Year"}
                            ]
                        },
                        "inputMessage": "Select a time range for the chart.",
                        "strict": True,
                        "showCustomUi": True
                    }
                }
            }]
        }
        
        # Set the validation rule for cell B3
        sheet.spreadsheet.batch_update(body)
        
        # Set a default value
        sheet.update('B3', [['Last 24 Hours']])
        
        print("   ✅ Date range dropdown added successfully.")
    except Exception as e:
        print(f"   ❌ Error adding dropdown: {e}")

def main():
    print("--- Adding Dashboard Interactivity ---")
    try:
        gspread_client = get_gspread_client()
        spreadsheet = gspread_client.open_by_key(SPREADSHEET_ID)
        dashboard_sheet = spreadsheet.worksheet(DASHBOARD_SHEET_NAME)
        
        add_date_range_dropdown(dashboard_sheet)
        
        print("--- ✅ Interactivity features added successfully! ---")
        print(f"\n🔗 View your updated dashboard: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard_sheet.id}")

    except Exception as e:
        print(f"\n❌ A critical error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
