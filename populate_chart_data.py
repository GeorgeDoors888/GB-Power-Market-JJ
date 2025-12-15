#!/usr/bin/env python3
"""
Check Chart Data sheet and populate it with dashboard data
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime
import os

# Setup
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

print("\n🔧 Setting up Chart Data for dashboard charts...")
print("=" * 60)

# Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

# BigQuery
bq_client = bigquery.Client(project=PROJECT_ID)

# Open spreadsheet
spreadsheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')

# Check Chart Data sheet
try:
    chart_sheet = spreadsheet.worksheet('Chart Data')
    print("✅ Found 'Chart Data' sheet")
    
    # Check if it has data
    data = chart_sheet.get_all_values()
    print(f"   Current rows: {len(data)}")
    
    if len(data) <= 1:
        print("\n📊 Populating Chart Data with today's generation data...")
        
        # Query today's data
        date_today = datetime.now().date()
        query = f"""
        WITH combined AS (
          SELECT 
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            fuelType,
            generation
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
          WHERE CAST(settlementDate AS DATE) = '{date_today}'
            AND settlementPeriod >= 1
          
          UNION ALL
          
          SELECT 
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            fuelType,
            generation
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          WHERE CAST(settlementDate AS DATE) = '{date_today}'
            AND settlementPeriod >= 1
        )
        SELECT 
          date,
          settlementPeriod,
          fuelType,
          SUM(generation) as total_mwh
        FROM combined
        GROUP BY date, settlementPeriod, fuelType
        ORDER BY settlementPeriod, fuelType
        LIMIT 1000
        """
        
        df = bq_client.query(query).to_dataframe()
        
        if len(df) > 0:
            # Prepare data for sheets (convert to list of lists)
            headers = [['Date', 'Settlement Period', 'Fuel Type', 'Generation (MWh)', 'Timestamp', 'Hour']]
            
            rows = []
            for _, row in df.iterrows():
                hour = (row['settlementPeriod'] - 1) // 2  # SP to hour conversion
                rows.append([
                    str(row['date']),
                    int(row['settlementPeriod']),
                    str(row['fuelType']),
                    float(row['total_mwh']),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    int(hour)
                ])
            
            # Update sheet
            chart_sheet.clear()
            chart_sheet.update('A1', headers + rows)
            
            print(f"✅ Populated Chart Data with {len(rows)} rows")
            print(f"   Settlement Periods: {df['settlementPeriod'].min()} to {df['settlementPeriod'].max()}")
            print(f"   Fuel Types: {df['fuelType'].nunique()}")
        else:
            print("⚠️  No data found for today")
    else:
        print(f"✅ Chart Data already has {len(data) - 1} rows of data")
        
except gspread.exceptions.WorksheetNotFound:
    print("❌ 'Chart Data' sheet not found")
    print("\n🔧 Creating 'Chart Data' sheet...")
    
    chart_sheet = spreadsheet.add_worksheet(title='Chart Data', rows=1000, cols=10)
    print("✅ Created 'Chart Data' sheet")
    print("\n🔄 Re-run this script to populate it with data")

print("\n" + "=" * 60)
print("🎯 Next step: Run createDashboardCharts() in Apps Script")
print("=" * 60)
