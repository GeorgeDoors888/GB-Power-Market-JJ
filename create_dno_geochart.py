#!/usr/bin/env python3
"""
Create Google Sheets GeoChart for UK DNO Regions
Uses native Google Sheets charting instead of Apps Script
"""

import gspread
from google.oauth2.service_account import Credentials
import json

# Google Sheets credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

def create_dno_geochart():
    """Create GeoChart in Google Sheets DNO tab"""
    
    # Authenticate
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    # Open spreadsheet and DNO sheet
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    
    try:
        sheet = spreadsheet.worksheet('DNO')
    except:
        print("❌ DNO sheet not found")
        return
    
    # Load real GeoJSON data
    with open('gb_power_map_deployment/dno_regions.geojson', 'r') as f:
        geojson_data = json.load(f)
    
    print(f"✅ Loaded {len(geojson_data['features'])} DNO regions")
    
    # Prepare data for GeoChart
    # Format: Region Name | Metric Value | Tooltip
    headers = ['DNO Region', 'Customers (M)', 'Area (km²)', 'MPAN ID']
    data = [headers]
    
    for feature in geojson_data['features']:
        props = feature['properties']
        
        # Use area name as region identifier
        region_name = props.get('area', 'Unknown')
        
        # Calculate customers in millions (estimate based on area)
        area_sqkm = props.get('area_sqkm', 0)
        # Rough estimate: 200 customers per km² average
        customers_millions = (area_sqkm * 200) / 1000000
        
        mpan_id = props.get('mpan_id', 0)
        
        data.append([
            region_name,
            round(customers_millions, 2),
            round(area_sqkm, 0),
            mpan_id
        ])
    
    # Clear existing data in columns K:N (chart data area)
    sheet.batch_clear(['K1:N20'])
    
    # Write data starting at K1
    sheet.update('K1:N15', data)
    
    print(f"✅ Written {len(data)-1} DNO regions to K1:N15")
    
    # Create GeoChart specification
    chart_spec = {
        "chartId": 999,
        "basicChart": None,
        "pieChart": None,
        "geoChart": {
            "domain": "GB",  # United Kingdom
            "series": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet.id,
                        "startRowIndex": 0,
                        "endRowIndex": len(data),
                        "startColumnIndex": 10,  # Column K
                        "endColumnIndex": 12     # Column L (Customers)
                    }]
                }
            },
            "headerCount": 1
        },
        "position": {
            "overlayPosition": {
                "anchorCell": {
                    "sheetId": sheet.id,
                    "rowIndex": 0,
                    "columnIndex": 15  # Column P
                },
                "offsetXPixels": 0,
                "offsetYPixels": 0,
                "widthPixels": 800,
                "heightPixels": 600
            }
        },
        "title": "UK DNO License Areas",
        "subtitle": "Customer Distribution by Region"
    }
    
    # Add chart to sheet
    requests = [{
        'addChart': {
            'chart': chart_spec
        }
    }]
    
    try:
        spreadsheet.batch_update({'requests': requests})
        print("✅ GeoChart created in column P!")
    except Exception as e:
        print(f"❌ Chart creation failed: {e}")
        print("\n📋 Manual Steps:")
        print("1. Select range K1:L15")
        print("2. Insert → Chart")
        print("3. Chart type → Geo chart")
        print("4. Region: United Kingdom")
        print("5. Color by: Customers (M)")
    
    # Also create a summary table in columns K:N
    print("\n✅ Data Summary:")
    print("=" * 60)
    for row in data[1:]:
        print(f"{row[3]:2d} | {row[0]:30s} | {row[1]:6.2f}M | {row[2]:8.0f} km²")

if __name__ == '__main__':
    create_dno_geochart()
