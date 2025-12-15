#!/usr/bin/env python3
"""
Quick GB Live Dashboard Updater - Uses Real IRIS Data
Updates the main dashboard with current generation, pricing, and frequency data
"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime, timedelta

# Config
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SHEET_NAME = "Dashboard"
CREDS_FILE = "/home/george/.config/google-cloud/bigquery-credentials.json"

def get_latest_data():
    """Fetch latest real-time data from IRIS tables"""
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/bigquery",
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = bigquery.Client(project=PROJECT_ID, credentials=creds)
    
    # Get most recent settlement period with data
    latest_sp_query = """
    SELECT 
        CAST(settlementDate AS DATE) as date,
        MAX(settlementPeriod) as max_sp
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
    GROUP BY date
    ORDER BY date DESC
    LIMIT 1
    """
    latest_sp_df = client.query(latest_sp_query).result().to_dataframe()
    
    if latest_sp_df.empty:
        print("❌ No recent data found")
        return None
        
    latest_date = latest_sp_df['date'][0]
    latest_sp = int(latest_sp_df['max_sp'][0])
    
    print(f"📊 Fetching data for {latest_date}, SP {latest_sp}")
    
    # 1. Generation Mix (MW -> GW)
    gen_query = f"""
    SELECT 
        fuelType,
        ROUND(SUM(generation) / 1000.0, 2) as generation_gw
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = '{latest_date}'
        AND settlementPeriod = {latest_sp}
        AND fuelType IN ('WIND', 'NUCLEAR', 'CCGT', 'BIOMASS', 'COAL', 'HYDRO', 'NPSHYD', 'OCGT', 'OIL', 'PS', 'OTHER', 'INTFR', 'INTIRL', 'INTNED', 'INTEW', 'INTNEM', 'INTELEC', 'INTNSL')
    GROUP BY fuelType
    ORDER BY generation_gw DESC
    """
    gen_df = client.query(gen_query).result().to_dataframe()
    
    # 2. Wholesale Price (average of non-zero prices for the SP)
    price_query = f"""
    SELECT 
        AVG(price) as avg_price
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
    WHERE CAST(settlementDate AS DATE) = '{latest_date}'
        AND settlementPeriod = {latest_sp}
        AND price > 0
    """
    price_df = client.query(price_query).result().to_dataframe()
    wholesale_price = round(price_df['avg_price'][0], 2) if not price_df.empty and price_df['avg_price'][0] is not None else 0.0
    
    # 3. Grid Frequency (from bmrs_freq_iris - use measurementTime column)
    freq_query = """
    SELECT 
        AVG(frequency) as avg_frequency
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
    WHERE DATE(measurementTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    """
    freq_df = client.query(freq_query).result().to_dataframe()
    grid_frequency = round(freq_df['avg_frequency'][0], 2) if not freq_df.empty and freq_df['avg_frequency'][0] is not None else 50.0
    
    # Calculate totals
    total_generation = round(gen_df['generation_gw'].sum(), 2)
    wind_output = round(gen_df[gen_df['fuelType'] == 'WIND']['generation_gw'].sum(), 2) if 'WIND' in gen_df['fuelType'].values else 0.0
    
    # Assume demand ~= generation (close approximation for GB)
    system_demand = total_generation
    
    return {
        'wholesale_price': wholesale_price,
        'grid_frequency': grid_frequency,
        'total_generation': total_generation,
        'wind_output': wind_output,
        'system_demand': system_demand,
        'generation_mix': gen_df,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def update_sheet(data):
    """Update Google Sheet with real data"""
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SHEET_NAME)
    
    # Update KPI values (adjust ranges based on your sheet layout)
    # These are example locations - you'll need to verify the actual cells
    ws.update('B4', [[data['wholesale_price']]])  # Wholesale Price
    ws.update('E4', [[data['grid_frequency']]])    # Grid Frequency
    ws.update('H4', [[data['total_generation']]])  # Total Generation
    ws.update('K4', [[data['wind_output']]])       # Wind Output
    ws.update('N4', [[data['system_demand']]])     # System Demand
    
    print(f"✅ Dashboard updated at {data['timestamp']}")
    print(f"   💨 Wholesale: £{data['wholesale_price']}/MWh")
    print(f"   💓 Frequency: {data['grid_frequency']} Hz")
    print(f"   🏭 Generation: {data['total_generation']} GW")
    print(f"   🌬️  Wind: {data['wind_output']} GW")
    print(f"   🔌 Demand: {data['system_demand']} GW")

if __name__ == "__main__":
    try:
        print("🚀 Starting GB Live Dashboard Update...")
        data = get_latest_data()
        if data:
            update_sheet(data)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
