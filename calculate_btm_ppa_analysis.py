#!/usr/bin/env python3
"""
Behind-the-Meter (BtM) PPA Analysis Calculator
Calculates profitable periods where system price + costs < PPA price
Populates BESS sheet rows 23-42 with comprehensive cost and revenue analysis
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

# Configuration
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
MAIN_DASHBOARD_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Fixed costs (£/MWh) - these are constants
FIXED_COSTS = {
    'tnuos': 12.50,
    'bsuos': 4.50,
    'ccl': 7.75,
    'ro': 61.90,
    'fit': 11.50
}
TOTAL_FIXED = sum(FIXED_COSTS.values())  # £98.15/MWh

# DUoS rates (£/MWh) by time band
DUOS_RATES = {
    'red': 17.64,    # SP 33-39 (16:00-19:30 weekdays)
    'amber': 2.05,   # SP 17-32, 40-44 (08:00-16:00, 19:30-22:00 weekdays)
    'green': 0.11    # SP 1-16, 45-48 (off-peak + weekends)
}

def get_duos_band(settlement_period):
    """Determine DUoS time band from settlement period"""
    if 33 <= settlement_period <= 39:
        return 'red'
    elif (17 <= settlement_period <= 32) or (40 <= settlement_period <= 44):
        return 'amber'
    else:
        return 'green'

print("=" * 100)
print("BtM PPA ANALYSIS - CALCULATING PROFITABLE PERIODS")
print("=" * 100)

# Connect to Google Sheets
print("\n📊 Connecting to Google Sheets...")
creds = Credentials.from_service_account_file(
    CREDENTIALS_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
wb = gc.open_by_key(MAIN_DASHBOARD_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

# Read PPA price from B39
print("📋 Reading PPA price from B39...")
ppa_value = (bess_sheet.acell('B39').value or "150").strip().replace('£', '').replace(',', '')
ppa_price = float(ppa_value)
print(f"   PPA Price: £{ppa_price:.2f}/MWh")

# Read HH Data
print("\n📂 Reading HH Data sheet...")
hh_data = hh_sheet.get_all_records()
print(f"   Total HH periods: {len(hh_data)}")

# Convert to DataFrame
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['demand_mwh'] = df_hh['demand_kw'] / 1000 / 2  # Convert kW to MWh (half-hour)
print(f"   Date range: {df_hh['timestamp'].min()} to {df_hh['timestamp'].max()}")

# Connect to BigQuery
print("\n🔍 Querying BigQuery for system prices...")
client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)

# Get system prices for the date range
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
  settlementPeriod,
  MAX(system_buy_price) as system_buy_price
FROM period_data
GROUP BY date, settlementPeriod
ORDER BY date, settlementPeriod
"""

df_prices = client.query(query).to_dataframe()
print(f"   Retrieved {len(df_prices)} price records")

# Calculate system price statistics
system_price_min = df_prices['system_buy_price'].min()
system_price_avg = df_prices['system_buy_price'].mean()
system_price_max = df_prices['system_buy_price'].max()

print(f"\n💷 System Price Statistics:")
print(f"   Min: £{system_price_min:.2f}/MWh")
print(f"   Average: £{system_price_avg:.2f}/MWh")
print(f"   Max: £{system_price_max:.2f}/MWh")

# Merge HH data with system prices
df_hh['date'] = df_hh['timestamp'].dt.date
df_hh['hour'] = df_hh['timestamp'].dt.hour
df_hh['minute'] = df_hh['timestamp'].dt.minute
df_hh['settlement_period'] = ((df_hh['hour'] * 60 + df_hh['minute']) // 30) + 1

# Merge with prices
df_merged = df_hh.merge(
    df_prices,
    left_on=['date', 'settlement_period'],
    right_on=['date', 'settlementPeriod'],
    how='left'
)

print(f"\n🔗 Merged HH data with system prices: {len(df_merged)} records")

# Calculate costs and profitability for each period
print("\n💰 Calculating costs and profitability...")

df_merged['duos_band'] = df_merged['settlement_period'].apply(get_duos_band)
df_merged['duos_rate'] = df_merged['duos_band'].map(DUOS_RATES)
df_merged['total_cost_per_mwh'] = df_merged['system_buy_price'] + df_merged['duos_rate'] + TOTAL_FIXED
df_merged['is_profitable'] = df_merged['total_cost_per_mwh'] < ppa_price
df_merged['profit_per_mwh'] = ppa_price - df_merged['total_cost_per_mwh']

# Calculate costs and revenues
df_merged['import_cost'] = df_merged['demand_mwh'] * df_merged['system_buy_price']
df_merged['duos_cost'] = df_merged['demand_mwh'] * df_merged['duos_rate']
df_merged['fixed_cost'] = df_merged['demand_mwh'] * TOTAL_FIXED
df_merged['total_cost'] = df_merged['import_cost'] + df_merged['duos_cost'] + df_merged['fixed_cost']
df_merged['ppa_revenue'] = df_merged['demand_mwh'] * ppa_price

# Filter profitable periods only
df_profitable = df_merged[df_merged['is_profitable']].copy()

# Calculate totals
total_periods = len(df_merged)
profitable_periods = len(df_profitable)
profitable_pct = (profitable_periods / total_periods * 100) if total_periods > 0 else 0

# Total kWh (convert MWh to kWh)
total_import_kwh = df_merged['demand_mwh'].sum() * 1000
profitable_import_kwh = df_profitable['demand_mwh'].sum() * 1000

# Costs breakdown by DUoS band
duos_red_cost = df_merged[df_merged['duos_band'] == 'red']['duos_cost'].sum()
duos_amber_cost = df_merged[df_merged['duos_band'] == 'amber']['duos_cost'].sum()
duos_green_cost = df_merged[df_merged['duos_band'] == 'green']['duos_cost'].sum()
total_duos_cost = duos_red_cost + duos_amber_cost + duos_green_cost

# Fixed costs totals
total_tnuos = df_merged['demand_mwh'].sum() * FIXED_COSTS['tnuos']
total_bsuos = df_merged['demand_mwh'].sum() * FIXED_COSTS['bsuos']
total_ccl = df_merged['demand_mwh'].sum() * FIXED_COSTS['ccl']
total_ro = df_merged['demand_mwh'].sum() * FIXED_COSTS['ro']
total_fit = df_merged['demand_mwh'].sum() * FIXED_COSTS['fit']

# Revenue
ppa_revenue_total = df_profitable['ppa_revenue'].sum()

print("\n" + "=" * 100)
print("📊 CALCULATION RESULTS")
print("=" * 100)

print(f"\n⚡ VOLUMES:")
print(f"   Total Import kWh: {total_import_kwh:,.0f} kWh")
print(f"   Profitable Import kWh: {profitable_import_kwh:,.0f} kWh")

print(f"\n🔢 PROFITABLE PERIODS:")
print(f"   Count: {profitable_periods:,} of {total_periods:,} ({profitable_pct:.1f}%)")

print(f"\n💷 DUoS COSTS:")
print(f"   Red: £{duos_red_cost:,.2f}")
print(f"   Amber: £{duos_amber_cost:,.2f}")
print(f"   Green: £{duos_green_cost:,.2f}")
print(f"   Total: £{total_duos_cost:,.2f}")

print(f"\n💷 FIXED COSTS:")
print(f"   TNUoS: £{total_tnuos:,.2f}")
print(f"   BSUoS: £{total_bsuos:,.2f}")
print(f"   CCL: £{total_ccl:,.2f}")
print(f"   RO: £{total_ro:,.2f}")
print(f"   FiT: £{total_fit:,.2f}")

print(f"\n💰 REVENUE:")
print(f"   PPA Revenue (profitable periods): £{ppa_revenue_total:,.2f}")

# Prepare data for BESS sheet
# LEFT SIDE (B-D): Direct import without BESS optimization
# For now, both sides will have same values (BESS optimization would be a separate calculation)

print("\n" + "=" * 100)
print("📝 WRITING TO BESS SHEET")
print("=" * 100)

# Prepare update data
updates = [
    # Row 26: Red DUoS
    ['B26', f'£{duos_red_cost:,.2f}'],
    # Row 27: Amber DUoS
    ['B27', f'£{duos_amber_cost:,.2f}'],
    # Row 28: Green DUoS
    ['B28', f'£{duos_green_cost:,.2f}'],
    # Row 29: TNUoS
    ['B29', f'£{total_tnuos:,.2f}'],
    # Row 30: BSUoS
    ['B30', f'£{total_bsuos:,.2f}'],
    # Row 31: CCL
    ['B31', f'£{total_ccl:,.2f}'],
    # Row 32: RO
    ['B32', f'£{total_ro:,.2f}'],
    # Row 33: FiT
    ['B33', f'£{total_fit:,.2f}'],
    # Row 35: Min system price
    ['B35', f'£{system_price_min:.2f}'],
    # Row 36: Avg system price
    ['B36', f'£{system_price_avg:.2f}'],
    # Row 37: Max system price
    ['B37', f'£{system_price_max:.2f}'],
    # Row 38: Import kWh
    ['B38', f'{profitable_import_kwh:,.0f}'],
    # Row 39: PPA kWh (same as import for profitable periods)
    # B39 already contains PPA price, skip
    # Row 40: Profitable Periods
    ['B40', f'{profitable_periods:,}'],
    # Row 42: PPA Revenue
    ['B42', f'£{ppa_revenue_total:,.2f}'],
]

# Write updates
print("\n📝 Updating cells...")
for cell, value in updates:
    bess_sheet.update_acell(cell, value)
    print(f"   {cell}: {value}")

print("\n✅ Update complete!")

print("\n" + "=" * 100)
print("🎯 SUMMARY")
print("=" * 100)
print(f"""
PPA Price: £{ppa_price:.2f}/MWh
Profitable Periods: {profitable_periods:,}/{total_periods:,} ({profitable_pct:.1f}%)
Profitable Import: {profitable_import_kwh:,.0f} kWh
PPA Revenue: £{ppa_revenue_total:,.2f}

System Price Range: £{system_price_min:.2f} - £{system_price_max:.2f}/MWh (avg £{system_price_avg:.2f})

Total Costs:
- DUoS: £{total_duos_cost:,.2f} (Red: £{duos_red_cost:,.2f}, Amber: £{duos_amber_cost:,.2f}, Green: £{duos_green_cost:,.2f})
- Fixed: £{total_tnuos + total_bsuos + total_ccl + total_ro + total_fit:,.2f}

Results written to BESS sheet rows 26-42, column B
Note: Right side (columns F-H) for "With BESS" will require separate optimization logic
""")
