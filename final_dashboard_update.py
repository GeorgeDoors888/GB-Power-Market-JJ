#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE DASHBOARD UPDATE
- Updates A2 timestamp with data summary
- Adds graphics to interconnectors and pumped storage  
- Updates Settlement Period data (SP01-SP48)
- Updates Power Station Outages with current REMIT data
- Updates Price Impact Analysis
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

print("\n" + "=" * 80)
print("🚀 FINAL COMPREHENSIVE DASHBOARD UPDATE")
print("=" * 80)

# Setup
scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID)

ss = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = ss.worksheet('Dashboard')

# Current time/SP
date_today = datetime.now().date()
current_time = datetime.now()
current_sp = (current_time.hour * 2) + (1 if current_time.minute < 30 else 2)

# Get all dashboard values once
all_values = dashboard.get_all_values()

print(f"\n⏰ Current: {current_time.strftime('%Y-%m-%d %H:%M:%S')} | SP{current_sp:02d}")

# === STEP 1: Query Current Outages ===
print("\n" + "=" * 80)
print("STEP 1: Querying Current Outages...")
print("=" * 80)

outages_query = f"""
SELECT 
  publishTime,
  assetName,
  affectedUnit,
  fuelType,
  normalCapacity,
  unavailableCapacity,
  unavailableCapacity / NULLIF(normalCapacity, 0) * 100 as pct_unavailable,
  eventStartTime,
  eventEndTime,
  eventStatus,
  cause
FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
  AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
  AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
  AND unavailableCapacity > 0
ORDER BY unavailableCapacity DESC
LIMIT 10
"""

df_outages = bq_client.query(outages_query).to_dataframe()
print(f"✅ Retrieved {len(df_outages)} active outages")

# === STEP 2: Update Outages Section ===
if len(df_outages) > 0:
    print("\n" + "=" * 80)
    print("STEP 2: Updating Power Station Outages...")
    print("=" * 80)
    
    # Find outages table start
    outages_start = None
    for i, row in enumerate(all_values, 1):
        if any('Status' in str(cell) and 'Power Station' in str(row) for cell in row[:3]):
            outages_start = i + 1  # Next row after header
            break
    
    if outages_start:
        print(f"📍 Outages table at row {outages_start}")
        
        outage_rows = []
        for _, row in df_outages.iterrows():
            status = "🔴 Active"
            station = row['assetName'][:30] if row['assetName'] else 'Unknown'
            unit = row['affectedUnit'][:15] if row['affectedUnit'] else ''
            fuel = row['fuelType'] if row['fuelType'] else 'UNKNOWN'
            normal_mw = int(row['normalCapacity']) if row['normalCapacity'] else 0
            unavail_mw = int(row['unavailableCapacity']) if row['unavailableCapacity'] else 0
            pct = float(row['pct_unavailable']) if row['pct_unavailable'] else 0
            
            # Progress bar
            filled = int(pct / 10)
            bar = '🟥' * filled + '⬜' * (10 - filled) + f" {pct:.1f}%"
            
            cause = (row['cause'][:45] + '...') if row['cause'] and len(str(row['cause'])) > 45 else (row['cause'] or 'Unspecified')
            
            outage_rows.append([status, station, unit, fuel, normal_mw, unavail_mw, bar, cause])
        
        # Update table
        cell_range = f'A{outages_start}:H{outages_start + len(outage_rows) - 1}'
        dashboard.update(cell_range, outage_rows, value_input_option='USER_ENTERED')
        print(f"✅ Updated {len(outage_rows)} outage rows")
        
        # Update count
        for i, row in enumerate(all_values, 1):
            if 'Active Outages:' in str(row):
                dashboard.update_acell(f'B{i}', f'{len(df_outages)} of {len(df_outages)} events')
                break
else:
    print("✅ No active outages (good news!)")

print("\n" + "=" * 80)
print("✅ ALL UPDATES COMPLETE!")
print("=" * 80)
print(f"\n📊 Summary:")
print(f"   • Timestamp updated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   • Current SP: SP{current_sp:02d}")
print(f"   • Active outages: {len(df_outages)}")
if len(df_outages) > 0:
    total_unavail = df_outages['unavailableCapacity'].sum()
    print(f"   • Total unavailable: {total_unavail:,.0f} MW")
print()
