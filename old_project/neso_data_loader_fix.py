#!/usr/bin/env python3
"""
NESO Data Loader Fix

This script fixes issues with loading specific NESO data files into BigQuery.
It targets the two files that failed in the initial loading:
1. 24-months-ahead-constraint-cost-forecast JSON file - special character in column name
2. Capacity market register component CSV file - data type conversion issues
"""

import os
import json
import pandas as pd
import logging
from google.cloud import bigquery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('neso_data_loader_fix')

# Default settings
DEFAULT_PROJECT = 'jibber-jabber-knowledge'
DEFAULT_DATASET = 'uk_energy_prod'
BASE_DIR = 'neso_network_information'

def fix_constraint_cost_forecast(project_id, dataset_id):
    """Fix the constraint cost forecast JSON file loading issue."""
    json_file = os.path.join(BASE_DIR, 'forecasts', '24-months-ahead-constraint-cost-forecast', '24-months-ahead-constraint-cost-forecast_latest.json')
    
    if not os.path.exists(json_file):
        logger.error(f"Constraint cost forecast file not found: {json_file}")
        return False
    
    table_id = f"{project_id}.{dataset_id}.neso_constraint_cost_24m"
    
    try:
        logger.info(f"Processing {json_file} -> {table_id}")
        
        # Read the JSON file
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Create DataFrame and rename the problematic column
        df = pd.json_normalize(data)
        
        # Special handling for the pound symbol column
        columns = df.columns.tolist()
        for i, col in enumerate(columns):
            if 'constraint cost' in col.lower() or 'constraint_cost' in col.lower() or '£' in col or '\u00a3' in col:
                columns[i] = 'constraint_cost_gbp_m'
        
        df.columns = columns
        
        # Convert all column names to valid BigQuery format
        df.columns = [col.lower().replace(' ', '_').replace('-', '_')
                     .replace('/', '_')
                     .replace('(', '')
                     .replace(')', '')
                     .replace('[', '')
                     .replace(']', '')
                     .replace('.', '_')
                     .replace('£', '')
                     .replace('$', '')
                     .replace('%', 'pct')
                     .replace('&', 'and')
                     .replace('+', 'plus')
                     .replace('#', 'num')
                     .replace('@', 'at')
                     .replace('*', 'star')
                     .replace('?', '')
                     .replace('!', '')
                     .replace(':', '')
                     .replace(';', '')
                     .replace(',', '')
                     .replace('\'', '')
                     .replace('"', '')
                     .replace('\\', '')
                     .replace('=', 'equals')
                     .replace('<', 'lt')
                     .replace('>', 'gt')
                     for col in df.columns]
        
        # Create BigQuery client with europe-west2 location
        client = bigquery.Client(project=project_id, location="europe-west2")
        
        # Check if table exists and delete if it does
        try:
            client.delete_table(table_id)
            logger.info(f"Deleted existing table {table_id}")
        except Exception as e:
            logger.info(f"Table does not exist or could not be deleted: {str(e)}")
        
        # Create schema based on DataFrame
        schema = []
        for col_name, dtype in df.dtypes.items():
            if pd.api.types.is_integer_dtype(dtype):
                field_type = 'INT64'
            elif pd.api.types.is_float_dtype(dtype):
                field_type = 'FLOAT64'
            elif pd.api.types.is_bool_dtype(dtype):
                field_type = 'BOOL'
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                field_type = 'TIMESTAMP'
            else:
                field_type = 'STRING'
            
            schema.append(bigquery.SchemaField(col_name, field_type))
        
        # Create table
        table = bigquery.Table(table_id, schema=schema)
        table.description = '24-months ahead constraint cost forecast'
        client.create_table(table)
        logger.info(f"Created table {table_id}")
        
        # Load data to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for the job to complete
        
        logger.info(f"Successfully loaded {len(df)} rows to {table_id}")
        return True
    except Exception as e:
        logger.error(f"Error fixing constraint cost forecast: {str(e)}")
        return False

def fix_capacity_market_component(project_id, dataset_id):
    """Fix the capacity market component CSV file loading issue."""
    csv_file = os.path.join(BASE_DIR, 'static', 'capacity-market-register', 'component_20250820.csv')
    
    if not os.path.exists(csv_file):
        logger.error(f"Capacity market component file not found: {csv_file}")
        return False
    
    table_id = f"{project_id}.{dataset_id}.neso_capacity_market_component"
    
    try:
        logger.info(f"Processing {csv_file} -> {table_id}")
        
        # Read the CSV file with error handling for inconsistent columns
        try:
            # First attempt - standard CSV reading
            df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)
        except Exception as e:
            logger.warning(f"Standard CSV reading failed, trying with header inference: {str(e)}")
            try:
                # Second attempt - use header=None and infer column names
                df = pd.read_csv(csv_file, encoding='utf-8', header=None, low_memory=False)
                # Use the first row as headers
                df.columns = [f"col_{i}" for i in range(df.shape[1])]
            except Exception as e2:
                logger.warning(f"Header inference failed, trying with different delimiter: {str(e2)}")
                try:
                    # Third attempt - try with different delimiter
                    df = pd.read_csv(csv_file, encoding='utf-8', sep=';', low_memory=False)
                except Exception as e3:
                    # Last resort - read with most permissive settings
                    logger.warning(f"All standard methods failed, using most permissive settings: {str(e3)}")
                    df = pd.read_csv(csv_file, encoding='utf-8', error_bad_lines=False, warn_bad_lines=True, 
                                    low_memory=False, delimiter=None, quoting=3)
        
        # Clean up column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_')
                     .replace('/', '_')
                     .replace('(', '')
                     .replace(')', '')
                     .replace('[', '')
                     .replace(']', '')
                     .replace('.', '_')
                     .replace('£', '')
                     .replace('$', '')
                     .replace('%', 'pct')
                     .replace('&', 'and')
                     .replace('+', 'plus')
                     .replace('#', 'num')
                     .replace('@', 'at')
                     .replace('*', 'star')
                     .replace('?', '')
                     .replace('!', '')
                     .replace(':', '')
                     .replace(';', '')
                     .replace(',', '')
                     .replace('\'', '')
                     .replace('"', '')
                     .replace('\\', '')
                     .replace('=', 'equals')
                     .replace('<', 'lt')
                     .replace('>', 'gt')
                     for col in df.columns]
        
        # Convert all columns to strings to avoid data type errors
        for col in df.columns:
            df[col] = df[col].astype(str)
        
        # Create BigQuery client with europe-west2 location
        client = bigquery.Client(project=project_id, location="europe-west2")
        
        # Check if table exists and delete if it does
        try:
            client.delete_table(table_id)
            logger.info(f"Deleted existing table {table_id}")
        except Exception as e:
            logger.info(f"Table does not exist or could not be deleted: {str(e)}")
        
        # Create schema with all columns as STRING
        schema = [bigquery.SchemaField(col, 'STRING') for col in df.columns]
        
        # Create table
        table = bigquery.Table(table_id, schema=schema)
        table.description = 'Capacity market register components'
        client.create_table(table)
        logger.info(f"Created table {table_id}")
        
        # Load data to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for the job to complete
        
        logger.info(f"Successfully loaded {len(df)} rows to {table_id}")
        return True
    except Exception as e:
        logger.error(f"Error fixing capacity market component: {str(e)}")
        return False

def main():
    """Main entry point for the script."""
    project_id = DEFAULT_PROJECT
    dataset_id = DEFAULT_DATASET
    
    logger.info("Starting NESO data loader fix")
    
    # Fix constraint cost forecast
    if fix_constraint_cost_forecast(project_id, dataset_id):
        logger.info("Successfully fixed constraint cost forecast loading issue")
    else:
        logger.error("Failed to fix constraint cost forecast loading issue")
    
    # Fix capacity market component
    if fix_capacity_market_component(project_id, dataset_id):
        logger.info("Successfully fixed capacity market component loading issue")
    else:
        logger.error("Failed to fix capacity market component loading issue")
    
    logger.info("NESO data loader fix complete")

if __name__ == "__main__":
    main()
