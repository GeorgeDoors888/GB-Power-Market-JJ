#!/usr/bin/env python3
"""
Import DNO Centroids to Google Sheets and set up GeoChart
Creates DNO_CENTROIDS tab with interactive map
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
WORKSHEET_NAME = "DNO_CENTROIDS"

def main():
    print("🗺️  Importing DNO Centroids to Google Sheets...")
    print("="*80)
    
    # Read CSV
    print("\n📥 Reading dno_centroids.csv...")
    df = pd.read_csv('dno_centroids.csv')
    print(f"   Loaded {len(df)} DNO regions")
    
    # Connect to Google Sheets
    print("\n📝 Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Create or clear worksheet
    try:
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        print(f"   Found existing '{WORKSHEET_NAME}' sheet - clearing...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"   Creating new '{WORKSHEET_NAME}' sheet...")
        sheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=100, cols=10)
    
    # Prepare data with headers
    print("\n📊 Preparing data...")
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Add value column header
    data[0].append('value')
    
    # Add value formulas for each row
    for i in range(1, len(data)):
        # Formula: =IF(B2='Dashboard V3'!$B$10, 1, 0)
        row_num = i + 1
        formula = f"=IF(B{row_num}='Dashboard V3'!$B$10, 1, 0)"
        data[i].append(formula)
    
    # Write to sheet
    print(f"\n✍️  Writing {len(data)} rows to Google Sheets...")
    sheet.update('A1', data, value_input_option='USER_ENTERED')
    
    # Format header row
    print("\n🎨 Formatting sheet...")
    sheet.format('A1:F1', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Set column widths
    requests = [
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1},
                'properties': {'pixelSize': 80},
                'fields': 'pixelSize'
            }
        },
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2},
                'properties': {'pixelSize': 280},
                'fields': 'pixelSize'
            }
        },
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 4},
                'properties': {'pixelSize': 100},
                'fields': 'pixelSize'
            }
        }
    ]
    spreadsheet.batch_update({'requests': requests})
    
    print("\n✅ DNO Centroids imported successfully!")
    print(f"\n📍 Summary:")
    print(f"   - Spreadsheet: {SPREADSHEET_ID}")
    print(f"   - Worksheet: {WORKSHEET_NAME}")
    print(f"   - DNO Regions: {len(df)}")
    print(f"   - Columns: dno_id, dno_name, lat, lon, size, value")
    print("\n📊 Next steps:")
    print("   1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc")
    print("   2. Go to DNO_CENTROIDS tab")
    print("   3. Select data range A1:F15")
    print("   4. Insert → Chart")
    print("   5. Chart type: Geo chart")
    print("   6. Region: World (or United Kingdom)")
    print("   7. Display mode: Markers")
    print("   8. Setup:")
    print("      - Latitude: Column C (lat)")
    print("      - Longitude: Column D (lon)")
    print("      - Color: Column F (value)")
    print("      - Tooltip: Column B (dno_name)")
    print("\n🎯 Test: Change 'Dashboard V3'!B10 to a DNO ID (ENWL, NPG, UKPN, etc.)")
    print("   → Map marker will highlight!")

if __name__ == "__main__":
    main()
