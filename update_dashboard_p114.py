#!/usr/bin/env python3
"""
Update Dashboard with P114 Settlement Data
Replaces BOALF-based VLP revenue with TRUE settlement revenue from P114

Changes:
1. Use mart_vlp_revenue_p114 view (P114 settlement) instead of BOALF
2. Add data_maturity indicator (RF/R3/II)
3. Include settlement mechanism classification (self-balancing)
4. Update revenue calculations to use imbalance pricing

Integration Points:
- Google Sheets dashboard (VLP revenue section)
- realtime_dashboard_updater.py (add P114 data source)
- update_analysis_bi_enhanced.py (replace BOALF queries)
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Google Sheets credentials
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', SCOPE)
gc = gspread.authorize(CREDS)

# Dashboard sheet ID
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

client = bigquery.Client(project=PROJECT_ID, location='US')

def get_vlp_revenue_summary(days=30):
    """Get VLP revenue from P114 settlement data"""
    query = f'''
    SELECT
      bm_unit_id,
      COUNT(DISTINCT settlement_date) as days_active,
      SUM(revenue_gbp) as total_revenue_gbp,
      AVG(revenue_gbp) / COUNT(DISTINCT settlement_date) as avg_daily_revenue,
      SUM(energy_mwh) as total_energy_mwh,
      AVG(price_gbp_per_mwh) as avg_system_price,
      -- Data maturity breakdown
      COUNTIF(settlement_run = 'RF') as days_rf_final,
      COUNTIF(settlement_run = 'R3') as days_r3_high_conf,
      COUNTIF(settlement_run = 'II') as days_ii_preliminary,
      -- Settlement mechanism
      'Self-Balancing (P114 Only)' as settlement_mechanism
    FROM `{PROJECT_ID}.{DATASET}.mart_vlp_revenue_p114`
    WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    GROUP BY bm_unit_id
    ORDER BY total_revenue_gbp DESC
    '''

    df = client.query(query).to_dataframe()
    return df

def get_vlp_daily_breakdown(days=7):
    """Get recent daily VLP revenue breakdown"""
    query = f'''
    SELECT
      settlement_date,
      bm_unit_id,
      data_maturity,
      SUM(revenue_gbp) as revenue_gbp,
      SUM(energy_mwh) as energy_mwh,
      AVG(price_gbp_per_mwh) as avg_price,
      COUNT(DISTINCT settlement_period) as periods_active
    FROM `{PROJECT_ID}.{DATASET}.mart_vlp_revenue_p114`
    WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    GROUP BY settlement_date, bm_unit_id, data_maturity
    ORDER BY settlement_date DESC, bm_unit_id
    '''

    df = client.query(query).to_dataframe()
    return df

def compare_p114_vs_boalf(days=30):
    """Compare P114 settlement vs BOALF acceptance data"""
    query = f'''
    WITH p114_revenue AS (
      SELECT
        bm_unit_id,
        DATE_TRUNC(settlement_date, MONTH) as month,
        SUM(revenue_gbp) as p114_revenue,
        SUM(energy_mwh) as p114_energy,
        COUNT(DISTINCT settlement_date) as p114_days
      FROM `{PROJECT_ID}.{DATASET}.mart_vlp_revenue_p114`
      WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
      GROUP BY bm_unit_id, month
    ),
    boalf_data AS (
      SELECT
        bmUnit as bm_unit_id,
        DATE_TRUNC(CAST(acceptanceTime AS DATE), MONTH) as month,
        COUNT(*) as boalf_acceptances,
        SUM(acceptanceVolume) as boalf_volume
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE bmUnit IN ('FBPGM002', 'FFSEN005')
        AND CAST(acceptanceTime AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
      GROUP BY bm_unit_id, month
    )
    SELECT
      COALESCE(p.bm_unit_id, b.bm_unit_id) as unit,
      COALESCE(p.month, b.month) as month,
      p.p114_revenue,
      p.p114_energy,
      p.p114_days,
      b.boalf_acceptances,
      b.boalf_volume,
      CASE
        WHEN b.boalf_acceptances IS NULL THEN 'Self-Balancing Only'
        WHEN p.p114_revenue IS NOT NULL AND b.boalf_acceptances IS NOT NULL THEN 'Hybrid'
        ELSE 'Unknown'
      END as mechanism
    FROM p114_revenue p
    FULL OUTER JOIN boalf_data b
      ON p.bm_unit_id = b.bm_unit_id AND p.month = b.month
    ORDER BY month DESC, unit
    '''

    df = client.query(query).to_dataframe()
    return df

def update_dashboard_vlp_section():
    """Update Google Sheets dashboard with P114 data"""
    print('🔄 Updating dashboard VLP section with P114 settlement data...')

    try:
        sheet = gc.open_by_key(SHEET_ID)

        # Find or create "VLP Revenue (P114)" worksheet
        try:
            worksheet = sheet.worksheet('VLP Revenue (P114)')
        except:
            worksheet = sheet.add_worksheet(title='VLP Revenue (P114)', rows=1000, cols=20)
            print('  ✅ Created new worksheet: VLP Revenue (P114)')

        # Get 30-day summary
        summary_df = get_vlp_revenue_summary(days=30)

        # Write header
        worksheet.update('A1', [['Last Updated', datetime.now().strftime('%Y-%m-%d %H:%M UTC')]])
        worksheet.update('A2', [['Data Source', 'P114 Settlement (Elexon Portal)']])
        worksheet.update('A3', [['Period', 'Last 30 Days']])

        # Write summary table
        worksheet.update('A5', [['VLP REVENUE SUMMARY (30 Days)']])

        headers = [
            'Unit', 'Days Active', 'Total Revenue (£)', 'Avg Daily (£)',
            'Total Energy (MWh)', 'Avg Price (£/MWh)',
            'Days RF (Final)', 'Days R3 (High)', 'Days II (Prelim)',
            'Settlement Mechanism'
        ]
        worksheet.update('A6', [headers])

        # Convert DataFrame to list of lists
        data = summary_df.values.tolist()
        if data:
            worksheet.update(f'A7', data)

        print(f'  ✅ Updated VLP summary: {len(data)} units')

        # Get 7-day daily breakdown
        daily_df = get_vlp_daily_breakdown(days=7)

        # Write daily breakdown
        worksheet.update('A15', [['DAILY BREAKDOWN (Last 7 Days)']])

        daily_headers = [
            'Date', 'Unit', 'Data Maturity', 'Revenue (£)',
            'Energy (MWh)', 'Avg Price (£/MWh)', 'Periods Active'
        ]
        worksheet.update('A16', [daily_headers])

        daily_data = daily_df.values.tolist()
        if daily_data:
            worksheet.update(f'A17', daily_data)

        print(f'  ✅ Updated daily breakdown: {len(daily_data)} rows')

        # Get P114 vs BOALF comparison
        comparison_df = compare_p114_vs_boalf(days=30)

        # Write comparison table
        worksheet.update('A30', [['P114 SETTLEMENT vs BOALF ACCEPTANCES']])
        worksheet.update('A31', [['Note: VLP units primarily self-balance (P114 only), minimal ESO interventions (BOALF)']])

        comparison_headers = [
            'Unit', 'Month', 'P114 Revenue (£)', 'P114 Energy (MWh)', 'P114 Days',
            'BOALF Acceptances', 'BOALF Volume (MWh)', 'Mechanism'
        ]
        worksheet.update('A33', [comparison_headers])

        comparison_data = comparison_df.values.tolist()
        if comparison_data:
            worksheet.update(f'A34', comparison_data)

        print(f'  ✅ Updated comparison table: {len(comparison_data)} rows')

        print('✅ Dashboard VLP section updated successfully!')

    except Exception as e:
        print(f'❌ Dashboard update failed: {e}')
        raise

if __name__ == '__main__':
    print('='*80)
    print('🚀 DASHBOARD UPDATE: P114 Settlement Data Integration')
    print('='*80)
    print('')

    print('📊 Fetching VLP revenue data from P114...')

    # Test queries
    summary = get_vlp_revenue_summary(days=30)
    print(f'\n30-Day Summary:')
    print(summary.to_string(index=False))

    daily = get_vlp_daily_breakdown(days=7)
    print(f'\n7-Day Daily Breakdown: {len(daily)} rows')
    print(daily.head(10).to_string(index=False))

    comparison = compare_p114_vs_boalf(days=30)
    print(f'\nP114 vs BOALF Comparison:')
    print(comparison.to_string(index=False))

    # Update dashboard
    print('\n' + '='*80)
    response = input('Update Google Sheets dashboard? (y/n): ')
    if response.lower() == 'y':
        update_dashboard_vlp_section()
    else:
        print('⏭️  Skipped dashboard update')

    print('\n✅ Complete!')
