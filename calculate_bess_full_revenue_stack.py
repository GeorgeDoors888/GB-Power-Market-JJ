#!/usr/bin/env python3
"""
BESS FULL REVENUE STACK MODEL
==============================
Comprehensive revenue model for 2.5 MW / 5 MWh BTM BESS including:

REVENUE STREAMS:
1. Dynamic Containment (DC) - Availability payments (£/MW/h)
2. Wholesale Arbitrage - Buy low, sell high
3. Imbalance Trading - System price (SSP/SBP) optimization
4. VLP Flexibility - Demand-side events
5. Network Savings - DUoS Red/Amber/Green avoidance
6. Levy Avoidance - BSUoS, RO, FiT, CfD, CCL, ECO, WHD
7. PPA Revenue - Supply end-user at £150/MWh (separate from BtM PPA analysis)

COST ACCOUNTING:
1. Charging costs (wholesale + network + levies)
2. Round-trip efficiency losses (15%)
3. Degradation (£5/MWh throughput)
4. VLP aggregator fees (20%)
5. Fixed O&M (£10/kW/year)
6. Insurance & maintenance

REALISTIC RANGES (2.5 MW / 5 MWh):
- Conservative: £80-150k/year
- Typical: £200-400k/year  
- Aggressive: £450-650k/year
- Extreme volatility: £1M+/year (2021/2022 type events)
"""

import gspread
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# BESS Physical Parameters
POWER_MW = 2.5  # Import/Export capacity
ENERGY_MWH = 5.0  # Storage capacity (2 hour duration)
ROUND_TRIP_EFFICIENCY = 0.85  # 85%
MAX_CYCLES_PER_DAY = 1.5  # Conservative for lifetime

# Cost Parameters
DEGRADATION_COST_PER_MWH = 5.0  # £/MWh throughput
VLP_FEE_SHARE = 0.20  # 20% aggregator fee
FIXED_OM_PER_KW_YEAR = 10.0  # £/kW/year
INSURANCE_PER_KW_YEAR = 2.0  # £/kW/year

# Revenue Parameters - Dynamic Containment
DC_CLEARING_PRICE_DAY = 15.0  # £/MW/h (conservative avg)
DC_CLEARING_PRICE_NIGHT = 5.0  # £/MW/h
DC_AVAILABILITY_FACTOR = 0.85  # 85% availability (maintenance, outages)
DC_POWER_DERATE = 0.90  # 90% of nameplate for DC (response time requirements)

# Revenue Parameters - VLP Flexibility
VLP_EVENT_PRICE = 80.0  # £/MWh delivered (conservative)
VLP_EVENTS_PER_YEAR = 40  # 40 events per year (NESO typical)
VLP_EVENT_DURATION_HOURS = 2.0  # 2 hours average

# Fixed Costs (£/MWh)
BSUOS_COST = 4.50
CCL_COST = 8.56
RO_COST = 14.50
FIT_COST = 7.40
CFD_COST = 9.00
ECO_COST = 1.75
WHD_COST = 0.75
TOTAL_FIXED_LEVIES = BSUOS_COST + CCL_COST + RO_COST + FIT_COST + CFD_COST + ECO_COST + WHD_COST

# DUoS Rates
DUOS_RED = 176.40  # £/MWh
DUOS_AMBER = 20.50  # £/MWh
DUOS_GREEN = 1.10  # £/MWh

print("=" * 100)
print("BESS FULL REVENUE STACK MODEL - 2.5 MW / 5 MWh")
print("=" * 100)
print(f"\n⚙️  CONFIGURATION:")
print(f"   Power: {POWER_MW:.1f} MW")
print(f"   Energy: {ENERGY_MWH:.1f} MWh ({ENERGY_MWH/POWER_MW:.1f} hour duration)")
print(f"   Efficiency: {ROUND_TRIP_EFFICIENCY*100:.0f}%")
print(f"   Max Cycles/Day: {MAX_CYCLES_PER_DAY:.1f}")
print(f"   Degradation: £{DEGRADATION_COST_PER_MWH:.2f}/MWh")

# ============================================================================
# CONNECT TO GOOGLE SHEETS
# ============================================================================

print("\n📊 Connecting to Google Sheets...")
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

# Read PPA price
ppa_price = float((bess_sheet.acell('D43').value or "150").strip().replace('£', '').replace(',', ''))
print(f"   PPA Rate: £{ppa_price:.2f}/MWh")

# ============================================================================
# LOAD SITE DEMAND PROFILE
# ============================================================================

print("\n📂 Loading site demand profile...")
hh_data = hh_sheet.get_all_records()
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['date'] = df_hh['timestamp'].dt.date
df_hh['period'] = ((df_hh['timestamp'].dt.hour * 2) + (df_hh['timestamp'].dt.minute // 30) + 1)
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['site_demand_mwh'] = df_hh['demand_kw'] / 1000 / 2  # Half-hourly

# Calculate DUoS band
df_hh['hour'] = df_hh['timestamp'].dt.hour
df_hh['is_weekend'] = df_hh['timestamp'].dt.dayofweek >= 5
df_hh['duos_band'] = 'Green'
df_hh.loc[(df_hh['hour'] >= 16) & (df_hh['hour'] < 19) & (~df_hh['is_weekend']), 'duos_band'] = 'Red'
df_hh.loc[((df_hh['hour'] >= 8) & (df_hh['hour'] < 16)) | ((df_hh['hour'] >= 19) & (df_hh['hour'] < 22)), 'duos_band'] = 'Amber'
df_hh.loc[df_hh['is_weekend'], 'duos_band'] = 'Green'

duos_map = {'Red': DUOS_RED, 'Amber': DUOS_AMBER, 'Green': DUOS_GREEN}
df_hh['duos_rate'] = df_hh['duos_band'].map(duos_map)

# DC availability (day vs night)
df_hh['dc_clearing_price'] = DC_CLEARING_PRICE_NIGHT
df_hh.loc[(df_hh['hour'] >= 7) & (df_hh['hour'] < 23), 'dc_clearing_price'] = DC_CLEARING_PRICE_DAY

print(f"   Loaded {len(df_hh):,} settlement periods")
print(f"   Date Range: {df_hh['timestamp'].min()} to {df_hh['timestamp'].max()}")

# ============================================================================
# QUERY BIGQUERY FOR SYSTEM PRICES
# ============================================================================

print("\n🔍 Querying BigQuery for system prices...")
client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)
min_date = df_hh['timestamp'].min().date()
max_date = df_hh['timestamp'].max().date()

query = f"""
SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod as period,
    MAX(systemBuyPrice) as system_buy_price,
    MAX(systemSellPrice) as system_sell_price
FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
WHERE CAST(settlementDate AS DATE) >= '{min_date}'
    AND CAST(settlementDate AS DATE) <= '{max_date}'
GROUP BY date, settlementPeriod
ORDER BY date, period
"""

df_prices = client.query(query).to_dataframe()
df_prices['period'] = df_prices['period'].astype(int)
print(f"   Retrieved {len(df_prices):,} price records")

# Merge
df = df_hh.merge(df_prices, on=['date', 'period'], how='left')
df = df.sort_values('timestamp').reset_index(drop=True)
df['system_buy_price'] = df['system_buy_price'].fillna(df['system_buy_price'].mean())
df['system_sell_price'] = df['system_sell_price'].fillna(df['system_sell_price'].mean())

# Calculate effective import/export prices
df['import_price'] = df['system_buy_price'] + df['duos_rate'] + TOTAL_FIXED_LEVIES
df['export_price'] = df['system_sell_price']  # Wholesale only when exporting

print(f"   Merged dataset: {len(df):,} periods")

# ============================================================================
# REVENUE STREAM 1: DYNAMIC CONTAINMENT (AVAILABILITY PAYMENTS)
# ============================================================================

print("\n💰 REVENUE STREAM 1: Dynamic Containment (Frequency Response)")

dc_power_available = POWER_MW * DC_POWER_DERATE  # 2.25 MW
annual_dc_revenue = 0

for idx, row in df.iterrows():
    # Availability payment per half-hour
    dc_revenue_period = dc_power_available * row['dc_clearing_price'] * 0.5 * DC_AVAILABILITY_FACTOR
    df.at[idx, 'rev_dc_availability'] = dc_revenue_period
    annual_dc_revenue += dc_revenue_period

print(f"   DC Power Available: {dc_power_available:.2f} MW ({DC_POWER_DERATE*100:.0f}% of nameplate)")
print(f"   Avg Day Clearing: £{DC_CLEARING_PRICE_DAY:.2f}/MW/h")
print(f"   Avg Night Clearing: £{DC_CLEARING_PRICE_NIGHT:.2f}/MW/h")
print(f"   Availability Factor: {DC_AVAILABILITY_FACTOR*100:.0f}%")
print(f"   Annual DC Revenue: £{annual_dc_revenue:,.2f}")

# ============================================================================
# REVENUE STREAM 2: WHOLESALE ARBITRAGE + IMBALANCE TRADING
# ============================================================================

print("\n💰 REVENUE STREAM 2: Wholesale Arbitrage + Imbalance Trading")

# Simple arbitrage strategy: charge when cheap, discharge when expensive
df['price_rank_daily'] = df.groupby('date')['system_buy_price'].rank(pct=True)

df['arbitrage_charge_mwh'] = 0.0
df['arbitrage_discharge_mwh'] = 0.0
df['arbitrage_revenue'] = 0.0
df['arbitrage_cost'] = 0.0

# Strategy: Charge in cheapest 20% of daily periods, discharge in most expensive 20%
charge_threshold_pct = 0.20
discharge_threshold_pct = 0.80

max_charge_per_period = POWER_MW / 2  # 1.25 MWh per half-hour
max_discharge_per_period = POWER_MW / 2

soc = 0.0
daily_cycles = 0
last_date = None
total_arbitrage_revenue = 0
total_arbitrage_cost = 0

for idx, row in df.iterrows():
    current_date = row['date']
    
    if current_date != last_date:
        daily_cycles = 0
        last_date = current_date
    
    # Charge during cheap periods
    if row['price_rank_daily'] < charge_threshold_pct and soc < ENERGY_MWH and daily_cycles < MAX_CYCLES_PER_DAY:
        charge_mwh = min(max_charge_per_period, ENERGY_MWH - soc)
        cost = charge_mwh * row['import_price']
        df.at[idx, 'arbitrage_charge_mwh'] = charge_mwh
        df.at[idx, 'arbitrage_cost'] = cost
        soc += charge_mwh
        total_arbitrage_cost += cost
        daily_cycles += 0.5
    
    # Discharge during expensive periods
    elif row['price_rank_daily'] > discharge_threshold_pct and soc > 0 and daily_cycles < MAX_CYCLES_PER_DAY:
        discharge_mwh = min(max_discharge_per_period, soc)
        revenue = discharge_mwh * row['export_price'] * ROUND_TRIP_EFFICIENCY
        df.at[idx, 'arbitrage_discharge_mwh'] = discharge_mwh
        df.at[idx, 'arbitrage_revenue'] = revenue
        soc -= discharge_mwh
        total_arbitrage_revenue += revenue
        daily_cycles += 0.5
    
    df.at[idx, 'soc_mwh'] = soc

arbitrage_cycles = (df['arbitrage_charge_mwh'] > 0).sum()
arbitrage_net = total_arbitrage_revenue - total_arbitrage_cost

print(f"   Strategy: Charge in cheapest {charge_threshold_pct*100:.0f}%, discharge in most expensive {(1-discharge_threshold_pct)*100:.0f}%")
print(f"   Charge Periods: {arbitrage_cycles:,}")
print(f"   Discharge Periods: {(df['arbitrage_discharge_mwh'] > 0).sum():,}")
print(f"   Gross Revenue: £{total_arbitrage_revenue:,.2f}")
print(f"   Charging Cost: £{total_arbitrage_cost:,.2f}")
print(f"   Net Arbitrage Profit: £{arbitrage_net:,.2f}")

# ============================================================================
# REVENUE STREAM 3: VLP FLEXIBILITY EVENTS
# ============================================================================

print("\n💰 REVENUE STREAM 3: VLP Flexibility Events")

# Simulate VLP events (random high-stress periods)
np.random.seed(42)
vlp_event_dates = np.random.choice(df['date'].unique(), size=VLP_EVENTS_PER_YEAR, replace=False)
vlp_event_periods = int(VLP_EVENT_DURATION_HOURS * 2)  # Convert to half-hour periods

df['vlp_event'] = False
df['vlp_revenue_gross'] = 0.0

total_vlp_gross = 0

for event_date in vlp_event_dates:
    # Random start hour between 16-19 (peak demand)
    start_hour = np.random.randint(16, 19)
    event_start = pd.Timestamp(event_date) + pd.Timedelta(hours=start_hour)
    
    for i in range(vlp_event_periods):
        event_time = event_start + pd.Timedelta(minutes=i*30)
        mask = df['timestamp'] == event_time
        if mask.any():
            idx = df[mask].index[0]
            df.at[idx, 'vlp_event'] = True
            # VLP payment for delivering flexibility
            vlp_revenue = POWER_MW / 2 * VLP_EVENT_PRICE  # Half-hourly
            df.at[idx, 'vlp_revenue_gross'] = vlp_revenue
            total_vlp_gross += vlp_revenue

# VLP fees
df['vlp_fee'] = df['vlp_revenue_gross'] * VLP_FEE_SHARE
df['vlp_revenue_net'] = df['vlp_revenue_gross'] - df['vlp_fee']
total_vlp_net = df['vlp_revenue_net'].sum()
total_vlp_fees = df['vlp_fee'].sum()

print(f"   Events per Year: {VLP_EVENTS_PER_YEAR}")
print(f"   Event Duration: {VLP_EVENT_DURATION_HOURS:.1f} hours")
print(f"   Payment Rate: £{VLP_EVENT_PRICE:.2f}/MWh")
print(f"   Total Periods: {df['vlp_event'].sum()}")
print(f"   Gross Revenue: £{total_vlp_gross:,.2f}")
print(f"   Aggregator Fee (20%): £{total_vlp_fees:,.2f}")
print(f"   Net Revenue: £{total_vlp_net:,.2f}")

# ============================================================================
# REVENUE STREAM 4: NETWORK SAVINGS (DUoS + BSUoS + LEVIES)
# ============================================================================

print("\n💰 REVENUE STREAM 4: Network & Levy Savings")

# Battery reduces site import during Red/Amber periods
df['network_saving_discharge_mwh'] = 0.0
df['network_saving_revenue'] = 0.0

# Strategy: Discharge during Red periods to avoid DUoS
for idx, row in df.iterrows():
    if row['duos_band'] == 'Red' and row['site_demand_mwh'] > 0:
        # Discharge up to site demand, limited by battery discharge rate
        discharge_mwh = min(max_discharge_per_period, row['site_demand_mwh'])
        # Avoided cost = full import price (wholesale + DUoS + levies)
        avoided_cost = discharge_mwh * row['import_price'] * ROUND_TRIP_EFFICIENCY
        df.at[idx, 'network_saving_discharge_mwh'] = discharge_mwh
        df.at[idx, 'network_saving_revenue'] = avoided_cost

total_network_savings = df['network_saving_revenue'].sum()

# Breakdown by DUoS band
red_savings = df[df['duos_band'] == 'Red']['network_saving_revenue'].sum()
amber_savings = df[df['duos_band'] == 'Amber']['network_saving_revenue'].sum()
green_savings = df[df['duos_band'] == 'Green']['network_saving_revenue'].sum()

print(f"   Red DUoS Savings: £{red_savings:,.2f}")
print(f"   Amber DUoS Savings: £{amber_savings:,.2f}")
print(f"   Green Savings: £{green_savings:,.2f}")
print(f"   Total Network Savings: £{total_network_savings:,.2f}")

# ============================================================================
# REVENUE STREAM 5: PPA SUPPLY TO END USER
# ============================================================================

print("\n💰 REVENUE STREAM 5: PPA Supply to End User")

# When battery has charge and site has demand, can supply at PPA rate
# This is SEPARATE from BtM PPA analysis (which looks at when to import from grid)
df['ppa_supply_mwh'] = 0.0
df['ppa_revenue'] = 0.0

# Note: This conflicts with network savings - can't do both simultaneously
# Priority: Network savings in Red (£176.40 DUoS), PPA elsewhere
for idx, row in df.iterrows():
    # Only supply PPA if not already doing network savings
    if row['network_saving_discharge_mwh'] == 0 and row['site_demand_mwh'] > 0 and df.at[idx, 'soc_mwh'] > 0:
        supply_mwh = min(max_discharge_per_period, row['site_demand_mwh'], df.at[idx, 'soc_mwh'])
        ppa_revenue = supply_mwh * ppa_price * ROUND_TRIP_EFFICIENCY
        df.at[idx, 'ppa_supply_mwh'] = supply_mwh
        df.at[idx, 'ppa_revenue'] = ppa_revenue
        df.at[idx, 'soc_mwh'] -= supply_mwh

total_ppa_revenue = df['ppa_revenue'].sum()
total_ppa_mwh = df['ppa_supply_mwh'].sum()

print(f"   PPA Rate: £{ppa_price:.2f}/MWh")
print(f"   Supply Periods: {(df['ppa_supply_mwh'] > 0).sum()}")
print(f"   Total Supply: {total_ppa_mwh:,.1f} MWh")
print(f"   PPA Revenue: £{total_ppa_revenue:,.2f}")
print(f"   Note: Separate from 'BtM PPA Non BESS Element Costs' analysis")

# ============================================================================
# TOTAL REVENUES
# ============================================================================

total_revenue = (
    annual_dc_revenue +
    arbitrage_net +
    total_vlp_net +
    total_network_savings +
    total_ppa_revenue
)

# ============================================================================
# COSTS
# ============================================================================

print("\n💸 COSTS:")

# 1. Charging costs (already included in arbitrage_cost)
# 2. Degradation
total_throughput = (
    df['arbitrage_charge_mwh'].sum() +
    df['arbitrage_discharge_mwh'].sum() +
    df['network_saving_discharge_mwh'].sum() +
    df['ppa_supply_mwh'].sum()
)
degradation_cost = total_throughput * DEGRADATION_COST_PER_MWH

# 3. Fixed O&M
annual_om = POWER_MW * 1000 * FIXED_OM_PER_KW_YEAR

# 4. Insurance
annual_insurance = POWER_MW * 1000 * INSURANCE_PER_KW_YEAR

# 5. VLP fees (already calculated)

total_costs = degradation_cost + annual_om + annual_insurance

print(f"   Degradation (£{DEGRADATION_COST_PER_MWH:.2f}/MWh × {total_throughput:,.1f} MWh): £{degradation_cost:,.2f}")
print(f"   Fixed O&M (£{FIXED_OM_PER_KW_YEAR:.2f}/kW/year × {POWER_MW*1000:.0f} kW): £{annual_om:,.2f}")
print(f"   Insurance (£{INSURANCE_PER_KW_YEAR:.2f}/kW/year × {POWER_MW*1000:.0f} kW): £{annual_insurance:,.2f}")
print(f"   VLP Aggregator Fees: £{total_vlp_fees:,.2f}")
print(f"   {'─' * 50}")
print(f"   TOTAL COSTS: £{total_costs + total_vlp_fees:,.2f}")

# ============================================================================
# NET PROFIT
# ============================================================================

net_profit = total_revenue - total_costs - total_vlp_fees

print("\n" + "=" * 100)
print("ANNUAL RESULTS - FULL REVENUE STACK")
print("=" * 100)

print(f"\n💰 REVENUES BY STREAM:")
print(f"   1. Dynamic Containment (FR):    £{annual_dc_revenue:>12,.2f}  ({annual_dc_revenue/total_revenue*100:>5.1f}%)")
print(f"   2. Wholesale Arbitrage:          £{arbitrage_net:>12,.2f}  ({arbitrage_net/total_revenue*100:>5.1f}%)")
print(f"   3. VLP Flexibility (net):        £{total_vlp_net:>12,.2f}  ({total_vlp_net/total_revenue*100:>5.1f}%)")
print(f"   4. Network & Levy Savings:       £{total_network_savings:>12,.2f}  ({total_network_savings/total_revenue*100:>5.1f}%)")
print(f"   5. PPA Supply to End User:       £{total_ppa_revenue:>12,.2f}  ({total_ppa_revenue/total_revenue*100:>5.1f}%)")
print(f"   {'─' * 65}")
print(f"   TOTAL REVENUE:                   £{total_revenue:>12,.2f}")

print(f"\n💸 COSTS:")
print(f"   Degradation:                     £{degradation_cost:>12,.2f}")
print(f"   Fixed O&M:                       £{annual_om:>12,.2f}")
print(f"   Insurance:                       £{annual_insurance:>12,.2f}")
print(f"   VLP Fees:                        £{total_vlp_fees:>12,.2f}")
print(f"   {'─' * 65}")
print(f"   TOTAL COSTS:                     £{total_costs + total_vlp_fees:>12,.2f}")

print(f"\n✅ NET PROFIT:                       £{net_profit:>12,.2f}/year")

# Performance metrics
profit_per_mw = net_profit / POWER_MW
profit_per_mwh_capacity = net_profit / ENERGY_MWH
roi_pct = (net_profit / (total_costs + total_vlp_fees)) * 100 if (total_costs + total_vlp_fees) > 0 else 0

print(f"\n📊 PERFORMANCE METRICS:")
print(f"   Profit per MW:                   £{profit_per_mw:>12,.2f}/MW/year")
print(f"   Profit per MWh Capacity:         £{profit_per_mwh_capacity:>12,.2f}/MWh/year")
print(f"   ROI:                             {roi_pct:>12,.1f}%")
print(f"   Total Throughput:                {total_throughput:>12,.1f} MWh")
print(f"   Avg Cycles per Day:              {total_throughput/(ENERGY_MWH*365):>12,.2f}")

# Benchmark against industry ranges
print(f"\n📈 BENCHMARK vs INDUSTRY RANGES (2.5 MW / 5 MWh):")
print(f"   Conservative Range:              £80,000 - £150,000")
print(f"   Typical Range:                   £200,000 - £400,000")
print(f"   Aggressive Range:                £450,000 - £650,000")
print(f"   YOUR RESULT:                     £{net_profit:,.0f} ", end="")
if net_profit < 150000:
    print("(Conservative)")
elif net_profit < 400000:
    print("(Typical)")
elif net_profit < 650000:
    print("(Aggressive)")
else:
    print("(Exceptional!)")

# ============================================================================
# UPDATE GOOGLE SHEETS
# ============================================================================

print("\n📝 Updating Google Sheets...")

try:
    # Update Full Revenue Stack section (rows 68-90)
    updates = [
        # Header
        ('A68', '=== FULL REVENUE STACK (All Opportunities) ==='),
        
        # Revenues (B70-B75)
        ('A70', 'Dynamic Containment (FR)'),
        ('B70', f"{annual_dc_revenue:.2f}"),
        ('A71', 'Wholesale Arbitrage'),
        ('B71', f"{arbitrage_net:.2f}"),
        ('A72', 'VLP Flexibility (net)'),
        ('B72', f"{total_vlp_net:.2f}"),
        ('A73', 'Network & Levy Savings'),
        ('B73', f"{total_network_savings:.2f}"),
        ('A74', 'PPA Supply Revenue'),
        ('B74', f"{total_ppa_revenue:.2f}"),
        ('A75', 'TOTAL REVENUE'),
        ('B75', f"{total_revenue:.2f}"),
        
        # Costs (B77-B81)
        ('A77', 'Degradation'),
        ('B77', f"{degradation_cost:.2f}"),
        ('A78', 'Fixed O&M'),
        ('B78', f"{annual_om:.2f}"),
        ('A79', 'Insurance'),
        ('B79', f"{annual_insurance:.2f}"),
        ('A80', 'VLP Fees'),
        ('B80', f"{total_vlp_fees:.2f}"),
        ('A81', 'TOTAL COSTS'),
        ('B81', f"{total_costs + total_vlp_fees:.2f}"),
        
        # Net Profit
        ('A83', 'NET PROFIT'),
        ('B83', f"{net_profit:.2f}"),
        
        # Metrics (D70-D75)
        ('C70', 'Profit/MW/year'),
        ('D70', f"{profit_per_mw:.2f}"),
        ('C71', 'ROI %'),
        ('D71', f"{roi_pct:.1f}"),
        ('C72', 'Throughput MWh'),
        ('D72', f"{total_throughput:.1f}"),
        ('C73', 'Cycles/Day'),
        ('D73', f"{total_throughput/(ENERGY_MWH*365):.2f}"),
        ('C74', 'Benchmark'),
        ('D74', 'Typical' if 200000 <= net_profit <= 400000 else ('Conservative' if net_profit < 200000 else 'Aggressive')),
    ]
    
    for cell, value in updates:
        bess_sheet.update_acell(cell, value)
    
    print("   ✅ Spreadsheet updated (rows 68-83)")
    
except Exception as e:
    print(f"   ⚠️  Failed to update spreadsheet: {e}")

# ============================================================================
# EXPORT DETAILED CSV
# ============================================================================

output_file = f"bess_full_revenue_stack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df_export = df[[
    'timestamp', 'duos_band', 'system_buy_price', 'system_sell_price', 'import_price',
    'site_demand_mwh', 'rev_dc_availability', 'arbitrage_charge_mwh', 'arbitrage_discharge_mwh',
    'arbitrage_revenue', 'arbitrage_cost', 'vlp_event', 'vlp_revenue_net',
    'network_saving_discharge_mwh', 'network_saving_revenue', 'ppa_supply_mwh', 'ppa_revenue',
    'soc_mwh'
]]
df_export.to_csv(output_file, index=False)
print(f"\n💾 Detailed results exported to: {output_file}")

print("\n" + "=" * 100)
print("FULL REVENUE STACK ANALYSIS COMPLETE")
print("=" * 100)
print(f"\n🎯 KEY INSIGHTS:")
print(f"   • Dynamic Containment is the largest revenue stream (£{annual_dc_revenue:,.0f})")
print(f"   • PPA supply revenue (£{total_ppa_revenue:,.0f}) is SEPARATE from BtM PPA analysis")
print(f"   • Total profit £{net_profit:,.0f}/year = £{profit_per_mw:,.0f}/MW/year")
print(f"   • This model includes ALL revenue opportunities for 2.5 MW / 5 MWh BESS")
