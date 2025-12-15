#!/usr/bin/env python3
"""Create DNO map chart using Google Sheets API directly"""
import gspread
from google.oauth2.service_account import Credentials
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet('DNO')

# Get sheet ID
sheet_id = sheet.id
print(f"✅ Sheet ID: {sheet_id}")

# Calculate center point for each DNO region
def get_center(coordinates):
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

# Load GeoJSON
with open('/home/george/GB-Power-Market-JJ/gb_power_map_deployment/dno_regions.geojson', 'r') as f:
    data = json.load(f)

# Prepare data with coordinates
headers = ['DNO Area', 'Latitude', 'Longitude', 'MPAN', 'Area km²']
rows = [headers]

for f in data['features']:
    p = f['properties']
    lat, lon = get_center(f['geometry']['coordinates'])
    rows.append([
        p.get('area', 'Unknown'),
        round(lat, 4),
        round(lon, 4),
        p.get('mpan_id', 0),
        round(p.get('area_sqkm', 0), 0)
    ])

# Write data starting at A1
sheet.clear()
sheet.update(values=rows, range_name='A1:E15')
print(f"✅ Written {len(rows)} rows to A1:E15")

# Create map chart using Sheets API
chart_request = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "UK DNO License Areas",
                "basicChart": {
                    "chartType": "SCATTER",
                    "legendPosition": "RIGHT_LEGEND",
                    "axis": [
                        {
                            "position": "BOTTOM_AXIS",
                            "title": "Longitude"
                        },
                        {
                            "position": "LEFT_AXIS",
                            "title": "Latitude"
                        }
                    ],
                    "domains": [
                        {
                            "domain": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "sheetId": sheet_id,
                                            "startRowIndex": 1,
                                            "endRowIndex": 15,
                                            "startColumnIndex": 2,  # Column C (Longitude)
                                            "endColumnIndex": 3
                                        }
                                    ]
                                }
                            }
                        }
                    ],
                    "series": [
                        {
                            "series": {
                                "sourceRange": {
                                    "sources": [
                                        {
                                            "sheetId": sheet_id,
                                            "startRowIndex": 1,
                                            "endRowIndex": 15,
                                            "startColumnIndex": 1,  # Column B (Latitude)
                                            "endColumnIndex": 2
                                        }
                                    ]
                                }
                            },
                            "targetAxis": "LEFT_AXIS"
                        }
                    ],
                    "headerCount": 1
                }
            },
            "position": {
                "overlayPosition": {
                    "anchorCell": {
                        "sheetId": sheet_id,
                        "rowIndex": 0,
                        "columnIndex": 6  # Column G
                    },
                    "offsetXPixels": 20,
                    "offsetYPixels": 20,
                    "widthPixels": 800,
                    "heightPixels": 600
                }
            }
        }
    }
}

# Execute the chart creation
response = spreadsheet.batch_update({"requests": [chart_request]})
print(f"✅ Chart created successfully!")
print(f"📊 Chart ID: {response['replies'][0]['addChart']['chart']['chartId']}")

print(f"\n✅ DONE! Open spreadsheet to see the DNO map chart:")
print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")

# Print data summary
print(f"\n📍 DNO Locations:")
for row in rows[1:]:
    print(f"  MPAN {row[3]:2d}: {row[0]:35s} @ ({row[1]}, {row[2]})")
