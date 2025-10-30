#!/usr/bin/env python3
"""
Update Google Sheet dashboard with real-time data from BigQuery
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import os
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
SHEET_ID = "YOUR_SHEET_ID_HERE"  # Replace with actual Google Sheet ID
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
    SELECT fuel_type, generation_mw
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
        fuel_key = fuel_mapping.get(row.fuel_type, row.fuel_type)
        data[fuel_key] = row.generation_mw / 1000  # Convert to GW
    
    # Combine wind if needed
    if 'WIND_OFFSHORE' in data and 'WIND_ONSHORE' in data:
        data['WIND'] = data['WIND_OFFSHORE'] + data['WIND_ONSHORE']
    
    return data

def get_latest_frequency():
    """Get latest grid frequency from fuelinst table"""
    # Note: frequency data may not be in our current tables
    # This is a placeholder - adjust based on actual data availability
    return None  # TODO: Find frequency data in tables

def get_latest_demand():
    """Get latest demand from actual demand tables"""
    query = f"""
    SELECT 
        quantity as demand_mw
    FROM `{PROJECT_ID}.{DATASET_ID}.demand_outturn_summary`
    ORDER BY settlementPeriod DESC
    LIMIT 1
    """
    
    try:
        results = bq_client.query(query).result()
        for row in results:
            return row.demand_mw / 1000  # Convert to GW
    except:
        pass
    
    return None

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
    """
    
    results = bq_client.query(query).result()
    data = {}
    
    interconnector_mapping = {
        'INTFR': 'France',
        'INTNED': 'Netherlands', 
        'INTIRL': 'Ireland',
        'INTEW': 'Belgium',
        'INTNSL': 'Norway',
        'INTNEM': 'Belgium_2',
        'INTELEC': 'Eleclink'
    }
    
    for row in results:
        ic_key = interconnector_mapping.get(row.fuelType, row.fuelType)
        data[ic_key] = row.generation / 1000  # Convert to GW
    
    return data

def update_sheet():
    """Update the Google Sheet with latest data"""
    print("🔄 Fetching latest data from BigQuery...")
    
    # Get data
    generation = get_latest_generation()
    interconnectors = get_interconnector_flows()
    demand = get_latest_demand()
    
    print(f"✅ Fetched generation data for {len(generation)} fuel types")
    if interconnectors:
        print(f"✅ Fetched {len(interconnectors)} interconnector flows")
    if demand:
        print(f"✅ Demand: {demand:.2f} GW")
    
    # Print summary
    print("\n📊 GENERATION SUMMARY:")
    for fuel, value in sorted(generation.items(), key=lambda x: x[1], reverse=True):
        print(f"   {fuel:20} : {value:6.2f} GW")
    
    if interconnectors:
        print("\n🔌 INTERCONNECTOR FLOWS:")
        for ic, value in interconnectors.items():
            direction = "→ IMPORT" if value > 0 else "← EXPORT"
            print(f"   {ic:20} : {abs(value):6.2f} GW {direction}")
    
    # Open the spreadsheet (when you provide the SHEET_ID)
    # sheet = gc.open_by_key(SHEET_ID)
    # worksheet = sheet.worksheet("Sheet1")
    # ... update cells based on your layout
    
    print(f"\n✅ Data fetched at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️  To update Google Sheet, replace SHEET_ID with your actual sheet ID")

if __name__ == "__main__":
    try:
        update_sheet()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def get_latest_generation_data():
    """Query BigQuery for latest generation by fuel type"""
    query = """
    SELECT 
        fuelType,
        generation,
        publishTime
    FROM `inner-cinema-476211-u9.uk_energy_prod.generation_fuel_instant`
    WHERE publishTime = (
        SELECT MAX(publishTime) 
        FROM `inner-cinema-476211-u9.uk_energy_prod.generation_fuel_instant`
    )
    ORDER BY generation DESC
    """
    
    results = bq_client.query(query).result()
    
    generation_data = {}
    for row in results:
        generation_data[row.fuelType] = row.generation
    
    return generation_data


def get_latest_frequency():
    """Query BigQuery for latest system frequency"""
    query = """
    SELECT 
        frequency,
        startTime
    FROM `inner-cinema-476211-u9.uk_energy_prod.system_frequency`
    WHERE startTime = (
        SELECT MAX(startTime) 
        FROM `inner-cinema-476211-u9.uk_energy_prod.system_frequency`
    )
    LIMIT 1
    """
    
    results = bq_client.query(query).result()
    
    for row in results:
        return row.frequency
    
    return 50.0


def get_latest_demand():
    """Query BigQuery for latest demand data"""
    query = """
    SELECT 
        demand,
        publishTime
    FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn`
    WHERE publishTime = (
        SELECT MAX(publishTime) 
        FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn`
    )
    LIMIT 1
    """
    
    results = bq_client.query(query).result()
    
    for row in results:
        return row.demand / 1000  # Convert MW to GW
    
    return 0.0


def get_interconnector_flows():
    """Query BigQuery for interconnector data"""
    # This would need the interconnector flows table
    # For now, returning placeholder data
    return {
        'IFA': 2.0,
        'IFA2': 1.0,
        'BritNed': 1.0,
        'Nemo': 1.0,
        'NSL': 1.4,
        'Moyle': 0.5
    }


def calculate_metrics(generation_data, demand):
    """Calculate derived metrics"""
    # Total generation
    total_generation = sum(generation_data.values()) / 1000  # Convert MW to GW
    
    # Low carbon (Nuclear + Wind + Solar + Hydro + Biomass)
    low_carbon = 0
    for fuel in ['NUCLEAR', 'WIND', 'SOLAR', 'HYDRO', 'BIOMASS']:
        low_carbon += generation_data.get(fuel, 0)
    low_carbon_pct = (low_carbon / sum(generation_data.values())) * 100 if sum(generation_data.values()) > 0 else 0
    
    # Renewable (Wind + Solar + Hydro + Biomass)
    renewable = 0
    for fuel in ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS']:
        renewable += generation_data.get(fuel, 0)
    renewable_pct = (renewable / sum(generation_data.values())) * 100 if sum(generation_data.values()) > 0 else 0
    
    # System balance
    balance = total_generation - demand
    
    # Carbon intensity (rough estimate)
    carbon_intensity = 180  # Placeholder
    
    return {
        'total_generation': total_generation,
        'low_carbon_pct': low_carbon_pct,
        'renewable_pct': renewable_pct,
        'balance': balance,
        'carbon_intensity': carbon_intensity
    }


def update_google_sheet(data):
    """Update Google Sheet with new data"""
    
    # Prepare the data to update
    # Format: [[value1], [value2], ...] for each cell
    updates = [
        # Row 1: Grid Frequency, Gas, IFA, Time series
        [
            f"Grid Frequency: {data['frequency']:.2f} Hz",
            f"💨 Gas: {data['gas']:.1f} GW",
            f"🇫🇷 IFA (France): {data['interconnectors']['IFA']:.1f} GW",
            f"Latest: Demand {data['demand']:.1f}GW | Generation {data['total_generation']:.1f}GW",
            f"🌱 Low Carbon Generation: {data['low_carbon_pct']:.0f}%"
        ],
        # Row 2: System demand, Nuclear, IFA2, etc.
        [
            f"Total System Demand: {data['demand']:.1f} GW",
            f"☢️ Nuclear: {data['nuclear']:.1f} GW",
            f"🇫🇷 IFA2 (France): {data['interconnectors']['IFA2']:.1f} GW",
            "",
            f"♻️ Renewable Generation: {data['renewable_pct']:.0f}%"
        ],
        # Row 3: System supply, Wind, BritNed, etc.
        [
            f"Total System Supply: {data['total_generation']:.1f} GW",
            f"🌀 Wind: {data['wind']:.1f} GW",
            f"🇳🇱 BritNed (Netherlands): {data['interconnectors']['BritNed']:.1f} GW",
            "",
            f"🔌 Total Import Capacity: {data['total_import']:.1f} GW"
        ],
        # Row 4: System balance, Solar, Nemo, etc.
        [
            f"System Balance: {data['balance']:+.1f} GW",
            f"☀️ Solar: {data['solar']:.1f} GW",
            f"🇧🇪 Nemo (Belgium): {data['interconnectors']['Nemo']:.1f} GW",
            "",
            f"🌡️ Carbon Intensity: {data['carbon_intensity']:.0f} gCO₂/kWh"
        ],
        # Row 5: Grid status, Biomass, NSL, etc.
        [
            f"Grid Status: {data['grid_status']}",
            f"🌿 Biomass: {data['biomass']:.1f} GW",
            f"🇳🇴 NSL (Norway): {data['interconnectors']['NSL']:.1f} GW",
            "",
            f"📈 Peak Demand Today: {data['peak_demand']:.1f} GW"
        ],
        # Row 6: Hydro, Moyle
        [
            "",
            f"💧 Hydro: {data['hydro']:.1f} GW",
            f"🇮🇪 Moyle (N. Ireland): {data['interconnectors']['Moyle']:.1f} GW",
            "",
            ""
        ],
        # Row 7: Coal
        [
            "",
            f"⚫ Coal: {data['coal']:.1f} GW",
            "",
            "",
            ""
        ]
    ]
    
    # Update the sheet
    try:
        range_name = f"{SHEET_NAME}!A1:E7"
        
        body = {
            'values': updates
        }
        
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        print(f"✅ Updated {result.get('updatedCells')} cells in Google Sheet")
        return True
        
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        return False


def main():
    """Main function to fetch data and update sheet"""
    
    print("📊 Fetching latest data from BigQuery...")
    
    # Get all the data
    frequency = get_latest_frequency()
    generation_data = get_latest_generation_data()
    demand = get_latest_demand()
    interconnectors = get_interconnector_flows()
    
    # Extract generation by fuel type (convert MW to GW)
    gas = generation_data.get('GAS', 0) / 1000
    nuclear = generation_data.get('NUCLEAR', 0) / 1000
    wind = generation_data.get('WIND', 0) / 1000
    solar = generation_data.get('SOLAR', 0) / 1000
    biomass = generation_data.get('BIOMASS', 0) / 1000
    hydro = generation_data.get('HYDRO', 0) / 1000
    coal = generation_data.get('COAL', 0) / 1000
    
    # Calculate metrics
    metrics = calculate_metrics(generation_data, demand)
    
    # Determine grid status
    if abs(metrics['balance']) < 0.5:
        grid_status = "NORMAL"
    elif metrics['balance'] > 0.5:
        grid_status = "SURPLUS"
    else:
        grid_status = "TIGHT"
    
    # Prepare data dictionary
    data = {
        'frequency': frequency,
        'gas': gas,
        'nuclear': nuclear,
        'wind': wind,
        'solar': solar,
        'biomass': biomass,
        'hydro': hydro,
        'coal': coal,
        'demand': demand,
        'total_generation': metrics['total_generation'],
        'balance': metrics['balance'],
        'low_carbon_pct': metrics['low_carbon_pct'],
        'renewable_pct': metrics['renewable_pct'],
        'carbon_intensity': metrics['carbon_intensity'],
        'interconnectors': interconnectors,
        'total_import': sum(interconnectors.values()),
        'grid_status': grid_status,
        'peak_demand': demand * 1.1  # Rough estimate
    }
    
    print("\n📈 Latest Data:")
    print(f"  Frequency: {frequency:.2f} Hz")
    print(f"  Demand: {demand:.1f} GW")
    print(f"  Generation: {metrics['total_generation']:.1f} GW")
    print(f"  Balance: {metrics['balance']:+.1f} GW")
    print(f"  Low Carbon: {metrics['low_carbon_pct']:.0f}%")
    print(f"  Renewable: {metrics['renewable_pct']:.0f}%")
    print()
    
    # Update Google Sheet
    print("📝 Updating Google Sheet...")
    success = update_google_sheet(data)
    
    if success:
        print("✅ Dashboard updated successfully!")
        print(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("❌ Failed to update dashboard")
    
    return success


if __name__ == "__main__":
    main()
