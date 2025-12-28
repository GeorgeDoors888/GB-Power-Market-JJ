#!/usr/bin/env python3
"""Add 3 dropdowns to Analysis sheet"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'

def main():
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)

    # Get Analysis sheet ID
    metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    analysis_sheet_id = None
    for sheet in metadata.get('sheets', []):
        if sheet['properties']['title'] == 'Analysis':
            analysis_sheet_id = sheet['properties']['sheetId']
            break

    if not analysis_sheet_id:
        print("❌ Analysis sheet not found")
        return

    print(f"✅ Found Analysis sheet (ID: {analysis_sheet_id})")

    # Generate date list (last 90 days + next 7 days for future dates)
    dates = []
    for i in range(90, -8, -1):
        date = datetime.now() - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))

    print(f"📅 Generated {len(dates)} dates from {dates[0]} to {dates[-1]}")

    # Build data validation requests
    requests = [
        # Dropdown 1: Time Period (B1)
        {
            'setDataValidation': {
                'range': {
                    'sheetId': analysis_sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 1,  # Column B
                    'endColumnIndex': 2
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_LIST',
                        'values': [
                            {'userEnteredValue': 'LIVE DATA'},
                            {'userEnteredValue': 'TODAY'},
                            {'userEnteredValue': 'WEEK'},
                            {'userEnteredValue': 'MONTH'},
                            {'userEnteredValue': 'YEAR'},
                            {'userEnteredValue': 'ALL'}
                        ]
                    },
                    'showCustomUi': True,
                    'strict': True
                }
            }
        },
        # Dropdown 2: From Date (D1)
        {
            'setDataValidation': {
                'range': {
                    'sheetId': analysis_sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 3,  # Column D
                    'endColumnIndex': 4
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_LIST',
                        'values': [{'userEnteredValue': date} for date in dates]
                    },
                    'showCustomUi': True,
                    'strict': True
                }
            }
        },
        # Dropdown 3: To Date (F1)
        {
            'setDataValidation': {
                'range': {
                    'sheetId': analysis_sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 5,  # Column F
                    'endColumnIndex': 6
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_LIST',
                        'values': [{'userEnteredValue': date} for date in dates]
                    },
                    'showCustomUi': True,
                    'strict': True
                }
            }
        }
    ]

    # Apply formatting to dropdown row
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': analysis_sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 1,
                'startColumnIndex': 0,
                'endColumnIndex': 6
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    'horizontalAlignment': 'CENTER',
                    'verticalAlignment': 'MIDDLE'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
        }
    })

    # Execute batch update
    print("📝 Applying data validation rules...")
    body = {'requests': requests}
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()

    print(f"\n✅ Successfully created 3 dropdowns in Analysis sheet!")
    print(f"\n╔════════════════════════════════════════════════════════════╗")
    print(f"║  DROPDOWN 1 (B1): Time Period                              ║")
    print(f"║  Options: LIVE DATA, TODAY, WEEK, MONTH, YEAR, ALL         ║")
    print(f"╠════════════════════════════════════════════════════════════╣")
    print(f"║  DROPDOWN 2 (D1): From Date                                ║")
    print(f"║  Options: {len(dates)} dates ({dates[0]} to {dates[-1]})  ║")
    print(f"╠════════════════════════════════════════════════════════════╣")
    print(f"║  DROPDOWN 3 (F1): To Date                                  ║")
    print(f"║  Options: {len(dates)} dates ({dates[0]} to {dates[-1]})  ║")
    print(f"╚════════════════════════════════════════════════════════════╝")
    print(f"\n🎨 Applied blue header formatting to dropdown row")

if __name__ == '__main__':
    main()
