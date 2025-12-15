#!/usr/bin/env python3
"""
Diagnose Dashboard display issues:
1. Check if flags are actually in the sheet
2. Check if all fuel types are showing
3. Explain data freshness indicator
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

print("🔍 DIAGNOSING DASHBOARD DISPLAY...")
print("=" * 100)

# Check what's actually in the Dashboard
result = sheets.values().get(spreadsheetId=SHEET_ID, range='Dashboard!A1:F20').execute()
vals = result.get('values', [])

print("\n📊 CURRENT DASHBOARD CONTENT (Rows 1-20):")
print("=" * 100)

for i, row in enumerate(vals, start=1):
    cols = row + [''] * (6 - len(row))
    print(f"Row {i:2d}: A='{cols[0][:40]}...' | B='{cols[1][:15]}' | C='{cols[2][:10]}' | D='{cols[3][:40]}...' | E='{cols[4][:20]}'")

print("\n" + "=" * 100)

# Check what fuel types we're getting from BigQuery
from google.cloud import bigquery
from datetime import date

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
bq_client = bigquery.Client(project=PROJECT_ID, location='US', credentials=CREDS)

today = date.today().strftime('%Y-%m-%d')

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
GROUP BY ld.fuelType
ORDER BY total_generation_mw DESC
"""

print("\n📊 ALL FUEL TYPES FROM BIGQUERY (including interconnectors):")
print("=" * 100)

df = bq_client.query(fuel_query).to_dataframe()
for _, row in df.iterrows():
    fuel = row['fuelType']
    mw = row['total_generation_mw']
    is_ic = "🔌 INTERCONNECTOR" if fuel.startswith('INT') else "⚡ FUEL"
    print(f"{fuel:20s} {mw:10.1f} MW  {is_ic}")

print("\n" + "=" * 100)
print("\n❓ QUESTIONS:")
print("1. Are you seeing the country flags in Column D (Interconnectors)?")
print("2. Are you seeing pumped hydro (NPSHYD) in Column A (Fuel Breakdown)?")
print("3. What exactly are you seeing in your Google Sheets view?")

print("\n\n💡 DATA FRESHNESS INDICATOR EXPLAINED:")
print("=" * 100)
print("Location: Dashboard Row 3")
print("Purpose: Shows how old the data is")
print()
print("The indicator legend means:")
print("  ✅ <10min    = Data is FRESH (updated within last 10 minutes)")
print("  ⚠️ 10-60min  = Data is STALE (10-60 minutes old, might want to refresh)")
print("  🔴 >60min    = Data is OLD (over 1 hour old, definitely needs refresh)")
print()
print("The actual freshness status appears in Row 2, like:")
print("  '⏰ Last Updated: 2025-11-10 12:44:34 | ✅ FRESH'")
print()
print("This helps you know if you're looking at real-time data or old data.")
print("If you see 🔴 OLD, you should refresh the Dashboard.")
print("=" * 100)
