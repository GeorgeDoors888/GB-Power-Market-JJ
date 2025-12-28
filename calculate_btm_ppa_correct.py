#!/usr/bin/env python3
"""
BtM PPA Analysis - CORRECTED COLUMN MAPPING
Non-BESS: Column B (kWh) and Column C (£ costs)
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
    if 16 <= hour < 19:  # 16:00-19:00
        return 'Red'
    elif (8 <= hour < 16) or (19 <= hour < 22):
        return 'Amber'
    else:
        return 'Green'

print("=" * 100)
print("BtM PPA ANALYSIS - NON-BESS (Corrected Mapping)")
print("=" * 100)

# Connect to Google Sheets
print("\n📊 Connecting to Google Sheets...")
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
bess_sheet = wb.worksheet('BESS')
hh_sheet = wb.worksheet('HH Data')

# Read PPA price
ppa_value = (bess_sheet.acell('B39').value or "150").strip().replace('£', '').replace(',', '')
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
df['duos_rate_per_kwh'] = df['duos_band'].map({'Red': DUOS_RED, 'Amber': DUOS_AMBER, 'Green': DUOS_GREEN})

# Calculate total cost per MWh
df['system_price_per_mwh'] = df['system_buy_price']
df['duos_cost_per_mwh'] = df['duos_rate_per_kwh'] / 100 * 1000  # Convert p/kWh to £/MWh
df['total_cost_per_mwh'] = df['system_price_per_mwh'] + df['duos_cost_per_mwh'] + TOTAL_FIXED

# Profitable when grid cost < PPA price
df['profitable'] = df['total_cost_per_mwh'] < ppa_price

# Calculate totals by DUoS band
red_kwh = df[df['duos_band'] == 'Red']['demand_kw'].sum() / 2  # Half-hourly to kWh
amber_kwh = df[df['duos_band'] == 'Amber']['demand_kw'].sum() / 2
green_kwh = df[df['duos_band'] == 'Green']['demand_kw'].sum() / 2

red_cost = red_kwh * DUOS_RED / 100
amber_cost = amber_kwh * DUOS_AMBER / 100
green_cost = green_kwh * DUOS_GREEN / 100

# Fixed costs (for ALL consumption, not just profitable)
total_mwh = df['demand_mwh'].sum()
tnuos_cost = total_mwh * TNUOS
bsuos_cost = total_mwh * BSUOS
ccl_cost = total_mwh * CCL
ro_cost = total_mwh * RO
fit_cost = total_mwh * FIT
cfd_cost = total_mwh * CFD
eco_cost = total_mwh * ECO
whd_cost = total_mwh * WHD

# Profitable periods only
profitable_kwh = (df[df['profitable']]['demand_mwh'].sum() * 1000)
profitable_count = df['profitable'].sum()

print("\n" + "=" * 100)
print("RESULTS")
print("=" * 100)
print(f"\n⚡ DUoS Consumption:")
print(f"   Red:   {red_kwh:,.0f} kWh → £{red_cost:,.2f}")
print(f"   Amber: {amber_kwh:,.0f} kWh → £{amber_cost:,.2f}")
print(f"   Green: {green_kwh:,.0f} kWh → £{green_cost:,.2f}")

print(f"\n💷 Fixed Costs (total consumption {total_mwh:,.0f} MWh):")
print(f"   TNUoS: £{tnuos_cost:,.2f}")
print(f"   BSUoS: £{bsuos_cost:,.2f}")
print(f"   CCL:   £{ccl_cost:,.2f}")
print(f"   RO:    £{ro_cost:,.2f}")
print(f"   FiT:   £{fit_cost:,.2f}")
print(f"   CfD:   £{cfd_cost:,.2f}")
print(f"   ECO:   £{eco_cost:,.2f}")
print(f"   WHD:   £{whd_cost:,.2f}")

print(f"\n✅ Profitable Import:")
print(f"   Periods: {profitable_count:,} ({profitable_count/len(df)*100:.1f}%)")
print(f"   Volume:  {profitable_kwh:,.0f} kWh")

# Write to sheet - Column B (kWh) and Column C (£ costs)
print("\n📝 Writing to BESS sheet (Columns B & C)...")
updates = [
    ('B28', f'{red_kwh:,.0f}'),
    ('C28', f'£{red_cost:,.2f}'),
    ('B29', f'{amber_kwh:,.0f}'),
    ('C29', f'£{amber_cost:,.2f}'),
    ('B30', f'{green_kwh:,.0f}'),
    ('C30', f'£{green_cost:,.2f}'),
    ('B31', f'{total_mwh:,.0f}'),
    ('C31', f'£{tnuos_cost:,.2f}'),
    ('B32', f'{total_mwh:,.0f}'),
    ('C32', f'£{bsuos_cost:,.2f}'),
    ('B35', f'{total_mwh:,.0f}'),
    ('C35', f'£{ccl_cost:,.2f}'),
    ('B36', f'{total_mwh:,.0f}'),
    ('C36', f'£{ro_cost:,.2f}'),
    ('B37', f'{total_mwh:,.0f}'),
    ('C37', f'£{fit_cost:,.2f}'),
    ('B38', f'{total_mwh:,.0f}'),
    ('C38', f'£{cfd_cost:,.2f}'),
    ('B39', f'{total_mwh:,.0f}'),
    ('C39', f'£{eco_cost:,.2f}'),
    ('B40', f'{total_mwh:,.0f}'),
    ('C40', f'£{whd_cost:,.2f}'),
]

for cell, value in updates:
    bess_sheet.update_acell(cell, value)
    print(f"   {cell}: {value}")

print("\n✅ Complete!")
print(f"\nNon-BESS scenario: {profitable_count:,} profitable periods, {profitable_kwh:,.0f} kWh")
