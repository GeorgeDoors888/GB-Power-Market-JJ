#!/usr/bin/env python3
"""
Update BOTH GB Live Dashboards with Real-Time IRIS Data
- Main Dashboard (12jY0d4jzD6...)
- BtM Calculator Dashboard (1-u794i...)
"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime

# Config
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_FILE = "/home/george/.config/google-cloud/bigquery-credentials.json"

# Both dashboards - CORRECTED CELL LOCATIONS
DASHBOARDS = [
    {
        'name': 'Main Dashboard - Dashboard V3',
        'spreadsheet_id': '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8',
        'sheet_name': 'Dashboard V3',
        'cells': {
            'wholesale': 'C5',  # Wholesale Price cell
            'frequency': 'E5',  # Grid Frequency
            'generation': 'G5', # Total Generation
            'wind': 'I5',       # Wind Output
            'demand': 'K5',     # System Demand
            'timestamp': 'B2'   # Last Updated timestamp
        }
    },
    {
        'name': 'BtM Calculator - Live Dashboard v2',
        'spreadsheet_id': '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
        'sheet_name': 'Live Dashboard v2',
        'cells': {
            'wholesale': 'C6',  # Wholesale Price
            'frequency': 'E6',  # Grid Frequency
            'generation': 'G6', # Total Generation
            'wind': 'I6',       # Wind Output
            'demand': 'K6',     # System Demand
            'timestamp': 'B2'   # Last Updated timestamp
        }
    },
    {
        'name': 'BtM Calculator - GB Live',
        'spreadsheet_id': '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
        'sheet_name': 'GB Live',
        'cells': {
            'wholesale': 'B4',  # Total BESS revenue (repurpose for wholesale)
            'frequency': 'E4',  # Total charging cost (repurpose for frequency)
            'generation': 'H4', # Net margin (repurpose for generation)
            'wind': 'K4',       # Unused cell for wind
            'demand': 'B5',     # Total discharged (repurpose for demand)
            'timestamp': 'B2'   # Date cell
        }
    }
]

def get_latest_iris_data():
    """Fetch latest available data from IRIS or historical tables"""
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/bigquery",
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = bigquery.Client(project=PROJECT_ID, credentials=creds)
    
    # Try IRIS first, fall back to historical if IRIS is stale
    latest_sp_query = """
    WITH iris_data AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            MAX(settlementPeriod) as max_sp,
            'IRIS' as source
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        GROUP BY date
    ),
    historical_data AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            MAX(settlementPeriod) as max_sp,
            'Historical' as source
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
        WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        GROUP BY date
    )
    SELECT * FROM iris_data
    UNION ALL
    SELECT * FROM historical_data
    ORDER BY date DESC, max_sp DESC
    LIMIT 1
    """
    latest_sp_df = client.query(latest_sp_query).result().to_dataframe()
    
    if latest_sp_df.empty:
        print("❌ No recent data found in IRIS or historical tables")
        return None
        
    latest_date = latest_sp_df['date'][0]
    latest_sp = int(latest_sp_df['max_sp'][0])
    data_source = latest_sp_df['source'][0]
    
    print(f"📊 Fetching data for {latest_date}, SP {latest_sp} (Source: {data_source})")
    
    # Choose table suffix based on source
    table_suffix = '_iris' if data_source == 'IRIS' else ''
    
    # 1. Generation Mix (MW -> GW)
    gen_query = f"""
    SELECT 
        fuelType,
        ROUND(SUM(generation) / 1000.0, 2) as generation_gw
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst{table_suffix}`
    WHERE CAST(settlementDate AS DATE) = '{latest_date}'
        AND settlementPeriod = {latest_sp}
    GROUP BY fuelType
    ORDER BY generation_gw DESC
    """
    gen_df = client.query(gen_query).result().to_dataframe()
    
    # 2. Wholesale Price
    price_query = f"""
    SELECT 
        AVG(price) as avg_price
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid{table_suffix}`
    WHERE CAST(settlementDate AS DATE) = '{latest_date}'
        AND settlementPeriod = {latest_sp}
        AND price > 0
    """
    price_df = client.query(price_query).result().to_dataframe()
    wholesale_price = round(price_df['avg_price'][0], 2) if not price_df.empty and price_df['avg_price'][0] is not None else 0.0
    
    # 3. Grid Frequency (from appropriate source)
    if data_source == 'IRIS':
        freq_query = """
        SELECT 
            AVG(frequency) as avg_frequency
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
        WHERE DATE(measurementTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        """
    else:
        freq_query = f"""
        SELECT 
            AVG(frequency) as avg_frequency
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
        WHERE CAST(dataProviderPublishTime AS DATE) = '{latest_date}'
        """
    freq_df = client.query(freq_query).result().to_dataframe()
    grid_frequency = round(freq_df['avg_frequency'][0], 2) if not freq_df.empty and freq_df['avg_frequency'][0] is not None else 50.0
    
    # Calculate totals
    total_generation = round(gen_df['generation_gw'].sum(), 2)
    wind_output = round(gen_df[gen_df['fuelType'] == 'WIND']['generation_gw'].sum(), 2) if 'WIND' in gen_df['fuelType'].values else 0.0
    system_demand = total_generation  # Approximation
    
    return {
        'wholesale_price': wholesale_price,
        'grid_frequency': grid_frequency,
        'total_generation': total_generation,
        'wind_output': wind_output,
        'system_demand': system_demand,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': latest_date,
        'sp': latest_sp,
        'source': data_source
    }

def update_dashboard(dashboard, data):
    """Update a single dashboard with real data"""
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    
    try:
        sh = gc.open_by_key(dashboard['spreadsheet_id'])
        ws = sh.worksheet(dashboard['sheet_name'])
        
        # Update timestamp if configured
        if 'timestamp' in dashboard['cells']:
            ws.update(values=[[data['timestamp']]], range_name=dashboard['cells']['timestamp'])
        
        # Update cells
        updates = []
        updates.append({'range': dashboard['cells']['wholesale'], 'values': [[data['wholesale_price']]]})
        updates.append({'range': dashboard['cells']['frequency'], 'values': [[data['grid_frequency']]]})
        updates.append({'range': dashboard['cells']['generation'], 'values': [[data['total_generation']]]})
        updates.append({'range': dashboard['cells']['wind'], 'values': [[data['wind_output']]]})
        updates.append({'range': dashboard['cells']['demand'], 'values': [[data['system_demand']]]})
        
        # Batch update
        for update in updates:
            ws.update(values=update['values'], range_name=update['range'])
        
        print(f"✅ {dashboard['name']} updated ({dashboard['sheet_name']} sheet)")
        
    except Exception as e:
        print(f"❌ Failed to update {dashboard['name']}: {e}")

if __name__ == "__main__":
    try:
        print("🚀 Starting BOTH Dashboard Updates...")
        print("=" * 60)
        
        data = get_latest_iris_data()
        
        if data:
            print(f"\n📈 Latest Available Data (SP {data['sp']} on {data['date']}, Source: {data['source']}):")
            print(f"   💨 Wholesale: £{data['wholesale_price']}/MWh")
            print(f"   💓 Frequency: {data['grid_frequency']} Hz")
            print(f"   🏭 Generation: {data['total_generation']} GW")
            print(f"   🌬️  Wind: {data['wind_output']} GW")
            print(f"   🔌 Demand: {data['system_demand']} GW")
            
            if data['source'] == 'Historical':
                print(f"\n⚠️  WARNING: Using historical data - IRIS pipeline offline!")
                print(f"   IRIS server (94.237.55.234) unreachable")
            print()
            
            for dashboard in DASHBOARDS:
                update_dashboard(dashboard, data)
                
            print(f"\n🎉 All dashboards updated at {data['timestamp']}")
        else:
            print("⚠️ No data available to update")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
