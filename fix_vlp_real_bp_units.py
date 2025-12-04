#!/usr/bin/env python3
"""
Add REAL VLP data from 2__FBPGM001 and 2__FBPGM002 only
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

ss = gc.open_by_key(SPREADSHEET_ID)
dashboard = ss.worksheet('Dashboard')

bq_creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location='US')

print("="*80)
print("ADDING REAL VLP DATA - BP GAS MARKETING (2__FBPGM001, 2__FBPGM002)")
print("="*80)
print()

# Read current row 6
current_row6 = dashboard.row_values(6)
print(f"Current row 6: {current_row6}")
print()

# Query REAL VLP data - ONLY the two BP units
print("Querying BigQuery for 2__FBPGM001 and 2__FBPGM002...")
vlp_query = f"""
SELECT 
    bmUnit,
    COUNT(*) as acceptances,
    SUM(levelTo - levelFrom) as total_mw_changes,
    AVG(ABS(levelTo - levelFrom)) as avg_mw_per_action,
    MIN(settlementDate) as first_date,
    MAX(settlementDate) as last_date
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
WHERE bmUnit IN ('2__FBPGM001', '2__FBPGM002')
    AND settlementDate >= '2025-01-01'
GROUP BY bmUnit
ORDER BY bmUnit
"""

vlp_units_df = bq_client.query(vlp_query).to_dataframe()
print()
print("VLP Units Found:")
print(vlp_units_df.to_string(index=False))
print()

if not vlp_units_df.empty:
    total_acceptances = vlp_units_df['acceptances'].sum()
    avg_mw = vlp_units_df['avg_mw_per_action'].mean()
    
    # Known capacities from vlp_battery_units_data.json
    fbpgm001_cap = 33.6
    fbpgm002_cap = 50.3
    total_capacity = fbpgm001_cap + fbpgm002_cap
    
    print(f"✅ Total VLP capacity: {total_capacity:.1f} MW")
    print(f"✅ Total acceptances: {total_acceptances:,}")
    print(f"✅ Avg MW per action: {avg_mw:.2f} MW")
    print()
    
    # Calculate FR revenue (simplified: £50/MWh avg price × avg action size × acceptances)
    # This is a rough estimate - actual revenue would need detailed settlement period analysis
    estimated_annual_mwh = total_acceptances * avg_mw * (365 / 335)  # Scale to full year
    estimated_fr_revenue = estimated_annual_mwh * 50  # £50/MWh rough estimate
    
    print(f"Estimated Annual MWh: {estimated_annual_mwh:,.0f}")
    print(f"Estimated FR Revenue: £{estimated_fr_revenue:,.0f}/yr")
    print()
    
    # Get arbitrage opportunity from price spreads
    arb_query = f"""
    SELECT 
        AVG(systemSellPrice - systemBuyPrice) as avg_spread,
        MAX(systemSellPrice - systemBuyPrice) as max_spread,
        COUNT(*) as periods
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= '2025-01-01'
        AND systemSellPrice IS NOT NULL
        AND systemBuyPrice IS NOT NULL
        AND (systemSellPrice - systemBuyPrice) > 10  -- Only profitable periods
    """
    
    arb_df = bq_client.query(arb_query).to_dataframe()
    if not arb_df.empty:
        avg_spread = float(arb_df['avg_spread'].iloc[0])
        # Assume 1 cycle/day × capacity × spread × 365
        estimated_arb_revenue = total_capacity * avg_spread * 365 / 1000  # Convert MW to MWh
        print(f"Avg spread on profitable periods: £{avg_spread:.2f}/MWh")
        print(f"Estimated Arbitrage Revenue: £{estimated_arb_revenue:,.0f}/yr")
    else:
        estimated_arb_revenue = 10000
    
    print()
    total_vlp_revenue = estimated_fr_revenue + estimated_arb_revenue
    
    # UPDATE row 6 (don't insert!)
    vlp_row = [[
        '💰 VLP FLEXIBILITY',
        '2 Units',
        f'{total_capacity:.1f} MW',
        '📊 FR REVENUE',
        f'£{estimated_fr_revenue:,.0f}/yr',
        '⚡ ARBITRAGE',
        f'£{estimated_arb_revenue:,.0f}/yr',
        '💷 TOTAL VLP',
        f'£{total_vlp_revenue:,.0f}/yr'
    ]]
    
    dashboard.update(range_name='A6:I6', values=vlp_row)
    dashboard.format('A6:I6', {
        'backgroundColor': {'red': 0.0, 'green': 0.44, 'blue': 0.75},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    
    print("✅ Updated row 6 with VLP data")
    print()
    
    # Add VLP detail table
    detail_query = f"""
    SELECT 
        DATE(settlementDate) as date,
        settlementPeriodFrom as period,
        bmUnit,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as mw_change,
        acceptanceNumber as acceptance_id,
        acceptanceTime as time
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
    WHERE bmUnit IN ('2__FBPGM001', '2__FBPGM002')
        AND settlementDate >= CURRENT_DATE() - 7
    ORDER BY settlementDate DESC, acceptanceTime DESC
    LIMIT 30
    """
    
    detail_df = bq_client.query(detail_query).to_dataframe()
    
    if not detail_df.empty:
        # Clear existing VLP section and add fresh data
        vlp_header = [[
            '💰 VLP BALANCING ACTIONS - LAST 7 DAYS (BP Gas Marketing)', '', '', '', '', '', '', ''
        ]]
        vlp_col_headers = [[
            'Date', 'Period', 'BM Unit', 'From MW', 'To MW', 'Change MW', 'Acceptance ID', 'Time'
        ]]
        
        dashboard.update(range_name='A40:H40', values=vlp_header)
        dashboard.update(range_name='A41:H41', values=vlp_col_headers)
        
        # Format headers
        dashboard.format('A40:H40', {
            'backgroundColor': {'red': 0.96, 'green': 0.65, 'blue': 0.14},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
            'horizontalAlignment': 'CENTER'
        })
        dashboard.format('A41:H41', {
            'backgroundColor': {'red': 0.0, 'green': 0.44, 'blue': 0.75},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
            'horizontalAlignment': 'CENTER'
        })
        
        # Add data
        detail_values = detail_df.values.tolist()
        dashboard.update(range_name=f'A42:H{41 + len(detail_values)}', values=detail_values)
        
        print(f"✅ Added {len(detail_df)} VLP actions to detail table")
    else:
        print("⚠️  No VLP actions in last 7 days")
    
    print()
    
    # Add timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    dashboard.update(range_name='A99', values=[[f'Last Updated: {timestamp}']])
    
    print("="*80)
    print("✅ VLP DATA COMPLETE")
    print("="*80)
    print()
    print(f"SUMMARY:")
    print(f"  • 2 VLP units (2__FBPGM001, 2__FBPGM002)")
    print(f"  • {total_capacity:.1f} MW total capacity (BP Gas Marketing)")
    print(f"  • {total_acceptances:,} balancing actions YTD 2025")
    print(f"  • £{estimated_fr_revenue:,.0f}/yr FR revenue (est.)")
    print(f"  • £{estimated_arb_revenue:,.0f}/yr arbitrage (est.)")
    print(f"  • £{total_vlp_revenue:,.0f}/yr TOTAL")
    print()
    print("Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/")

else:
    print("❌ No VLP data found in bmrs_boalf")
