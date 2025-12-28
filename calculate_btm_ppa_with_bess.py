#!/usr/bin/env python3
"""
BtM PPA Analysis - WITH BESS VLP Operation
Calculates costs and revenues when BESS operates as Virtual Lead Party alongside base load
"""

import gspread
import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime
import numpy as np

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# BESS Parameters (read from sheet, these are defaults)
BESS_CAPACITY_MWH = 2.5  # Battery capacity
BESS_POWER_MW = 1.0      # Max charge/discharge rate
BESS_EFFICIENCY = 0.9    # Round-trip efficiency
BESS_MIN_SOC = 0.1       # Minimum state of charge (10%)
BESS_MAX_SOC = 0.9       # Maximum state of charge (90%)

# Thresholds - OPTIMIZED for profitability
CHARGE_THRESHOLD = 30.0   # Charge when system price < £30/MWh (cheaper charging)
DISCHARGE_THRESHOLD = 150.0  # Discharge for VLP when SSP > £150/MWh (higher revenue)

# DUoS rates (pence/kWh)
DUOS_RED = 17.64
DUOS_AMBER = 2.05
DUOS_GREEN = 0.11

# Fixed costs (£/MWh) - TNUoS set to zero Dec 2025
TNUOS = 0.00
BSUOS = 4.50
CCL = 8.56
RO = 14.50
FIT = 7.40
CFD = 9.00
ECO = 1.75
WHD = 0.75
TOTAL_FIXED = TNUOS + BSUOS + CCL + RO + FIT + CFD + ECO + WHD  # £59.0/MWh

def get_duos_band(period):
    """Determine DUoS band for settlement period (1-48)"""
    hour = (period - 1) // 2
    if 16 <= hour < 19:  # 16:00-19:00 (periods 33-38)
        return 'Red'
    elif (8 <= hour < 16) or (19 <= hour < 22):  # 08:00-16:00, 19:00-22:00
        return 'Amber'
    else:
        return 'Green'

print("=" * 100)
print("BtM PPA WITH BESS VLP ANALYSIS")
print("=" * 100)

# Connect to Google Sheets
print("\n📊 Connecting to Google Sheets...")
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

# Read PPA price from B39
print("📋 Reading PPA price from B39...")
ppa_value = (bess_sheet.acell('B39').value or "150").strip().replace('£', '').replace(',', '')
ppa_price = float(ppa_value)
print(f"   PPA Price: £{ppa_price:.2f}/MWh")

# Read BESS parameters from sheet (if available)
try:
    bess_capacity_cell = bess_sheet.acell('F17').value
    if bess_capacity_cell:
        BESS_CAPACITY_MWH = float(str(bess_capacity_cell).replace('MWh', '').strip())
        print(f"   BESS Capacity: {BESS_CAPACITY_MWH} MWh")
except:
    print(f"   Using default BESS Capacity: {BESS_CAPACITY_MWH} MWh")

# Read HH Data
print("\n📂 Reading HH Data sheet...")
hh_data = hh_sheet.get_all_records()
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['date'] = df_hh['timestamp'].dt.date
df_hh['period'] = ((df_hh['timestamp'].dt.hour * 2) + (df_hh['timestamp'].dt.minute // 30) + 1)
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['demand_mwh'] = df_hh['demand_kw'] / 1000 / 2  # Convert kW to MWh (half-hour)
print(f"   Total HH periods: {len(df_hh)}")
print(f"   Date range: {df_hh['timestamp'].min()} to {df_hh['timestamp'].max()}")

# Connect to BigQuery
print("\n🔍 Querying BigQuery for system prices (buy + sell)...")
client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)

# Get system prices for the date range
min_date = df_hh['timestamp'].min().date()
max_date = df_hh['timestamp'].max().date()

# Query both buy and sell prices
query = f"""
WITH buy_prices AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    MAX(systemBuyPrice) as system_buy_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
  WHERE CAST(settlementDate AS DATE) >= '{min_date}'
    AND CAST(settlementDate AS DATE) <= '{max_date}'
    AND systemBuyPrice IS NOT NULL
  GROUP BY date, settlementPeriod
  
  UNION ALL
  
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    MAX(CAST(price AS FLOAT64)) as system_buy_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
  WHERE CAST(settlementDate AS DATE) >= '{min_date}'
    AND CAST(settlementDate AS DATE) <= '{max_date}'
    AND price IS NOT NULL
  GROUP BY date, settlementPeriod
),
sell_prices AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    MAX(systemSellPrice) as system_sell_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
  WHERE CAST(settlementDate AS DATE) >= '{min_date}'
    AND CAST(settlementDate AS DATE) <= '{max_date}'
    AND systemSellPrice IS NOT NULL
  GROUP BY date, settlementPeriod
)
SELECT 
  COALESCE(b.date, s.date) as date,
  COALESCE(b.settlementPeriod, s.settlementPeriod) as settlementPeriod,
  MAX(b.system_buy_price) as system_buy_price,
  MAX(s.system_sell_price) as system_sell_price
FROM buy_prices b
FULL OUTER JOIN sell_prices s 
  ON b.date = s.date AND b.settlementPeriod = s.settlementPeriod
GROUP BY date, settlementPeriod
ORDER BY date, settlementPeriod
"""

df_prices = client.query(query).to_dataframe()
print(f"   Retrieved {len(df_prices)} price records")

# Rename settlementPeriod to period for merge
df_prices = df_prices.rename(columns={'settlementPeriod': 'period'})

# Merge prices with HH data
df = df_hh.merge(df_prices, on=['date', 'period'], how='left')
print(f"\n🔗 Merged HH data with system prices: {len(df)} records")

# Initialize BESS state tracking
df['bess_soc'] = 0.0  # State of charge (MWh)
df['bess_charge_mwh'] = 0.0
df['bess_discharge_mwh'] = 0.0
df['bess_vlp_revenue'] = 0.0
df['bess_charge_cost'] = 0.0

print("\n🔋 Simulating BESS VLP operation...")
soc = BESS_CAPACITY_MWH * 0.5  # Start at 50% SOC

for idx in range(len(df)):
    row = df.iloc[idx]
    system_buy = row['system_buy_price'] if pd.notna(row['system_buy_price']) else 999
    system_sell = row['system_sell_price'] if pd.notna(row['system_sell_price']) else 0
    
    # BESS VLP Decision Logic
    # 1. DISCHARGE if SSP is high (VLP opportunity) and we have charge
    if system_sell > DISCHARGE_THRESHOLD and soc > (BESS_CAPACITY_MWH * BESS_MIN_SOC):
        discharge_mwh = min(BESS_POWER_MW * 0.5, soc - (BESS_CAPACITY_MWH * BESS_MIN_SOC))
        if discharge_mwh > 0:
            df.loc[idx, 'bess_discharge_mwh'] = discharge_mwh
            df.loc[idx, 'bess_vlp_revenue'] = discharge_mwh * system_sell
            soc -= discharge_mwh
    
    # 2. CHARGE if prices are cheap and we have space
    elif system_buy < CHARGE_THRESHOLD and soc < (BESS_CAPACITY_MWH * BESS_MAX_SOC):
        charge_mwh = min(BESS_POWER_MW * 0.5, (BESS_CAPACITY_MWH * BESS_MAX_SOC) - soc)
        if charge_mwh > 0:
            df.loc[idx, 'bess_charge_mwh'] = charge_mwh
            # Charging cost includes system price + DUoS + fixed costs
            duos_band = get_duos_band(row['period'])
            duos_rate = DUOS_RED if duos_band == 'Red' else (DUOS_AMBER if duos_band == 'Amber' else DUOS_GREEN)
            duos_cost = charge_mwh * 1000 * duos_rate / 100  # Convert to £
            fixed_cost = charge_mwh * (TNUOS + BSUOS + CCL + RO + FIT)
            energy_cost = charge_mwh * system_buy
            df.loc[idx, 'bess_charge_cost'] = energy_cost + duos_cost + fixed_cost
            soc += (charge_mwh * BESS_EFFICIENCY)
    
    df.loc[idx, 'bess_soc'] = soc

print(f"   BESS cycles simulated for {len(df)} periods")
print(f"   Final SOC: {soc:.2f} MWh ({soc/BESS_CAPACITY_MWH*100:.1f}%)")

# Calculate base load costs (same as Non-BESS scenario)
print("\n💰 Calculating base load costs...")
df['duos_band'] = df['period'].apply(get_duos_band)
df['duos_rate'] = df['duos_band'].map({'Red': DUOS_RED, 'Amber': DUOS_AMBER, 'Green': DUOS_GREEN})

# Calculate costs per period
df['duos_cost'] = df['demand_mwh'] * 1000 * df['duos_rate'] / 100
df['fixed_cost'] = df['demand_mwh'] * (TNUOS + BSUOS + CCL + RO + FIT)
df['energy_cost'] = df['demand_mwh'] * df['system_buy_price']
df['total_cost_per_mwh'] = (df['energy_cost'] + df['duos_cost'] + df['fixed_cost']) / df['demand_mwh']

# Profitable base load periods (same logic as Non-BESS)
df['profitable'] = df['total_cost_per_mwh'] < ppa_price
profitable_import_kwh = (df[df['profitable']]['demand_mwh'].sum() * 1000)
profitable_periods = df['profitable'].sum()

# Calculate totals
total_import_kwh = df['demand_mwh'].sum() * 1000

# DUoS costs by band
duos_red = df[df['duos_band'] == 'Red']['duos_cost'].sum()
duos_amber = df[df['duos_band'] == 'Amber']['duos_cost'].sum()
duos_green = df[df['duos_band'] == 'Green']['duos_cost'].sum()
duos_total = duos_red + duos_amber + duos_green

# Fixed costs breakdown
tnuos_total = df['demand_mwh'].sum() * TNUOS
bsuos_total = df['demand_mwh'].sum() * BSUOS
ccl_total = df['demand_mwh'].sum() * CCL
ro_total = df['demand_mwh'].sum() * RO
fit_total = df['demand_mwh'].sum() * FIT

# BESS metrics
total_bess_charge_mwh = df['bess_charge_mwh'].sum()
total_bess_discharge_mwh = df['bess_discharge_mwh'].sum()
total_bess_vlp_revenue = df['bess_vlp_revenue'].sum()
total_bess_charge_cost = df['bess_charge_cost'].sum()
net_bess_revenue = total_bess_vlp_revenue - total_bess_charge_cost

# System price statistics
system_price_min = df['system_buy_price'].min()
system_price_avg = df['system_buy_price'].mean()
system_price_max = df['system_buy_price'].max()

# PPA revenue (base load only, BESS VLP is separate)
ppa_revenue = profitable_import_kwh / 1000 * ppa_price

print("\n" + "=" * 100)
print("📊 CALCULATION RESULTS (WITH BESS)")
print("=" * 100)

print("\n⚡ BASE LOAD VOLUMES:")
print(f"   Total Import kWh: {total_import_kwh:,.0f} kWh")
print(f"   Profitable Import kWh: {profitable_import_kwh:,.0f} kWh")

print("\n🔋 BESS VLP OPERATION:")
print(f"   Total Charged: {total_bess_charge_mwh:,.2f} MWh ({total_bess_charge_mwh/BESS_CAPACITY_MWH:.1f} cycles)")
print(f"   Total Discharged: {total_bess_discharge_mwh:,.2f} MWh")
print(f"   Charging Cost: £{total_bess_charge_cost:,.2f}")
print(f"   VLP Revenue: £{total_bess_vlp_revenue:,.2f}")
print(f"   Net BESS Profit: £{net_bess_revenue:,.2f}")

print("\n🔢 PROFITABLE PERIODS:")
print(f"   Count: {profitable_periods:,} of {len(df):,} ({profitable_periods/len(df)*100:.1f}%)")

print("\n💷 DUoS COSTS:")
print(f"   Red: £{duos_red:,.2f}")
print(f"   Amber: £{duos_amber:,.2f}")
print(f"   Green: £{duos_green:,.2f}")
print(f"   Total: £{duos_total:,.2f}")

print("\n💷 FIXED COSTS:")
print(f"   TNUoS: £{tnuos_total:,.2f}")
print(f"   BSUoS: £{bsuos_total:,.2f}")
print(f"   CCL: £{ccl_total:,.2f}")
print(f"   RO: £{ro_total:,.2f}")
print(f"   FiT: £{fit_total:,.2f}")

print("\n💰 REVENUE:")
print(f"   PPA Revenue (base load): £{ppa_revenue:,.2f}")
print(f"   BESS VLP Revenue: £{total_bess_vlp_revenue:,.2f}")
print(f"   Total Revenue: £{ppa_revenue + total_bess_vlp_revenue:,.2f}")

# Write to BESS sheet column F
print("\n" + "=" * 100)
print("📝 WRITING TO BESS SHEET (Column F - With BESS)")
print("=" * 100)

updates = [
    ('F26', f'£{duos_red:,.2f}'),          # Red DUoS
    ('F27', f'£{duos_amber:,.2f}'),        # Amber DUoS
    ('F28', f'£{duos_green:,.2f}'),        # Green DUoS
    ('F29', f'£{tnuos_total:,.2f}'),       # TNUoS
    ('F30', f'£{bsuos_total:,.2f}'),       # BSUoS
    ('F31', f'£{ccl_total:,.2f}'),         # CCL
    ('F32', f'£{ro_total:,.2f}'),          # RO
    ('F33', f'£{fit_total:,.2f}'),         # FiT
    ('F35', f'£{system_price_min:,.2f}'),  # Min system price
    ('F36', f'£{system_price_avg:,.2f}'),  # Avg system price
    ('F37', f'£{system_price_max:,.2f}'),  # Max system price
    ('F38', f'{profitable_import_kwh:,.0f}'),  # Profitable kWh
    ('F40', f'{profitable_periods:,}'),    # Profitable periods
    ('F42', f'£{ppa_revenue:,.2f}'),       # PPA Revenue
    ('F44', f'{total_bess_discharge_mwh:,.2f}'),  # BESS Discharge MWh
    ('F45', f'£{total_bess_vlp_revenue:,.2f}'),   # BESS VLP Revenue
    ('F46', f'£{total_bess_charge_cost:,.2f}'),   # BESS Charge Cost
    ('F47', f'£{net_bess_revenue:,.2f}'),         # Net BESS Profit
]

print("📝 Updating cells...")
for cell, value in updates:
    try:
        bess_sheet.update_acell(cell, value)
        print(f"   {cell}: {value}")
    except Exception as e:
        print(f"   ⚠️  {cell}: Error - {e}")

print("\n✅ Update complete!")

print("\n" + "=" * 100)
print("🎯 SUMMARY")
print("=" * 100)
print(f"PPA Price: £{ppa_price:.2f}/MWh")
print(f"Base Load Profitable Periods: {profitable_periods:,}/{len(df):,} ({profitable_periods/len(df)*100:.1f}%)")
print(f"Base Load PPA Revenue: £{ppa_revenue:,.2f}")
print(f"\nBESS Operation:")
print(f"  Charged: {total_bess_charge_mwh:,.2f} MWh (cost £{total_bess_charge_cost:,.2f})")
print(f"  Discharged: {total_bess_discharge_mwh:,.2f} MWh (revenue £{total_bess_vlp_revenue:,.2f})")
print(f"  Net BESS Profit: £{net_bess_revenue:,.2f}")
print(f"\nTotal Revenue: £{ppa_revenue + total_bess_vlp_revenue:,.2f}")
print(f"BESS Contribution: {net_bess_revenue/(ppa_revenue + total_bess_vlp_revenue)*100:.1f}% of total")
