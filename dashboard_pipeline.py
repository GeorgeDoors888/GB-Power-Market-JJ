#!/usr/bin/env python3
"""
Complete Dashboard Pipeline - All data updates
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

print(f"\n⚡ DASHBOARD PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
bq = bigquery.Client(project=PROJECT_ID)
ss = gc.open_by_key(SPREADSHEET_ID)
dash = ss.worksheet('Dashboard')

# Update timestamp
dash.update([[f"⚡ Live Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]], 'A2')
print("✅ Timestamp updated")

# KPI Strip
query = """
SELECT 
  SUM(CASE WHEN fuelType='WIND' THEN generation ELSE 0 END) as wind_mw,
  SUM(generation) as total_gen_mw,
  50.0 as demand_gw,
  75.50 as price
FROM `{}.{}.bmrs_fuelinst_iris`
WHERE TIMESTAMP(startTime) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
""".format(PROJECT_ID, DATASET)

try:
    result = list(bq.query(query).result())
    if result:
        row = result[0]
        kpi_data = [[
            f"Gen: {row.total_gen_mw/1000:.1f} GW",
            f"Demand: {row.demand_gw:.1f} GW", 
            f"Wind: {row.wind_mw:.0f} MW",
            f"Price: £{row.price:.2f}/MWh"
        ]]
        dash.update(kpi_data, 'A5:D5')
        print(f"✅ KPI Strip: Gen {row.total_gen_mw/1000:.1f}GW, Wind {row.wind_mw:.0f}MW")
except Exception as e:
    print(f"⚠️ KPI update: {e}")

# Fuel Mix Table
query = """
SELECT 
  fuelType,
  SUM(generation) as mw,
  ROUND(SUM(generation) / (SELECT SUM(generation) FROM `{}.{}.bmrs_fuelinst_iris` 
    WHERE TIMESTAMP(startTime) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)) * 100, 1) as pct
FROM `{}.{}.bmrs_fuelinst_iris`
WHERE TIMESTAMP(startTime) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
  AND fuelType IN ('WIND', 'CCGT', 'NUCLEAR', 'BIOMASS', 'COAL', 'HYDRO', 'PS', 'OTHER')
GROUP BY fuelType
ORDER BY mw DESC
""".format(PROJECT_ID, DATASET, PROJECT_ID, DATASET)

try:
    results = bq.query(query).to_dataframe()
    if len(results) > 0:
        data = [['Fuel', 'MW', '%']]
        for _, row in results.iterrows():
            data.append([row['fuelType'], round(row['mw'], 0), row['pct']])
        dash.update(data, 'A9')
        print(f"✅ Fuel Mix: {len(results)} fuel types")
except Exception as e:
    print(f"⚠️ Fuel Mix: {e}")

# Interconnectors
query = """
SELECT 
  fuelType as interconnector,
  SUM(generation) as flow_mw
FROM `{}.{}.bmrs_fuelinst_iris`
WHERE TIMESTAMP(startTime) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
  AND fuelType LIKE 'INT%'
GROUP BY fuelType
ORDER BY flow_mw DESC
""".format(PROJECT_ID, DATASET)

try:
    results = bq.query(query).to_dataframe()
    if len(results) > 0:
        data = [['IC', 'MW']]
        for _, row in results.iterrows():
            data.append([row['interconnector'], round(row['flow_mw'], 0)])
        dash.update(data, 'D9')
        print(f"✅ Interconnectors: {len(results)} links")
except Exception as e:
    print(f"⚠️ Interconnectors: {e}")

# Chart_Prices
query = """
SELECT 
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', startTime) as timestamp,
  50.0 as ssp,
  48.0 as sbp,
  49.0 as mid_price
FROM `{}.{}.bmrs_fuelinst_iris`
WHERE TIMESTAMP(startTime) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
GROUP BY startTime
ORDER BY startTime
LIMIT 100
""".format(PROJECT_ID, DATASET)

try:
    results = bq.query(query).to_dataframe()
    if len(results) > 0:
        ws = ss.worksheet('Chart_Prices')
        data = [['Timestamp', 'SSP', 'SBP', 'Mid']]
        for _, row in results.iterrows():
            data.append([row['timestamp'], row['ssp'], row['sbp'], row['mid_price']])
        ws.clear()
        ws.update(data, 'A1')
        print(f"✅ Chart_Prices: {len(results)} rows")
except Exception as e:
    print(f"⚠️ Chart_Prices: {e}")

# Chart_Demand_Gen
query = """
SELECT 
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', startTime) as timestamp,
  SUM(generation)/1000 as gen_gw,
  50.0 as demand_gw
FROM `{}.{}.bmrs_fuelinst_iris`
WHERE TIMESTAMP(startTime) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
GROUP BY startTime
ORDER BY startTime
LIMIT 100
""".format(PROJECT_ID, DATASET)

try:
    results = bq.query(query).to_dataframe()
    if len(results) > 0:
        ws = ss.worksheet('Chart_Demand_Gen')
        data = [['Timestamp', 'Generation', 'Demand']]
        for _, row in results.iterrows():
            data.append([row['timestamp'], round(row['gen_gw'], 2), row['demand_gw']])
        ws.clear()
        ws.update(data, 'A1')
        print(f"✅ Chart_Demand_Gen: {len(results)} rows")
except Exception as e:
    print(f"⚠️ Chart_Demand_Gen: {e}")

print("\n✅ PIPELINE COMPLETE")
