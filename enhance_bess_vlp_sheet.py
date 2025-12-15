#!/usr/bin/env python3
"""
Enhanced BESS_VLP sheet with:
- Hidden reference table
- DNO dropdown selector
- Google Maps integration
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import pandas as pd

# Initialize clients
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery'
]
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
bq_client = bigquery.Client(project='inner-cinema-476211-u9', location='US', credentials=creds)

print("🔋 Enhancing BESS_VLP Sheet")
print("=" * 60)

# Get or create sheet
try:
    sheet = spreadsheet.worksheet('BESS_VLP')
    print("✅ BESS_VLP sheet found, will update it")
except:
    sheet = spreadsheet.add_worksheet(title='BESS_VLP', rows=100, cols=10)
    print("✅ Created new BESS_VLP sheet")

print("\n📊 Setting up enhanced structure...")

# Prepare all updates in batch format
updates = [
    # Row 1-2: Title
    {'range': 'A1', 'values': [['BESS VLP - DNO Lookup Tool']]},
    {'range': 'A2', 'values': [['Enter postcode OR select DNO ID to find Distribution Network Operator']]},
    
    # Row 4: Postcode input
    {'range': 'A4', 'values': [['Postcode:']]},
    {'range': 'B4', 'values': [['ENTER POSTCODE']]},
    
    # Row 4: DNO dropdown (column D-E)
    {'range': 'D4', 'values': [['OR Select DNO:']]},
    {'range': 'E4', 'values': [['Select DNO ID...']]},
    
    # Row 5: Instruction
    {'range': 'A5', 'values': [['↓ Use menu: 🔋 BESS VLP Tools → Lookup']]},
    
    # Row 7: Results header
    {'range': 'A7', 'values': [['DNO INFORMATION:']]},
    
    # Row 9: Column headers for DNO data
    {'range': 'A9:H9', 'values': [[
        'MPAN/Distributor ID',
        'DNO Key',
        'DNO Name',
        'DNO Short Code',
        'Market Participant ID',
        'GSP Group ID',
        'GSP Group Name',
        'Coverage Area'
    ]]},
    
    # Row 13-15: Location info
    {'range': 'A13', 'values': [['SITE LOCATION:']]},
    {'range': 'A14', 'values': [['Latitude:']]},
    {'range': 'A15', 'values': [['Longitude:']]},
    
    # Row 17: Map header
    {'range': 'A17', 'values': [['LOCATION MAP:']]},
    {'range': 'A18', 'values': [['Map will appear below after lookup']]},
    
    # Row 21: Hidden reference table header
    {'range': 'A21', 'values': [['ALL UK DNO REFERENCE DATA (HIDDEN):']]},
    
    # Row 23: Reference table headers
    {'range': 'A23:H23', 'values': [[
        'MPAN',
        'DNO Key',
        'DNO Name',
        'Short Code',
        'Participant ID',
        'GSP Group',
        'GSP Name',
        'Coverage'
    ]]},
]

# Apply all header/structure updates at once
sheet.batch_update(updates)
print("✅ Sheet structure created")

# Fetch DNO reference data from BigQuery
print("\n📡 Fetching DNO reference data from BigQuery...")

query = """
SELECT 
    mpan_distributor_id,
    dno_key,
    dno_name,
    dno_short_code,
    market_participant_id,
    gsp_group_id,
    gsp_group_name,
    primary_coverage_area
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
ORDER BY mpan_distributor_id
"""

df = bq_client.query(query).to_dataframe()

# Prepare data for batch update
dno_data = []
for _, row in df.iterrows():
    dno_data.append([
        int(row['mpan_distributor_id']),
        row['dno_key'],
        row['dno_name'],
        row['dno_short_code'] if row['dno_short_code'] else '',
        row['market_participant_id'] if row['market_participant_id'] else '',
        row['gsp_group_id'],
        row['gsp_group_name'],
        row['primary_coverage_area'][:50] if row['primary_coverage_area'] else ''
    ])

# Update reference table (will be hidden)
if dno_data:
    range_name = f'A24:H{23 + len(dno_data)}'
    sheet.update(values=dno_data, range_name=range_name, value_input_option='USER_ENTERED')
    print(f"✅ Populated {len(dno_data)} DNO records")

# Format the sheet
print("\n🎨 Applying formatting...")

# Format title
sheet.format('A1:H1', {
    'textFormat': {'bold': True, 'fontSize': 14},
    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
    'horizontalAlignment': 'LEFT'
})

# Format section headers
for row in [7, 13, 17, 21]:
    sheet.format(f'A{row}:H{row}', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })

# Format column headers
sheet.format('A9:H9', {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
})

sheet.format('A23:H23', {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
})

# Format input cells
sheet.format('B4', {
    'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.8},
    'textFormat': {'bold': True}
})

sheet.format('E4', {
    'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 1},
    'textFormat': {'bold': True}
})

# Set column widths
requests = [
    {
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet.id,
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': 1
            },
            'properties': {'pixelSize': 180},
            'fields': 'pixelSize'
        }
    },
    {
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet.id,
                'dimension': 'COLUMNS',
                'startIndex': 1,
                'endIndex': 2
            },
            'properties': {'pixelSize': 150},
            'fields': 'pixelSize'
        }
    },
    {
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet.id,
                'dimension': 'COLUMNS',
                'startIndex': 2,
                'endIndex': 3
            },
            'properties': {'pixelSize': 350},
            'fields': 'pixelSize'
        }
    },
    {
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet.id,
                'dimension': 'COLUMNS',
                'startIndex': 3,
                'endIndex': 8
            },
            'properties': {'pixelSize': 150},
            'fields': 'pixelSize'
        }
    }
]

spreadsheet.batch_update({'requests': requests})

# Hide reference table rows (21 onwards)
print("\n🔒 Hiding reference table rows...")
hide_rows_request = {
    'requests': [
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet.id,
                    'dimension': 'ROWS',
                    'startIndex': 20,  # Row 21 (0-indexed)
                    'endIndex': 50     # Hide up to row 50
                },
                'properties': {'hiddenByUser': True},
                'fields': 'hiddenByUser'
            }
        }
    ]
}
spreadsheet.batch_update(hide_rows_request)
print("✅ Reference table hidden (rows 21-50)")

# Create data validation for DNO dropdown
print("\n📋 Creating DNO dropdown list...")
dropdown_values = [[f"{int(row[0])} - {row[2]}"] for row in dno_data]

validation_request = {
    'requests': [
        {
            'setDataValidation': {
                'range': {
                    'sheetId': sheet.id,
                    'startRowIndex': 3,    # Row 4 (0-indexed)
                    'endRowIndex': 4,
                    'startColumnIndex': 4,  # Column E
                    'endColumnIndex': 5
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_LIST',
                        'values': [{'userEnteredValue': val[0]} for val in dropdown_values]
                    },
                    'showCustomUi': True,
                    'strict': True
                }
            }
        }
    ]
}
spreadsheet.batch_update(validation_request)
print("✅ DNO dropdown created in E4")

# Add instruction note
sheet.update(values=[['Note: Use postcode OR DNO dropdown, then click Lookup from menu']], range_name='A6')

print("\n✅ Enhanced BESS_VLP sheet created successfully!")
print(f"\n📊 Sheet URL: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid={sheet.id}")
print("\n🔧 Features added:")
print("   ✅ DNO dropdown selector (column E4)")
print("   ✅ Reference table hidden (rows 21+)")
print("   ✅ Map placeholder (row 17-20)")
print("\n🔧 Next: Update Apps Script for dropdown + map integration")
