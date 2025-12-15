#!/usr/bin/env python3
"""Create DNO map with proper UK region codes for Google Sheets GeoChart"""
import gspread
from google.oauth2.service_account import Credentials
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet('DNO')

# Load GeoJSON
with open('/home/george/GB-Power-Market-JJ/gb_power_map_deployment/dno_regions.geojson', 'r') as f:
    data = json.load(f)

# Map DNO areas to Google-recognized UK region names
region_mapping = {
    'East England': 'East of England',
    'East Midlands': 'East Midlands',
    'London': 'London',
    'North Wales, Merseyside and Cheshire': 'North West',
    'West Midlands': 'West Midlands',
    'North East England': 'North East',
    'North West England': 'North West',
    'Southern England': 'South East',
    'South East England': 'South East',
    'South Wales': 'Wales',
    'South West England': 'South West',
    'Yorkshire': 'Yorkshire and the Humber',
    'South and Central Scotland': 'Scotland',
    'North Scotland': 'Scotland'
}

headers = ['Region', 'Coverage Area', 'MPAN ID', 'Area km²']
rows = [headers]

for f in data['features']:
    p = f['properties']
    area = p.get('area', 'Unknown')
    google_region = region_mapping.get(area, area)
    
    rows.append([
        google_region,
        area,
        p.get('mpan_id', 0),
        round(p.get('area_sqkm', 0), 0)
    ])

# Clear and write
sheet.clear()
sheet.update(values=rows, range_name='A1:D15')

print(f"✅ Updated DNO sheet with {len(rows)-1} regions")
print("\n📊 NOW ADD CHART:")
print("1. Select A1:A15 (just the Region column)")
print("2. Insert → Chart")
print("3. Chart type → Map → Geo chart")
print("4. Region: United Kingdom")
print("5. Color by: Leave default")
print("\nRegions mapped:")
for row in rows[1:]:
    print(f"  {row[1]:35s} → {row[0]}")
