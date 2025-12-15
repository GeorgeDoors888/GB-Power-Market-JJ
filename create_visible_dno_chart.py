#!/usr/bin/env python3
"""Create visible DNO map chart in Google Sheets"""
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet('DNO')
sheet_id = sheet.id

print(f"✅ Working on DNO sheet (ID: {sheet_id})")

# Delete any existing charts first
delete_requests = []
try:
    metadata = spreadsheet.fetch_sheet_metadata()
    for s in metadata['sheets']:
        if s['properties']['sheetId'] == sheet_id:
            if 'charts' in s:
                for chart in s['charts']:
                    delete_requests.append({
                        'deleteEmbeddedObject': {
                            'objectId': chart['chartId']
                        }
                    })
    if delete_requests:
        spreadsheet.batch_update({'requests': delete_requests})
        print(f"✅ Deleted {len(delete_requests)} existing charts")
except Exception as e:
    print(f"⚠️  Could not delete old charts: {e}")

# Create new scatter chart showing DNO locations
chart_request = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "🗺️ UK DNO Geographic Distribution",
                "subtitle": "14 Distribution Network Operator Regions",
                "basicChart": {
                    "chartType": "SCATTER",
                    "legendPosition": "BOTTOM_LEGEND",
                    "axis": [
                        {
                            "position": "BOTTOM_AXIS",
                            "title": "Longitude (East ←→ West)"
                        },
                        {
                            "position": "LEFT_AXIS",
                            "title": "Latitude (South ←→ North)"
                        }
                    ],
                    "domains": [
                        {
                            "domain": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "sheetId": sheet_id,
                                            "startRowIndex": 1,
                                            "endRowIndex": 15,
                                            "startColumnIndex": 2,  # Longitude
                                            "endColumnIndex": 3
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
                                            "startRowIndex": 1,
                                            "endRowIndex": 15,
                                            "startColumnIndex": 1,  # Latitude
                                            "endColumnIndex": 2
                                        }
                                    ]
                                }
                            },
                            "targetAxis": "LEFT_AXIS",
                            "dataLabel": {
                                "type": "CUSTOM",
                                "customLabelData": {
                                    "sourceRange": {
                                        "sources": [
                                            {
                                                "sheetId": sheet_id,
                                                "startRowIndex": 1,
                                                "endRowIndex": 15,
                                                "startColumnIndex": 0,  # DNO Area names
                                                "endColumnIndex": 1
                                            }
                                        ]
                                    }
                                }
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
                        "rowIndex": 1,
                        "columnIndex": 6  # Column G, row 2
                    },
                    "offsetXPixels": 10,
                    "offsetYPixels": 10,
                    "widthPixels": 900,
                    "heightPixels": 700
                }
            }
        }
    }
}

response = spreadsheet.batch_update({"requests": [chart_request]})
chart_id = response['replies'][0]['addChart']['chart']['chartId']
print(f"✅ Chart created! ID: {chart_id}")
print(f"\n📊 Chart positioned at column G, row 2")
print(f"📍 Shows all 14 DNO regions with geographic labels")
print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet_id}")
