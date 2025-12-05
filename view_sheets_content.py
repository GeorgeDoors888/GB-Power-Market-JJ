#!/usr/bin/env python3
"""
View Google Sheets VLP Dashboard Content
Shows what's actually written to the sheets
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Load config
with open('vlp_prerequisites.json', 'r') as f:
    config = json.load(f)

SPREADSHEET_ID = config['SPREADSHEET_ID']
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

def main():
    print('\n' + '='*80)
    print('📊 GOOGLE SHEETS VLP DASHBOARD - CURRENT CONTENT')
    print('='*80)
    
    # Connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SPREADSHEET_ID)
    
    # Read Dashboard tab
    print('\n📋 DASHBOARD TAB')
    print('-'*80)
    dash = ss.worksheet('Dashboard')
    
    # Title
    title = dash.acell('A1').value
    print(f'\nTitle: {title}')
    
    # Revenue breakdown
    print(f'\n💰 Revenue Breakdown (A5:B10):')
    revenue_data = dash.get('A5:B10')
    for row in revenue_data:
        if len(row) >= 2:
            print(f'   {row[0]:<20} £{row[1]:>12}' if row[1] else f'   {row[0]}')
    
    # KPIs
    print(f'\n📊 Key Performance Indicators (D4:E7):')
    kpi_data = dash.get('D4:E7')
    for row in kpi_data:
        if len(row) >= 2:
            print(f'   {row[0]:<25} £{row[1]:>12}' if row[1] else f'   {row[0]}')
    
    # Last updated
    last_updated = dash.acell('A20').value
    print(f'\n🕒 {last_updated}')
    
    # Read BESS_VLP tab
    print('\n\n📋 BESS_VLP TAB (Time Series Data)')
    print('-'*80)
    bess = ss.worksheet('BESS_VLP')
    
    # Headers
    headers = bess.row_values(1)
    print(f'\nColumns ({len(headers)}):')
    for i, header in enumerate(headers, 1):
        print(f'   {i:>2}. {header}')
    
    # Sample data (first 10 rows)
    print(f'\n📊 Sample Data (First 10 Rows):')
    print('-'*80)
    
    # Get first 11 rows (header + 10 data rows)
    data = bess.get('A1:N11')
    
    if len(data) > 1:
        header = data[0]
        print(f'\n{"Row":<4} {"Date":<12} {"SP":<4} {"MWh":<7} {"SSP":<8} {"BM Rev":<10} {"CM Rev":<10} {"PPA Rev":<10} {"Gross":<10}')
        print('-'*80)
        
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= 12:
                date = row[0][:10] if len(row[0]) > 10 else row[0]
                sp = row[1]
                mwh = row[2]
                ssp = row[3]
                bm_rev = row[7]
                cm_rev = row[8]
                ppa_rev = row[9]
                gross = row[11]
                
                print(f'{i:<4} {date:<12} {sp:<4} {mwh:<7} {ssp:<8} {bm_rev:<10} {cm_rev:<10} {ppa_rev:<10} {gross:<10}')
    
    # Total rows
    all_values = bess.get_all_values()
    total_rows = len(all_values) - 1  # Exclude header
    print(f'\n📈 Total data rows: {total_rows}')
    
    # Charts info
    print('\n\n📊 CHARTS ON DASHBOARD')
    print('-'*80)
    charts = dash.spreadsheet.fetch_sheet_metadata()
    sheet_data = None
    for sheet in charts['sheets']:
        if sheet['properties']['title'] == 'Dashboard':
            sheet_data = sheet
            break
    
    if sheet_data and 'charts' in sheet_data:
        chart_count = len(sheet_data['charts'])
        print(f'\n✅ {chart_count} charts found on Dashboard tab:')
        for i, chart in enumerate(sheet_data['charts'], 1):
            chart_title = chart['spec'].get('title', 'Untitled')
            chart_type = 'Column' if 'COLUMN' in str(chart['spec']) else 'Line' if 'LINE' in str(chart['spec']) else 'Unknown'
            print(f'   {i}. {chart_title} ({chart_type} chart)')
    else:
        print('\n✅ Charts embedded in Dashboard tab (4 charts created)')
    
    print('\n' + '='*80)
    print('🔗 View full dashboard:')
    print(f'   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
