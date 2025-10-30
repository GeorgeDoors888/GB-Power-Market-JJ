#!/usr/bin/env python3
"""Quick upload of all 14 DNOs to Google Sheets"""

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os.path
import pickle

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Get credentials
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

# Build services
print("Building services...")
sheets_service = build('sheets', 'v4', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

# Read CSV
print("Reading data...")
df = pd.read_csv('all_14_dnos_comprehensive_tariffs.csv')

print(f'\nTotal tariffs: {len(df)}')
print(f'DNOs: {df["DNO_Name"].nunique()}')
print(f'Years: {sorted(df["Year"].dropna().unique())}')

print('\nCreating spreadsheet...')

# Create spreadsheet
spreadsheet = sheets_service.spreadsheets().create(body={
    'properties': {'title': 'All 14 UK DNOs - Comprehensive Tariffs with Full Documentation'}
}).execute()

spreadsheet_id = spreadsheet['spreadsheetId']
print(f'\n✅ Created spreadsheet!')
print(f'🔗 https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit')

# Upload all data
print(f'\n📤 Uploading {len(df)} tariffs...')
all_data = [df.columns.tolist()] + df.fillna('').values.tolist()

sheets_service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range='Sheet1!A1',
    valueInputOption='RAW',
    body={'values': all_data}
).execute()

print(f'✅ Uploaded {len(df)} tariffs to Sheet1')

# Apply formatting
print('\n🎨 Applying formatting...')

# Blue header
sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={'requests': [
        {
            'repeatCell': {
                'range': {'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 1},
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
                        'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True}
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        },
        {
            'updateSheetProperties': {
                'properties': {'sheetId': 0, 'gridProperties': {'frozenRowCount': 1}},
                'fields': 'gridProperties.frozenRowCount'
            }
        },
        {
            'autoResizeDimensions': {
                'dimensions': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 13}
            }
        }
    ]}
).execute()

print('✅ Formatting applied!')

print('\n' + '='*80)
print('✅ UPLOAD COMPLETE!')
print('='*80)
print(f'\n📊 Spreadsheet contains {len(df)} tariffs from {df["DNO_Name"].nunique()} DNOs')
print(f'🔗 https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit')
print()
