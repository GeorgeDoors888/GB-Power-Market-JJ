#!/usr/bin/env python3
"""
Update Unit Names dropdown with descriptive format: BMU_ID (Lead Party Name)
This makes it searchable and meaningful
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'

print("📊 Fetching BMU IDs with Lead Party names...\n")

bq = bigquery.Client(project=PROJECT_ID, location='US')

# Get BMU IDs with their lead party names from dim_bmu
query = """
SELECT DISTINCT
    bm_unit_id,
    lead_party_name,
    fuel_type,
    is_battery_storage,
    is_vlp
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_bmu`
WHERE bm_unit_id IS NOT NULL
  AND lead_party_name IS NOT NULL
ORDER BY bm_unit_id
"""
df = bq.query(query).to_dataframe()

print(f"✅ Found {len(df)} BMU units with lead party info")

# Create formatted unit names: "T_DRAXX-1 (Drax Power Limited)"
unit_names = ['All']
for _, row in df.iterrows():
    bmu_id = row['bm_unit_id']
    party = row['lead_party_name']

    # Add context tags for batteries and VLPs
    tags = []
    if row['is_battery_storage']:
        tags.append('Battery')
    if row['is_vlp']:
        tags.append('VLP')

    if tags:
        formatted = f"{bmu_id} ({party} - {', '.join(tags)})"
    else:
        formatted = f"{bmu_id} ({party})"

    unit_names.append(formatted)

print(f"✅ Created {len(unit_names)-1} formatted unit names")
print("\n📋 Sample formatted names:")
for name in unit_names[1:21]:
    print(f"   {name}")

# Update DropdownData sheet
print("\n📝 Updating DropdownData sheet column C (Unit Names)...\n")

creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
service = build('sheets', 'v4', credentials=creds)

# Prepare data
unit_names_data = [['Unit Names']] + [[name] for name in unit_names]

# Write to column C
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=f'DropdownData!C1:C{len(unit_names_data)}',
    valueInputOption='RAW',
    body={'values': unit_names_data}
).execute()

print(f"✅ Updated DropdownData sheet with {len(unit_names)} unit names")
print("\n✅ COMPLETE - Unit Names dropdown now shows:")
print("   Format: BMU_ID (Lead Party Name)")
print("   Example: FFSEN005 (F & S Energy Ltd)")
print("   Example: T_DRAXX-1 (Drax Power Limited)")
print("\n🎯 Dropdown is now searchable by BMU ID or company name!")
