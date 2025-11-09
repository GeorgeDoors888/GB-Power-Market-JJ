#!/usr/bin/env python3
"""
Enhanced Dashboard Layout Creator
Creates a professional dashboard with:
- Current metrics KPIs
- Multiple interactive charts
- Real-time data display
- Formatted sections
"""

import pickle
import gspread
from google.cloud import bigquery
from google.oauth2 import service_account as sa
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
TOKEN_FILE = Path("token.pickle")
SA_FILE = Path("inner-cinema-credentials.json")

print("📊 Enhanced Dashboard Layout Creator")
print("=" * 60)

# Authenticate Google Sheets
print("\n🔐 Authenticating with Google Sheets...")
with open(TOKEN_FILE, 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
ss = gc.open_by_key(SPREADSHEET_ID)

# Authenticate BigQuery
print("🔐 Authenticating with BigQuery...")
bq_credentials = sa.Credentials.from_service_account_file(str(SA_FILE))
bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_credentials, location="US")

# Get or create Dashboard sheet
try:
    dashboard = ss.worksheet('Dashboard')
    print("✅ Found existing Dashboard sheet")
    dashboard.clear()
    print("🧹 Cleared old dashboard data")
except:
    print("📄 Creating new Dashboard sheet")
    dashboard = ss.add_worksheet(title='Dashboard', rows=100, cols=26)

# Get or create hidden ChartData sheet for chart source data
try:
    chart_data = ss.worksheet('ChartData')
    print("✅ Found existing ChartData sheet")
    # CLEAR ALL OLD DATA to prevent stale data accumulation
    chart_data.clear()
    print("🧹 Cleared old chart data")
except:
    print("📄 Creating new ChartData sheet")
    chart_data = ss.add_worksheet(title='ChartData', rows=200, cols=10)
    
# Hide the ChartData sheet
try:
    # Use batch_update to hide the sheet
    requests = [{
        "updateSheetProperties": {
            "properties": {
                "sheetId": chart_data.id,
                "hidden": True
            },
            "fields": "hidden"
        }
    }]
    ss.batch_update({"requests": requests})
    print("✅ ChartData sheet hidden")
except Exception as e:
    print(f"⚠️  Could not hide sheet: {e}")

print("\n📥 Fetching current data from BigQuery...")

# Query 1: Current Generation Mix (Last 30 minutes)
gen_query = f"""
WITH latest_gen AS (
  SELECT 
    fuelType,
    generation,
    settlementDate,
    settlementPeriod,
    ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY settlementDate DESC, settlementPeriod DESC) as rn
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
    AND generation IS NOT NULL
)
SELECT 
  fuelType,
  ROUND(SUM(generation), 1) as total_mw,
  MAX(settlementDate) as last_date,
  MAX(settlementPeriod) as last_sp
FROM latest_gen
WHERE rn = 1
GROUP BY fuelType
ORDER BY total_mw DESC
"""

gen_df = bq_client.query(gen_query).to_dataframe()
total_gen = gen_df['total_mw'].sum()

# Query 2: Current Prices (use MID table)
price_query = f"""
SELECT 
  price as marketPrice,
  settlementDate,
  settlementPeriod
FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND price IS NOT NULL
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 1
"""

price_df = bq_client.query(price_query).to_dataframe()

# Query 3: Last 24 Hours Trend (for chart)
trend_query = f"""
WITH recent_data AS (
  SELECT 
    settlementDate,
    settlementPeriod,
    SUM(CASE WHEN fuelType IN ('WIND', 'OFFSHORE') THEN generation ELSE 0 END) as wind_mw,
    SUM(CASE WHEN fuelType IN ('SOLAR') THEN generation ELSE 0 END) as solar_mw,
    SUM(CASE WHEN fuelType = 'NUCLEAR' THEN generation ELSE 0 END) as nuclear_mw,
    SUM(CASE WHEN fuelType IN ('CCGT', 'OCGT') THEN generation ELSE 0 END) as gas_mw,
    SUM(generation) as total_mw
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  GROUP BY settlementDate, settlementPeriod
)
SELECT 
  settlementDate,
  settlementPeriod,
  wind_mw,
  solar_mw,
  nuclear_mw,
  gas_mw,
  total_mw
FROM recent_data
ORDER BY settlementDate, settlementPeriod
"""

trend_df = bq_client.query(trend_query).to_dataframe()

print(f"✅ Retrieved {len(gen_df)} fuel types, {len(trend_df)} data points")

# Build Dashboard Layout
print("\n🎨 Building enhanced dashboard layout...")

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
current_price = price_df['marketPrice'].iloc[0] if len(price_df) > 0 else 0
current_sp = price_df['settlementPeriod'].iloc[0] if len(price_df) > 0 else 0

# Calculate renewable percentage
renewable_mw = gen_df[gen_df['fuelType'].isin(['WIND', 'OFFSHORE', 'SOLAR', 'HYDRO', 'BIOMASS'])]['total_mw'].sum()
renewable_pct = (renewable_mw / total_gen * 100) if total_gen > 0 else 0

# Layout structure
layout_data = []

# HEADER SECTION (Rows 1-3)
layout_data.append(['🔋 GB POWER MARKET - LIVE DASHBOARD', '', '', '', '', ''])
layout_data.append([f'Last Updated: {current_time} | Settlement Period: {current_sp}', '', '', '', '', ''])
layout_data.append(['', '', '', '', '', ''])  # Spacer

# KPI METRICS SECTION (Rows 4-6)
layout_data.append(['📊 CURRENT METRICS', '', '', '💰 MARKET PRICES', '', ''])
layout_data.append([
    f'Total Generation: {total_gen:,.0f} MW',
    '',
    '',
    f'Sell Price: £{current_price:.2f}/MWh',
    '',
    ''
])
layout_data.append([
    f'Renewable Share: {renewable_pct:.1f}%',
    '',
    '',
    f'Renewable MW: {renewable_mw:,.0f} MW',
    '',
    ''
])
layout_data.append(['', '', '', '', '', ''])  # Spacer

# GENERATION MIX TABLE (Rows 8+)
layout_data.append(['⚡ GENERATION BY FUEL TYPE', '', '', '', '', ''])
layout_data.append(['Fuel Type', 'Generation (MW)', '% of Total', 'Status', '', ''])

# Emoji mapping for fuel types
fuel_emojis = {
    'WIND': '💨',
    'OFFSHORE': '🌊',
    'CCGT': '🔥',
    'NUCLEAR': '⚛️',
    'SOLAR': '☀️',
    'HYDRO': '💧',
    'BIOMASS': '🌿',
    'COAL': '⚫',
    'OIL': '🛢️',
    'OTHER': '⚙️'
}

for _, row in gen_df.iterrows():
    fuel = row['fuelType']
    mw = row['total_mw']
    pct = (mw / total_gen * 100) if total_gen > 0 else 0
    emoji = fuel_emojis.get(fuel, '⚡')
    status = '🟢 Active' if mw > 0 else '🔴 Offline'
    
    layout_data.append([
        f'{emoji} {fuel}',
        f'{mw:,.0f}',
        f'{pct:.1f}%',
        status,
        '',
        ''
    ])

layout_data.append(['', '', '', '', '', ''])  # Spacer

# Write Dashboard data (without trend data)
print(f"📝 Writing {len(layout_data)} rows to Dashboard...")
dashboard.update('A1:F{}'.format(len(layout_data)), layout_data)

# CHART DATA - Write to separate hidden sheet
print("\n📊 Writing chart data to hidden ChartData sheet...")
chart_data_rows = []

# Header row
chart_data_rows.append(['Settlement Period', 'Wind', 'Solar', 'Nuclear', 'Gas', 'Total'])

# Data rows
for _, row in trend_df.iterrows():
    sp = row['settlementPeriod']
    chart_data_rows.append([
        f'SP {sp}',
        float(row["wind_mw"]) if pd.notna(row["wind_mw"]) else 0,
        float(row["solar_mw"]) if pd.notna(row["solar_mw"]) else 0,
        float(row["nuclear_mw"]) if pd.notna(row["nuclear_mw"]) else 0,
        float(row["gas_mw"]) if pd.notna(row["gas_mw"]) else 0,
        float(row["total_mw"]) if pd.notna(row["total_mw"]) else 0
    ])

chart_data.update('A1:F{}'.format(len(chart_data_rows)), chart_data_rows)
print(f"✅ Wrote {len(chart_data_rows)} rows to ChartData sheet")

# Apply Formatting
print("🎨 Applying formatting...")

# Format header (Row 1)
dashboard.format('A1:F1', {
    'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.6},
    'textFormat': {
        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
        'fontSize': 16,
        'bold': True
    },
    'horizontalAlignment': 'CENTER'
})

# Merge header cells
try:
    dashboard.merge_cells('A1:F1')
except Exception as e:
    print(f"⚠️  Could not merge A1:F1: {e}")

# Format subheader (Row 2)
dashboard.format('A2:F2', {
    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
    'textFormat': {'fontSize': 10, 'italic': True},
    'horizontalAlignment': 'CENTER'
})
try:
    dashboard.merge_cells('A2:F2')
except Exception as e:
    print(f"⚠️  Could not merge A2:F2: {e}")

# Format section headers
section_rows = [4, 8, 8 + len(gen_df) + 3]  # Metrics, Generation, Trend
for row in section_rows:
    dashboard.format(f'A{row}:F{row}', {
        'backgroundColor': {'red': 0.4, 'green': 0.5, 'blue': 0.7},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'fontSize': 12,
            'bold': True
        }
    })

# Format KPI cells
kpi_rows = [5, 6]
for row in kpi_rows:
    dashboard.format(f'A{row}:C{row}', {
        'backgroundColor': {'red': 0.95, 'green': 0.98, 'blue': 1},
        'textFormat': {'fontSize': 11, 'bold': True}
    })
    dashboard.format(f'D{row}:F{row}', {
        'backgroundColor': {'red': 1, 'green': 0.98, 'blue': 0.9},
        'textFormat': {'fontSize': 11, 'bold': True}
    })

# Format table headers
dashboard.format('A10:F10', {
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
    'textFormat': {'bold': True}
})

# Adjust column widths (using format instead of set_column_width)
try:
    # Use the spreadsheet object to set column widths
    ss.batch_update({
        'requests': [
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': dashboard.id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,  # Column A
                        'endIndex': 1
                    },
                    'properties': {'pixelSize': 250},
                    'fields': 'pixelSize'
                }
            },
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': dashboard.id,
                        'dimension': 'COLUMNS',
                        'startIndex': 1,  # Column B
                        'endIndex': 2
                    },
                    'properties': {'pixelSize': 150},
                    'fields': 'pixelSize'
                }
            },
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': dashboard.id,
                        'dimension': 'COLUMNS',
                        'startIndex': 2,  # Column C
                        'endIndex': 3
                    },
                    'properties': {'pixelSize': 120},
                    'fields': 'pixelSize'
                }
            }
        ]
    })
    print("✅ Column widths adjusted")
except Exception as e:
    print(f"⚠️  Could not adjust column widths: {e}")

print("\n✅ Dashboard layout created successfully!")
print(f"\n📊 Summary:")
print(f"   • Total Generation: {total_gen:,.0f} MW")
print(f"   • Renewable Share: {renewable_pct:.1f}%")
print(f"   • Current Price: £{current_price:.2f}/MWh")
print(f"   • Dashboard Rows: {len(layout_data)}")
print(f"   • Chart Data Points: {len(chart_data_rows)} (last 24h)")
print(f"\n🔗 View Dashboard:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard.id}")

print("\n� Sheet Structure:")
print("   • Dashboard: Clean display with KPIs & generation mix")
print("   • ChartData: Hidden sheet with trend data for charts")

print("\n📈 Charts will use:")
print("   • Data source: ChartData sheet (hidden)")
print("   • Range: A1:F{} (Settlement Period + 5 series)".format(len(chart_data_rows)))
print("   • Charts auto-update when data refreshes")

print("\n💡 Tip: Run this script via cron for auto-updates!")
print("   */5 * * * * cd '{}' && python3 enhance_dashboard_layout.py >> logs/dashboard_enhance.log 2>&1".format(Path.cwd()))
