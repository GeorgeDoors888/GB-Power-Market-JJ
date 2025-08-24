#!/usr/bin/env python3
"""
BigQuery Dataset Population Script

This script helps populate the new uk_energy_prod dataset with data.
Originally created for region migration, it has been repurposed after
discovering that the existing uk_energy dataset was already in europe-west2
but contained empty tables.

Usage:
    python export_bq_to_eu.py

Requirements:
    - Google Cloud SDK installed and configured
    - Appropriate permissions to read/write BigQuery and Cloud Storage
    - Environment variables set for PROJECT, SOURCE_DATASET, DEST_DATASET
"""

import os
import subprocess
import json
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load project configuration from PROJECT_MEMORY.md
def load_project_config():
    try:
        with open('PROJECT_MEMORY.md', 'r') as f:
            content = f.read()
            # Extract JSON part
            json_start = content.find('```json')
            json_end = content.find('```', json_start + 6)
            json_content = content[json_start + 7:json_end].strip()
            return json.loads(json_content)
    except Exception as e:
        logger.error(f"Failed to load project config: {e}")
        return None

# Get environment variables with defaults
def get_env_var(var_name, default=None):
    value = os.environ.get(var_name, default)
    if value is None:
        logger.warning(f"Environment variable {var_name} not set!")
    return value

# Run a shell command and log output
def run_command(cmd, description):
    logger.info(f"Running: {description}")
    logger.debug(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, 
                               capture_output=True)
        logger.info(f"Success: {description}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Error: {e.stderr}")
        raise

# Get list of tables to migrate
def get_tables_to_migrate(config, dataset_id):
    tables = []
    
    # Add production tables
    for table in config['detail']['bigquery_data_state']['production_tables']:
        if table['status'] == 'Populated':
            tables.append(table['name'])
    
    # Add development tables that might have data
    for table in config['detail']['bigquery_data_state']['development_tables']:
        if table['status'] != 'Empty':
            tables.append(table['name'])
    
    return tables

# Step 1: Export table from BigQuery to GCS (US bucket)
def export_table_to_gcs(project, source_dataset, table, us_bucket):
    export_cmd = (
        f"bq extract --destination_format=PARQUET "
        f"{project}:{source_dataset}.{table} "
        f"gs://{us_bucket}/bq_export/{table}/*.parquet"
    )
    run_command(export_cmd, f"Exporting {table} to US bucket")

# Step 2: Copy data from US bucket to EU bucket
def copy_data_between_buckets(us_bucket, eu_bucket, table):
    copy_cmd = (
        f"gsutil -m cp -r gs://{us_bucket}/bq_export/{table} "
        f"gs://{eu_bucket}/bq_export/{table}"
    )
    run_command(copy_cmd, f"Copying {table} data to EU bucket")

# Step 3: Load data from EU bucket to BigQuery in europe-west2
def load_data_to_eu_bigquery(project, dest_dataset, table, eu_bucket):
    load_cmd = (
        f"bq --location=europe-west2 load --source_format=PARQUET "
        f"{project}:{dest_dataset}.{table} "
        f"gs://{eu_bucket}/bq_export/{table}/*.parquet"
    )
    run_command(load_cmd, f"Loading {table} to europe-west2 BigQuery")

# Main process
def main():
    logger.info("Starting BigQuery region migration process")
    
    # Load project config
    config = load_project_config()
    if not config:
        logger.error("Could not load project config. Exiting.")
        return
    
    # Get environment variables
    project = get_env_var("PROJECT", config['detail']['project_id'])
    source_dataset = get_env_var("SOURCE_DATASET", config['detail']['bigquery_data_state']['dataset_id'])
    dest_dataset = get_env_var("DEST_DATASET", "uk_energy_prod")  # Use the new production dataset
    us_bucket = get_env_var("US_BUCKET")
    eu_bucket = get_env_var("EU_BUCKET")
    
    # Validate required variables
    if not all([project, source_dataset, dest_dataset, us_bucket, eu_bucket]):
        logger.error("Missing required environment variables. Please set PROJECT, SOURCE_DATASET, DEST_DATASET, US_BUCKET, and EU_BUCKET.")
        return
    
    # Get list of tables to migrate
    tables = get_tables_to_migrate(config, source_dataset)
    logger.info(f"Found {len(tables)} tables to migrate: {', '.join(tables)}")
    
    # Create destination dataset if it doesn't exist
    create_dataset_cmd = f"bq --location=europe-west2 mk --dataset {project}:{dest_dataset}"
    try:
        run_command(create_dataset_cmd, f"Creating destination dataset {dest_dataset} in europe-west2")
    except subprocess.CalledProcessError:
        logger.info(f"Dataset {dest_dataset} might already exist, continuing...")
    
    # Process each table
    for table in tables:
        try:
            logger.info(f"Processing table: {table}")
            
            # Step 1: Export to US bucket
            export_table_to_gcs(project, source_dataset, table, us_bucket)
            
            # Step 2: Copy to EU bucket
            copy_data_between_buckets(us_bucket, eu_bucket, table)
            
            # Step 3: Load to BigQuery in europe-west2
            load_data_to_eu_bigquery(project, dest_dataset, table, eu_bucket)
            
            logger.info(f"Successfully migrated table {table} to europe-west2")
            
        except Exception as e:
            logger.error(f"Failed to migrate table {table}: {e}")
    
    logger.info("BigQuery region migration process completed")

if __name__ == "__main__":
    main()
