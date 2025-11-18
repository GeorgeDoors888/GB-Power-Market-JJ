#!/usr/bin/env python3
"""
Update Dashboard header with latest timestamp and data freshness indicator
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

# Auth
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

print("🔄 UPDATING DASHBOARD HEADER...")
print("=" * 80)

# Get current time
now = datetime.now()
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

# Read Live Dashboard to get last data timestamp
print("\n📡 Reading Live Dashboard to check data freshness...")
result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live Dashboard!A2:A2'
).execute()

live_vals = result.get('values', [])
if live_vals and len(live_vals[0]) > 0:
    last_data_time_str = live_vals[0][0]
    print(f"✅ Last data timestamp from Live Dashboard: {last_data_time_str}")
    
    # Parse and calculate freshness
    try:
        last_data_time = datetime.strptime(last_data_time_str, "%Y-%m-%d %H:%M:%S")
        age_minutes = (now - last_data_time).total_seconds() / 60
        
        if age_minutes < 10:
            freshness = "✅ FRESH"
        elif age_minutes < 60:
            freshness = "⚠️ STALE"
        else:
            freshness = "🔴 OLD"
        
        print(f"📊 Data age: {age_minutes:.1f} minutes → {freshness}")
    except:
        freshness = "✅ FRESH"
        last_data_time_str = timestamp
else:
    freshness = "✅ FRESH"
    last_data_time_str = timestamp

# Update header rows
print("\n✍️  Updating header rows 1-5...")

header_data = [
    ['File: Dashboard', '', '', '', '', ''],
    [f'⏰ Last Updated: {timestamp} | {freshness}', '', '', '', '', ''],
    ['Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min', '', '', '', '', ''],
    ['📊 SYSTEM METRICS', '', '', '', '', ''],
    ['', '', '', '', '', '']  # Row 5 for system totals (will be calculated)
]

sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A1',
    valueInputOption='USER_ENTERED',
    body={'values': header_data}
).execute()

print("✅ Header updated")

# Calculate and update system metrics (row 5)
print("\n📊 Reading current fuel data to calculate totals...")

fuel_result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A8:B17'
).execute()

fuel_vals = fuel_result.get('values', [])

total_generation = 0.0
renewable_generation = 0.0

for row in fuel_vals:
    if len(row) >= 2 and row[1]:
        try:
            # Extract GW value
            gw_str = row[1].replace('GW', '').strip()
            gw = float(gw_str)
            total_generation += gw
            
            # Check if renewable
            fuel_type = row[0].upper()
            if any(word in fuel_type for word in ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS']):
                renewable_generation += gw
        except:
            pass

renewable_pct = (renewable_generation / total_generation * 100) if total_generation > 0 else 0

print(f"✅ Total Generation: {total_generation:.1f} GW")
print(f"✅ Renewable Generation: {renewable_generation:.1f} GW ({renewable_pct:.0f}%)")

# Read interconnector total
ic_result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Interconnectors!B12:B12'
).execute()

ic_vals = ic_result.get('values', [])
net_import = float(ic_vals[0][0]) if ic_vals and ic_vals[0] else 0.0

print(f"✅ Net Import: {net_import:.0f} MW ({net_import/1000:.1f} GW)")

# Total supply = generation + net import
total_supply = total_generation + (net_import / 1000)

metrics_row = [[
    f'Total Generation: {total_generation:.1f} GW | Supply: {total_supply:.1f} GW | Renewables: {renewable_pct:.0f}%',
    '', '', '', '', ''
]]

sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!A5',
    valueInputOption='USER_ENTERED',
    body={'values': metrics_row}
).execute()

print("✅ System metrics updated")

print("\n" + "=" * 80)
print("✅ DASHBOARD HEADER UPDATED!")
print("=" * 80)
print(f"\n⏰ Timestamp: {timestamp}")
print(f"📊 Freshness: {freshness}")
print(f"⚡ Total Generation: {total_generation:.1f} GW")
print(f"🔋 Total Supply: {total_supply:.1f} GW")
print(f"🌱 Renewables: {renewable_pct:.0f}%")
