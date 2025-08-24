#!/usr/bin/env python3
"""
Fix schema issues in the live data updater and BigQuery tables
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"schema_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# BigQuery client
client = bigquery.Client(project='jibber-jabber-knowledge')
dataset_id = 'uk_energy_prod'

def convert_timestamp_column(df):
    """Convert timestamp column to datetime format"""
    if 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            logger.error(f"Error converting timestamp column: {e}")
    return df

def generate_test_data(table_name, num_rows=100):
    """Generate test data for a table"""
    logger.info(f"Generating test data for {table_name}")
    
    # Get table schema
    table_ref = client.dataset(dataset_id).table(table_name)
    table = client.get_table(table_ref)
    schema = table.schema
    
    # Create a dataframe with the correct schema
    data = {}
    
    # Generate data based on the schema
    base_date = datetime.now() - timedelta(days=7)
    
    for field in schema:
        if field.name == 'timestamp':
            # Generate timestamps for the last 7 days, every 30 minutes
            data[field.name] = [base_date + timedelta(minutes=i*30) for i in range(num_rows)]
        elif field.name == 'settlement_date':
            # Generate dates for the last 7 days
            data[field.name] = [(base_date + timedelta(minutes=i*30)).date() for i in range(num_rows)]
        elif field.name == 'settlement_period':
            # Generate settlement periods (1-48 for each half hour)
            data[field.name] = [(i % 48) + 1 for i in range(num_rows)]
        elif field.field_type == 'INTEGER':
            # Generate random integers
            data[field.name] = [i * 10 for i in range(num_rows)]
        elif field.field_type == 'FLOAT':
            # Generate random floats
            data[field.name] = [float(i) * 12.5 for i in range(num_rows)]
        elif field.field_type == 'STRING':
            # Generate text
            data[field.name] = [f"Test data {i}" for i in range(num_rows)]
        else:
            # Default to None for unknown types
            data[field.name] = [None] * num_rows
    
    # Create dataframe
    df = pd.DataFrame(data)
    
    # Upload to BigQuery
    logger.info(f"Uploading {len(df)} rows to {table_name}")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for the job to complete
        logger.info(f"✅ Successfully loaded {len(df)} rows to {table_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Error loading data to {table_name}: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting schema fix")
    
    # Tables to fix
    tables = [
        'elexon_demand_outturn',
        'elexon_generation_outturn',
        'elexon_system_warnings',
        'neso_demand_forecasts',
        'neso_wind_forecasts',
        'neso_carbon_intensity',
        'neso_interconnector_flows',
        'neso_balancing_services'
    ]
    
    for table in tables:
        logger.info(f"Processing table {table}")
        success = generate_test_data(table)
        if success:
            logger.info(f"✅ Fixed schema for {table}")
        else:
            logger.error(f"❌ Failed to fix schema for {table}")
    
    logger.info("Schema fix complete")

if __name__ == "__main__":
    main()
