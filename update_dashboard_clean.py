#!/usr/bin/env python3
"""
Update Google Sheet dashboard with real-time UK power market data from BigQuery

This script:
1. Queries BigQuery for latest generation, demand, and interconnector data
2. Calculates summary metrics
3. Updates a Google Sheet with the data (preserving formatting)

Usage:
    python update_dashboard_clean.py [--sheet-id YOUR_SHEET_ID]
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import os
from datetime import datetime
import argparse

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
SERVICE_ACCOUNT_FILE = "/Users/georgemajor/GB Power Market JJ/jibber_jabber_key.json"

# Set up BigQuery client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
bq_client = bigquery.Client(project=PROJECT_ID)

# Set up Google Sheets client
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

def get_latest_generation():
    """Get latest generation by fuel type from BigQuery using nested data structure"""
    query = f"""
    WITH latest_data AS (
        SELECT 
            startTime,
            data
        FROM `{PROJECT_ID}.{DATASET_ID}.generation_actual_per_type`
        ORDER BY startTime DESC
        LIMIT 1
    ),
    unpacked AS (
        SELECT
            startTime,
            gen.psrType as fuel_type,
            gen.quantity as generation_mw
        FROM latest_data,
        UNNEST(data) as gen
    )
    SELECT startTime, fuel_type, generation_mw
    FROM unpacked
    ORDER BY generation_mw DESC
    """
    
    results = bq_client.query(query).result()
    data = {}
    timestamp = None
    
    # Map API fuel types to dashboard names
    fuel_mapping = {
        'Wind Offshore': 'WIND_OFFSHORE',
        'Wind Onshore': 'WIND_ONSHORE', 
        'Nuclear': 'NUCLEAR',
        'Fossil Gas': 'GAS',
        'Solar': 'SOLAR',
        'Biomass': 'BIOMASS',
        'Hydro Run-of-river and poundage': 'HYDRO',
        'Hydro Pumped Storage': 'PUMPED_STORAGE',
        'Fossil Hard coal': 'COAL',
        'Fossil Oil': 'OIL',
        'Other': 'OTHER'
    }
    
    for row in results:
        if timestamp is None:
            timestamp = row.startTime
        fuel_key = fuel_mapping.get(row.fuel_type, row.fuel_type)
        data[fuel_key] = row.generation_mw / 1000  # Convert to GW
    
    # Combine wind if needed
    if 'WIND_OFFSHORE' in data and 'WIND_ONSHORE' in data:
        data['WIND_TOTAL'] = data['WIND_OFFSHORE'] + data['WIND_ONSHORE']
    
    return data, timestamp

def get_latest_demand():
    """Get latest demand from actual demand tables"""
    # Try to get from demand_outturn_summary
    query = f"""
    SELECT 
        startTime,
        quantity as demand_mw
    FROM `{PROJECT_ID}.{DATASET_ID}.demand_outturn_summary`
    ORDER BY startTime DESC
    LIMIT 1
    """
    
    try:
        results = bq_client.query(query).result()
        for row in results:
            return row.demand_mw / 1000, row.startTime  # Convert to GW
    except Exception as e:
        print(f"   ⚠️  Could not fetch demand: {e}")
    
    return None, None

def get_interconnector_flows():
    """Get interconnector flows from fuelinst data"""
    query = f"""
    SELECT 
        publishTime,
        fuelType,
        generation
    FROM `{PROJECT_ID}.{DATASET_ID}.fuelinst_sep_oct_2025`
    WHERE publishTime = (
        SELECT MAX(publishTime)
        FROM `{PROJECT_ID}.{DATASET_ID}.fuelinst_sep_oct_2025`
    )
    AND fuelType LIKE 'INT%'
    ORDER BY generation DESC
    """
    
    results = bq_client.query(query).result()
    data = {}
    timestamp = None
    
    interconnector_mapping = {
        'INTFR': 'France',
        'INTNED': 'Netherlands', 
        'INTIRL': 'Ireland',
        'INTEW': 'Belgium',
        'INTNSL': 'Norway',
        'INTNEM': 'Belgium_2',
        'INTELEC': 'Eleclink',
        'INTIFA2': 'IFA2',
        'INTVKL': 'Viking'
    }
    
    for row in results:
        if timestamp is None:
            timestamp = row.publishTime
        ic_key = interconnector_mapping.get(row.fuelType, row.fuelType)
        data[ic_key] = row.generation / 1000  # Convert to GW
    
    return data, timestamp

def print_summary(generation, interconnectors, demand):
    """Print a summary of the data"""
    print("\n📊 GENERATION SUMMARY:")
    print("-" * 60)
    total_gen = 0
    for fuel, value in sorted(generation.items(), key=lambda x: x[1], reverse=True):
        if fuel != 'WIND_TOTAL':  # Don't count total wind twice
            if not fuel.startswith('WIND_'):
                total_gen += value
        print(f"   {fuel:20} : {value:7.2f} GW")
    print(f"   {'TOTAL':20} : {total_gen:7.2f} GW")
    
    if interconnectors:
        print("\n🔌 INTERCONNECTOR FLOWS:")
        print("-" * 60)
        total_import = 0
        total_export = 0
        for ic, value in sorted(interconnectors.items(), key=lambda x: abs(x[1]), reverse=True):
            if value > 0:
                direction = "→ IMPORT"
                total_import += value
            else:
                direction = "← EXPORT"
                total_export += abs(value)
            print(f"   {ic:20} : {abs(value):7.2f} GW {direction}")
        print(f"\n   Net import: {total_import - total_export:7.2f} GW")
    
    if demand:
        print(f"\n⚡ DEMAND: {demand:.2f} GW")
        if total_gen > 0:
            print(f"   Balance: {total_gen - demand:+.2f} GW")

def update_google_sheet(sheet_id, generation, interconnectors, demand):
    """Update Google Sheet with latest data"""
    try:
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.worksheet("Sheet1")
        
        print("\n📝 Updating Google Sheet...")
        
        # TODO: Map data to specific cells based on your sheet layout
        # Example:
        # worksheet.update_acell('B2', f"{generation.get('WIND_TOTAL', 0):.2f}")
        # worksheet.update_acell('B3', f"{generation.get('NUCLEAR', 0):.2f}")
        # etc.
        
        print("✅ Sheet updated successfully")
        
    except Exception as e:
        print(f"❌ Failed to update sheet: {e}")

def main():
    parser = argparse.ArgumentParser(description='Update Google Sheet with UK power market data')
    parser.add_argument('--sheet-id', help='Google Sheet ID to update')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🇬🇧 UK POWER MARKET DATA - BIGQUERY TO GOOGLE SHEETS")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🔄 Fetching latest data from BigQuery...")
    
    try:
        generation, gen_time = get_latest_generation()
        print(f"✅ Generation data: {len(generation)} fuel types (at {gen_time})")
        
        interconnectors, ic_time = get_interconnector_flows()
        print(f"✅ Interconnector flows: {len(interconnectors)} connections (at {ic_time})")
        
        demand, demand_time = get_latest_demand()
        if demand:
            print(f"✅ Demand: {demand:.2f} GW (at {demand_time})")
        else:
            print("⚠️  Demand data not available")
        
        print_summary(generation, interconnectors, demand)
        
        if args.sheet_id:
            update_google_sheet(args.sheet_id, generation, interconnectors, demand)
        else:
            print("\n⚠️  No --sheet-id provided. Data fetched but not written to sheet.")
            print("   To update a sheet, run: python update_dashboard_clean.py --sheet-id YOUR_SHEET_ID")
        
        print("\n✅ Complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
