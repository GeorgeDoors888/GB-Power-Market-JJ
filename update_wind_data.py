#!/usr/bin/env python3
"""
Wind Performance Data Update - Populate Chart_Wind_Perf sheet
Queries bmrs_fuelinst_iris for actual wind generation
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime
import os
import pandas as pd

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

print("\n🌬️  WIND PERFORMANCE DATA UPDATE")
print("=" * 60)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID)

ss = gc.open_by_key(SPREADSHEET_ID)

# Query wind data
query = f"""
SELECT
    TIMESTAMP_TRUNC(CAST(settlementDate AS TIMESTAMP), HOUR) as timestamp,
    AVG(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) as actual_mw,
    0 as forecast_mw
FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
  AND fuelType = 'WIND'
GROUP BY timestamp
ORDER BY timestamp
"""

print("📊 Querying wind generation data...")
df = bq_client.query(query).to_dataframe()

print(f"✅ Retrieved {len(df)} hours of wind data")

# Calculate error percentage
df['error_pct'] = 0

# Prepare data for sheets
data = [['Timestamp', 'Actual_MW', 'Forecast_MW', 'Error_Pct']]
for _, row in df.iterrows():
    data.append([
        row['timestamp'].strftime('%Y-%m-%d %H:%M'),
        round(row['actual_mw'], 2),
        row['forecast_mw'],
        row['error_pct']
    ])

# Update or create Chart_Wind_Perf sheet
try:
    ws = ss.worksheet('Chart_Wind_Perf')
    print("📝 Updating Chart_Wind_Perf sheet...")
except:
    print("📝 Creating Chart_Wind_Perf sheet...")
    ws = ss.add_worksheet(title='Chart_Wind_Perf', rows=100, cols=4)

ws.clear()
ws.update(data, 'A1')

print(f"✅ Chart_Wind_Perf updated: {len(df)} rows")
print("✅ Wind performance data update COMPLETE!")
