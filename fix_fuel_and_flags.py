#!/usr/bin/env python3
"""
FIX DASHBOARD: Add country flags to interconnectors AND populate fuel breakdown
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, date

# Configuration
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Auth
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()
bq_client = bigquery.Client(project=PROJECT_ID, location='US', credentials=CREDS)

# Country flag mapping
IC_FLAGS = {
    "ElecLink": "🇫🇷",
    "IFA": "🇫🇷",
    "IFA2": "🇫🇷",
    "East-West": "🇮🇪",
    "Greenlink": "🇮🇪",
    "Moyle": "🇮🇪",
    "BritNed": "🇳🇱",
    "Nemo": "🇧🇪",
    "NSL": "🇳🇴",
    "Viking Link": "🇩🇰"
}

print("🔧 FIXING DASHBOARD...")
print("=" * 80)

# ====================
# 1. GET FUEL BREAKDOWN FROM BIGQUERY
# ====================
print("\n📊 Step 1: Querying fuel breakdown from BigQuery...")

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
GROUP BY ld.fuelType
ORDER BY total_generation_mw DESC
"""

df_fuel = bq_client.query(fuel_query).to_dataframe()

print(f"✅ Found {len(df_fuel)} fuel types")

# Format fuel data
fuel_rows = []
for _, row in df_fuel.iterrows():
    fuel = row['fuelType']
    mw = row['total_generation_mw']
    gw = mw / 1000.0
    
    # Fuel type emoji mapping
    emoji = {
        'CCGT': '🔥', 'OCGT': '🔥', 'GAS': '🔥',
        'NUCLEAR': '⚛️',
        'WIND': '💨', 'OFFSHORE': '🌊',
        'SOLAR': '☀️',
        'BIOMASS': '🌱',
        'HYDRO': '💧',
        'COAL': '⛏️',
        'OIL': '🛢️',
        'STORAGE': '🔋',
        'OTHER': '⚡'
    }.get(fuel.upper(), '⚡')
    
    fuel_rows.append([f"{emoji} {fuel}", f"{gw:.1f} GW", ""])

print(f"✅ Formatted {len(fuel_rows)} fuel rows")

# ====================
# 2. GET INTERCONNECTOR DATA WITH FLAGS
# ====================
print("\n🌍 Step 2: Reading interconnector data...")

ic_result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Interconnectors!A2:C20'
).execute()

ic_vals = ic_result.get('values', [])
print(f"✅ Found {len(ic_vals)} interconnector rows")

# Format interconnector data WITH FLAGS (only if not already present)
ic_rows = []
for row in ic_vals:
    if len(row) >= 3:
        ic_name = row[0]
        mw = row[1]
        direction = row[2]
        
        # Skip total row
        if 'TOTAL' in ic_name.upper():
            continue
        
        # Check if flag emoji already exists in name
        has_flag = any(char in ic_name for char in ['🇫', '🇬', '🇮', '🇳', '🇧', '🇩'])
        
        if has_flag:
            # Flag already present, use as-is
            formatted = ic_name
        else:
            # Add flag
            flag = ""
            for key, flag_emoji in IC_FLAGS.items():
                if key in ic_name:
                    flag = flag_emoji
                    break
            formatted = f"{flag} {ic_name}" if flag else ic_name
        
        ic_rows.append([formatted, f"{mw} MW {direction}", ""])

print(f"✅ Formatted {len(ic_rows)} interconnectors with flags")

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

# Combine side by side
combined_data = []
for fuel_row, ic_row in zip(fuel_rows, ic_rows):
    combined_data.append(fuel_row + ic_row)

print(f"✅ Created {len(combined_data)} combined rows")

# ====================
# 4. WRITE TO DASHBOARD
# ====================
print("\n✍️  Step 4: Writing to Dashboard rows 8-{} ...".format(7 + len(combined_data)))

sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A8',
    valueInputOption='USER_ENTERED',
    body={'values': combined_data}
).execute()

print("\n" + "=" * 80)
print("✅ DASHBOARD FIXED!")
print("=" * 80)
print("\n📊 FUEL BREAKDOWN:")
for i, row in enumerate(fuel_rows[:5], 1):
    if row[0]:
        print(f"  {i}. {row[0]:<30} {row[1]}")

print("\n🌍 INTERCONNECTORS:")
for i, row in enumerate(ic_rows[:5], 1):
    if row[0]:
        print(f"  {i}. {row[0]:<35} {row[1]}")

print("\n✅ Both fuel data and country flags are now live!")
