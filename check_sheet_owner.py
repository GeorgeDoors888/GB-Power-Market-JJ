#!/usr/bin/env python3
"""Check spreadsheet owner"""

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load credentials
creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=[
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
)

gc = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

# Check the spreadsheet
spreadsheet_id = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

try:
    sheet = gc.open_by_key(spreadsheet_id)
    print(f'✅ Spreadsheet: {sheet.title}')
    print(f'   URL: {sheet.url}')
    
    # Get owner info
    file_info = drive_service.files().get(
        fileId=spreadsheet_id,
        fields='owners,permissions'
    ).execute()
    
    print(f'\n📧 Owner: {file_info["owners"][0]["emailAddress"]}')
    print(f'   Name: {file_info["owners"][0]["displayName"]}')
    
    print(f'\n👥 Permissions:')
    for perm in file_info.get('permissions', []):
        print(f'   - {perm.get("emailAddress", "Anyone")}: {perm["role"]}')
        
except Exception as e:
    print(f'❌ Error: {e}')
