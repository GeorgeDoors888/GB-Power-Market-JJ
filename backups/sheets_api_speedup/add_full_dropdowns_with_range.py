#!/usr/bin/env python3
"""
Add comprehensive dropdowns using "List from a range" method
This bypasses the 500-item limit by storing values in a hidden reference sheet
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
ANALYSIS_SHEET_ID = 225925794
PROJECT_ID = 'inner-cinema-476211-u9'

print("📊 Fetching ALL data from BigQuery...\n")

bq = bigquery.Client(project=PROJECT_ID, location='US')

# Get ALL BMU IDs
query_bmus = """
SELECT DISTINCT bmUnit as bmu_id
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE settlementDate >= '2025-11-01'
  AND bmUnit IS NOT NULL
ORDER BY bmUnit
"""
df_bmus = bq.query(query_bmus).to_dataframe()
bmu_ids = ['All'] + df_bmus['bmu_id'].tolist()
print(f"✅ BMU IDs: {len(bmu_ids)-1}")

# Get all Lead Parties
lead_parties_set = sorted(set(bmu[:4] for bmu in df_bmus['bmu_id'] if len(bmu) >= 4))
lead_parties = ['All'] + lead_parties_set
print(f"✅ Lead Parties: {len(lead_parties)-1}")

# Get all Generation Types
query_fuels = """
SELECT DISTINCT fuelType
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE fuelType IS NOT NULL
  AND fuelType NOT LIKE 'INT%'
ORDER BY fuelType
"""
df_fuels = bq.query(query_fuels).to_dataframe()
generation_types = ['All'] + df_fuels['fuelType'].tolist()
print(f"✅ Generation Types: {len(generation_types)-1}")

party_roles = ['All', 'Generator', 'Supplier', 'Trader', 'Interconnector', 'Storage']

creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
service = build('sheets', 'v4', credentials=creds)

print("\n🔧 Creating/updating DropdownData sheet...\n")

# Check if DropdownData sheet exists, create if not
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
dropdown_sheet_id = None
for sheet in sheet_metadata['sheets']:
    if sheet['properties']['title'] == 'DropdownData':
        dropdown_sheet_id = sheet['properties']['sheetId']
        print(f"✅ Found existing DropdownData sheet (ID: {dropdown_sheet_id})")
        break

if not dropdown_sheet_id:
    print("📝 Creating new DropdownData sheet...")
    request = {
        'addSheet': {
            'properties': {
                'title': 'DropdownData',
                'hidden': True,
                'gridProperties': {'rowCount': 2000, 'columnCount': 5}
            }
        }
    }
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [request]}
    ).execute()
    dropdown_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
    print(f"✅ Created DropdownData sheet (ID: {dropdown_sheet_id})")

# Write data to DropdownData sheet
print("\n📝 Writing dropdown data to DropdownData sheet...")

# Prepare data in columns
max_rows = max(len(party_roles), len(bmu_ids), len(generation_types), len(lead_parties))
data = []
for i in range(max_rows):
    row = [
        party_roles[i] if i < len(party_roles) else '',
        bmu_ids[i] if i < len(bmu_ids) else '',
        bmu_ids[i] if i < len(bmu_ids) else '',  # Unit Names = BMU IDs
        generation_types[i] if i < len(generation_types) else '',
        lead_parties[i] if i < len(lead_parties) else ''
    ]
    data.append(row)

# Add headers
headers = [['Party Roles', 'BMU IDs', 'Unit Names', 'Generation Types', 'Lead Parties']]
all_data = headers + data

service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='DropdownData!A1:E' + str(len(all_data)),
    valueInputOption='RAW',
    body={'values': all_data}
).execute()

print(f"✅ Data written to DropdownData sheet ({len(all_data)} rows)")

# Create dropdowns using range references
print("\n🔧 Creating dropdowns in Analysis sheet...\n")

requests = [
    # B5: Party Role
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 4, 'endRowIndex': 5,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!A2:A{len(party_roles)+1}'
                    }]
                },
                'showCustomUi': True,
                'strict': True
            }
        }
    },
    # B6: BMU IDs
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 5, 'endRowIndex': 6,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!B2:B{len(bmu_ids)+1}'
                    }]
                },
                'showCustomUi': True,
                'strict': False
            }
        }
    },
    # B7: Unit Names
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 6, 'endRowIndex': 7,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!C2:C{len(bmu_ids)+1}'
                    }]
                },
                'showCustomUi': True,
                'strict': False
            }
        }
    },
    # B8: Generation Type
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 7, 'endRowIndex': 8,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!D2:D{len(generation_types)+1}'
                    }]
                },
                'showCustomUi': True,
                'strict': True
            }
        }
    },
    # B9: Lead Party
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 8, 'endRowIndex': 9,
                'startColumnIndex': 1, 'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!E2:E{len(lead_parties)+1}'
                    }]
                },
                'showCustomUi': True,
                'strict': False
            }
        }
    }
]

service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()

print("✅ Dropdowns created using range references")

# Set defaults
print("📝 Setting defaults to 'All'...")
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Analysis!B5:B9',
    valueInputOption='RAW',
    body={'values': [['All'], ['All'], ['All'], ['All'], ['All']]}
).execute()

print("\n✅ COMPLETE - Full dropdowns added:")
print(f"   B5: Party Role ({len(party_roles)-1} options)")
print(f"   B6: BMU IDs ({len(bmu_ids)-1} options)")
print(f"   B7: Unit Names ({len(bmu_ids)-1} options)")
print(f"   B8: Generation Type ({len(generation_types)-1} options)")
print(f"   B9: Lead Party ({len(lead_parties)-1} options)")
print("\n📝 Data stored in hidden 'DropdownData' sheet")
print("🎯 Open Google Sheets - all dropdowns now have complete lists!")
