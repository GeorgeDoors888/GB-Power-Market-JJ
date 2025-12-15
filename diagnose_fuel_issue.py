#!/usr/bin/env python3
"""
Diagnose and fix fuel breakdown issues:
1. Remove interconnector entries from fuel section
2. Show actual generation fuel types only
3. Fix flags on interconnectors
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

print("🔍 DIAGNOSING FUEL BREAKDOWN ISSUE...")
print("=" * 80)

# Query fuel data
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

print(f"\n📊 RAW FUEL DATA FROM BIGQUERY ({len(df_fuel)} rows):")
print("=" * 80)
print(df_fuel.to_string())

print("\n\n🔍 ANALYSIS:")
print("=" * 80)

# Separate actual generation from interconnectors
actual_fuel = []
interconnector_entries = []
negative_entries = []

for _, row in df_fuel.iterrows():
    fuel = row['fuelType']
    mw = row['total_generation_mw']
    
    if fuel.startswith('INT'):
        interconnector_entries.append((fuel, mw))
    elif mw < 0:
        negative_entries.append((fuel, mw))
    else:
        actual_fuel.append((fuel, mw))

print(f"\n✅ ACTUAL FUEL TYPES ({len(actual_fuel)}):")
for fuel, mw in actual_fuel[:10]:
    print(f"   {fuel:20s} {mw:10.1f} MW")

print(f"\n❌ INTERCONNECTOR ENTRIES (should NOT be in fuel section) ({len(interconnector_entries)}):")
for fuel, mw in interconnector_entries[:10]:
    print(f"   {fuel:20s} {mw:10.1f} MW")

print(f"\n❌ NEGATIVE VALUES ({len(negative_entries)}):")
for fuel, mw in negative_entries[:10]:
    print(f"   {fuel:20s} {mw:10.1f} MW")

print("\n\n💡 SOLUTION:")
print("=" * 80)
print("1. FILTER OUT fuel types starting with 'INT' (interconnectors)")
print("2. ONLY show fuel types with positive generation > 0")
print("3. Keep interconnectors ONLY in the interconnector column")
