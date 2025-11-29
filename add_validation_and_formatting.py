#!/usr/bin/env python3
"""
add_validation_and_formatting.py
---------------------------------
Add data validation (dropdowns) and conditional formatting to Dashboard V2
using Google Sheets API directly.

Usage:
    python3 add_validation_and_formatting.py
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def get_sheets_service():
    """Get Google Sheets API service"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def get_sheet_id(service, sheet_name="Dashboard"):
    """Get the sheet ID (gid) for a given sheet name"""
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for sheet in sheet_metadata.get('sheets', []):
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return None

def add_data_validations(service, sheet_id):
    """Add dropdown validations to cells B3, D3, F3"""
    print("🔽 Adding dropdown validations...")
    
    requests = []
    
    # Time Range dropdown (B3)
    time_values = ["Real-Time (10 min)", "24 h", "48 h", "7 days", "30 days"]
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,  # Row 3 (0-indexed)
                "endRowIndex": 3,
                "startColumnIndex": 1,  # Column B
                "endColumnIndex": 2
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": val} for val in time_values]
                },
                "showCustomUi": True,
                "strict": True
            }
        }
    })
    
    # Region dropdown (D3) - All 14 DNO/GSP regions
    region_values = [
        "All GB",
        "Eastern Power Networks (EPN)",
        "South Eastern Power Networks (SPN)", 
        "London Power Networks (LPN)",
        "South Wales",
        "South West",
        "East Midlands",
        "West Midlands",
        "North Wales & Merseyside",
        "South Scotland",
        "North Scotland",
        "Northern",
        "Yorkshire",
        "North West",
        "Southern"
    ]
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 3,  # Column D
                "endColumnIndex": 4
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": val} for val in region_values]
                },
                "showCustomUi": True,
                "strict": True
            }
        }
    })
    
    # Alert filter dropdown (F3)
    alert_values = ["All", "Critical Only", "Wind Warning", "Outages", "Price Spike"]
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 5,  # Column F
                "endColumnIndex": 6
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": val} for val in alert_values]
                },
                "showCustomUi": True,
                "strict": True
            }
        }
    })
    
    # Start Date picker (H3)
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 7,  # Column H
                "endColumnIndex": 8
            },
            "rule": {
                "condition": {
                    "type": "DATE_IS_VALID"
                },
                "showCustomUi": True,
                "strict": False
            }
        }
    })
    
    # End Date picker (J3)
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 9,  # Column J
                "endColumnIndex": 10
            },
            "rule": {
                "condition": {
                    "type": "DATE_IS_VALID"
                },
                "showCustomUi": True,
                "strict": False
            }
        }
    })
    
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()
    
    print("   ✅ Added dropdowns to cells B3, D3, F3")
    print("   ✅ Added date pickers to cells H3, J3")

def add_conditional_formatting(service, sheet_id):
    """Add conditional formatting rules"""
    print("🎨 Adding conditional formatting...")
    
    requests = []
    
    # Rule 1: Critical outages (capacity > 500 MW) - Red background
    # Applies to column B (capacity) in outages section (rows 32-42)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 31,  # Row 32
                    "endRowIndex": 43,    # Row 43
                    "startColumnIndex": 1,  # Column B
                    "endColumnIndex": 2
                }],
                "booleanRule": {
                    "condition": {
                        "type": "NUMBER_GREATER",
                        "values": [{"userEnteredValue": "500"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.90, "green": 0.22, "blue": 0.21},  # #E53935 - Warning Red
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                    }
                }
            },
            "index": 0
        }
    })
    
    # Rule 2: Generation data highlighting (optional - high generation)
    # Highlight generation values > 5000 MW in generation section
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 9,   # Row 10
                    "endRowIndex": 19,    # Row 19
                    "startColumnIndex": 1,  # Column B
                    "endColumnIndex": 2
                }],
                "booleanRule": {
                    "condition": {
                        "type": "NUMBER_GREATER",
                        "values": [{"userEnteredValue": "5000"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.26, "green": 0.63, "blue": 0.28},  # #43A047 - Positive Green
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                    }
                }
            },
            "index": 1
        }
    })
    
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()
    
    print("   ✅ Critical outages (>500 MW): Red background")
    print("   ✅ High generation (>5000 MW): Green background")

def main():
    """Main execution"""
    print("=" * 60)
    print("⚡ ADDING VALIDATION & CONDITIONAL FORMATTING")
    print("=" * 60)
    print(f"📊 Spreadsheet: {SPREADSHEET_ID}")
    print()
    
    try:
        # Connect to API
        service = get_sheets_service()
        print("✅ Connected to Google Sheets API")
        
        # Get sheet ID
        sheet_id = get_sheet_id(service, "Dashboard")
        if sheet_id is None:
            print("❌ Error: 'Dashboard' sheet not found")
            return
        
        print(f"✅ Found Dashboard sheet (ID: {sheet_id})")
        print()
        
        # Add validations
        add_data_validations(service, sheet_id)
        print()
        
        # Add conditional formatting
        add_conditional_formatting(service, sheet_id)
        print()
        
        print("=" * 60)
        print("✅ COMPLETE!")
        print("=" * 60)
        print()
        print("🌐 View dashboard:")
        print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
        print()
        print("📋 What was added:")
        print("   • B3: Time range dropdown (Real-Time, 24h, 48h, 7d, 30d)")
        print("   • D3: Region dropdown (All GB + 14 DNO/GSP regions)")
        print("   • F3: Alert filter dropdown (All, Critical, etc.)")
        print("   • H3: Start date picker (calendar)")
        print("   • J3: End date picker (calendar)")
        print("   • Conditional: Outages >500 MW highlighted bright red")
        print("   • Conditional: Generation >5000 MW highlighted bright green")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
