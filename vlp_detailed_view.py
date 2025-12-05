#!/usr/bin/env python3
"""
VLP Dashboard - Detailed View
Shows per-settlement-period breakdown with all calculations
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import json

# Load config
with open('vlp_prerequisites.json', 'r') as f:
    config = json.load(f)

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
BMU_ID = config['BMU_BATTERY']

def main():
    print('\n' + '='*80)
    print('🔋 VLP DASHBOARD - DETAILED ANALYSIS')
    print('='*80)
    print(f'\n📋 Configuration:')
    print(f'   BMU: {BMU_ID}')
    print(f'   Period: Oct 17-23, 2025 (High-price event week)')
    print(f'   Battery: 2.5 MW / 5.0 MWh / 85% efficiency')
    print('\n' + '-'*80)
    
    # Fetch data
    print('\n📊 Fetching BM acceptance data from BigQuery...')
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH bm_volumes AS (
      SELECT
        CAST(settlementDate AS DATE) AS settlementDate,
        settlementPeriodFrom AS settlementPeriod,
        SUM(ABS(levelTo - levelFrom)) AS accepted_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE bmUnit = '{BMU_ID}'
        AND CAST(settlementDate AS DATE) BETWEEN '2025-10-17' AND '2025-10-23'
      GROUP BY settlementDate, settlementPeriod
    )
    
    SELECT
      c.settlementDate,
      c.settlementPeriod,
      c.systemBuyPrice AS wholesale_price,
      c.systemSellPrice AS ssp_price,
      COALESCE(bm.accepted_mw, 0) AS bm_accepted_mw,
      COALESCE(bm.accepted_mw, 0) * 0.5 AS bm_accepted_mwh
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs` c
    LEFT JOIN bm_volumes bm USING (settlementDate, settlementPeriod)
    WHERE c.settlementDate BETWEEN '2025-10-17' AND '2025-10-23'
      AND COALESCE(bm.accepted_mw, 0) > 0
    ORDER BY c.settlementDate, c.settlementPeriod
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print('   ❌ No BM acceptances found for this period')
        return
    
    print(f'   ✅ Found {len(df)} settlement periods with BM activity')
    print(f'   📅 Date range: {df["settlementDate"].min()} to {df["settlementDate"].max()}')
    
    # Summary statistics
    total_mwh = df['bm_accepted_mwh'].sum()
    avg_ssp = df['ssp_price'].mean()
    max_ssp = df['ssp_price'].max()
    min_ssp = df['ssp_price'].min()
    
    print(f'\n📈 Market Statistics:')
    print(f'   Total BM Volume: {total_mwh:,.1f} MWh')
    print(f'   Avg SSP: £{avg_ssp:,.2f}/MWh')
    print(f'   Max SSP: £{max_ssp:,.2f}/MWh (settlement period {df.loc[df["ssp_price"].idxmax(), "settlementPeriod"]})')
    print(f'   Min SSP: £{min_ssp:,.2f}/MWh (settlement period {df.loc[df["ssp_price"].idxmin(), "settlementPeriod"]})')
    
    # Revenue calculations
    df['bm_revenue'] = df['bm_accepted_mwh'] * df['ssp_price']
    df['cm_revenue'] = df['bm_accepted_mwh'] * 9.04  # £9.04/MWh
    df['ppa_revenue'] = df['bm_accepted_mwh'] * 150  # £150/MWh
    
    total_bm = df['bm_revenue'].sum()
    total_cm = df['cm_revenue'].sum()
    total_ppa = df['ppa_revenue'].sum()
    
    print(f'\n💰 Revenue Breakdown:')
    print(f'   BM Revenue:  £{total_bm:>12,.0f}  ({total_bm/total_mwh:>6.2f}/MWh)')
    print(f'   CM Revenue:  £{total_cm:>12,.0f}  ({total_cm/total_mwh:>6.2f}/MWh)')
    print(f'   PPA Revenue: £{total_ppa:>12,.0f}  ({total_ppa/total_mwh:>6.2f}/MWh)')
    print(f'   ' + '-'*45)
    print(f'   Total:       £{total_bm + total_cm + total_ppa:>12,.0f}')
    
    # Daily breakdown
    print(f'\n📅 Daily Breakdown:')
    print(f'   {"Date":<12} {"SPs":<5} {"MWh":<8} {"Avg SSP":<10} {"BM Rev":<12} {"Total Rev"}')
    print(f'   ' + '-'*70)
    
    daily = df.groupby('settlementDate').agg({
        'settlementPeriod': 'count',
        'bm_accepted_mwh': 'sum',
        'ssp_price': 'mean',
        'bm_revenue': 'sum',
    })
    daily['total_revenue'] = (
        daily['bm_revenue'] + 
        df.groupby('settlementDate')['cm_revenue'].sum() + 
        df.groupby('settlementDate')['ppa_revenue'].sum()
    )
    
    for date, row in daily.iterrows():
        print(f'   {str(date):<12} {int(row["settlementPeriod"]):<5} {row["bm_accepted_mwh"]:>6.1f}   £{row["ssp_price"]:>7.2f}   £{row["bm_revenue"]:>10,.0f}   £{row["total_revenue"]:>10,.0f}')
    
    # Show top 10 most profitable settlement periods
    print(f'\n🏆 Top 10 Most Profitable Settlement Periods:')
    print(f'   {"Date":<12} {"SP":<4} {"MWh":<6} {"SSP":<9} {"BM Rev":<11} {"Total Rev"}')
    print(f'   ' + '-'*65)
    
    df['total_revenue'] = df['bm_revenue'] + df['cm_revenue'] + df['ppa_revenue']
    top10 = df.nlargest(10, 'total_revenue')
    
    for _, row in top10.iterrows():
        print(f'   {str(row["settlementDate"]):<12} {int(row["settlementPeriod"]):<4} {row["bm_accepted_mwh"]:>4.1f}   £{row["ssp_price"]:>6.2f}   £{row["bm_revenue"]:>9,.0f}   £{row["total_revenue"]:>9,.0f}')
    
    # Show sample of raw data
    print(f'\n📋 Sample Data (First 20 Settlement Periods):')
    print(f'   {"Date":<12} {"SP":<4} {"MW":<5} {"MWh":<6} {"SSP (£/MWh)":<12} {"BM Rev (£)"}')
    print(f'   ' + '-'*65)
    
    for _, row in df.head(20).iterrows():
        print(f'   {str(row["settlementDate"]):<12} {int(row["settlementPeriod"]):<4} {row["bm_accepted_mw"]:>3.0f}   {row["bm_accepted_mwh"]:>4.1f}   £{row["ssp_price"]:>9.2f}   £{row["bm_revenue"]:>10,.0f}')
    
    if len(df) > 20:
        print(f'   ... ({len(df) - 20} more periods)')
    
    print('\n' + '='*80)
    print('✅ Analysis complete. For full data, check Google Sheets:')
    print('   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/')
    print('   - Dashboard tab: Summary & charts')
    print('   - BESS_VLP tab: All 336 settlement periods with detailed calculations')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
