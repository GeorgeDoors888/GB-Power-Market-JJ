#!/usr/bin/env python3
"""
BigQuery Table Creator

This script creates tables in the new BigQuery dataset by copying schemas from the existing dataset.
"""

import subprocess
import json
import os
import sys
import tempfile
from pathlib import Path

# Configuration
PROJECT = "jibber-jabber-knowledge"
SOURCE_DATASET = "uk_energy"
TARGET_DATASET = "uk_energy_prod"
LOCATION = "europe-west2"

# Tables to copy with their configuration
TABLES = [
    {
        "name": "neso_demand_forecasts",
        "description": "Contains National Grid ESO demand forecasts",
        "time_partition": "settlement_date",
        "clustering": "forecast_date,settlement_period"
    },
    {
        "name": "neso_balancing_services",
        "description": "Contains data on balancing mechanism services",
        "time_partition": "charge_date",
        "clustering": "settlement_period"
    },
    {
        "name": "neso_wind_forecasts",
        "description": "Contains wind generation forecast data",
        "time_partition": "settlement_date",
        "clustering": "wind_farm_id,settlement_period"
    },
    {
        "name": "elexon_demand_outturn",
        "description": "Contains demand data from Elexon BMRS",
        "time_partition": "settlement_date",
        "clustering": "settlement_period"
    },
    {
        "name": "elexon_generation_outturn",
        "description": "Contains generation data from Elexon BMRS",
        "time_partition": "settlement_date",
        "clustering": "fuel_type,settlement_period"
    }
]

def run_command(cmd):
    """Run a shell command and return the output."""
    print(f"Running: {cmd}")
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if process.returncode != 0:
        print(f"Error: {process.stderr}")
        return False, process.stderr
    return True, process.stdout

def create_dataset():
    """Create the target dataset if it doesn't exist."""
    print(f"\nCreating dataset {TARGET_DATASET} in {LOCATION}...")
    try:
        # Check if dataset exists
        check_cmd = f"bq ls --format=pretty {PROJECT}:{TARGET_DATASET}"
        check_process = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        
        if check_process.returncode == 0:
            print(f"ℹ️ Dataset {TARGET_DATASET} already exists.")
            return True
        
        # Create dataset if it doesn't exist
        cmd = f"bq --location={LOCATION} mk --dataset --description 'Production UK energy dataset' {PROJECT}:{TARGET_DATASET}"
        create_process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if create_process.returncode == 0:
            print(f"✅ Dataset {TARGET_DATASET} created successfully.")
            return True
        else:
            print(f"❌ Failed to create dataset: {create_process.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating dataset: {str(e)}")
        return False

def create_table(table_config):
    """Create a table in the target dataset based on source table schema."""
    table_name = table_config["name"]
    print(f"\nProcessing table: {table_name}")
    
    # Get the schema from source table
    schema_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    schema_cmd = f"bq show --schema=true --format=json {PROJECT}:{SOURCE_DATASET}.{table_name} > {schema_file.name}"
    
    success, _ = run_command(schema_cmd)
    if not success:
        print(f"❌ Failed to get schema for {table_name}")
        return False
    
    # Create table in target dataset
    create_cmd = f"bq mk --table"
    create_cmd += f" --schema {schema_file.name}"
    
    if table_config.get("time_partition"):
        create_cmd += f" --time_partitioning_field {table_config['time_partition']}"
    
    if table_config.get("clustering"):
        create_cmd += f" --clustering_fields {table_config['clustering']}"
    
    create_cmd += f" --description \"{table_config['description']}\""
    create_cmd += f" --location={LOCATION}"
    create_cmd += f" {PROJECT}:{TARGET_DATASET}.{table_name}"
    
    success, output = run_command(create_cmd)
    
    # Clean up temp file
    try:
        os.unlink(schema_file.name)
    except:
        pass
    
    if success:
        print(f"✅ Table {table_name} created successfully in {TARGET_DATASET}")
        return True
    else:
        print(f"❌ Failed to create table {table_name}: {output}")
        return False

def main():
    """Main function to create dataset and tables."""
    print(f"BigQuery Table Creator")
    print(f"Project: {PROJECT}")
    print(f"Source Dataset: {SOURCE_DATASET}")
    print(f"Target Dataset: {TARGET_DATASET}")
    print(f"Location: {LOCATION}")
    
    # Create dataset
    if not create_dataset():
        print("❌ Exiting due to dataset creation failure.")
        return
    
    # Create tables
    success_count = 0
    for table_config in TABLES:
        if create_table(table_config):
            success_count += 1
    
    # Summary
    print(f"\n✅ Created {success_count} out of {len(TABLES)} tables in {TARGET_DATASET}.")
    print(f"Run 'bq ls --format=pretty {PROJECT}:{TARGET_DATASET}' to see the tables.")

if __name__ == "__main__":
    main()
