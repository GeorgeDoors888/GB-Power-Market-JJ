#!/usr/bin/env python3
"""
Fetch Google Sheets data and create repo.md documentation files
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID of the spreadsheet
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def get_sheets_service():
    """Authenticate and return Google Sheets service"""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('sheets', 'v4', credentials=creds)
    return service

def fetch_sheet_data(service, range_name):
    """Fetch data from a specific range in the spreadsheet"""
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    
    values = result.get('values', [])
    return values

def create_repo_md(data):
    """Create repo.md from sheet data"""
    content = "# UK Energy Dashboard Repository\n\n"
    content += f"**Generated from:** [Google Sheet](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID})\n\n"
    content += "---\n\n"
    
    # Process data and create markdown
    for row in data:
        if row:
            content += f"- {' | '.join(row)}\n"
    
    return content

def main():
    """Main function to fetch data and create files"""
    print("🔐 Authenticating with Google Sheets API...")
    service = get_sheets_service()
    
    print("📊 Fetching spreadsheet metadata...")
    # Get spreadsheet metadata to see all sheets
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = spreadsheet.get('sheets', [])
    
    print(f"\n📋 Found {len(sheets)} sheets:")
    for sheet in sheets:
        title = sheet['properties']['title']
        sheet_id = sheet['properties']['sheetId']
        print(f"  - {title} (ID: {sheet_id})")
    
    # Fetch data from first sheet (adjust range as needed)
    print(f"\n📥 Fetching data from first sheet...")
    first_sheet = sheets[0]['properties']['title']
    data = fetch_sheet_data(service, f"{first_sheet}!A1:Z1000")
    
    print(f"✅ Retrieved {len(data)} rows")
    
    # Create repo.md
    print("\n📝 Creating repo.md...")
    repo_content = create_repo_md(data)
    
    with open('repo.md', 'w') as f:
        f.write(repo_content)
    
    print("✅ Created repo.md")
    
    # If there are multiple sheets, create repo2.md from second sheet
    if len(sheets) > 1:
        print("\n📥 Fetching data from second sheet...")
        second_sheet = sheets[1]['properties']['title']
        data2 = fetch_sheet_data(service, f"{second_sheet}!A1:Z1000")
        
        print(f"✅ Retrieved {len(data2)} rows")
        
        repo2_content = create_repo_md(data2)
        with open('repo2.md', 'w') as f:
            f.write(repo2_content)
        
        print("✅ Created repo2.md")
    
    print("\n🎉 Done! Files created successfully.")

if __name__ == '__main__':
    main()
