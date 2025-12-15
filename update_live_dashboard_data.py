#!/usr/bin/env python3
"""
Update Live Dashboard v2 data source rows with latest settlement periods
Populates rows 20-24 with last 48 settlement periods from BigQuery
Uses IRIS real-time data when available
"""

from google.cloud import bigquery
import gspread
from datetime import datetime, timedelta
import json
from pathlib import Path

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"
IRIS_DATA_DIR = Path("/home/george/GB-Power-Data/iris_windows_deployment/iris_client/python/iris_data")

def get_latest_iris_freq():
    """Get latest frequency data from IRIS JSON files"""
    freq_dir = IRIS_DATA_DIR / "FREQ"
    if not freq_dir.exists():
        return []
    
    # Get last 10 FREQ files (covers ~20 minutes of data)
    freq_files = sorted(freq_dir.glob("FREQ_*.json"), reverse=True)[:10]
    freq_data = []
    
    for file in freq_files:
        try:
            with open(file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    freq_data.extend(data)
                elif isinstance(data, dict) and 'data' in data:
                    freq_data.extend(data['data'])
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    return freq_data

def get_latest_iris_generation():
    """Get latest generation data from IRIS JSON files"""
    fuel_dir = IRIS_DATA_DIR / "FUELINST"
    if not fuel_dir.exists():
        return []
    
    # Get last 48 FUELINST files (covers 24 hours, updated every 30 min)
    fuel_files = sorted(fuel_dir.glob("FUELINST_*.json"), reverse=True)[:48]
    gen_data = []
    
    for file in fuel_files:
        try:
            with open(file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    gen_data.extend(data)
                elif isinstance(data, dict) and 'data' in data:
                    gen_data.extend(data['data'])
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    return gen_data

def get_latest_48_periods():
    """Query BigQuery + IRIS for last 48 settlement periods"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get pricing data from BigQuery (goes back 7 days to ensure we get data)
    query = f"""
    SELECT 
        DATE(settlementDate) as date,
        settlementPeriod as sp,
        AVG(systemSellPrice) as system_price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY date, sp
    ORDER BY date DESC, sp DESC
    LIMIT 48
    """
    
    print("Querying BigQuery for last 48 settlement periods (prices)...")
    df = client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} settlement periods from BigQuery")
    
    # Get real-time IRIS data
    print("\nFetching IRIS real-time data...")
    freq_data = get_latest_iris_freq()
    gen_data = get_latest_iris_generation()
    
    print(f"✅ Retrieved {len(freq_data)} FREQ records from IRIS")
    print(f"✅ Retrieved {len(gen_data)} FUELINST records from IRIS")
    
    # Process IRIS frequency data (last value only for simplicity)
    if freq_data:
        latest_freq = freq_data[0].get('frequency', 50.0) if isinstance(freq_data[0], dict) else 50.0
        df['avg_freq'] = latest_freq
    else:
        df['avg_freq'] = 50.0
    
    # Process IRIS generation data (aggregate by fuel type)
    wind_gen = 0
    gas_gen = 0
    nuclear_gen = 0
    
    if gen_data:
        for record in gen_data[:20]:  # Last 20 records
            if isinstance(record, dict):
                fuel = record.get('fuelType', '').upper()
                gen = float(record.get('generation', 0))
                if 'WIND' in fuel:
                    wind_gen += gen
                elif 'CCGT' in fuel or 'GAS' in fuel:
                    gas_gen += gen
                elif 'NUCLEAR' in fuel:
                    nuclear_gen += gen
        
        # Average across records
        wind_gen /= min(20, len(gen_data))
        gas_gen /= min(20, len(gen_data))
        nuclear_gen /= min(20, len(gen_data))
    
    df['wind_gen'] = wind_gen / 1000  # Convert MW to GW
    df['gas_gen'] = gas_gen / 1000
    df['nuclear_gen'] = nuclear_gen / 1000
    
    print(f"\n📊 IRIS Live Data:")
    print(f"   Frequency: {df['avg_freq'].iloc[0]:.3f} Hz")
    print(f"   Wind: {wind_gen/1000:.2f} GW")
    print(f"   Gas: {gas_gen/1000:.2f} GW")
    print(f"   Nuclear: {nuclear_gen/1000:.2f} GW")
    
    return df

def update_dashboard(df):
    """Update Google Sheets rows 20-24 with data"""
    gc = gspread.service_account(filename='/home/george/inner-cinema-credentials.json')
    
    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    
    print(f"\nUpdating '{SHEET_NAME}' data source rows...")
    
    # Prepare data arrays (reverse order for sparklines - oldest to newest)
    system_prices = df['system_price'].tolist()[::-1]
    frequencies = df['avg_freq'].tolist()[::-1]
    wind_gen = df['wind_gen'].tolist()[::-1]
    total_demand = [wind + gas + nuclear for wind, gas, nuclear 
                    in zip(df['wind_gen'], df['gas_gen'], df['nuclear_gen'])][::-1]
    
    # Calculate frequency deviation from 50Hz
    freq_deviations = [freq - 50.0 if freq else 0 for freq in frequencies]
    
    # Update rows 20-24 (each row = one metric, 48 columns wide)
    updates = [
        {'range': 'A20:AV20', 'values': [system_prices]},      # System price
        {'range': 'A21:AV21', 'values': [freq_deviations]},    # Frequency deviation
        {'range': 'A22:AV22', 'values': [total_demand]},       # Total demand
        {'range': 'A23:AV23', 'values': [wind_gen]},           # Wind generation
        {'range': 'A24:AV24', 'values': [total_demand]},       # Demand again (K7 duplicate)
    ]
    
    for update in updates:
        sheet.update(update['range'], update['values'])
    
    print("✅ Row 20: System prices (48 values)")
    print("✅ Row 21: Frequency deviations (48 values)")
    print("✅ Row 22: Total demand (48 values)")
    print("✅ Row 23: Wind generation (48 values)")
    print("✅ Row 24: Total demand duplicate (48 values)")
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.update('A25', [[f"Last updated: {timestamp}"]])
    print(f"\n✅ Dashboard data updated at {timestamp}")
    
    return True

def main():
    print("="*80)
    print("📊 UPDATING LIVE DASHBOARD V2 DATA")
    print("="*80)
    
    try:
        # Get data from BigQuery
        df = get_latest_48_periods()
        
        if df.empty:
            print("⚠️  No data retrieved from BigQuery")
            return
        
        # Update Google Sheets
        update_dashboard(df)
        
        print("\n" + "="*80)
        print("✅ UPDATE COMPLETE")
        print("="*80)
        print(f"\nSparklines should now display:")
        print(f"  C7: System price trend (last 48 SPs)")
        print(f"  E7: Frequency deviation from 50Hz")
        print(f"  G7: Total demand (Wind+Gas+Nuclear)")
        print(f"  I7: Wind generation")
        print(f"  K7: Total demand (duplicate)")
        print(f"\nView: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
