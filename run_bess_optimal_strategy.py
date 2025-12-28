#!/usr/bin/env python3
"""
BESS OPTIMAL STRATEGY EXECUTION
================================
Runs the optimal threshold strategy (£20 charge / £180 discharge)
and updates Google Sheets with comprehensive revenue breakdown.

Based on threshold optimization showing:
- £36,671 annual profit (best of 36 combinations tested)
- 536 cycles/year (36.7% utilization)
- £68.42 profit per cycle
- 694 demand discharge periods, 0 VLP periods
"""

import gspread
import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# OPTIMAL THRESHOLDS (from optimization)
CHARGE_THRESHOLD = 20.0  # £20/MWh
DISCHARGE_VLP_THRESHOLD = 180.0  # £180/MWh (rarely met, focus on demand)
ROUND_TRIP_EFFICIENCY = 0.85
DEGRADATION_COST_PER_MWH = 5.0
VLP_FEE_SHARE = 0.20
FIXED_OM_PER_KW_YEAR = 10.0

# Fixed costs
TOTAL_FIXED_COST = 46.5
DUOS_RED = 176.40
DUOS_AMBER = 20.50
DUOS_GREEN = 1.10

print("=" * 100)
print("BESS OPTIMAL STRATEGY EXECUTION")
print("=" * 100)
print(f"\n⚙️  OPTIMAL THRESHOLDS:")
print(f"   Charge: < £{CHARGE_THRESHOLD:.2f}/MWh")
print(f"   Discharge VLP: > £{DISCHARGE_VLP_THRESHOLD:.2f}/MWh")
print(f"   Discharge Demand: When import price > PPA (£150/MWh)")

# Connect to Google Sheets
print("\n📊 Connecting to Google Sheets...")
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

# Read BESS config
print("\n🔋 Reading BESS Configuration...")
import_capacity_kw = float(bess_sheet.acell('F13').value or 2500)
export_capacity_kw = float(bess_sheet.acell('F14').value or 2500)
duration_hrs = float(bess_sheet.acell('F15').value or 2)
max_cycles_per_day = float(bess_sheet.acell('F16').value or 4)
ppa_price = float((bess_sheet.acell('D43').value or "150").strip().replace('£', '').replace(',', ''))

capacity_mwh = (import_capacity_kw / 1000) * duration_hrs
max_charge_mwh_per_period = import_capacity_kw / 1000 / 2
max_discharge_mwh_per_period = export_capacity_kw / 1000 / 2
annual_fixed_om = (import_capacity_kw / 1000) * FIXED_OM_PER_KW_YEAR

print(f"   Capacity: {capacity_mwh:.1f} MWh")
print(f"   PPA: £{ppa_price:.2f}/MWh")

# Read HH Data
print("\n📂 Loading site demand profile...")
hh_data = hh_sheet.get_all_records()
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['date'] = df_hh['timestamp'].dt.date
df_hh['period'] = ((df_hh['timestamp'].dt.hour * 2) + (df_hh['timestamp'].dt.minute // 30) + 1)
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['site_baseline_import_mwh'] = df_hh['demand_kw'] / 1000 / 2

# Calculate DUoS
df_hh['hour'] = df_hh['timestamp'].dt.hour
df_hh['is_weekend'] = df_hh['timestamp'].dt.dayofweek >= 5
df_hh['duos_band'] = 'Green'
df_hh.loc[(df_hh['hour'] >= 16) & (df_hh['hour'] < 19) & (~df_hh['is_weekend']), 'duos_band'] = 'Red'
df_hh.loc[((df_hh['hour'] >= 8) & (df_hh['hour'] < 16)) | ((df_hh['hour'] >= 19) & (df_hh['hour'] < 22)), 'duos_band'] = 'Amber'
df_hh.loc[df_hh['is_weekend'], 'duos_band'] = 'Green'
duos_map = {'Red': DUOS_RED, 'Amber': DUOS_AMBER, 'Green': DUOS_GREEN}
df_hh['duos_rate'] = df_hh['duos_band'].map(duos_map)

# Query BigQuery
print("🔍 Querying BigQuery for system prices...")
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
"""

df_prices = client.query(query).to_dataframe()
df_prices['period'] = df_prices['period'].astype(int)

# Merge
df = df_hh.merge(df_prices, on=['date', 'period'], how='left')
df = df.sort_values('timestamp').reset_index(drop=True)
df['system_buy_price'] = df['system_buy_price'].fillna(df['system_buy_price'].mean())
df['system_sell_price'] = df['system_sell_price'].fillna(df['system_sell_price'].mean())
df['import_price_per_mwh'] = df['system_buy_price'] + df['duos_rate'] + TOTAL_FIXED_COST

print(f"   Loaded {len(df):,} periods")

# BESS Simulation
print("\n⚡ Simulating BESS with optimal thresholds...")
df['soc_mwh'] = 0.0
df['charge_mwh'] = 0.0
df['discharge_vlp_mwh'] = 0.0
df['discharge_demand_mwh'] = 0.0
df['avoided_import_mwh'] = 0.0

soc = 0.0
daily_charges = 0
daily_discharges = 0
last_date = None

for idx, row in df.iterrows():
    current_date = row['date']
    
    if current_date != last_date:
        daily_charges = 0
        daily_discharges = 0
        last_date = current_date
    
    system_buy = row['system_buy_price']
    system_sell = row['system_sell_price']
    site_demand_mwh = row['site_baseline_import_mwh']
    import_price = row['import_price_per_mwh']
    
    # Charge (very selective - only when wholesale < £20)
    if system_buy < CHARGE_THRESHOLD and soc < capacity_mwh and daily_charges < max_cycles_per_day:
        charge_possible = min(max_charge_mwh_per_period, capacity_mwh - soc)
        df.at[idx, 'charge_mwh'] = charge_possible
        soc += charge_possible
        daily_charges += 1
    
    # Discharge VLP (almost never - wholesale > £180 is rare)
    if system_sell > DISCHARGE_VLP_THRESHOLD and soc > 0 and daily_discharges < max_cycles_per_day:
        discharge_vlp = min(max_discharge_mwh_per_period, soc)
        df.at[idx, 'discharge_vlp_mwh'] = discharge_vlp
        soc -= discharge_vlp
        daily_discharges += 1
    
    # Discharge to meet demand (primary strategy)
    elif soc > 0 and site_demand_mwh > 0 and import_price > ppa_price and daily_discharges < max_cycles_per_day:
        discharge_demand = min(max_discharge_mwh_per_period, soc, site_demand_mwh)
        df.at[idx, 'discharge_demand_mwh'] = discharge_demand
        df.at[idx, 'avoided_import_mwh'] = discharge_demand * ROUND_TRIP_EFFICIENCY
        soc -= discharge_demand
        daily_discharges += 1
    
    df.at[idx, 'soc_mwh'] = soc

# Calculate revenues and costs
print("💰 Calculating financials...")

# Revenues
df['rev_avoided_import'] = df['avoided_import_mwh'] * df['import_price_per_mwh']
df['rev_vlp_energy'] = df['discharge_vlp_mwh'] * df['system_sell_price'] * ROUND_TRIP_EFFICIENCY
df['rev_vlp_net'] = df['rev_vlp_energy'] * (1 - VLP_FEE_SHARE)

# Costs
df['cost_charging_energy'] = df['charge_mwh'] * df['import_price_per_mwh']
df['throughput_mwh'] = df['charge_mwh'] + df['discharge_vlp_mwh'] + df['discharge_demand_mwh']
df['cost_degradation'] = df['throughput_mwh'] * DEGRADATION_COST_PER_MWH

# Profit
df['profit_per_period'] = df['rev_avoided_import'] + df['rev_vlp_net'] - df['cost_charging_energy'] - df['cost_degradation']

# Aggregate results
total_avoided_import = df['rev_avoided_import'].sum()
total_vlp_gross = df['rev_vlp_energy'].sum()
total_vlp_fees = (df['rev_vlp_energy'] * VLP_FEE_SHARE).sum()
total_vlp_net = df['rev_vlp_net'].sum()
total_revenue = total_avoided_import + total_vlp_net

total_charge_cost = df['cost_charging_energy'].sum()
total_deg_cost = df['cost_degradation'].sum()
total_cost = total_charge_cost + total_deg_cost + annual_fixed_om

net_profit = total_revenue - total_cost

charge_periods = (df['charge_mwh'] > 0).sum()
vlp_periods = (df['discharge_vlp_mwh'] > 0).sum()
demand_periods = (df['discharge_demand_mwh'] > 0).sum()
total_charge_mwh = df['charge_mwh'].sum()
total_vlp_mwh = df['discharge_vlp_mwh'].sum()
total_demand_mwh = df['discharge_demand_mwh'].sum()
total_throughput = df['throughput_mwh'].sum()
actual_cycles = (charge_periods + vlp_periods + demand_periods) / 2

# Print results
print("\n" + "=" * 100)
print("RESULTS - OPTIMAL STRATEGY")
print("=" * 100)

print(f"\n💰 REVENUES:")
print(f"   Avoided Import:       £{total_avoided_import:>12,.2f}")
print(f"   VLP Net:              £{total_vlp_net:>12,.2f}")
print(f"   {'─' * 40}")
print(f"   TOTAL:                £{total_revenue:>12,.2f}")

print(f"\n💸 COSTS:")
print(f"   Charging:             £{total_charge_cost:>12,.2f}")
print(f"   Degradation:          £{total_deg_cost:>12,.2f}")
print(f"   Fixed O&M:            £{annual_fixed_om:>12,.2f}")
print(f"   {'─' * 40}")
print(f"   TOTAL:                £{total_cost:>12,.2f}")

print(f"\n✅ NET PROFIT:            £{net_profit:>12,.2f}/year")

print(f"\n⚡ OPERATIONS:")
print(f"   Charge Periods:       {charge_periods:>12,} ({total_charge_mwh:,.1f} MWh)")
print(f"   VLP Periods:          {vlp_periods:>12,} ({total_vlp_mwh:,.1f} MWh)")
print(f"   Demand Periods:       {demand_periods:>12,} ({total_demand_mwh:,.1f} MWh)")
print(f"   Annual Cycles:        {actual_cycles:>12,.0f}")
print(f"   Utilization:          {(actual_cycles/1460)*100:>12,.1f}%")

# Update Google Sheets
print("\n📝 Updating Google Sheets...")

updates = [
    # Revenue (B51-B55)
    ('B51', f"{total_avoided_import:.2f}"),
    ('B52', f"{total_vlp_gross:.2f}"),
    ('B53', f"{total_vlp_fees:.2f}"),
    ('B54', f"{total_vlp_net:.2f}"),
    ('B55', f"{total_revenue:.2f}"),
    
    # Costs (B57-B61)
    ('B57', f"{total_charge_cost:.2f}"),
    ('B58', f"0.00"),  # Efficiency losses embedded in avoided import
    ('B59', f"{total_deg_cost:.2f}"),
    ('B60', f"{annual_fixed_om:.2f}"),
    ('B61', f"{total_cost:.2f}"),
    
    # Net profit (B63)
    ('B63', f"{net_profit:.2f}"),
    
    # Operations (D51-D61)
    ('D51', f"{charge_periods}"),
    ('D52', f"{total_charge_mwh:.1f}"),
    ('D53', f"{vlp_periods}"),
    ('D54', f"{total_vlp_mwh:.1f}"),
    ('D55', f"{demand_periods}"),
    ('D56', f"{total_demand_mwh:.1f}"),
    ('D58', f"{actual_cycles:.0f}"),
    ('D59', f"{(actual_cycles/1460)*100:.1f}"),
    ('D60', f"{net_profit/total_throughput:.2f}"),
    ('D61', f"{net_profit/(import_capacity_kw/1000):.2f}"),
    
    # Recommendation (B65-B66)
    ('B65', f"OPTIMAL: Charge <£{CHARGE_THRESHOLD:.0f}, Discharge when import >£{ppa_price:.0f}"),
    ('B66', f"Expected Profit: £{net_profit:,.2f}/year | {actual_cycles:.0f} cycles | {(actual_cycles/1460)*100:.1f}% utilization"),
]

for cell, value in updates:
    try:
        bess_sheet.update_acell(cell, value)
    except Exception as e:
        print(f"   ⚠️  Failed to update {cell}: {e}")

print("   ✅ Spreadsheet updated")

# Export CSV
output_file = f"bess_optimal_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df_export = df[['timestamp', 'duos_band', 'system_buy_price', 'system_sell_price',
                'import_price_per_mwh', 'site_baseline_import_mwh', 'charge_mwh',
                'discharge_vlp_mwh', 'discharge_demand_mwh', 'soc_mwh',
                'rev_avoided_import', 'cost_charging_energy', 'cost_degradation',
                'profit_per_period']]
df_export.to_csv(output_file, index=False)
print(f"\n💾 Detailed results exported to: {output_file}")

print("\n" + "=" * 100)
print("OPTIMAL STRATEGY EXECUTION COMPLETE")
print("=" * 100)
print(f"\n🎯 KEY TAKEAWAY:")
print(f"   Focus on AVOIDED IMPORT (not VLP) by:")
print(f"   1. Charging only when wholesale < £{CHARGE_THRESHOLD:.0f}/MWh (very selective)")
print(f"   2. Discharging when import price > £{ppa_price:.0f}/MWh PPA (retail arbitrage)")
print(f"   3. Result: £{net_profit:,.2f}/year profit, {actual_cycles:.0f} cycles, £{net_profit/actual_cycles:.2f}/cycle")
