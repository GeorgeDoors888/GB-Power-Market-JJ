#!/usr/bin/env python3
from googleapiclient.discovery import build
from google.oauth2 import service_account

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Interconnectors!A1:D12'
).execute()

vals = result.get('values', [])
print('Live_Raw_Interconnectors tab content:')
for i, row in enumerate(vals):
    print(f'Row {i}: {row}')
