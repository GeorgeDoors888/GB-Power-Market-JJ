#!/usr/bin/env python3
"""
Upload Comprehensive DNO Tariffs to Google Sheets
With full documentation and proper formatting
"""

import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load the comprehensive tariffs
df = pd.read_csv('comprehensive_dno_tariffs_with_references.csv')

# Add Year column
df['Year'] = df['Document_Reference'].str.extract(r'(20\d{2})')

# Reorder columns for clarity
column_order = [
    'Year',
    'DNO_Name',
    'DNO_Code',
    'Tariff_Name',
    'LLFCs',
    'PCs',
    'Red_Rate_p_kWh',
    'Amber_Rate_p_kWh',
    'Green_Rate_p_kWh',
    'Fixed_Charge_p_day',
    'Capacity_Charge_p_kVA_day',
    'Document',
    'Document_Reference',
    'Source_Sheet'
]

df = df[column_order]

# Sort by Year, DNO, Tariff
df = df.sort_values(['Year', 'DNO_Name', 'Tariff_Name'])

print("=" * 100)
print("📤 UPLOADING COMPREHENSIVE DNO TARIFFS TO GOOGLE SHEETS")
print("=" * 100)
print(f"\nTotal tariffs: {len(df)}")
print(f"Years: {sorted(df['Year'].dropna().unique())}")
print(f"DNOs: {sorted(df['DNO_Name'].unique())}")
print()

try:
    creds = Credentials.from_authorized_user_file('token.json', [
        'https://www.googleapis.com/auth/spreadsheets'
    ])
    
    service = build('sheets', 'v4', credentials=creds)
    
    # Create new spreadsheet
    spreadsheet = {
        'properties': {
            'title': 'Comprehensive DNO Tariffs with Full Documentation'
        }
    }
    
    spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    
    print(f"✅ Created spreadsheet")
    print(f"🔗 https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit\n")
    
    # Prepare data for "All Tariffs" sheet
    headers = list(df.columns)
    all_values = [headers] + df.fillna('').astype(str).values.tolist()
    
    # Upload All Tariffs sheet
    print("📊 Uploading 'All Tariffs' sheet...")
    body = {'values': all_values}
    
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()
    
    # Rename Sheet1 to "All Tariffs"
    requests = [{
        'updateSheetProperties': {
            'properties': {
                'sheetId': 0,
                'title': 'All Tariffs'
            },
            'fields': 'title'
        }
    }]
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    
    print(f"✅ Uploaded {len(df)} tariffs\n")
    
    # Create sheets for each year
    for year in sorted(df['Year'].dropna().unique()):
        year_df = df[df['Year'] == year]
        print(f"📊 Creating sheet for {year} ({len(year_df)} tariffs)...")
        
        # Add new sheet
        requests = [{
            'addSheet': {
                'properties': {
                    'title': f'Year {year}'
                }
            }
        }]
        
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        # Upload data
        year_values = [headers] + year_df.fillna('').astype(str).values.tolist()
        body = {'values': year_values}
        
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'Year {year}'!A1",
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"   ✅ Uploaded")
    
    # Create sheet for Non-Domestic Aggregated tariffs only
    print(f"\n📊 Creating 'Non-Domestic Aggregated' summary sheet...")
    agg_df = df[df['Tariff_Name'].str.contains('Non-Domestic Aggregated', case=False, na=False)]
    
    requests = [{
        'addSheet': {
            'properties': {
                'title': 'Non-Domestic Aggregated'
            }
        }
    }]
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    
    agg_values = [headers] + agg_df.fillna('').astype(str).values.tolist()
    body = {'values': agg_values}
    
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Non-Domestic Aggregated'!A1",
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"   ✅ Uploaded {len(agg_df)} tariffs\n")
    
    # Apply formatting to all sheets
    print("🎨 Applying formatting...")
    
    # Get all sheet IDs
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', [])
    
    requests = []
    for sheet in sheets:
        sheet_id = sheet['properties']['sheetId']
        
        # Format header row
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.86},
                        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })
        
        # Auto-resize columns
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': len(headers)
                }
            }
        })
        
        # Freeze header row
        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'frozenRowCount': 1
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        })
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    
    print("✅ Formatting applied\n")
    
    print("=" * 100)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 100)
    print(f"\n🔗 Spreadsheet URL:")
    print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    print(f"\n📊 Sheets created:")
    print(f"   - All Tariffs ({len(df)} tariffs)")
    for year in sorted(df['Year'].dropna().unique()):
        year_count = len(df[df['Year'] == year])
        print(f"   - Year {year} ({year_count} tariffs)")
    print(f"   - Non-Domestic Aggregated ({len(agg_df)} tariffs)")
    
except FileNotFoundError:
    print("❌ token.json not found - Google Sheets upload skipped")
except HttpError as e:
    print(f"❌ Google Sheets API error: {e}")
