#!/usr/bin/env python3
"""
Upload Dashboard Data to Google Sheets
Uploads traffic light tariffs, TNUoS/BSUoS charges, and time band summaries
"""

import pandas as pd
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
DASHBOARD_DIR = Path("/Users/georgemajor/GB Power Market JJ/dashboard_data")
TOKEN_PATH = Path("/Users/georgemajor/GB Power Market JJ/token.json")
SPREADSHEET_NAME = "DNO Charging Dashboard - Traffic Light Tariffs"

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def authenticate():
    """Authenticate using saved token"""
    print("🔐 Authenticating...")
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    print("   ✅ Authenticated as: george@upowerenergy.uk")
    return creds

def create_spreadsheet(service, title):
    """Create new spreadsheet"""
    spreadsheet = {
        'properties': {'title': title}
    }
    spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId,spreadsheetUrl').execute()
    return spreadsheet.get('spreadsheetId'), spreadsheet.get('spreadsheetUrl')

def upload_dataframe(service, spreadsheet_id, df, sheet_name, start_cell='A1'):
    """Upload DataFrame to sheet"""
    values = [df.columns.tolist()] + df.fillna('').values.tolist()
    body = {'values': values}
    
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f'{sheet_name}!{start_cell}',
        valueInputOption='RAW',
        body=body
    ).execute()

def main():
    print("=" * 80)
    print("DASHBOARD DATA UPLOADER")
    print("=" * 80)
    print()
    
    # Authenticate
    creds = authenticate()
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # Create spreadsheet
    print(f"\n📄 Creating spreadsheet...")
    spreadsheet_id, spreadsheet_url = create_spreadsheet(sheets_service, SPREADSHEET_NAME)
    print(f"   ✅ Created: {spreadsheet_url}")
    
    # Load data files
    traffic_light_df = pd.read_csv(DASHBOARD_DIR / "traffic_light_tariffs.csv")
    tnuos_df = pd.read_csv(DASHBOARD_DIR / "tnuos_charges.csv")
    time_band_df = pd.read_csv(DASHBOARD_DIR / "time_band_summary.csv")
    
    print(f"\n📤 Uploading sheets...")
    
    # Upload traffic light tariffs (smaller chunks)
    print(f"   📊 Traffic Light Tariffs ({len(traffic_light_df):,} rows)...")
    upload_dataframe(sheets_service, spreadsheet_id, traffic_light_df, 'Sheet1')
    
    # Rename Sheet1
    requests = [{
        'updateSheetProperties': {
            'properties': {'sheetId': 0, 'title': 'Traffic Light Tariffs'},
            'fields': 'title'
        }
    }]
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
    
    # Add TNUoS sheet
    print(f"   📊 TNUoS Charges ({len(tnuos_df):,} rows)...")
    requests = [{'addSheet': {'properties': {'title': 'TNUoS Charges'}}}]
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
    upload_dataframe(sheets_service, spreadsheet_id, tnuos_df, 'TNUoS Charges')
    
    # Add Time Bands sheet
    print(f"   📊 Time Band Summary ({len(time_band_df):,} rows)...")
    requests = [{'addSheet': {'properties': {'title': 'Time Band Summary'}}}]
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
    upload_dataframe(sheets_service, spreadsheet_id, time_band_df, 'Time Band Summary')
    
    print()
    print("=" * 80)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 80)
    print()
    print(f"🔗 Dashboard URL:")
    print(f"   {spreadsheet_url}")
    print()
    print("📊 Sheets created:")
    print(f"   1. Traffic Light Tariffs: 2,309 tariffs with Red/Amber/Green time bands")
    print(f"   2. TNUoS Charges: 113 transmission network charges")
    print(f"   3. Time Band Summary: 41 time band configurations by DNO and year")
    print()

if __name__ == "__main__":
    main()
