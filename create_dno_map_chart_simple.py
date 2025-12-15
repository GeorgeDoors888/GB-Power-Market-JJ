#!/usr/bin/env python3
"""Create DNO map as Google Sheets chart"""
import gspread
from google.oauth2.service_account import Credentials
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# Find or create DNO sheet
try:
    sheet = spreadsheet.worksheet('DNO')
    print("✅ Found existing DNO sheet")
except:
    sheet = spreadsheet.add_worksheet(title='DNO', rows=100, cols=20)
    print("✅ Created new DNO sheet")

# Load real GeoJSON
with open('/home/george/GB-Power-Market-JJ/gb_power_map_deployment/dno_regions.geojson', 'r') as f:
    data = json.load(f)

print(f"✅ Loaded {len(data['features'])} DNO regions")

# Prepare data for chart: Region | Value | Tooltip
headers = ['Region', 'Customers', 'Area', 'MPAN']
rows = [headers]

for f in data['features']:
    p = f['properties']
    rows.append([
        p.get('area', 'Unknown'),
        round(p.get('area_sqkm', 0) * 200 / 1000000, 2),  # Estimated customers
        round(p.get('area_sqkm', 0), 0),
        p.get('mpan_id', 0)
    ])

# Write to columns A:D
sheet.update('A1:D15', rows)
print(f"✅ Written {len(rows)} rows to A1:D15")

# Now manually add chart:
print("\n📊 MANUAL STEPS TO ADD MAP:")
print("1. Open spreadsheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/")
print("2. Go to DNO tab")
print("3. Select range A1:B15")
print("4. Insert → Chart")
print("5. Chart type → Geo chart")
print("6. Region: United Kingdom")
print("7. Done!")
