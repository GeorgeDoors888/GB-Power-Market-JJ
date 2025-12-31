#!/usr/bin/env python3
"""
Generate HH (Half-Hourly) Profile Data for BtM Sheet - API Version

Fetches real HH profile data from API and scales to kW range based on:
- B17: Min kW
- B18: Avg kW (for reference only)
- B19: Max kW
- B20: Supply Type (dropdown)

Generates 17,520 HH periods in "HH DATA" sheet using actual load profiles from API.

Usage:
    python3 generate_hh_data_api.py
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
import requests
from datetime import datetime
import sys

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
BASE_URL = 'https://ukpowernetworks.opendatasoft.com'
DATASET_ID = 'ukpn-standard-profiles-electricity-demand'

def main():
    # Auth
    creds = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json', scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    
    print('📊 HH DATA GENERATOR (API-powered)')
    print('=' * 80)
    
    # 1. Read inputs from BtM sheet
    result = service.spreadsheets().values().batchGet(
        spreadsheetId=SPREADSHEET_ID,
        ranges=['BtM!B17', 'BtM!B18', 'BtM!B19', 'BtM!B20']
    ).execute()
    
    values = result['valueRanges']
    min_kw = float(values[0].get('values', [[0]])[0][0] or 0)
    avg_kw = float(values[1].get('values', [[0]])[0][0] or 0)
    max_kw = float(values[2].get('values', [[0]])[0][0] or 0)
    supply_type = values[3].get('values', [['Commercial']])[0][0]
    supply_type_key = supply_type.lower().replace(' ', '_')
    
    # Determine which scaling value to use (priority: Max > Avg > Min)
    if max_kw > 0:
        scale_value = max_kw
        scale_type = 'Max'
    elif avg_kw > 0:
        scale_value = avg_kw
        scale_type = 'Avg'
    elif min_kw > 0:
        scale_value = min_kw
        scale_type = 'Min'
    else:
        print('❌ Error: Please enter a value in B17 (Min kW), B18 (Avg kW), or B19 (Max kW)')
        sys.exit(1)
    
    print(f'📌 BtM Parameters:')
    print(f'   {scale_type} kW: {scale_value:,.0f} (scaling value)')
    print(f'   Supply Type: {supply_type} (API key: {supply_type_key})')
    
    # 2. Fetch all HH profile data from UK Power Networks (using export endpoint for all 17,520 records)
    export_url = f'{BASE_URL}/api/v2/catalog/datasets/{DATASET_ID}/exports/json?limit=-1'
    print(f'\n🌐 Fetching all 17,520 HH periods from UK Power Networks...')
    print(f'   Using export endpoint for complete dataset')
    
    try:
        response = requests.get(export_url, timeout=60)
        response.raise_for_status()
        all_records = response.json()
        
        print(f'✅ Fetched {len(all_records)} HH periods from UK Power Networks')
        
    except Exception as e:
        print(f'❌ API Error: {e}')
        print(f'   Check BASE_URL: {BASE_URL}')
        print(f'   Check DATASET_ID: {DATASET_ID}')
        sys.exit(1)
    
    # Transform export format to our format
    api_data = {
        'total_count': len(all_records),
        'results': [
            {
                'timestamp': record['timestamp'],
                'domestic': record.get('domestic'),
                'commercial': record.get('commercial'),
                'industrial': record.get('industrial'),
                'network_rail': record.get('network_rail'),
                'ev_charging': record.get('ev_charging'),
                'datacentre': record.get('datacentre'),
                'non_variable': record.get('non_variable'),
                'solar_and_storage': record.get('solar_and_storage'),
                'storage': record.get('storage'),
                'solar_and_wind_and_storage': record.get('solar_and_wind_and_storage')
            }
            for record in all_records
        ]
    }
    
    # 2b. Validate supply type exists
    if not api_data.get('results'):
        print('❌ No data returned from API')
        sys.exit(1)
    
    first_record = api_data['results'][0]
    if supply_type_key not in first_record:
        available = [k for k in first_record.keys() if k != 'timestamp']
        print(f'❌ Supply type "{supply_type_key}" not found in API data')
        print(f'   Available: {", ".join(available)}')
        sys.exit(1)
    
    # 3. Find or create HH DATA sheet
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    hh_sheet_id = None
    for sheet in spreadsheet.get('sheets', []):
        if sheet['properties']['title'] == 'HH DATA':
            hh_sheet_id = sheet['properties']['sheetId']
            break
    
    if hh_sheet_id:
        print('\n📄 Clearing existing HH DATA sheet...')
        # Resize if needed
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': hh_sheet_id,
                        'gridProperties': {'rowCount': 20000, 'columnCount': 10}
                    },
                    'fields': 'gridProperties'
                }
            }]}
        ).execute()
        
        # Clear content
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range='HH DATA!A:Z'
        ).execute()
    else:
        print('\n📄 Creating HH DATA sheet...')
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [{
                'addSheet': {
                    'properties': {
                        'title': 'HH DATA',
                        'gridProperties': {'rowCount': 20000, 'columnCount': 10}
                    }
                }
            }]}
        ).execute()
        print('✅ Sheet created')
    
    # 4. Process API data and write to sheet
    print(f'\n📝 Processing {len(api_data["results"])} HH periods...')
    hh_data = [['Timestamp', 'Settlement Period', 'Day Type', 'Demand (kW)', 'Profile %']]
    
    sp = 1
    for record in api_data['results']:
        # Parse timestamp
        timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        is_weekend = timestamp.weekday() >= 5
        day_type = 'Weekend' if is_weekend else 'Weekday'
        
        # Get profile % from API
        profile_pct = float(record[supply_type_key])
        
        # Scale profile: demand = scale_value × (profile% / 100)
        demand_kw = scale_value * (profile_pct / 100.0)
        
        # Format timestamp
        formatted_time = timestamp.strftime('%Y-%m-%d %H:%M')
        
        hh_data.append([
            formatted_time,
            sp,
            day_type,
            round(demand_kw, 2),
            round(profile_pct, 1)
        ])
        
        # Increment settlement period (1-48, resets at midnight)
        sp += 1
        if sp > 48:
            sp = 1
    
    # 5. Upload to Google Sheets in batches
    print(f'📤 Uploading {len(hh_data) - 1} periods to HH DATA sheet...')
    batch_size = 5000
    for i in range(0, len(hh_data), batch_size):
        batch = hh_data[i:i + batch_size]
        start_row = i + 1
        end_row = start_row + len(batch) - 1
        
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'HH DATA!A{start_row}:E{end_row}',
            valueInputOption='RAW',
            body={'values': batch}
        ).execute()
        
        if i > 0:  # Skip header batch
            print(f'   Rows {start_row:,}-{end_row:,}')
    
    # 6. Format headers
    print('\n🎨 Formatting headers...')
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [{
            'repeatCell': {
                'range': {
                    'sheetId': hh_sheet_id if hh_sheet_id else 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
                        'textFormat': {
                            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                            'bold': True
                        },
                        'horizontalAlignment': 'CENTER'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
            }
        }]}
    ).execute()
    
    print('\n' + '=' * 80)
    print(f'✅ COMPLETE - HH DATA READY')
    print(f'   Profile: {supply_type.title()}')
    print(f'   Scaling: {scale_type} kW = {scale_value:,.0f}')
    print(f'   Formula: demand = {scale_value:,.0f} × (profile% / 100)')
    print(f'   Periods: {len(hh_data):,} (from API)')
    print('=' * 80)

if __name__ == '__main__':
    main()
