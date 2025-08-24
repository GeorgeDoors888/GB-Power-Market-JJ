#!/usr/bin/env python3
"""
Generate Test Data for UK Energy Dashboard (Automated Version)
-------------------------------------------------------------
This script creates test data for the BigQuery tables with automated approvals
and better tracking of what's been done to avoid redundant operations.
"""

import os
import sys
import json
import random
import argparse
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery

# Add argument parser for better control
parser = argparse.ArgumentParser(description='Generate and load test data to BigQuery with automation.')
parser.add_argument('--force', action='store_true', help='Force regeneration of all data even if already exists')
parser.add_argument('--no-prompt', action='store_true', help='Run with no prompts or confirmations')
parser.add_argument('--tables', nargs='+', help='Specific tables to generate data for')
parser.add_argument('--days', type=int, help='Number of days to generate (from start date)')
parser.add_argument('--start-date', help='Start date in YYYY-MM-DD format')
parser.add_argument('--end-date', help='End date in YYYY-MM-DD format')
parser.add_argument('--status-file', default='data_generation_status.json', help='Path to status tracking file')
args = parser.parse_args()

# Configuration
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"  # Production dataset in europe-west2 region
START_DATE = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else datetime(2023, 1, 1)
END_DATE = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else datetime(2024, 12, 31)
NUM_SETTLEMENT_PERIODS = 48  # 48 half-hour periods per day

# Override end date if days is specified
if args.days:
    END_DATE = START_DATE + timedelta(days=args.days-1)

NUM_DAYS = (END_DATE - START_DATE).days + 1

# For tracking what's been generated
STATUS_FILE = args.status_file
status_data = {}
if os.path.exists(STATUS_FILE) and not args.force:
    try:
        with open(STATUS_FILE, 'r') as f:
            status_data = json.load(f)
        print(f"Loaded generation status from {STATUS_FILE}")
    except Exception as e:
        print(f"Error loading status file: {e}")
        status_data = {}

# Tables to generate data for
ALL_TABLES = [
    "neso_demand_forecasts",
    "neso_wind_forecasts", 
    "neso_balancing_services",
    "neso_carbon_intensity",
    "neso_interconnector_flows",
    "elexon_system_warnings"
]

TABLES_TO_GENERATE = args.tables if args.tables else ALL_TABLES

print(f"Generating test data for {NUM_DAYS} days ({START_DATE.date()} to {END_DATE.date()})")
print(f"Tables: {', '.join(TABLES_TO_GENERATE)}")

# Initialize BigQuery client
client = None
try:
    client = bigquery.Client(project=PROJECT_ID)
    print(f"✅ Connected to BigQuery project: {PROJECT_ID}")
except Exception as e:
    print(f"❌ Failed to connect to BigQuery: {e}")
    sys.exit(1)

# Helper functions
def get_table_schema(table_name):
    """Get the schema of a table to ensure generated data matches the structure."""
    try:
        table_ref = client.dataset(DATASET_ID).table(table_name)
        table = client.get_table(table_ref)
        return table.schema
    except Exception as e:
        print(f"❌ Failed to get schema for table {table_name}: {e}")
        return None

def check_table_data(table_name):
    """Check if a table already has data for the specified date range."""
    if table_name not in status_data:
        return False
    
    # Check if the table has been fully generated for our date range
    table_status = status_data[table_name]
    if 'generated' in table_status and table_status['generated']:
        if 'start_date' in table_status and 'end_date' in table_status:
            stored_start = datetime.strptime(table_status['start_date'], '%Y-%m-%d').date()
            stored_end = datetime.strptime(table_status['end_date'], '%Y-%m-%d').date()
            current_start = START_DATE.date()
            current_end = END_DATE.date()
            
            # If the stored range fully covers our requested range, data exists
            if stored_start <= current_start and stored_end >= current_end:
                return True
    
    return False

def generate_demand_forecast_data():
    """Generate test data for neso_demand_forecasts table."""
    table_name = "neso_demand_forecasts"
    
    # Check if data already exists
    if check_table_data(table_name) and not args.force:
        print(f"✅ Data for {table_name} already exists for the date range. Skipping...")
        return None
    
    print(f"Generating data for {table_name}...")
    
    rows = []
    current_date = START_DATE
    
    # For each day in the date range
    while current_date <= END_DATE:
        settlement_date = current_date.date()
        forecast_date = settlement_date - timedelta(days=1)  # Forecast from day before
        
        # For each settlement period (48 half-hours per day)
        for sp in range(1, NUM_SETTLEMENT_PERIODS + 1):
            # Create a row with realistic values
            base_demand = 30000 + random.randint(-5000, 5000)  # Around 30 GW
            row = {
                "forecast_date": forecast_date,
                "settlement_date": settlement_date,
                "settlement_period": sp,
                "national_demand_forecast": base_demand,
                "temperature_forecast": random.uniform(2, 25),  # In Celsius
                "wind_forecast": random.uniform(1000, 8000),  # In MW
                "solar_forecast": random.uniform(0, 5000),  # In MW
                "forecast_error": random.uniform(-500, 500)  # In MW
            }
            rows.append(row)
        
        current_date += timedelta(days=1)
        
        # Print progress every 30 days
        if (current_date - START_DATE).days % 30 == 0:
            print(f"  - Generated data up to {current_date.date()} ({(current_date - START_DATE).days} days)")
    
    # Create a DataFrame
    df = pd.DataFrame(rows)
    
    # Update status
    status_data[table_name] = {
        'generated': True,
        'start_date': START_DATE.date().isoformat(),
        'end_date': END_DATE.date().isoformat(),
        'row_count': len(df),
        'last_updated': datetime.now().isoformat()
    }
    
    return df

def generate_wind_forecast_data():
    """Generate test data for neso_wind_forecasts table."""
    table_name = "neso_wind_forecasts"
    
    # Check if data already exists
    if check_table_data(table_name) and not args.force:
        print(f"✅ Data for {table_name} already exists for the date range. Skipping...")
        return None
    
    print(f"Generating data for {table_name}...")
    
    rows = []
    current_date = START_DATE
    
    # Define some wind farms
    wind_farms = [
        {"id": "WFARM001", "name": "North Sea Array", "capacity": 500},
        {"id": "WFARM002", "name": "Scottish Highlands", "capacity": 350},
        {"id": "WFARM003", "name": "Welsh Valley", "capacity": 200},
        {"id": "WFARM004", "name": "Coastal Front", "capacity": 450},
        {"id": "WFARM005", "name": "Western Isles", "capacity": 300}
    ]
    
    # For each day in the date range
    while current_date <= END_DATE:
        settlement_date = current_date.date()
        
        # For each wind farm
        for farm in wind_farms:
            # For each settlement period (48 half-hours per day)
            for sp in range(1, NUM_SETTLEMENT_PERIODS + 1):
                # Create a row with realistic values
                forecast_timestamp = datetime.combine(settlement_date, datetime.min.time()) + timedelta(hours=sp/2)
                capacity_mw = farm["capacity"]
                wind_speed = random.uniform(2, 15)  # m/s
                availability_factor = random.uniform(0.7, 0.98)
                forecast_output_mw = capacity_mw * (wind_speed / 12) * availability_factor  # Simplified model
                actual_output_mw = forecast_output_mw * random.uniform(0.9, 1.1)  # Actual differs from forecast
                
                row = {
                    "forecast_timestamp": forecast_timestamp,
                    "settlement_date": settlement_date,
                    "settlement_period": sp,
                    "wind_farm_id": farm["id"],
                    "wind_farm_name": farm["name"],
                    "capacity_mw": capacity_mw,
                    "forecast_output_mw": forecast_output_mw,
                    "actual_output_mw": actual_output_mw,
                    "availability_factor": availability_factor,
                    "wind_speed_ms": wind_speed
                }
                rows.append(row)
        
        current_date += timedelta(days=1)
        
        # Print progress every 30 days
        if (current_date - START_DATE).days % 30 == 0:
            print(f"  - Generated data up to {current_date.date()} ({(current_date - START_DATE).days} days)")
    
    # Create a DataFrame
    df = pd.DataFrame(rows)
    
    # Update status
    status_data[table_name] = {
        'generated': True,
        'start_date': START_DATE.date().isoformat(),
        'end_date': END_DATE.date().isoformat(),
        'row_count': len(df),
        'last_updated': datetime.now().isoformat()
    }
    
    return df

def generate_balancing_services_data():
    """Generate test data for neso_balancing_services table."""
    table_name = "neso_balancing_services"
    
    # Check if data already exists
    if check_table_data(table_name) and not args.force:
        print(f"✅ Data for {table_name} already exists for the date range. Skipping...")
        return None
    
    print(f"Generating data for {table_name}...")
    
    rows = []
    current_date = START_DATE
    
    # For each day in the date range
    while current_date <= END_DATE:
        charge_date = current_date.date()
        # Add settlement_date field to match dashboard query expectations
        
        # For each settlement period (48 half-hours per day)
        for sp in range(1, NUM_SETTLEMENT_PERIODS + 1):
            # Create a row with realistic values
            bsuos_rate = random.uniform(2, 5)         # £/MWh
            volume = random.uniform(5000, 15000)      # MWh
            cost = bsuos_rate * volume                # £
            balancing_services = cost * 0.7           # £
            transmission_losses = cost * 0.2          # £
            constraint_costs = cost * 0.1             # £
            
            row = {
                "charge_date": charge_date,
                "settlement_period": sp,
                "bsuos_rate_pounds_mwh": bsuos_rate,
                "volume_mwh": volume,
                "cost_pounds": cost,
                "balancing_services_cost": balancing_services,
                "transmission_losses_cost": transmission_losses,
                "constraint_costs": constraint_costs,
                # Adding settlement_date as a copy of charge_date to match dashboard expectations
                "settlement_date": charge_date
            }
            rows.append(row)
        
        current_date += timedelta(days=1)
        
        # Print progress every 30 days
        if (current_date - START_DATE).days % 30 == 0:
            print(f"  - Generated data up to {current_date.date()} ({(current_date - START_DATE).days} days)")
    
    # Create a DataFrame
    df = pd.DataFrame(rows)
    
    # Update status
    status_data[table_name] = {
        'generated': True,
        'start_date': START_DATE.date().isoformat(),
        'end_date': END_DATE.date().isoformat(),
        'row_count': len(df),
        'last_updated': datetime.now().isoformat()
    }
    
    return df

def generate_carbon_intensity_data():
    """Generate test data for neso_carbon_intensity table."""
    table_name = "neso_carbon_intensity"
    
    # Check if data already exists
    if check_table_data(table_name) and not args.force:
        print(f"✅ Data for {table_name} already exists for the date range. Skipping...")
        return None
    
    print(f"Generating data for {table_name}...")
    
    rows = []
    current_date = START_DATE
    
    # For each day in the date range
    while current_date <= END_DATE:
        measurement_date = current_date.date()
        
        # For each settlement period (48 half-hours per day)
        for sp in range(1, NUM_SETTLEMENT_PERIODS + 1):
            # Create timestamp and half hour ID
            hour = (sp - 1) // 2
            minute = 0 if (sp % 2) == 1 else 30
            measurement_time = f"{hour:02d}:{minute:02d}:00"
            
            # Create a row with realistic values
            base_carbon = 150 + random.randint(-50, 100)  # gCO2/kWh
            forecast_carbon = base_carbon * random.uniform(0.9, 1.1)
            
            # Generate a simple mix
            gas_pct = random.uniform(30, 60)
            wind_pct = random.uniform(10, 40)
            solar_pct = random.uniform(0, 15) if 8 <= hour <= 16 else random.uniform(0, 2)
            nuclear_pct = random.uniform(15, 25)
            other_pct = 100 - (gas_pct + wind_pct + solar_pct + nuclear_pct)
            
            generation_mix = {
                "gas": gas_pct,
                "wind": wind_pct,
                "solar": solar_pct,
                "nuclear": nuclear_pct,
                "other": other_pct
            }
            
            row = {
                "measurement_date": measurement_date,
                "measurement_time": measurement_time,
                "carbon_intensity_gco2_kwh": base_carbon,
                "forecast_carbon_intensity_gco2_kwh": forecast_carbon,
                "generation_mix": json.dumps(generation_mix),
                "region": "GB",
                "data_source": "NESO"
            }
            rows.append(row)
        
        current_date += timedelta(days=1)
        
        # Print progress every 30 days
        if (current_date - START_DATE).days % 30 == 0:
            print(f"  - Generated data up to {current_date.date()} ({(current_date - START_DATE).days} days)")
    
    # Create a DataFrame
    df = pd.DataFrame(rows)
    
    # Update status
    status_data[table_name] = {
        'generated': True,
        'start_date': START_DATE.date().isoformat(),
        'end_date': END_DATE.date().isoformat(),
        'row_count': len(df),
        'last_updated': datetime.now().isoformat()
    }
    
    return df

def generate_interconnector_flows_data():
    """Generate test data for neso_interconnector_flows table."""
    table_name = "neso_interconnector_flows"
    
    # Check if data already exists
    if check_table_data(table_name) and not args.force:
        print(f"✅ Data for {table_name} already exists for the date range. Skipping...")
        return None
    
    print(f"Generating data for {table_name}...")
    
    rows = []
    current_date = START_DATE
    
    # Define interconnectors
    interconnectors = [
        {"id": "IFA", "name": "IFA", "country": "France", "capacity": 2000},
        {"id": "BRITNED", "name": "BritNed", "country": "Netherlands", "capacity": 1000},
        {"id": "NEMO", "name": "Nemo Link", "country": "Belgium", "capacity": 1000},
        {"id": "NSIA", "name": "North Sea Link", "country": "Norway", "capacity": 1400},
        {"id": "EWIC", "name": "East-West Interconnector", "country": "Ireland", "capacity": 500},
        {"id": "MOYLE", "name": "Moyle", "country": "Northern Ireland", "capacity": 500}
    ]
    
    # For each day in the date range
    while current_date <= END_DATE:
        settlement_date = current_date.date()
        
        # For each interconnector
        for ic in interconnectors:
            # For each settlement period (48 half-hours per day)
            for sp in range(1, NUM_SETTLEMENT_PERIODS + 1):
                # Create a row with realistic values
                capacity_mw = ic["capacity"]
                # Direction alternates throughout the day, with bias toward import or export
                flow_direction = 1 if random.random() > 0.4 else -1
                flow_pct = random.uniform(0.3, 0.9)
                flow_mw = capacity_mw * flow_pct * flow_direction
                utilization_pct = flow_pct * 100
                price_diff = random.uniform(5, 30) * (1 if flow_direction > 0 else -1)
                forecast_timestamp = datetime.combine(settlement_date, datetime.min.time()) + timedelta(hours=sp/2)
                
                row = {
                    "settlement_date": settlement_date,
                    "settlement_period": sp,
                    "interconnector_id": ic["id"],
                    "interconnector_name": ic["name"],
                    "connected_country": ic["country"],
                    "flow_mw": flow_mw,
                    "direction": "IMPORT" if flow_direction > 0 else "EXPORT",
                    "capacity_mw": capacity_mw,
                    "utilization_pct": utilization_pct,
                    "price_differential_gbp_mwh": price_diff,
                    "forecast_timestamp": forecast_timestamp
                }
                rows.append(row)
        
        current_date += timedelta(days=1)
        
        # Print progress every 30 days
        if (current_date - START_DATE).days % 30 == 0:
            print(f"  - Generated data up to {current_date.date()} ({(current_date - START_DATE).days} days)")
    
    # Create a DataFrame
    df = pd.DataFrame(rows)
    
    # Update status
    status_data[table_name] = {
        'generated': True,
        'start_date': START_DATE.date().isoformat(),
        'end_date': END_DATE.date().isoformat(),
        'row_count': len(df),
        'last_updated': datetime.now().isoformat()
    }
    
    return df

def generate_system_warnings_data():
    """Generate test data for elexon_system_warnings table."""
    table_name = "elexon_system_warnings"
    
    # Check if data already exists
    if check_table_data(table_name) and not args.force:
        print(f"✅ Data for {table_name} already exists for the date range. Skipping...")
        return None
    
    print(f"Generating data for {table_name}...")
    
    rows = []
    
    # This is a sparse table - only generate a warning every ~20 days on average
    warning_types = ["CAPACITY_MARGIN", "FREQUENCY_DEVIATION", "VOLTAGE_CONTROL", "GENERATION_LOSS", "DEMAND_CONTROL"]
    severity_levels = ["LOW", "MEDIUM", "HIGH"]
    areas = ["NATIONAL", "SCOTLAND", "NORTH_ENGLAND", "MIDLANDS", "SOUTH_ENGLAND", "WALES", "LONDON"]
    statuses = ["ACTIVE", "RESOLVED", "CANCELLED"]
    
    # Generate warnings (we'll do this differently - random sparse events)
    num_warnings = random.randint(40, 60)  # 40-60 warnings over the period
    
    for i in range(num_warnings):
        # Random date within our range
        days_offset = random.randint(0, NUM_DAYS - 1)
        warning_date = (START_DATE + timedelta(days=days_offset)).date()
        
        # Random time
        hour = random.randint(0, 23)
        minute = random.choice([0, 15, 30, 45])
        second = random.randint(0, 59)
        start_time = datetime.combine(warning_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute, seconds=second)
        
        # Duration: 15 minutes to 8 hours
        duration_minutes = random.randint(15, 480)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Some warnings might not have an end time (still active)
        if random.random() < 0.1:  # 10% chance
            end_time = None
        
        # Status
        status = random.choice(statuses)
        if end_time is None:
            status = "ACTIVE"  # If no end time, it must be active
        
        # Resolution time
        resolution_time = None
        if status == "RESOLVED" and end_time is not None:
            resolution_time = end_time + timedelta(minutes=random.randint(0, 120))
        
        # Other fields
        warning_type = random.choice(warning_types)
        severity = random.choice(severity_levels)
        affected_area = random.choice(areas)
        impact_mw = random.randint(100, 2000) if random.random() < 0.7 else None
        
        # Create unique ID
        warning_id = f"W{warning_date.strftime('%Y%m%d')}-{i+1:03d}"
        
        # Row
        row = {
            "warning_id": warning_id,
            "warning_type": warning_type,
            "warning_date": warning_date,
            "start_time": start_time,
            "end_time": end_time,
            "severity": severity,
            "message": f"{severity} {warning_type} warning in {affected_area}",
            "affected_area": affected_area,
            "status": status,
            "resolution_time": resolution_time,
            "impact_mw": impact_mw
        }
        rows.append(row)
    
    # Create a DataFrame
    df = pd.DataFrame(rows)
    
    # Update status
    status_data[table_name] = {
        'generated': True,
        'start_date': START_DATE.date().isoformat(),
        'end_date': END_DATE.date().isoformat(),
        'row_count': len(df),
        'last_updated': datetime.now().isoformat()
    }
    
    return df

def load_dataframe_to_bigquery(df, table_name):
    """Load a DataFrame to a BigQuery table."""
    if df is None:
        return True  # Skip if no data to load (already exists)
    
    try:
        # Get full table reference
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        
        # Check if the table exists and get row count
        try:
            query = f"SELECT COUNT(*) as count FROM `{table_ref}`"
            query_job = client.query(query)
            results = query_job.result()
            for row in results:
                existing_rows = row.count
                print(f"Table {table_name} currently has {existing_rows} rows.")
        except Exception as e:
            print(f"Error checking row count: {e}")
            existing_rows = 0
        
        # Ask for confirmation if there's existing data and not running in no-prompt mode
        if existing_rows > 0 and not args.no_prompt and not args.force:
            confirm = input(f"Table {table_name} already has {existing_rows} rows. Replace data? (y/n): ")
            if confirm.lower() != 'y':
                print(f"Skipping table {table_name}...")
                return False
        
        # Load options
        job_config = bigquery.LoadJobConfig(
            # If the table already has data, replace it
            write_disposition="WRITE_TRUNCATE" if existing_rows > 0 else "WRITE_EMPTY",
            # Auto-detect schema
            autodetect=True
        )
        
        # Load the data
        print(f"Loading {len(df)} rows to {table_ref}...")
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for the job to complete
        
        # Confirm the results
        table = client.get_table(table_ref)
        print(f"✅ Loaded {table.num_rows} rows to {table_name}")
        
        # Update status file
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        return True
    
    except Exception as e:
        print(f"❌ Failed to load data to {table_name}: {e}")
        return False

def main():
    """Main function to generate and load test data."""
    print("Starting test data generation...")
    
    # Generate and load data for each selected table
    if "neso_demand_forecasts" in TABLES_TO_GENERATE:
        demand_df = generate_demand_forecast_data()
        load_dataframe_to_bigquery(demand_df, "neso_demand_forecasts")
    
    if "neso_wind_forecasts" in TABLES_TO_GENERATE:
        wind_df = generate_wind_forecast_data()
        load_dataframe_to_bigquery(wind_df, "neso_wind_forecasts")
    
    if "neso_balancing_services" in TABLES_TO_GENERATE:
        balancing_df = generate_balancing_services_data()
        load_dataframe_to_bigquery(balancing_df, "neso_balancing_services")
    
    if "neso_carbon_intensity" in TABLES_TO_GENERATE:
        carbon_df = generate_carbon_intensity_data()
        load_dataframe_to_bigquery(carbon_df, "neso_carbon_intensity")
    
    if "neso_interconnector_flows" in TABLES_TO_GENERATE:
        interconnector_df = generate_interconnector_flows_data()
        load_dataframe_to_bigquery(interconnector_df, "neso_interconnector_flows")
    
    if "elexon_system_warnings" in TABLES_TO_GENERATE:
        warnings_df = generate_system_warnings_data()
        load_dataframe_to_bigquery(warnings_df, "elexon_system_warnings")
    
    print("\nTest data generation completed.")
    print(f"Status saved to {STATUS_FILE}")

if __name__ == "__main__":
    main()
