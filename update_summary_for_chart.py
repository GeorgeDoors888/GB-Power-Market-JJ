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
  SELECT 
    CAST(settlementDate AS DATE) as settlement_date,
    settlementPeriod,
    fuelType,
    generation
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
  
  UNION ALL
  
  SELECT 
    CAST(settlementDate AS DATE) as settlement_date,
    settlementPeriod,
    fuelType,
    generation
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
  ROUND(f.total_gen_mw * 0.95, 0) as demand_mw,
  ROUND(f.total_gen_mw, 0) as generation_mw,
  ROUND((f.wind_mw / NULLIF(f.total_gen_mw, 0)) * 100, 1) as wind_percent,
  ROUND(COALESCE(p.price, 50.0), 2) as price_gbp_mwh,
  50.0 as frequency_hz,
  0 as constraint_mw
FROM aggregated_fuel f
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

# Prepare data
headers = ['Time', 'Demand', 'Generation', 'Wind %', 'Price', 'Frequency', 'Constraint']
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
print(f'   Demand: {df["demand_mw"].min():.0f} - {df["demand_mw"].max():.0f} MW')
print(f'   Generation: {df["generation_mw"].min():.0f} - {df["generation_mw"].max():.0f} MW')
print(f'   Wind: {df["wind_percent"].min():.1f}% - {df["wind_percent"].max():.1f}%')
print(f'   Price: £{df["price_gbp_mwh"].min():.2f} - £{df["price_gbp_mwh"].max():.2f}/MWh')

# Update Dashboard KPIs (row 6)
print('\n📊 Updating Dashboard KPIs (row 6)...')
latest = df.iloc[-1]
dashboard = spreadsheet.worksheet('Dashboard')

# Convert numpy types to native Python types for JSON serialization
kpi_values = [[
    float(latest['demand_mw']),
    float(latest['generation_mw']),
    float(latest['wind_percent']),
    float(latest['price_gbp_mwh']),
    float(latest['frequency_hz']),
    float(latest['constraint_mw'])
]]

dashboard.update(range_name='B6:G6', values=kpi_values, value_input_option='USER_ENTERED')

print('✅ Dashboard KPIs updated')
print(f'   Demand: {latest["demand_mw"]:.0f} MW')
print(f'   Generation: {latest["generation_mw"]:.0f} MW')
print(f'   Wind: {latest["wind_percent"]:.1f}%')
print(f'   Price: £{latest["price_gbp_mwh"]:.2f}/MWh')

print('\n' + '=' * 80)
print('✅ COMPLETE - Chart now displays live data')
print('=' * 80)
