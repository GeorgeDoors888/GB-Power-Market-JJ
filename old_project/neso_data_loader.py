#!/usr/bin/env python3
"""
NESO Static and Forecast Data Loader

This script processes the static and forecast data downloaded from National Grid ESO
and loads it into BigQuery for the energy dashboard.
"""

import os
import json
import glob
import argparse
import logging
import pandas as pd
from datetime import datetime
from google.cloud import bigquery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('neso_data_loader')

# Default settings
DEFAULT_PROJECT = 'jibber-jabber-knowledge'
DEFAULT_DATASET = 'uk_energy_prod'

# Mapping of data directories to BigQuery tables
STATIC_DATA_MAPPING = {
    'capacity-market-register': {
        'table_prefix': 'neso_capacity_market',
        'description': 'Contains data about capacity market registered units'
    },
    'transmission-entry-capacity-tec-register': {
        'table_prefix': 'neso_transmission_capacity',
        'description': 'Contains data about transmission entry capacity'
    },
    'embedded-register': {
        'table_prefix': 'neso_embedded_register',
        'description': 'Contains data about embedded generation units'
    },
    'interconnector-register': {
        'table_prefix': 'neso_interconnector_register',
        'description': 'Contains data about interconnectors'
    },
    'dispatch-transparency': {
        'table_prefix': 'neso_dispatch_transparency',
        'description': 'Contains data about dispatch transparency'
    },
    'national-demand-balancing-mechanism-units': {
        'table_prefix': 'neso_national_demand_bm_units',
        'description': 'Contains data about national demand balancing mechanism units'
    },
    'school-holiday-percentages': {
        'table_prefix': 'neso_school_holiday',
        'description': 'Contains school holiday data used for demand forecasting'
    },
    'skip-rates': {
        'table_prefix': 'neso_skip_rates',
        'description': 'Contains data about skip rates'
    },
    'transmission-losses': {
        'table_prefix': 'neso_transmission_losses',
        'description': 'Contains data about transmission losses'
    }
}

FORECAST_DATA_MAPPING = {
    '1-day-ahead-demand-forecast': {
        'table': 'neso_demand_forecast_1d',
        'description': '1-day ahead demand forecast'
    },
    '7-day-ahead-national-forecast': {
        'table': 'neso_national_forecast_7d',
        'description': '7-day ahead national forecast'
    },
    '14-days-ahead-wind-forecasts': {
        'table': 'neso_wind_forecast_14d',
        'description': '14-day ahead wind forecast'
    },
    'dynamic-containment-4-day-forecast': {
        'table': 'neso_dynamic_containment_4d',
        'description': '4-day dynamic containment forecast'
    },
    'long-term-2-52-weeks-ahead-national-demand-forecast': {
        'table': 'neso_national_demand_52w',
        'description': '2-52 weeks ahead national demand forecast'
    },
    '24-months-ahead-constraint-cost-forecast': {
        'table': 'neso_constraint_cost_24m',
        'description': '24-months ahead constraint cost forecast'
    }
}

def process_csv_file(csv_file, project_id, dataset_id):
    """Process a single CSV file and load it to BigQuery."""
    try:
        # Determine target table name based on file location
        file_path = os.path.normpath(csv_file)
        path_parts = file_path.split(os.sep)
        
        # Find either 'static' or 'forecasts' in the path
        if 'static' in path_parts:
            idx = path_parts.index('static')
            data_type = 'static'
            category = path_parts[idx + 1]
        elif 'forecasts' in path_parts:
            idx = path_parts.index('forecasts')
            data_type = 'forecasts'
            category = path_parts[idx + 1]
        else:
            logger.warning(f"Could not determine data type for {csv_file}")
            return False
        
        # Get file name without extension for table name
        file_name = os.path.splitext(os.path.basename(csv_file))[0]
        
        # Determine table name based on category and mapping
        if data_type == 'static':
            if category in STATIC_DATA_MAPPING:
                table_prefix = STATIC_DATA_MAPPING[category]['table_prefix']
                table_name = f"{table_prefix}_{file_name}"
            else:
                table_name = f"neso_static_{category}_{file_name}"
        else:  # forecasts
            if category in FORECAST_DATA_MAPPING:
                table_name = FORECAST_DATA_MAPPING[category]['table']
            else:
                table_name = f"neso_forecast_{category}_{file_name}"
        
        # Clean up table name to ensure valid BigQuery table name
        table_name = table_name.lower().replace('-', '_').replace('.', '_')
        
        # Construct fully qualified table ID
        table_id = f"{project_id}.{dataset_id}.{table_name}"
        
        logger.info(f"Processing {csv_file} -> {table_id}")
        
        # Try to read the CSV file with pandas
        try:
            # Try different encodings and delimiter detection
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
            except Exception:
                try:
                    df = pd.read_csv(csv_file, encoding='latin1')
                except Exception:
                    try:
                        df = pd.read_csv(csv_file, encoding='utf-8', sep=';')
                    except Exception:
                        df = pd.read_csv(csv_file, encoding='latin1', sep=';')
            
            # Convert column names to valid BigQuery column names
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
            
            # Check if the table exists
            client = bigquery.Client(project=project_id, location="europe-west2")
            try:
                client.get_table(table_id)
                exists = True
            except Exception:
                exists = False
            
            # Create schema if table doesn't exist
            if not exists:
                # Infer schema from pandas dataframe
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
                
                # Add description based on mapping
                if data_type == 'static' and category in STATIC_DATA_MAPPING:
                    table.description = STATIC_DATA_MAPPING[category]['description']
                elif data_type == 'forecasts' and category in FORECAST_DATA_MAPPING:
                    table.description = FORECAST_DATA_MAPPING[category]['description']
                
                client.create_table(table)
                logger.info(f"Created table {table_id}")
            
            # Load data to BigQuery
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
            )
            
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for the job to complete
            
            logger.info(f"Loaded {len(df)} rows to {table_id}")
            return True
        except Exception as e:
            logger.error(f"Error processing {csv_file}: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error processing {csv_file}: {str(e)}")
        return False

def process_json_file(json_file, project_id, dataset_id):
    """Process a single JSON file and load it to BigQuery."""
    try:
        # Determine target table name based on file location
        file_path = os.path.normpath(json_file)
        path_parts = file_path.split(os.sep)
        
        # We expect forecasts directory to have JSON files
        if 'forecasts' in path_parts:
            idx = path_parts.index('forecasts')
            category = path_parts[idx + 1]
        else:
            logger.warning(f"Could not determine data type for {json_file}")
            return False
        
        # Determine table name based on category and mapping
        if category in FORECAST_DATA_MAPPING:
            table_name = FORECAST_DATA_MAPPING[category]['table']
        else:
            file_name = os.path.splitext(os.path.basename(json_file))[0]
            table_name = f"neso_forecast_{category}_{file_name}"
        
        # Clean up table name to ensure valid BigQuery table name
        table_name = table_name.lower().replace('-', '_').replace('.', '_')
        
        # Construct fully qualified table ID
        table_id = f"{project_id}.{dataset_id}.{table_name}"
        
        logger.info(f"Processing {json_file} -> {table_id}")
        
        # Try to read the JSON file
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                df = pd.json_normalize(data)
            elif isinstance(data, dict) and 'results' in data:
                df = pd.json_normalize(data['results'])
            elif isinstance(data, dict) and 'data' in data:
                df = pd.json_normalize(data['data'])
            elif isinstance(data, dict) and 'items' in data:
                df = pd.json_normalize(data['items'])
            else:
                df = pd.json_normalize(data)
            
            # Convert column names to valid BigQuery column names
            df.columns = [col.lower().replace(' ', '_').replace('-', '_').replace('.', '_') for col in df.columns]
            
            # Check if the table exists
            client = bigquery.Client(project=project_id, location="europe-west2")
            try:
                client.get_table(table_id)
                exists = True
            except Exception:
                exists = False
            
            # Create schema if table doesn't exist
            if not exists:
                # Infer schema from pandas dataframe
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
                
                # Add description based on mapping
                if category in FORECAST_DATA_MAPPING:
                    table.description = FORECAST_DATA_MAPPING[category]['description']
                
                client.create_table(table)
                logger.info(f"Created table {table_id}")
            
            # Load data to BigQuery
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
            )
            
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for the job to complete
            
            logger.info(f"Loaded {len(df)} rows to {table_id}")
            return True
        except Exception as e:
            logger.error(f"Error processing {json_file}: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error processing {json_file}: {str(e)}")
        return False

def process_directory(base_dir, project_id, dataset_id):
    """Process all data files in directories under the base directory."""
    csv_success = 0
    csv_fail = 0
    json_success = 0
    json_fail = 0
    
    # Process CSV files
    csv_files = glob.glob(os.path.join(base_dir, '**', '*.csv'), recursive=True)
    
    for csv_file in csv_files:
        logger.info(f"Processing {csv_file}")
        if process_csv_file(csv_file, project_id, dataset_id):
            csv_success += 1
        else:
            csv_fail += 1
    
    # Process JSON files
    json_files = glob.glob(os.path.join(base_dir, '**', '*.json'), recursive=True)
    
    for json_file in json_files:
        logger.info(f"Processing {json_file}")
        if process_json_file(json_file, project_id, dataset_id):
            json_success += 1
        else:
            json_fail += 1
    
    logger.info(f"Processed {csv_success + csv_fail} CSV files. Success: {csv_success}, Failed: {csv_fail}")
    logger.info(f"Processed {json_success + json_fail} JSON files. Success: {json_success}, Failed: {json_fail}")
    return csv_success, csv_fail, json_success, json_fail

def main():
    """Main entry point for script."""
    parser = argparse.ArgumentParser(description='Load NESO static and forecast data to BigQuery')
    parser.add_argument('--project', type=str, default=DEFAULT_PROJECT,
                        help=f'BigQuery project ID (default: {DEFAULT_PROJECT})')
    parser.add_argument('--dataset', type=str, default=DEFAULT_DATASET,
                        help=f'BigQuery dataset ID (default: {DEFAULT_DATASET})')
    parser.add_argument('--base-dir', type=str, default='neso_network_information',
                        help='Base directory for NESO data')
    
    args = parser.parse_args()
    
    # Process static data
    logger.info(f"Processing static data in {args.base_dir}/static")
    if os.path.exists(os.path.join(args.base_dir, 'static')):
        process_directory(os.path.join(args.base_dir, 'static'), args.project, args.dataset)
    else:
        logger.error(f"Static data directory not found: {os.path.join(args.base_dir, 'static')}")
    
    # Process forecast data
    logger.info(f"Processing forecast data in {args.base_dir}/forecasts")
    if os.path.exists(os.path.join(args.base_dir, 'forecasts')):
        process_directory(os.path.join(args.base_dir, 'forecasts'), args.project, args.dataset)
    else:
        logger.error(f"Forecast data directory not found: {os.path.join(args.base_dir, 'forecasts')}")
    
    logger.info("Data loading complete.")

if __name__ == "__main__":
    main()
