#!/usr/bin/env python3
"""
BtM PPA Analysis - FINAL VERSION
Only calculates for PROFITABLE periods (when importing is cheaper than PPA)
Shows 0 for Red periods since they're never profitable
"""

import gspread
import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# DUoS rates (£/MWh)
DUOS_RED = 176.40
DUOS_AMBER = 20.50
DUOS_GREEN = 1.10

# Fixed costs (£/MWh) - TNUoS set to zero Dec 2025
TNUOS = 0.00
BSUOS = 4.50
CCL = 8.56
RO = 14.50
FIT = 7.40
CFD = 9.00
ECO = 1.75
WHD = 0.75
TOTAL_FIXED = TNUOS + BSUOS + CCL + RO + FIT + CFD + ECO + WHD

def get_duos_band(period):
    hour = (period - 1) // 2
    if 16 <= hour < 19:
        return 'Red'
    elif (8 <= hour < 16) or (19 <= hour < 22):
        return 'Amber'
    else:
        return 'Green'

print("=" * 100)
print("BtM PPA ANALYSIS - PROFITABLE PERIODS ONLY")
print("=" * 100)

# Connect to Google Sheets
print("\n📊 Connecting to Google Sheets...")
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

# Read PPA price from D43 (moved from row 39 to 43)
ppa_value = (bess_sheet.acell('D43').value or "150").strip().replace('£', '').replace(',', '')
ppa_price = float(ppa_value)
print(f"PPA Price: £{ppa_price:.2f}/MWh")

# Read HH Data
print("\n📂 Reading HH Data...")
hh_data = hh_sheet.get_all_records()
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['date'] = df_hh['timestamp'].dt.date
df_hh['period'] = ((df_hh['timestamp'].dt.hour * 2) + (df_hh['timestamp'].dt.minute // 30) + 1)
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['demand_mwh'] = df_hh['demand_kw'] / 1000 / 2

# Query BigQuery
print("\n🔍 Querying BigQuery...")
client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)
min_date = df_hh['timestamp'].min().date()
max_date = df_hh['timestamp'].max().date()

query = f"""
WITH period_data AS (
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
)
SELECT 
  date,
  settlementPeriod as period,
  MAX(system_buy_price) as system_buy_price
FROM period_data
GROUP BY date, period
ORDER BY date, period
"""

df_prices = client.query(query).to_dataframe()
print(f"Retrieved {len(df_prices)} price records")

# Merge and calculate
df = df_hh.merge(df_prices, on=['date', 'period'], how='left')
df['duos_band'] = df['period'].apply(get_duos_band)
df['duos_rate_per_mwh'] = df['duos_band'].map({'Red': DUOS_RED, 'Amber': DUOS_AMBER, 'Green': DUOS_GREEN})

# Calculate total cost per MWh
df['total_cost_per_mwh'] = df['system_buy_price'] + df['duos_rate_per_mwh'] + TOTAL_FIXED

# Profitable when grid cost < PPA price
df['profitable'] = df['total_cost_per_mwh'] < ppa_price

# Filter to PROFITABLE periods only
df_prof = df[df['profitable']].copy()

print(f"\n✅ Profitable Periods: {len(df_prof):,} of {len(df):,} ({len(df_prof)/len(df)*100:.1f}%)")

# Calculate by DUoS band (PROFITABLE ONLY)
red_prof = df_prof[df_prof['duos_band'] == 'Red']
amber_prof = df_prof[df_prof['duos_band'] == 'Amber']
green_prof = df_prof[df_prof['duos_band'] == 'Green']

# MWh by band
red_mwh = red_prof['demand_mwh'].sum()
amber_mwh = amber_prof['demand_mwh'].sum()
green_mwh = green_prof['demand_mwh'].sum()
total_profitable_mwh = red_mwh + amber_mwh + green_mwh

# DUoS costs
red_duos_cost = red_mwh * DUOS_RED
amber_duos_cost = amber_mwh * DUOS_AMBER
green_duos_cost = green_mwh * DUOS_GREEN

# Fixed costs (per component)
tnuos_cost = total_profitable_mwh * TNUOS
bsuos_cost = total_profitable_mwh * BSUOS
ccl_cost = total_profitable_mwh * CCL
ro_cost = total_profitable_mwh * RO
fit_cost = total_profitable_mwh * FIT
cfd_cost = total_profitable_mwh * CFD
eco_cost = total_profitable_mwh * ECO
whd_cost = total_profitable_mwh * WHD

# System price stats (profitable periods only)
system_price_min = df_prof['system_buy_price'].min()
system_price_avg = df_prof['system_buy_price'].mean()
system_price_max = df_prof['system_buy_price'].max()

# Total cost calculation
total_energy_cost = (df_prof['system_buy_price'] * df_prof['demand_mwh']).sum()
total_duos_cost = red_duos_cost + amber_duos_cost + green_duos_cost
total_fixed_cost = tnuos_cost + bsuos_cost + ccl_cost + ro_cost + fit_cost + cfd_cost + eco_cost + whd_cost
total_cost = total_energy_cost + total_duos_cost + total_fixed_cost

print("\n" + "=" * 100)
print("RESULTS (Profitable Periods Only)")
print("=" * 100)

print(f"\n⚡ Import Volumes by DUoS Band:")
print(f"   Red:   {red_mwh:>8.1f} MWh (£{red_duos_cost:,.2f} DUoS)")
print(f"   Amber: {amber_mwh:>8.1f} MWh (£{amber_duos_cost:,.2f} DUoS)")
print(f"   Green: {green_mwh:>8.1f} MWh (£{green_duos_cost:,.2f} DUoS)")
print(f"   TOTAL: {total_profitable_mwh:>8.1f} MWh")

print(f"\n💷 Fixed Costs (on {total_profitable_mwh:.1f} MWh imported):")
print(f"   TNUoS: {total_profitable_mwh:>8.1f} MWh × £{TNUOS:.2f} = £{tnuos_cost:,.2f}")
print(f"   BSUoS: {total_profitable_mwh:>8.1f} MWh × £{BSUOS:.2f} = £{bsuos_cost:,.2f}")
print(f"   CCL:   {total_profitable_mwh:>8.1f} MWh × £{CCL:.2f} = £{ccl_cost:,.2f}")
print(f"   RO:    {total_profitable_mwh:>8.1f} MWh × £{RO:.2f} = £{ro_cost:,.2f}")
print(f"   FiT:   {total_profitable_mwh:>8.1f} MWh × £{FIT:.2f} = £{fit_cost:,.2f}")
print(f"   CfD:   {total_profitable_mwh:>8.1f} MWh × £{CFD:.2f} = £{cfd_cost:,.2f}")
print(f"   ECO:   {total_profitable_mwh:>8.1f} MWh × £{ECO:.2f} = £{eco_cost:,.2f}")
print(f"   WHD:   {total_profitable_mwh:>8.1f} MWh × £{WHD:.2f} = £{whd_cost:,.2f}")

print(f"\n💰 System Price Stats (profitable periods):")
print(f"   Min: £{system_price_min:.2f}/MWh")
print(f"   Avg: £{system_price_avg:.2f}/MWh")
print(f"   Max: £{system_price_max:.2f}/MWh")

# Write to sheet
print("\n📝 Writing to BESS sheet (Columns B & C)...")
updates = [
    # DUoS - MWh and costs (only profitable periods!)
    ('B28', f'{red_mwh:,.1f}'),           # Red MWh (will be 0)
    ('C28', f'£{red_duos_cost:,.2f}'),    # Red cost (will be £0)
    ('B29', f'{amber_mwh:,.1f}'),         # Amber MWh
    ('C29', f'£{amber_duos_cost:,.2f}'),  # Amber cost
    ('B30', f'{green_mwh:,.1f}'),         # Green MWh
    ('C30', f'£{green_duos_cost:,.2f}'),  # Green cost
    
    # Fixed costs - MWh and costs
    ('B31', f'{total_profitable_mwh:,.1f}'),  # TNUoS MWh
    ('C31', f'£{tnuos_cost:,.2f}'),
    ('B32', f'{total_profitable_mwh:,.1f}'),  # BSUoS MWh
    ('C32', f'£{bsuos_cost:,.2f}'),
    
    # Environmental levies (row 34 is header/summary - skip it)
    ('B35', f'{total_profitable_mwh:,.1f}'),  # CCL MWh
    ('C35', f'£{ccl_cost:,.2f}'),
    ('B36', f'{total_profitable_mwh:,.1f}'),  # RO MWh
    ('C36', f'£{ro_cost:,.2f}'),
    ('B37', f'{total_profitable_mwh:,.1f}'),  # FiT MWh
    ('C37', f'£{fit_cost:,.2f}'),
    ('B38', f'{total_profitable_mwh:,.1f}'),  # CfD MWh (no label in A38)
    ('C38', f'£{cfd_cost:,.2f}'),
    
    # System Buy Price stats (row 39 is header, row 40 has data)
    ('B40', f'{total_profitable_mwh:,.1f}'),  # Volume MWh
    ('C40', f'£{system_price_avg:.2f}'),      # Average price
    ('D40', f'£{system_price_min:.2f}'),      # Minimum price
    ('E40', f'£{system_price_max:.2f}'),      # Maximum price
    ('F40', f'£{total_cost:,.2f}'),           # Total cost
    
    # CfD/ECO/WHD in E/F columns for "With BESS" side
    ('E38', f'{total_profitable_mwh:,.1f}'),  # CfD MWh
    ('F38', f'£{cfd_cost:,.2f}'),
    ('E43', f'{total_profitable_mwh:,.1f}'),  # ECO MWh (row 43 PPA price row)
    ('F43', f'£{eco_cost:,.2f}'),
]

for cell, value in updates:
    bess_sheet.update_acell(cell, value)
    print(f"   {cell}: {value}")

print("\n✅ Complete!")
print(f"\nSummary:")
print(f"  Profitable import: {total_profitable_mwh:,.1f} MWh ({len(df_prof):,} periods)")
print(f"  Red: {red_mwh:.1f} MWh (likely ZERO - Red is too expensive)")
print(f"  Amber: {amber_mwh:.1f} MWh")
print(f"  Green: {green_mwh:.1f} MWh")
