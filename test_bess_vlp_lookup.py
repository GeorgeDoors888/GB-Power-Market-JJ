#!/usr/bin/env python3
"""
Test the complete BESS VLP lookup workflow
Simulates what Apps Script should do
"""

import gspread
import requests
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

# Initialize clients
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery'
]
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet('BESS_VLP')

# Get postcode from B4
postcode = sheet.acell('B4').value
print(f'📍 Testing postcode: {postcode}')

# Step 1: Get coordinates from postcode API
print('\n🌐 Step 1: Lookup coordinates from postcodes.io...')
clean_postcode = postcode.replace(' ', '').upper()
url = f'https://api.postcodes.io/postcodes/{clean_postcode}'

try:
    response = requests.get(url)
    data = response.json()
    
    if data['status'] == 200 and data['result']:
        lat = data['result']['latitude']
        lng = data['result']['longitude']
        admin_district = data['result']['admin_district']
        
        print(f'✅ Found coordinates:')
        print(f'   Latitude: {lat}')
        print(f'   Longitude: {lng}')
        print(f'   Admin District: {admin_district}')
        
        # Update sheet with coordinates
        sheet.update('B14', [[lat]])
        sheet.update('B15', [[lng]])
        
    else:
        print(f'❌ Postcode not found: {data}')
        exit(1)
        
except Exception as e:
    print(f'❌ Postcode API error: {e}')
    exit(1)

# Step 2: Query BigQuery for DNO
print('\n🔍 Step 2: Query BigQuery for DNO boundary match...')

# Use same credentials for BigQuery
bq_client = bigquery.Client(project='inner-cinema-476211-u9', location='US', credentials=creds)

query = f"""
SELECT 
    d.dno_id,
    d.dno_code,
    r.mpan_distributor_id,
    r.dno_key,
    r.dno_name,
    r.dno_short_code,
    r.market_participant_id,
    r.gsp_group_id,
    r.gsp_group_name,
    r.primary_coverage_area
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries` d
JOIN `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` r
    ON d.dno_id = r.mpan_distributor_id
WHERE ST_CONTAINS(
    d.boundary,
    ST_GEOGPOINT({lng}, {lat})
)
LIMIT 1
"""

try:
    df = bq_client.query(query).to_dataframe()
    
    if len(df) > 0:
        row = df.iloc[0]
        print(f'✅ Found DNO:')
        print(f'   MPAN: {row["mpan_distributor_id"]}')
        print(f'   DNO Key: {row["dno_key"]}')
        print(f'   DNO Name: {row["dno_name"]}')
        print(f'   Short Code: {row["dno_short_code"]}')
        print(f'   Market Participant: {row["market_participant_id"]}')
        print(f'   GSP Group: {row["gsp_group_id"]}')
        print(f'   GSP Name: {row["gsp_group_name"]}')
        print(f'   Coverage: {row["primary_coverage_area"][:50]}...')
        
        # Step 3: Populate results in sheet
        print('\n📝 Step 3: Updating Google Sheet with results...')
        
        results = [[
            int(row["mpan_distributor_id"]),
            row["dno_key"],
            row["dno_name"],
            row["dno_short_code"] if row["dno_short_code"] else '',
            row["market_participant_id"] if row["market_participant_id"] else '',
            row["gsp_group_id"],
            row["gsp_group_name"],
            row["primary_coverage_area"][:50] if row["primary_coverage_area"] else ''
        ]]
        
        sheet.update('A10:H10', results)
        
        # Highlight results row
        sheet.format('A10:H10', {
            'backgroundColor': {'red': 0.85, 'green': 0.92, 'blue': 0.83}
        })
        
        # Add timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sheet.update('A11', [[f'Last updated: {timestamp}']])
        
        print('✅ Sheet updated successfully!')
        print(f'\n🔗 View results: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet.id}')
        
    else:
        print('❌ No DNO found for these coordinates')
        print(f'   Query returned 0 rows')
        print(f'   Coordinates: {lat}, {lng}')
        
except Exception as e:
    print(f'❌ BigQuery error: {e}')
    import traceback
    traceback.print_exc()
