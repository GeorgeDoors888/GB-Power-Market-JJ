#!/usr/bin/env python3
"""
Resize Dropdowns sheet and populate missing data
"""

from googleapiclient.discovery import build
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDS_FILE = "inner-cinema-credentials.json"

# Initialize clients
bq_client = bigquery.Client(project=PROJECT_ID, location="US")
sheets_creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets_service = build('sheets', 'v4', credentials=sheets_creds)
gc = gspread.authorize(sheets_creds)
wb = gc.open_by_key(SPREADSHEET_ID)

print("🔧 Resizing Dropdowns sheet...")

# Get Dropdowns sheet
try:
    dropdown_sheet = wb.worksheet('Dropdowns')
    sheet_id = dropdown_sheet.id
    
    # Resize to accommodate more columns
    resize_request = {
        'requests': [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'rowCount': 3000,
                        'columnCount': 15  # Increase from 11 to 15
                    }
                },
                'fields': 'gridProperties(rowCount,columnCount)'
            }
        }]
    }
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=resize_request
    ).execute()
    
    print("   ✅ Resized to 3000 rows x 15 columns")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Now populate data
print("\n📊 Populating missing dropdown data...")

# Define data
capacity_ranges = [
    'None', 'All',
    'Micro (<1 MW)',
    'Small (1-10 MW)',
    'Medium (10-50 MW)',
    'Large (50-100 MW)',
    'Very Large (100-500 MW)',
    'Mega (>500 MW)'
]

print("\n🔌 Fetching Connection Sites...")
query = """
SELECT DISTINCT bmu_name
FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators`
WHERE is_active = TRUE
AND bmu_name IS NOT NULL
AND generation_capacity_mw > 10
ORDER BY bmu_name
LIMIT 100
"""
df = bq_client.query(query).to_dataframe()
connection_sites = ['None', 'All'] + df['bmu_name'].tolist()

project_status = [
    'None', 'All',
    'Active/Operational',
    'Under Construction',
    'Planned/Consented',
    'Testing/Commissioning',
    'Decommissioned',
    'On Hold',
    'Cancelled'
]

print(f"   ✅ Capacity ranges: {len(capacity_ranges)-2}")
print(f"   ✅ Connection sites: {len(connection_sites)-2}")
print(f"   ✅ Project status: {len(project_status)-2}")

# Write data
batch_data = [
    {'range': 'Dropdowns!K1', 'values': [['Capacity Ranges']]},
    {'range': f'Dropdowns!K2:K{len(capacity_ranges)+1}', 'values': [[cr] for cr in capacity_ranges]},
    {'range': 'Dropdowns!L1', 'values': [['Connection Sites']]},
    {'range': f'Dropdowns!L2:L{len(connection_sites)+1}', 'values': [[cs] for cs in connection_sites]},
    {'range': 'Dropdowns!M1', 'values': [['Project Status']]},
    {'range': f'Dropdowns!M2:M{len(project_status)+1}', 'values': [[ps] for ps in project_status]}
]

body = {'valueInputOption': 'USER_ENTERED', 'data': batch_data}
result = sheets_service.spreadsheets().values().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body=body
).execute()

print(f"\n✅ Wrote {result.get('totalUpdatedCells', 0)} cells")
print("\n✅ All search dropdown data is now complete!")
