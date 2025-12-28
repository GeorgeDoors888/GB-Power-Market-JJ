#!/usr/bin/env python3
"""
System Frequency Data Update - Populate Chart_Frequency sheet
Queries bmrs_freq_iris for system frequency data
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

print("\n⚡ SYSTEM FREQUENCY DATA UPDATE")
print("=" * 60)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID)

ss = gc.open_by_key(SPREADSHEET_ID)

# Query frequency data
query = f"""
SELECT
    TIMESTAMP_TRUNC(CAST(measurementTime AS TIMESTAMP), MINUTE) as timestamp,
    AVG(frequency) as frequency_hz
FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
WHERE CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY timestamp
ORDER BY timestamp
"""

print("📊 Querying system frequency data...")
df = bq_client.query(query).to_dataframe()

print(f"✅ Retrieved {len(df)} minutes of frequency data")

# Prepare data for sheets
data = [['Timestamp', 'Frequency_Hz']]
for _, row in df.iterrows():
    data.append([
        row['timestamp'].strftime('%Y-%m-%d %H:%M'),
        round(row['frequency_hz'], 3)
    ])

# Update or create Chart_Frequency sheet
try:
    ws = ss.worksheet('Chart_Frequency')
    print("�� Updating Chart_Frequency sheet...")
except:
    print("📝 Creating Chart_Frequency sheet...")
    ws = ss.add_worksheet(title='Chart_Frequency', rows=2000, cols=2)

ws.clear()
ws.update(data, 'A1')

print(f"✅ Chart_Frequency updated: {len(df)} rows")
print("✅ Frequency data update COMPLETE!")
