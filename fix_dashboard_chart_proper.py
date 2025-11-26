#!/usr/bin/env python3
"""
Fix Dashboard Chart - Proper Multi-Axis with Bars and Lines
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import gspread

SA_FILE = 'inner-cinema-credentials.json'
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = Credentials.from_service_account_file(
    SA_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
service = build('sheets', 'v4', credentials=creds)

print('=' * 80)
print('FIXING DASHBOARD CHART WITH PROPER AXES AND CHART TYPES')
print('=' * 80)

# Get sheet IDs
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
dashboard_id = None
summary_id = None

for sheet in sheet_metadata['sheets']:
    title = sheet['properties']['title']
    sheet_id = sheet['properties']['sheetId']
    if title == 'Dashboard':
        dashboard_id = sheet_id
    elif title == 'Summary':
        summary_id = sheet_id

print(f'\n📋 Dashboard ID: {dashboard_id}')
print(f'📋 Summary ID: {summary_id}')

# Delete existing chart
print('\n🗑️  Deleting existing chart...')
delete_requests = []
for sheet in sheet_metadata['sheets']:
    if sheet['properties']['title'] == 'Dashboard':
        if 'charts' in sheet:
            for chart in sheet.get('charts', []):
                delete_requests.append({
                    'deleteEmbeddedObject': {
                        'objectId': chart['chartId']
                    }
                })

if delete_requests:
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': delete_requests}
    ).execute()
    print(f'   Deleted {len(delete_requests)} chart(s)')

# Create new chart with proper configuration
print('\n📊 Creating new multi-axis chart...')
print('   Left Axis (GW): Demand (Bar), Generation (Bar)')
print('   Right Axis (£/MWh): Price (Bar)')

requests = [{
    'addChart': {
        'chart': {
            'spec': {
                'title': 'System Overview - Last 48 Periods',
                'basicChart': {
                    'chartType': 'COMBO',
                    'legendPosition': 'TOP_LEGEND',
                    'axis': [
                        {
                            'position': 'BOTTOM_AXIS',
                            'title': 'Time'
                        },
                        {
                            'position': 'LEFT_AXIS',
                            'title': 'Gigawatts (GW)'
                        },
                        {
                            'position': 'RIGHT_AXIS',
                            'title': 'Price £/MWh'
                        }
                    ],
                    'domains': [{
                        'domain': {
                            'sourceRange': {
                                'sources': [{
                                    'sheetId': summary_id,
                                    'startRowIndex': 1,
                                    'startColumnIndex': 0,
                                    'endColumnIndex': 1
                                }]
                            }
                        }
                    }],
                    'series': [
                        # Series 1: Demand (GW) - Column Bar on LEFT axis
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': summary_id,
                                        'startRowIndex': 0,
                                        'startColumnIndex': 1,
                                        'endColumnIndex': 2
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'COLUMN'
                        },
                        # Series 2: Generation (GW) - Column Bar on LEFT axis
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': summary_id,
                                        'startRowIndex': 0,
                                        'startColumnIndex': 2,
                                        'endColumnIndex': 3
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'COLUMN'
                        },
                        # Series 3: Price (£/MWh) - Column Bar on RIGHT axis
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': summary_id,
                                        'startRowIndex': 0,
                                        'startColumnIndex': 4,
                                        'endColumnIndex': 5
                                    }]
                                }
                            },
                            'targetAxis': 'RIGHT_AXIS',
                            'type': 'COLUMN'
                        }
                    ],
                    'headerCount': 1
                }
            },
            'position': {
                'overlayPosition': {
                    'anchorCell': {
                        'sheetId': dashboard_id,
                        'rowIndex': 17,
                        'columnIndex': 0
                    },
                    'widthPixels': 1000,
                    'heightPixels': 400
                }
            }
        }
    }
}]

response = service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()

print('✅ Chart created successfully!')
print('\n📊 Chart Configuration:')
print('   Type: COMBO (multi-axis)')
print('   Position: Dashboard A18 (1000x400 px)')
print('   Left Axis (GW): Demand (Bar), Generation (Bar)')
print('   Right Axis (£/MWh): Price (Bar)')
print('   Legend: Top')
print('\n' + '=' * 80)
print('✅ COMPLETE - Chart now has proper axes and labels')
print('=' * 80)
