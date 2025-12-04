#!/usr/bin/env python3
"""
REALISTIC VLP Revenue Calculation
Includes ALL revenue streams: Arbitrage + FFR + DCL + DM + Locational premiums
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime

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

print("="*90)
print("VLP REALISTIC REVENUE CALCULATION - MULTI-STREAM ANALYSIS")
print("="*90)
print()

# VLP capacity from vlp_battery_units_data.json
vlp_capacity_mw = 83.9  # 2__FBPGM001 (33.6) + 2__FBPGM002 (50.3)
vlp_units = 2

print(f"VLP Units: {vlp_units} (BP Gas Marketing)")
print(f"Total Capacity: {vlp_capacity_mw} MW")
print()

# REVENUE STREAM 1: Energy Arbitrage
print("=" * 90)
print("REVENUE STREAM 1: ENERGY ARBITRAGE")
print("=" * 90)

arb_query = f"""
WITH daily_prices AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    MAX(systemSellPrice) as max_sell,
    MIN(systemBuyPrice) as min_buy,
    (MAX(systemSellPrice) - MIN(systemBuyPrice)) as daily_spread
  FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
  WHERE settlementDate >= '2025-01-01'
    AND settlementDate <= '2025-10-31'
    AND systemSellPrice IS NOT NULL
    AND systemBuyPrice IS NOT NULL
  GROUP BY date
)
SELECT 
  AVG(daily_spread) as avg_daily_spread,
  COUNT(*) as trading_days
FROM daily_prices
WHERE daily_spread > 20  -- Lower threshold (£20/MWh minimum viable)
"""

arb_result = bq_client.query(arb_query).to_dataframe()

if not arb_result.empty:
    avg_spread = float(arb_result['avg_daily_spread'].iloc[0])
    trading_days = int(arb_result['trading_days'].iloc[0])
    
    # Realistic arbitrage assumptions
    cycles_per_day = 2  # Industry standard: 2 full cycles/day
    utilization = trading_days / 304  # Actual utilization
    efficiency = 0.85  # 85% round-trip
    
    # Annual MWh traded
    annual_cycles = trading_days * cycles_per_day
    annual_mwh_arbitrage = vlp_capacity_mw * annual_cycles
    
    # Revenue = MWh × (spread/2) × efficiency
    arbitrage_revenue = annual_mwh_arbitrage * (avg_spread / 2) * efficiency
    
    print(f"Avg Daily Spread: £{avg_spread:.2f}/MWh")
    print(f"Trading Days: {trading_days} ({utilization*100:.0f}% utilization)")
    print(f"Cycles per Day: {cycles_per_day}")
    print(f"Annual MWh Traded: {annual_mwh_arbitrage:,.0f}")
    print(f"Revenue: £{arbitrage_revenue:,.0f}/yr")
    print(f"Per MW: £{arbitrage_revenue/vlp_capacity_mw:,.0f}/MW/yr")
else:
    arbitrage_revenue = 0
    print("❌ No arbitrage data available")

print()

# REVENUE STREAM 2: Frequency Response (FFR)
print("=" * 90)
print("REVENUE STREAM 2: FREQUENCY RESPONSE (FFR)")
print("=" * 90)

# FFR contracts pay £10-30/MW/hr depending on service (DCL, DM, DCH)
# VLP typically secures 50% of capacity for FFR
ffr_capacity_mw = vlp_capacity_mw * 0.5  # 50% committed to FFR
ffr_rate_per_mw_hr = 15  # £15/MW/hr (conservative DCL rate)
ffr_hours_per_year = 8760

ffr_revenue = ffr_capacity_mw * ffr_rate_per_mw_hr * ffr_hours_per_year

print(f"FFR Capacity: {ffr_capacity_mw:.1f} MW (50% of total)")
print(f"FFR Rate: £{ffr_rate_per_mw_hr}/MW/hr (DCL market)")
print(f"Hours per Year: {ffr_hours_per_year:,}")
print(f"Revenue: £{ffr_revenue:,.0f}/yr")
print(f"Per MW: £{ffr_revenue/vlp_capacity_mw:,.0f}/MW/yr")
print()

# REVENUE STREAM 3: Dynamic Containment & Moderation
print("=" * 90)
print("REVENUE STREAM 3: DYNAMIC CONTAINMENT & MODERATION")
print("=" * 90)

# DC pays £5-10/MW/hr for availability
dc_capacity_mw = vlp_capacity_mw * 0.3  # 30% for DC services
dc_rate_per_mw_hr = 7  # £7/MW/hr
dc_hours_per_year = 8760

dc_revenue = dc_capacity_mw * dc_rate_per_mw_hr * dc_hours_per_year

print(f"DC Capacity: {dc_capacity_mw:.1f} MW (30% of total)")
print(f"DC Rate: £{dc_rate_per_mw_hr}/MW/hr")
print(f"Hours per Year: {dc_hours_per_year:,}")
print(f"Revenue: £{dc_revenue:,.0f}/yr")
print(f"Per MW: £{dc_revenue/vlp_capacity_mw:,.0f}/MW/yr")
print()

# REVENUE STREAM 4: Balancing Mechanism Premiums
print("=" * 90)
print("REVENUE STREAM 4: BALANCING MECHANISM PREMIUMS")
print("=" * 90)

# From actual bmrs_boalf data - 109k acceptances
# VLP gets paid for accepted offers (not just spread arbitrage)
bm_query = f"""
SELECT 
    COUNT(*) as total_actions,
    AVG(ABS(levelTo - levelFrom)) as avg_mw_per_action
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
WHERE bmUnit IN ('2__FBPGM001', '2__FBPGM002')
    AND settlementDate >= '2025-01-01'
"""

bm_result = bq_client.query(bm_query).to_dataframe()
if not bm_result.empty:
    total_actions = int(bm_result['total_actions'].iloc[0])
    avg_mw = float(bm_result['avg_mw_per_action'].iloc[0])
    
    # Conservative: £5/MW per action (includes NIV premiums)
    bm_premium_per_action = 5
    bm_revenue = total_actions * avg_mw * bm_premium_per_action * (365 / 304)  # Scale to full year
    
    print(f"Balancing Actions: {total_actions:,} (Jan-Oct 2025)")
    print(f"Avg MW per Action: {avg_mw:.2f} MW")
    print(f"Premium: £{bm_premium_per_action}/MW per action")
    print(f"Revenue (annualized): £{bm_revenue:,.0f}/yr")
    print(f"Per MW: £{bm_revenue/vlp_capacity_mw:,.0f}/MW/yr")
else:
    bm_revenue = 0
    print("❌ No BM data available")

print()

# TOTAL REVENUE CALCULATION
print("=" * 90)
print("TOTAL VLP REVENUE - ALL STREAMS")
print("=" * 90)

total_revenue = arbitrage_revenue + ffr_revenue + dc_revenue + bm_revenue

print(f"1. Energy Arbitrage:        £{arbitrage_revenue:>12,.0f}/yr ({arbitrage_revenue/total_revenue*100:.1f}%)")
print(f"2. Frequency Response:      £{ffr_revenue:>12,.0f}/yr ({ffr_revenue/total_revenue*100:.1f}%)")
print(f"3. Dynamic Containment:     £{dc_revenue:>12,.0f}/yr ({dc_revenue/total_revenue*100:.1f}%)")
print(f"4. BM Premiums:             £{bm_revenue:>12,.0f}/yr ({bm_revenue/total_revenue*100:.1f}%)")
print("-" * 90)
print(f"TOTAL:                      £{total_revenue:>12,.0f}/yr")
print()
print(f"Revenue per MW:             £{total_revenue/vlp_capacity_mw:>12,.0f}/MW/yr")
print()

# Investment analysis
capex_per_mw = 500_000
total_capex = capex_per_mw * vlp_capacity_mw
payback = total_capex / total_revenue
roi = (total_revenue / total_capex) * 100

print("INVESTMENT ANALYSIS:")
print("-" * 90)
print(f"CAPEX: £{total_capex:,.0f} (£{capex_per_mw:,}/MW)")
print(f"Payback Period: {payback:.1f} years {'✅ VIABLE' if payback < 10 else '❌ TOO LONG'}")
print(f"Annual ROI: {roi:.1f}% {'✅ GOOD' if roi > 10 else '❌ POOR'}")
print()

# Update Dashboard
print("Updating Dashboard...")
vlp_row = [[
    '💰 VLP FLEXIBILITY',
    f'{vlp_units} Units',
    f'{vlp_capacity_mw:.1f} MW',
    '📊 TOTAL REVENUE',
    f'£{total_revenue:,.0f}/yr',
    '⚡ PER MW',
    f'£{total_revenue/vlp_capacity_mw:,.0f}/MW/yr',
    '💷 ROI',
    f'{roi:.1f}%/yr'
]]

dashboard.update(range_name='A6:I6', values=vlp_row)
dashboard.format('A6:I6', {
    'backgroundColor': {'red': 0.0, 'green': 0.44, 'blue': 0.75},
    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
    'horizontalAlignment': 'CENTER'
})

# Add revenue breakdown table
revenue_breakdown = [[
    '💰 VLP REVENUE BREAKDOWN - MULTI-STREAM ANALYSIS', '', '', ''
], [
    'Revenue Stream', 'Annual Revenue', '% of Total', 'Per MW'
], [
    'Energy Arbitrage', f'£{arbitrage_revenue:,.0f}', f'{arbitrage_revenue/total_revenue*100:.1f}%', f'£{arbitrage_revenue/vlp_capacity_mw:,.0f}'
], [
    'Frequency Response (FFR)', f'£{ffr_revenue:,.0f}', f'{ffr_revenue/total_revenue*100:.1f}%', f'£{ffr_revenue/vlp_capacity_mw:,.0f}'
], [
    'Dynamic Containment', f'£{dc_revenue:,.0f}', f'{dc_revenue/total_revenue*100:.1f}%', f'£{dc_revenue/vlp_capacity_mw:,.0f}'
], [
    'BM Premiums', f'£{bm_revenue:,.0f}', f'{bm_revenue/total_revenue*100:.1f}%', f'£{bm_revenue/vlp_capacity_mw:,.0f}'
], [
    'TOTAL', f'£{total_revenue:,.0f}', '100%', f'£{total_revenue/vlp_capacity_mw:,.0f}'
]]

dashboard.update(range_name='A40:D46', values=revenue_breakdown)
dashboard.format('A40:D40', {
    'backgroundColor': {'red': 0.96, 'green': 0.65, 'blue': 0.14},
    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
    'horizontalAlignment': 'CENTER'
})
dashboard.format('A41:D41', {
    'backgroundColor': {'red': 0.0, 'green': 0.44, 'blue': 0.75},
    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
    'horizontalAlignment': 'CENTER'
})
dashboard.format('A46:D46', {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
})

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
dashboard.update(range_name='A99', values=[[f'Last Updated: {timestamp}']])

print("✅ Dashboard updated")
print()
print("=" * 90)
print("✅ REALISTIC VLP REVENUE CALCULATION COMPLETE")
print("=" * 90)
print()
print(f"Summary: {vlp_units} VLP units ({vlp_capacity_mw} MW) generate £{total_revenue:,.0f}/yr")
print(f"This is £{total_revenue/vlp_capacity_mw:,.0f}/MW/yr - industry benchmark: £100k-£150k/MW/yr")
print()
print("View: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/")
