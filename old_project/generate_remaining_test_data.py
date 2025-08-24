#!/usr/bin/env python3
"""
Generate Test Data for Remaining UK Energy Dashboard Tables
----------------------------------------------------------
This script creates test data for the remaining BigQuery tables to allow
development and testing of the dashboard while the real data ingestion is
being set up.
"""

import os
import sys
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from google.cloud import bigquery
from typing import List, Dict

# Configuration
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)
NUM_DAYS = (END_DATE - START_DATE).days + 1

print(f"Generating test data for remaining tables ({NUM_DAYS} days)")

# Initialize BigQuery client
client = None
try:
    client = bigquery.Client(project=PROJECT_ID)
    print(f"✅ Connected to BigQuery project: {PROJECT_ID}")
except Exception as e:
    print(f"❌ Failed to connect to BigQuery: {e}")
    sys.exit(1)

def generate_system_warnings_data():
    """Generate test data for elexon_system_warnings table."""
    print(f"Generating data for elexon_system_warnings...")
    
    rows = []
    current_date = START_DATE
    
    # Define warning types and severities
    warning_types = ["Capacity Warning", "Demand Control", "System Stress", "Interconnector Issue", "Generation Shortfall"]
    severities = ["Low", "Medium", "High", "Critical"]
    areas = ["National", "South West", "London", "Scotland", "Wales", "North East"]
    statuses = ["Active", "Resolved", "Monitoring"]
    
    # Generate approximately 1 warning every 15 days (realistic frequency)
    warning_count = NUM_DAYS // 15
    
    # Generate random warning dates
    warning_dates = sorted(random.sample(range(NUM_DAYS), warning_count))
    
    for i, day_offset in enumerate(warning_dates):
        warning_date = START_DATE + timedelta(days=day_offset)
        warning_id = f"W{warning_date.strftime('%Y%m%d')}-{i+1:03d}"
        warning_type = random.choice(warning_types)
        severity = random.choice(severities)
        affected_area = random.choice(areas)
        status = random.choice(statuses)
        
        # Random start time during the day
        start_hour = random.randint(7, 18)  # Between 7am and 6pm
        start_time = datetime.combine(warning_date.date(), time(start_hour, random.randint(0, 59)))
        
        # Random duration between 1-8 hours
        duration_hours = random.randint(1, 8)
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Resolution time if status is Resolved
        resolution_time = end_time if status == "Resolved" else None
        
        # Impact in MW
        impact_mw = random.uniform(100, 5000) if random.random() > 0.3 else None
        
        # Message
        messages = {
            "Capacity Warning": f"Capacity margin below required level in {affected_area}",
            "Demand Control": f"Demand reduction request issued for {affected_area}",
            "System Stress": f"System stress event declared affecting {affected_area}",
            "Interconnector Issue": f"Reduced capacity on interconnector to {affected_area}",
            "Generation Shortfall": f"Generation shortfall detected in {affected_area}"
        }
        
        message = messages.get(warning_type, f"{warning_type} affecting {affected_area}")
        
        row = {
            "warning_id": warning_id,
            "warning_type": warning_type,
            "warning_date": warning_date.date(),
            "start_time": start_time,
            "end_time": end_time,
            "severity": severity,
            "message": message,
            "affected_area": affected_area,
            "status": status,
            "resolution_time": resolution_time,
            "impact_mw": impact_mw
        }
        rows.append(row)
    
    # Create a DataFrame
    df = pd.DataFrame(rows)
    return df

def generate_carbon_intensity_data():
    """Generate test data for neso_carbon_intensity table."""
    print(f"Generating data for neso_carbon_intensity...")
    
    rows = []
    current_date = START_DATE
    
    # Define regions
    regions = ["National", "London", "South East", "South West", "Midlands", "Wales", "North West", "North East", "Scotland"]
    
    # For each day in the date range
    while current_date <= END_DATE:
        measurement_date = current_date.date()
        
        # Base carbon intensity for the day (seasonal variation)
        day_of_year = current_date.timetuple().tm_yday
        seasonal_factor = 0.5 * np.sin(2 * np.pi * day_of_year / 365) + 0.5  # 0 to 1 factor
        base_intensity = 100 + seasonal_factor * 150  # Between 100-250 gCO2/kWh
        
        # For each hour of the day
        for hour in range(24):
            # Time of day effect - higher carbon intensity during peak hours
            time_factor = 1.0
            if 7 <= hour <= 9 or 17 <= hour <= 20:  # Peak hours
                time_factor = 1.2
            elif 0 <= hour <= 5:  # Night hours (more baseload, less carbon)
                time_factor = 0.8
            
            measurement_time = time(hour, 0, 0)
            
            # For each region
            for region in regions:
                # Regional variation
                regional_factor = 1.0
                if region == "Scotland":
                    regional_factor = 0.7  # Lower carbon due to more renewables
                elif region in ["London", "South East"]:
                    regional_factor = 1.15  # Higher carbon in densely populated areas
                
                # Calculate carbon intensity with some randomness
                carbon_intensity = base_intensity * time_factor * regional_factor * random.uniform(0.9, 1.1)
                
                # Forecast is slightly different from actual
                forecast = carbon_intensity * random.uniform(0.85, 1.15)
                
                # Generation mix JSON string (simplified)
                generation_mix = {
                    "wind": random.uniform(15, 45),
                    "solar": random.uniform(0, 25) if 6 <= hour <= 18 else 0,
                    "nuclear": random.uniform(15, 25),
                    "gas": random.uniform(20, 40),
                    "coal": random.uniform(0, 10),
                    "biomass": random.uniform(5, 15),
                    "hydro": random.uniform(1, 5),
                    "imports": random.uniform(5, 15)
                }
                
                # Ensure percentages sum to 100
                total = sum(generation_mix.values())
                generation_mix = {k: v * 100 / total for k, v in generation_mix.items()}
                
                row = {
                    "measurement_date": measurement_date,
                    "measurement_time": measurement_time,
                    "carbon_intensity_gco2_kwh": carbon_intensity,
                    "forecast_carbon_intensity_gco2_kwh": forecast,
                    "generation_mix": str(generation_mix),
                    "region": region,
                    "data_source": "Test Data"
                }
                rows.append(row)
        
        current_date += timedelta(days=1)
        
        # Print progress every 30 days
        if (current_date - START_DATE).days % 30 == 0:
            print(f"  - Generated data up to {current_date.date()} ({(current_date - START_DATE).days} days)")
    
    # Create a DataFrame
    df = pd.DataFrame(rows)
    return df

def generate_interconnector_flows_data():
    """Generate test data for neso_interconnector_flows table."""
    print(f"Generating data for neso_interconnector_flows...")
    
    rows = []
    current_date = START_DATE
    
    # Define interconnectors
    interconnectors = [
        {"id": "IFA", "name": "France Interconnector", "country": "France", "capacity": 2000},
        {"id": "BritNed", "name": "Netherlands Interconnector", "country": "Netherlands", "capacity": 1000},
        {"id": "Moyle", "name": "Northern Ireland Interconnector", "country": "Northern Ireland", "capacity": 500},
        {"id": "EWIC", "name": "Ireland Interconnector", "country": "Ireland", "capacity": 500},
        {"id": "NSL", "name": "Norway Interconnector", "country": "Norway", "capacity": 1400},
        {"id": "ElecLink", "name": "France ElecLink", "country": "France", "capacity": 1000}
    ]
    
    # For each day in the date range
    while current_date <= END_DATE:
        settlement_date = current_date.date()
        
        # For each settlement period (48 half-hours per day)
        for sp in range(1, 49):
            # Hour of day (0-23)
            hour = (sp - 1) // 2
            
            # For each interconnector
            for ic in interconnectors:
                # Direction biases by interconnector and time of day
                direction_bias = 0
                
                # France and Netherlands tend to export to UK during day
                if ic["country"] in ["France", "Netherlands"] and 8 <= hour <= 18:
                    direction_bias = -0.3  # Import bias
                
                # Norway tends to export to UK at night
                if ic["country"] == "Norway" and (hour < 6 or hour > 20):
                    direction_bias = -0.3  # Import bias
                
                # UK tends to export to Ireland and NI during day
                if ic["country"] in ["Ireland", "Northern Ireland"] and 8 <= hour <= 18:
                    direction_bias = 0.3  # Export bias
                
                # Flow direction probability (-1 to +1 value, negative is import to UK)
                flow_direction_value = random.uniform(-1, 1) + direction_bias
                
                # Convert to string direction
                direction = "Import" if flow_direction_value < 0 else "Export"
                
                # Flow amount as percentage of capacity
                utilization_pct = abs(flow_direction_value) * random.uniform(0.5, 0.9)
                
                # Flow in MW (signed value)
                capacity_mw = ic["capacity"]
                flow_mw = capacity_mw * utilization_pct
                if direction == "Import":
                    flow_mw = -flow_mw  # Negative for imports
                
                # Price differential (UK price minus connected country price)
                price_differential = flow_mw / 100  # Simplified model
                
                # Forecast timestamp
                forecast_timestamp = datetime.combine(
                    settlement_date - timedelta(days=1),
                    time(hour=12, minute=0)
                )
                
                row = {
                    "settlement_date": settlement_date,
                    "settlement_period": sp,
                    "interconnector_id": ic["id"],
                    "interconnector_name": ic["name"],
                    "connected_country": ic["country"],
                    "flow_mw": flow_mw,
                    "direction": direction,
                    "capacity_mw": capacity_mw,
                    "utilization_pct": utilization_pct * 100,  # Convert to percentage
                    "price_differential_gbp_mwh": price_differential,
                    "forecast_timestamp": forecast_timestamp
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
        return True
    
    except Exception as e:
        print(f"❌ Failed to load data to {table_name}: {e}")
        return False

def main():
    """Main function to generate and load test data."""
    print("Starting test data generation for remaining tables...")
    
    # Generate and load system warnings data
    warnings_df = generate_system_warnings_data()
    load_dataframe_to_bigquery(warnings_df, "elexon_system_warnings")
    
    # Generate and load carbon intensity data
    carbon_df = generate_carbon_intensity_data()
    load_dataframe_to_bigquery(carbon_df, "neso_carbon_intensity")
    
    # Generate and load interconnector flows data
    flows_df = generate_interconnector_flows_data()
    load_dataframe_to_bigquery(flows_df, "neso_interconnector_flows")
    
    print("\nTest data generation for remaining tables completed.")

if __name__ == "__main__":
    main()
