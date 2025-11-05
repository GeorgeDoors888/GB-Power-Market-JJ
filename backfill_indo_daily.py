#!/usr/bin/env python3
"""
Daily INDO Data Backfill Script
Downloads last 60 days of INDO/INDGEN/INDDEM data from Elexon API to maintain continuous coverage
Runs daily via cron to ensure no gaps in data
"""

import requests
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/iris-pipeline/logs/indo_backfill.log'),
        logging.StreamHandler()
    ]
)

# BigQuery setup
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'

# BMRS API endpoint (no auth required for public data)
BMRS_API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'

# Dataset mappings
DATASETS = {
    'INDO': {
        'endpoint': '/datasets/INDO',
        'table': 'bmrs_indo',
        'schema': [
            bigquery.SchemaField('dataset', 'STRING'),
            bigquery.SchemaField('publishTime', 'TIMESTAMP'),
            bigquery.SchemaField('startTime', 'TIMESTAMP'),
            bigquery.SchemaField('settlementDate', 'DATE'),
            bigquery.SchemaField('settlementPeriod', 'INTEGER'),
            bigquery.SchemaField('demand', 'FLOAT'),
            bigquery.SchemaField('ingested_utc', 'TIMESTAMP'),
            bigquery.SchemaField('source', 'STRING')
        ]
    },
    'INDGEN': {
        'endpoint': '/datasets/INDGEN',
        'table': 'bmrs_indgen',
        'schema': [
            bigquery.SchemaField('dataset', 'STRING'),
            bigquery.SchemaField('publishTime', 'TIMESTAMP'),
            bigquery.SchemaField('startTime', 'TIMESTAMP'),
            bigquery.SchemaField('settlementDate', 'DATE'),
            bigquery.SchemaField('settlementPeriod', 'INTEGER'),
            bigquery.SchemaField('generation', 'FLOAT'),
            bigquery.SchemaField('boundary', 'STRING'),
            bigquery.SchemaField('ingested_utc', 'TIMESTAMP'),
            bigquery.SchemaField('source', 'STRING')
        ]
    },
    'INDDEM': {
        'endpoint': '/datasets/INDDEM',
        'table': 'bmrs_inddem',
        'schema': [
            bigquery.SchemaField('dataset', 'STRING'),
            bigquery.SchemaField('publishTime', 'TIMESTAMP'),
            bigquery.SchemaField('startTime', 'TIMESTAMP'),
            bigquery.SchemaField('settlementDate', 'DATE'),
            bigquery.SchemaField('settlementPeriod', 'INTEGER'),
            bigquery.SchemaField('demand', 'FLOAT'),
            bigquery.SchemaField('boundary', 'STRING'),
            bigquery.SchemaField('ingested_utc', 'TIMESTAMP'),
            bigquery.SchemaField('source', 'STRING')
        ]
    }
}


def download_indo_data(dataset_name, from_date, to_date):
    """Download INDO data from Elexon API"""
    dataset_info = DATASETS[dataset_name]
    url = f"{BMRS_API_BASE}{dataset_info['endpoint']}"
    
    params = {
        'settlementDateFrom': from_date.strftime('%Y-%m-%d'),
        'settlementDateTo': to_date.strftime('%Y-%m-%d'),
        'format': 'json'
    }
    
    logging.info(f"Downloading {dataset_name} from {from_date} to {to_date}...")
    
    try:
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            records = data['data']
            logging.info(f"Downloaded {len(records)} records for {dataset_name}")
            return records
        else:
            logging.warning(f"No data field in response for {dataset_name}")
            return []
            
    except Exception as e:
        logging.error(f"Error downloading {dataset_name}: {e}")
        return []


def transform_record(record, dataset_name):
    """Transform API record to BigQuery format"""
    ingested_utc = datetime.utcnow().isoformat()
    
    # Base fields common to all
    transformed = {
        'dataset': record.get('dataset', dataset_name),
        'publishTime': record.get('publishTime'),
        'startTime': record.get('startTime'),
        'settlementDate': record.get('settlementDate'),
        'settlementPeriod': record.get('settlementPeriod'),
        'ingested_utc': ingested_utc,
        'source': 'API_BACKFILL'
    }
    
    # Dataset-specific fields
    if dataset_name == 'INDO':
        transformed['demand'] = record.get('demand')
    elif dataset_name == 'INDGEN':
        transformed['generation'] = record.get('generation')
        transformed['boundary'] = record.get('boundary')
    elif dataset_name == 'INDDEM':
        transformed['demand'] = record.get('demand')
        transformed['boundary'] = record.get('boundary')
    
    return transformed


def upload_to_bigquery(dataset_name, records):
    """Upload records to BigQuery, avoiding duplicates"""
    if not records:
        logging.info(f"No records to upload for {dataset_name}")
        return 0
    
    dataset_info = DATASETS[dataset_name]
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{dataset_info['table']}"
    
    client = bigquery.Client(project=BQ_PROJECT)
    
    # Check if table exists, create if not
    try:
        client.get_table(table_id)
        logging.info(f"Table {table_id} exists")
    except Exception:
        logging.info(f"Creating table {table_id}")
        table = bigquery.Table(table_id, schema=dataset_info['schema'])
        client.create_table(table)
    
    # Transform records
    rows = [transform_record(r, dataset_name) for r in records]
    
    # Upload using streaming insert (handles duplicates automatically)
    logging.info(f"Uploading {len(rows)} rows to {table_id}...")
    
    try:
        # Use WRITE_APPEND to add new data
        job_config = bigquery.LoadJobConfig(
            schema=dataset_info['schema'],
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        
        # Create temp table to check for duplicates
        temp_table_id = f"{table_id}_temp"
        client.delete_table(temp_table_id, not_found_ok=True)
        
        # Load to temp table
        job = client.load_table_from_json(rows, temp_table_id, job_config=job_config)
        job.result()
        
        # Merge only new records (avoid duplicates based on settlementDate + settlementPeriod + boundary if exists)
        if dataset_name == 'INDO':
            merge_query = f"""
            MERGE `{table_id}` T
            USING `{temp_table_id}` S
            ON T.settlementDate = S.settlementDate 
               AND T.settlementPeriod = S.settlementPeriod
               AND T.source = 'API_BACKFILL'
            WHEN NOT MATCHED THEN
              INSERT ROW
            """
        else:  # INDGEN or INDDEM have boundary field
            merge_query = f"""
            MERGE `{table_id}` T
            USING `{temp_table_id}` S
            ON T.settlementDate = S.settlementDate 
               AND T.settlementPeriod = S.settlementPeriod
               AND T.boundary = S.boundary
               AND T.source = 'API_BACKFILL'
            WHEN NOT MATCHED THEN
              INSERT ROW
            """
        
        merge_job = client.query(merge_query)
        result = merge_job.result()
        
        # Get count of inserted rows
        rows_inserted = merge_job.num_dml_affected_rows
        
        # Clean up temp table
        client.delete_table(temp_table_id, not_found_ok=True)
        
        logging.info(f"Successfully inserted {rows_inserted} new rows to {table_id}")
        return rows_inserted
        
    except Exception as e:
        logging.error(f"Error uploading to BigQuery: {e}")
        return 0


def main():
    """Main backfill function"""
    logging.info("="*70)
    logging.info("Starting INDO Daily Backfill")
    logging.info("="*70)
    
    # Calculate date range (last 60 days)
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=60)
    
    logging.info(f"Date range: {from_date} to {to_date}")
    
    total_inserted = 0
    
    # Process each dataset
    for dataset_name in ['INDO', 'INDGEN', 'INDDEM']:
        logging.info(f"\nProcessing {dataset_name}...")
        
        # Download data
        records = download_indo_data(dataset_name, from_date, to_date)
        
        # Upload to BigQuery
        inserted = upload_to_bigquery(dataset_name, records)
        total_inserted += inserted
    
    logging.info("="*70)
    logging.info(f"Backfill complete! Total new rows inserted: {total_inserted}")
    logging.info("="*70)
    
    return total_inserted


if __name__ == '__main__':
    try:
        result = main()
        sys.exit(0 if result >= 0 else 1)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
