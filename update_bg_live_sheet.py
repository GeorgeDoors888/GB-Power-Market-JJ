#!/usr/bin/env python3
"""
Update BG Live Sheet with Real-Time Data
Uses recent historical data (bmrs_fuelinst) from BigQuery
Preserves existing sheet structure, only updates data values

Key Data Facts (from STOP_DATA_ARCHITECTURE_REFERENCE.md):
- bmrs_fuelinst.generation is in MW (NOT MWh!)
- bmrs_costs = imbalance prices (SSP/SBP merged to single price)
- bmrs_mid = wholesale market prices
- Historical tables are reliable, IRIS tables may have gaps
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

# Configuration
SHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SHEET_NAME = 'BG Live'
CREDS_PATH = '/home/george/inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def authenticate():
    """Authenticate with Google Sheets and BigQuery"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
    sheets_client = gspread.authorize(creds)
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')
    return sheets_client, bq_client

def get_live_generation():
    """
    Get latest generation by fuel type from IRIS real-time tables
    IRIS has 198k+ rows updated to Dec 5, 2025
    Generation values are in MW per STOP_DATA_ARCHITECTURE_REFERENCE.md
    """
    _, bq_client = authenticate()
    
    query = f"""
    WITH latest_batch AS (
        -- Get the most recent publishTime from IRIS (no time filter)
        -- IRIS pipeline may be delayed/stopped, use whatever is latest
        SELECT MAX(publishTime) as latest_time
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    )
    SELECT 
        f.fuelType,
        ROUND(f.generation, 1) as generation_mw,  -- Already in MW!
        f.publishTime
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris` f
    CROSS JOIN latest_batch lb
    WHERE f.publishTime = lb.latest_time
      AND UPPER(f.fuelType) NOT LIKE 'INT%'  -- Exclude interconnectors
    ORDER BY f.generation DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    return df

def get_live_interconnectors():
    """Get latest interconnector flows using IRIS real-time tables
    
    Architecture: Interconnectors appear as fuelType LIKE 'INT%' in bmrs_fuelinst_iris.
    Positive values = import to UK, negative = export from UK.
    
    Reference: IRIS table uses TIMESTAMP (not DATETIME like historical)
    """
    _, bq_client = authenticate()
    
    query = f"""
    WITH latest_batch AS (
        -- Get absolute latest publishTime (IRIS may be delayed)
        SELECT MAX(publishTime) as latest_time
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    )
    SELECT 
        f.fuelType,
        ROUND(f.generation, 0) as flow_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris` f
    CROSS JOIN latest_batch lb
    WHERE f.publishTime = lb.latest_time
      AND UPPER(f.fuelType) LIKE 'INT%'  -- Only interconnectors
    ORDER BY ABS(f.generation) DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    return df

def get_total_demand():
    """Calculate total demand from latest generation data using IRIS
    
    Architecture: Sum all generation values from latest publishTime batch in IRIS.
    Returns MW, caller converts to GW for display.
    
    Reference: IRIS table has 198k+ rows updated to Dec 5, 2025
    """
    _, bq_client = authenticate()
    
    query = f"""
    WITH latest_batch AS (
        -- Get absolute latest publishTime (IRIS may be delayed)
        SELECT MAX(publishTime) as latest_time
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    )
    SELECT 
        ROUND(SUM(f.generation), 1) as total_mw,  -- Sum in MW
        MAX(f.publishTime) as latest_time
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris` f
    CROSS JOIN latest_batch lb
    WHERE f.publishTime = lb.latest_time
    """
    
    df = bq_client.query(query).to_dataframe()
    if len(df) > 0 and df.iloc[0]['total_mw'] > 0:
        return df.iloc[0]
    else:
        return {'total_mw': 0, 'latest_time': datetime.now()}

def map_fuel_to_emoji(fuel_type):
    """Map fuel types to emojis (matching existing sheet format)"""
    emoji_map = {
        'CCGT': '🔥',
        'WIND': '💨',
        'NUCLEAR': '⚛️',
        'PS': '💧',
        'BIOMASS': '🌱',
        'COAL': '⚫',
        'NPSHYD': '💧',
        'OIL': '🛢️',
        'OCGT': '🔥',
        'OTHER': '❓',
        'INTFR': '🇫🇷',
        'INTIRL': '🇮🇪',
        'INTNED': '🇳🇱',
        'INTEW': '🏴󐁧󐁢󐁥󐁮󐁧󐁿',
        'INTNEM': '🇧🇪',
        'INTELEC': '⚡',
        'INTNSL': '🇳🇴',
        'INTIFA2': '🇫🇷',
        'INTVKL': '🇩🇰'
    }
    
    base_fuel = fuel_type.upper().replace('_', '')
    return emoji_map.get(base_fuel, '❓')

def map_interconnector_name(bmunit_id):
    """Map bmUnitId to friendly interconnector name"""
    ic_map = {
        'INTFR': '🇫🇷 INTFR',
        'INTIRL': '🇮🇪 INTIRL',
        'INTNED': '🇳🇱 INTNED',
        'INTEW': '🏴󐁧󐁢󐁥󐁮󐁧󐁿 INTEW',
        'INTNEM': '🇧🇪 INTNEM',
        'INTELEC': '⚡ INTELEC',
        'INTNSL': '🇳🇴 INTNSL',
        'INTIFA2': '🇫🇷 INTIFA2',
        'INTVKL': '🇩🇰 INTVKL'
    }
    
    for key in ic_map:
        if key in bmunit_id.upper():
            return ic_map[key]
    
    return bmunit_id

def update_bg_live_sheet():
    """Update BG Live sheet with latest data while preserving structure"""
    print("🔄 Updating BG Live sheet with real-time data...")
    print("=" * 80)
    
    # Authenticate
    sheets_client, _ = authenticate()
    sheet = sheets_client.open_by_key(SHEET_ID)
    ws = sheet.worksheet(SHEET_NAME)
    
    # Get live data
    print("📊 Fetching live generation data...")
    gen_df = get_live_generation()
    
    if len(gen_df) == 0:
        print("⚠️  No generation data found - check BigQuery tables")
        return
    
    print("🔌 Fetching interconnector flows...")
    ic_df = get_live_interconnectors()
    
    print("⚡ Calculating total demand...")
    demand_data = get_total_demand()
    
    total_mw = demand_data['total_mw']
    total_gw = total_mw / 1000.0  # Convert MW to GW
    latest_time = demand_data['latest_time']
    
    print(f"\n✅ Data retrieved:")
    print(f"   Total Generation: {total_gw:.2f} GW ({total_mw:.0f} MW)")
    print(f"   Latest Time: {latest_time}")
    print(f"   Fuel Types: {len(gen_df)}")
    print(f"   Interconnectors: {len(ic_df)}")
    
    # Update timestamp (Row 2)
    timestamp_str = f"Live Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws.update(range_name='A2', values=[[timestamp_str]])
    print(f"\n🕐 Updated timestamp: {timestamp_str}")
    
    # Update total generation (Row 7)
    total_gen_str = f"Total Gen: {total_gw:.2f} GW"
    ws.update(range_name='A7', values=[[total_gen_str]])
    print(f"📊 Updated total generation: {total_gen_str}")
    
    # Update fuel type data (starting Row 10)
    print("\n🔥 Updating fuel type breakdown...")
    fuel_data = []
    for idx, row in gen_df.iterrows():
        fuel_type = row['fuelType']
        gen_mw = row['generation_mw']  # Already in MW
        gen_gw = gen_mw / 1000.0
        percentage = gen_mw / total_mw if total_mw > 0 else 0
        
        emoji = map_fuel_to_emoji(fuel_type)
        fuel_name = f"{emoji} {fuel_type}"
        
        fuel_data.append([
            fuel_name,
            int(gen_mw),  # MW as integer
            percentage    # Percentage as decimal
        ])
    
    if fuel_data:
        # Update starting from row 10, columns A-C
        start_row = 10
        ws.update(range_name=f'A{start_row}:C{start_row + len(fuel_data) - 1}', 
                 values=fuel_data)
        print(f"   ✅ Updated {len(fuel_data)} fuel types")
    
    # Update interconnector data (starting Row 10, columns D-E)
    print("\n🔌 Updating interconnector flows...")
    ic_data = []
    for idx, row in ic_df.iterrows():
        fuel_type = row['fuelType']
        flow = row['flow_mw']
        
        ic_name = map_interconnector_name(fuel_type)
        ic_data.append([
            ic_name,
            int(flow)
        ])
    
    if ic_data:
        # Update starting from row 10, columns D-E
        start_row = 10
        ws.update(range_name=f'D{start_row}:E{start_row + len(ic_data) - 1}', 
                 values=ic_data)
        print(f"   ✅ Updated {len(ic_data)} interconnectors")
    
    print("\n" + "=" * 80)
    print("✅ BG Live sheet updated successfully!")
    print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0")
    print(f"⏱️  Data from: {latest_time}")
    print("=" * 80)

if __name__ == '__main__':
    try:
        update_bg_live_sheet()
    except Exception as e:
        print(f"\n❌ Error updating sheet: {e}")
        import traceback
        traceback.print_exc()
