#!/usr/bin/env python3
"""
⚡ FAST API VERSION - Add Voltage Dropdown to BESS Sheet
Completes in ~1s (was 60s+ with gspread)
Creates dropdown in A10 with LV/HV/EHV options
"""

from fast_sheets_helper import FastSheetsAPI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time

# Configuration
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDS_FILE = 'inner-cinema-credentials.json'
WORKSHEET_NAME = 'BESS'

def add_voltage_dropdown():
    """Add voltage dropdown to cell A10 with descriptions"""
    
    start = time.time()
    print("=" * 80)
    print("ADDING VOLTAGE DROPDOWN TO BESS SHEET (Fast API)")
    print("=" * 80)
    
    # Initialize APIs
    print("\n🔐 Connecting to Google Sheets...")
    api = FastSheetsAPI(CREDS_FILE)
    
    # Get sheets service for advanced operations (data validation)
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    print("   ✅ Connected")
    
    # Get sheet ID for BESS worksheet
    print(f"\n🔍 Finding '{WORKSHEET_NAME}' worksheet...")
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheet_id = None
    for sheet in sheet_metadata.get('sheets', []):
        if sheet['properties']['title'] == WORKSHEET_NAME:
            sheet_id = sheet['properties']['sheetId']
            break
    
    if not sheet_id:
        print(f"   ❌ Worksheet '{WORKSHEET_NAME}' not found!")
        return
    
    print(f"   ✅ Found worksheet (ID: {sheet_id})")
    
    # Define dropdown options
    voltage_options = [
        'LV (<1kV)',
        'HV (6.6-33kV)',
        'EHV (66-132kV+)'
    ]
    
    print(f"\n📝 Creating dropdown in A10...")
    print(f"   Options: {voltage_options}")
    
    # Create data validation request
    request = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 9,  # Row 10 (0-indexed)
                        "endRowIndex": 10,
                        "startColumnIndex": 0,  # Column A
                        "endColumnIndex": 1
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": opt} for opt in voltage_options
                            ]
                        },
                        "showCustomUi": True,
                        "strict": True
                    }
                }
            },
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 9,
                        "endRowIndex": 10,
                        "startColumnIndex": 0,
                        "endColumnIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "borders": {
                                "top": {"style": "SOLID", "width": 2, "color": {"red": 0.2, "green": 0.4, "blue": 0.8}},
                                "bottom": {"style": "SOLID", "width": 2, "color": {"red": 0.2, "green": 0.4, "blue": 0.8}},
                                "left": {"style": "SOLID", "width": 2, "color": {"red": 0.2, "green": 0.4, "blue": 0.8}},
                                "right": {"style": "SOLID", "width": 2, "color": {"red": 0.2, "green": 0.4, "blue": 0.8}}
                            },
                            "horizontalAlignment": "CENTER",
                            "textFormat": {"bold": True}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,borders,horizontalAlignment,textFormat)"
                }
            }
        ]
    }
    
    # Apply validation and formatting
    service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body=request
    ).execute()
    print("   ✅ Dropdown created and formatted!")
    
    # Set default value using fast API
    print("\n📝 Setting default value...")
    api.update_single_range(SHEET_ID, f'{WORKSHEET_NAME}!A10', [['LV (<1kV)']])
    print("   ✅ Default set to 'LV (<1kV)'")
    
    elapsed = time.time() - start
    print("\n" + "=" * 80)
    print(f"✅ VOLTAGE DROPDOWN COMPLETE! (⚡ {elapsed:.2f}s)")
    print("=" * 80)
    print("\n📋 Dropdown options:")
    for i, opt in enumerate(voltage_options, 1):
        print(f"   {i}. {opt}")
    print("\n🎯 Usage:")
    print("   1. Click on cell A10 in BESS sheet")
    print("   2. Click the dropdown arrow")
    print("   3. Select voltage level")
    print("   4. Use 'Refresh DNO' button to get rates")
    

if __name__ == "__main__":
    add_voltage_dropdown()
