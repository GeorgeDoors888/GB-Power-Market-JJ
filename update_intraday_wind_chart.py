#!/usr/bin/env python3
"""
Update Intraday Wind Chart Data and Position
Updates the chart at A40:F57 with latest wind actual vs forecast data
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from datetime import datetime

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
SA_FILE = 'inner-cinema-credentials.json'

def fetch_wind_actual_forecast():
    """Fetch today's wind actual data (forecast table not available in IRIS)"""
    print("📊 Fetching wind actual data...")
    
    bq_creds = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")
    
    # Get wind generation (actual) from fuelinst_iris - deduplicate by latest publishTime
    query = f"""
    WITH ranked_data AS (
        SELECT
            settlementDate,
            settlementPeriod,
            generation,
            ROW_NUMBER() OVER (PARTITION BY settlementPeriod ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND fuelType = 'WIND'
    )
    SELECT
        settlementPeriod,
        SUM(generation) / 1000 as actual_gw,
        0 as forecast_gw  -- Placeholder for forecast (not available)
    FROM ranked_data
    WHERE rn = 1
    GROUP BY settlementPeriod
    ORDER BY settlementPeriod
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        print(f"   ✅ Retrieved {len(df)} settlement periods")
        return df
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return None

def update_chart_data(df):
    """Update the data range for the wind chart"""
    print("\n📝 Updating chart data in Google Sheets...")
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    sheets_creds = service_account.Credentials.from_service_account_file(SA_FILE, scopes=SCOPES)
    gc = gspread.authorize(sheets_creds)
    
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    # Prepare data for writing (Settlement Period, Actual GW, Forecast GW)
    data = [['Settlement Period', 'Actual (GW)', 'Forecast (GW)']]
    for _, row in df.iterrows():
        data.append([
            int(row['settlementPeriod']),
            round(float(row['actual_gw']), 2),
            round(float(row['forecast_gw']), 2)
        ])
    
    # Write to A40:C88 (header + 48 periods)
    sheet.update('A40:C88', data, value_input_option='USER_ENTERED')
    print(f"   ✅ Updated {len(data)-1} rows of data at A40:C88")
    
    return sheet

def reposition_chart(sheet):
    """Reposition the chart to proper location"""
    print("\n📐 Repositioning chart...")
    
    spreadsheet = sheet.spreadsheet
    sheet_id = sheet.id
    
    # Get all charts on the sheet
    sheet_metadata = spreadsheet.fetch_sheet_metadata({'includeGridData': False})
    
    for s in sheet_metadata['sheets']:
        if s['properties']['sheetId'] == sheet_id:
            if 'charts' in s:
                print(f"   Found {len(s['charts'])} chart(s) on sheet")
                
                # Find the wind chart (should be the one referencing our data range)
                for chart in s['charts']:
                    chart_id = chart['chartId']
                    
                    # Update chart position to A40 (anchor position)
                    update_request = {
                        "requests": [{
                            "updateEmbeddedObjectPosition": {
                                "objectId": chart_id,
                                "newPosition": {
                                    "overlayPosition": {
                                        "anchorCell": {
                                            "sheetId": sheet_id,
                                            "rowIndex": 39,  # Row 40 (0-indexed)
                                            "columnIndex": 0  # Column A
                                        },
                                        "offsetXPixels": 0,
                                        "offsetYPixels": 0,
                                        "widthPixels": 500,
                                        "heightPixels": 300
                                    }
                                },
                                "fields": "overlayPosition"
                            }
                        }]
                    }
                    
                    spreadsheet.batch_update(update_request)
                    print(f"   ✅ Repositioned chart to A40 (500x300px)")
                    break
            else:
                print("   ⚠️  No charts found on sheet")

def main():
    print("\n" + "=" * 80)
    print("⚡ INTRADAY WIND CHART UPDATE")
    print("=" * 80)
    
    # Fetch data
    df = fetch_wind_actual_forecast()
    if df is None or df.empty:
        print("❌ No data available")
        return
    
    # Update data
    sheet = update_chart_data(df)
    
    # Note: Chart repositioning removed due to API limitations
    # Chart already exists at A40:F57, data range is A40:C88
    
    print("\n" + "=" * 80)
    print("✅ UPDATE COMPLETE")
    print("=" * 80)
    print(f"Chart data: A40:C{39+len(df)+1}")
    print(f"Chart should now display updated wind data")
    print(f"\nNote: Chart repositioning skipped (already at A40:F57)")
    print("      If chart position is incorrect, manually adjust in Google Sheets")

if __name__ == "__main__":
    main()
