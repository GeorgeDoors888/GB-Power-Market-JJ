#!/usr/bin/env python3
"""
BESS THRESHOLD OPTIMIZATION
============================
Tests multiple threshold combinations to find optimal balance between:
- Cycle frequency (more cycles = more throughput)
- Profit per cycle (higher margins = better quality)

Goal: Maximize annual net profit
"""

import gspread
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime
import itertools

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

# Fixed parameters
ROUND_TRIP_EFFICIENCY = 0.85
DEGRADATION_COST_PER_MWH = 5.0
VLP_FEE_SHARE = 0.20
FIXED_OM_PER_KW_YEAR = 10.0

# Fixed costs (£/MWh)
TOTAL_FIXED_COST = 46.5  # TNUoS(0) + BSUoS(4.5) + CCL(8.56) + RO(14.5) + FiT(7.4) + CfD(9) + ECO(1.75) + WHD(0.75)

# DUoS
DUOS_RED = 176.40
DUOS_AMBER = 20.50
DUOS_GREEN = 1.10

print("=" * 100)
print("BESS THRESHOLD OPTIMIZATION")
print("=" * 100)

# Connect to Google Sheets
print("\n📊 Loading configuration...")
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

# Read BESS config
import_capacity_kw = float(bess_sheet.acell('F13').value or 2500)
export_capacity_kw = float(bess_sheet.acell('F14').value or 2500)
duration_hrs = float(bess_sheet.acell('F15').value or 2)
max_cycles_per_day = float(bess_sheet.acell('F16').value or 4)
ppa_price = float((bess_sheet.acell('D43').value or "150").strip().replace('£', '').replace(',', ''))

capacity_mwh = (import_capacity_kw / 1000) * duration_hrs
max_charge_mwh_per_period = import_capacity_kw / 1000 / 2
max_discharge_mwh_per_period = export_capacity_kw / 1000 / 2
annual_fixed_om = (import_capacity_kw / 1000) * FIXED_OM_PER_KW_YEAR

print(f"   BESS Capacity: {capacity_mwh:.1f} MWh")
print(f"   PPA Rate: £{ppa_price:.2f}/MWh")

# Read HH Data
print("\n📂 Loading demand profile...")
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
print("🔍 Querying BigQuery...")
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

# Define threshold combinations to test
charge_thresholds = [20, 30, 40, 50, 60, 70]
discharge_thresholds = [80, 90, 100, 120, 150, 180]

print(f"\n🔬 Testing {len(charge_thresholds) * len(discharge_thresholds)} threshold combinations...")
print(f"   Charge: {charge_thresholds}")
print(f"   Discharge: {discharge_thresholds}")

results = []

for charge_thresh, discharge_thresh in itertools.product(charge_thresholds, discharge_thresholds):
    # Skip if spread is too narrow (< £20/MWh)
    if discharge_thresh - charge_thresh < 20:
        continue
    
    # Simulate BESS operations
    df_sim = df.copy()
    df_sim['soc_mwh'] = 0.0
    df_sim['charge_mwh'] = 0.0
    df_sim['discharge_vlp_mwh'] = 0.0
    df_sim['discharge_demand_mwh'] = 0.0
    df_sim['avoided_import_mwh'] = 0.0
    
    soc = 0.0
    daily_charges = 0
    daily_discharges = 0
    last_date = None
    
    for idx, row in df_sim.iterrows():
        current_date = row['date']
        
        if current_date != last_date:
            daily_charges = 0
            daily_discharges = 0
            last_date = current_date
        
        system_buy = row['system_buy_price']
        system_sell = row['system_sell_price']
        site_demand_mwh = row['site_baseline_import_mwh']
        import_price = row['import_price_per_mwh']
        
        # Charge
        if system_buy < charge_thresh and soc < capacity_mwh and daily_charges < max_cycles_per_day:
            charge_possible = min(max_charge_mwh_per_period, capacity_mwh - soc)
            df_sim.at[idx, 'charge_mwh'] = charge_possible
            soc += charge_possible
            daily_charges += 1
        
        # Discharge VLP
        if system_sell > discharge_thresh and soc > 0 and daily_discharges < max_cycles_per_day:
            discharge_vlp = min(max_discharge_mwh_per_period, soc)
            df_sim.at[idx, 'discharge_vlp_mwh'] = discharge_vlp
            soc -= discharge_vlp
            daily_discharges += 1
        
        # Discharge demand
        elif soc > 0 and site_demand_mwh > 0 and import_price > ppa_price and daily_discharges < max_cycles_per_day:
            discharge_demand = min(max_discharge_mwh_per_period, soc, site_demand_mwh)
            df_sim.at[idx, 'discharge_demand_mwh'] = discharge_demand
            df_sim.at[idx, 'avoided_import_mwh'] = discharge_demand * ROUND_TRIP_EFFICIENCY
            soc -= discharge_demand
            daily_discharges += 1
        
        df_sim.at[idx, 'soc_mwh'] = soc
    
    # Calculate revenues
    df_sim['rev_avoided_import'] = df_sim['avoided_import_mwh'] * df_sim['import_price_per_mwh']
    df_sim['rev_vlp_energy'] = df_sim['discharge_vlp_mwh'] * df_sim['system_sell_price'] * ROUND_TRIP_EFFICIENCY
    df_sim['rev_vlp_net'] = df_sim['rev_vlp_energy'] * (1 - VLP_FEE_SHARE)
    
    # Calculate costs
    df_sim['cost_charging_energy'] = df_sim['charge_mwh'] * df_sim['import_price_per_mwh']
    df_sim['throughput_mwh'] = df_sim['charge_mwh'] + df_sim['discharge_vlp_mwh'] + df_sim['discharge_demand_mwh']
    df_sim['cost_degradation'] = df_sim['throughput_mwh'] * DEGRADATION_COST_PER_MWH
    
    # Totals
    total_revenue = df_sim['rev_avoided_import'].sum() + df_sim['rev_vlp_net'].sum()
    total_cost = df_sim['cost_charging_energy'].sum() + df_sim['cost_degradation'].sum() + annual_fixed_om
    net_profit = total_revenue - total_cost
    
    charge_periods = (df_sim['charge_mwh'] > 0).sum()
    vlp_periods = (df_sim['discharge_vlp_mwh'] > 0).sum()
    demand_periods = (df_sim['discharge_demand_mwh'] > 0).sum()
    actual_cycles = (charge_periods + vlp_periods + demand_periods) / 2
    throughput = df_sim['throughput_mwh'].sum()
    
    results.append({
        'charge_threshold': charge_thresh,
        'discharge_threshold': discharge_thresh,
        'spread': discharge_thresh - charge_thresh,
        'net_profit': net_profit,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'cycles': actual_cycles,
        'throughput_mwh': throughput,
        'profit_per_cycle': net_profit / actual_cycles if actual_cycles > 0 else 0,
        'profit_per_mwh': net_profit / throughput if throughput > 0 else 0,
        'charge_periods': charge_periods,
        'vlp_periods': vlp_periods,
        'demand_periods': demand_periods,
    })

df_results = pd.DataFrame(results)
df_results = df_results.sort_values('net_profit', ascending=False)

print("\n" + "=" * 100)
print("TOP 10 THRESHOLD COMBINATIONS (by Net Profit)")
print("=" * 100)
print(df_results.head(10).to_string(index=False))

print("\n" + "=" * 100)
print("BEST RESULT:")
print("=" * 100)
best = df_results.iloc[0]
print(f"   Charge Threshold:        £{best['charge_threshold']:.2f}/MWh")
print(f"   Discharge Threshold:     £{best['discharge_threshold']:.2f}/MWh")
print(f"   Price Spread:            £{best['spread']:.2f}/MWh")
print(f"   Net Profit:              £{best['net_profit']:,.2f}/year")
print(f"   Total Revenue:           £{best['total_revenue']:,.2f}")
print(f"   Total Cost:              £{best['total_cost']:,.2f}")
print(f"   Annual Cycles:           {best['cycles']:.0f}")
print(f"   Throughput:              {best['throughput_mwh']:,.1f} MWh")
print(f"   Profit per Cycle:        £{best['profit_per_cycle']:,.2f}")
print(f"   Profit per MWh:          £{best['profit_per_mwh']:,.2f}")
print(f"   Charge Periods:          {best['charge_periods']:.0f}")
print(f"   VLP Periods:             {best['vlp_periods']:.0f}")
print(f"   Demand Periods:          {best['demand_periods']:.0f}")

# Export results
output_file = f"bess_threshold_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df_results.to_csv(output_file, index=False)
print(f"\n💾 Full results exported to: {output_file}")

# Update BESS sheet with recommendation
print("\n📝 Updating BESS sheet with recommendation...")
try:
    bess_sheet.update_acell('B65', f"OPTIMAL: Charge <£{best['charge_threshold']:.0f}, Discharge >£{best['discharge_threshold']:.0f}")
    bess_sheet.update_acell('B66', f"Expected Profit: £{best['net_profit']:,.2f}/year")
    print("   ✅ Recommendation written to B65-B66")
except Exception as e:
    print(f"   ⚠️  Failed to update sheet: {e}")

print("\n" + "=" * 100)
print("OPTIMIZATION COMPLETE")
print("=" * 100)
