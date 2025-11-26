#!/usr/bin/env python3
"""Quick check of Battery Revenue Analysis data"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from google.oauth2 import service_account

# Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json', scope
)
client = gspread.authorize(credentials)
sheet = client.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
battery_sheet = sheet.worksheet('Battery Revenue Analysis')

print('='*70)
print('BATTERY REVENUE ANALYSIS - CURRENT DATA')
print('='*70)
print()

print('📊 KPIs (Row 2):')
kpis = battery_sheet.row_values(2)
for i, kpi in enumerate(kpis[:4]):
    print(f'  Column {chr(65+i)}: {kpi}')
print()

print('📋 TODAY\'S ACCEPTANCES - Headers:')
headers = battery_sheet.row_values(4)
for i, h in enumerate(headers[:11]):
    print(f'  {chr(65+i)}: {h}')
print()

print('📋 Sample Data (Rows 5-7):')
sample = battery_sheet.get('A5:K7')
for row_num, row in enumerate(sample, start=5):
    print(f'\n  Row {row_num}:')
    for col_num, val in enumerate(row):
        print(f'    {chr(65+col_num)}: {val}')
print()

print('='*70)
print('CHECKING BIGQUERY SOURCE DATA')
print('='*70)

# BigQuery
credentials_bq = service_account.Credentials.from_service_account_file(
    '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json',
    scopes=["https://www.googleapis.com/auth/bigquery"]
)
client_bq = bigquery.Client(
    project="inner-cinema-476211-u9", 
    location="US",
    credentials=credentials_bq
)

# Check today's acceptances with pricing
query = """
SELECT 
  acceptanceTime,
  bmUnit,
  levelFrom,
  levelTo,
  (levelTo - levelFrom) as volume_mw,
  m.price as market_price,
  m.volume as market_volume,
  -- Revenue calc
  CASE 
    WHEN (levelTo - levelFrom) > 0 THEN (levelTo - levelFrom) * m.price / 2
    WHEN (levelTo - levelFrom) < 0 THEN (levelTo - levelFrom) * m.price / 2
    ELSE 0
  END as estimated_value
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris` a
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris` m
  ON CAST(a.settlementDate AS DATE) = CAST(m.settlementDate AS DATE)
  AND a.settlementPeriodFrom = m.settlementPeriod
WHERE CAST(a.settlementDate AS DATE) = CURRENT_DATE()
  AND bmUnit = 'FBPGM002'
ORDER BY acceptanceTime DESC
LIMIT 3
"""

print('\n🔋 Sample FBPGM002 Acceptances Today:')
df = client_bq.query(query).to_dataframe()
print(df.to_string())
print()

# Check what bmrs_mid_iris.price actually represents
query2 = """
SELECT 
  settlementDate,
  settlementPeriod,
  dataProvider,
  price,
  volume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
ORDER BY settlementPeriod DESC
LIMIT 5
"""

print('\n💷 bmrs_mid_iris Price Data (Last 5 periods):')
df2 = client_bq.query(query2).to_dataframe()
print(df2.to_string())
print()

# Check if systemSellPrice exists anywhere
query3 = """
SELECT column_name, data_type
FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'bmrs_mid_iris'
ORDER BY ordinal_position
"""

print('\n📋 bmrs_mid_iris Full Schema:')
df3 = client_bq.query(query3).to_dataframe()
print(df3.to_string())
print()

# Check indicated_imbalance table
query4 = """
SELECT *
FROM `inner-cinema-476211-u9.uk_energy_prod.indicated_imbalance`
WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
ORDER BY settlementPeriod DESC
LIMIT 5
"""

print('\n⚡ indicated_imbalance Data (Alternative pricing source):')
try:
    df4 = client_bq.query(query4).to_dataframe()
    print(df4.to_string())
except Exception as e:
    print(f'  Error: {e}')
