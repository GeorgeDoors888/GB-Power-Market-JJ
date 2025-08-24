#!/usr/bin/env python3
"""
BigQuery Data Loader Utility

This script helps load data from Google Cloud Storage to BigQuery tables for 
the energy data system. It supports multiple datasets and provides validation.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from google.cloud import storage, bigquery
from google.api_core.exceptions import NotFound

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bq_data_loading.log')
    ]
)
logger = logging.getLogger('bq_data_loader')

# Default settings
DEFAULT_BUCKET = 'elexon-historical-data-storage'
DEFAULT_PROJECT = 'jibber-jabber-knowledge'
DEFAULT_DATASET = 'uk_energy_prod'
DATA_TYPES = ['demand', 'frequency', 'generation', 'balancing', 'warnings', 'interconnector', 'carbon']

# Mapping from data types to GCS paths and BigQuery tables
DATA_MAPPING = {
    'demand': {
        'gcs_prefix': 'demand/',
        'bq_table': 'elexon_demand_outturn',
        'date_column': 'settlement_date',
        'transformer': 'transform_demand_data'
    },
    'frequency': {
        'gcs_prefix': 'frequency/',
        'bq_table': 'elexon_frequency',
        'date_column': 'settlement_date',
        'transformer': 'transform_frequency_data'
    },
    'generation': {
        'gcs_prefix': 'generation/',
        'bq_table': 'elexon_generation_outturn',
        'date_column': 'settlement_date',
        'transformer': 'transform_generation_data'
    },
    'balancing': {
        'gcs_prefix': 'balancing/',
        'bq_table': 'neso_balancing_services',
        'date_column': 'settlement_date',
        'transformer': 'transform_balancing_data'
    },
    'warnings': {
        'gcs_prefix': 'warnings/',
        'bq_table': 'elexon_system_warnings',
        'date_column': 'published_time',
        'transformer': 'transform_warnings_data'
    },
    'interconnector': {
        'gcs_prefix': 'interconnector/',
        'bq_table': 'neso_interconnector_flows',
        'date_column': 'settlement_date',
        'transformer': 'transform_interconnector_data'
    },
    'carbon': {
        'gcs_prefix': 'carbon/',
        'bq_table': 'neso_carbon_intensity',
        'date_column': 'settlement_date',
        'transformer': 'transform_carbon_data'
    }
}

def format_datetime(dt_str):
    """Format datetime string to match BigQuery DATETIME format."""
    if not dt_str:
        return None
    
    # Replace 'T' with space and remove 'Z' or any timezone info
    return dt_str.replace('T', ' ').split('+')[0].split('Z')[0]

def format_date(date_str):
    """Format date string to ensure it's in YYYY-MM-DD format."""
    if not date_str:
        return None
    
    # Handle possible date formats
    if 'T' in date_str:
        return date_str.split('T')[0]
    if ' ' in date_str:
        return date_str.split(' ')[0]
    
    return date_str

def list_gcs_files(bucket_name, prefix="", max_results=None):
    """List files in a GCS bucket with a specific prefix."""
    client = storage.Client()
    try:
        bucket = client.get_bucket(bucket_name)
        if max_results:
            blobs = list(bucket.list_blobs(prefix=prefix, max_results=max_results))
        else:
            blobs = list(bucket.list_blobs(prefix=prefix))
        return blobs
    except Exception as e:
        logger.error(f"Error listing files in GCS bucket {bucket_name}: {e}")
        return []

def get_file_content(blob):
    """Download and parse JSON content from a GCS blob."""
    try:
        content = blob.download_as_text()
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Error parsing JSON from {blob.name}")
        return None
    except Exception as e:
        logger.error(f"Error downloading {blob.name}: {e}")
        return None

def transform_demand_data(data):
    """Transform demand data to match BigQuery schema."""
    transformed_rows = []
    
    if 'data' not in data:
        logger.warning("No 'data' field in JSON")
        return []
        
    for item in data['data']:
        # Convert fields to match schema
        row = {
            'publishTime': format_datetime(item.get('publishTime')),
            'startTime': format_datetime(item.get('startTime')),
            'settlementDate': format_date(item.get('settlementDate')),
            'settlementPeriod': item.get('settlementPeriod'),
            'initialDemandOutturn': item.get('demand'),
            'initialTransmissionSystemDemandOutturn': item.get('demand')  # As a fallback, use the same value
        }
        transformed_rows.append(row)
    
    return transformed_rows

def transform_frequency_data(data):
    """Transform frequency data to match BigQuery schema."""
    transformed_rows = []
    
    if 'data' not in data:
        logger.warning("No 'data' field in JSON")
        return []
        
    for item in data['data']:
        # Convert fields to match schema
        row = {
            'timestamp': format_datetime(item.get('startTime')),
            'settlement_date': format_date(item.get('settlementDate')),
            'settlement_period': item.get('settlementPeriod'),
            'frequency': item.get('frequency', 0.0)
        }
        transformed_rows.append(row)
    
    return transformed_rows

def transform_generation_data(data):
    """Transform generation data to match BigQuery schema."""
    transformed_rows = []
    
    if 'data' not in data:
        logger.warning("No 'data' field in JSON")
        return []
    
    # Group by settlement date, period to aggregate generation by fuel type
    generation_by_period = {}
    for item in data['data']:
        key = (
            item.get('settlementDate', ''),
            item.get('settlementPeriod', 0),
            format_datetime(item.get('startTime', ''))
        )
        
        if key not in generation_by_period:
            generation_by_period[key] = {
                'recordType': 'GENERATION',
                'startTime': format_datetime(item.get('startTime')),
                'settlementDate': format_date(item.get('settlementDate')),
                'settlementPeriod': item.get('settlementPeriod'),
                'demand': 0.0  # Initialize with zero
            }
        
        # Add generation value to total demand
        if item.get('generation') is not None:
            generation_by_period[key]['demand'] += float(item.get('generation', 0))
    
    # Convert the dictionary to a list of rows
    for row in generation_by_period.values():
        transformed_rows.append(row)
    
    return transformed_rows

def transform_balancing_data(data):
    """Transform balancing services data to match BigQuery schema."""
    transformed_rows = []
    
    if 'data' not in data:
        logger.warning("No 'data' field in JSON")
        return []
        
    for item in data['data']:
        # Convert fields to match schema
        row = {
            'timestamp': format_datetime(item.get('startTime')),
            'settlement_date': format_date(item.get('settlementDate')),
            'settlement_period': item.get('settlementPeriod'),
            'service_type': item.get('serviceType'),
            'volume': item.get('volume'),
            'cost': item.get('cost')
        }
        transformed_rows.append(row)
    
    return transformed_rows

def transform_warnings_data(data):
    """Transform system warnings data to match BigQuery schema."""
    transformed_rows = []
    
    if 'data' not in data:
        logger.warning("No 'data' field in JSON")
        return []
        
    for item in data['data']:
        # Convert fields to match schema
        row = {
            'published_time': format_datetime(item.get('publishedTime')),
            'warning_type': item.get('warningType'),
            'message': item.get('message'),
            'severity': item.get('severity')
        }
        transformed_rows.append(row)
    
    return transformed_rows

def transform_interconnector_data(data):
    """Transform interconnector flows data to match BigQuery schema."""
    transformed_rows = []
    
    if 'data' not in data:
        logger.warning("No 'data' field in JSON")
        return []
        
    for item in data['data']:
        # Convert fields to match schema
        row = {
            'timestamp': format_datetime(item.get('startTime')),
            'settlement_date': format_date(item.get('settlementDate')),
            'settlement_period': item.get('settlementPeriod'),
            'interconnector_id': item.get('interconnectorId'),
            'flow_volume': item.get('flowVolume'),
            'flow_direction': item.get('flowDirection')
        }
        transformed_rows.append(row)
    
    return transformed_rows

def transform_carbon_data(data):
    """Transform carbon intensity data to match BigQuery schema."""
    transformed_rows = []
    
    if 'data' not in data:
        logger.warning("No 'data' field in JSON")
        return []
        
    for item in data['data']:
        # Convert fields to match schema
        row = {
            'timestamp': format_datetime(item.get('startTime')),
            'settlement_date': format_date(item.get('settlementDate')),
            'settlement_period': item.get('settlementPeriod'),
            'carbon_intensity': item.get('carbonIntensity'),
            'generation_mix': json.dumps(item.get('generationMix', {}))
        }
        transformed_rows.append(row)
    
    return transformed_rows

def load_data_to_bigquery(rows, table_ref, client=None):
    """Load transformed data to BigQuery."""
    if client is None:
        client = bigquery.Client()
    
    # Skip if no rows to load
    if not rows:
        logger.info(f"No rows to load to {table_ref}")
        return False
    
    # Debug output for the first row
    logger.info(f"Sample row for {table_ref}: {json.dumps(rows[0], indent=2)}")
    
    # Check if table exists, create if not
    try:
        client.get_table(table_ref)
    except NotFound:
        logger.warning(f"Table {table_ref} not found. It will be created with the schema inferred from the data.")
    
    # Load data
    try:
        errors = client.insert_rows_json(table_ref, rows)
        if errors:
            logger.error(f"Errors loading data to {table_ref}: {errors}")
            return False
        else:
            logger.info(f"Successfully loaded {len(rows)} rows to {table_ref}")
            return True
    except Exception as e:
        logger.error(f"Exception during load: {str(e)}")
        return False

def process_data_type(data_type, bucket_name, project, dataset, date_filter=None, max_files=None, start_date=None, end_date=None):
    """Process a specific data type from GCS to BigQuery."""
    logger.info(f"Processing {data_type} data...")
    
    if data_type not in DATA_MAPPING:
        logger.error(f"Unknown data type: {data_type}")
        return False
    
    mapping = DATA_MAPPING[data_type]
    table_ref = f"{project}.{dataset}.{mapping['bq_table']}"
    transformer_name = mapping['transformer']
    transformer_func = globals()[transformer_name]
    
    # List files
    gcs_prefix = mapping['gcs_prefix']
    blobs = list_gcs_files(bucket_name, gcs_prefix, max_files)
    logger.info(f"Found {len(blobs)} {data_type} files")
    
    # Filter blobs by date if needed
    filtered_blobs = []
    for blob in blobs:
        filename = blob.name.split('/')[-1]
        # Extract date from filename (different formats based on data type)
        file_date = None
        
        # Try to extract date from filename (format: data_type_YYYY-MM-DD.json)
        if '_' in filename and '.' in filename:
            date_part = filename.split('_')[-1].split('.')[0]
            if '-' in date_part and len(date_part) == 10:  # YYYY-MM-DD format
                file_date = date_part
        
        # Skip files that don't match date criteria
        if date_filter and (not file_date or file_date < date_filter):
            continue
        if start_date and (not file_date or file_date < start_date):
            continue
        if end_date and (not file_date or file_date > end_date):
            continue
        
        filtered_blobs.append(blob)
    
    logger.info(f"After date filtering: {len(filtered_blobs)} {data_type} files")
    
    total_rows = 0
    success_count = 0
    
    # Create BigQuery client once for reuse
    client = bigquery.Client()
    
    for blob in filtered_blobs:
        logger.info(f"Processing {blob.name}")
        data = get_file_content(blob)
        if not data:
            continue
            
        transformed_rows = transformer_func(data)
        
        # Apply date filter if provided
        if date_filter and transformed_rows:
            date_column = mapping['date_column']
            transformed_rows = [
                row for row in transformed_rows 
                if row.get(date_column) and row[date_column] >= date_filter
            ]
        
        if transformed_rows:
            if load_data_to_bigquery(transformed_rows, table_ref, client):
                total_rows += len(transformed_rows)
                success_count += 1
    
    logger.info(f"{data_type} data processing complete. Loaded {total_rows} rows from {success_count}/{len(blobs)} files")
    return success_count > 0

def validate_loaded_data(data_type, project, dataset, date_filter=None):
    """Validate that data was loaded correctly."""
    if data_type not in DATA_MAPPING:
        logger.error(f"Unknown data type: {data_type}")
        return False
    
    mapping = DATA_MAPPING[data_type]
    table_ref = f"{project}.{dataset}.{mapping['bq_table']}"
    date_column = mapping['date_column']
    
    client = bigquery.Client()
    
    # Build query
    query = f"SELECT COUNT(*) as count FROM `{table_ref}`"
    if date_filter:
        query += f" WHERE {date_column} >= '{date_filter}'"
    
    logger.info(f"Running validation query: {query}")
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        for row in results:
            count = row.count
            logger.info(f"Found {count} rows in {table_ref}")
            return count > 0
            
    except Exception as e:
        logger.error(f"Error validating data in {table_ref}: {e}")
        return False

def get_authentication_status():
    """Check and report on the authentication status."""
    # Check for application default credentials
    adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    adc_exists = os.path.exists(adc_path)
    
    # Try to create clients to check authentication
    try:
        storage_client = storage.Client()
        storage_auth_ok = True
    except Exception:
        storage_auth_ok = False
    
    try:
        bigquery_client = bigquery.Client()
        bigquery_auth_ok = True
    except Exception:
        bigquery_auth_ok = False
    
    return {
        "adc_exists": adc_exists,
        "adc_path": adc_path,
        "storage_auth_ok": storage_auth_ok,
        "bigquery_auth_ok": bigquery_auth_ok
    }

def main():
    """Main function to execute the data loading process."""
    parser = argparse.ArgumentParser(description='Load data from GCS to BigQuery with schema transformation')
    parser.add_argument('--bucket', type=str, default=DEFAULT_BUCKET, 
                        help=f'GCS bucket name (default: {DEFAULT_BUCKET})')
    parser.add_argument('--project', type=str, default=DEFAULT_PROJECT,
                        help=f'BigQuery project (default: {DEFAULT_PROJECT})')
    parser.add_argument('--dataset', type=str, default=DEFAULT_DATASET,
                        help=f'BigQuery dataset (default: {DEFAULT_DATASET})')
    parser.add_argument('--data-type', type=str, choices=DATA_TYPES + ['all'], 
                        default='all', help='Data type to process (default: all)')
    parser.add_argument('--date-filter', type=str, 
                        help='Only process data from this date forward (YYYY-MM-DD)')
    parser.add_argument('--start-date', type=str,
                        help='Start date for processing data (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                        help='End date for processing data (YYYY-MM-DD)')
    parser.add_argument('--max-files', type=int,
                        help='Maximum number of files to process per data type')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only validate data, don\'t load')
    parser.add_argument('--check-auth', action='store_true',
                        help='Check authentication status and exit')
    
    args = parser.parse_args()
    
    # Check authentication if requested
    if args.check_auth:
        logger.info("Checking authentication status...")
        auth_status = get_authentication_status()
        
        logger.info(f"Application Default Credentials:")
        logger.info(f"  Exists: {auth_status['adc_exists']}")
        logger.info(f"  Path: {auth_status['adc_path']}")
        logger.info(f"Storage Authentication: {'OK' if auth_status['storage_auth_ok'] else 'Failed'}")
        logger.info(f"BigQuery Authentication: {'OK' if auth_status['bigquery_auth_ok'] else 'Failed'}")
        
        if not auth_status['adc_exists'] or not auth_status['storage_auth_ok'] or not auth_status['bigquery_auth_ok']:
            logger.error("Authentication issues detected. Please run: gcloud auth application-default login")
            return 1
        
        logger.info("Authentication check passed!")
        return 0
    
    logger.info(f"Starting data loading process")
    logger.info(f"Using bucket: {args.bucket}")
    logger.info(f"Target project: {args.project}")
    logger.info(f"Target dataset: {args.dataset}")
    logger.info(f"Processing data type(s): {args.data_type}")
    if args.date_filter:
        logger.info(f"Date filter: {args.date_filter}")
    if args.max_files:
        logger.info(f"Max files per data type: {args.max_files}")
    
    success = True
    
    # Determine which data types to process
    data_types_to_process = DATA_TYPES if args.data_type == 'all' else [args.data_type]
    
    # Handle date parameters
    date_filter = args.date_filter
    start_date = args.start_date
    end_date = args.end_date
    
    if date_filter:
        logger.info(f"Date filter: {date_filter}")
    if start_date:
        logger.info(f"Start date: {start_date}")
    if end_date:
        logger.info(f"End date: {end_date}")
    
    for data_type in data_types_to_process:
        if args.validate_only:
            if not validate_loaded_data(data_type, args.project, args.dataset, args.date_filter):
                logger.warning(f"Validation failed for {data_type}")
                success = False
        else:
            if not process_data_type(data_type, args.bucket, args.project, args.dataset, 
                                      args.date_filter, args.max_files, args.start_date, args.end_date):
                logger.warning(f"Processing failed for {data_type}")
                success = False
            
            # Validate after loading
            if not validate_loaded_data(data_type, args.project, args.dataset, args.date_filter):
                logger.warning(f"Validation failed for {data_type}")
                success = False
    
    if success:
        logger.info("Data loading process completed successfully")
    else:
        logger.warning("Data loading process completed with warnings or errors")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
