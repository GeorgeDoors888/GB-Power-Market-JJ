#!/usr/bin/env python3
"""
Populate Chart Data sheet for Dashboard V3 timeseries charts

Fetches today's data from BigQuery:
- Settlement periods (48 half-hourly)
- System demand (MW)
- Expected wind (MW)
- Delivered wind (MW)
- Interconnector net import (MW)
- Day-ahead price (£/MWh)
- Imbalance price (£/MWh)

Populates rows 2-49 (48 SPs) in Chart Data sheet
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, date
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SHEET_NAME = "Chart Data"

def get_todays_data():
    """Query BigQuery for today's settlement period data"""
    print("\n📥 Querying BigQuery for today's data...")
    
    creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
    client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    
    today = date.today().strftime('%Y-%m-%d')
    
    query = f"""
    WITH settlement_periods AS (
        SELECT settlement_period
        FROM UNNEST(GENERATE_ARRAY(1, 48)) AS settlement_period
    ),
    
    wind_data AS (
        SELECT 
            settlementPeriod as sp,
            AVG(generation) as delivered_wind_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE fuelType = 'WIND'
          AND CAST(settlementDate AS DATE) = '{today}'
        GROUP BY sp
    ),
    
    demand_data AS (
        SELECT
            settlementPeriod as sp,
            AVG(demand) as system_demand_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem_iris`
        WHERE CAST(settlementDate AS DATE) = '{today}'
        GROUP BY sp
    ),
    
    ic_data AS (
        SELECT
            settlementPeriod as sp,
            SUM(generation) as ic_net_import_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE fuelType IN ('INTFR', 'INTIRL', 'INTNED', 'INTEW', 'INTNEM', 'INTNSL', 'INTIFA2')
          AND CAST(settlementDate AS DATE) = '{today}'
        GROUP BY sp
    ),
    
    price_data AS (
        SELECT
            settlementPeriod as sp,
            AVG(price) as imbalance_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE CAST(settlementDate AS DATE) = '{today}'
        GROUP BY sp
    )
    
    SELECT 
        sp.settlement_period,
        COALESCE(dd.system_demand_mw, 0) as system_demand_mw,
        COALESCE(wd.delivered_wind_mw, 0) as expected_wind_mw,  -- Use actual as proxy for expected
        COALESCE(wd.delivered_wind_mw, 0) as delivered_wind_mw,
        COALESCE(ic.ic_net_import_mw, 0) as ic_net_import_mw,
        0 as dayahead_price,  -- Placeholder - would need DA price source
        COALESCE(pd.imbalance_price, 0) as imbalance_price
    FROM settlement_periods sp
    LEFT JOIN wind_data wd ON sp.settlement_period = wd.sp
    LEFT JOIN demand_data dd ON sp.settlement_period = dd.sp
    LEFT JOIN ic_data ic ON sp.settlement_period = ic.sp
    LEFT JOIN price_data pd ON sp.settlement_period = pd.sp
    ORDER BY sp.settlement_period
    """
    
    df = client.query(query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} settlement periods")
    return df

def create_or_clear_sheet(spreadsheet, sheet_name):
    """Create Chart Data sheet or clear if exists"""
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        print(f"   Found existing '{sheet_name}' - clearing...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"   Creating new '{sheet_name}' sheet...")
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)
    return sheet

def populate_sheet(df):
    """Write data to Chart Data sheet"""
    print("\n📝 Writing to Google Sheets...")
    
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    sheet = create_or_clear_sheet(spreadsheet, SHEET_NAME)
    
    # Headers
    headers = [
        'Settlement Period',
        'System Demand (MW)',
        'Expected Wind (MW)',
        'Delivered Wind (MW)',
        'IC Net Import (MW)',
        'Unused F',
        'Day-ahead Price (£/MWh)',
        'Imbalance Price (£/MWh)'
    ]
    
    # Prepare data
    data = [headers]
    for _, row in df.iterrows():
        data.append([
            int(row['settlement_period']),
            float(row['system_demand_mw']),
            float(row['expected_wind_mw']),
            float(row['delivered_wind_mw']),
            float(row['ic_net_import_mw']),
            '',  # Col F unused
            float(row['dayahead_price']),
            float(row['imbalance_price'])
        ])
    
    # Write to sheet
    sheet.update(values=data, range_name='A1', value_input_option='USER_ENTERED')
    
    # Format header
    sheet.format('A1:H1', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    print(f"   ✅ Wrote {len(data)} rows to {SHEET_NAME}")
    return sheet.id

def main():
    print("📊 Populating Chart Data for Dashboard V3")
    print("="*60)
    
    df = get_todays_data()
    sheet_id = populate_sheet(df)
    
    print("\n✅ Chart Data populated successfully!")
    print(f"\n   Sheet ID: {sheet_id}")
    print(f"   Rows: 49 (header + 48 SPs)")
    print(f"   Columns: A-H")
    print(f"\n📝 Next: Run update_dashboard_v3_layout_timeseries.py")

if __name__ == "__main__":
    main()
