#!/usr/bin/env python3
"""
Direct Google Sheets Update - Three-Tier Battery Revenue Model
Writes Conservative/Base/Best/BTM scenarios to Battery_Revenue_Analysis worksheet
Uses results from battery_revenue_final_20251205_131134.csv
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import os

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
WORKSHEET_NAME = 'Battery_Revenue_Analysis'
RESULTS_FILE = '/home/george/GB-Power-Market-JJ/logs/battery_revenue_final_20251205_131134.csv'

# Google Sheets auth
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = '/home/george/inner-cinema-credentials.json'

def setup_sheets_client():
    """Initialize Google Sheets client"""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def format_currency(value):
    """Format value as £XX,XXX"""
    if pd.isna(value) or value == 0:
        return '£0'
    return f'£{value:,.0f}'

def format_percentage(value):
    """Format value as XX%"""
    if pd.isna(value) or value == 0:
        return '0%'
    return f'{value:.1f}%'

def update_battery_revenue_sheet():
    """Update Google Sheets with three-tier model"""
    
    print("=" * 80)
    print("THREE-TIER BATTERY REVENUE MODEL - GOOGLE SHEETS UPDATE")
    print("=" * 80)
    
    # Check results file exists
    if not os.path.exists(RESULTS_FILE):
        print(f"❌ Results file not found: {RESULTS_FILE}")
        print("Run update_battery_revenue_model_final.py first")
        return
    
    # Load results (simplified CSV format: Scenario, Monthly, Annual, Status)
    print(f"\n📊 Loading results from: {RESULTS_FILE}")
    df = pd.read_csv(RESULTS_FILE)
    print(f"✅ Loaded {len(df)} scenarios")
    print(f"\nScenarios found: {df['Scenario'].tolist()}")
    
    # Extract values
    conservative = df[df['Scenario'] == 'Conservative']['Monthly (£)'].iloc[0]
    base = df[df['Scenario'] == 'Base Case']['Monthly (£)'].iloc[0]
    best = df[df['Scenario'] == 'Best Case']['Monthly (£)'].iloc[0]
    btm = df[df['Scenario'] == 'BTM Case']['Monthly (£)'].iloc[0]
    
    # Hardcoded breakdown values (from update_battery_revenue_model_final.py output)
    arb_net = 122235.50
    vlp_net = 96004.10
    cm_revenue = 67500.00
    fr_revenue = 51000.00
    duos_saving = 75000.00
    
    # Connect to Google Sheets
    print(f"\n🔗 Connecting to Google Sheets...")
    gc = setup_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Get or create Battery_Revenue_Analysis worksheet
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        print(f"✅ Found worksheet: {WORKSHEET_NAME}")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=200, cols=20)
        print(f"✅ Created worksheet: {WORKSHEET_NAME}")
    
    # Clear existing content from row 100 onwards (preserve any existing data above)
    START_ROW = 100
    print(f"\n🧹 Clearing rows {START_ROW}+ to prepare for new data...")
    worksheet.batch_clear([f'A{START_ROW}:Z500'])
    
    # Build output data
    data = []
    current_row = START_ROW
    
    # Header
    data.append([f'THREE-TIER BATTERY REVENUE MODEL - Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
    data.append(['Battery Specification: 50 MWh / 25 MW / 90% Efficiency / 2 Cycles/Day'])
    data.append(['Analysis Period: Nov 5 - Dec 5, 2025 (30 days)'])
    data.append([''])
    
    # Conservative Scenario
    data.append(['═' * 60])
    data.append(['CONSERVATIVE SCENARIO - PROVEN ONLY'])
    data.append(['═' * 60])
    data.append([''])
    
    data.append(['Stream 1: Energy Arbitrage', '✅ PROVEN', format_currency(arb_net)])
    data.append(['  Discharge Revenue:', '', format_currency(153450)])
    data.append(['  Charge Cost:', '', format_currency(66553)])
    data.append(['  Efficiency Loss:', '', '171 MWh (10%)'])
    data.append(['  Net Profit:', '', format_currency(arb_net)])
    data.append([''])
    data.append(['TOTAL CONSERVATIVE:', '', format_currency(conservative)])
    data.append(['Annual Projection:', '', format_currency(conservative * 12)])
    data.append([''])
    
    # Base Scenario
    data.append(['═' * 60])
    data.append(['BASE SCENARIO - ARBITRAGE + VLP + CM'])
    data.append(['═' * 60])
    data.append([''])
    
    data.append(['Stream 1: Energy Arbitrage', '✅ PROVEN', format_currency(arb_net)])
    data.append(['Stream 2: BM via VLP', '⚠️ CONDITIONAL', format_currency(vlp_net)])
    data.append(['  Gross BM Revenue:', '', format_currency(112946)])
    data.append(['  VLP Fee (15%):', '', f'-{format_currency(16942)}'])
    data.append(['  Net BM Revenue:', '', format_currency(vlp_net)])
    data.append(['Stream 4: Capacity Market', '⚠️ CONDITIONAL', format_currency(cm_revenue)])
    data.append(['  De-rated Capacity:', '', '24 MW (96% for 2h battery)'])
    data.append(['  Auction Success Rate:', '', '45%'])
    data.append([''])
    data.append(['TOTAL BASE:', '', format_currency(base)])
    data.append(['Annual Projection:', '', format_currency(base * 12)])
    data.append([''])
    
    # Best Scenario
    data.append(['═' * 60])
    data.append(['BEST SCENARIO - BASE + FREQUENCY RESPONSE'])
    data.append(['═' * 60])
    data.append([''])
    
    data.append(['Stream 1: Energy Arbitrage', '✅ PROVEN', format_currency(arb_net)])
    data.append(['Stream 2: BM via VLP', '⚠️ CONDITIONAL', format_currency(vlp_net)])
    data.append(['Stream 4: Capacity Market', '⚠️ CONDITIONAL', format_currency(cm_revenue)])
    data.append(['Stream 5: Frequency Response', '⚠️ CONDITIONAL', format_currency(fr_revenue)])
    data.append(['  Service:', '', 'Dynamic Containment'])
    data.append(['  Rate:', '', '£17/MW/hour'])
    data.append(['  Utilization:', '', '40% (market adjusted)'])
    data.append([''])
    data.append(['TOTAL BEST:', '', format_currency(best)])
    data.append(['Annual Projection:', '', format_currency(best * 12)])
    data.append([''])
    
    # BTM Scenario
    data.append(['═' * 60])
    data.append(['BTM SCENARIO - BEHIND-THE-METER DEPLOYMENT'])
    data.append(['═' * 60])
    data.append([''])
    
    data.append(['Stream 1: Energy Arbitrage', '✅ PROVEN', format_currency(arb_net)])
    data.append(['Stream 2: BM via VLP', '⚠️ CONDITIONAL', format_currency(vlp_net)])
    data.append(['Stream 3: DUoS Avoidance', '⚠️ BTM ONLY', format_currency(duos_saving)])
    data.append(['  Red Rate:', '', '4.837 p/kWh (UKPN-EPN HV)'])
    data.append(['  Peak Shaving:', '', '16:00-19:30 weekdays'])
    data.append(['Stream 4: Capacity Market', '⚠️ CONDITIONAL', format_currency(cm_revenue)])
    data.append(['Stream 5: Frequency Response', '⚠️ CONDITIONAL', format_currency(fr_revenue)])
    data.append([''])
    data.append(['TOTAL BTM:', '', format_currency(btm)])
    data.append(['Annual Projection:', '', format_currency(btm * 12)])
    data.append([''])
    
    # VLP Route Comparison
    data.append(['═' * 60])
    data.append(['VLP ROUTE ECONOMICS'])
    data.append(['═' * 60])
    data.append([''])
    data.append(['VLP Aggregator Route:'])
    data.append(['  Setup Cost:', '', '£5,000'])
    data.append(['  Monthly Fee:', '', f'{format_currency(16942)} (15% of gross)'])
    data.append(['  Net BM Revenue:', '', format_currency(vlp_net)])
    data.append([''])
    data.append(['Direct BSC Route:'])
    data.append(['  Setup Cost:', '', '£100,000+'])
    data.append(['  Annual Fees:', '', '£35,000'])
    data.append(['  Net BM Revenue:', '', format_currency(112946)])
    data.append([''])
    data.append(['Break-Even Analysis:'])
    data.append(['  Cost Difference:', '', '£95,000 (setup)'])
    data.append(['  Monthly Difference:', '', format_currency(112946 - vlp_net)])
    data.append(['  Break-Even Period:', '', '6.8 months'])
    data.append([''])
    data.append(['RECOMMENDATION: VLP route for first 12 months'])
    data.append([''])
    
    # Key Findings
    data.append(['═' * 60])
    data.append(['KEY FINDINGS'])
    data.append(['═' * 60])
    data.append([''])
    data.append(['1. Only arbitrage is PROVEN (uses complete bmrs_costs historical data)'])
    data.append(['2. BM revenue requires VLP aggregator contract (Limejump, Flexitricity, etc.)'])
    data.append(['3. CM revenue requires T-4 auction win (45% success rate assumed)'])
    data.append(['4. FR revenue requires ESO Dynamic Containment contract'])
    data.append(['5. DUoS only applies to Behind-the-Meter installations'])
    data.append(['6. VLP route saves £95k upfront, break-even in 6.8 months'])
    data.append([''])
    
    # Next Steps
    data.append(['═' * 60])
    data.append(['NEXT STEPS'])
    data.append(['═' * 60])
    data.append([''])
    data.append(['1. Review VLP aggregator options (Limejump, Flexitricity, Kiwi Power)'])
    data.append(['2. Submit CM prequalification for T-4 auction'])
    data.append(['3. Request FR capability assessment from National Grid ESO'])
    data.append(['4. ✅ COMPLETE - Updated Google Sheets with three-tier model'])
    data.append([''])
    
    # Metadata
    data.append(['═' * 60])
    data.append(['METADATA'])
    data.append(['═' * 60])
    data.append([''])
    data.append(['Data Source:', '', 'bmrs_costs (complete Nov 5 - Dec 5, 2025)'])
    data.append(['IRIS Status:', '', 'bmrs_boalf_iris ✅ working, bmrs_costs_iris ❌ not configured'])
    data.append(['Script:', '', 'update_battery_revenue_model_final.py'])
    data.append(['Results:', '', RESULTS_FILE])
    data.append(['Updated:', '', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    
    # Write to Google Sheets
    print(f"\n✍️ Writing {len(data)} rows to {WORKSHEET_NAME} starting at row {START_ROW}...")
    
    # Update in batch (fix deprecated API call)
    cell_range = f'A{START_ROW}:C{START_ROW + len(data) - 1}'
    worksheet.update(values=data, range_name=cell_range, value_input_option='USER_ENTERED')
    
    print(f"✅ Successfully updated {len(data)} rows")
    
    # Apply formatting
    print(f"\n🎨 Applying formatting...")
    
    # Bold headers and scenario titles
    bold_format = {
        'textFormat': {'bold': True, 'fontSize': 11}
    }
    
    header_rows = [START_ROW, START_ROW + 4, START_ROW + 15, START_ROW + 30, START_ROW + 45, START_ROW + 60, START_ROW + 75]
    for row in header_rows:
        worksheet.format(f'A{row}:C{row}', bold_format)
    
    # Currency formatting for column C
    currency_format = {
        'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'}
    }
    worksheet.format(f'C{START_ROW}:C{START_ROW + len(data)}', currency_format)
    
    # Column width adjustment (using batch_update on spreadsheet)
    try:
        spreadsheet.batch_update({
            'requests': [{
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': worksheet.id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 1
                    },
                    'properties': {'pixelSize': 400},
                    'fields': 'pixelSize'
                }
            }]
        })
        print("✅ Column width adjusted")
    except Exception as e:
        print(f"⚠️ Column width adjustment skipped: {e}")
    
    print("✅ Formatting applied")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ DEPLOYMENT COMPLETE")
    print("=" * 80)
    print(f"\nSpreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"Worksheet: {WORKSHEET_NAME}")
    print(f"Rows Updated: {START_ROW} to {START_ROW + len(data) - 1}")
    print(f"\nScenarios Deployed:")
    print(f"  • Conservative: {format_currency(conservative)}/month (PROVEN)")
    print(f"  • Base: {format_currency(base)}/month (+ VLP + CM)")
    print(f"  • Best: {format_currency(best)}/month (+ FR)")
    print(f"  • BTM: {format_currency(btm)}/month (+ DUoS)")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        update_battery_revenue_sheet()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
