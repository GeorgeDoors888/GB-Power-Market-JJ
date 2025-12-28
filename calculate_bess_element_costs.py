#!/usr/bin/env python3
"""
Calculate BtM PPA BESS Element Costs
Populates columns F-I (rows 27-37) with BESS-specific cost calculations
Includes DUoS (Red/Amber/Green), TNUoS, BNUoS, Environmental Levies (CCL, RO, FiT)

SHEET STRUCTURE (as of 2025-12-02):
  - F13:F16 = BESS config (capacity, duration, cycles)
  - B10:D10 = DNO DUoS rates (Red, Amber, Green in p/kWh)
  - D43 = PPA price (£/MWh)
  - F28:H37 = BESS cost outputs (rates, kWh, costs £)

IMPORTANT: DNO rates are in ROW 10 (not row 9 which is header)
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
    'bnuos': 4.50,
    'ccl': 7.75,
    'ro': 61.90,
    'fit': 11.50
}

# Cell mappings (source of truth)
CELL_IMPORT_CAPACITY = "F13"
CELL_EXPORT_CAPACITY = "F14"
CELL_DURATION = "F15"
CELL_MAX_CYCLES = "F16"
CELL_RED_RATE = "B10"      # Row 10, NOT 9!
CELL_AMBER_RATE = "C10"    # Row 10, NOT 9!
CELL_GREEN_RATE = "D10"    # Row 10, NOT 9!
CELL_PPA_PRICE = "D43"

# DUoS rates will be read from sheet row 9
# Red Rate (p/kWh), Amber Rate (p/kWh), Green Rate (p/kWh)

def get_duos_band(settlement_period, day_of_week):
    """
    Determine DUoS time band from settlement period and day
    Red: SP 33-39 (16:00-19:30 weekdays)
    Amber: SP 17-32, 40-44 (08:00-16:00, 19:30-22:00 weekdays)
    Green: SP 1-16, 45-48 (off-peak + all weekend)
    """
    # Weekend is always green
    if day_of_week >= 5:  # Saturday=5, Sunday=6
        return 'green'
    
    # Weekday time bands
    if 33 <= settlement_period <= 39:
        return 'red'
    elif (17 <= settlement_period <= 32) or (40 <= settlement_period <= 44):
        return 'amber'
    else:
        return 'green'

print("=" * 100)
print("BtM PPA BESS ELEMENT COSTS CALCULATOR")
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

# Read DNO rates from row 10 (B10, C10, D10 = Red, Amber, Green in p/kWh)
print("\n📋 Reading DNO DUoS rates from row 10...")
red_rate_pkwh = float(bess_sheet.acell(CELL_RED_RATE).value or 1.764)
amber_rate_pkwh = float(bess_sheet.acell(CELL_AMBER_RATE).value or 0.205)
green_rate_pkwh = float(bess_sheet.acell(CELL_GREEN_RATE).value or 0.011)

# Convert p/kWh to £/MWh
DUOS_RATES = {
    'red': red_rate_pkwh * 10,      # p/kWh × 10 = £/MWh
    'amber': amber_rate_pkwh * 10,
    'green': green_rate_pkwh * 10
}

print(f"   Red Rate: {red_rate_pkwh} p/kWh = £{DUOS_RATES['red']:.2f}/MWh")
print(f"   Amber Rate: {amber_rate_pkwh} p/kWh = £{DUOS_RATES['amber']:.2f}/MWh")
print(f"   Green Rate: {green_rate_pkwh} p/kWh = £{DUOS_RATES['green']:.2f}/MWh")

# Read BESS configuration
print("\n⚡ Reading BESS configuration...")
import_capacity_kw = float(bess_sheet.acell(CELL_IMPORT_CAPACITY).value or 2500)
export_capacity_kw = float(bess_sheet.acell(CELL_EXPORT_CAPACITY).value or 2500)
duration_hrs = float(bess_sheet.acell(CELL_DURATION).value or 2)
max_cycles = float(bess_sheet.acell(CELL_MAX_CYCLES).value or 4)

print(f"   Import Capacity: {import_capacity_kw:,.0f} kW")
print(f"   Export Capacity: {export_capacity_kw:,.0f} kW")
print(f"   Duration: {duration_hrs} hours")
print(f"   Max Cycles/Day: {max_cycles}")

# Read PPA price
print("\n💷 Reading PPA price...")
ppa_value = (bess_sheet.acell(CELL_PPA_PRICE).value or "150").strip().replace('£', '').replace(',', '')
ppa_price = float(ppa_value)
print(f"   PPA Price: £{ppa_price:.2f}/MWh")

# Read HH Data
print("\n📂 Reading HH Data sheet...")
hh_data = hh_sheet.get_all_records()
df_hh = pd.DataFrame(hh_data)
df_hh['timestamp'] = pd.to_datetime(df_hh['Timestamp'])
df_hh['demand_kw'] = pd.to_numeric(df_hh['Demand (kW)'], errors='coerce')
df_hh['demand_mwh'] = df_hh['demand_kw'] / 1000 / 2  # Convert kW to MWh (half-hour)
print(f"   Total HH periods: {len(df_hh)}")
print(f"   Date range: {df_hh['timestamp'].min()} to {df_hh['timestamp'].max()}")

# Connect to BigQuery
print("\n🔍 Querying BigQuery for system prices...")
client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)

min_date = df_hh['timestamp'].min().date()
max_date = df_hh['timestamp'].max().date()

query = f"""
WITH period_data AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    MAX(systemBuyPrice) as system_buy_price,
    MAX(systemSellPrice) as system_sell_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
  WHERE CAST(settlementDate AS DATE) >= '{min_date}'
    AND CAST(settlementDate AS DATE) <= '{max_date}'
    AND systemBuyPrice IS NOT NULL
  GROUP BY date, settlementPeriod
  
  UNION ALL
  
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    MAX(CAST(price AS FLOAT64)) as system_buy_price,
    MAX(CAST(price AS FLOAT64)) as system_sell_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
  WHERE CAST(settlementDate AS DATE) >= '{min_date}'
    AND CAST(settlementDate AS DATE) <= '{max_date}'
    AND price IS NOT NULL
  GROUP BY date, settlementPeriod
)
SELECT 
  date,
  settlementPeriod,
  MAX(system_buy_price) as system_buy_price,
  MAX(system_sell_price) as system_sell_price
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
df_hh['day_of_week'] = df_hh['timestamp'].dt.dayofweek
df_hh['settlement_period'] = ((df_hh['hour'] * 60 + df_hh['minute']) // 30) + 1

df_merged = df_hh.merge(
    df_prices,
    left_on=['date', 'settlement_period'],
    right_on=['date', 'settlementPeriod'],
    how='left'
)

print(f"\n🔗 Merged HH data with system prices: {len(df_merged)} records")

# ==================================================================================
# CALCULATE BESS OPERATION COSTS
# ==================================================================================

print("\n" + "=" * 100)
print("💰 CALCULATING BESS COSTS (DUoS-Aware Arbitrage)")
print("=" * 100)

# Determine DUoS band for each period
df_merged['duos_band'] = df_merged.apply(
    lambda row: get_duos_band(row['settlement_period'], row['day_of_week']), 
    axis=1
)
df_merged['duos_rate'] = df_merged['duos_band'].map(DUOS_RATES)

# Calculate total cost per MWh
TOTAL_FIXED = sum(FIXED_COSTS.values())
df_merged['total_cost_per_mwh'] = df_merged['system_buy_price'] + df_merged['duos_rate'] + TOTAL_FIXED

# BESS STRATEGY:
# - CHARGE during GREEN periods (low DUoS, low system price)
# - DISCHARGE during RED periods (high DUoS - avoid expensive grid import)
# - Only charge when total cost < PPA price AND in GREEN or low-cost AMBER

# Define charging strategy: prioritize GREEN, allow AMBER if cheap enough
df_merged['should_charge'] = False

# GREEN: Charge if cost < PPA - 20 (allow margin for discharge value)
green_mask = (df_merged['duos_band'] == 'green') & (df_merged['total_cost_per_mwh'] < ppa_price - 20)
df_merged.loc[green_mask, 'should_charge'] = True

# AMBER: Only if very cheap (system price < 40)
amber_cheap_mask = (df_merged['duos_band'] == 'amber') & (df_merged['system_buy_price'] < 40) & (df_merged['total_cost_per_mwh'] < ppa_price - 30)
df_merged.loc[amber_cheap_mask, 'should_charge'] = True

# RED: NEVER charge during red periods (always too expensive with DUoS premium)
# (already excluded by not setting should_charge for red band)

# Calculate charging
df_merged['bess_charge_mwh'] = 0.0
df_merged.loc[df_merged['should_charge'], 'bess_charge_mwh'] = df_merged['demand_mwh']

# Apply BESS capacity constraint (can't charge more than capacity/2 per half-hour)
max_charge_per_period = (import_capacity_kw / 1000) / 2  # kW to MW, then /2 for half-hour
df_merged['bess_charge_mwh'] = df_merged['bess_charge_mwh'].clip(upper=max_charge_per_period)

print(f"\n📊 CHARGING STRATEGY:")
print(f"   GREEN periods eligible: {green_mask.sum():,}")
print(f"   AMBER periods eligible: {amber_cheap_mask.sum():,}")
print(f"   RED periods (avoided): {(df_merged['duos_band'] == 'red').sum():,}")
print(f"   Total periods charging: {df_merged['should_charge'].sum():,}")

# Calculate costs for BESS charging
df_merged['bess_import_cost'] = df_merged['bess_charge_mwh'] * df_merged['system_buy_price']
df_merged['bess_duos_cost'] = df_merged['bess_charge_mwh'] * df_merged['duos_rate']
df_merged['bess_fixed_cost'] = df_merged['bess_charge_mwh'] * TOTAL_FIXED
df_merged['bess_total_cost'] = df_merged['bess_import_cost'] + df_merged['bess_duos_cost'] + df_merged['bess_fixed_cost']

# Calculate totals
total_bess_kwh = df_merged['bess_charge_mwh'].sum() * 1000
total_bess_mwh = df_merged['bess_charge_mwh'].sum()

# Costs breakdown by DUoS band (both kWh and MWh)
bess_duos_red_kwh = (df_merged[df_merged['duos_band'] == 'red']['bess_charge_mwh'].sum() * 1000)
bess_duos_amber_kwh = (df_merged[df_merged['duos_band'] == 'amber']['bess_charge_mwh'].sum() * 1000)
bess_duos_green_kwh = (df_merged[df_merged['duos_band'] == 'green']['bess_charge_mwh'].sum() * 1000)

bess_duos_red_mwh = df_merged[df_merged['duos_band'] == 'red']['bess_charge_mwh'].sum()
bess_duos_amber_mwh = df_merged[df_merged['duos_band'] == 'amber']['bess_charge_mwh'].sum()
bess_duos_green_mwh = df_merged[df_merged['duos_band'] == 'green']['bess_charge_mwh'].sum()

bess_duos_red_cost = df_merged[df_merged['duos_band'] == 'red']['bess_duos_cost'].sum()
bess_duos_amber_cost = df_merged[df_merged['duos_band'] == 'amber']['bess_duos_cost'].sum()
bess_duos_green_cost = df_merged[df_merged['duos_band'] == 'green']['bess_duos_cost'].sum()
bess_total_duos_cost = bess_duos_red_cost + bess_duos_amber_cost + bess_duos_green_cost

# Fixed costs totals (based on actual BESS charging)
bess_tnuos = total_bess_mwh * FIXED_COSTS['tnuos']
bess_bnuos = total_bess_mwh * FIXED_COSTS['bnuos']
bess_ccl = total_bess_mwh * FIXED_COSTS['ccl']
bess_ro = total_bess_mwh * FIXED_COSTS['ro']
bess_fit = total_bess_mwh * FIXED_COSTS['fit']

# Environmental levies total
bess_env_levies = bess_ccl + bess_ro + bess_fit

print(f"\n⚡ BESS CHARGING VOLUMES:")
print(f"   Total BESS Charging: {total_bess_kwh:,.0f} kWh")
print(f"   Red Band: {bess_duos_red_kwh:,.0f} kWh")
print(f"   Amber Band: {bess_duos_amber_kwh:,.0f} kWh")
print(f"   Green Band: {bess_duos_green_kwh:,.0f} kWh")

print(f"\n💷 BESS DUoS COSTS:")
print(f"   Red: £{bess_duos_red_cost:,.2f}")
print(f"   Amber: £{bess_duos_amber_cost:,.2f}")
print(f"   Green: £{bess_duos_green_cost:,.2f}")
print(f"   Total DUoS: £{bess_total_duos_cost:,.2f}")

print(f"\n💷 BESS NETWORK COSTS:")
print(f"   TNUoS: £{bess_tnuos:,.2f}")
print(f"   BNUoS: £{bess_bnuos:,.2f}")

print(f"\n💷 BESS ENVIRONMENTAL LEVIES:")
print(f"   CCL: £{bess_ccl:,.2f}")
print(f"   RO: £{bess_ro:,.2f}")
print(f"   FiT: £{bess_fit:,.2f}")
print(f"   Total Environmental: £{bess_env_levies:,.2f}")

# ==================================================================================
# UPDATE BESS SHEET
# ==================================================================================

print("\n" + "=" * 100)
print("📝 WRITING TO BESS SHEET (COLUMNS E-H)")
print("=" * 100)

# Update BESS costs section (Column E = MWh, F = Rate/Label, G = kWh, H = Costs)
updates = [
    # Header row (26) - already exists
    
    # DUoS section (rows 28-30)
    ['E28', bess_duos_red_mwh],              # Red MWh
    ['F28', f'{red_rate_pkwh} p/kWh'],       # Red rate
    ['G28', bess_duos_red_kwh],              # Red kWh
    ['H28', f'£{bess_duos_red_cost:,.2f}'],  # Red cost
    
    ['E29', bess_duos_amber_mwh],            # Amber MWh
    ['F29', f'{amber_rate_pkwh} p/kWh'],     # Amber rate
    ['G29', bess_duos_amber_kwh],            # Amber kWh
    ['H29', f'£{bess_duos_amber_cost:,.2f}'],# Amber cost
    
    ['E30', bess_duos_green_mwh],            # Green MWh
    ['F30', f'{green_rate_pkwh} p/kWh'],     # Green rate
    ['G30', bess_duos_green_kwh],            # Green kWh
    ['H30', f'£{bess_duos_green_cost:,.2f}'],# Green cost
    
    # Network costs (rows 31-32)
    ['E31', total_bess_mwh],                      # TNUoS MWh
    ['F31', f'£{FIXED_COSTS["tnuos"]:.2f}/MWh'],  # TNUoS rate
    ['G31', total_bess_kwh],                      # TNUoS kWh
    ['H31', f'£{bess_tnuos:,.2f}'],               # TNUoS cost
    
    ['E32', total_bess_mwh],                      # BNUoS MWh
    ['F32', f'£{FIXED_COSTS["bnuos"]:.2f}/MWh'],  # BNUoS rate
    ['G32', total_bess_kwh],                      # BNUoS kWh
    ['H32', f'£{bess_bnuos:,.2f}'],               # BNUoS cost
    
    # Environmental Levies (row 34) - total
    ['E34', total_bess_mwh],                      # Environmental MWh
    ['F34', 'Total'],                             # Label
    ['G34', total_bess_kwh],                      # Environmental kWh
    ['H34', f'£{bess_env_levies:,.2f}'],          # Environmental total
    
    # Individual levies (rows 35-37)
    ['E35', total_bess_mwh],                      # CCL MWh
    ['F35', f'£{FIXED_COSTS["ccl"]:.2f}/MWh'],    # CCL rate
    ['G35', total_bess_kwh],                      # CCL kWh
    ['H35', f'£{bess_ccl:,.2f}'],                 # CCL cost
    
    ['E36', total_bess_mwh],                      # RO MWh
    ['F36', f'£{FIXED_COSTS["ro"]:.2f}/MWh'],     # RO rate
    ['G36', total_bess_kwh],                      # RO kWh
    ['H36', f'£{bess_ro:,.2f}'],                  # RO cost
    
    ['E37', total_bess_mwh],                      # FiT MWh
    ['F37', f'£{FIXED_COSTS["fit"]:.2f}/MWh'],    # FiT rate
    ['G37', total_bess_kwh],                      # FiT kWh
    ['H37', f'£{bess_fit:,.2f}'],                 # FiT cost
]

# Apply updates
print("\n📝 Updating cells...")
for update in updates:
    cell = update[0]
    value = update[1]
    
    # Format numbers for display
    if isinstance(value, (int, float)) and not isinstance(value, str):
        # Column E should show MWh with decimals
        if cell.startswith('E'):
            display_value = f'{value:,.2f}'
        # Column G shows kWh without decimals
        elif value >= 1000:
            display_value = f'{value:,.0f}'
        else:
            display_value = f'{value:.2f}'
    else:
        display_value = value
    
    bess_sheet.update_acell(cell, display_value)
    print(f"   {cell}: {display_value}")

print("\n✅ Update complete!")

print("\n" + "=" * 100)
print("🎯 SUMMARY - BtM PPA BESS COSTS")
print("=" * 100)
print(f"""
BESS Charging Profile:
- Total Charging: {total_bess_kwh:,.0f} kWh
- Red Band: {bess_duos_red_kwh:,.0f} kWh (16:00-19:30 weekdays)
- Amber Band: {bess_duos_amber_kwh:,.0f} kWh (08:00-16:00, 19:30-22:00 weekdays)
- Green Band: {bess_duos_green_kwh:,.0f} kWh (off-peak + weekends)

BESS Cost Breakdown:
- DUoS Total: £{bess_total_duos_cost:,.2f}
  * Red: £{bess_duos_red_cost:,.2f} @ {red_rate_pkwh} p/kWh
  * Amber: £{bess_duos_amber_cost:,.2f} @ {amber_rate_pkwh} p/kWh
  * Green: £{bess_duos_green_cost:,.2f} @ {green_rate_pkwh} p/kWh

- Network Costs: £{bess_tnuos + bess_bnuos:,.2f}
  * TNUoS: £{bess_tnuos:,.2f} @ £{FIXED_COSTS['tnuos']:.2f}/MWh
  * BNUoS: £{bess_bnuos:,.2f} @ £{FIXED_COSTS['bnuos']:.2f}/MWh

- Environmental Levies: £{bess_env_levies:,.2f}
  * CCL: £{bess_ccl:,.2f} @ £{FIXED_COSTS['ccl']:.2f}/MWh
  * RO: £{bess_ro:,.2f} @ £{FIXED_COSTS['ro']:.2f}/MWh
  * FiT: £{bess_fit:,.2f} @ £{FIXED_COSTS['fit']:.2f}/MWh

TOTAL BESS COSTS: £{bess_total_duos_cost + bess_tnuos + bess_bnuos + bess_env_levies:,.2f}

Results written to BESS sheet columns E-H (rows 28-37)
  • Column E: MWh (energy in megawatt-hours)
  • Column F: Rates (p/kWh or £/MWh)
  • Column G: kWh (energy in kilowatt-hours)
  • Column H: Costs (£)
View: https://docs.google.com/spreadsheets/d/{MAIN_DASHBOARD_ID}/
""")
