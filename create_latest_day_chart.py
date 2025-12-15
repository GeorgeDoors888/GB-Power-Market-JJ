#!/usr/bin/env python3
"""
Latest Day Settlement Period Analysis
1. Query BigQuery for latest day's data (demand, wind, expected wind, SSP)
2. Write to Google Sheets (Sheet1 A18:H31)
3. Create chart automatically
"""

from google.cloud import bigquery
from googleapiclient.discovery import build
import pickle
from datetime import datetime, timedelta
import pandas as pd

print("=" * 80)
print("📊 LATEST DAY SETTLEMENT PERIOD ANALYSIS")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
DATA_SHEET_NAME = 'Latest Day Data'  # Sheet for data
CHART_SHEET_NAME = 'Sheet1'  # Sheet for chart
WRITE_RANGE = 'Latest Day Data!A1:H5000'  # Write to separate sheet

# ============================================================================
# STEP 1: QUERY BIGQUERY FOR LATEST DAY DATA
# ============================================================================

print("=" * 80)
print("1️⃣  QUERYING BIGQUERY")
print("=" * 80)

bq_client = bigquery.Client(project=PROJECT_ID)

# Query to get latest day's settlement period data
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
      INTERVAL (settlementPeriod - 1) * 30 MINUTE))) as time_label,
    ROUND(CAST(demand AS FLOAT64) / 1000, 2) as demand_gw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indo`
  CROSS JOIN latest_date
  WHERE DATE(settlementDate) = latest_date.max_date
    AND settlementPeriod BETWEEN 1 AND 48
),

-- Get wind generation for latest day
wind_data AS (
  SELECT
    DATE(settlementDate) as date,
    settlementPeriod,
    ROUND(SUM(CASE WHEN UPPER(fuelType) = 'WIND' THEN CAST(generation AS FLOAT64) ELSE 0 END) / 1000, 2) as wind_gw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  CROSS JOIN latest_date
  WHERE DATE(settlementDate) = latest_date.max_date
    AND settlementPeriod BETWEEN 1 AND 48
  GROUP BY date, settlementPeriod
),

-- Get wind forecast for latest day (using actual wind * 1.1 as estimate)
-- Replace with actual forecast table if available
wind_forecast AS (
  SELECT
    DATE(settlementDate) as date,
    settlementPeriod,
    ROUND(SUM(CASE WHEN UPPER(fuelType) = 'WIND' THEN CAST(generation AS FLOAT64) ELSE 0 END) / 1000 * 1.1, 2) as expected_wind_gw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  CROSS JOIN latest_date
  WHERE DATE(settlementDate) = latest_date.max_date
    AND settlementPeriod BETWEEN 1 AND 48
  GROUP BY date, settlementPeriod
),

-- Get System Sell Price (SSP) for latest day  
-- Using bmrs_mid (Market Index Data) for actual system prices
ssp_data AS (
  SELECT
    DATE(settlementDate) as date,
    settlementPeriod,
    ROUND(AVG(CAST(price AS FLOAT64)), 2) as ssp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  CROSS JOIN latest_date
  WHERE DATE(settlementDate) = latest_date.max_date
    AND settlementPeriod BETWEEN 1 AND 48
  GROUP BY date, settlementPeriod
)

-- Combine all data (limit to 48 settlement periods for 1 day)
SELECT
  d.date,
  d.settlementPeriod,
  d.time_label,
  d.demand_gw,
  COALESCE(w.wind_gw, 0) as wind_gw,
  COALESCE(wf.expected_wind_gw, 0) as expected_wind_gw,
  COALESCE(s.ssp, 0) as ssp,
  d.date as latest_date
FROM demand_data d
LEFT JOIN wind_data w ON d.date = w.date AND d.settlementPeriod = w.settlementPeriod
LEFT JOIN wind_forecast wf ON d.date = wf.date AND d.settlementPeriod = wf.settlementPeriod
LEFT JOIN ssp_data s ON d.date = s.date AND d.settlementPeriod = s.settlementPeriod
ORDER BY d.settlementPeriod
LIMIT 48
"""

print("📊 Querying for latest day's settlement period data...")
print("   Tables: bmrs_indo (demand), bmrs_fuelinst (generation), bmrs_mid (prices)")
print("   Metrics: Demand (GW), Wind (GW), Expected Wind (GW), SSP (£/MWh)")
print("   ⚠️  Note: Limited by slowest-updating table (bmrs_indo)")
print()

try:
    df = bq_client.query(query).to_dataframe()
    
    if df.empty:
        print("❌ No data returned from BigQuery")
        print("   Check that tables have recent data")
        exit(1)
    
    print(f"✅ Retrieved {len(df)} settlement periods")
    
    if len(df) > 0:
        latest_date = df['latest_date'].iloc[0]
        print(f"📅 Latest date: {latest_date}")
        
        # Warning if data is not from today
        from datetime import date
        today = date.today()
        if str(latest_date) != str(today):
            days_old = (today - latest_date).days
            print(f"⚠️  WARNING: Data is {days_old} day(s) old (today is {today})")
            print(f"   Latest available: {latest_date}")
        
        print()
        print("📊 Data summary:")
        print(f"   Demand: {df['demand_gw'].min():.2f} - {df['demand_gw'].max():.2f} GW")
        print(f"   Wind: {df['wind_gw'].min():.2f} - {df['wind_gw'].max():.2f} GW")
        print(f"   Expected Wind: {df['expected_wind_gw'].min():.2f} - {df['expected_wind_gw'].max():.2f} GW")
        print(f"   SSP: £{df['ssp'].min():.2f} - £{df['ssp'].max():.2f}/MWh")
        
        if len(df) != 48:
            print()
            print(f"⚠️  Expected 48 settlement periods but got {len(df)}")
        
        # System warnings analysis
        print()
        print("=" * 80)
        print("⚠️  SYSTEM WARNINGS & ALERTS")
        print("=" * 80)
        
        warnings = []
        
        # Check for missing price data
        missing_prices = df[df['ssp'] == 0].shape[0]
        if missing_prices > 40:
            print(f"⚠️  Price data incomplete: {missing_prices}/48 periods missing (bmrs_mid table lag)")
            print(f"   Power station outage warnings may be inaccurate")
            print()
        
        # 1. High price alert (capacity shortage indicator)
        high_price_threshold = 80  # £80/MWh (typical high)
        high_prices = df[df['ssp'] > high_price_threshold]
        if len(high_prices) > 0:
            max_price_row = df.loc[df['ssp'].idxmax()]
            warnings.append(f"� HIGH PRICES: {len(high_prices)} periods above £{high_price_threshold}/MWh (Peak: £{max_price_row['ssp']:.2f} at {max_price_row['time_label']})")
        
        # 2. Extremely high price (system stress / outages)
        extreme_price_threshold = 150  # £150/MWh indicates serious issues
        extreme_prices = df[df['ssp'] > extreme_price_threshold]
        if len(extreme_prices) > 0:
            warnings.append(f"🔴 EXTREME PRICES: {len(extreme_prices)} periods above £{extreme_price_threshold}/MWh - POWER STATION OUTAGES OR CAPACITY SHORTAGE")
        
        # 2b. Negative prices (excess wind)
        negative_prices = df[df['ssp'] < 0]
        if len(negative_prices) > 0:
            min_price_row = df.loc[df['ssp'].idxmin()]
            warnings.append(f"🟢 NEGATIVE PRICES: {len(negative_prices)} periods (Min: £{min_price_row['ssp']:.2f} at {min_price_row['time_label']}) - Excess renewable generation")
        
        # 3. Low wind vs expected (curtailment or forecast error)
        df['wind_shortfall'] = df['expected_wind_gw'] - df['wind_gw']
        significant_shortfall = df[df['wind_shortfall'] > 5]  # >5GW difference
        if len(significant_shortfall) > 0:
            max_shortfall = df['wind_shortfall'].max()
            warnings.append(f"🟡 WIND SHORTFALL: Actual wind {max_shortfall:.1f}GW below expected (possible curtailment or forecast error)")
        
        # 4. High demand (system stress)
        high_demand_threshold = 30  # 30GW
        high_demand = df[df['demand_gw'] > high_demand_threshold]
        if len(high_demand) > 0:
            max_demand_row = df.loc[df['demand_gw'].idxmax()]
            warnings.append(f"🟡 HIGH DEMAND: {len(high_demand)} periods above {high_demand_threshold}GW (Peak: {max_demand_row['demand_gw']:.2f}GW at {max_demand_row['time_label']})")
        
        # 5. Very high wind (possible curtailment risk)
        very_high_wind_threshold = 20  # 20GW
        very_high_wind = df[df['wind_gw'] > very_high_wind_threshold]
        if len(very_high_wind) > 0:
            max_wind_row = df.loc[df['wind_gw'].idxmax()]
            warnings.append(f"🟢 HIGH WIND: {len(very_high_wind)} periods above {very_high_wind_threshold}GW (Peak: {max_wind_row['wind_gw']:.2f}GW at {max_wind_row['time_label']})")
        
        if warnings:
            for warning in warnings:
                print(warning)
        else:
            print("✅ No significant warnings - System operating normally")
        
        print()
    
except Exception as e:
    print(f"❌ BigQuery error: {e}")
    exit(1)

# ============================================================================
# STEP 2: WRITE DATA TO GOOGLE SHEETS
# ============================================================================

print()
print("=" * 80)
print("2️⃣  WRITING TO GOOGLE SHEETS")
print("=" * 80)

# Load credentials
print("🔑 Loading credentials...")
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

if creds.expired and creds.refresh_token:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
    with open('token.pickle', 'wb') as f:
        pickle.dump(creds, f)

service = build('sheets', 'v4', credentials=creds)
print("✅ Connected to Google Sheets API")
print()

# Prepare data for Sheets
# Format: Headers in row 18, data starts row 19
headers = [
    'Settlement Period',
    'Time',
    'Demand (GW)',
    'Wind Generation (GW)',
    'Expected Wind (GW)',
    'System Sell Price (£/MWh)',
    'Date',
    ''
]

# Convert dataframe to list of lists
data_rows = []
for _, row in df.iterrows():
    data_rows.append([
        int(row['settlementPeriod']),
        row['time_label'],
        float(row['demand_gw']),
        float(row['wind_gw']),
        float(row['expected_wind_gw']),
        float(row['ssp']),
        str(row['date']),
        ''
    ])

# Combine headers and data
all_data = [headers] + data_rows

# First, check if "Latest Day Data" sheet exists, create if not
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
data_sheet_exists = False
data_sheet_id = None

for sheet in spreadsheet.get('sheets', []):
    if sheet['properties']['title'] == DATA_SHEET_NAME:
        data_sheet_exists = True
        data_sheet_id = sheet['properties']['sheetId']
        break

if not data_sheet_exists:
    print(f"� Creating '{DATA_SHEET_NAME}' sheet...")
    try:
        request = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': DATA_SHEET_NAME,
                        'gridProperties': {
                            'rowCount': 5000,
                            'columnCount': 10
                        }
                    }
                }
            }]
        }
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=request
        ).execute()
        data_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
        print(f"✅ Created '{DATA_SHEET_NAME}' sheet")
    except Exception as e:
        print(f"⚠️  Sheet creation note: {e}")

print(f"�📝 Writing {len(all_data)} rows to {WRITE_RANGE}...")

try:
    # Clear existing data first
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=WRITE_RANGE
    ).execute()
    
    # Write new data
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=WRITE_RANGE,
        valueInputOption='RAW',
        body={'values': all_data}
    ).execute()
    
    print(f"✅ Wrote {result.get('updatedCells')} cells")
    print(f"   Sheet: {DATA_SHEET_NAME}")
    print(f"   Range: A1:H{len(all_data)}")
    
except Exception as e:
    print(f"❌ Error writing to Sheets: {e}")
    exit(1)

# ============================================================================
# STEP 3: CREATE CHART
# ============================================================================

print()
print("=" * 80)
print("3️⃣  CREATING CHART")
print("=" * 80)

# Get sheet IDs
spreadsheet_info = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
chart_sheet_id = None
data_sheet_id_final = None

for sheet in spreadsheet_info.get('sheets', []):
    if sheet['properties']['title'] == CHART_SHEET_NAME:
        chart_sheet_id = sheet['properties']['sheetId']
    if sheet['properties']['title'] == DATA_SHEET_NAME:
        data_sheet_id_final = sheet['properties']['sheetId']

if chart_sheet_id is None:
    print(f"❌ Sheet '{CHART_SHEET_NAME}' not found")
    exit(1)

if data_sheet_id_final is None:
    print(f"❌ Sheet '{DATA_SHEET_NAME}' not found")
    exit(1)

print(f"✅ Chart sheet: {CHART_SHEET_NAME} (ID: {chart_sheet_id})")
print(f"✅ Data sheet: {DATA_SHEET_NAME} (ID: {data_sheet_id_final})")

# Create combo chart
# Data is in "Latest Day Data" sheet
# Row 1 = headers (index 0)
# Rows 2+ = data (index 1+)
data_start_row = 1  # Row 2 (0-indexed, skip header)
data_end_row = 1 + len(df)  # Up to last data row

chart_request = {
    "requests": [{
        "addChart": {
            "chart": {
                "spec": {
                    "title": f"Settlement Period Analysis - {latest_date}",
                    "subtitle": "Demand, Wind Generation, Expected Wind (GW) & System Sell Price (£/MWh)",
                    "basicChart": {
                        "chartType": "COMBO",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {
                                "position": "BOTTOM_AXIS",
                                "title": "Settlement Period (Time)"
                            },
                            {
                                "position": "LEFT_AXIS",
                                "title": "Generation / Demand (GW)"
                            },
                            {
                                "position": "RIGHT_AXIS",
                                "title": "System Sell Price (£/MWh)"
                            }
                        ],
                        "domains": [{
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": data_sheet_id_final,  # Reference data sheet
                                        "startRowIndex": data_start_row,
                                        "endRowIndex": data_end_row,
                                        "startColumnIndex": 1,  # Column B (Time)
                                        "endColumnIndex": 2
                                    }]
                                }
                            }
                        }],
                        "series": [
                            # Series 1: Demand (GW)
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": data_sheet_id_final,
                                            "startRowIndex": data_start_row,
                                            "endRowIndex": data_end_row,
                                            "startColumnIndex": 2,  # Column C
                                            "endColumnIndex": 3
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE"
                            },
                            # Series 2: Wind Generation (GW)
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": data_sheet_id_final,
                                            "startRowIndex": data_start_row,
                                            "endRowIndex": data_end_row,
                                            "startColumnIndex": 3,  # Column D
                                            "endColumnIndex": 4
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE"
                            },
                            # Series 3: Expected Wind (GW) - Dashed line
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": data_sheet_id_final,
                                            "startRowIndex": data_start_row,
                                            "endRowIndex": data_end_row,
                                            "startColumnIndex": 4,  # Column E
                                            "endColumnIndex": 5
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "type": "LINE"
                            },
                            # Series 4: System Sell Price (£/MWh) - Column chart
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": data_sheet_id_final,
                                            "startRowIndex": data_start_row,
                                            "endRowIndex": data_end_row,
                                            "startColumnIndex": 5,  # Column F
                                            "endColumnIndex": 6
                                        }]
                                    }
                                },
                                "targetAxis": "RIGHT_AXIS",
                                "type": "COLUMN"
                            }
                        ],
                        "headerCount": 1
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": chart_sheet_id,  # Chart goes in Sheet1
                            "rowIndex": 17,  # Row 18
                            "columnIndex": 0  # Column A
                        },
                        "widthPixels": 1000,
                        "heightPixels": 600
                    }
                }
            }
        }
    }]
}

print("📈 Creating combo chart...")

try:
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=chart_request
    ).execute()
    
    print("✅ Chart created successfully!")
    
except Exception as e:
    print(f"⚠️  Chart creation note: {e}")
    print("   (Chart may already exist, or you can create manually)")

# ============================================================================
# STEP 4: ADD WARNINGS SECTION TO SHEET
# ============================================================================

print()
print("=" * 80)
print("4️⃣  ADDING SYSTEM WARNINGS")
print("=" * 80)

# Create warnings section below chart (starting at row 30)
warnings_data = [
    [''],  # Blank row
    ['⚠️ SYSTEM WARNINGS & ALERTS', '', '', '', f'Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'],
    ['']
]

if warnings:
    for warning in warnings:
        # Parse warning type
        if '🔴' in warning:
            warnings_data.append([warning, '', '', '', 'HIGH PRIORITY'])
        elif '🟡' in warning:
            warnings_data.append([warning, '', '', '', 'MEDIUM PRIORITY'])
        else:
            warnings_data.append([warning, '', '', '', 'INFO'])
else:
    warnings_data.append(['✅ No significant warnings - System operating normally', '', '', '', 'NORMAL'])

warnings_data.append([''])
warnings_data.append(['Legend:'])
warnings_data.append(['🔴 HIGH PRIORITY - Capacity shortage / Extreme prices (>£200/MWh)'])
warnings_data.append(['🟡 MEDIUM - High demand / Wind variations'])
warnings_data.append(['🟢 INFO - High renewable generation'])

try:
    # Write warnings to Sheet1 starting at row 30
    warnings_end_row = 30 + len(warnings_data)
    warnings_range = f'Sheet1!A30:E{warnings_end_row}'
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=warnings_range,
        valueInputOption='RAW',
        body={'values': warnings_data}
    ).execute()
    
    # Format warnings section
    format_requests = [{
        'repeatCell': {
            'range': {
                'sheetId': chart_sheet_id,
                'startRowIndex': 29,  # Row 30 (0-indexed)
                'endRowIndex': 30,
                'startColumnIndex': 0,
                'endColumnIndex': 5
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
                    'textFormat': {'bold': True, 'fontSize': 11},
                    'horizontalAlignment': 'LEFT'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    }]
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': format_requests}
    ).execute()
    
    print(f"✅ Added {len(warnings) if warnings else 1} warnings to Sheet1")
    print("   Location: Sheet1!A30:E40")
    
except Exception as e:
    print(f"⚠️  Warning section note: {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print()
print("=" * 80)
print("✅ COMPLETE")
print("=" * 80)
print()
print(f"📅 Latest date: {latest_date}")
print(f"📊 Settlement periods: {len(df)} (00:00 to 23:30)")
print(f"📍 Data written to: {DATA_SHEET_NAME}!A1:H{len(df)+1}")
print(f"📈 Chart location: {CHART_SHEET_NAME}, Row 18, Column A")
print()
print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
print()
print("📊 Chart shows:")
print("   • Left axis (GW):")
print("     - Demand Generation (solid line)")
print("     - Wind Generation (solid line)")
print("     - Expected Wind Generation (line)")
print("   • Right axis (£/MWh):")
print("     - System Sell Price (column chart)")
print()
print("💡 To refresh with latest data:")
print("   python create_latest_day_chart.py")
print()
