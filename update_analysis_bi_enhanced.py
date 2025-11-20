#!/usr/bin/env python3
"""
Update Enhanced BI Analysis Sheet
Reads dropdown selections and refreshes data from BigQuery
"""

import pickle
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET_NAME = 'Enhanced_BI_Analysis'  # Separate sheet for detailed analysis (NOT the main Dashboard)
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

print("=" * 80)
print("🔄 UPDATING ENHANCED BI ANALYSIS SHEET")
print("=" * 80)
print()

# Initialize
print("🔧 Connecting...")
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(SHEET_NAME)
bq_client = bigquery.Client(project=PROJECT_ID)

print("✅ Connected")
print()

# Read user selections
print("📖 Reading user selections...")
quick_select = sheet.acell('B5').value or '1 Week'
custom_from = sheet.acell('D5').value
custom_to = sheet.acell('F5').value
view_type = sheet.acell('H5').value or 'Summary'

print(f"  Quick Select: {quick_select}")
print(f"  View Type: {view_type}")
print()

# Determine date range
days_map = {
    '24 Hours': 1,
    '1 Week': 7,
    '1 Month': 30,
    '3 Months': 90,
    '6 Months': 180,
    '1 Year': 365,
    'Custom': None
}

days = days_map.get(quick_select, 7)

if quick_select == 'Custom' and custom_from and custom_to:
    try:
        start_date = datetime.strptime(custom_from, '%d/%m/%Y')
        end_date = datetime.strptime(custom_to, '%d/%m/%Y')
        days = (end_date - start_date).days
        print(f"  Using custom range: {start_date.date()} to {end_date.date()}")
    except:
        print(f"  ⚠️ Invalid custom dates, using default (1 Week)")
        days = 7
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
else:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    print(f"  Date range: {start_date.date()} to {end_date.date()} ({days} days)")

print()

# ============================================================================
# 1. UPDATE GENERATION DATA
# ============================================================================
print("1️⃣ Updating generation data...")
try:
    gen_query = f"""
    WITH combined AS (
        SELECT 
            CAST(publishTime AS DATETIME) as timestamp,
            fuelType,
            generation,
            'historical' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE CAST(publishTime AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL {days} DAY)
        UNION ALL
        SELECT 
            CAST(publishTime AS DATETIME) as timestamp,
            fuelType,
            generation,
            'real-time' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(publishTime AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
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
    print(f"  ✅ Retrieved {len(gen_results)} fuel types")
    
    # Calculate totals
    total_generation = sum(row.total_mwh for row in gen_results)
    
    # Clear old data
    sheet.update('A18:G34', [['' for _ in range(7)] for _ in range(17)])
    
    # Populate new data
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
        
        # Update summary metrics
        renewable_fuels = ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS', 'NUCLEAR']
        renewable_gen = sum(row.total_mwh for row in gen_results if row.fuelType.upper() in renewable_fuels)
        renewable_pct = round((renewable_gen / total_generation * 100), 2) if total_generation > 0 else 0
        
        sheet.update('B10', [[f'{int(total_generation):,} MWh']])
        sheet.update('B13', [[f'{renewable_pct}%']])
        
        # Calculate peak demand (max generation)
        peak_gen = max(row.max_mw for row in gen_results)
        sheet.update('D13', [[f'{int(peak_gen):,} MW']])
        
        print(f"  ✅ Updated Generation Mix table ({len(gen_data)} rows)")
        print(f"     Total: {int(total_generation):,} MWh | Renewable: {renewable_pct}%")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# ============================================================================
# 2. UPDATE FREQUENCY DATA
# ============================================================================
print("2️⃣ Updating frequency data...")
try:
    freq_query = f"""
    WITH combined AS (
        SELECT 
            CAST(measurementTime AS DATETIME) as timestamp,
            frequency,
            'historical' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
        WHERE CAST(measurementTime AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL {days} DAY)
        UNION ALL
        SELECT 
            CAST(measurementTime AS DATETIME) as timestamp,
            frequency,
            'real-time' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE CAST(measurementTime AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
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
    print(f"  ✅ Retrieved {len(freq_results)} frequency records")
    
    # Clear old data
    sheet.update('A38:E59', [['' for _ in range(5)] for _ in range(22)])
    
    # Populate new data
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
        
        # Update avg frequency metric
        avg_freq = sum(row.frequency for row in freq_results) / len(freq_results)
        sheet.update('D10', [[f'{avg_freq:.3f} Hz']])
        
        # Grid stability assessment
        stability = 'Normal'
        if any(row.frequency < 49.5 or row.frequency > 50.5 for row in freq_results):
            stability = 'Critical'
        elif any(row.frequency < 49.8 or row.frequency > 50.2 for row in freq_results):
            stability = 'Warning'
        
        sheet.update('F13', [[stability]])
        
        print(f"  ✅ Updated Frequency table ({len(freq_data)} rows)")
        print(f"     Avg: {avg_freq:.3f} Hz | Stability: {stability}")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# ============================================================================
# 3. UPDATE MARKET PRICES
# ============================================================================
print("3️⃣ Updating market prices...")
try:
    price_query = f"""
    WITH combined AS (
        SELECT 
            settlementDate as date,
            settlementPeriod as settlement_period,
            ROUND(price, 2) as price,
            ROUND(volume, 2) as volume,
            dataProvider,
            'historical' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        UNION ALL
        SELECT 
            settlementDate as date,
            settlementPeriod as settlement_period,
            ROUND(price, 2) as price,
            ROUND(volume, 2) as volume,
            dataProvider,
            'real-time' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
    )
    SELECT * FROM combined
    ORDER BY date DESC, settlement_period DESC
    LIMIT 20
    """
    
    price_results = list(bq_client.query(price_query).result())
    print(f"  ✅ Retrieved {len(price_results)} price records")
    
    # Clear old data
    sheet.update('A63:F84', [['' for _ in range(6)] for _ in range(22)])
    
    # Populate new data - MID format
    price_data = []
    for row in price_results:
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
        
        # Update avg price metric
        avg_price = sum(row.price for row in price_results) / len(price_results)
        sheet.update('F10', [[f'£{avg_price:.2f}/MWh']])
        
        print(f"  ✅ Updated Market Prices table ({len(price_data)} rows)")
        print(f"     Avg Market Price: £{avg_price:.2f}/MWh")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# ============================================================================
# 4. UPDATE BALANCING COSTS
# ============================================================================
print("4️⃣ Updating balancing costs...")
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
        ROUND(sellPricePriceAdjustment, 2) as sell_price_adj,
        'historical' as source
    FROM `{PROJECT_ID}.{DATASET}.bmrs_netbsad`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 20
    """
    
    bsad_results = list(bq_client.query(bsad_query).result())
    print(f"  ✅ Retrieved {len(bsad_results)} NETBSAD records")
    
    # Clear old data
    sheet.update('A88:F109', [['' for _ in range(6)] for _ in range(22)])
    
    # Populate new data - NETBSAD format
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
        print(f"  ✅ Updated NETBSAD table ({len(bsad_data)} rows)")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# Update timestamp
sheet.update('A110', [[f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])

print("=" * 80)
print("✅ SHEET UPDATED SUCCESSFULLY!")
print("=" * 80)
print()
print("📊 View your data:")
print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
print("💡 Tip: Change the dropdown selections in the sheet and run this script again")
print()
