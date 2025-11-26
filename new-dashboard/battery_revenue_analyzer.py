#!/usr/bin/env python3
"""
Battery Revenue Opportunity Analyzer
Analyzes BOALF acceptances matched with MID prices for battery arbitrage opportunities
Data Coverage: Jan 2022 - Present (3.9+ years)
"""

import logging
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('logs/battery_revenue_analyzer.log'),
        logging.StreamHandler()
    ]
)

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
CREDS_FILE = "/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json"

# Battery BM Units (VLP units)
BATTERY_UNITS = [
    'FBPGM002', 'FFSEN005',  # Major VLP batteries
    '2__FBPGM001', '2__FFSEN001',  # Alternative IDs
    '2__DSTAT002', '2__DSTAT004', '2__GSTAT011',  # D/G STAT units
    '2__HANGE001', '2__HANGE002', '2__HANGE004',  # Hangar battery
    '2__MSTAT001', '2__NFLEX001',  # M/N STAT units
    '2__HLOND002', '2__LANGE002'   # Additional batteries
]

def connect_bigquery():
    """Connect to BigQuery"""
    creds = Credentials.from_service_account_file(CREDS_FILE)
    client = bigquery.Client(project=PROJECT_ID, location="US", credentials=creds)
    logging.info("✅ Connected to BigQuery")
    return client

def connect_sheets():
    """Connect to Google Sheets"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    logging.info("✅ Connected to Google Sheets")
    return spreadsheet

def analyze_battery_acceptances_today(bq_client):
    """
    Analyze today's battery acceptances with price matching
    Returns: DataFrame with acceptance details + matched prices
    """
    query = f"""
    WITH todays_acceptances AS (
      SELECT 
        settlementDate,
        settlementPeriodFrom,
        bmUnit,
        acceptanceNumber,
        acceptanceTime,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as volume_mw,
        soFlag,
        storFlag,
        rrFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND bmUnit IN UNNEST(@battery_units)
      ORDER BY acceptanceTime DESC
    ),
    matched_prices AS (
      SELECT 
        a.*,
        m.price as market_price,
        m.volume as market_volume,
        -- Calculate estimated revenue (simplified: use market price)
        CASE 
          WHEN a.volume_mw > 0 THEN a.volume_mw * m.price / 2  -- Discharge (sell at market price)
          WHEN a.volume_mw < 0 THEN ABS(a.volume_mw) * m.price / 2  -- Charge (buy at market price)
          ELSE 0
        END as estimated_revenue
      FROM todays_acceptances a
      LEFT JOIN `{PROJECT_ID}.{DATASET}.bmrs_mid_iris` m
        ON CAST(a.settlementDate AS DATE) = CAST(m.settlementDate AS DATE)
        AND a.settlementPeriodFrom = m.settlementPeriod
    )
    SELECT * FROM matched_prices
    ORDER BY acceptanceTime DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("battery_units", "STRING", BATTERY_UNITS)
        ]
    )
    
    df = bq_client.query(query, job_config=job_config).to_dataframe()
    logging.info(f"📊 Retrieved {len(df)} battery acceptances today")
    
    return df

def analyze_historical_battery_revenue(bq_client, days_back=30):
    """
    Analyze historical battery revenue opportunities
    Args:
        days_back: Number of days to analyze (default 30, max ~1400 days available)
    Returns: DataFrame with daily aggregated revenue metrics
    """
    query = f"""
    WITH battery_acceptances AS (
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriodFrom as period,
        bmUnit,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as volume_mw,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
        AND bmUnit IN UNNEST(@battery_units)
    ),
    prices AS (
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod as period,
        systemSellPrice,
        systemBuyPrice,
        imbalancePriceAmount
      FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
    ),
    matched_data AS (
      SELECT 
        a.*,
        p.systemSellPrice,
        p.systemBuyPrice,
        p.imbalancePriceAmount,
        -- Calculate revenue per acceptance
        CASE 
          WHEN a.volume_mw > 0 THEN a.volume_mw * p.systemSellPrice / 2  -- Discharge
          WHEN a.volume_mw < 0 THEN ABS(a.volume_mw) * p.systemBuyPrice / 2  -- Charge
          ELSE 0
        END as revenue_gbp
      FROM battery_acceptances a
      LEFT JOIN prices p USING (date, period)
    ),
    daily_summary AS (
      SELECT 
        date,
        COUNT(DISTINCT bmUnit) as active_batteries,
        COUNT(*) as total_acceptances,
        SUM(CASE WHEN volume_mw > 0 THEN 1 ELSE 0 END) as discharge_actions,
        SUM(CASE WHEN volume_mw < 0 THEN 1 ELSE 0 END) as charge_actions,
        SUM(ABS(volume_mw)) as total_volume_mw,
        AVG(systemSellPrice) as avg_sell_price,
        AVG(systemBuyPrice) as avg_buy_price,
        SUM(revenue_gbp) as estimated_daily_revenue,
        SUM(CASE WHEN soFlag THEN 1 ELSE 0 END) as so_flag_count
      FROM matched_data
      GROUP BY date
      ORDER BY date DESC
    )
    SELECT * FROM daily_summary
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("days_back", "INT64", days_back),
            bigquery.ArrayQueryParameter("battery_units", "STRING", BATTERY_UNITS)
        ]
    )
    
    df = bq_client.query(query, job_config=job_config).to_dataframe()
    logging.info(f"📊 Retrieved {len(df)} days of historical battery revenue data")
    
    return df

def analyze_unit_performance(bq_client, days_back=30):
    """
    Analyze performance by individual battery unit
    Returns: DataFrame with per-unit metrics
    """
    query = f"""
    WITH battery_acceptances AS (
      SELECT 
        bmUnit,
        settlementDate,
        settlementPeriodFrom as period,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as volume_mw,
        acceptanceTime,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
        AND bmUnit IN UNNEST(@battery_units)
      
      UNION ALL
      
      SELECT 
        bmUnit,
        settlementDate,
        settlementPeriodFrom as period,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as volume_mw,
        acceptanceTime,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
        AND bmUnit IN UNNEST(@battery_units)
    ),
    unit_summary AS (
      SELECT 
        bmUnit,
        COUNT(*) as total_acceptances,
        MIN(CAST(settlementDate AS DATE)) as first_acceptance,
        MAX(CAST(settlementDate AS DATE)) as last_acceptance,
        SUM(CASE WHEN volume_mw > 0 THEN 1 ELSE 0 END) as discharge_count,
        SUM(CASE WHEN volume_mw < 0 THEN 1 ELSE 0 END) as charge_count,
        AVG(ABS(volume_mw)) as avg_volume_mw,
        MAX(ABS(volume_mw)) as max_volume_mw,
        SUM(CASE WHEN soFlag THEN 1 ELSE 0 END) as so_instructions
      FROM battery_acceptances
      GROUP BY bmUnit
      ORDER BY total_acceptances DESC
    )
    SELECT * FROM unit_summary
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("days_back", "INT64", days_back),
            bigquery.ArrayQueryParameter("battery_units", "STRING", BATTERY_UNITS)
        ]
    )
    
    df = bq_client.query(query, job_config=job_config).to_dataframe()
    logging.info(f"📊 Retrieved performance data for {len(df)} battery units")
    
    return df

def create_battery_analysis_sheet(spreadsheet):
    """
    Create or update 'Battery Revenue Analysis' sheet with dropdowns
    """
    try:
        sheet = spreadsheet.worksheet('Battery Revenue Analysis')
        logging.info("Sheet already exists, will update...")
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(
            title='Battery Revenue Analysis',
            rows=500,
            cols=20
        )
        logging.info("✅ Created new 'Battery Revenue Analysis' sheet")
    
    return sheet

def update_battery_analysis_sheet(sheet, todays_data, historical_data, unit_performance):
    """
    Update Battery Revenue Analysis sheet with latest data
    """
    # Header
    sheet.update('A1', [['BATTERY REVENUE OPPORTUNITY ANALYSIS']])
    sheet.format('A1', {
        'textFormat': {'fontSize': 16, 'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    
    # Timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.update('A2', [[f'Last Updated: {timestamp}']])
    
    # Summary metrics (K6:L10)
    if len(todays_data) > 0:
        total_revenue_today = todays_data['estimated_revenue'].sum()
        avg_price_today = (todays_data['systemSellPrice'].mean() + todays_data['systemBuyPrice'].mean()) / 2
        total_volume_today = todays_data['volume_mw'].abs().sum()
    else:
        total_revenue_today = 0
        avg_price_today = 0
        total_volume_today = 0
    
    if len(historical_data) > 0:
        avg_daily_revenue = historical_data['estimated_daily_revenue'].mean()
        total_30d_revenue = historical_data['estimated_daily_revenue'].sum()
    else:
        avg_daily_revenue = 0
        total_30d_revenue = 0
    
    summary_labels = [
        ['Today\'s Revenue:'],
        ['Today\'s Volume:'],
        ['Avg Price Today:'],
        ['30-Day Revenue:'],
        ['Avg Daily Revenue:']
    ]
    
    summary_values = [
        [f'£{total_revenue_today:,.0f}'],
        [f'{total_volume_today:,.0f} MW'],
        [f'£{avg_price_today:.2f}/MWh'],
        [f'£{total_30d_revenue:,.0f}'],
        [f'£{avg_daily_revenue:,.0f}']
    ]
    
    sheet.update('J6:J10', summary_labels)
    sheet.update('K6:K10', summary_values)
    
    # Format summary
    sheet.format('J6:J10', {'textFormat': {'bold': True}, 'horizontalAlignment': 'RIGHT'})
    sheet.format('K6:K10', {'textFormat': {'fontSize': 12}, 'horizontalAlignment': 'LEFT'})
    
    # Today's acceptances table (A5:L5 + data starting A6)
    headers_today = [[
        'Time', 'BM Unit', 'Period', 'Level From', 'Level To', 'Volume (MW)',
        'Sell Price', 'Buy Price', 'Revenue £', 'SO Flag', 'STOR', 'RR'
    ]]
    sheet.update('A5:L5', headers_today)
    
    if len(todays_data) > 0:
        today_table = []
        for _, row in todays_data.iterrows():
            today_table.append([
                row['acceptanceTime'].strftime('%H:%M:%S'),
                row['bmUnit'],
                int(row['settlementPeriodFrom']),
                round(row['levelFrom'], 1),
                round(row['levelTo'], 1),
                round(row['volume_mw'], 1),
                round(row['systemSellPrice'], 2) if pd.notna(row['systemSellPrice']) else 0,
                round(row['systemBuyPrice'], 2) if pd.notna(row['systemBuyPrice']) else 0,
                round(row['estimated_revenue'], 2),
                'Yes' if row['soFlag'] else 'No',
                'Yes' if row['storFlag'] else 'No',
                'Yes' if row['rrFlag'] else 'No'
            ])
        
        end_row = 5 + len(today_table)
        sheet.update(f'A6:L{end_row}', today_table)
        logging.info(f"✅ Updated {len(today_table)} today's acceptances")
    
    # Historical trend (starting row 25)
    sheet.update('A25', [['HISTORICAL REVENUE TREND (Last 30 Days)']])
    sheet.format('A25', {'textFormat': {'bold': True, 'fontSize': 12}})
    
    headers_historical = [[
        'Date', 'Active Batteries', 'Acceptances', 'Discharge Actions', 'Charge Actions',
        'Volume (MW)', 'Avg Sell Price', 'Avg Buy Price', 'Daily Revenue £', 'SO Instructions'
    ]]
    sheet.update('A26:J26', headers_historical)
    
    if len(historical_data) > 0:
        hist_table = []
        for _, row in historical_data.iterrows():
            hist_table.append([
                row['date'].strftime('%Y-%m-%d'),
                int(row['active_batteries']),
                int(row['total_acceptances']),
                int(row['discharge_actions']),
                int(row['charge_actions']),
                round(row['total_volume_mw'], 0),
                round(row['avg_sell_price'], 2) if pd.notna(row['avg_sell_price']) else 0,
                round(row['avg_buy_price'], 2) if pd.notna(row['avg_buy_price']) else 0,
                round(row['estimated_daily_revenue'], 2),
                int(row['so_flag_count'])
            ])
        
        end_row_hist = 26 + len(hist_table)
        sheet.update(f'A27:J{end_row_hist}', hist_table)
        logging.info(f"✅ Updated {len(hist_table)} historical trend rows")
    
    # Unit performance (starting M6)
    sheet.update('M5', [['UNIT PERFORMANCE (Last 30 Days)']])
    sheet.format('M5', {'textFormat': {'bold': True, 'fontSize': 12}})
    
    headers_units = [[
        'BM Unit', 'Total Acceptances', 'First Seen', 'Last Seen',
        'Discharge Count', 'Charge Count', 'Avg Volume MW', 'Max Volume MW', 'SO Instructions'
    ]]
    sheet.update('M6:U6', headers_units)
    
    if len(unit_performance) > 0:
        units_table = []
        for _, row in unit_performance.iterrows():
            units_table.append([
                row['bmUnit'],
                int(row['total_acceptances']),
                row['first_acceptance'].strftime('%Y-%m-%d'),
                row['last_acceptance'].strftime('%Y-%m-%d'),
                int(row['discharge_count']),
                int(row['charge_count']),
                round(row['avg_volume_mw'], 1),
                round(row['max_volume_mw'], 1),
                int(row['so_instructions'])
            ])
        
        end_row_units = 6 + len(units_table)
        sheet.update(f'M7:U{end_row_units}', units_table)
        logging.info(f"✅ Updated {len(units_table)} unit performance rows")
    
    # Format headers
    sheet.format('A5:L5', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
        'horizontalAlignment': 'CENTER'
    })
    sheet.format('A26:J26', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
        'horizontalAlignment': 'CENTER'
    })
    sheet.format('M6:U6', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
        'horizontalAlignment': 'CENTER'
    })

def main():
    """Main execution function"""
    logging.info("="*80)
    logging.info("🔋 BATTERY REVENUE ANALYZER")
    logging.info("="*80)
    
    try:
        # Connect to services
        bq_client = connect_bigquery()
        spreadsheet = connect_sheets()
        
        # Analyze data
        logging.info("📊 Analyzing today's battery acceptances...")
        todays_data = analyze_battery_acceptances_today(bq_client)
        
        logging.info("📊 Analyzing historical revenue (last 30 days)...")
        historical_data = analyze_historical_battery_revenue(bq_client, days_back=30)
        
        logging.info("📊 Analyzing unit performance...")
        unit_performance = analyze_unit_performance(bq_client, days_back=30)
        
        # Update sheet
        sheet = create_battery_analysis_sheet(spreadsheet)
        update_battery_analysis_sheet(sheet, todays_data, historical_data, unit_performance)
        
        # Log summary
        logging.info("\n" + "="*80)
        logging.info("📈 ANALYSIS SUMMARY:")
        logging.info(f"   Today's acceptances: {len(todays_data)}")
        logging.info(f"   Historical days: {len(historical_data)}")
        logging.info(f"   Active units: {len(unit_performance)}")
        if len(todays_data) > 0:
            logging.info(f"   Today's estimated revenue: £{todays_data['estimated_revenue'].sum():,.0f}")
        if len(historical_data) > 0:
            logging.info(f"   30-day total revenue: £{historical_data['estimated_daily_revenue'].sum():,.0f}")
        logging.info("="*80)
        logging.info("✅ BATTERY REVENUE ANALYSIS COMPLETE")
        logging.info("="*80)
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
