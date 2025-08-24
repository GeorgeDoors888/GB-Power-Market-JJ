#!/usr/bin/env python3
"""
Elexon Data Loader

This script loads Elexon data from GCS to BigQuery. It's designed to specifically 
handle the missing Elexon datasets that were identified in the comprehensive report.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from google.cloud import storage, bigquery
from google.api_core.exceptions import NotFound

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('elexon_data_loading.log')
    ]
)
logger = logging.getLogger('elexon_data_loader')

# Default settings
DEFAULT_BUCKET = 'jibber-jabber-knowledge-bmrs-data'
DEFAULT_PROJECT = 'jibber-jabber-knowledge'
DEFAULT_DATASET = 'uk_energy_prod'

# Elexon data types - these are the ones missing from BigQuery but in GCS
ELEXON_DATA_TYPES = [
    'bid_offer_acceptances',
    'generation_outturn',
    'demand_outturn',
    'system_warnings',
    'frequency'
]

# Mapping from data types to GCS paths and BigQuery tables
DATA_MAPPING = {
    'bid_offer_acceptances': {
        'gcs_prefix': 'bmrs_data/bid_offer_acceptances/',
        'bq_table': 'elexon_bid_offer_acceptances',
        'date_column': 'settlement_date',
    },
    'generation_outturn': {
        'gcs_prefix': 'bmrs_data/generation_outturn/',
        'bq_table': 'elexon_generation_outturn',
        'date_column': 'settlement_date',
    },
    'demand_outturn': {
        'gcs_prefix': 'bmrs_data/demand_outturn/',
        'bq_table': 'elexon_demand_outturn',
        'date_column': 'settlement_date',
    },
    'system_warnings': {
        'gcs_prefix': 'bmrs_data/system_warnings/',
        'bq_table': 'elexon_system_warnings',
        'date_column': 'published_time',
    },
    'frequency': {
        'gcs_prefix': 'bmrs_data/frequency/',
        'bq_table': 'elexon_frequency',
        'date_column': 'settlement_date',
    }
}

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

def load_data_to_bigquery(data, table_ref, client=None):
    """Load JSON data to BigQuery."""
    if client is None:
        client = bigquery.Client()
    
    # Skip if no data to load
    if not data or 'data' not in data or not data['data']:
        logger.info(f"No data to load to {table_ref}")
        return False
    
    rows = data['data']
    
    # Debug output for the first row
    if rows:
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
        
        if load_data_to_bigquery(data, table_ref, client):
            if 'data' in data:
                total_rows += len(data['data'])
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
    
    # Build query for basic count validation
    count_query = f"SELECT COUNT(*) as count FROM `{table_ref}`"
    if date_filter:
        count_query += f" WHERE {date_column} >= '{date_filter}'"
    
    logger.info(f"Running validation query: {count_query}")
    
    try:
        # Check basic row count
        query_job = client.query(count_query)
        results = query_job.result()
        
        row_count = 0
        for row in results:
            row_count = row.count
            logger.info(f"Found {row_count} rows in {table_ref}")
        
        if row_count == 0:
            logger.error(f"No rows found in {table_ref}")
            return False
            
        # Quality checks - perform deeper validation
        logger.info(f"Performing quality validation for {data_type}")
        
        # Check for nulls in critical columns
        critical_columns = get_critical_columns(data_type)
        if critical_columns:
            nulls_query = f"""
            SELECT 
                {', '.join([f'COUNTIF({col} IS NULL) as {col}_nulls' for col in critical_columns])}
            FROM `{table_ref}`
            """
            
            nulls_job = client.query(nulls_query)
            nulls_result = nulls_job.result()
            
            has_null_issues = False
            for row in nulls_result:
                for col in critical_columns:
                    null_count = getattr(row, f"{col}_nulls")
                    null_percentage = (null_count / row_count) * 100 if row_count > 0 else 0
                    if null_percentage > 10:  # Alert if more than 10% nulls
                        logger.warning(f"Quality issue: {col} has {null_percentage:.2f}% null values")
                        has_null_issues = True
                    else:
                        logger.info(f"Quality check passed: {col} has {null_percentage:.2f}% null values")
            
            if has_null_issues:
                logger.warning("Data loaded but has quality issues with null values")
        
        # Check date range coverage
        if date_column:
            date_range_query = f"""
            SELECT 
                MIN({date_column}) as min_date,
                MAX({date_column}) as max_date,
                COUNT(DISTINCT {date_column}) as unique_dates
            FROM `{table_ref}`
            """
            
            range_job = client.query(date_range_query)
            range_result = range_job.result()
            
            for row in range_result:
                logger.info(f"Date range: {row.min_date} to {row.max_date} ({row.unique_dates} unique dates)")
                # Check for significant gaps if covering a longer period
                if row.unique_dates > 30:  # Only check gaps for longer periods
                    continuity_check(client, table_ref, date_column, row.min_date, row.max_date)
        
        return True
            
    except Exception as e:
        logger.error(f"Error validating data in {table_ref}: {e}")
        return False

def get_critical_columns(data_type):
    """Get the critical columns that should not be null for a data type."""
    critical_columns_map = {
        'bid_offer_acceptances': ['settlement_date', 'settlement_period', 'bmu_id'],
        'generation_outturn': ['settlement_date', 'settlement_period', 'demand'],
        'demand_outturn': ['settlement_date', 'settlement_period', 'initial_demand_outturn'],
        'system_warnings': ['published_time', 'warning_type', 'message'],
        'frequency': ['timestamp', 'frequency']
    }
    
    return critical_columns_map.get(data_type, [])

def continuity_check(client, table_ref, date_column, min_date, max_date):
    """Check for significant gaps in date coverage."""
    # Create a date spine query to identify missing dates
    gap_query = f"""
    WITH date_spine AS (
        SELECT date 
        FROM UNNEST(GENERATE_DATE_ARRAY(
            CAST('{min_date}' AS DATE), 
            CAST('{max_date}' AS DATE)
        )) AS date
    ),
    actual_dates AS (
        SELECT DISTINCT CAST({date_column} AS DATE) as date
        FROM `{table_ref}`
    )
    SELECT 
        s.date as missing_date
    FROM date_spine s
    LEFT JOIN actual_dates a ON s.date = a.date
    WHERE a.date IS NULL
    ORDER BY s.date
    LIMIT 10
    """
    
    try:
        gap_job = client.query(gap_query)
        gap_result = gap_job.result()
        
        missing_dates = list(gap_result)
        if missing_dates:
            logger.warning(f"Found {len(missing_dates)} date gaps. First 10 missing dates:")
            for row in missing_dates:
                logger.warning(f"  - Missing date: {row.missing_date}")
        else:
            logger.info("Quality check passed: No significant date gaps found")
    except Exception as e:
        logger.warning(f"Could not perform continuity check: {e}")

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
    parser = argparse.ArgumentParser(description='Load Elexon data from GCS to BigQuery')
    parser.add_argument('--bucket', type=str, default=DEFAULT_BUCKET, 
                        help=f'GCS bucket name (default: {DEFAULT_BUCKET})')
    parser.add_argument('--project', type=str, default=DEFAULT_PROJECT,
                        help=f'BigQuery project (default: {DEFAULT_PROJECT})')
    parser.add_argument('--dataset', type=str, default=DEFAULT_DATASET,
                        help=f'BigQuery dataset (default: {DEFAULT_DATASET})')
    parser.add_argument('--data-type', type=str, choices=ELEXON_DATA_TYPES + ['all'], 
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
    
    logger.info(f"Starting Elexon data loading process")
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
    data_types_to_process = ELEXON_DATA_TYPES if args.data_type == 'all' else [args.data_type]
    
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
        logger.info("Elexon data loading process completed successfully")
    else:
        logger.warning("Elexon data loading process completed with warnings or errors")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
