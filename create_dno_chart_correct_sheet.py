#!/usr/bin/env python3
"""Create DNO map chart in the CORRECT spreadsheet"""
import gspread
from google.oauth2.service_account import Credentials
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'  # CORRECT ONE

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)

print(f"✅ Connected to correct spreadsheet")
print(f"📋 Available sheets: {[s.title for s in spreadsheet.worksheets()]}")

# Get or create DNO sheet
try:
    sheet = spreadsheet.worksheet('DNO')
    print(f"✅ Found DNO sheet")
except:
    sheet = spreadsheet.add_worksheet(title='DNO', rows=100, cols=20)
    print(f"✅ Created DNO sheet")

sheet_id = sheet.id

# Load GeoJSON and calculate centers
with open('/home/george/GB-Power-Market-JJ/gb_power_map_deployment/dno_regions.geojson', 'r') as f:
    data = json.load(f)

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

# Prepare data
headers = ['DNO Region', 'Latitude', 'Longitude', 'MPAN', 'Area km²', 'Company']
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

# Clear and write data
sheet.clear()
sheet.update(values=rows, range_name='A1:F15')
print(f"✅ Written {len(rows)} rows to A1:F15")

# Delete old charts
try:
    metadata = spreadsheet.fetch_sheet_metadata()
    delete_requests = []
    for s in metadata['sheets']:
        if s['properties']['sheetId'] == sheet_id and 'charts' in s:
            for chart in s['charts']:
                delete_requests.append({'deleteEmbeddedObject': {'objectId': chart['chartId']}})
    if delete_requests:
        spreadsheet.batch_update({'requests': delete_requests})
        print(f"✅ Deleted {len(delete_requests)} old charts")
except:
    pass

# Create scatter chart with labels
chart_request = {
    "addChart": {
        "chart": {
            "spec": {
                "title": "🗺️ UK DNO Geographic Map",
                "subtitle": "14 Distribution Network Operator License Areas",
                "basicChart": {
                    "chartType": "SCATTER",
                    "legendPosition": "BOTTOM_LEGEND",
                    "axis": [
                        {
                            "position": "BOTTOM_AXIS",
                            "title": "Longitude (West ←→ East)"
                        },
                        {
                            "position": "LEFT_AXIS",
                            "title": "Latitude (South ←→ North)"
                        }
                    ],
                    "domains": [
                        {
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 1,
                                        "endRowIndex": 15,
                                        "startColumnIndex": 2,  # Longitude
                                        "endColumnIndex": 3
                                    }]
                                }
                            }
                        }
                    ],
                    "series": [
                        {
                            "series": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 1,
                                        "endRowIndex": 15,
                                        "startColumnIndex": 1,  # Latitude
                                        "endColumnIndex": 2
                                    }]
                                }
                            },
                            "targetAxis": "LEFT_AXIS",
                            "dataLabel": {
                                "type": "CUSTOM",
                                "customLabelData": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheet_id,
                                            "startRowIndex": 1,
                                            "endRowIndex": 15,
                                            "startColumnIndex": 0,  # DNO names
                                            "endColumnIndex": 1
                                        }]
                                    }
                                }
                            }
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
                        "columnIndex": 7  # Column H
                    },
                    "offsetXPixels": 20,
                    "offsetYPixels": 20,
                    "widthPixels": 900,
                    "heightPixels": 700
                }
            }
        }
    }
}

response = spreadsheet.batch_update({"requests": [chart_request]})
chart_id = response['replies'][0]['addChart']['chart']['chartId']

print(f"\n✅ SUCCESS! Chart created (ID: {chart_id})")
print(f"\n📊 DNO Data in columns A-F:")
for i, row in enumerate(rows[:5], 1):
    print(f"   Row {i}: {row}")
print(f"   ... ({len(rows)-5} more rows)")

print(f"\n🗺️ Chart positioned at column H")
print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet_id}")
