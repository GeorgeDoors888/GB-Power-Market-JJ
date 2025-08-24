#!/usr/bin/env python3
"""
Generate Test Data for UK Energy Dashboard
------------------------------------------
This script creates test data for the BigQuery tables to allow development
and testing of the dashboard while the real data ingestion is being set up.
"""

import os
import sys
import random
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery

# Configuration
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"  # Production dataset in europe-west2 region
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)
NUM_SETTLEMENT_PERIODS = 48  # 48 half-hour periods per day
NUM_DAYS = (END_DATE - START_DATE).days + 1

print(f"Generating test data for {NUM_DAYS} days ({START_DATE.date()} to {END_DATE.date()})")

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

def generate_demand_forecast_data():
    """Generate test data for neso_demand_forecasts table."""
    print(f"Generating data for neso_demand_forecasts...")
    
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
    return df

def generate_wind_forecast_data():
    """Generate test data for neso_wind_forecasts table."""
    print(f"Generating data for neso_wind_forecasts...")
    
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
    return df

def generate_balancing_services_data():
    """Generate test data for neso_balancing_services table."""
    print(f"Generating data for neso_balancing_services...")
    
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
    return df

def load_dataframe_to_bigquery(df, table_name):
    """Load a DataFrame to a BigQuery table."""
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
        
        # Load options
        job_config = bigquery.LoadJobConfig(
            # If the table already has data, append to it
            write_disposition="WRITE_TRUNCATE" if existing_rows > 0 else "WRITE_EMPTY",
            # Auto-detect schema (though we should already have the schema from table creation)
            autodetect=True
        )
        
        # Load the data
        print(f"Loading {len(df)} rows to {table_ref}...")
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for the job to complete
        
        # Confirm the results
        table = client.get_table(table_ref)
        print(f"✅ Loaded {table.num_rows} rows to {table_name}")
        return True
    
    except Exception as e:
        print(f"❌ Failed to load data to {table_name}: {e}")
        return False

def main():
    """Main function to generate and load test data."""
    print("Starting test data generation...")
    
    # Generate and load demand forecast data
    demand_df = generate_demand_forecast_data()
    load_dataframe_to_bigquery(demand_df, "neso_demand_forecasts")
    
    # Generate and load wind forecast data
    wind_df = generate_wind_forecast_data()
    load_dataframe_to_bigquery(wind_df, "neso_wind_forecasts")
    
    # Generate and load balancing services data
    balancing_df = generate_balancing_services_data()
    load_dataframe_to_bigquery(balancing_df, "neso_balancing_services")
    
    # For now, we'll leave elexon_* tables empty as they're listed as "development" tables
    
    print("\nTest data generation completed.")

if __name__ == "__main__":
    main()
