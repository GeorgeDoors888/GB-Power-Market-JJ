#!/usr/bin/env python3
"""
Generate HH (Half-Hourly) Profile Data for BtM Sheet

Reads parameters from BtM sheet:
- B17: Min kW
- B18: Avg kW
- B19: Max kW
- B20: Supply Type (dropdown)

Generates 1 year of HH data (17,520 periods) in "HH DATA" sheet
Based on realistic load profiles for each customer type.

Usage:
    python3 generate_hh_data.py
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
import random
from datetime import datetime, timedelta

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def main():
    # Auth
    creds = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json', scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    print('📊 HH DATA GENERATOR')
    print('=' * 80)

    # 1. Read inputs from BtM sheet
    result = service.spreadsheets().values().batchGet(
        spreadsheetId=SPREADSHEET_ID,
        ranges=['BtM!B17', 'BtM!B18', 'BtM!B19', 'BtM!B20']
    ).execute()

    values = result['valueRanges']
    min_kw = float(values[0].get('values', [[500]])[0][0])
    avg_kw = float(values[1].get('values', [[1000]])[0][0])
    max_kw = float(values[2].get('values', [[1500]])[0][0])
    supply_type = values[3].get('values', [['Commercial']])[0][0]

    print(f'📌 BtM Parameters:')
    print(f'   Min kW: {min_kw:,.0f}')
    print(f'   Avg kW: {avg_kw:,.0f}')
    print(f'   Max kW: {max_kw:,.0f}')
    print(f'   Supply Type: {supply_type}')

    # 2. Define realistic hourly profiles (% of max capacity)
    profiles = {
        'Domestic': {
            'weekday': [22,18,15,13,14,18,25,35,30,25,23,24,26,28,30,35,43,52,60,65,58,45,32,26],
            'weekend': [25,20,18,16,15,17,20,28,35,38,40,42,43,42,40,38,42,48,55,60,55,48,38,30]
        },
        'Commercial': {
            'weekday': [44,42,40,39,40,45,55,66,72,75,78,78,76,74,75,78,75,68,62,58,52,48,46,45],
            'weekend': [40,38,36,35,36,38,42,48,52,54,56,58,58,57,56,55,52,48,44,42,40,39,38,38]
        },
        'Industrial': {
            'weekday': [45,46,47,48,50,54,60,64,68,72,75,77,78,76,72,70,66,60,54,50,48,47,46,45],
            'weekend': [48,47,46,45,46,48,52,56,60,62,64,65,65,64,62,60,58,54,52,50,49,48,48,48]
        },
        'Network Rail': {
            'weekday': [28,26,25,24,26,30,38,44,48,46,44,44,45,46,48,50,44,38,34,32,30,29,28,28],
            'weekend': [30,28,27,26,27,29,32,36,40,42,42,42,42,41,40,38,36,34,32,31,30,30,29,29]
        },
        'EV Charging': {
            'weekday': [12,10,10,11,12,15,35,61,58,52,48,46,48,50,56,62,68,75,83,78,65,52,38,20],
            'weekend': [15,12,11,11,12,14,20,32,42,48,52,54,55,54,52,50,48,45,42,38,32,26,22,18]
        },
        'Datacentre': {
            'weekday': [84]*24,
            'weekend': [84]*24
        },
        'Non-Variable': {
            'weekday': [100]*24,
            'weekend': [100]*24
        },
        'Solar and Storage': {
            'weekday': [50,50,50,50,50,50,50,50,45,35,30,25,25,25,25,30,35,40,45,50,50,50,50,50],
            'weekend': [50]*24
        },
        'Storage': {
            'weekday': [50,50,50,50,50,50,50,50,45,35,30,25,25,25,25,30,35,40,45,50,50,50,50,50],
            'weekend': [50]*24
        },
        'Solar and Wind and Storage': {
            'weekday': [50,50,50,50,50,50,50,50,45,35,30,25,25,25,25,30,35,40,45,50,50,50,50,50],
            'weekend': [50]*24
        }
    }

    # 3. Get/create HH DATA sheet
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    hh_sheet_id = next((s['properties']['sheetId']
                        for s in spreadsheet['sheets']
                        if s['properties']['title'] == 'HH DATA'), None)

    if hh_sheet_id:
        print('🗑️  Clearing old HH DATA...')
        # Resize to 20k rows
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': hh_sheet_id,
                        'gridProperties': {'rowCount': 20000, 'columnCount': 10}
                    },
                    'fields': 'gridProperties(rowCount,columnCount)'
                }
            }]}
        ).execute()

        # Clear
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range='HH DATA!A:Z'
        ).execute()
        print('✅ Old data deleted')
    else:
        print('📄 Creating HH DATA sheet...')
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

    # 4. Generate 1 year of HH data
    start_date = datetime(2024, 1, 1)
    hh_data = [['Timestamp', 'Settlement Period', 'Day Type', 'Demand (kW)', 'Profile %']]

    profile = profiles.get(supply_type, profiles['Commercial'])

    for day in range(365):
        current_date = start_date + timedelta(days=day)
        is_weekend = current_date.weekday() >= 5
        day_type = 'Weekend' if is_weekend else 'Weekday'
        pattern = profile['weekend'] if is_weekend else profile['weekday']

        for sp in range(1, 49):  # 48 settlement periods per day
            hour = (sp - 1) // 2

            # Base profile % with random variation
            profile_pct = pattern[hour] + random.uniform(-5, 5)
            profile_pct = max(0, min(100, profile_pct))

            # Scale to kW range: profile % directly maps between Min and Max
            # 0% = min_kw, 100% = max_kw (avg_kw is ignored)
            demand_kw = min_kw + (profile_pct / 100.0) * (max_kw - min_kw)

            timestamp = current_date.strftime('%Y-%m-%d') + f' {hour:02d}:{30 if sp % 2 == 0 else "00"}'

            hh_data.append([
                timestamp,
                sp,
                day_type,
                round(demand_kw, 2),
                round(profile_pct, 1)
            ])

    print(f'✅ Generated {len(hh_data)-1:,} HH periods (365 days)')

    # 5. Upload in batches (5000 rows per batch)
    for i in range(0, len(hh_data), 5000):
        batch = hh_data[i:i+5000]
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'HH DATA!A{i+1}',
            valueInputOption='USER_ENTERED',
            body={'values': batch}
        ).execute()
        print(f'📤 Uploaded rows {i+1:,} to {i+len(batch):,}')

    # 6. Calculate actual average
    total_demand = sum(row[3] for row in hh_data[1:])
    actual_avg = total_demand / len(hh_data[1:])

    print('\n' + '=' * 80)
    print('✅ COMPLETE - HH DATA SHEET READY')
    print(f'\n📊 Summary:')
    print(f'   Supply Type: {supply_type}')
    print(f'   Total Periods: {len(hh_data)-1:,} (365 days × 48 SP)')
    print(f'   Min Demand: {min_kw:,.0f} kW')
    print(f'   Target Avg: {avg_kw:,.0f} kW')
    print(f'   Actual Avg: {actual_avg:,.0f} kW')
    print(f'   Max Demand: {max_kw:,.0f} kW')
    print(f'\n💡 To regenerate: Change BtM!B17-B20 values and rerun this script')

if __name__ == '__main__':
    main()
