#!/usr/bin/env python3
"""
Format VLP Dashboard - Apply currency formatting, conditional formatting, and styling
Part of automated dashboard pipeline: vlp_dashboard_simple.py → THIS SCRIPT → create_vlp_charts.py
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Load config
with open('vlp_prerequisites.json', 'r') as f:
    config = json.load(f)

SPREADSHEET_ID = config['SPREADSHEET_ID']
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

def get_sheets_client():
    """Authorize Google Sheets API"""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
    return gspread.authorize(creds)

def format_dashboard():
    """Apply formatting to Dashboard worksheet"""
    
    print('🎨 Formatting Dashboard worksheet...')
    
    gc = get_sheets_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    dash = ss.worksheet('Dashboard')
    
    # 1. Title formatting (A1)
    dash.format('A1', {
        'textFormat': {'bold': True, 'fontSize': 14},
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })
    
    # 2. Section headers (A3, A4, D4 row)
    dash.format('A3', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.81, 'green': 0.89, 'blue': 0.95}
    })
    
    dash.format('A4:B4', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.81, 'green': 0.89, 'blue': 0.95},
        'horizontalAlignment': 'LEFT'
    })
    
    # 3. Currency formatting for revenue columns (B5:B10)
    dash.format('B5:B10', {
        'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'},
        'horizontalAlignment': 'RIGHT'
    })
    
    # 4. KPI section headers (D4:E4)
    dash.format('D4:E4', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.81, 'green': 0.89, 'blue': 0.95}
    })
    
    # 5. Currency formatting for KPI values (E5:E7)
    dash.format('E5:E7', {
        'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'},
        'horizontalAlignment': 'RIGHT'
    })
    
    # 6. Conditional formatting for negative margins (D5:D7 - if any go negative)
    dash.format('D5:D7', {
        'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'},
        'horizontalAlignment': 'RIGHT'
    })
    
    # 7. Borders for revenue table (A4:B10)
    dash.format('A4:B10', {
        'borders': {
            'top': {'style': 'SOLID', 'width': 2},
            'bottom': {'style': 'SOLID', 'width': 2},
            'left': {'style': 'SOLID', 'width': 2},
            'right': {'style': 'SOLID', 'width': 2}
        }
    })
    
    # 8. Borders for KPI table (D4:E7)
    dash.format('D4:E7', {
        'borders': {
            'top': {'style': 'SOLID', 'width': 2},
            'bottom': {'style': 'SOLID', 'width': 2},
            'left': {'style': 'SOLID', 'width': 2},
            'right': {'style': 'SOLID', 'width': 2}
        }
    })
    
    # 9. Timestamp styling (A20)
    dash.format('A20', {
        'textFormat': {'italic': True, 'fontSize': 9},
        'horizontalAlignment': 'LEFT'
    })
    
    # 10. Freeze header rows
    dash.freeze(rows=4)
    
    print('   ✅ Dashboard formatted')

def format_bess_vlp():
    """Apply formatting to BESS_VLP time series worksheet"""
    
    print('🎨 Formatting BESS_VLP worksheet...')
    
    gc = get_sheets_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    bess = ss.worksheet('BESS_VLP')
    
    # 1. Header row (row 1)
    bess.format('1:1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.81, 'green': 0.89, 'blue': 0.95},
        'horizontalAlignment': 'CENTER'
    })
    
    # 2. Date column (A) - left align
    bess.format('A:A', {
        'horizontalAlignment': 'LEFT'
    })
    
    # 3. Currency columns (H:K for r_bm_gbp, r_cm_gbp, r_ppa_gbp, r_avoided_import_gbp)
    # Column H = r_bm_gbp, I = r_cm_gbp, J = r_ppa_gbp, K = r_avoided_import_gbp
    bess.format('H:K', {
        'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'},
        'horizontalAlignment': 'RIGHT'
    })
    
    # 4. Gross margin column (L = gross_margin_sp)
    bess.format('L:L', {
        'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'},
        'horizontalAlignment': 'RIGHT'
    })
    
    # 5. SoC columns (M:N = soc_start, soc_end) - 2 decimal places
    bess.format('M:N', {
        'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'},
        'horizontalAlignment': 'RIGHT'
    })
    
    # 6. Freeze header row
    bess.freeze(rows=1)
    
    print('   ✅ BESS_VLP formatted')

def main():
    """Apply all formatting"""
    
    print('🎨 VLP DASHBOARD FORMATTING')
    print('=' * 60)
    
    format_dashboard()
    format_bess_vlp()
    
    print(f'\n✅ COMPLETE! Formatting applied to Dashboard and BESS_VLP sheets')
    print(f'   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/')

if __name__ == '__main__':
    main()
