#!/usr/bin/env python3
"""
Historical Data Loader with Schema Transformation (Fixed Version)

This script loads historical data from the GCS bucket 'elexon-historical-data-storage'
to the appropriate BigQuery tables, applying necessary schema transformations.
It includes fixes for the datetime format issue.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from google.cloud import storage, bigquery

def print_with_timestamp(message):
    """Print message with timestamp."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] {message}")
    sys.stdout.flush()  # Ensure output is displayed immediately

def format_datetime(dt_str):
    """Format datetime string to match BigQuery DATETIME format.
    
    BigQuery expects datetime strings in the format YYYY-MM-DD HH:MM:SS[.SSSSSS],
    without the 'Z' timezone indicator or 'T' separator.
    """
    if not dt_str:
        return None
    
    # Replace 'T' with space and remove 'Z' or any timezone info
    return dt_str.replace('T', ' ').split('+')[0].split('Z')[0]

def format_date(date_str):
    """Format date string to ensure it's in YYYY-MM-DD format."""
    if not date_str:
        return None
        
    return date_str

def list_gcs_files(bucket_name, prefix=""):
    """List files in a GCS bucket with a specific prefix."""
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))
    return blobs

def get_file_content(blob):
    """Download and parse JSON content from a GCS blob."""
    try:
        content = blob.download_as_text()
        return json.loads(content)
    except Exception as e:
        print_with_timestamp(f"Error reading {blob.name}: {str(e)}")
        return None


# --- Elexon and NESO Table Transformations ---
def transform_demand_data(data):
    """Transform Elexon demand data to match BigQuery schema (elexon_demand_outturn)."""
    transformed_rows = []
    if 'data' not in data:
        print_with_timestamp("Warning: No 'data' field in JSON")
        return []
    for item in data['data']:
        row = {
            'publishTime': format_datetime(item.get('publishTime')),
            'startTime': format_datetime(item.get('startTime')),
            'settlementDate': format_date(item.get('settlementDate')),
            'settlementPeriod': item.get('settlementPeriod'),
            'initialDemandOutturn': item.get('initialDemandOutturn'),
            'initialTransmissionSystemDemandOutturn': item.get('initialTransmissionSystemDemandOutturn')
        }
        transformed_rows.append(row)
    return transformed_rows

def transform_neso_demand_forecasts(data):
    """Transform NESO demand forecasts to match BigQuery schema."""
    transformed_rows = []
    if 'data' not in data:
        print_with_timestamp("Warning: No 'data' field in JSON")
        return []
    for item in data['data']:
        row = {
            'publishTime': format_datetime(item.get('publishTime')),
            'settlementDate': format_date(item.get('settlementDate')),
            'settlementPeriod': item.get('settlementPeriod'),
            'demand': item.get('demand')
        }
        transformed_rows.append(row)
    return transformed_rows

def transform_neso_carbon_intensity(data):
    """Transform NESO carbon intensity to match BigQuery schema."""
    transformed_rows = []
    if 'data' not in data:
        print_with_timestamp("Warning: No 'data' field in JSON")
        return []
    for item in data['data']:
        row = {
            'publishTime': format_datetime(item.get('publishTime')),
            'settlementDate': format_date(item.get('settlementDate')),
            'settlementPeriod': item.get('settlementPeriod'),
            'fuel_type': item.get('fuel_type'),
            'generation': item.get('generation')
        }
        transformed_rows.append(row)
    return transformed_rows

def transform_neso_balancing_services(data):
    """Transform NESO balancing services to match BigQuery schema."""
    transformed_rows = []
    if 'data' not in data:
        print_with_timestamp("Warning: No 'data' field in JSON")
        return []
    for item in data['data']:
        row = {
            'dataset': item.get('dataset'),
            'settlementDate': format_date(item.get('settlementDate')),
            'settlementPeriod': item.get('settlementPeriod'),
            'id': item.get('id'),
            'cost': item.get('cost'),
            'volume': item.get('volume'),
            'soFlag': item.get('soFlag'),
            'storFlag': item.get('storFlag'),
            'partyId': item.get('partyId'),
            'assetId': item.get('assetId'),
            'isTendered': item.get('isTendered'),
            'service': item.get('service')
        }
        transformed_rows.append(row)
    return transformed_rows

# Add more NESO/Elexon transformation functions as needed

def transform_frequency_data(data):
    """Transform Elexon frequency data to match BigQuery schema (elexon_frequency)."""
    transformed_rows = []
    if 'data' not in data:
        print_with_timestamp("Warning: No 'data' field in JSON")
        return []
    for item in data['data']:
        row = {
            'timestamp': format_datetime(item.get('timestamp')),
            'settlement_date': format_date(item.get('settlement_date')),
            'settlement_period': item.get('settlement_period'),
            'frequency': item.get('frequency')
        }
        transformed_rows.append(row)
    return transformed_rows

def transform_generation_data(data):
    """Transform generation data to match BigQuery schema."""
    transformed_rows = []
    
    if 'data' not in data:
        print_with_timestamp("Warning: No 'data' field in JSON")
        return []
        
    for item in data['data']:
        # Only include fields present in the BigQuery schema
        row = {
            'recordType': item.get('recordType'),
            'startTime': format_datetime(item.get('startTime')),
            'settlementDate': format_date(item.get('settlementDate')),
            'settlementPeriod': item.get('settlementPeriod'),
            'demand': item.get('demand')
        }
        transformed_rows.append(row)
    
    return transformed_rows

def load_data_to_bigquery(rows, table_ref):
    """Load transformed data to BigQuery."""
    client = bigquery.Client()
    
    # Skip if no rows to load
    if not rows:
        print_with_timestamp(f"No rows to load to {table_ref}")
        return False
    
    # Debug output for the first row
    print_with_timestamp(f"Sample row for {table_ref}: {json.dumps(rows[0], indent=2)}")
    
    # Load data
    try:
        errors = client.insert_rows_json(table_ref, rows)
        if errors:
            print_with_timestamp(f"Errors loading data to {table_ref}: {errors}")
            return False
        else:
            print_with_timestamp(f"Successfully loaded {len(rows)} rows to {table_ref}")
            return True
    except Exception as e:
        print_with_timestamp(f"Exception during load: {str(e)}")
        return False


def process_demand_data(bucket_name):
    print_with_timestamp("Processing demand data...")
    table_ref = "jibber-jabber-knowledge.uk_energy_prod.elexon_demand_outturn"
    blobs = list_gcs_files(bucket_name, "demand/")
    print_with_timestamp(f"Found {len(blobs)} demand files")
    total_rows = 0
    success_count = 0
    for blob in blobs:
        print_with_timestamp(f"Processing {blob.name}")
        data = get_file_content(blob)
        if not data:
            continue
        transformed_rows = transform_demand_data(data)
        if transformed_rows:
            if load_data_to_bigquery(transformed_rows, table_ref):
                total_rows += len(transformed_rows)
                success_count += 1
    print_with_timestamp(f"Demand data processing complete. Loaded {total_rows} rows from {success_count}/{len(blobs)} files")
    return success_count > 0

def process_neso_demand_forecasts(bucket_name):
    print_with_timestamp("Processing NESO demand forecasts...")
    table_ref = "jibber-jabber-knowledge.uk_energy_prod.neso_demand_forecasts"
    blobs = list_gcs_files(bucket_name, "neso/demand_forecasts/")
    print_with_timestamp(f"Found {len(blobs)} NESO demand forecast files")
    total_rows = 0
    success_count = 0
    for blob in blobs:
        print_with_timestamp(f"Processing {blob.name}")
        data = get_file_content(blob)
        if not data:
            continue
        transformed_rows = transform_neso_demand_forecasts(data)
        if transformed_rows:
            if load_data_to_bigquery(transformed_rows, table_ref):
                total_rows += len(transformed_rows)
                success_count += 1
    print_with_timestamp(f"NESO demand forecasts processing complete. Loaded {total_rows} rows from {success_count}/{len(blobs)} files")
    return success_count > 0

def process_neso_carbon_intensity(bucket_name):
    print_with_timestamp("Processing NESO carbon intensity...")
    table_ref = "jibber-jabber-knowledge.uk_energy_prod.neso_carbon_intensity"
    blobs = list_gcs_files(bucket_name, "neso/carbon_intensity/")
    print_with_timestamp(f"Found {len(blobs)} NESO carbon intensity files")
    total_rows = 0
    success_count = 0
    for blob in blobs:
        print_with_timestamp(f"Processing {blob.name}")
        data = get_file_content(blob)
        if not data:
            continue
        transformed_rows = transform_neso_carbon_intensity(data)
        if transformed_rows:
            if load_data_to_bigquery(transformed_rows, table_ref):
                total_rows += len(transformed_rows)
                success_count += 1
    print_with_timestamp(f"NESO carbon intensity processing complete. Loaded {total_rows} rows from {success_count}/{len(blobs)} files")
    return success_count > 0

def process_neso_balancing_services(bucket_name):
    print_with_timestamp("Processing NESO balancing services...")
    table_ref = "jibber-jabber-knowledge.uk_energy_prod.neso_balancing_services"
    blobs = list_gcs_files(bucket_name, "neso/balancing_services/")
    print_with_timestamp(f"Found {len(blobs)} NESO balancing services files")
    total_rows = 0
    success_count = 0
    for blob in blobs:
        print_with_timestamp(f"Processing {blob.name}")
        data = get_file_content(blob)
        if not data:
            continue
        transformed_rows = transform_neso_balancing_services(data)
        if transformed_rows:
            if load_data_to_bigquery(transformed_rows, table_ref):
                total_rows += len(transformed_rows)
                success_count += 1
    print_with_timestamp(f"NESO balancing services processing complete. Loaded {total_rows} rows from {success_count}/{len(blobs)} files")
    return success_count > 0

def process_frequency_data(bucket_name):
    """Process frequency data from GCS to BigQuery."""
    print_with_timestamp("Processing frequency data...")
    table_ref = "jibber-jabber-knowledge.uk_energy_data.elexon_frequency"
    
    # List files
    blobs = list_gcs_files(bucket_name, "frequency/")
    print_with_timestamp(f"Found {len(blobs)} frequency files")
    
    total_rows = 0
    success_count = 0
    
    for blob in blobs:
        print_with_timestamp(f"Processing {blob.name}")
        data = get_file_content(blob)
        if not data:
            continue
            
        transformed_rows = transform_frequency_data(data)
        if transformed_rows:
            if load_data_to_bigquery(transformed_rows, table_ref):
                total_rows += len(transformed_rows)
                success_count += 1
    
    print_with_timestamp(f"Frequency data processing complete. Loaded {total_rows} rows from {success_count}/{len(blobs)} files")
    return success_count > 0

def process_generation_data(bucket_name):
    """Process generation data from GCS to BigQuery."""
    print_with_timestamp("Processing generation data...")
    table_ref = "jibber-jabber-knowledge.uk_energy_prod.elexon_generation_outturn"
    
    # List files
    blobs = list_gcs_files(bucket_name, "generation/")
    print_with_timestamp(f"Found {len(blobs)} generation files")
    
    total_rows = 0
    success_count = 0
    
    for blob in blobs:
        print_with_timestamp(f"Processing {blob.name}")
        data = get_file_content(blob)
        if not data:
            continue
            
        transformed_rows = transform_generation_data(data)
        if transformed_rows:
            if load_data_to_bigquery(transformed_rows, table_ref):
                total_rows += len(transformed_rows)
                success_count += 1
    
    print_with_timestamp(f"Generation data processing complete. Loaded {total_rows} rows from {success_count}/{len(blobs)} files")
    return success_count > 0


def main():
    """Main function to execute the data loading process."""
    parser = argparse.ArgumentParser(description='Load historical data from GCS to BigQuery with schema transformation')
    parser.add_argument('--bucket', type=str, default='elexon-historical-data-storage', 
                        help='GCS bucket name (default: elexon-historical-data-storage)')
    parser.add_argument('--dataset', type=str, choices=[
        'demand', 'frequency', 'generation',
        'neso_demand_forecasts', 'neso_carbon_intensity', 'neso_balancing_services',
        'all'], default='all', help='Dataset to process (default: all)')
    args = parser.parse_args()
    print_with_timestamp(f"Starting historical data loading process")
    print_with_timestamp(f"Using bucket: {args.bucket}")
    print_with_timestamp(f"Processing dataset(s): {args.dataset}")
    success = True
    if args.dataset == 'demand' or args.dataset == 'all':
        if not process_demand_data(args.bucket):
            success = False
    if args.dataset == 'frequency' or args.dataset == 'all':
        if not process_frequency_data(args.bucket):
            success = False
    if args.dataset == 'generation' or args.dataset == 'all':
        if not process_generation_data(args.bucket):
            success = False
    if args.dataset == 'neso_demand_forecasts' or args.dataset == 'all':
        if not process_neso_demand_forecasts(args.bucket):
            success = False
    if args.dataset == 'neso_carbon_intensity' or args.dataset == 'all':
        if not process_neso_carbon_intensity(args.bucket):
            success = False
    if args.dataset == 'neso_balancing_services' or args.dataset == 'all':
        if not process_neso_balancing_services(args.bucket):
            success = False
    if success:
        print_with_timestamp("Historical data loading process completed successfully")
    else:
        print_with_timestamp("Historical data loading process completed with errors")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
