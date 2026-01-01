#!/usr/bin/env python3
"""
Apply Traffic Light Conditional Formatting to Existing Wind Dashboard Data
Adds 🔴🟡🟢 visual alerts to rows A26-A82
"""

import logging
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def main():
    """Apply traffic light formatting to existing wind dashboard sections"""
    logger.info("🚦 Applying Traffic Light Formatting...")

    # Initialize Google Sheets API
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets'])
    service = build('sheets', 'v4', credentials=creds)

    # Get sheet ID
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_id = None
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == SHEET_NAME:
            sheet_id = sheet['properties']['sheetId']
            break

    if sheet_id is None:
        logger.error(f"Sheet '{SHEET_NAME}' not found")
        return

    logger.info(f"Found sheet ID: {sheet_id}")

    # Build formatting requests
    requests = []

    # 1. Wind Change Alerts (A26-A33) - Column G has the alert icons
    logger.info("Formatting wind change alerts (A26-A33)...")

    # Critical (60%+ change) - RED background
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{'sheetId': sheet_id, 'startRowIndex': 26, 'endRowIndex': 34, 'startColumnIndex': 3, 'endColumnIndex': 4}],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_GREATER_THAN_EQ',
                        'values': [{'userEnteredValue': '60'}]
                    },
                    'format': {
                        'backgroundColor': {'red': 0.957, 'green': 0.263, 'blue': 0.212},
                        'textFormat': {'bold': True}
                    }
                }
            },
            'index': 0
        }
    })

    # Warning (40-60% change) - ORANGE background
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{'sheetId': sheet_id, 'startRowIndex': 26, 'endRowIndex': 34, 'startColumnIndex': 3, 'endColumnIndex': 4}],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_BETWEEN',
                        'values': [
                            {'userEnteredValue': '40'},
                            {'userEnteredValue': '59'}
                        ]
                    },
                    'format': {
                        'backgroundColor': {'red': 1.0, 'green': 0.6, 'blue': 0.0},
                        'textFormat': {'bold': True}
                    }
                }
            },
            'index': 1
        }
    })

    # Stable (20-40% change) - YELLOW background
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{'sheetId': sheet_id, 'startRowIndex': 26, 'endRowIndex': 34, 'startColumnIndex': 3, 'endColumnIndex': 4}],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_BETWEEN',
                        'values': [
                            {'userEnteredValue': '20'},
                            {'userEnteredValue': '39'}
                        ]
                    },
                    'format': {
                        'backgroundColor': {'red': 1.0, 'green': 0.95, 'blue': 0.6},
                        'textFormat': {'bold': False}
                    }
                }
            },
            'index': 2
        }
    })

    # 2. Revenue Impact (A63-A72) - Severity column highlighting
    logger.info("Formatting revenue impact severity (A63-A72)...")

    # High severity - RED text
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{'sheetId': sheet_id, 'startRowIndex': 63, 'endRowIndex': 73, 'startColumnIndex': 5, 'endColumnIndex': 7}],
                'booleanRule': {
                    'condition': {
                        'type': 'TEXT_CONTAINS',
                        'values': [{'userEnteredValue': 'High'}]
                    },
                    'format': {
                        'textFormat': {'foregroundColor': {'red': 0.8, 'green': 0.0, 'blue': 0.0}, 'bold': True}
                    }
                }
            },
            'index': 3
        }
    })

    # Medium severity - ORANGE text
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{'sheetId': sheet_id, 'startRowIndex': 63, 'endRowIndex': 73, 'startColumnIndex': 5, 'endColumnIndex': 7}],
                'booleanRule': {
                    'condition': {
                        'type': 'TEXT_CONTAINS',
                        'values': [{'userEnteredValue': 'Medium'}]
                    },
                    'format': {
                        'textFormat': {'foregroundColor': {'red': 1.0, 'green': 0.5, 'blue': 0.0}, 'bold': True}
                    }
                }
            },
            'index': 4
        }
    })

    # 3. Hour-of-Day Accuracy (A73-A82) - Error % color scale
    logger.info("Formatting hour-of-day accuracy (A73-A82)...")

    # High error (>50%) - RED background
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{'sheetId': sheet_id, 'startRowIndex': 75, 'endRowIndex': 83, 'startColumnIndex': 2, 'endColumnIndex': 3}],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_GREATER_THAN',
                        'values': [{'userEnteredValue': '50'}]
                    },
                    'format': {
                        'backgroundColor': {'red': 0.957, 'green': 0.263, 'blue': 0.212},
                        'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True}
                    }
                }
            },
            'index': 5
        }
    })

    # Moderate error (10-50%) - YELLOW background
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{'sheetId': sheet_id, 'startRowIndex': 75, 'endRowIndex': 83, 'startColumnIndex': 2, 'endColumnIndex': 3}],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_BETWEEN',
                        'values': [
                            {'userEnteredValue': '10'},
                            {'userEnteredValue': '50'}
                        ]
                    },
                    'format': {
                        'backgroundColor': {'red': 1.0, 'green': 0.95, 'blue': 0.6}
                    }
                }
            },
            'index': 6
        }
    })

    # Low error (<10%) - GREEN background
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{'sheetId': sheet_id, 'startRowIndex': 75, 'endRowIndex': 83, 'startColumnIndex': 2, 'endColumnIndex': 3}],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_LESS_THAN',
                        'values': [{'userEnteredValue': '10'}]
                    },
                    'format': {
                        'backgroundColor': {'red': 0.718, 'green': 0.867, 'blue': 0.643}
                    }
                }
            },
            'index': 7
        }
    })

    # 4. Add header styling for all sections
    logger.info("Formatting section headers...")

    # Wind alerts header (A26)
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 25,
                'endRowIndex': 26,
                'startColumnIndex': 0,
                'endColumnIndex': 7
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'textFormat': {
                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                        'bold': True,
                        'fontSize': 12
                    },
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    })

    # Revenue impact header (A63)
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 62,
                'endRowIndex': 63,
                'startColumnIndex': 0,
                'endColumnIndex': 7
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'textFormat': {
                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                        'bold': True,
                        'fontSize': 12
                    },
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    })

    # Hour-of-day header (A73)
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 72,
                'endRowIndex': 73,
                'startColumnIndex': 0,
                'endColumnIndex': 7
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'textFormat': {
                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                        'bold': True,
                        'fontSize': 12
                    },
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    })

    # Execute all formatting requests
    logger.info(f"Applying {len(requests)} formatting rules...")
    try:
        body = {'requests': requests}
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()

        logger.info(f"✅ Applied {len(response.get('replies', []))} formatting updates")

        print("\n" + "="*70)
        print("✅ TRAFFIC LIGHT FORMATTING COMPLETE")
        print("="*70)
        print(f"Sheet: {SHEET_NAME}")
        print(f"\nFormatted Sections:")
        print(f"  🔴🟡🟢 A26-A33: Wind Change Alerts")
        print(f"    • RED: 60%+ change (Critical)")
        print(f"    • ORANGE: 40-60% change (Warning)")
        print(f"    • YELLOW: 20-40% change (Caution)")
        print(f"")
        print(f"  💰 A63-A72: Revenue Impact")
        print(f"    • High severity: RED text")
        print(f"    • Medium severity: ORANGE text")
        print(f"")
        print(f"  📅 A73-A82: Hour-of-Day Accuracy")
        print(f"    • RED: >50% error")
        print(f"    • YELLOW: 10-50% error")
        print(f"    • GREEN: <10% error")
        print("="*70)
        print(f"\n📊 View dashboard: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")

    except Exception as e:
        logger.error(f"Failed to apply formatting: {e}")
        raise

if __name__ == "__main__":
    main()
