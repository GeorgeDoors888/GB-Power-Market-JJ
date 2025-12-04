#!/usr/bin/env python3
"""
VLP Revenue Dashboard - Python + Google Sheets API
Reads BigQuery data and writes to Google Sheets with formatting
Much more powerful than Apps Script for large datasets
"""

import os
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials
import time

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
VIEW_NAME = 'v_btm_bess_inputs'
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Color schemes
COLORS = {
    'header_bg': {'red': 0.0, 'green': 0.4, 'blue': 0.6},      # Dark blue
    'profit_high': {'red': 0.0, 'green': 0.6, 'blue': 0.0},    # Green
    'profit_med': {'red': 1.0, 'green': 0.6, 'blue': 0.0},     # Orange
    'profit_low': {'red': 0.8, 'green': 0.0, 'blue': 0.0},     # Red
    'ticker_bg': {'red': 0.2, 'green': 0.3, 'blue': 0.4},      # Gray-blue
    'white': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
    'light_gray': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
}

def get_bigquery_client():
    """Initialize BigQuery client"""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/bigquery']
    )
    return bigquery.Client(
        project=PROJECT_ID,
        location='US',
        credentials=creds
    )

def get_sheets_client():
    """Initialize Google Sheets client"""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )
    return gspread.authorize(creds)

def query_current_period():
    """Get current settlement period data from BigQuery"""
    client = get_bigquery_client()
    
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        ts_halfhour,
        duos_band,
        ROUND(ssp_charge, 2) as market_price,
        ROUND(bm_revenue_per_mwh, 2) as bm_revenue,
        bm_acceptance_count,
        ROUND(dc_revenue_per_mwh, 2) as dc_revenue,
        ROUND(dm_revenue_per_mwh, 2) as dm_revenue,
        ROUND(dr_revenue_per_mwh, 2) as dr_revenue,
        ROUND(cm_revenue_per_mwh, 2) as cm_revenue,
        ROUND(triad_value_per_mwh, 2) as triad_revenue,
        negative_pricing,
        ROUND(paid_to_charge_amount, 2) as negative_price_value,
        ppa_price,
        ROUND(total_stacked_revenue_per_mwh, 2) as total_revenue,
        ROUND(duos_charge, 2) as duos_cost,
        ROUND(levies_per_mwh, 2) as levies,
        ROUND(total_cost_per_mwh, 2) as total_cost,
        ROUND(net_margin_per_mwh, 2) as profit,
        trading_signal,
        high_stress_period
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= CURRENT_DATE() - 1
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 1
    """
    
    result = client.query(query).to_dataframe()
    return result.iloc[0] if len(result) > 0 else None

def query_recent_periods(hours=24):
    """Get recent periods for trend analysis"""
    client = get_bigquery_client()
    
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        duos_band,
        ROUND(ssp_charge, 2) as market_price,
        ROUND(total_stacked_revenue_per_mwh, 2) as total_revenue,
        ROUND(total_cost_per_mwh, 2) as total_cost,
        ROUND(net_margin_per_mwh, 2) as profit,
        trading_signal
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= CURRENT_DATE() - 2
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT {hours * 2}
    """
    
    return client.query(query).to_dataframe()

def query_service_breakdown():
    """Get service-by-service breakdown"""
    client = get_bigquery_client()
    
    query = f"""
    WITH latest AS (
      SELECT * FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
      WHERE settlementDate >= CURRENT_DATE() - 1
      ORDER BY settlementDate DESC, settlementPeriod DESC
      LIMIT 1
    ),
    recent AS (
      SELECT 
        AVG(bm_revenue_per_mwh) as bm_avg,
        AVG(bm_acceptance_count) as bm_count,
        AVG(triad_value_per_mwh) as triad_avg,
        AVG(paid_to_charge_amount) as neg_avg
      FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
      WHERE settlementDate >= CURRENT_DATE() - 7
    )
    SELECT 'PPA' as service,
           ppa_price as revenue_per_mwh,
           ROUND(ppa_price * 2482 / 1000, 0) as annual_revenue_k,
           '✅' as status,
           'Power Purchase Agreement' as description
    FROM latest
    
    UNION ALL
    
    SELECT 'DC' as service,
           ROUND(dc_revenue_per_mwh, 2) as revenue_per_mwh,
           ROUND(dc_annual_revenue / 1000, 0) as annual_revenue_k,
           '✅' as status,
           'Dynamic Containment' as description
    FROM latest
    
    UNION ALL
    
    SELECT 'DM' as service,
           ROUND(dm_revenue_per_mwh, 2) as revenue_per_mwh,
           ROUND(dm_annual_revenue / 1000, 0) as annual_revenue_k,
           '✅' as status,
           'Dynamic Moderation' as description
    FROM latest
    
    UNION ALL
    
    SELECT 'DR' as service,
           ROUND(dr_revenue_per_mwh, 2) as revenue_per_mwh,
           ROUND(dr_annual_revenue / 1000, 0) as annual_revenue_k,
           '📅' as status,
           'Dynamic Regulation' as description
    FROM latest
    
    UNION ALL
    
    SELECT 'CM' as service,
           ROUND(cm_revenue_per_mwh, 2) as revenue_per_mwh,
           ROUND(cm_annual_revenue / 1000, 0) as annual_revenue_k,
           '✅' as status,
           'Capacity Market' as description
    FROM latest
    
    UNION ALL
    
    SELECT 'BM' as service,
           ROUND(bm_avg, 2) as revenue_per_mwh,
           ROUND(bm_avg * 2482 / 1000, 0) as annual_revenue_k,
           CASE WHEN bm_count > 0 THEN '✅' ELSE '⚠️' END as status,
           'Balancing Mechanism' as description
    FROM recent
    
    UNION ALL
    
    SELECT 'TRIAD' as service,
           ROUND(triad_avg, 2) as revenue_per_mwh,
           100.0 as annual_revenue_k,
           '📅' as status,
           'Triad Avoidance (Nov-Feb)' as description
    FROM recent
    
    UNION ALL
    
    SELECT 'NEG' as service,
           ROUND(neg_avg, 2) as revenue_per_mwh,
           25.0 as annual_revenue_k,
           CASE WHEN neg_avg > 0 THEN '🔥' ELSE '⚪' END as status,
           'Negative Pricing' as description
    FROM recent
    
    ORDER BY annual_revenue_k DESC
    """
    
    return client.query(query).to_dataframe()

def query_profit_by_band():
    """Get profit statistics by DUoS band"""
    client = get_bigquery_client()
    
    query = f"""
    SELECT 
        duos_band,
        COUNT(*) as periods,
        ROUND(AVG(net_margin_per_mwh), 2) as avg_profit,
        ROUND(MIN(net_margin_per_mwh), 2) as min_profit,
        ROUND(MAX(net_margin_per_mwh), 2) as max_profit,
        ROUND(AVG(ssp_charge), 2) as avg_price
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= CURRENT_DATE() - 7
    GROUP BY duos_band
    ORDER BY 
        CASE duos_band 
            WHEN 'GREEN' THEN 1 
            WHEN 'AMBER' THEN 2 
            WHEN 'RED' THEN 3 
        END
    """
    
    return client.query(query).to_dataframe()

def create_live_ticker(worksheet, current_data):
    """Create live ticker header with current period info"""
    if current_data is None:
        worksheet.update(values=[['⚠️ DATA UNAVAILABLE - Check BigQuery connection']], range_name='A1')
        return
    
    profit = current_data['profit']
    signal = current_data['trading_signal']
    
    # Determine profit icon
    if profit > 150:
        icon = '🟢'
    elif profit > 100:
        icon = '🟡'
    else:
        icon = '🔴'
    
    # Build ticker text
    ticker_text = f"💰 LIVE: £{profit:.2f}/MWh | {icon} {signal} | Period {int(current_data['settlementPeriod'])} | {current_data['duos_band']} band"
    
    # Write ticker (merged cells A1:M1)
    worksheet.update(values=[[ticker_text]], range_name='A1')
    
    # Add timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    worksheet.update(values=[[f"Last updated: {timestamp} | Next refresh: 5 min"]], range_name='A2')
    
    return

def write_current_period(worksheet, current_data):
    """Write current period details"""
    if current_data is None:
        return
    
    headers = ['Metric', 'Value']
    data = [
        headers,
        ['Settlement Date', str(current_data['settlementDate'])[:10]],
        ['Settlement Period', str(int(current_data['settlementPeriod']))],  # Force string to prevent currency format
        ['Time', str(current_data['ts_halfhour'])],
        ['DUoS Band', current_data['duos_band']],
        ['Market Price', f"£{current_data['market_price']:.2f}"],
        ['Total Revenue', f"£{current_data['total_revenue']:.2f}"],
        ['Total Cost', f"£{current_data['total_cost']:.2f}"],
        ['Net Profit', f"£{current_data['profit']:.2f}"],
        ['Trading Signal', current_data['trading_signal']]
    ]
    
    worksheet.update(values=data, range_name='A5')
    
def write_service_breakdown(worksheet, services_df):
    """Write service breakdown table"""
    headers = ['Service', '£/MWh', 'Annual (£k)', 'Status', 'Description']
    
    data = [headers]
    for _, row in services_df.iterrows():
        data.append([
            row['service'],
            f"£{row['revenue_per_mwh']:.2f}",
            f"£{row['annual_revenue_k']:.0f}k",
            row['status'],
            row['description']
        ])
    
    # Add total row
    total_mwh = services_df['revenue_per_mwh'].sum()
    total_annual = services_df['annual_revenue_k'].sum()
    data.append(['TOTAL', f"£{total_mwh:.2f}", f"£{total_annual:.0f}k", '✅', 'All Services Stacked'])
    
    worksheet.update(values=data, range_name='A17')

def write_profit_by_band(worksheet, profit_df):
    """Write profit analysis by DUoS band"""
    headers = ['Band', 'Periods', 'Avg Profit', 'Min', 'Max', 'Avg Price']
    
    data = [headers]
    for _, row in profit_df.iterrows():
        data.append([
            row['duos_band'],
            int(row['periods']),
            f"£{row['avg_profit']:.2f}",
            f"£{row['min_profit']:.2f}",
            f"£{row['max_profit']:.2f}",
            f"£{row['avg_price']:.2f}"
        ])
    
    worksheet.update(values=data, range_name='K5')

def write_stacking_scenarios(worksheet):
    """Write revenue stacking scenarios"""
    headers = ['Scenario', 'Services', 'Annual £k', 'Risk', 'Notes']
    
    data = [
        headers,
        ['Conservative', 'DC + CM + PPA', '£599k', '🟢 Low', 'High availability, proven revenue'],
        ['Balanced', 'DC + DM + CM + PPA + BM', '£749k', '🟡 Medium', 'Multiple frequency services'],
        ['Aggressive', 'DC + DM + DR + CM + PPA + BM + TRIAD', '£999k', '🔴 High', 'Maximum revenue, complex control'],
        ['Opportunistic', 'DC + CM + PPA + NEGATIVE', '£624k', '🟢 Low', 'Capture pricing events']
    ]
    
    worksheet.update(values=data, range_name='A30')

def apply_formatting(worksheet):
    """Apply professional formatting to the dashboard"""
    # Get the worksheet ID for batch updates
    sheet_id = worksheet.id
    
    requests = [
        # Freeze top 3 rows
        {
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {'frozenRowCount': 3}
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        },
        # Merge cells for ticker (A1:M1)
        {
            'mergeCells': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 13
                },
                'mergeType': 'MERGE_ALL'
            }
        },
        # Format ticker background
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 13
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': COLORS['ticker_bg'],
                        'textFormat': {
                            'foregroundColor': COLORS['white'],
                            'fontSize': 14,
                            'bold': True
                        },
                        'horizontalAlignment': 'CENTER',
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat'
            }
        },
        # Bold headers
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 4,
                    'endRowIndex': 5,
                    'startColumnIndex': 0,
                    'endColumnIndex': 13
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': COLORS['header_bg'],
                        'textFormat': {
                            'foregroundColor': COLORS['white'],
                            'bold': True
                        }
                    }
                },
                'fields': 'userEnteredFormat'
            }
        }
    ]
    
    # Execute batch update
    worksheet.spreadsheet.batch_update({'requests': requests})

def main():
    """Main execution"""
    print("=" * 80)
    print("VLP REVENUE DASHBOARD - PYTHON REFRESH")
    print("=" * 80)
    print()
    
    # 1. Query BigQuery
    print("📊 Querying BigQuery...")
    current_data = query_current_period()
    services_df = query_service_breakdown()
    profit_df = query_profit_by_band()
    
    if current_data is not None:
        print(f"✅ Current period: {current_data['settlementDate']} P{int(current_data['settlementPeriod'])}")
        print(f"   Profit: £{current_data['profit']:.2f}/MWh | Signal: {current_data['trading_signal']}")
    else:
        print("⚠️  No current data available")
    
    print(f"✅ Retrieved {len(services_df)} services")
    print(f"✅ Retrieved {len(profit_df)} DUoS bands")
    print()
    
    # 2. Connect to Google Sheets
    print("📝 Connecting to Google Sheets...")
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Get or create VLP Revenue sheet
    try:
        worksheet = spreadsheet.worksheet('VLP Revenue')
        print("✅ Found existing 'VLP Revenue' sheet")
    except:
        worksheet = spreadsheet.add_worksheet('VLP Revenue', rows=100, cols=20)
        print("✅ Created new 'VLP Revenue' sheet")
    
    print()
    
    # 3. Write data
    print("✍️  Writing data to sheet...")
    create_live_ticker(worksheet, current_data)
    write_current_period(worksheet, current_data)
    write_service_breakdown(worksheet, services_df)
    write_profit_by_band(worksheet, profit_df)
    write_stacking_scenarios(worksheet)
    print("✅ Data written")
    print()
    
    # 4. Apply formatting
    print("🎨 Applying formatting...")
    apply_formatting(worksheet)
    print("✅ Formatting applied")
    print()
    
    # 5. Summary
    print("=" * 80)
    print("✅ DASHBOARD UPDATE COMPLETE")
    print("=" * 80)
    print()
    print(f"🔗 View dashboard: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")
    print()
    
    if current_data is not None:
        print("📊 Current Metrics:")
        print(f"   Net Profit: £{current_data['profit']:.2f}/MWh")
        print(f"   Total Revenue: £{current_data['total_revenue']:.2f}/MWh")
        print(f"   Total Cost: £{current_data['total_cost']:.2f}/MWh")
        print(f"   Trading Signal: {current_data['trading_signal']}")
        print()
    
    print("💡 To refresh again: python3 vlp_dashboard_python.py")
    print()

if __name__ == '__main__':
    main()
