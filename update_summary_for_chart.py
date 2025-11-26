#!/usr/bin/env python3
"""
Update Summary Sheet for Dashboard Chart
Queries BigQuery for time-series data and updates both Summary sheet and Dashboard KPIs
"""

import gspread
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd

SA_FILE = 'inner-cinema-credentials.json'
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
PROJECT_ID = "inner-cinema-476211-u9"

print('=' * 80)
print('UPDATING SUMMARY SHEET WITH TIME-SERIES DATA')
print('=' * 80)

# Authenticate
creds = service_account.Credentials.from_service_account_file(
    SA_FILE,
    scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/bigquery'
    ]
)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")

# Query TODAY'S settlement periods (00:00 to current time) - uses IRIS for today's data
print('\n🔍 Querying BigQuery for TODAY\'S settlement periods (00:00 onwards)...')
query = """
WITH fuel_data AS (
  -- Get latest generation value for each fuel type per settlement period
  SELECT 
    CAST(settlementDate AS DATE) as settlement_date,
    settlementPeriod,
    fuelType,
    generation,
    ROW_NUMBER() OVER (PARTITION BY CAST(settlementDate AS DATE), settlementPeriod, fuelType ORDER BY publishTime DESC) as rn
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
  
  UNION ALL
  
  SELECT 
    CAST(settlementDate AS DATE) as settlement_date,
    settlementPeriod,
    fuelType,
    generation,
    ROW_NUMBER() OVER (PARTITION BY CAST(settlementDate AS DATE), settlementPeriod, fuelType ORDER BY publishTime DESC) as rn
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
),
aggregated_fuel AS (
  SELECT 
    settlement_date,
    settlementPeriod,
    SUM(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) as wind_mw,
    SUM(generation) as total_gen_mw
  FROM fuel_data
  WHERE rn = 1  -- Take only the latest value for each fuel type
  GROUP BY settlement_date, settlementPeriod
),
demand_data AS (
  SELECT 
    CAST(settlementDate AS DATE) as settlement_date,
    settlementPeriod,
    AVG(demand) as demand_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indo_iris`
  WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
  GROUP BY settlement_date, settlementPeriod
),
price_data AS (
  SELECT 
    CAST(settlementDate AS DATE) as settlement_date,
    settlementPeriod,
    AVG(price) as price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
  WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    AND price IS NOT NULL
  GROUP BY settlement_date, settlementPeriod
)
SELECT 
  FORMAT_TIMESTAMP('%H:%M', 
    TIMESTAMP(CURRENT_DATE()) + INTERVAL ((f.settlementPeriod - 1) * 30) MINUTE
  ) as time_period,
  ROUND(COALESCE(d.demand_mw, f.total_gen_mw * 0.95) / 1000, 2) as demand_gw,
  ROUND(f.total_gen_mw / 1000, 2) as generation_gw,
  ROUND((f.wind_mw / NULLIF(f.total_gen_mw, 0)) * 100, 1) as wind_percent,
  ROUND(COALESCE(p.price, 50.0), 2) as price_gbp_mwh,
  50.0 as frequency_hz,
  0 as constraint_mw
FROM aggregated_fuel f
LEFT JOIN demand_data d
  ON f.settlement_date = d.settlement_date
  AND f.settlementPeriod = d.settlementPeriod
LEFT JOIN price_data p 
  ON f.settlement_date = p.settlement_date 
  AND f.settlementPeriod = p.settlementPeriod
WHERE f.total_gen_mw IS NOT NULL
ORDER BY f.settlementPeriod ASC
"""

df = bq_client.query(query).to_dataframe()

if len(df) == 0:
    print('❌ No data returned')
    exit(1)

print(f'✅ Retrieved {len(df)} periods')

# Prepare data with clear labels
headers = ['Time', 'Demand (GW)', 'Generation (GW)', 'Wind %', 'Price (£/MWh)', 'Frequency (Hz)', 'Constraint']
values = [headers] + df.values.tolist()

# Update Summary sheet
print('\n📝 Updating Summary sheet...')
try:
    summary = spreadsheet.worksheet('Summary')
    print('   Found existing Summary sheet')
except:
    print('   Creating new Summary sheet')
    summary = spreadsheet.add_worksheet(title='Summary', rows=100, cols=10)

summary.clear()
summary.update('A1', values, value_input_option='USER_ENTERED')

print(f'✅ Summary sheet updated ({len(df)} periods)')
print(f'   Demand: {df["demand_gw"].min():.2f} - {df["demand_gw"].max():.2f} GW')
print(f'   Generation: {df["generation_gw"].min():.2f} - {df["generation_gw"].max():.2f} GW')
print(f'   Wind: {df["wind_percent"].min():.1f}% - {df["wind_percent"].max():.1f}%')
print(f'   Price: £{df["price_gbp_mwh"].min():.2f} - £{df["price_gbp_mwh"].max():.2f}/MWh')

# Update Dashboard row 5 summary and row 6 KPIs
print('\n📊 Updating Dashboard rows 5-6...')
latest = df.iloc[-1]
dashboard = spreadsheet.worksheet('Dashboard')

# Calculate current SP
from datetime import datetime
now = datetime.now()
sp = (now.hour * 2) + (1 if now.minute < 30 else 2)

# Row 5: Human-readable summary
summary_text = f'Total Generation: {latest["generation_gw"]:.1f} GW | Demand: {latest["demand_gw"]:.1f} GW | Wind: {latest["wind_percent"]:.0f}% | 💰 Market Price: £{latest["price_gbp_mwh"]:.2f}/MWh (SP{sp}, {now.strftime("%H:%M")})'
dashboard.update(range_name='A5', values=[[summary_text]], value_input_option='USER_ENTERED')

# Row 6 labels (A6)
dashboard.update(range_name='A6', values=[['📊 Current:']], value_input_option='USER_ENTERED')

# Row 6: Labeled KPI values (B6:G6) with headers
kpi_with_labels = [[
    f'Demand: {float(latest["demand_gw"]):.2f} GW',
    f'Generation: {float(latest["generation_gw"]):.2f} GW',
    f'Wind: {float(latest["wind_percent"]):.0f}%',
    f'Price: £{float(latest["price_gbp_mwh"]):.2f}/MWh',
    f'Frequency: {float(latest["frequency_hz"]):.2f} Hz',
    f'Constraint: {float(latest["constraint_mw"]):.0f} MW'
]]

dashboard.update(range_name='B6:G6', values=kpi_with_labels, value_input_option='USER_ENTERED')

print('✅ Dashboard rows 5-6 updated')
print(f'   Row 5: {summary_text}')
print(f'   Row 6: Demand {latest["demand_gw"]:.2f} GW, Generation {latest["generation_gw"]:.2f} GW, Wind {latest["wind_percent"]:.1f}%, Price £{latest["price_gbp_mwh"]:.2f}/MWh')

print('\n' + '=' * 80)
print('✅ COMPLETE - Chart now displays live data')
print('=' * 80)
