#!/usr/bin/env python3
"""
Upload all 14 DNOs comprehensive tariff data to Google Sheets
"""

import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def create_spreadsheet_with_data():
    """Upload comprehensive DNO tariffs to Google Sheets"""
    
    # Load credentials
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Build services
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Read CSV
    df = pd.read_csv('all_14_dnos_comprehensive_tariffs.csv')
    
    print(f"\n📤 UPLOADING ALL 14 DNOs COMPREHENSIVE TARIFFS")
    print("="*100)
    print(f"\nTotal tariffs: {len(df)}")
    print(f"DNOs: {sorted(df['DNO_Name'].unique())}")
    print(f"Years: {sorted(df['Year'].dropna().unique())}")
    
    # Create new spreadsheet
    spreadsheet = {
        'properties': {
            'title': 'All 14 UK DNOs - Comprehensive Tariffs with Full Documentation'
        }
    }
    
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = spreadsheet['spreadsheetId']
    
    print(f"\n✅ Created spreadsheet")
    print(f"🔗 https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    
    # Prepare batch requests
    requests = []
    
    # 1. Upload "All Tariffs" sheet
    print(f"\n📊 Uploading 'All Tariffs' sheet ({len(df)} tariffs)...")
    
    # Rename Sheet1 to "All Tariffs"
    requests.append({
        'updateSheetProperties': {
            'properties': {
                'sheetId': 0,
                'title': 'All Tariffs'
            },
            'fields': 'title'
        }
    })
    
    # Prepare data
    all_data = [df.columns.tolist()] + df.fillna('').values.tolist()
    
    # Update values
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='All Tariffs!A1',
        valueInputOption='RAW',
        body={'values': all_data}
    ).execute()
    
    print(f"   ✅ Uploaded {len(df)} tariffs")
    
    # 2. Create sheets by year
    years = sorted([y for y in df['Year'].unique() if y])
    
    for year in years:
        year_df = df[df['Year'] == year]
        sheet_name = f'Year {year}'
        
        print(f"\n📊 Creating sheet for {year} ({len(year_df)} tariffs)...")
        
        # Add sheet
        requests.append({
            'addSheet': {
                'properties': {
                    'title': sheet_name
                }
            }
        })
        
        # Execute batch request to create sheet
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        requests = []  # Clear for next batch
        
        # Upload data
        year_data = [year_df.columns.tolist()] + year_df.fillna('').values.tolist()
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A1',
            valueInputOption='RAW',
            body={'values': year_data}
        ).execute()
        
        print(f"   ✅ Uploaded {len(year_df)} tariffs")
    
    # 3. Create sheets by DNO
    dnos = sorted(df['DNO_Name'].unique())
    
    for dno in dnos:
        dno_df = df[df['DNO_Name'] == dno]
        sheet_name = dno[:31]  # Excel/Sheets sheet name limit
        
        print(f"\n📊 Creating sheet for {dno} ({len(dno_df)} tariffs)...")
        
        # Add sheet
        requests.append({
            'addSheet': {
                'properties': {
                    'title': sheet_name
                }
            }
        })
        
        # Execute batch request
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        requests = []
        
        # Upload data
        dno_data = [dno_df.columns.tolist()] + dno_df.fillna('').values.tolist()
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A1',
            valueInputOption='RAW',
            body={'values': dno_data}
        ).execute()
        
        print(f"   ✅ Uploaded {len(dno_df)} tariffs")
    
    # 4. Create "Non-Domestic Summary" sheet
    nd_df = df[df['Tariff_Name'].str.contains('Non-Domestic', case=False, na=False)]
    
    if len(nd_df) > 0:
        print(f"\n📊 Creating 'Non-Domestic Summary' sheet ({len(nd_df)} tariffs)...")
        
        requests.append({
            'addSheet': {
                'properties': {
                    'title': 'Non-Domestic Summary'
                }
            }
        })
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        requests = []
        
        nd_data = [nd_df.columns.tolist()] + nd_df.fillna('').values.tolist()
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Non-Domestic Summary!A1',
            valueInputOption='RAW',
            body={'values': nd_data}
        ).execute()
        
        print(f"   ✅ Uploaded {len(nd_df)} tariffs")
    
    # 5. Apply formatting to all sheets
    print(f"\n🎨 Applying formatting...")
    
    # Get all sheets
    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    
    format_requests = []
    for sheet in sheets:
        sheet_id = sheet['properties']['sheetId']
        
        # Blue header with white text
        format_requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
                        'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True}
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })
        
        # Freeze header row
        format_requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {'frozenRowCount': 1}
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        })
        
        # Auto-resize columns
        format_requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 13
                }
            }
        })
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': format_requests}
    ).execute()
    
    print(f"   ✅ Formatting applied")
    
    # Summary
    print("\n" + "="*100)
    print("✅ UPLOAD COMPLETE!")
    print("="*100)
    print(f"\n📊 Sheets created:")
    print(f"   - All Tariffs ({len(df)} tariffs)")
    for year in years:
        year_count = len(df[df['Year'] == year])
        print(f"   - Year {year} ({year_count} tariffs)")
    for dno in dnos:
        dno_count = len(df[df['DNO_Name'] == dno])
        print(f"   - {dno} ({dno_count} tariffs)")
    print(f"   - Non-Domestic Summary ({len(nd_df)} tariffs)")
    
    print(f"\n🔗 Spreadsheet URL:")
    print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    print()


if __name__ == "__main__":
    create_spreadsheet_with_data()
