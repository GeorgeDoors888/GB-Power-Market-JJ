#!/usr/bin/env python3
"""
VLP Revenue Dashboard - Python Data Refresh Script
Queries BigQuery and updates Google Sheets with latest VLP revenue data
"""

import os
import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
VIEW_NAME = 'v_btm_bess_inputs'
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
SHEET_NAME = 'VLP Revenue'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

# Initialize clients
def get_clients():
    """Initialize BigQuery and Sheets clients"""
    # BigQuery client
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')
    
    # Sheets client
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    sheets_client = gspread.authorize(creds)
    
    return bq_client, sheets_client

def query_latest_vlp_data(bq_client):
    """Get latest VLP revenue data from BigQuery"""
    query = f"""
    SELECT 
      settlementDate,
      settlementPeriod,
      ts_halfhour,
      duos_band,
      ssp_charge as market_price,
      bm_revenue_per_mwh,
      dc_revenue_per_mwh,
      dm_revenue_per_mwh,
      dr_revenue_per_mwh,
      cm_revenue_per_mwh,
      triad_value_per_mwh,
      ppa_price,
      total_stacked_revenue_per_mwh,
      total_cost_per_mwh,
      net_margin_per_mwh,
      trading_signal,
      negative_pricing
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 1
    """
    
    result = bq_client.query(query).to_dataframe()
    if len(result) > 0:
        return result.iloc[0].to_dict()
    return None

def query_48_period_forecast(bq_client):
    """Get 48-period forecast data"""
    query = f"""
    SELECT 
      settlementDate,
      settlementPeriod,
      duos_band,
      ssp_charge as market_price,
      total_stacked_revenue_per_mwh as total_revenue,
      total_cost_per_mwh as total_cost,
      net_margin_per_mwh as profit,
      trading_signal
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 48
    """
    
    return bq_client.query(query).to_dataframe()

def query_profit_by_band(bq_client):
    """Get profit analysis by DUoS band"""
    query = f"""
    SELECT 
      duos_band,
      AVG(net_margin_per_mwh) as avg_profit,
      MIN(net_margin_per_mwh) as min_profit,
      MAX(net_margin_per_mwh) as max_profit,
      COUNT(*) as period_count
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY duos_band
    ORDER BY 
      CASE duos_band 
        WHEN 'GREEN' THEN 1 
        WHEN 'AMBER' THEN 2 
        WHEN 'RED' THEN 3 
      END
    """
    
    return bq_client.query(query).to_dataframe()

def update_live_ticker(sheet, latest_data):
    """Update the live ticker at top of sheet"""
    if not latest_data:
        sheet.update('A1', '⚠️ DATA UNAVAILABLE - Check IRIS feed')
        return
    
    profit = latest_data['net_margin_per_mwh']
    profit_icon = '🟢' if profit > 150 else '🟡' if profit > 100 else '🔴'
    
    ticker_text = (
        f"{profit_icon} LIVE: {latest_data['duos_band']} | "
        f"Market £{latest_data['market_price']:.2f} | "
        f"Revenue £{latest_data['total_stacked_revenue_per_mwh']:.2f} | "
        f"Profit £{profit:.2f}/MWh | "
        f"Signal: {latest_data['trading_signal']} | "
        f"{datetime.now().strftime('%H:%M:%S')}"
    )
    
    sheet.update('A1', ticker_text)
    print(f"✅ Updated live ticker: Profit £{profit:.2f}/MWh")

def update_current_period(sheet, latest_data):
    """Update current period summary section"""
    if not latest_data:
        return
    
    values = [
        [str(latest_data['settlementDate'])],
        [int(latest_data['settlementPeriod'])],
        [str(latest_data['ts_halfhour'])],
        [latest_data['duos_band']],
        [float(latest_data['market_price'])],
        [float(latest_data['total_stacked_revenue_per_mwh'])],
        [float(latest_data['total_cost_per_mwh'])],
        [float(latest_data['net_margin_per_mwh'])],
        [latest_data['trading_signal']]
    ]
    
    sheet.update('B6:B14', values)
    print(f"✅ Updated current period: {latest_data['settlementDate']} Period {latest_data['settlementPeriod']}")

def update_service_breakdown(sheet, latest_data):
    """Update service breakdown section"""
    if not latest_data:
        return
    
    services = {
        'PPA Discharge': float(latest_data.get('ppa_price', 150.0)),
        'DC': float(latest_data.get('dc_revenue_per_mwh', 78.75)),
        'DM': float(latest_data.get('dm_revenue_per_mwh', 40.29)),
        'DR': float(latest_data.get('dr_revenue_per_mwh', 60.44)),
        'CM': float(latest_data.get('cm_revenue_per_mwh', 12.59)),
        'BM': float(latest_data.get('bm_revenue_per_mwh', 0.0)),
        'Triad': float(latest_data.get('triad_value_per_mwh', 0.0)),
        'Negative': float(latest_data.get('market_price', 0.0)) if latest_data.get('negative_pricing') else 0.0
    }
    
    total = sum(services.values())
    
    values = []
    for service, value in services.items():
        pct = (value / total * 100) if total > 0 else 0
        annual = value * 2482  # Annual MWh discharged
        status = '✅' if value > 0 else '⏸️'
        values.append([value, pct, annual, status])
    
    sheet.update('B19:E26', values)
    
    # Update total
    sheet.update('B27', [[total]])
    sheet.update('D27', [[total * 2482]])
    
    print(f"✅ Updated service breakdown: Total £{total:.2f}/MWh")

def update_stacking_scenarios(sheet):
    """Update stacking scenarios table"""
    scenarios = [
        ['DC + CM + PPA', 599008, 241.34, 121.34, '✅'],
        ['DC + DM + CM + PPA + BM', 749008, 301.78, 181.78, '🟡'],
        ['DC + DM + DR + CM + PPA + BM + TRIAD', 999008, 402.50, 282.50, '⚠️'],
        ['DC + CM + PPA + Negative Pricing', 624008, 251.41, 131.41, '✅']
    ]
    
    sheet.update('B32:F35', scenarios)
    print(f"✅ Updated stacking scenarios")

def update_profit_analysis(sheet, profit_df):
    """Update profit analysis by DUoS band"""
    if profit_df.empty:
        return
    
    values = []
    for _, row in profit_df.iterrows():
        values.append([
            float(row['avg_profit']),
            float(row['min_profit']),
            float(row['max_profit'])
        ])
    
    if values:
        sheet.update('L20:N22', values)
        print(f"✅ Updated profit analysis: {len(values)} bands")

def main():
    """Main refresh workflow"""
    print(f"\n{'='*60}")
    print(f"VLP Revenue Dashboard Refresh - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # Initialize clients
        print("🔌 Connecting to BigQuery and Google Sheets...")
        bq_client, sheets_client = get_clients()
        
        # Open spreadsheet
        spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
        
        # Check if VLP Revenue sheet exists
        try:
            sheet = spreadsheet.worksheet(SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            print(f"⚠️ Sheet '{SHEET_NAME}' not found. Creating...")
            sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=100, cols=26)
        
        print(f"✅ Connected to spreadsheet: {spreadsheet.title}")
        
        # Query latest data
        print("\n📊 Querying BigQuery for latest VLP data...")
        latest_data = query_latest_vlp_data(bq_client)
        
        if not latest_data:
            print("❌ No data returned from BigQuery!")
            sys.exit(1)
        
        print(f"✅ Retrieved data for {latest_data['settlementDate']} Period {latest_data['settlementPeriod']}")
        
        # Query forecast data
        print("\n📈 Querying 48-period forecast...")
        forecast_df = query_48_period_forecast(bq_client)
        print(f"✅ Retrieved {len(forecast_df)} periods")
        
        # Query profit analysis
        print("\n💰 Querying profit by DUoS band...")
        profit_df = query_profit_by_band(bq_client)
        print(f"✅ Retrieved profit data for {len(profit_df)} bands")
        
        # Update sheet sections
        print("\n📝 Updating Google Sheets...")
        update_live_ticker(sheet, latest_data)
        update_current_period(sheet, latest_data)
        update_service_breakdown(sheet, latest_data)
        update_stacking_scenarios(sheet)
        update_profit_analysis(sheet, profit_df)
        
        # Update timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sheet.update('A99', f"Last Updated: {timestamp}")
        
        print(f"\n{'='*60}")
        print(f"✅ VLP Dashboard refresh complete!")
        print(f"{'='*60}\n")
        
        # Summary
        print("📊 Summary:")
        print(f"  • Market Price: £{latest_data['market_price']:.2f}/MWh")
        print(f"  • Total Revenue: £{latest_data['total_stacked_revenue_per_mwh']:.2f}/MWh")
        print(f"  • Net Profit: £{latest_data['net_margin_per_mwh']:.2f}/MWh")
        print(f"  • Trading Signal: {latest_data['trading_signal']}")
        print(f"  • DUoS Band: {latest_data['duos_band']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
