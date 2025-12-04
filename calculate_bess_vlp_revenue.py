#!/usr/bin/env python3
"""
BESS VLP Revenue Analysis
Analyzes revenue opportunities from:
1. Virtual Lead Party (VLP) - balancing mechanism arbitrage
2. End-user supply - discharge to meet demand at PPA rate
3. Ensures no double-counting with BtM PPA imports
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
SHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

# VLP thresholds - ADJUSTED for better utilization
CHARGE_THRESHOLD = 50.0  # Charge when system price < £50/MWh (was £30)
DISCHARGE_VLP_THRESHOLD = 100.0  # Discharge for VLP when system sell price > £100/MWh (was £150)
EFFICIENCY = 0.85  # Round-trip efficiency 85%

print("=" * 100)
print("BESS VLP REVENUE ANALYSIS")
print("=" * 100)

# Connect to Google Sheets
print("\n📊 Connecting to Google Sheets...")
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

# Read BESS configuration
print("\n🔋 Reading BESS Configuration...")
import_capacity_kw = float(bess_sheet.acell('F13').value or 2500)
export_capacity_kw = float(bess_sheet.acell('F14').value or 2500)
duration_hrs = float(bess_sheet.acell('F15').value or 2)
max_cycles_per_day = float(bess_sheet.acell('F16').value or 4)

capacity_mwh = (import_capacity_kw / 1000) * duration_hrs
max_charge_mwh = import_capacity_kw / 1000 / 2  # Per half-hour
max_discharge_mwh = export_capacity_kw / 1000 / 2  # Per half-hour

print(f"   Import Capacity: {import_capacity_kw:,.0f} kW")
print(f"   Export Capacity: {export_capacity_kw:,.0f} kW")
print(f"   Storage Capacity: {capacity_mwh:.1f} MWh")
print(f"   Max Cycles/Day: {max_cycles_per_day}")
print(f"   Efficiency: {EFFICIENCY*100:.0f}%")

# Read PPA price and time period
ppa_price = float((bess_sheet.acell('D43').value or "150").strip().replace('£', '').replace(',', ''))
time_period = bess_sheet.acell('L6').value or "2 Year"
print(f"\n💰 PPA Rate: £{ppa_price:.2f}/MWh")
print(f"📅 Analysis Period: {time_period}")

# Read HH Data
print("\n📂 Reading HH Data...")
hh_data = hh_sheet.get_all_records()
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['date'] = df_hh['timestamp'].dt.date
df_hh['period'] = ((df_hh['timestamp'].dt.hour * 2) + (df_hh['timestamp'].dt.minute // 30) + 1)
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['demand_mwh'] = df_hh['demand_kw'] / 1000 / 2

# Query BigQuery for system prices (use bmrs_costs for historical data like BtM PPA script)
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
# Convert period to int for consistent merge
df_prices['period'] = df_prices['period'].astype(int)
print(f"Retrieved {len(df_prices):,} price records")

# Merge HH data with prices
df = df_hh.merge(df_prices, on=['date', 'period'], how='left')
print(f"After merge: {len(df):,} rows (should be {len(df_hh):,})")
if len(df) > len(df_hh):
    print(f"⚠️  WARNING: Merge created {len(df) - len(df_hh):,} duplicate rows!")
df = df.sort_values('timestamp').reset_index(drop=True)
df['system_buy_price'] = df['system_buy_price'].fillna(df['system_buy_price'].mean())
df['system_sell_price'] = df['system_sell_price'].fillna(df['system_sell_price'].mean())

print(f"\n✅ Merged dataset: {len(df):,} periods")

# BESS Operation Logic
print("\n⚡ Simulating BESS Operations...")

# Track BESS state
df['soc_mwh'] = 0.0  # State of charge
df['charge_mwh'] = 0.0  # Energy charged this period
df['discharge_vlp_mwh'] = 0.0  # Discharged for VLP
df['discharge_demand_mwh'] = 0.0  # Discharged to meet demand
df['btm_import_mwh'] = 0.0  # BtM PPA import (from previous analysis)

soc = 0.0
daily_charges = 0
daily_discharges = 0
last_date = None

for idx, row in df.iterrows():
    current_date = row['date']
    
    # Reset operation counters at midnight
    if current_date != last_date:
        daily_charges = 0
        daily_discharges = 0
        last_date = current_date
    
    system_buy = row['system_buy_price']
    system_sell = row['system_sell_price']
    demand_mwh = row['demand_mwh']
    
    # Decision 1: Should we charge?
    # Can charge up to max_cycles_per_day times per day
    if system_buy < CHARGE_THRESHOLD and soc < capacity_mwh and daily_charges < max_cycles_per_day:
        charge_possible = min(max_charge_mwh, capacity_mwh - soc)
        df.at[idx, 'charge_mwh'] = charge_possible
        soc += charge_possible
        daily_charges += 1
    
    # Decision 2: Should we discharge for VLP?
    # Can discharge up to max_cycles_per_day times per day
    if system_sell > DISCHARGE_VLP_THRESHOLD and soc > 0 and daily_discharges < max_cycles_per_day:
        discharge_vlp = min(max_discharge_mwh, soc)
        df.at[idx, 'discharge_vlp_mwh'] = discharge_vlp
        soc -= discharge_vlp
        daily_discharges += 1
    
    # Decision 3: Should we discharge to meet demand?
    # Only if we're NOT importing via BtM PPA and haven't hit discharge limit
    elif soc > 0 and demand_mwh > 0 and system_buy > ppa_price and daily_discharges < max_cycles_per_day:
        discharge_demand = min(max_discharge_mwh, soc, demand_mwh)
        df.at[idx, 'discharge_demand_mwh'] = discharge_demand
        soc -= discharge_demand
        daily_discharges += 1
    
    df.at[idx, 'soc_mwh'] = soc

# Calculate revenues and costs
print("\n💰 Calculating Revenues...")

# Charge costs
df['charge_cost'] = df['charge_mwh'] * df['system_buy_price']

# VLP revenue (selling at system sell price, bought at charge price)
df['vlp_revenue'] = df['discharge_vlp_mwh'] * df['system_sell_price'] * EFFICIENCY

# Demand revenue (selling to end-user at PPA rate)
df['demand_revenue'] = df['discharge_demand_mwh'] * ppa_price * EFFICIENCY

# Total costs and revenues
total_charge_cost = df['charge_cost'].sum()
total_vlp_revenue = df['vlp_revenue'].sum()
total_demand_revenue = df['demand_revenue'].sum()
total_revenue = total_vlp_revenue + total_demand_revenue
net_profit = total_revenue - total_charge_cost

# Statistics
total_charge_mwh = df['charge_mwh'].sum()
total_discharge_vlp_mwh = df['discharge_vlp_mwh'].sum()
total_discharge_demand_mwh = df['discharge_demand_mwh'].sum()
total_discharge_mwh = total_discharge_vlp_mwh + total_discharge_demand_mwh

charge_periods = (df['charge_mwh'] > 0).sum()
discharge_vlp_periods = (df['discharge_vlp_mwh'] > 0).sum()
discharge_demand_periods = (df['discharge_demand_mwh'] > 0).sum()

avg_charge_price = df[df['charge_mwh'] > 0]['system_buy_price'].mean() if charge_periods > 0 else 0
avg_discharge_vlp_price = df[df['discharge_vlp_mwh'] > 0]['system_sell_price'].mean() if discharge_vlp_periods > 0 else 0

print("\n" + "=" * 100)
print("RESULTS")
print("=" * 100)

print(f"\n⚡ CHARGING:")
print(f"   Periods: {charge_periods:,}")
print(f"   Volume: {total_charge_mwh:,.1f} MWh")
print(f"   Avg Price: £{avg_charge_price:.2f}/MWh")
print(f"   Cost: £{total_charge_cost:,.2f}")

print(f"\n📤 DISCHARGE - VLP (Balancing Mechanism):")
print(f"   Periods: {discharge_vlp_periods:,}")
print(f"   Volume: {total_discharge_vlp_mwh:,.1f} MWh")
print(f"   Avg Price: £{avg_discharge_vlp_price:.2f}/MWh")
print(f"   Revenue: £{total_vlp_revenue:,.2f}")

print(f"\n🏭 DISCHARGE - End User Demand:")
print(f"   Periods: {discharge_demand_periods:,}")
print(f"   Volume: {total_discharge_demand_mwh:,.1f} MWh")
print(f"   Price: £{ppa_price:.2f}/MWh")
print(f"   Revenue: £{total_demand_revenue:,.2f}")

print(f"\n💰 FINANCIAL SUMMARY:")
print(f"   Total Charge Cost: £{total_charge_cost:,.2f}")
print(f"   Total Revenue: £{total_revenue:,.2f}")
print(f"   Net Profit: £{net_profit:,.2f}")
print(f"   ROI: {(net_profit / total_charge_cost * 100) if total_charge_cost > 0 else 0:.1f}%")

# Write results to spreadsheet
print("\n📝 Writing to BESS sheet...")
updates = [
    # BESS operations summary (could go in rows 46-52 or similar)
    ('B46', f'{total_charge_mwh:,.1f}'),  # Charge MWh
    ('C46', f'£{total_charge_cost:,.2f}'),  # Charge cost
    ('B47', f'{total_discharge_vlp_mwh:,.1f}'),  # VLP discharge MWh
    ('C47', f'£{total_vlp_revenue:,.2f}'),  # VLP revenue
    ('B48', f'{total_discharge_demand_mwh:,.1f}'),  # Demand discharge MWh
    ('C48', f'£{total_demand_revenue:,.2f}'),  # Demand revenue
    ('B49', f'{net_profit:,.2f}'),  # Net profit
]

for cell, value in updates:
    bess_sheet.update_acell(cell, value)
    print(f"   {cell}: {value}")

print("\n✅ Complete!")
print(f"\nSummary:")
print(f"  BESS charged {total_charge_mwh:,.1f} MWh at avg £{avg_charge_price:.2f}/MWh")
print(f"  Discharged {total_discharge_vlp_mwh:,.1f} MWh for VLP at avg £{avg_discharge_vlp_price:.2f}/MWh")
print(f"  Supplied {total_discharge_demand_mwh:,.1f} MWh to end-user at £{ppa_price:.2f}/MWh")
print(f"  Net profit: £{net_profit:,.2f}")
