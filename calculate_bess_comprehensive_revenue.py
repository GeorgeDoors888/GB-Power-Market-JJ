#!/usr/bin/env python3
"""
COMPREHENSIVE BESS REVENUE MODEL
================================
Calculates all revenue streams and costs for a behind-the-meter BESS:

REVENUE STREAMS:
1. Avoided import cost - discharge reduces site import, avoiding wholesale + network + levies
2. VLP/SO revenue - selling flexibility to system operator (BM, balancing services)
3. Availability payments - capacity payments for being available (e.g., Dynamic Containment)

COSTS:
1. Charging cost - energy + network + levies when charging from grid
2. Round-trip efficiency losses
3. Battery degradation (£/MWh throughput)
4. VLP service fees (% of ESO revenues)
5. Fixed O&M (£/kW/year)

CRITICAL: Avoids double-counting when battery both:
- Reduces site import (avoided cost)
- Provides VLP flexibility (SO payment)
These are separate, legitimate revenue streams.
"""

import gspread
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

# BESS Operating Parameters
CHARGE_THRESHOLD = 50.0  # Charge when system price < £50/MWh
DISCHARGE_VLP_THRESHOLD = 100.0  # Discharge for VLP when system sell price > £100/MWh
ROUND_TRIP_EFFICIENCY = 0.85  # 85% round-trip efficiency

# Cost Parameters
DEGRADATION_COST_PER_MWH = 5.0  # £/MWh throughput (includes both charge + discharge)
VLP_FEE_SHARE = 0.20  # 20% of VLP revenues to aggregator
FIXED_OM_PER_KW_YEAR = 10.0  # £/kW/year fixed O&M

# Fixed Costs (£/MWh) - from BtM PPA analysis
TNUOS_COST = 0.00  # £/MWh (set to zero per user)
BSUOS_COST = 4.50  # £/MWh
CCL_COST = 8.56  # £/MWh
RO_COST = 14.50  # £/MWh
FIT_COST = 7.40  # £/MWh
CFD_COST = 9.00  # £/MWh
ECO_COST = 1.75  # £/MWh
WHD_COST = 0.75  # £/MWh
TOTAL_FIXED_COST = TNUOS_COST + BSUOS_COST + CCL_COST + RO_COST + FIT_COST + CFD_COST + ECO_COST + WHD_COST

# DUoS Charges (£/MWh) - time-of-use
DUOS_RED = 176.40  # 16:00-19:00
DUOS_AMBER = 20.50  # 08:00-16:00, 19:00-22:00
DUOS_GREEN = 1.10  # 22:00-08:00

print("=" * 100)
print("COMPREHENSIVE BESS REVENUE MODEL")
print("=" * 100)
print(f"\n⚙️  CONFIGURATION:")
print(f"   Charge Threshold: £{CHARGE_THRESHOLD:.2f}/MWh")
print(f"   Discharge VLP Threshold: £{DISCHARGE_VLP_THRESHOLD:.2f}/MWh")
print(f"   Round-trip Efficiency: {ROUND_TRIP_EFFICIENCY*100:.0f}%")
print(f"   Degradation Cost: £{DEGRADATION_COST_PER_MWH:.2f}/MWh throughput")
print(f"   VLP Fee: {VLP_FEE_SHARE*100:.0f}%")
print(f"   Fixed O&M: £{FIXED_OM_PER_KW_YEAR:.2f}/kW/year")

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

# ============================================================================
# READ BESS CONFIGURATION
# ============================================================================

print("\n🔋 Reading BESS Configuration...")
import_capacity_kw = float(bess_sheet.acell('F13').value or 2500)
export_capacity_kw = float(bess_sheet.acell('F14').value or 2500)
duration_hrs = float(bess_sheet.acell('F15').value or 2)
max_cycles_per_day = float(bess_sheet.acell('F16').value or 4)

capacity_mwh = (import_capacity_kw / 1000) * duration_hrs
max_charge_mwh_per_period = import_capacity_kw / 1000 / 2  # Per half-hour
max_discharge_mwh_per_period = export_capacity_kw / 1000 / 2  # Per half-hour

annual_fixed_om = (import_capacity_kw / 1000) * FIXED_OM_PER_KW_YEAR

print(f"   Import Capacity: {import_capacity_kw:,.0f} kW")
print(f"   Export Capacity: {export_capacity_kw:,.0f} kW")
print(f"   Storage Capacity: {capacity_mwh:.1f} MWh")
print(f"   Max Charge/Discharge per Period: {max_charge_mwh_per_period:.2f} MWh")
print(f"   Max Cycles/Day: {max_cycles_per_day}")
print(f"   Annual Fixed O&M: £{annual_fixed_om:,.2f}")

# Read PPA price and time period
ppa_price = float((bess_sheet.acell('D43').value or "150").strip().replace('£', '').replace(',', ''))
time_period = bess_sheet.acell('L6').value or "2 Year"
print(f"\n💰 PPA Rate: £{ppa_price:.2f}/MWh")
print(f"📅 Analysis Period: {time_period}")

# ============================================================================
# READ HH DATA (SITE BASELINE DEMAND)
# ============================================================================

print("\n📂 Reading HH Data (baseline site demand)...")
hh_data = hh_sheet.get_all_records()
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['date'] = df_hh['timestamp'].dt.date
df_hh['period'] = ((df_hh['timestamp'].dt.hour * 2) + (df_hh['timestamp'].dt.minute // 30) + 1)
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['site_baseline_import_mwh'] = df_hh['demand_kw'] / 1000 / 2  # Half-hourly

# Calculate DUoS band
df_hh['hour'] = df_hh['timestamp'].dt.hour
df_hh['is_weekend'] = df_hh['timestamp'].dt.dayofweek >= 5
df_hh['duos_band'] = 'Green'  # Default
df_hh.loc[(df_hh['hour'] >= 16) & (df_hh['hour'] < 19) & (~df_hh['is_weekend']), 'duos_band'] = 'Red'
df_hh.loc[((df_hh['hour'] >= 8) & (df_hh['hour'] < 16)) | ((df_hh['hour'] >= 19) & (df_hh['hour'] < 22)), 'duos_band'] = 'Amber'
df_hh.loc[df_hh['is_weekend'], 'duos_band'] = 'Green'

# Map DUoS rates
duos_map = {'Red': DUOS_RED, 'Amber': DUOS_AMBER, 'Green': DUOS_GREEN}
df_hh['duos_rate'] = df_hh['duos_band'].map(duos_map)

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
WITH period_data AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod as period,
    MAX(systemBuyPrice) as system_buy_price,
    MAX(systemSellPrice) as system_sell_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
  WHERE CAST(settlementDate AS DATE) >= '{min_date}'
    AND CAST(settlementDate AS DATE) <= '{max_date}'
  GROUP BY date, settlementPeriod
)
SELECT * FROM period_data
ORDER BY date, period
"""

df_prices = client.query(query).to_dataframe()
df_prices['period'] = df_prices['period'].astype(int)
print(f"   Retrieved {len(df_prices):,} price records")

# Merge HH data with prices
df = df_hh.merge(df_prices, on=['date', 'period'], how='left')
df = df.sort_values('timestamp').reset_index(drop=True)
df['system_buy_price'] = df['system_buy_price'].fillna(df['system_buy_price'].mean())
df['system_sell_price'] = df['system_sell_price'].fillna(df['system_sell_price'].mean())

print(f"   Merged dataset: {len(df):,} periods")

# ============================================================================
# CALCULATE EFFECTIVE IMPORT PRICE (per SP)
# ============================================================================

print("\n💷 Calculating effective import price per period...")
df['import_price_per_mwh'] = df['system_buy_price'] + df['duos_rate'] + TOTAL_FIXED_COST

print(f"   Avg Import Price: £{df['import_price_per_mwh'].mean():.2f}/MWh")
print(f"   Min: £{df['import_price_per_mwh'].min():.2f}, Max: £{df['import_price_per_mwh'].max():.2f}")

# ============================================================================
# BESS OPERATION SIMULATION
# ============================================================================

print("\n⚡ Simulating BESS Operations...")

# Initialize state tracking
df['soc_mwh'] = 0.0  # State of charge
df['charge_mwh'] = 0.0  # Energy charged this period
df['discharge_vlp_mwh'] = 0.0  # Discharged for VLP (selling to SO)
df['discharge_demand_mwh'] = 0.0  # Discharged to meet site demand
df['avoided_import_mwh'] = 0.0  # Import reduction due to BESS discharge

soc = 0.0
daily_charges = 0
daily_discharges = 0
last_date = None

for idx, row in df.iterrows():
    current_date = row['date']
    
    # Reset daily cycle counters at midnight
    if current_date != last_date:
        daily_charges = 0
        daily_discharges = 0
        last_date = current_date
    
    system_buy = row['system_buy_price']
    system_sell = row['system_sell_price']
    site_demand_mwh = row['site_baseline_import_mwh']
    import_price = row['import_price_per_mwh']
    
    # ========================================================================
    # DECISION 1: CHARGE BATTERY (when wholesale is cheap)
    # ========================================================================
    if system_buy < CHARGE_THRESHOLD and soc < capacity_mwh and daily_charges < max_cycles_per_day:
        charge_possible = min(max_charge_mwh_per_period, capacity_mwh - soc)
        df.at[idx, 'charge_mwh'] = charge_possible
        soc += charge_possible
        daily_charges += 1
    
    # ========================================================================
    # DECISION 2: DISCHARGE FOR VLP (when SO price is high)
    # ========================================================================
    # This is selling energy to the system operator for balancing
    # Revenue = system_sell_price (high), not avoiding import
    if system_sell > DISCHARGE_VLP_THRESHOLD and soc > 0 and daily_discharges < max_cycles_per_day:
        discharge_vlp = min(max_discharge_mwh_per_period, soc)
        df.at[idx, 'discharge_vlp_mwh'] = discharge_vlp
        soc -= discharge_vlp
        daily_discharges += 1
    
    # ========================================================================
    # DECISION 3: DISCHARGE TO MEET SITE DEMAND (avoided import)
    # ========================================================================
    # Discharge to avoid importing when:
    # - Battery has charge
    # - Site has demand
    # - Import price > PPA price (grid is expensive)
    # - Not already discharged for VLP
    # - Haven't hit daily discharge limit
    elif soc > 0 and site_demand_mwh > 0 and import_price > ppa_price and daily_discharges < max_cycles_per_day:
        discharge_demand = min(max_discharge_mwh_per_period, soc, site_demand_mwh)
        df.at[idx, 'discharge_demand_mwh'] = discharge_demand
        df.at[idx, 'avoided_import_mwh'] = discharge_demand * ROUND_TRIP_EFFICIENCY  # Account for losses
        soc -= discharge_demand
        daily_discharges += 1
    
    df.at[idx, 'soc_mwh'] = soc

print(f"   Simulation complete: {len(df):,} periods processed")

# ============================================================================
# CALCULATE REVENUES
# ============================================================================

print("\n💰 Calculating Revenues...")

# Revenue 1: Avoided Import Cost (on-site value)
# When BESS discharges to meet site demand, it avoids importing at high price
df['rev_avoided_import'] = df['avoided_import_mwh'] * df['import_price_per_mwh']

# Revenue 2: VLP/SO Revenue (selling flexibility to system operator)
# When BESS discharges for VLP, it's paid the system sell price
df['rev_vlp_energy'] = df['discharge_vlp_mwh'] * df['system_sell_price'] * ROUND_TRIP_EFFICIENCY

# Revenue 3: VLP Availability Payments (if applicable)
# This would require separate contract data - set to 0 for now
df['rev_vlp_availability'] = 0.0

# Total VLP revenue before fees
df['rev_vlp_total'] = df['rev_vlp_energy'] + df['rev_vlp_availability']

# VLP service fee (aggregator takes a cut)
df['vlp_service_fee'] = df['rev_vlp_total'] * VLP_FEE_SHARE

# Net VLP revenue (after fees)
df['rev_vlp_net'] = df['rev_vlp_total'] - df['vlp_service_fee']

# ============================================================================
# CALCULATE COSTS
# ============================================================================

print("\n💸 Calculating Costs...")

# Cost 1: Charging Energy Cost
# Pay import_price when charging from grid
df['cost_charging_energy'] = df['charge_mwh'] * df['import_price_per_mwh']

# Cost 2: Efficiency Losses (already embedded in discharge calculations)
# To deliver X MWh, must charge X/efficiency MWh
# Loss energy: X * (1/efficiency - 1)
df['throughput_mwh'] = df['charge_mwh'] + df['discharge_vlp_mwh'] + df['discharge_demand_mwh']
df['loss_mwh'] = df['throughput_mwh'] * (1/ROUND_TRIP_EFFICIENCY - 1)
df['cost_losses'] = df['loss_mwh'] * df['import_price_per_mwh']

# Cost 3: Battery Degradation (throughput-based)
df['cost_degradation'] = df['throughput_mwh'] * DEGRADATION_COST_PER_MWH

# Total costs per period
df['total_cost_per_period'] = df['cost_charging_energy'] + df['cost_losses'] + df['cost_degradation']

# ============================================================================
# CALCULATE PER-PERIOD PROFIT
# ============================================================================

print("\n📊 Calculating Per-Period Profit...")

df['profit_per_period'] = (
    df['rev_avoided_import'] +
    df['rev_vlp_net'] -
    df['total_cost_per_period']
)

# ============================================================================
# AGGREGATE RESULTS
# ============================================================================

print("\n" + "=" * 100)
print("RESULTS SUMMARY")
print("=" * 100)

# Revenue breakdown
total_avoided_import = df['rev_avoided_import'].sum()
total_vlp_gross = df['rev_vlp_total'].sum()
total_vlp_fees = df['vlp_service_fee'].sum()
total_vlp_net = df['rev_vlp_net'].sum()
total_revenue = total_avoided_import + total_vlp_net

print(f"\n💰 REVENUES:")
print(f"   Avoided Import Cost:       £{total_avoided_import:>12,.2f}")
print(f"   VLP Energy Revenue (gross): £{total_vlp_gross:>12,.2f}")
print(f"   VLP Service Fee ({VLP_FEE_SHARE*100:.0f}%):       £{total_vlp_fees:>12,.2f}")
print(f"   VLP Net Revenue:           £{total_vlp_net:>12,.2f}")
print(f"   {'─' * 45}")
print(f"   TOTAL REVENUE:             £{total_revenue:>12,.2f}")

# Cost breakdown
total_charge_cost = df['cost_charging_energy'].sum()
total_loss_cost = df['cost_losses'].sum()
total_deg_cost = df['cost_degradation'].sum()
total_var_cost = total_charge_cost + total_loss_cost + total_deg_cost
total_cost = total_var_cost + annual_fixed_om

print(f"\n💸 COSTS:")
print(f"   Charging Energy:           £{total_charge_cost:>12,.2f}")
print(f"   Efficiency Losses:         £{total_loss_cost:>12,.2f}")
print(f"   Degradation:               £{total_deg_cost:>12,.2f}")
print(f"   Fixed O&M:                 £{annual_fixed_om:>12,.2f}")
print(f"   {'─' * 45}")
print(f"   TOTAL COST:                £{total_cost:>12,.2f}")

# Net profit
net_profit = total_revenue - total_cost

print(f"\n✅ NET PROFIT:                 £{net_profit:>12,.2f}")

# Operations summary
total_charge_periods = (df['charge_mwh'] > 0).sum()
total_vlp_periods = (df['discharge_vlp_mwh'] > 0).sum()
total_demand_periods = (df['discharge_demand_mwh'] > 0).sum()
total_charge_mwh = df['charge_mwh'].sum()
total_vlp_mwh = df['discharge_vlp_mwh'].sum()
total_demand_mwh = df['discharge_demand_mwh'].sum()
total_throughput = df['throughput_mwh'].sum()

print(f"\n⚡ OPERATIONS:")
print(f"   Charge Periods:            {total_charge_periods:>12,} ({total_charge_mwh:,.1f} MWh)")
print(f"   VLP Discharge Periods:     {total_vlp_periods:>12,} ({total_vlp_mwh:,.1f} MWh)")
print(f"   Demand Discharge Periods:  {total_demand_periods:>12,} ({total_demand_mwh:,.1f} MWh)")
print(f"   Total Throughput:          {total_throughput:>12,.1f} MWh")

# Utilization
theoretical_max_cycles = 365 * max_cycles_per_day
actual_cycles = (total_charge_periods + total_vlp_periods + total_demand_periods) / 2
utilization = (actual_cycles / theoretical_max_cycles) * 100 if theoretical_max_cycles > 0 else 0

print(f"\n📈 UTILIZATION:")
print(f"   Theoretical Max Cycles:    {theoretical_max_cycles:>12,.0f}/year")
print(f"   Actual Cycles:             {actual_cycles:>12,.0f}/year")
print(f"   Utilization:               {utilization:>12,.1f}%")

# Performance metrics
profit_per_mwh_throughput = net_profit / total_throughput if total_throughput > 0 else 0
profit_per_kw_year = net_profit / (import_capacity_kw / 1000) if import_capacity_kw > 0 else 0

print(f"\n📊 PERFORMANCE METRICS:")
print(f"   Profit per MWh Throughput: £{profit_per_mwh_throughput:>12,.2f}")
print(f"   Profit per MW per Year:    £{profit_per_kw_year:>12,.2f}")

# ============================================================================
# UPDATE GOOGLE SHEETS
# ============================================================================

print("\n📝 Updating Google Sheets...")

# Write to BESS Comprehensive Revenue section (rows 51-65)
updates = [
    # Revenue breakdown
    ('B51', f"{total_avoided_import:.2f}"),
    ('B52', f"{total_vlp_gross:.2f}"),
    ('B53', f"{total_vlp_fees:.2f}"),
    ('B54', f"{total_vlp_net:.2f}"),
    ('B55', f"{total_revenue:.2f}"),
    
    # Cost breakdown
    ('B57', f"{total_charge_cost:.2f}"),
    ('B58', f"{total_loss_cost:.2f}"),
    ('B59', f"{total_deg_cost:.2f}"),
    ('B60', f"{annual_fixed_om:.2f}"),
    ('B61', f"{total_cost:.2f}"),
    
    # Net profit
    ('B63', f"{net_profit:.2f}"),
    
    # Operations
    ('D51', f"{total_charge_periods}"),
    ('D52', f"{total_charge_mwh:.1f}"),
    ('D53', f"{total_vlp_periods}"),
    ('D54', f"{total_vlp_mwh:.1f}"),
    ('D55', f"{total_demand_periods}"),
    ('D56', f"{total_demand_mwh:.1f}"),
    
    # Metrics
    ('D58', f"{actual_cycles:.0f}"),
    ('D59', f"{utilization:.1f}"),
    ('D60', f"{profit_per_mwh_throughput:.2f}"),
    ('D61', f"{profit_per_kw_year:.2f}"),
]

for cell, value in updates:
    try:
        bess_sheet.update_acell(cell, value)
    except Exception as e:
        print(f"   ⚠️  Failed to update {cell}: {e}")

print("   ✅ Spreadsheet updated")

# ============================================================================
# EXPORT DETAILED CSV
# ============================================================================

output_file = f"bess_comprehensive_revenue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df_export = df[['timestamp', 'duos_band', 'system_buy_price', 'system_sell_price', 
                'import_price_per_mwh', 'site_baseline_import_mwh', 'charge_mwh', 
                'discharge_vlp_mwh', 'discharge_demand_mwh', 'soc_mwh',
                'rev_avoided_import', 'rev_vlp_net', 'cost_charging_energy', 
                'cost_degradation', 'profit_per_period']]
df_export.to_csv(output_file, index=False)
print(f"\n💾 Detailed results exported to: {output_file}")

print("\n" + "=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
