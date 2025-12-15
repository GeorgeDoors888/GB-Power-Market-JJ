#!/usr/bin/env python3
"""Create actual visual DNO map in Google Sheets using latitude/longitude points"""
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

# Calculate center point for each DNO region
def get_center(coordinates):
    """Get approximate center of a polygon/multipolygon"""
    all_lons, all_lats = [], []
    
    if isinstance(coordinates[0][0][0], list):  # MultiPolygon
        for polygon in coordinates:
            for ring in polygon:
                for lon, lat in ring:
                    all_lons.append(lon)
                    all_lats.append(lat)
    else:  # Polygon
        for ring in coordinates:
            for lon, lat in ring:
                all_lons.append(lon)
                all_lats.append(lat)
    
    return sum(all_lats)/len(all_lats), sum(all_lons)/len(all_lons)

# Create data with lat/lon for map chart
headers = ['DNO Area', 'Latitude', 'Longitude', 'MPAN', 'Area km²', 'Company']
rows = [headers]

for f in data['features']:
    p = f['properties']
    lat, lon = get_center(f['geometry']['coordinates'])
    
    rows.append([
        p.get('area', 'Unknown'),
        round(lat, 4),
        round(lon, 4),
        p.get('mpan_id', 0),
        round(p.get('area_sqkm', 0), 0),
        p.get('dno_name', 'Unknown')
    ])

# Write to columns M:R
sheet.update(values=rows, range_name='M1:R15')

print(f"✅ Written {len(rows)} rows to M1:R15")
print(f"\n📍 DNO CENTERS (for Map chart):")
print("=" * 80)
for row in rows[1:]:
    print(f"MPAN {row[3]:2d}: {row[0]:35s} @ ({row[1]}, {row[2]})")

print(f"\n📊 CREATE MAP CHART:")
print("1. Select M1:R15")
print("2. Insert → Chart")
print("3. Chart type → 'Map' (not Geo chart!)")
print("4. Latitude: Column B (Latitude)")
print("5. Longitude: Column C (Longitude)")
print("6. Label: Column A (DNO Area)")
print("\nThis will show actual location points for each DNO region on a real map!")
