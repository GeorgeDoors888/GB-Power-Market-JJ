#!/usr/bin/env python3
"""
Enhanced BI Analysis Sheet
Uses pattern from jibber-jabber-knowledge.uk_energy BI views
Applied to inner-cinema-476211-u9.uk_energy_prod dataset
"""

import pickle
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from googleapiclient.discovery import build

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET_NAME = 'Analysis BI Enhanced'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

print("=" * 80)
print("📊 ENHANCED BI ANALYSIS SHEET")
print("=" * 80)
print()

# Initialize
print("🔧 Initializing connections...")
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
bq_client = bigquery.Client(project=PROJECT_ID)

# Google Sheets API for dropdown validation
sheets_service = build('sheets', 'v4', credentials=creds)

print("✅ Connected to Google Sheets and BigQuery")
print()

# Get or create sheet
print("📄 Setting up sheet...")
try:
    sheet = spreadsheet.worksheet(SHEET_NAME)
    print(f"Found existing '{SHEET_NAME}' sheet")
except gspread.exceptions.WorksheetNotFound:
    print(f"Creating new '{SHEET_NAME}' sheet")
    sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=200, cols=15)

sheet.clear()
print("✅ Sheet cleared and ready")
print()

# Build sheet structure
print("🎨 Building sheet structure...")

# ============================================================================
# HEADER SECTION
# ============================================================================
sheet.update('A1:O1', [['⚡ ENHANCED BI ANALYSIS DASHBOARD - UK POWER MARKET']])
sheet.format('A1:O1', {
    'backgroundColor': {'red': 0.102, 'green': 0.137, 'blue': 0.494},
    'textFormat': {'bold': True, 'fontSize': 18, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER',
    'verticalAlignment': 'MIDDLE'
})

# Merge cells
merge_requests = [{
    'mergeCells': {
        'range': {'sheetId': sheet.id, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': 0, 'endColumnIndex': 15},
        'mergeType': 'MERGE_ALL'
    }
}]

# ============================================================================
# CONTROL PANEL
# ============================================================================
sheet.update('A3:O3', [['📅 CONTROL PANEL']])
sheet.format('A3:O3', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
merge_requests.append({
    'mergeCells': {
        'range': {'sheetId': sheet.id, 'startRowIndex': 2, 'endRowIndex': 3, 'startColumnIndex': 0, 'endColumnIndex': 15},
        'mergeType': 'MERGE_ALL'
    }
})

# Date range controls
sheet.update('A5', [['Quick Select:']])
sheet.update('C5', [['Custom From:']])
sheet.update('E5', [['Custom To:']])
sheet.update('G5', [['View Type:']])

sheet.format('A5:O5', {
    'textFormat': {'bold': True, 'fontSize': 11},
    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
})

# Set default values
sheet.update('B5', [['1 Week']])
sheet.update('D5', [[(datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y')]])
sheet.update('F5', [[datetime.now().strftime('%d/%m/%Y')]])
sheet.update('H5', [['Summary']])

# Add Status indicator and hidden trigger cell
sheet.update('L5', [['✅ Ready']])
sheet.format('L5', {
    'backgroundColor': {'red': 0.78, 'green': 0.9, 'blue': 0.79},  # Light green
    'textFormat': {'bold': True, 'fontSize': 10},
    'horizontalAlignment': 'CENTER'
})

# Add instruction label
sheet.update('J5', [['Status:']])
sheet.format('J5', {
    'textFormat': {'bold': True, 'fontSize': 10},
    'horizontalAlignment': 'RIGHT'
})

# Hidden trigger cell M5 (for Google Apps Script)
sheet.update('M5', [['']])
sheet.format('M5', {
    'textFormat': {'fontSize': 8, 'foregroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}}
})

# Add dropdown validation for Quick Select
dropdown_values = ['24 Hours', '1 Week', '1 Month', '3 Months', '6 Months', '1 Year', 'Custom']
requests = [{
    'setDataValidation': {
        'range': {
            'sheetId': sheet.id,
            'startRowIndex': 4,
            'endRowIndex': 5,
            'startColumnIndex': 1,
            'endColumnIndex': 2
        },
        'rule': {
            'condition': {
                'type': 'ONE_OF_LIST',
                'values': [{'userEnteredValue': val} for val in dropdown_values]
            },
            'showCustomUi': True,
            'strict': True
        }
    }
}]

# Add dropdown for View Type
view_types = ['Summary', 'Generation Mix', 'System Frequency', 'Market Prices', 'Balancing Costs']
requests.append({
    'setDataValidation': {
        'range': {
            'sheetId': sheet.id,
            'startRowIndex': 4,
            'endRowIndex': 5,
            'startColumnIndex': 7,
            'endColumnIndex': 8
        },
        'rule': {
            'condition': {
                'type': 'ONE_OF_LIST',
                'values': [{'userEnteredValue': val} for val in view_types]
            },
            'showCustomUi': True,
            'strict': True
        }
    }
})

# ============================================================================
# SUMMARY METRICS SECTION
# ============================================================================
sheet.update('A7:O7', [['📊 KEY METRICS & INSIGHTS']])
sheet.format('A7:O7', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
merge_requests.append({
    'mergeCells': {
        'range': {'sheetId': sheet.id, 'startRowIndex': 6, 'endRowIndex': 7, 'startColumnIndex': 0, 'endColumnIndex': 15},
        'mergeType': 'MERGE_ALL'
    }
})

# Metric cards
metrics = [
    ['🔋 Total Generation', '', '⚖️ Avg System Frequency', '', '💰 Avg System Price', ''],
    ['0 MWh', '', '50.00 Hz', '', '£0.00/MWh', ''],
    ['', '', '', '', '', ''],
    ['🌱 Renewable %', '', '📈 Peak Demand', '', '⚡ Grid Stability', ''],
    ['0%', '', '0 MW', '', 'Normal', '']
]

sheet.update('A9:F13', metrics)

# Format metric cards
metric_ranges = [
    'A9:B10', 'C9:D10', 'E9:F10',
    'A12:B13', 'C12:D13', 'E12:F13'
]

for range_addr in metric_ranges:
    sheet.format(range_addr, {
        'backgroundColor': {'red': 0.95, 'green': 0.97, 'blue': 1.0},
        'borders': {
            'top': {'style': 'SOLID', 'width': 1},
            'bottom': {'style': 'SOLID', 'width': 1},
            'left': {'style': 'SOLID', 'width': 1},
            'right': {'style': 'SOLID', 'width': 1}
        }
    })

# ============================================================================
# DATA SECTIONS
# ============================================================================

# Generation Mix Section
sheet.update('A15:O15', [['🔋 GENERATION MIX (by Fuel Type)']])
sheet.format('A15:O15', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
merge_requests.append({
    'mergeCells': {
        'range': {'sheetId': sheet.id, 'startRowIndex': 14, 'endRowIndex': 15, 'startColumnIndex': 0, 'endColumnIndex': 15},
        'mergeType': 'MERGE_ALL'
    }
})

# Generation table headers
gen_headers = [['Fuel Type', 'Total MWh', 'Avg MW', '% Share', 'Max MW', 'Min MW', 'Source Mix']]
sheet.update('A17:G17', gen_headers)
sheet.format('A17:G17', {
    'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.6},
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})

# System Frequency Section
sheet.update('A35:O35', [['📊 SYSTEM FREQUENCY ANALYSIS']])
sheet.format('A35:O35', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
merge_requests.append({
    'mergeCells': {
        'range': {'sheetId': sheet.id, 'startRowIndex': 34, 'endRowIndex': 35, 'startColumnIndex': 0, 'endColumnIndex': 15},
        'mergeType': 'MERGE_ALL'
    }
})

# Frequency table headers
freq_headers = [['Timestamp', 'Frequency (Hz)', 'Deviation (mHz)', 'Status', 'Source']]
sheet.update('A37:E37', freq_headers)
sheet.format('A37:E37', {
    'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.6},
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})

# Market Prices Section
sheet.update('A60:O60', [['💰 MARKET INDEX DATA (MID)']])
sheet.format('A60:O60', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
merge_requests.append({
    'mergeCells': {
        'range': {'sheetId': sheet.id, 'startRowIndex': 59, 'endRowIndex': 60, 'startColumnIndex': 0, 'endColumnIndex': 15},
        'mergeType': 'MERGE_ALL'
    }
})

# Price table headers - adjusted for MID data
price_headers = [['Date', 'Settlement Period', 'Market Price (£/MWh)', 'Volume (MWh)', 'Data Provider', 'Source']]
sheet.update('A62:F62', price_headers)
sheet.format('A62:F62', {
    'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.6},
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})

# Balancing Costs Section  
sheet.update('A85:O85', [['⚖️ BALANCING COSTS (NETBSAD)']])
sheet.format('A85:O85', {
    'backgroundColor': {'red': 0.157, 'green': 0.208, 'blue': 0.576},
    'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})
merge_requests.append({
    'mergeCells': {
        'range': {'sheetId': sheet.id, 'startRowIndex': 84, 'endRowIndex': 85, 'startColumnIndex': 0, 'endColumnIndex': 15},
        'mergeType': 'MERGE_ALL'
    }
})

# BSAD table headers - adjusted for NETBSAD data
bsad_headers = [['Date', 'Settlement Period', 'Cost Breakdown (£)', 'Net Cost (£)', 'Net Volume (MWh)', 'Price Adj (Buy/Sell £/MWh)']]
sheet.update('A87:F87', bsad_headers)
sheet.format('A87:F87', {
    'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.6},
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
    'horizontalAlignment': 'CENTER'
})

# Footer with instructions
footer_data = [
    [f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
    [''],
    ['💡 HOW TO USE THIS DASHBOARD:'],
    ['1. Change date range in cell B5 (Quick Select dropdown) or use custom dates in D5-F5'],
    ['2. Click menu: "⚡ Power Market" > "🔄 Refresh Data Now" (automatic refresh!)'],
    ['3. Or run manually: python3 update_analysis_bi_enhanced.py'],
    ['4. Status indicator in cell L5 shows: ✅ Ready | ⏳ Refreshing... | ❌ Error'],
    ['5. For automatic menu to work, start watcher: python3 watch_sheet_for_refresh.py'],
]
sheet.update('A110:O116', [[item] + [''] * 14 for item in [row[0] for row in footer_data]])
sheet.format('A110', {
    'textFormat': {'italic': True, 'fontSize': 9},
    'horizontalAlignment': 'LEFT'
})
sheet.format('A112:O112', {
    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
    'textFormat': {'bold': True, 'fontSize': 10},
})
sheet.format('A113:O116', {
    'textFormat': {'fontSize': 9},
})

# Apply all merge requests
sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': merge_requests}
).execute()

# Apply dropdown validations
sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()

print("✅ Sheet structure created with dropdowns")
print()

# ============================================================================
# QUERY AND POPULATE DATA
# ============================================================================

print("📊 Querying data from BigQuery...")

# Determine date range
quick_select = '1 Week'
days_map = {
    '24 Hours': 1,
    '1 Week': 7,
    '1 Month': 30,
    '3 Months': 90,
    '6 Months': 180,
    '1 Year': 365,
    'Custom': 7  # default
}
days = days_map.get(quick_select, 7)

end_date = datetime.now()
start_date = end_date - timedelta(days=days)

print(f"  Date range: {start_date.date()} to {end_date.date()}")
print()

# 1. Query Generation Data (from bmrs_fuelinst + bmrs_fuelinst_iris)
print("  1️⃣ Querying generation data...")
try:
    gen_query = f"""
    WITH combined AS (
        SELECT 
            publishTime as timestamp,
            fuelType,
            generation,
            'historical' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL {days} DAY)
        UNION ALL
        SELECT 
            publishTime as timestamp,
            fuelType,
            generation,
            'real-time' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
    )
    SELECT 
        fuelType,
        COUNT(*) as record_count,
        ROUND(SUM(generation)/1000, 2) as total_mwh,
        ROUND(AVG(generation), 2) as avg_mw,
        ROUND(MAX(generation), 2) as max_mw,
        ROUND(MIN(generation), 2) as min_mw,
        COUNTIF(source='historical') as hist_count,
        COUNTIF(source='real-time') as iris_count
    FROM combined
    GROUP BY fuelType
    ORDER BY total_mwh DESC
    LIMIT 20
    """
    
    gen_results = list(bq_client.query(gen_query).result())
    print(f"    ✅ Retrieved {len(gen_results)} fuel types")
    
    # Calculate total for percentages
    total_generation = sum(row.total_mwh for row in gen_results)
    
    # Populate generation table
    gen_data = []
    for row in gen_results:
        pct_share = round((row.total_mwh / total_generation * 100), 2) if total_generation > 0 else 0
        source_mix = f"Hist:{row.hist_count} | IRIS:{row.iris_count}"
        gen_data.append([
            row.fuelType,
            row.total_mwh,
            row.avg_mw,
            pct_share,
            row.max_mw,
            row.min_mw,
            source_mix
        ])
    
    if gen_data:
        sheet.update(f'A18:G{17+len(gen_data)}', gen_data)
        print(f"    ✅ Wrote {len(gen_data)} rows to Generation Mix table")
        
        # Update summary metrics
        renewable_fuels = ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS', 'NUCLEAR']
        renewable_gen = sum(row.total_mwh for row in gen_results if row.fuelType.upper() in renewable_fuels)
        renewable_pct = round((renewable_gen / total_generation * 100), 2) if total_generation > 0 else 0
        
        sheet.update('B10', [[f'{int(total_generation):,} MWh']])
        sheet.update('B13', [[f'{renewable_pct}%']])
    
except Exception as e:
    print(f"    ⚠️ Error querying generation: {e}")

print()

# 2. Query Frequency Data (from bmrs_freq + bmrs_freq_iris)
print("  2️⃣ Querying frequency data...")
try:
    freq_query = f"""
    WITH combined AS (
        SELECT 
            measurementTime as timestamp,
            frequency,
            'historical' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
        WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL {days} DAY)
        UNION ALL
        SELECT 
            measurementTime as timestamp,
            frequency,
            'real-time' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
    )
    SELECT 
        timestamp,
        ROUND(frequency, 3) as frequency,
        source
    FROM combined
    ORDER BY timestamp DESC
    LIMIT 20
    """
    
    freq_results = list(bq_client.query(freq_query).result())
    print(f"    ✅ Retrieved {len(freq_results)} frequency records")
    
    # Populate frequency table
    freq_data = []
    for row in freq_results:
        deviation_mhz = round((row.frequency - 50.0) * 1000, 1)
        status = 'Normal' if 49.8 <= row.frequency <= 50.2 else 'Alert'
        freq_data.append([
            row.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            row.frequency,
            deviation_mhz,
            status,
            row.source
        ])
    
    if freq_data:
        sheet.update(f'A38:E{37+len(freq_data)}', freq_data)
        print(f"    ✅ Wrote {len(freq_data)} rows to Frequency table")
        
        # Update avg frequency metric
        avg_freq = sum(row.frequency for row in freq_results) / len(freq_results)
        sheet.update('D10', [[f'{avg_freq:.3f} Hz']])
    
except Exception as e:
    print(f"    ⚠️ Error querying frequency: {e}")

print()

# 3. Query Market Prices (from bmrs_mid - Market Index Data)
print("  3️⃣ Querying market prices...")
try:
    price_query = f"""
    SELECT 
        settlementDate as date,
        settlementPeriod as settlement_period,
        ROUND(price, 2) as price,
        ROUND(volume, 2) as volume,
        dataProvider,
        'mid' as source
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 20
    """
    
    price_results = list(bq_client.query(price_query).result())
    print(f"    ✅ Retrieved {len(price_results)} price records")
    
    # Populate price table - adjusted for MID data (price, volume, not buy/sell)
    price_data = []
    for row in price_results:
        # MID has price and volume, not separate buy/sell prices
        # We'll show price as "market price" and volume as traded volume
        price_data.append([
            row.date.strftime('%Y-%m-%d'),
            row.settlement_period,
            row.price,  # Market price
            row.volume,  # Traded volume
            row.dataProvider,
            row.source
        ])
    
    if price_data:
        sheet.update(f'A63:F{62+len(price_data)}', price_data)
        print(f"    ✅ Wrote {len(price_data)} rows to Prices table")
        
        # Update avg price metric
        avg_price = sum(row.price for row in price_results) / len(price_results)
        sheet.update('F10', [[f'£{avg_price:.2f}/MWh']])
    
except Exception as e:
    print(f"    ⚠️ Error querying prices: {e}")

print()

# 4. Query Balancing Costs (from bmrs_netbsad)
print("  4️⃣ Querying balancing costs...")
try:
    bsad_query = f"""
    SELECT 
        settlementDate as date,
        settlementPeriod as settlement_period,
        ROUND(netBuyPriceCostAdjustmentEnergy, 2) as buy_cost_energy,
        ROUND(netBuyPriceVolumeAdjustmentEnergy, 2) as buy_volume_energy,
        ROUND(netSellPriceCostAdjustmentEnergy, 2) as sell_cost_energy,
        ROUND(netSellPriceVolumeAdjustmentEnergy, 2) as sell_volume_energy,
        ROUND(buyPricePriceAdjustment, 2) as buy_price_adj,
        ROUND(sellPricePriceAdjustment, 2) as sell_price_adj
    FROM `{PROJECT_ID}.{DATASET}.bmrs_netbsad`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 20
    """
    
    bsad_results = list(bq_client.query(bsad_query).result())
    print(f"    ✅ Retrieved {len(bsad_results)} NETBSAD records")
    
    # Populate BSAD table - showing buy and sell adjustments
    bsad_data = []
    for row in bsad_results:
        # Calculate net costs and volumes
        net_cost = (row.buy_cost_energy or 0) + (row.sell_cost_energy or 0)
        net_volume = (row.buy_volume_energy or 0) + (row.sell_volume_energy or 0)
        
        bsad_data.append([
            row.date.strftime('%Y-%m-%d'),
            row.settlement_period,
            f'Buy: {row.buy_cost_energy or 0:.0f} | Sell: {row.sell_cost_energy or 0:.0f}',
            net_cost,
            net_volume,
            f'{row.buy_price_adj or 0:.2f} / {row.sell_price_adj or 0:.2f}'
        ])
    
    if bsad_data:
        sheet.update(f'A88:F{87+len(bsad_data)}', bsad_data)
        print(f"    ✅ Wrote {len(bsad_data)} rows to NETBSAD table")
    
except Exception as e:
    print(f"    ⚠️ Error querying BSAD: {e}")

print()

# Update timestamp
sheet.update('A110', [[f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])

print("=" * 80)
print("✅ ENHANCED BI ANALYSIS SHEET CREATED!")
print("=" * 80)
print()
print("📊 Features:")
print("  ✓ Generation Mix with fuel type breakdown")
print("  ✓ System Frequency monitoring")
print("  ✓ Market Index Data (MID prices & volumes)")
print("  ✓ Balancing Costs (NETBSAD buy/sell adjustments)")
print("  ✓ Date range dropdowns (24 Hours → 1 Year)")
print("  ✓ Historical + Real-time data combined")
print("  ✓ Custom menu with Refresh button!")
print()
print("📄 Sheet URL:")
print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
print("🔄 To enable automatic refresh from sheet menu:")
print("  1. Install Google Apps Script menu (see SHEET_REFRESH_MENU_SETUP.md)")
print("  2. Start watcher: python3 watch_sheet_for_refresh.py")
print("  3. In sheet, click: ⚡ Power Market > 🔄 Refresh Data Now")
print()
print("🔄 Or refresh manually:")
print("  python3 update_analysis_bi_enhanced.py")
print()
print("📊 Data Sources:")
print("  • bmrs_fuelinst + bmrs_fuelinst_iris (Generation)")
print("  • bmrs_freq + bmrs_freq_iris (Frequency)")
print("  • bmrs_mid (Market Index Data)")
print("  • bmrs_netbsad (Balancing Costs)")
print()
