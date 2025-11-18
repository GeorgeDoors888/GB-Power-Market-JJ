#!/usr/bin/env python3
"""
FIX DASHBOARD - FINAL VERSION:
1. Filter OUT interconnector entries from fuel section
2. Show ONLY actual generation fuel types
3. Keep interconnectors in their own column with proper flags
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, date

# Configuration
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Auth
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()
bq_client = bigquery.Client(project=PROJECT_ID, location='US', credentials=CREDS)

print("🔧 FIXING DASHBOARD - CLEAN FUEL BREAKDOWN...")
print("=" * 80)

# ====================
# 1. GET FUEL BREAKDOWN (EXCLUDE INTERCONNECTORS)
# ====================
print("\n📊 Step 1: Querying ACTUAL fuel generation (excluding interconnectors)...")

today = date.today().strftime('%Y-%m-%d')

fuel_query = f"""
WITH latest_data AS (
    SELECT 
        fuelType,
        generation,
        publishTime,
        settlementDate,
        settlementPeriod
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
  AND ld.fuelType NOT LIKE 'INT%'  -- EXCLUDE all interconnector entries
  AND ld.generation > 0              -- EXCLUDE negative/zero values
GROUP BY ld.fuelType
ORDER BY total_generation_mw DESC
"""

df_fuel = bq_client.query(fuel_query).to_dataframe()

print(f"✅ Found {len(df_fuel)} ACTUAL fuel types (interconnectors excluded)")

# Format fuel data with emojis
fuel_rows = []
for _, row in df_fuel.iterrows():
    fuel = row['fuelType']
    mw = row['total_generation_mw']
    gw = mw / 1000.0
    
    # Fuel type emoji mapping
    emoji_map = {
        'CCGT': '🔥',
        'OCGT': '🔥',
        'GAS': '🔥',
        'NUCLEAR': '⚛️',
        'WIND': '💨',
        'OFFSHORE': '🌊',
        'SOLAR': '☀️',
        'BIOMASS': '🌱',
        'HYDRO': '💧',
        'NPSHYD': '💧',  # Pumped storage hydro
        'COAL': '⛏️',
        'OIL': '🛢️',
        'PS': '🔋',  # Pumped storage
        'OTHER': '⚡'
    }
    
    # Find matching emoji
    emoji = '⚡'  # Default
    for key, em in emoji_map.items():
        if key in fuel.upper():
            emoji = em
            break
    
    fuel_rows.append([f"{emoji} {fuel}", f"{gw:.1f} GW", ""])

print(f"✅ Formatted {len(fuel_rows)} fuel rows")
print("\n📊 FUEL BREAKDOWN:")
for row in fuel_rows:
    print(f"   {row[0]:30s} {row[1]}")

# ====================
# 2. GET INTERCONNECTOR DATA (from Live_Raw_Interconnectors sheet)
# ====================
print("\n🌍 Step 2: Reading interconnector data from Live_Raw_Interconnectors...")

ic_result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Interconnectors!A2:C20'
).execute()

ic_vals = ic_result.get('values', [])
print(f"✅ Found {len(ic_vals)} interconnector rows")

# Format interconnector data (flags already in source data)
ic_rows = []
for row in ic_vals:
    if len(row) >= 3:
        ic_name = row[0]
        mw = row[1]
        direction = row[2]
        
        # Skip total row
        if 'TOTAL' in ic_name.upper():
            continue
        
        # Use as-is (flags already present in Live_Raw_Interconnectors)
        ic_rows.append([ic_name, f"{mw} MW {direction}", ""])

print(f"✅ Formatted {len(ic_rows)} interconnectors")
print("\n🌍 INTERCONNECTORS:")
for row in ic_rows[:5]:
    print(f"   {row[0]:35s} {row[1]}")

# ====================
# 3. COMBINE FUEL + INTERCONNECTOR DATA
# ====================
print("\n🔨 Step 3: Building combined layout...")

# Pad rows to same length
max_rows = max(len(fuel_rows), len(ic_rows))

while len(fuel_rows) < max_rows:
    fuel_rows.append(['', '', ''])
while len(ic_rows) < max_rows:
    ic_rows.append(['', '', ''])

# Combine side by side: [Fuel Col A, Fuel Col B, Fuel Col C, IC Col D, IC Col E, IC Col F]
combined_data = []
for fuel_row, ic_row in zip(fuel_rows, ic_rows):
    combined_data.append(fuel_row + ic_row)

print(f"✅ Created {len(combined_data)} combined rows")

# ====================
# 4. WRITE TO DASHBOARD
# ====================
print(f"\n✍️  Step 4: Writing to Dashboard rows 8-{7 + len(combined_data)} ...")

# First, clear old data
sheets.values().clear(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A8:F30'
).execute()

# Write new data
sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A8',
    valueInputOption='USER_ENTERED',
    body={'values': combined_data}
).execute()

print("\n" + "=" * 80)
print("✅ DASHBOARD FIXED - CLEAN FUEL BREAKDOWN!")
print("=" * 80)
print(f"\n✅ {len(fuel_rows)} fuel types (interconnectors EXCLUDED)")
print(f"✅ {len(ic_rows)} interconnectors (in separate column)")
print("\n📊 Fuel section now shows ONLY actual generation sources")
print("🌍 Interconnectors are in their own column with country flags")
