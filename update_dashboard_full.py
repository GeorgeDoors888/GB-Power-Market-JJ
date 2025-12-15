#!/usr/bin/env python3
"""
Update Dashboard with current data and graphics
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime, timedelta
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

print("\n🔍 Reading current Dashboard structure...")

# Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

# BigQuery
bq_client = bigquery.Client(project=PROJECT_ID)

# Open spreadsheet
ss = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = ss.worksheet('Dashboard')

# Read current A1 and A2
a1_value = dashboard.acell('A1').value
a2_value = dashboard.acell('A2').value

print(f"Current A1: {a1_value}")
print(f"Current A2: {a2_value}")
print()

# Get current settlement period and data stats
date_today = datetime.now().date()
current_hour = datetime.now().hour
current_minute = datetime.now().minute
current_sp = (current_hour * 2) + (1 if current_minute < 30 else 2)

print(f"📊 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📊 Current Settlement Period: SP{current_sp:02d}")
print()

# Query data statistics
query = f"""
WITH today_data AS (
  SELECT COUNT(*) as row_count
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
),
hourly_rate AS (
  SELECT 
    COUNT(*) / GREATEST(1, DATE_DIFF(CURRENT_TIMESTAMP(), TIMESTAMP(CURRENT_DATE()), HOUR)) as rows_per_hour
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
)
SELECT 
  (SELECT row_count FROM today_data) as total_rows_today,
  (SELECT rows_per_hour FROM hourly_rate) as avg_rows_per_hour
"""

df = bq_client.query(query).to_dataframe()
total_rows = int(df['total_rows_today'].iloc[0])
rows_per_hour = int(df['avg_rows_per_hour'].iloc[0])

print(f"📊 Total data rows today: {total_rows:,}")
print(f"📊 Average rows per hour: {rows_per_hour:,}")
print()

# Create new A2 value
new_a2 = f'⏰ Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Settlement Period {current_sp:02d} | Total Data: {total_rows:,} rows | Rate: ~{rows_per_hour:,} rows/hr'

print(f"✅ New A2 value:")
print(f"   {new_a2}")
print()

# Update A2
dashboard.update_acell('A2', new_a2)
print("✅ Updated A2 cell")

# Find sections to update
all_values = dashboard.get_all_values()

pumped_storage_row = None
interconnector_rows = {}
sp_data_row = None
outages_row = None

for i, row in enumerate(all_values, 1):
    row_text = ' '.join(str(cell) for cell in row).lower()
    
    if 'pumped storage' in row_text and not pumped_storage_row:
        pumped_storage_row = i
        print(f"📍 Found Pumped Storage at row {i}")
    
    if 'settlement period data' in row_text and not sp_data_row:
        sp_data_row = i
        print(f"📍 Found Settlement Period Data at row {i}")
    
    if 'power station outages' in row_text and not outages_row:
        outages_row = i
        print(f"📍 Found Power Station Outages at row {i}")
    
    # Find interconnector rows
    if 'ifa' in row_text and 'france' in row_text:
        interconnector_rows['IFA'] = i
    if 'ifa2' in row_text:
        interconnector_rows['IFA2'] = i
    if 'eleclink' in row_text:
        interconnector_rows['ElecLink'] = i
    if 'nemo' in row_text and 'belgium' in row_text:
        interconnector_rows['Nemo'] = i
    if 'viking' in row_text and 'denmark' in row_text:
        interconnector_rows['Viking'] = i
    if 'moyle' in row_text:
        interconnector_rows['Moyle'] = i
    if 'east-west' in row_text and 'ireland' in row_text:
        interconnector_rows['EastWest'] = i
    if 'greenlink' in row_text:
        interconnector_rows['Greenlink'] = i

print(f"\n📍 Found {len(interconnector_rows)} interconnector rows")
for name, row in interconnector_rows.items():
    print(f"   {name}: row {row}")

print("\n✅ Dashboard structure analyzed")
print(f"\n💡 Next steps:")
print(f"   1. Add graphics to Pumped Storage (row {pumped_storage_row})")
print(f"   2. Add graphics to interconnectors")
print(f"   3. Update Settlement Period Data (starting row {sp_data_row})")
print(f"   4. Update Power Station Outages (starting row {outages_row})")
