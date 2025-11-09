#!/usr/bin/env python3
"""
Update Dashboard with Current REMIT Outages
Uses correct column names and active outage filtering
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

print("\n🔴 UPDATING POWER STATION OUTAGES (REMIT DATA)...")
print("=" * 70)

# Setup Google Sheets
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
gc = gspread.authorize(creds)

# Setup BigQuery
bq_client = bigquery.Client(project=PROJECT_ID, location='US')

ss = gc.open_by_key(SPREADSHEET_ID)
dashboard = ss.worksheet('Dashboard')

# Query CURRENT ACTIVE outages with correct column names
query = f"""
SELECT 
  assetId,
  assetName,
  fuelType,
  normalCapacity,
  unavailableCapacity,
  ROUND(100.0 * unavailableCapacity / NULLIF(normalCapacity, 0), 1) as pct_unavailable,
  eventStatus,
  eventStartTime,
  eventEndTime,
  cause
FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
  AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
  AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
  AND unavailableCapacity > 0
ORDER BY unavailableCapacity DESC
LIMIT 10
"""

print("🔍 Querying BigQuery for active outages...")
df = bq_client.query(query).to_dataframe()

print(f"\n📊 Results: {len(df)} active outages found")

if len(df) > 0:
    print("\nActive Outages:")
    for _, row in df.iterrows():
        print(f"  • {row['assetName']} ({row['fuelType']}): {row['unavailableCapacity']}/{row['normalCapacity']} MW ({row['pct_unavailable']}%)")
        print(f"    Cause: {row['cause']}")
else:
    print("  ✅ No active outages currently")

# Find Power Station Outages section
print("\n📍 Locating outages section in dashboard...")
all_values = dashboard.get_all_values()
outages_row = None

for i, row in enumerate(all_values, 1):
    if any('Power Station Outages' in str(cell) for cell in row):
        outages_row = i + 2  # Skip header row
        print(f"   Found at row {i}, data starts row {outages_row}")
        break

if not outages_row:
    print("❌ Could not find 'Power Station Outages' section")
    exit(1)

# Prepare update data
if len(df) == 0:
    # No outages - clear the section
    update_data = [
        ["No active outages", "", "", ""],
        ["", "", "", ""],
        ["", "", "", ""],
        ["", "", "", ""],
        ["", "", "", ""]
    ]
else:
    update_data = []
    for _, row in df.iterrows():
        # Create visual bar
        pct = row['pct_unavailable']
        filled = int(pct / 10)
        bar = '🟥' * filled + '⬜' * (10 - filled)
        
        # Truncate long cause text
        cause_text = row['cause'][:50] if row['cause'] else 'Unknown'
        
        update_data.append([
            int(row['normalCapacity']),
            int(row['unavailableCapacity']),
            f"{bar} {pct}%",
            cause_text
        ])
    
    # Fill remaining rows with blanks
    while len(update_data) < 5:
        update_data.append(["", "", "", ""])

# Update dashboard
print(f"\n📝 Updating dashboard rows {outages_row} to {outages_row + 4}...")
range_name = f'E{outages_row}:H{outages_row + 4}'
dashboard.update(range_name, update_data, value_input_option='USER_ENTERED')

print(f"✅ Dashboard updated successfully!")
print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Active outages: {len(df)}")

if len(df) > 0:
    total_unavailable = df['unavailableCapacity'].sum()
    print(f"   Total unavailable capacity: {total_unavailable:,.0f} MW")
