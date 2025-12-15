#!/usr/bin/env python3
"""
Create BESS_VLP Sheet with Postcode to DNO Lookup
Uses UK postcode API to get coordinates, then BigQuery spatial query to find DNO
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import requests
import os

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_FILE

print("🔋 Creating BESS_VLP Sheet with DNO Lookup")
print("="*70)

# Setup Google Sheets
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
gc = gspread.authorize(creds)

# Setup BigQuery
bq_client = bigquery.Client(project=PROJECT_ID, location='US')

# Open spreadsheet
ss = gc.open_by_key(SPREADSHEET_ID)

# Check if BESS_VLP sheet exists
try:
    sheet = ss.worksheet('BESS_VLP')
    print("✅ BESS_VLP sheet already exists, will update it")
except:
    print("📝 Creating new BESS_VLP sheet...")
    sheet = ss.add_worksheet(title='BESS_VLP', rows=100, cols=20)
    print("✅ Created BESS_VLP sheet")

# Clear existing content
sheet.clear()

# Create header and structure
print("\n📊 Setting up sheet structure...")

# Prepare all updates in batch format
updates = [
    # Row 1-2: Title
    {'range': 'A1', 'values': [['BESS VLP - DNO Lookup Tool']]},
    {'range': 'A2', 'values': [['Enter postcode to find Distribution Network Operator']]},
    
    # Row 4: Input section
    {'range': 'A4', 'values': [['Postcode:']]},
    {'range': 'B4', 'values': [['ENTER POSTCODE HERE']]},
    
    # Row 5: Instruction
    {'range': 'A5', 'values': [['↓ Click "Lookup DNO" button below or use Apps Script']]},
    
    # Row 7: Results header
    {'range': 'A7', 'values': [['DNO INFORMATION:']]},
]

# Row 9: Column headers for DNO data
headers = [
    'MPAN/Distributor ID',
    'DNO Key',
    'DNO Name',
    'DNO Short Code',
    'Market Participant ID',
    'GSP Group ID',
    'GSP Group Name',
    'Coverage Area'
]
updates.append({'range': 'A9:H9', 'values': [headers]})

# Row 10: Data will be populated here (empty for now)

# Row 13-15: Additional info section
updates.append({'range': 'A13', 'values': [['SITE LOCATION:']]})
updates.append({'range': 'A14', 'values': [['Latitude:']]})
updates.append({'range': 'A15', 'values': [['Longitude:']]})

# Row 17: All DNOs reference table
updates.append({'range': 'A17', 'values': [['ALL UK DNO REFERENCE DATA:']]})

# Row 19: Reference table headers
ref_headers = [
    'MPAN',
    'DNO Key',
    'DNO Name',
    'Short Code',
    'Participant ID',
    'GSP Group',
    'GSP Name',
    'Coverage'
]
updates.append({'range': 'A19:H19', 'values': [ref_headers]})

# Apply all header/structure updates at once
sheet.batch_update(updates)
print("✅ Sheet structure created")

# Row 20+: Populate all 14 DNOs from BigQuery
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

# Update reference table
if dno_data:
    range_name = f'A20:H{19 + len(dno_data)}'
    sheet.update(range_name, dno_data, value_input_option='USER_ENTERED')
    print(f"✅ Populated {len(dno_data)} DNO records")

# Format the sheet
print("\n🎨 Applying formatting...")

# Format headers
sheet.format('A1:H1', {
    'textFormat': {'bold': True, 'fontSize': 14},
    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
    'horizontalAlignment': 'LEFT'
})

# Format section headers
for row in [7, 13, 17]:
    sheet.format(f'A{row}:H{row}', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })

# Format column headers
sheet.format('A9:H9', {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
})

sheet.format('A19:H19', {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
})

# Format input cell
sheet.format('B4', {
    'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.8},
    'textFormat': {'bold': True}
})

# Set column widths using batch_update (correct API)
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
            'properties': {'pixelSize': 300},
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

spreadsheet = gc.open_by_key(SPREADSHEET_ID)
spreadsheet.batch_update({'requests': requests})

# Add instruction note
sheet.update('A6', [['Note: Use Apps Script function lookupDNO() to populate results automatically']])

print("\n✅ BESS_VLP sheet created successfully!")
print(f"\n📊 Sheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet.id}")
print("\n🔧 Next step: Deploy Apps Script code for postcode lookup")
