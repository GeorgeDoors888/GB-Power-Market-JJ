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
    """Fetch today's wind actual and forecast data"""
    print("📊 Fetching wind actual and forecast data...")
    
    bq_creds = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")
    
    # Get wind generation (actual) and forecast
    # Wind forecast is hourly - replicate to both half-hourly SPs
    query = f"""
    WITH actual_data AS (
        SELECT
            settlementDate,
            settlementPeriod,
            generation,
            ROW_NUMBER() OVER (PARTITION BY settlementPeriod ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND fuelType = 'WIND'
    ),
    actual_agg AS (
        SELECT
            settlementPeriod,
            SUM(generation) / 1000 as actual_gw
        FROM actual_data
        WHERE rn = 1
        GROUP BY settlementPeriod
    ),
    latest_forecast_date AS (
        SELECT MAX(CAST(startTime AS DATE)) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor_iris`
    ),
    forecast_hourly AS (
        SELECT
            EXTRACT(HOUR FROM startTime) as hour,
            generation / 1000 as forecast_gw,
            CAST(startTime AS DATE) as forecast_date,
            publishTime,
            ROW_NUMBER() OVER (
                PARTITION BY EXTRACT(HOUR FROM startTime), CAST(startTime AS DATE)
                ORDER BY publishTime DESC
            ) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor_iris`
        WHERE CAST(startTime AS DATE) IN (
            CURRENT_DATE(),
            (SELECT max_date FROM latest_forecast_date)
        )
    ),
    forecast_expanded AS (
        -- Expand hourly forecasts to two settlement periods
        SELECT hour * 2 + 1 as settlementPeriod, forecast_gw, forecast_date FROM forecast_hourly WHERE rn = 1
        UNION ALL
        SELECT hour * 2 + 2 as settlementPeriod, forecast_gw, forecast_date FROM forecast_hourly WHERE rn = 1
    )
    SELECT
        a.settlementPeriod,
        COALESCE(a.actual_gw, 0) as actual_gw,
        COALESCE(AVG(f.forecast_gw), 0) as forecast_gw,
        MAX(f.forecast_date) as forecast_source_date
    FROM actual_agg a
    LEFT JOIN forecast_expanded f ON a.settlementPeriod = f.settlementPeriod
    GROUP BY a.settlementPeriod, a.actual_gw
    ORDER BY a.settlementPeriod
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        print(f"   ✅ Retrieved {len(df)} settlement periods")
        
        forecast_date = df['forecast_source_date'].dropna().iloc[0] if not df['forecast_source_date'].dropna().empty else None
        forecast_avg = df['forecast_gw'].mean()
        actual_avg = df['actual_gw'].mean()
        
        print(f"   📊 Actual: {actual_avg:.2f} GW avg")
        if forecast_avg > 0:
            print(f"   📊 Forecast: {forecast_avg:.2f} GW avg (from {forecast_date})")
        else:
            print(f"   ⚠️  Forecast: No data available (showing 0)")
        
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
    
    # Write to A40:C88 (header + 48 periods) with RAW_INPUT to prevent formatting
    sheet.update(values=data, range_name='A40:C88', value_input_option='RAW')
    
    # Apply number formatting (not currency) to columns B and C
    spreadsheet.batch_update({
        "requests": [{
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 40,  # Row 41 (0-indexed)
                    "endRowIndex": 88,     # Row 88
                    "startColumnIndex": 1, # Column B
                    "endColumnIndex": 3    # Column C (inclusive)
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "NUMBER",
                            "pattern": "0.00"
                        }
                    }
                },
                "fields": "userEnteredFormat.numberFormat"
            }
        }]
    })
    
    print(f"   ✅ Updated {len(data)-1} rows of data at A40:C88")
    print(f"   ✅ Applied number formatting (not currency)")
    
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
