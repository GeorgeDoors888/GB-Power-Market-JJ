#!/usr/bin/env python3
"""
BM Costs Data Update - Populate Chart_BM_Costs sheet
Queries bmrs_costs for system balance costs
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

print("\n💷 BM COSTS DATA UPDATE")
print("=" * 60)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID)

ss = gc.open_by_key(SPREADSHEET_ID)

# Query BM costs
query = f"""
SELECT
    TIMESTAMP_TRUNC(startTime, HOUR) as timestamp,
    SUM(totalAcceptedOfferVolume * systemSellPrice) as offer_cost,
    SUM(totalAcceptedBidVolume * systemBuyPrice) as bid_cost,
    SUM((totalAcceptedOfferVolume * systemSellPrice) + (totalAcceptedBidVolume * systemBuyPrice)) as total_cost
FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
WHERE CAST(startTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 720 HOUR)
GROUP BY timestamp
ORDER BY timestamp
"""

print("📊 Querying BM costs data...")
df = bq_client.query(query).to_dataframe()

print(f"✅ Retrieved {len(df)} hours of BM cost data")

# Prepare data for sheets
data = [['Timestamp', 'Actions', 'BOA', 'BOD']]
for _, row in df.iterrows():
    data.append([
        row['timestamp'].strftime('%Y-%m-%d %H:%M'),
        round(row['total_cost'], 2),
        round(row['offer_cost'], 2),
        round(row['bid_cost'], 2)
    ])

# Update or create Chart_BM_Costs sheet
try:
    ws = ss.worksheet('Chart_BM_Costs')
    print("📝 Updating Chart_BM_Costs sheet...")
except:
    print("📝 Creating Chart_BM_Costs sheet...")
    ws = ss.add_worksheet(title='Chart_BM_Costs', rows=100, cols=4)

ws.clear()
ws.update(data, 'A1')

print(f"✅ Chart_BM_Costs updated: {len(df)} rows")
print("✅ BM costs data update COMPLETE!")
