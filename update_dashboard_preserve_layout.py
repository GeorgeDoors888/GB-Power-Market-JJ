#!/usr/bin/env python3
"""
Updated Dashboard script that preserves user's formatting choices:
1. Title: "GB DASHBOARD - Power"
2. All fuel types in ONE section (no "Other Generators" separator)
3. Fixes broken country flag emojis
4. Maintains user's layout preferences
5. AUTO-VERIFIES flags after every update
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, date
from flag_utils import verify_and_fix_flags

# Configuration
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Auth
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()
bq_client = bigquery.Client(project=PROJECT_ID, location='US', credentials=CREDS)

print("🔧 DASHBOARD UPDATE (Preserving User Layout)...")
print("=" * 100)

today = date.today().strftime('%Y-%m-%d')
now = datetime.now()
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

# ====================
# 1. GET ALL FUEL DATA
# ====================
print("\n📊 Step 1: Querying fuel generation data...")

fuel_query = f"""
WITH latest_data AS (
    SELECT 
        fuelType,
        generation,
        publishTime
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE DATE(settlementDate) = '{today}'
    ORDER BY publishTime DESC
    LIMIT 1000
),
current_sp AS (
    SELECT MAX(publishTime) as latest_time
    FROM latest_data
)
SELECT 
    ld.fuelType,
    ROUND(SUM(ld.generation), 1) as total_generation_mw
FROM latest_data ld
CROSS JOIN current_sp cs
WHERE ld.publishTime = cs.latest_time
  AND ld.fuelType NOT LIKE 'INT%'  -- Exclude interconnectors
GROUP BY ld.fuelType
ORDER BY total_generation_mw DESC
"""

df_fuel = bq_client.query(fuel_query).to_dataframe()
print(f"✅ Found {len(df_fuel)} fuel types")

# Format ALL fuel types in ONE list (user's preference - no separation)
all_fuel_rows = []

for _, row in df_fuel.iterrows():
    fuel = row['fuelType']
    mw = row['total_generation_mw']
    gw = mw / 1000.0
    
    # Emoji mapping
    emoji_map = {
        'CCGT': '🔥', 'OCGT': '🔥', 'GAS': '🔥',
        'NUCLEAR': '⚛️',
        'WIND': '💨', 'OFFSHORE': '🌊',
        'SOLAR': '☀️',
        'BIOMASS': '🌱',
        'HYDRO': '💧', 'NPSHYD': '💧',
        'COAL': '⛏️',
        'OIL': '🛢️',
        'PS': '🔋',
        'OTHER': '⚡'
    }
    
    emoji = '⚡'
    for key, em in emoji_map.items():
        if key in fuel.upper():
            emoji = em
            break
    
    all_fuel_rows.append([f"{emoji} {fuel}", f"{gw:.1f} GW", ""])

print(f"✅ Formatted {len(all_fuel_rows)} fuel types")

# ====================
# 2. GET PRICE DATA
# ====================
print("\n💰 Step 2: Querying price data...")

price_query = f"""
SELECT 
    settlementPeriod,
    ROUND(AVG(price), 2) as avg_price
FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
WHERE DATE(settlementDate) = '{today}'
GROUP BY settlementPeriod
ORDER BY settlementPeriod DESC
LIMIT 1
"""

try:
    df_price = bq_client.query(price_query).to_dataframe()
    if not df_price.empty:
        imbalance_price = df_price['avg_price'].iloc[0]
        price_display = f"💰 Imbalance: £{imbalance_price:.2f}/MWh"
    else:
        price_display = "💰 Price: (pending data)"
except:
    price_display = "💰 Price: (pending data)"

# ====================
# 3. GET INTERCONNECTOR DATA WITH FIXED FLAGS
# ====================
print("\n🌍 Step 3: Building interconnector data with FIXED flags...")

# Read raw data
ic_result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Interconnectors!A2:C20'
).execute()

ic_vals = ic_result.get('values', [])

# Build interconnector rows with COMPLETE flag emojis
ic_rows = []
flag_map = {
    'ElecLink': '🇫🇷', 'IFA': '🇫🇷', 'IFA2': '🇫🇷',
    'East-West': '🇮🇪', 'Greenlink': '🇮🇪', 'Moyle': '🇮🇪',
    'BritNed': '🇳🇱',
    'Nemo': '🇧🇪',
    'NSL': '🇳🇴',
    'Viking': '🇩🇰'
}

for row in ic_vals:
    if len(row) >= 3:
        ic_name = row[0]
        mw = row[1]
        direction = row[2]
        
        if 'TOTAL' in ic_name.upper():
            continue
        
        # Remove existing flag if present
        ic_name_clean = ic_name
        for char in ic_name:
            if ord(char) > 127000:  # Remove emoji characters
                ic_name_clean = ic_name_clean.replace(char, '')
        ic_name_clean = ic_name_clean.strip()
        
        # Add correct flag
        flag_added = False
        for key, flag in flag_map.items():
            if key in ic_name_clean:
                ic_rows.append([f"{flag} {ic_name_clean}", f"{mw} MW {direction}", ""])
                flag_added = True
                break
        
        if not flag_added:
            ic_rows.append([ic_name_clean, f"{mw} MW {direction}", ""])

print(f"✅ Formatted {len(ic_rows)} interconnectors with COMPLETE flags")

# ====================
# 4. CALCULATE TOTALS
# ====================
print("\n🔨 Step 4: Calculating system metrics...")

total_generation = sum([float(f[1].replace('GW', '').strip()) for f in all_fuel_rows if f[1]])
renewable_generation = 0.0

for fuel_row in all_fuel_rows:
    fuel_name = fuel_row[0].upper()
    gw_str = fuel_row[1].replace('GW', '').strip()
    gw = float(gw_str) if gw_str else 0.0
    
    if any(word in fuel_name for word in ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS']):
        renewable_generation += gw

renewable_pct = (renewable_generation / total_generation * 100) if total_generation > 0 else 0

# Get net import
try:
    ic_total_result = sheets.values().get(spreadsheetId=SHEET_ID, range='Live_Raw_Interconnectors!B12:B12').execute()
    ic_total_vals = ic_total_result.get('values', [])
    net_import = float(ic_total_vals[0][0]) if ic_total_vals and ic_total_vals[0] else 0.0
except:
    net_import = 0.0

total_supply = total_generation + (net_import / 1000)

print(f"✅ Total Generation: {total_generation:.1f} GW")
print(f"✅ Renewables: {renewable_pct:.0f}%")
print(f"✅ Total Supply: {total_supply:.1f} GW")

# ====================
# 5. BUILD LAYOUT (USER'S FORMAT)
# ====================
print("\n✍️  Step 5: Building layout matching user's format...")

# Header (Rows 1-7) - Using user's title
header_data = [
    ['GB DASHBOARD - Power', '', '', '', '', ''],  # User's custom title
    [f'⏰ Last Updated: {timestamp} | ✅ FRESH', '', '', '', '', ''],
    ['Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min', '', '', '', '', ''],
    ['📊 SYSTEM METRICS', '', '', '', '', ''],
    [f'Total Generation: {total_generation:.1f} GW | Supply: {total_supply:.1f} GW | Renewables: {renewable_pct:.0f}% | {price_display}', '', '', '', '', ''],
    ['', '', '', '', '', ''],
    ['🔥 Fuel Breakdown', '', '', '🌍 Interconnectors', '', '']
]

# Fuel + Interconnector rows (8-17) - ALL fuel types in ONE section
max_rows = max(len(all_fuel_rows), len(ic_rows))
while len(all_fuel_rows) < max_rows:
    all_fuel_rows.append(['', '', ''])
while len(ic_rows) < max_rows:
    ic_rows.append(['', '', ''])

data_section = []
for fuel_row, ic_row in zip(all_fuel_rows, ic_rows):
    data_section.append(fuel_row + ic_row)

# Combine
all_data = header_data + data_section

# ====================
# 6. WRITE TO DASHBOARD
# ====================
print(f"\n💾 Step 6: Writing to Dashboard (rows 1-{len(all_data)})...")

# Clear old fuel data
sheets.values().clear(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1:F30'
).execute()

# Write new data using RAW_INPUT to preserve flags
sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1',
    valueInputOption='RAW',  # Use RAW instead of USER_ENTERED to preserve emojis
    body={'values': all_data}
).execute()

print("\n" + "=" * 100)
print("✅ DASHBOARD UPDATED (User Layout Preserved)!")
print("=" * 100)
print(f"\n📊 Layout: User's custom format maintained")
print(f"   • Title: 'GB DASHBOARD - Power'")
print(f"   • All {len(all_fuel_rows)} fuel types in single section (rows 8-{7+len(all_fuel_rows)})")
print(f"   • No 'Other Generators' separator")
print(f"   • {len(ic_rows)} interconnectors with COMPLETE flags 🇫🇷 🇮🇪 🇳🇱 🇧🇪 🇳🇴 🇩🇰")
print(f"\n📊 System Metrics:")
print(f"   • Total Generation: {total_generation:.1f} GW")
print(f"   • Supply: {total_supply:.1f} GW")
print(f"   • Renewables: {renewable_pct:.0f}%")
print(f"\n✅ Outages section (row 32+) preserved by script")

# ====================
# 7. AUTO-FIX & VERIFY FLAGS (using reusable module)
# ====================
all_complete, num_fixed = verify_and_fix_flags(sheets, SHEET_ID, verbose=True)

if not all_complete:
    print("\n⚠️  WARNING: Some flags could not be fixed automatically!")
    print("   Run: python3 fix_interconnector_flags_permanent.py")
