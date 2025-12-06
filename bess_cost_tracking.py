#!/usr/bin/env python3
"""
BESS Cost Tracking Automation
Calculates import costs, export revenues, and net position with monthly summaries
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd
import pytz

SHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

# Constants (from BESS sheet configuration)
LEVIES_GBP_PER_MWH = 98.15  # Blended (RO, FiT, CfD, CCL, BSUoS, TNUoS)
PPA_EXPORT_PRICE = 150.00   # £/MWh

# Note: DUoS rates table location changed from gb_power to uk_energy_prod
# Rates are fetched from sheet directly, not from BigQuery duos_unit_rates

def get_bess_config_from_sheet():
    """Read BESS configuration from sheet"""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scope)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SHEET_ID)
    
    try:
        bess_sheet = ss.worksheet('BESS')
        
        # Read DNO and voltage for DUoS lookup
        dno_name = bess_sheet.acell('C6').value
        voltage = bess_sheet.acell('A9').value
        
        # Read DUoS rates if available
        red_rate = float(bess_sheet.acell('B9').value or 0)
        amber_rate = float(bess_sheet.acell('C9').value or 0)
        green_rate = float(bess_sheet.acell('D9').value or 0)
        
        return {
            'dno_name': dno_name,
            'voltage': voltage,
            'duos_red': red_rate,
            'duos_amber': amber_rate,
            'duos_green': green_rate
        }
    except Exception as e:
        print(f'   ⚠️  Error reading BESS config: {e}')
        return None

def calculate_import_costs(start_date, end_date, duos_rates):
    """
    Calculate import costs: wholesale + DUoS + levies
    Returns DataFrame with per-SP costs
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH costs_data AS (
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod as sp,
        systemBuyPrice as wholesale_price,
        -- DUoS band logic
        CASE
          WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1,7) THEN 'GREEN'
          WHEN settlementPeriod BETWEEN 33 AND 39 THEN 'RED'
          WHEN settlementPeriod BETWEEN 17 AND 44 THEN 'AMBER'
          ELSE 'GREEN'
        END as duos_band
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) BETWEEN '{start_date}' AND '{end_date}'
      ORDER BY date, sp
    )
    SELECT 
      date,
      sp,
      wholesale_price,
      duos_band,
      CASE duos_band
        WHEN 'RED' THEN {duos_rates['duos_red']}
        WHEN 'AMBER' THEN {duos_rates['duos_amber']}
        ELSE {duos_rates['duos_green']}
      END as duos_rate,
      {LEVIES_GBP_PER_MWH} as levies_rate,
      wholesale_price + CASE duos_band
        WHEN 'RED' THEN {duos_rates['duos_red']}
        WHEN 'AMBER' THEN {duos_rates['duos_amber']}
        ELSE {duos_rates['duos_green']}
      END + {LEVIES_GBP_PER_MWH} as total_import_cost
    FROM costs_data
    """
    
    df = client.query(query).to_dataframe()
    return df

def calculate_arbitrage_opportunities(df, battery_capacity_mwh=5.0):
    """
    Find arbitrage opportunities: charge when cheap, discharge when expensive
    Simple greedy algorithm
    """
    # Calculate arbitrage spread (export revenue - import cost)
    df['export_revenue_per_mwh'] = PPA_EXPORT_PRICE
    df['arbitrage_spread'] = df['export_revenue_per_mwh'] - df['total_import_cost']
    
    # Daily summary
    daily_summary = df.groupby('date').agg({
        'total_import_cost': ['mean', 'min', 'max'],
        'arbitrage_spread': ['mean', 'max'],
        'wholesale_price': 'mean',
        'duos_rate': 'mean'
    }).round(2)
    
    daily_summary.columns = ['_'.join(col).strip() for col in daily_summary.columns.values]
    
    # Best arbitrage opportunities (top spreads)
    best_opportunities = df.nlargest(10, 'arbitrage_spread')[
        ['date', 'sp', 'wholesale_price', 'duos_band', 'total_import_cost', 'arbitrage_spread']
    ]
    
    return daily_summary, best_opportunities

def create_monthly_summary(df):
    """Create monthly cost and revenue summary"""
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
    
    monthly = df.groupby('month').agg({
        'total_import_cost': 'mean',
        'wholesale_price': 'mean',
        'duos_rate': 'mean',
        'date': 'count'  # Number of settlement periods
    }).round(2)
    
    monthly.columns = ['avg_import_cost_gbp_mwh', 'avg_wholesale_gbp_mwh', 
                       'avg_duos_gbp_mwh', 'settlement_periods']
    
    monthly['avg_levies_gbp_mwh'] = LEVIES_GBP_PER_MWH
    monthly['export_revenue_gbp_mwh'] = PPA_EXPORT_PRICE
    monthly['arbitrage_margin_gbp_mwh'] = (
        monthly['export_revenue_gbp_mwh'] - monthly['avg_import_cost_gbp_mwh']
    )
    
    return monthly

def write_to_bess_cost_tracker_sheet(daily_summary, monthly_summary, best_opportunities):
    """Write cost tracking data to new BESS_Cost_Tracker sheet"""
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scope)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SHEET_ID)
    
    # Create or get cost tracker sheet
    try:
        cost_sheet = ss.worksheet('BESS_Cost_Tracker')
        cost_sheet.clear()
    except:
        cost_sheet = ss.add_worksheet('BESS_Cost_Tracker', rows=1000, cols=20)
    
    # Write daily summary
    cost_sheet.update(values=[['DAILY COST SUMMARY']], range_name='A1')
    cost_sheet.update(values=[['Last Updated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]], range_name='A2')
    
    daily_data = [['Date'] + list(daily_summary.columns)]
    for date, row in daily_summary.reset_index().iterrows():
        daily_data.append([str(row['date'])] + [str(v) for v in row[1:]])
    
    cost_sheet.update(values=daily_data, range_name='A4')
    
    # Write monthly summary
    monthly_start_row = len(daily_data) + 7
    cost_sheet.update(values=[['MONTHLY SUMMARY']], range_name=f'A{monthly_start_row}')
    
    monthly_data = [['Month'] + list(monthly_summary.columns)]
    for month, row in monthly_summary.reset_index().iterrows():
        monthly_data.append([str(row['month'])] + [str(v) for v in row[1:]])
    
    cost_sheet.update(values=monthly_data, range_name=f'A{monthly_start_row + 1}')
    
    # Write best opportunities
    opp_start_row = monthly_start_row + len(monthly_data) + 4
    cost_sheet.update(values=[['TOP 10 ARBITRAGE OPPORTUNITIES']], range_name=f'A{opp_start_row}')
    
    opp_data = [['Date', 'SP', 'Wholesale', 'DUoS Band', 'Import Cost', 'Spread']]
    for _, row in best_opportunities.iterrows():
        opp_data.append([
            str(row['date']),
            int(row['sp']),
            f"£{row['wholesale_price']:.2f}",
            row['duos_band'],
            f"£{row['total_import_cost']:.2f}",
            f"£{row['arbitrage_spread']:.2f}"
        ])
    
    cost_sheet.update(values=opp_data, range_name=f'A{opp_start_row + 1}')
    
    # Format headers
    cost_sheet.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})
    cost_sheet.format('A4:Z4', {'textFormat': {'bold': True}, 
                                 'backgroundColor': {'red': 0.81, 'green': 0.89, 'blue': 0.95}})
    cost_sheet.format(f'A{monthly_start_row}', {'textFormat': {'bold': True, 'fontSize': 14}})
    cost_sheet.format(f'A{opp_start_row}', {'textFormat': {'bold': True, 'fontSize': 14}})

def main():
    print('\n💰 BESS COST TRACKING AUTOMATION')
    print('='*80)
    
    # Get BESS config
    print('\n📋 Reading BESS configuration...')
    config = get_bess_config_from_sheet()
    
    if not config:
        print('   ❌ Could not read BESS configuration')
        return
    
    print(f'   DNO: {config["dno_name"]}')
    print(f'   Voltage: {config["voltage"]}')
    print(f'   DUoS Rates: RED={config["duos_red"]:.3f}, AMBER={config["duos_amber"]:.3f}, GREEN={config["duos_green"]:.3f} p/kWh')
    
    # Calculate costs for last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    print(f'\n📊 Calculating costs from {start_date} to {end_date}...')
    
    df = calculate_import_costs(start_date, end_date, config)
    
    if df.empty:
        print('   ❌ No cost data available')
        return
    
    print(f'   ✅ Retrieved {len(df)} settlement periods')
    
    # Calculate arbitrage
    print('\n💡 Analyzing arbitrage opportunities...')
    daily_summary, best_opportunities = calculate_arbitrage_opportunities(df)
    
    print(f'   Average import cost: £{df["total_import_cost"].mean():.2f}/MWh')
    print(f'   Average arbitrage spread: £{df["arbitrage_spread"].mean():.2f}/MWh')
    print(f'   Best opportunity: £{best_opportunities.iloc[0]["arbitrage_spread"]:.2f}/MWh')
    
    # Monthly summary
    print('\n📅 Creating monthly summary...')
    monthly_summary = create_monthly_summary(df)
    print(f'   Months analyzed: {len(monthly_summary)}')
    
    # Write to sheets
    print('\n📝 Writing to BESS_Cost_Tracker sheet...')
    write_to_bess_cost_tracker_sheet(daily_summary, monthly_summary, best_opportunities)
    
    print(f'\n✅ Cost tracking complete!')
    print(f'🔗 View dashboard: https://docs.google.com/spreadsheets/d/{SHEET_ID}/')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
