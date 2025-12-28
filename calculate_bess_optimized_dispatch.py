#!/usr/bin/env python3
"""
BESS OPTIMIZED DISPATCH MODEL
==============================
Realistic revenue model with priority-based dispatch that prevents double-counting.

DISPATCH PRIORITY (per settlement period):
1. Dynamic Containment - Reserve capacity (always earning, low utilization)
2. Network Savings - Discharge during Red DUoS to avoid £176/MWh charges
3. Wholesale Arbitrage - Charge low, discharge high (market optimization)
4. VLP Events - When called by aggregator (premium rates)
5. PPA Supply - Supply end-user demand at £150/MWh (residual capacity)

REALISTIC ASSUMPTIONS:
- DC earns availability payments but doesn't prevent other uses (just reserves capacity)
- Can't do network savings AND PPA supply simultaneously (same energy)
- Arbitrage uses spare capacity not needed for site demand
- VLP events override other strategies (highest £/MWh)

EXPECTED RANGE: £200-400k/year (typical for 2.5 MW / 5 MWh BTM BESS)
"""

import gspread
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# BESS Parameters
POWER_MW = 2.5
ENERGY_MWH = 5.0
ROUND_TRIP_EFFICIENCY = 0.85
MAX_CYCLES_PER_DAY = 1.5

# Costs
DEGRADATION_COST_PER_MWH = 5.0
VLP_FEE_SHARE = 0.20
FIXED_OM_PER_KW_YEAR = 10.0
INSURANCE_PER_KW_YEAR = 2.0

# Revenue Parameters
DC_CLEARING_PRICE_DAY = 15.0  # £/MW/h
DC_CLEARING_PRICE_NIGHT = 5.0  # £/MW/h
DC_AVAILABILITY_FACTOR = 0.85
DC_POWER_DERATE = 0.90  # 10% reserved for DC response

VLP_EVENT_PRICE = 80.0  # £/MWh
VLP_EVENTS_PER_YEAR = 40
VLP_EVENT_DURATION_HOURS = 2.0

# Fixed costs
TOTAL_FIXED_LEVIES = 46.5  # TNUoS(0) + BSUoS + CCL + RO + FiT + CfD + ECO + WHD
DUOS_RED = 176.40
DUOS_AMBER = 20.50
DUOS_GREEN = 1.10

print("=" * 100)
print("BESS OPTIMIZED DISPATCH MODEL - 2.5 MW / 5 MWh")
print("=" * 100)
print(f"\n⚙️  Configuration: {POWER_MW:.1f} MW / {ENERGY_MWH:.1f} MWh ({ENERGY_MWH/POWER_MW:.1f}h duration)")

# Connect to sheets
print("\n📊 Connecting to Google Sheets...")
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

ppa_price = float((bess_sheet.acell('D43').value or "150").strip().replace('£', '').replace(',', ''))

# Load site demand
print("📂 Loading site demand...")
hh_data = hh_sheet.get_all_records()
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['date'] = df_hh['timestamp'].dt.date
df_hh['period'] = ((df_hh['timestamp'].dt.hour * 2) + (df_hh['timestamp'].dt.minute // 30) + 1)
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['site_demand_mwh'] = df_hh['demand_kw'] / 1000 / 2

# DUoS bands
df_hh['hour'] = df_hh['timestamp'].dt.hour
df_hh['is_weekend'] = df_hh['timestamp'].dt.dayofweek >= 5
df_hh['duos_band'] = 'Green'
df_hh.loc[(df_hh['hour'] >= 16) & (df_hh['hour'] < 19) & (~df_hh['is_weekend']), 'duos_band'] = 'Red'
df_hh.loc[((df_hh['hour'] >= 8) & (df_hh['hour'] < 16)) | ((df_hh['hour'] >= 19) & (df_hh['hour'] < 22)), 'duos_band'] = 'Amber'
df_hh.loc[df_hh['is_weekend'], 'duos_band'] = 'Green'
duos_map = {'Red': DUOS_RED, 'Amber': DUOS_AMBER, 'Green': DUOS_GREEN}
df_hh['duos_rate'] = df_hh['duos_band'].map(duos_map)

# DC clearing prices
df_hh['dc_clearing_price'] = DC_CLEARING_PRICE_NIGHT
df_hh.loc[(df_hh['hour'] >= 7) & (df_hh['hour'] < 23), 'dc_clearing_price'] = DC_CLEARING_PRICE_DAY

# Load prices
print("🔍 Querying BigQuery...")
client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)
min_date, max_date = df_hh['timestamp'].min().date(), df_hh['timestamp'].max().date()

query = f"""
SELECT CAST(settlementDate AS DATE) as date, settlementPeriod as period,
       MAX(systemBuyPrice) as system_buy_price, MAX(systemSellPrice) as system_sell_price
FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
WHERE CAST(settlementDate AS DATE) BETWEEN '{min_date}' AND '{max_date}'
GROUP BY date, settlementPeriod
"""

df_prices = client.query(query).to_dataframe()
df_prices['period'] = df_prices['period'].astype(int)

# Merge
df = df_hh.merge(df_prices, on=['date', 'period'], how='left')
df = df.sort_values('timestamp').reset_index(drop=True)
df['system_buy_price'].fillna(df['system_buy_price'].mean(), inplace=True)
df['system_sell_price'].fillna(df['system_sell_price'].mean(), inplace=True)
df['import_price'] = df['system_buy_price'] + df['duos_rate'] + TOTAL_FIXED_LEVIES

# Simulate VLP events
np.random.seed(42)
vlp_event_dates = np.random.choice(df['date'].unique(), size=VLP_EVENTS_PER_YEAR, replace=False)
vlp_event_periods = int(VLP_EVENT_DURATION_HOURS * 2)
df['vlp_event'] = False

for event_date in vlp_event_dates:
    start_hour = np.random.randint(16, 19)
    event_start = pd.Timestamp(event_date) + pd.Timedelta(hours=start_hour)
    for i in range(vlp_event_periods):
        mask = df['timestamp'] == (event_start + pd.Timedelta(minutes=i*30))
        df.loc[mask, 'vlp_event'] = True

print(f"   Loaded {len(df):,} periods")

# ============================================================================
# OPTIMIZED DISPATCH SIMULATION
# ============================================================================

print("\n⚡ Simulating Optimized Dispatch...")

# Initialize state
df['soc_mwh'] = 0.0
df['action'] = 'IDLE'
df['action_mwh'] = 0.0
df['revenue'] = 0.0
df['cost'] = 0.0

# Revenue tracking
df['rev_dc'] = 0.0
df['rev_network_saving'] = 0.0
df['rev_arbitrage'] = 0.0
df['rev_vlp'] = 0.0
df['rev_ppa'] = 0.0

max_charge_per_period = POWER_MW / 2
max_discharge_per_period = POWER_MW / 2
dc_power = POWER_MW * DC_POWER_DERATE

soc = 0.0
daily_cycles = 0
last_date = None

# First pass: rank periods for arbitrage strategy
df['price_rank_daily'] = df.groupby('date')['system_buy_price'].rank(pct=True)

for idx, row in df.iterrows():
    current_date = row['date']
    
    if current_date != last_date:
        daily_cycles = 0
        last_date = current_date
    
    # ========================================================================
    # REVENUE 1: Dynamic Containment (always earning, doesn't block other actions)
    # ========================================================================
    dc_revenue = dc_power * row['dc_clearing_price'] * 0.5 * DC_AVAILABILITY_FACTOR
    df.at[idx, 'rev_dc'] = dc_revenue
    
    # ========================================================================
    # PRIORITY 1: VLP Events (highest priority when called)
    # ========================================================================
    if row['vlp_event'] and daily_cycles < MAX_CYCLES_PER_DAY:
        # Discharge for VLP event
        discharge_mwh = min(max_discharge_per_period, soc) if soc > 0 else 0
        if discharge_mwh > 0:
            revenue_gross = discharge_mwh * VLP_EVENT_PRICE * ROUND_TRIP_EFFICIENCY
            vlp_fee = revenue_gross * VLP_FEE_SHARE
            revenue_net = revenue_gross - vlp_fee
            
            df.at[idx, 'action'] = 'VLP_DISCHARGE'
            df.at[idx, 'action_mwh'] = discharge_mwh
            df.at[idx, 'rev_vlp'] = revenue_net
            df.at[idx, 'revenue'] = revenue_net
            soc -= discharge_mwh
            daily_cycles += 0.5
    
    # ========================================================================
    # PRIORITY 2: Network Savings (Red DUoS avoidance)
    # ========================================================================
    elif row['duos_band'] == 'Red' and row['site_demand_mwh'] > 0 and soc > 0 and daily_cycles < MAX_CYCLES_PER_DAY:
        # Discharge to avoid Red DUoS (£176.40/MWh)
        discharge_mwh = min(max_discharge_per_period, soc, row['site_demand_mwh'])
        avoided_cost = discharge_mwh * row['import_price'] * ROUND_TRIP_EFFICIENCY
        
        df.at[idx, 'action'] = 'RED_DUOS_AVOID'
        df.at[idx, 'action_mwh'] = discharge_mwh
        df.at[idx, 'rev_network_saving'] = avoided_cost
        df.at[idx, 'revenue'] = avoided_cost
        soc -= discharge_mwh
        daily_cycles += 0.5
    
    # ========================================================================
    # PRIORITY 3: Arbitrage Charging (cheapest 20% of day)
    # ========================================================================
    elif row['price_rank_daily'] < 0.20 and soc < ENERGY_MWH and daily_cycles < MAX_CYCLES_PER_DAY:
        charge_mwh = min(max_charge_per_period, ENERGY_MWH - soc)
        charge_cost = charge_mwh * row['import_price']
        
        df.at[idx, 'action'] = 'ARBITRAGE_CHARGE'
        df.at[idx, 'action_mwh'] = charge_mwh
        df.at[idx, 'cost'] = charge_cost
        soc += charge_mwh
        daily_cycles += 0.5
    
    # ========================================================================
    # PRIORITY 4: Arbitrage Discharging (most expensive 20% of day)
    # ========================================================================
    elif row['price_rank_daily'] > 0.80 and soc > 0 and daily_cycles < MAX_CYCLES_PER_DAY:
        discharge_mwh = min(max_discharge_per_period, soc)
        revenue = discharge_mwh * row['system_sell_price'] * ROUND_TRIP_EFFICIENCY
        
        df.at[idx, 'action'] = 'ARBITRAGE_DISCHARGE'
        df.at[idx, 'action_mwh'] = discharge_mwh
        df.at[idx, 'rev_arbitrage'] = revenue
        df.at[idx, 'revenue'] = revenue
        soc -= discharge_mwh
        daily_cycles += 0.5
    
    # ========================================================================
    # PRIORITY 5: PPA Supply (residual - if battery has charge and site has demand)
    # ========================================================================
    elif row['site_demand_mwh'] > 0 and soc > 0 and row['import_price'] > ppa_price and daily_cycles < MAX_CYCLES_PER_DAY:
        # Only supply if avoiding import is better than waiting for arbitrage
        supply_mwh = min(max_discharge_per_period, soc, row['site_demand_mwh'])
        ppa_revenue = supply_mwh * ppa_price * ROUND_TRIP_EFFICIENCY
        
        df.at[idx, 'action'] = 'PPA_SUPPLY'
        df.at[idx, 'action_mwh'] = supply_mwh
        df.at[idx, 'rev_ppa'] = ppa_revenue
        df.at[idx, 'revenue'] = ppa_revenue
        soc -= supply_mwh
        daily_cycles += 0.5
    
    df.at[idx, 'soc_mwh'] = soc

# ============================================================================
# CALCULATE TOTALS
# ============================================================================

print("\n💰 Calculating Results...")

# Revenues
rev_dc_total = df['rev_dc'].sum()
rev_network_total = df['rev_network_saving'].sum()
rev_arbitrage_charge_cost = df[df['action'] == 'ARBITRAGE_CHARGE']['cost'].sum()
rev_arbitrage_discharge = df['rev_arbitrage'].sum()
rev_arbitrage_net = rev_arbitrage_discharge - rev_arbitrage_charge_cost
rev_vlp_total = df['rev_vlp'].sum()
rev_ppa_total = df['rev_ppa'].sum()

total_revenue = rev_dc_total + rev_network_total + rev_arbitrage_net + rev_vlp_total + rev_ppa_total

# Costs
total_throughput = df['action_mwh'].sum()
degradation_cost = total_throughput * DEGRADATION_COST_PER_MWH
annual_om = POWER_MW * 1000 * FIXED_OM_PER_KW_YEAR
annual_insurance = POWER_MW * 1000 * INSURANCE_PER_KW_YEAR
vlp_fees = df['rev_vlp'].sum() * VLP_FEE_SHARE / (1 - VLP_FEE_SHARE)  # Gross up to get fee

total_costs = degradation_cost + annual_om + annual_insurance + vlp_fees

net_profit = total_revenue - total_costs

# Action counts
action_counts = df['action'].value_counts()

print("\n" + "=" * 100)
print("OPTIMIZED DISPATCH RESULTS")
print("=" * 100)

print(f"\n💰 REVENUES:")
print(f"   Dynamic Containment:         £{rev_dc_total:>12,.2f}  (always earning)")
print(f"   Network Savings (Red DUoS):  £{rev_network_total:>12,.2f}  ({action_counts.get('RED_DUOS_AVOID', 0)} periods)")
print(f"   Arbitrage (net):             £{rev_arbitrage_net:>12,.2f}  ({action_counts.get('ARBITRAGE_CHARGE', 0)} charge, {action_counts.get('ARBITRAGE_DISCHARGE', 0)} discharge)")
print(f"   VLP Events (net):            £{rev_vlp_total:>12,.2f}  ({action_counts.get('VLP_DISCHARGE', 0)} periods)")
print(f"   PPA Supply:                  £{rev_ppa_total:>12,.2f}  ({action_counts.get('PPA_SUPPLY', 0)} periods)")
print(f"   {'─' * 65}")
print(f"   TOTAL REVENUE:               £{total_revenue:>12,.2f}")

print(f"\n💸 COSTS:")
print(f"   Degradation:                 £{degradation_cost:>12,.2f}  ({total_throughput:,.1f} MWh)")
print(f"   Fixed O&M:                   £{annual_om:>12,.2f}")
print(f"   Insurance:                   £{annual_insurance:>12,.2f}")
print(f"   VLP Aggregator Fees:         £{vlp_fees:>12,.2f}")
print(f"   {'─' * 65}")
print(f"   TOTAL COSTS:                 £{total_costs:>12,.2f}")

print(f"\n✅ NET PROFIT:                   £{net_profit:>12,.2f}/year")

print(f"\n📊 PERFORMANCE:")
print(f"   Profit per MW:               £{net_profit/POWER_MW:>12,.2f}/MW/year")
print(f"   ROI:                         {(net_profit/total_costs)*100:>12,.1f}%")
print(f"   Throughput:                  {total_throughput:>12,.1f} MWh/year")
print(f"   Avg Cycles/Day:              {total_throughput/(ENERGY_MWH*365):>12,.2f}")

print(f"\n📈 BENCHMARK:")
print(f"   Conservative (£80-150k):     ", end="")
print("✅" if 80000 <= net_profit <= 150000 else "")
print(f"\n   Typical (£200-400k):         ", end="")
print("✅" if 200000 <= net_profit <= 400000 else "")
print(f"\n   Aggressive (£450-650k):      ", end="")
print("✅" if 450000 <= net_profit <= 650000 else "")
print(f"\n   YOUR RESULT:                 £{net_profit:,.0f}")

# Update sheets
print("\n📝 Updating Google Sheets (rows 85-105)...")
try:
    updates = [
        ('A85', '=== OPTIMIZED DISPATCH MODEL (Realistic) ==='),
        ('A87', 'Dynamic Containment'), ('B87', f"{rev_dc_total:.2f}"),
        ('A88', 'Network Savings'), ('B88', f"{rev_network_total:.2f}"),
        ('A89', 'Arbitrage (net)'), ('B89', f"{rev_arbitrage_net:.2f}"),
        ('A90', 'VLP Events'), ('B90', f"{rev_vlp_total:.2f}"),
        ('A91', 'PPA Supply'), ('B91', f"{rev_ppa_total:.2f}"),
        ('A92', 'TOTAL REVENUE'), ('B92', f"{total_revenue:.2f}"),
        ('A94', 'Degradation'), ('B94', f"{degradation_cost:.2f}"),
        ('A95', 'O&M + Insurance'), ('B95', f"{annual_om + annual_insurance:.2f}"),
        ('A96', 'VLP Fees'), ('B96', f"{vlp_fees:.2f}"),
        ('A97', 'TOTAL COSTS'), ('B97', f"{total_costs:.2f}"),
        ('A99', 'NET PROFIT'), ('B99', f"{net_profit:.2f}"),
        ('C87', '£/MW/year'), ('D87', f"{net_profit/POWER_MW:.2f}"),
        ('C88', 'ROI %'), ('D88', f"{(net_profit/total_costs)*100:.1f}"),
        ('C89', 'Throughput MWh'), ('D89', f"{total_throughput:.1f}"),
        ('C90', 'Cycles/Day'), ('D90', f"{total_throughput/(ENERGY_MWH*365):.2f}"),
    ]
    
    for cell, value in updates:
        bess_sheet.update_acell(cell, value)
    print("   ✅ Updated")
except Exception as e:
    print(f"   ⚠️  {e}")

# Export
output_file = f"bess_optimized_dispatch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df[['timestamp', 'duos_band', 'system_buy_price', 'import_price', 'site_demand_mwh',
    'action', 'action_mwh', 'soc_mwh', 'rev_dc', 'rev_network_saving',
    'rev_arbitrage', 'rev_vlp', 'rev_ppa', 'revenue', 'cost']].to_csv(output_file, index=False)
print(f"\n💾 Exported: {output_file}")

print("\n" + "=" * 100)
print("COMPLETE - Realistic optimized dispatch prevents double-counting")
print("=" * 100)
