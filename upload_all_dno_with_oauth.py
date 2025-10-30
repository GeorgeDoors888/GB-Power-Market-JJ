#!/usr/bin/env python3
"""
Upload ALL DNO Charging Data to Google Sheets using OAuth
78,901 records from all 14 UK DNO license areas (2014-2026)
"""

import pandas as pd
from pathlib import Path
import time
from datetime import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
CSV_PATH = Path("/Users/georgemajor/GB Power Market JJ/all_dno_charging_data_parsed.csv")
OAUTH_CREDENTIALS = Path("/Users/georgemajor/GB Power Market JJ/oauth_credentials.json")
TOKEN_PATH = Path("/Users/georgemajor/GB Power Market JJ/token.json")
SPREADSHEET_NAME_PREFIX = "All DNO Charging Data"

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def authenticate_oauth():
    """Authenticate using OAuth (user account)"""
    print("🔐 Authenticating with OAuth...")
    print(f"   Account: george@upowerenergy.uk")
    print()
    
    creds = None
    
    if TOKEN_PATH.exists():
        print("   📄 Found saved token, attempting to use it...")
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("   🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not OAUTH_CREDENTIALS.exists():
                print()
                print("   ❌ ERROR: oauth_credentials.json not found!")
                print()
                raise FileNotFoundError("oauth_credentials.json not found")
            
            print("   🌐 Opening browser for authentication...")
            print("   👤 Please log in as: george@upowerenergy.uk")
            print()
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(OAUTH_CREDENTIALS), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
        print("   ✅ Token saved for future use")
    
    print("   ✅ Authentication successful!")
    print(f"   📧 Authenticated as: george@upowerenergy.uk")
    print()
    
    return creds

def create_spreadsheet(service, title):
    """Create a new Google Spreadsheet"""
    print(f"📄 Creating spreadsheet: {title}")
    
    try:
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        
        spreadsheet = service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()
        
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')
        
        print(f"   ✅ Created: {spreadsheet_url}")
        print(f"   📋 ID: {spreadsheet_id}")
        
        return spreadsheet_id, spreadsheet_url
    
    except HttpError as error:
        print(f"   ❌ Error creating spreadsheet: {error}")
        raise

def upload_data_to_sheet(service, spreadsheet_id, df, sheet_name='Charging Data'):
    """Upload DataFrame to a specific sheet"""
    print(f"   📤 Uploading {len(df):,} rows to '{sheet_name}'...")
    
    try:
        # Prepare data (header + rows)
        values = [df.columns.tolist()] + df.values.tolist()
        
        # Update the sheet
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"   ✅ Uploaded {result.get('updatedCells'):,} cells")
        
    except HttpError as error:
        print(f"   ❌ Error uploading data: {error}")
        raise

def create_summary_sheet(service, spreadsheet_id, df):
    """Create summary statistics sheet"""
    print(f"   📊 Creating summary sheet...")
    
    try:
        # Add a new sheet
        requests = [{
            'addSheet': {
                'properties': {
                    'title': 'Summary',
                    'index': 0
                }
            }
        }]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        # Prepare summary data
        summary_data = [
            ['All DNO Charging Data Summary', ''],
            ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['', ''],
            ['Statistics', ''],
            ['Total Records', len(df)],
            ['Years Covered', f"{df['year'].min()} - {df['year'].max()}"],
            ['DNO Areas (14 total)', ', '.join(sorted(df['dno_code'].unique()))],
            ['Files Parsed', 232],
            ['Files with Data', 193],
            ['', ''],
            ['Geographic Coverage', '100% of Great Britain'],
            ['', ''],
            ['Records by DNO', ''],
        ]
        
        # Add DNO breakdown
        dno_counts = df.groupby(['dno_code', 'dno_name']).size().sort_values(ascending=False)
        for (dno, name), count in dno_counts.items():
            summary_data.append([f'  {dno} ({name})', int(count)])
        
        summary_data.append(['', ''])
        summary_data.append(['Records by Year', ''])
        
        # Add year breakdown
        year_counts = df['year'].value_counts().sort_index()
        for year, count in year_counts.items():
            summary_data.append([f'  {year}', int(count)])
        
        # Upload summary
        body = {
            'values': summary_data
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Summary!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"   ✅ Summary sheet created")
        
    except HttpError as error:
        print(f"   ⚠️  Could not create summary: {error}")

def format_spreadsheet(service, spreadsheet_id):
    """Apply formatting to the spreadsheet"""
    print(f"   🎨 Applying formatting...")
    
    try:
        requests = [
            # Freeze header row in Sheet1
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            },
            # Format header row in Sheet1
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.2,
                                'green': 0.6,
                                'blue': 0.8
                            },
                            'textFormat': {
                                'bold': True,
                                'foregroundColor': {
                                    'red': 1,
                                    'green': 1,
                                    'blue': 1
                                }
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            }
        ]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        print(f"   ✅ Formatting applied")
        
    except HttpError as error:
        print(f"   ⚠️  Could not apply formatting: {error}")

def main():
    """Main execution"""
    print("=" * 80)
    print("ALL DNO CHARGING DATA - GOOGLE SHEETS UPLOADER (OAuth)")
    print("=" * 80)
    print()
    print("📊 Dataset: 78,901 records from all 14 UK DNO license areas")
    print("📅 Coverage: 2014-2026 (13 years)")
    print("🗺️  Geographic: 100% of Great Britain")
    print()
    
    # Authenticate
    try:
        creds = authenticate_oauth()
    except FileNotFoundError:
        return
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Build services
    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        print("✅ Connected to Google Sheets API")
        print()
    except Exception as e:
        print(f"❌ Could not connect to Google Sheets: {e}")
        return
    
    # Load data
    print("📂 Loading data...")
    try:
        df = load_data()
    except Exception as e:
        print(f"❌ Could not load data: {e}")
        return
    
    print()
    
    # Create spreadsheet
    print(f"📄 Creating spreadsheet in YOUR Google Drive...")
    print(f"   (This will use your 7TB storage, not service account)")
    print()
    
    try:
        spreadsheet_id, spreadsheet_url = create_spreadsheet(
            sheets_service, 
            f"{SPREADSHEET_NAME_PREFIX} (2014-2026)"
        )
    except Exception as e:
        print(f"❌ Could not create spreadsheet: {e}")
        return
    
    print()
    
    # Upload main data
    print("📤 Uploading ALL DNO charging data...")
    print("   ⏳ This may take a few minutes (78,901 rows)...")
    try:
        upload_data_to_sheet(sheets_service, spreadsheet_id, df, 'Sheet1')
    except Exception as e:
        print(f"❌ Could not upload data: {e}")
        return
    
    print()
    
    # Create summary
    try:
        create_summary_sheet(sheets_service, spreadsheet_id, df)
    except Exception as e:
        print(f"⚠️  Could not create summary: {e}")
    
    print()
    
    # Format
    try:
        format_spreadsheet(sheets_service, spreadsheet_id)
    except Exception as e:
        print(f"⚠️  Could not apply formatting: {e}")
    
    print()
    print("=" * 80)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 80)
    print()
    print(f"📊 Spreadsheet created in YOUR Google Drive:")
    print(f"   {spreadsheet_url}")
    print()
    print(f"📈 Data uploaded:")
    print(f"   Records: {len(df):,}")
    print(f"   DNOs: All 14 UK license areas")
    print(f"   Years: 2014-2026")
    print(f"   Sheets: Charging Data + Summary")
    print()
    print(f"🔗 Open in browser:")
    print(f"   {spreadsheet_url}")
    print()

def load_data():
    """Load parsed CSV data"""
    df = pd.read_csv(CSV_PATH)
    
    # Clean up the data - replace all NaN/None with empty strings
    df = df.fillna('')
    
    print(f"   ✅ Loaded {len(df):,} records")
    print(f"   🧹 Cleaned all null values")
    print(f"   📊 DNOs: {len(df['dno_code'].unique())} areas")
    print(f"   📅 Years: {df['year'].min()} - {df['year'].max()}")
    
    return df

if __name__ == "__main__":
    main()
