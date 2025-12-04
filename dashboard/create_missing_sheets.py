#!/usr/bin/env python3
"""
Create missing sheets for Dashboard V3
Adds: Chart Data, VLP_Data, ESO_Actions, Audit
"""

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'inner-cinema-credentials.json'


def get_client():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def create_missing_sheets():
    gc = get_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    
    print('🔧 Creating Missing Sheets for Dashboard V3')
    print('=' * 70)
    
    # Define sheets to create
    sheets_config = [
        {
            'name': 'Chart Data',
            'rows': 100,
            'cols': 10,
            'headers': [
                'Time/SP', 'DA Price (£/MWh)', 'Imbalance Price (£/MWh)',
                'Demand (MW)', 'Generation (MW)', 'IC Flow (MW)',
                'BM Actions (MW)', 'VLP Revenue (£k)', 'Overlay 1', 'Overlay 2'
            ]
        },
        {
            'name': 'VLP_Data',
            'rows': 1000,
            'cols': 15,
            'headers': [
                'settlementDate', 'settlementPeriod', 'duos_band', 'trading_signal',
                'net_margin_per_mwh', 'ppa_discharge_revenue', 'dc_revenue',
                'dm_revenue', 'cm_revenue', 'bm_revenue', 'triad_revenue',
                'negative_pricing', 'paid_to_charge_amount', 'total_cost', 'ssp_charge'
            ]
        },
        {
            'name': 'ESO_Actions',
            'rows': 500,
            'cols': 8,
            'headers': [
                'bmUnitId', 'acceptanceNumber', 'acceptanceTime', 'volume',
                'cashflowAmount', 'action_type', 'settlementDate', 'settlementPeriod'
            ]
        },
        {
            'name': 'Audit',
            'rows': 500,
            'cols': 5,
            'headers': ['Action', 'Timestamp', 'User/Source', 'Status', 'Error']
        }
    ]
    
    existing_sheets = [ws.title for ws in ss.worksheets()]
    
    for config in sheets_config:
        sheet_name = config['name']
        
        if sheet_name in existing_sheets:
            print(f'⏭️  {sheet_name}: Already exists, skipping')
            continue
        
        try:
            # Create sheet
            worksheet = ss.add_worksheet(
                title=sheet_name,
                rows=config['rows'],
                cols=config['cols']
            )
            
            # Add headers
            if config['headers']:
                worksheet.update(values=[config['headers']], range_name='A1')
            
            print(f'✅ {sheet_name}: Created with {config["cols"]} columns, {config["rows"]} rows')
            
        except Exception as e:
            print(f'❌ {sheet_name}: Error - {e}')
    
    print('\n✅ Sheet creation complete')


if __name__ == '__main__':
    create_missing_sheets()
