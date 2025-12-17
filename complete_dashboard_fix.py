#!/usr/bin/env python3
"""
Complete Dashboard Fix Diagnostic Tool
Reads Live Dashboard v2 and shows current vs expected layout
"""
from googleapiclient.discovery import build
from google.oauth2 import service_account
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

# Expected layout for Live Dashboard v2
EXPECTED_LAYOUT = {
    2: 'Last Updated: [timestamp]',
    13: '🌬️ WIND',
    14: '⚛️ NUCLEAR',
    15: '🏭 CCGT',
    16: '🌿 BIOMASS',
    17: '💧 NPSHYD',
    18: '❓ OTHER',
    19: '🛢️ OCGT',
    20: '[blank or additional fuel type]',
    21: '[blank or additional fuel type]',
    22: '[blank or additional fuel type]',
}

def main():
    print('='*80)
    print('LIVE DASHBOARD V2 - DIAGNOSTIC TOOL')
    print('='*80)

    creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    # Check both sheets
    for sheet_name in ['Live Dashboard v2', 'GB Live']:
        print(f'\n{"="*80}')
        print(f'SHEET: {sheet_name}')
        print('='*80)

        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{sheet_name}'!A1:H25"
        ).execute()
        vals = result.get('values', [])

        # Check timestamp row
        if len(vals) >= 2:
            timestamp_cell = vals[1][0] if len(vals[1]) > 0 else ''
            print(f'\nRow 2 (Timestamp): "{timestamp_cell[:60]}"')
            if 'Last Updated' in timestamp_cell:
                print('  ✅ Timestamp present')
            else:
                print('  ❌ No timestamp found')

        # Check fuel rows 13-22
        print(f'\nFuel Type Rows (13-22):')
        print('-'*80)
        for row_idx in range(12, 22):  # rows 13-22 (0-indexed as 12-21)
            if row_idx < len(vals):
                row = vals[row_idx]
                col_a = row[0] if len(row) > 0 else ''
                col_b = row[1] if len(row) > 1 else ''
                col_d = row[3] if len(row) > 3 else ''

                actual_row_num = row_idx + 1
                expected = EXPECTED_LAYOUT.get(actual_row_num, '')

                status = '✅' if col_a.strip() else '❌'
                print(f'Row {actual_row_num:2d} {status}: A="{col_a[:30]:<30}" B="{col_b[:15]:<15}" | Expected: {expected}')

        # Summary
        print(f'\n{"="*80}')
        print(f'SUMMARY FOR {sheet_name}:')
        print('='*80)

        has_fuel_names = False
        for row_idx in range(12, 19):  # Check rows 13-19
            if row_idx < len(vals):
                col_a = vals[row_idx][0] if len(vals[row_idx]) > 0 else ''
                if col_a.strip():
                    has_fuel_names = True
                    break

        if has_fuel_names:
            print(f'✅ {sheet_name} has fuel type names')
        else:
            print(f'❌ {sheet_name} is MISSING fuel type names in column A')

    # Recommendations
    print('\n' + '='*80)
    print('RECOMMENDATIONS:')
    print('='*80)
    print('1. update_bg_live_dashboard.py should target "Live Dashboard v2"')
    print('2. Fuel data should be written to rows 13-22 (WIND starts at row 13)')
    print('3. Timestamp should be in row 2')
    print('4. Use correct emojis: 🌬️ WIND (not 💨), 🏭 CCGT (not 🔥)')
    print('\nSee FUEL_ROW_MAPPING_REFERENCE.md for complete mapping')

if __name__ == '__main__':
    main()
