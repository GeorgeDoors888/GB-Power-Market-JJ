#!/usr/bin/env python3
"""
Update Sheet1 with Latest Day Chart and Analysis Sheet References
Adds:
1. Latest Day Settlement Period Chart (with power station warnings)
2. Links to the 3 analysis sheets: Latest Day Data, Analysis BI Enhanced, Grid Frequency
"""

from google.cloud import bigquery
from googleapiclient.discovery import build
import pickle
from datetime import datetime, timedelta
import pandas as pd

print("=" * 80)
print("📊 UPDATING SHEET1 WITH CHART & ANALYSIS LINKS")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET1_NAME = 'Sheet1'
DATA_SHEET_NAME = 'Latest Day Data'

# ============================================================================
# STEP 1: QUERY BIGQUERY FOR LATEST DAY DATA
# ============================================================================

print("=" * 80)
print("1️⃣  QUERYING BIGQUERY FOR LATEST DAY")
print("=" * 80)

bq_client = bigquery.Client(project=PROJECT_ID)

# Query for latest day settlement period data with warnings
query = """
WITH latest_date AS (
  SELECT MAX(DATE(settlementDate)) as max_date
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indo`
),

-- Get demand data for latest day
demand_data AS (
  SELECT
    DATE(settlementDate) as date,
    settlementPeriod,
    FORMAT_TIME('%H:%M', TIME(TIMESTAMP_ADD(TIMESTAMP('2000-01-01 00:00:00'), 
      INTERVAL (settlementPeriod - 1) * 30 MINUTE))) as time,
    ROUND(AVG(demand), 2) as demand_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indo`
  WHERE DATE(settlementDate) = (SELECT max_date FROM latest_date)
  GROUP BY date, settlementPeriod
),

-- Get wind generation for latest day
wind_data AS (
  SELECT
    DATE(publishTime) as date,
    settlementPeriod,
    ROUND(AVG(generation), 2) as wind_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE fuelType = 'WIND'
    AND DATE(publishTime) = (SELECT max_date FROM latest_date)
  GROUP BY date, settlementPeriod
),

-- Get expected wind (using demand as proxy - simplified)
expected_wind AS (
  SELECT
    settlementPeriod,
    ROUND(AVG(demand) * 0.35, 2) as expected_wind_mw  -- 35% of demand as typical wind
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indo`
  WHERE DATE(settlementDate) = (SELECT max_date FROM latest_date)
  GROUP BY settlementPeriod
),

-- Get System Sell Price (SSP) from bmrs_mid
price_data AS (
  SELECT
    DATE(settlementDate) as date,
    settlementPeriod,
    ROUND(AVG(price), 2) as ssp_gbp_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE DATE(settlementDate) = (SELECT max_date FROM latest_date)
  GROUP BY date, settlementPeriod
)

-- Combine all data
SELECT
  d.settlementPeriod,
  d.time,
  d.demand_mw,
  w.wind_mw,
  e.expected_wind_mw,
  COALESCE(p.ssp_gbp_mwh, 0.0) as ssp_gbp_mwh,
  d.date as data_date,
  -- Calculate days old
  DATE_DIFF(CURRENT_DATE(), d.date, DAY) as days_old
FROM demand_data d
LEFT JOIN wind_data w ON d.settlementPeriod = w.settlementPeriod
LEFT JOIN expected_wind e ON d.settlementPeriod = e.settlementPeriod
LEFT JOIN price_data p ON d.settlementPeriod = p.settlementPeriod
ORDER BY d.settlementPeriod
"""

print("🔍 Executing query...")
df = bq_client.query(query).to_dataframe()

print(f"✅ Retrieved {len(df)} settlement periods")
print(f"📅 Latest date: {df['data_date'].iloc[0] if len(df) > 0 else 'N/A'}")
print(f"⏰ Data age: {df['days_old'].iloc[0] if len(df) > 0 else 'N/A'} days old")
print()

# ============================================================================
# STEP 2: ANALYZE FOR WARNINGS
# ============================================================================

print("=" * 80)
print("2️⃣  ANALYZING FOR SYSTEM WARNINGS")
print("=" * 80)

warnings = []

if len(df) > 0:
    # Check for high prices (power station outages)
    high_price_threshold = 80  # £80/MWh
    extreme_price_threshold = 150  # £150/MWh (likely outages)
    high_prices = df[df['ssp_gbp_mwh'] > high_price_threshold]
    extreme_prices = df[df['ssp_gbp_mwh'] > extreme_price_threshold]
    
    if len(extreme_prices) > 0:
        max_price = df['ssp_gbp_mwh'].max()
        periods = ', '.join([str(p) for p in extreme_prices['settlementPeriod'].head(3)])
        warnings.append(f"🔴 EXTREME PRICES: £{max_price:.2f}/MWh in periods {periods} - Likely power station outages!")
    elif len(high_prices) > 0:
        max_price = df['ssp_gbp_mwh'].max()
        warnings.append(f"🟡 High prices: £{max_price:.2f}/MWh - Elevated system costs")
    
    # Check for negative prices (excess renewables)
    negative_prices = df[df['ssp_gbp_mwh'] < 0]
    if len(negative_prices) > 0:
        min_price = df['ssp_gbp_mwh'].min()
        warnings.append(f"🟢 Negative prices: £{min_price:.2f}/MWh - Excess renewable generation")
    
    # Check for wind shortfall
    wind_shortfall = df[df['wind_mw'] < (df['expected_wind_mw'] - 5000)]
    if len(wind_shortfall) > 0:
        warnings.append(f"💨 Wind shortfall detected: {len(wind_shortfall)} periods below expected")
    
    # Check for missing price data
    zero_prices = df[df['ssp_gbp_mwh'] == 0]
    if len(zero_prices) > 5:  # More than 5 periods with zero price
        warnings.append(f"⚠️ Price data incomplete: {len(zero_prices)}/48 periods missing (bmrs_mid table lag)")
    
    # Data age warning
    days_old = df['days_old'].iloc[0]
    if days_old > 0:
        warnings.append(f"📅 Data is {days_old} day(s) old (today is {datetime.now().strftime('%Y-%m-%d')})")

print(f"Found {len(warnings)} warnings:")
for w in warnings:
    print(f"  {w}")
print()

# ============================================================================
# STEP 3: LOAD GOOGLE SHEETS CREDENTIALS
# ============================================================================

print("=" * 80)
print("3️⃣  CONNECTING TO GOOGLE SHEETS")
print("=" * 80)

try:
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    service = build('sheets', 'v4', credentials=creds)
    print("✅ Connected to Google Sheets API")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# ============================================================================
# STEP 4: WRITE DATA TO "Latest Day Data" SHEET
# ============================================================================

print()
print("=" * 80)
print("4️⃣  WRITING DATA TO 'Latest Day Data' SHEET")
print("=" * 80)

# Prepare data for sheets
sheet_data = [
    ['Settlement Period', 'Time', 'Demand (MW)', 'Wind (MW)', 'Expected Wind (MW)', 'SSP (£/MWh)', 'Date', 'Days Old']
]

for _, row in df.iterrows():
    sheet_data.append([
        int(row['settlementPeriod']),
        row['time'],
        float(row['demand_mw']),
        float(row['wind_mw']) if pd.notna(row['wind_mw']) else 0.0,
        float(row['expected_wind_mw']) if pd.notna(row['expected_wind_mw']) else 0.0,
        float(row['ssp_gbp_mwh']),
        str(row['data_date']),
        int(row['days_old'])
    ])

# Write to Latest Day Data sheet
try:
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{DATA_SHEET_NAME}!A1:H{len(sheet_data)}',
        valueInputOption='RAW',
        body={'values': sheet_data}
    ).execute()
    print(f"✅ Wrote {len(sheet_data)-1} rows to '{DATA_SHEET_NAME}' sheet")
except Exception as e:
    print(f"❌ Error writing data: {e}")

# ============================================================================
# STEP 5: WRITE ANALYSIS LINKS TO SHEET1
# ============================================================================

print()
print("=" * 80)
print("5️⃣  ADDING ANALYSIS LINKS TO SHEET1")
print("=" * 80)

# Create analysis dashboard section for Sheet1
analysis_section = [
    [''],
    ['=== 📊 ANALYSIS DASHBOARDS ==='],
    [''],
    ['Latest Day Chart', '👇 See chart below (Row 18)'],
    [''],
    ['📈 Latest Day Data', '=HYPERLINK("#gid=1719763364", "View Settlement Period Data →")'],
    ['📊 Analysis BI Enhanced', '=HYPERLINK("#gid=288644183", "View Enhanced BI Analysis →")'],
    ['⚡ Grid Frequency', '=HYPERLINK("#gid=1877467239", "View Real-time Frequency →")'],
    [''],
    ['=== ⚠️ SYSTEM WARNINGS ==='],
    ['']
]

# Add warnings
for warning in warnings:
    analysis_section.append([warning])

# Write to Sheet1 starting at row 1
try:
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET1_NAME}!A1:D{len(analysis_section)}',
        valueInputOption='USER_ENTERED',  # USER_ENTERED to process formulas
        body={'values': analysis_section}
    ).execute()
    print(f"✅ Added analysis links and warnings to '{SHEET1_NAME}'")
except Exception as e:
    print(f"❌ Error writing analysis section: {e}")

# ============================================================================
# STEP 6: CREATE CHART IN SHEET1
# ============================================================================

print()
print("=" * 80)
print("6️⃣  CREATING CHART IN SHEET1")
print("=" * 80)

# Get sheet IDs
spreadsheet_info = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet1_id = None
data_sheet_id = None

for sheet in spreadsheet_info.get('sheets', []):
    title = sheet['properties']['title']
    if title == SHEET1_NAME:
        sheet1_id = sheet['properties']['sheetId']
    elif title == DATA_SHEET_NAME:
        data_sheet_id = sheet['properties']['sheetId']

if not sheet1_id or not data_sheet_id:
    print(f"❌ Error: Could not find required sheets")
    exit(1)

print(f"✅ Sheet1 ID: {sheet1_id}")
print(f"✅ Data sheet ID: {data_sheet_id}")

# Delete any existing charts in Sheet1 first
print("🗑️  Removing old charts...")
try:
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    delete_requests = []
    
    for sheet in spreadsheet.get('sheets', []):
        if sheet['properties']['title'] == SHEET1_NAME:
            for chart in sheet.get('charts', []):
                delete_requests.append({
                    'deleteEmbeddedObject': {
                        'objectId': chart['chartId']
                    }
                })
    
    if delete_requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': delete_requests}
        ).execute()
        print(f"✅ Deleted {len(delete_requests)} old chart(s)")
except Exception as e:
    print(f"⚠️  Could not delete old charts: {e}")

# Create new chart
chart_request = {
    'addChart': {
        'chart': {
            'spec': {
                'title': f'Latest Day Settlement Periods - {df["data_date"].iloc[0] if len(df) > 0 else "N/A"}',
                'basicChart': {
                    'chartType': 'COMBO',
                    'legendPosition': 'RIGHT_LEGEND',
                    'axis': [
                        {
                            'position': 'BOTTOM_AXIS',
                            'title': 'Time'
                        },
                        {
                            'position': 'LEFT_AXIS',
                            'title': 'MW / £/MWh'
                        }
                    ],
                    'series': [
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': len(df) + 1,
                                        'startColumnIndex': 2,
                                        'endColumnIndex': 3
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'LINE',
                            'lineStyle': {
                                'width': 2
                            },
                            'color': {'red': 0.2, 'green': 0.5, 'blue': 0.9}
                        },
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': len(df) + 1,
                                        'startColumnIndex': 3,
                                        'endColumnIndex': 4
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'LINE',
                            'lineStyle': {
                                'width': 2
                            },
                            'color': {'red': 0.1, 'green': 0.7, 'blue': 0.3}
                        },
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': len(df) + 1,
                                        'startColumnIndex': 4,
                                        'endColumnIndex': 5
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'LINE',
                            'lineStyle': {
                                'width': 1,
                                'type': 'DASHED'
                            },
                            'color': {'red': 0.7, 'green': 0.7, 'blue': 0.7}
                        },
                        {
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': len(df) + 1,
                                        'startColumnIndex': 5,
                                        'endColumnIndex': 6
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'type': 'COLUMN',
                            'color': {'red': 1.0, 'green': 0.6, 'blue': 0.0}
                        }
                    ],
                    'headerCount': 1,
                    'domains': [{
                        'domain': {
                            'sourceRange': {
                                'sources': [{
                                    'sheetId': data_sheet_id,
                                    'startRowIndex': 1,
                                    'endRowIndex': len(df) + 1,
                                    'startColumnIndex': 1,
                                    'endColumnIndex': 2
                                }]
                            }
                        }
                    }]
                }
            },
            'position': {
                'overlayPosition': {
                    'anchorCell': {
                        'sheetId': sheet1_id,
                        'rowIndex': 17,  # Row 18 (0-indexed)
                        'columnIndex': 0  # Column A
                    }
                }
            }
        }
    }
}

try:
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [chart_request]}
    ).execute()
    print("✅ Chart created in Sheet1 at row 18")
except Exception as e:
    print(f"❌ Error creating chart: {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print()
print("=" * 80)
print("✅ COMPLETE")
print("=" * 80)
print()
print(f"📊 Updated Sheet1 with:")
print(f"   • Analysis dashboard links (rows 1-8)")
print(f"   • {len(warnings)} system warnings (rows 10+)")
print(f"   • Latest day chart (row 18)")
print()
print(f"📈 Data written to '{DATA_SHEET_NAME}' sheet:")
print(f"   • {len(df)} settlement periods")
print(f"   • Date: {df['data_date'].iloc[0] if len(df) > 0 else 'N/A'}")
print(f"   • Age: {df['days_old'].iloc[0] if len(df) > 0 else 'N/A'} days old")
print()
print(f"🔗 View spreadsheet:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
print()
print("=" * 80)
