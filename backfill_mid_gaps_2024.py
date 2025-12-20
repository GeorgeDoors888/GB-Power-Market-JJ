#!/usr/bin/env python3
"""
Backfill bmrs_mid "Missing" 24 Days (2024)
These were thought to be permanent data loss but API HAS THE DATA!
"""

import requests
import json
import io
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'

def clean_datetime(dt_str):
    """Clean datetime string for BigQuery"""
    if dt_str:
        return dt_str.replace('T', ' ').replace('Z', '').split('.')[0]
    return None

def fetch_mid_date(date):
    """Fetch MID data for a single date"""
    url = f"{API_BASE}/balancing/pricing/market-index"
    params = {
        'from': f'{date}T00:00:00Z',
        'to': f'{date}T23:59:59Z',
        'format': 'json'
    }
    
    logging.info(f"Fetching MID: {date}")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        records = data.get('data', [])
        
        if not records:
            logging.warning(f"No MID data for {date}")
            return []
        
        # Clean datetime fields
        for record in records:
            for field in ['settlementDate', 'publishTime', 'startTime', 'deliveryStartTime', 'deliveryEndTime']:
                if field in record:
                    record[field] = clean_datetime(record[field])
        
        logging.info(f"✅ Retrieved {len(records)} MID records for {date}")
        return records
        
    except requests.exceptions.RequestException as e:
        logging.error(f"MID API error for {date}: {e}")
        return []

def upload_to_bigquery(client, records):
    """Upload records to BigQuery"""
    if not records:
        return False
    
    table_id = f"{PROJECT_ID}.{DATASET}.bmrs_mid"
    
    # Create newline-delimited JSON
    json_data = '\n'.join([json.dumps(record) for record in records])
    json_file = io.StringIO(json_data)
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
    )
    
    try:
        job = client.load_table_from_file(json_file, table_id, job_config=job_config)
        job.result()  # Wait for completion
        logging.info(f"✅ Uploaded {len(records)} records to bmrs_mid")
        return True
    except Exception as e:
        logging.error(f"Upload error: {e}")
        return False

def main():
    """Backfill the 24 "missing" days"""
    logging.info("\n" + "="*60)
    logging.info("🔍 BACKFILLING bmrs_mid 24-Day Gap (2024)")
    logging.info("="*60)
    
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    # The supposedly missing dates
    missing_dates = [
        # Apr 16-21 (6 days)
        '2024-04-16', '2024-04-17', '2024-04-18', '2024-04-19', '2024-04-20', '2024-04-21',
        # Jul 16-21 (6 days)
        '2024-07-16', '2024-07-17', '2024-07-18', '2024-07-19', '2024-07-20', '2024-07-21',
        # Sep 10-15 (6 days)
        '2024-09-10', '2024-09-11', '2024-09-12', '2024-09-13', '2024-09-14', '2024-09-15',
        # Oct 08-13 (6 days)
        '2024-10-08', '2024-10-09', '2024-10-10', '2024-10-11', '2024-10-12', '2024-10-13',
    ]
    
    logging.info(f"Processing {len(missing_dates)} dates\n")
    
    success = 0
    failed = 0
    
    for date_str in missing_dates:
        records = fetch_mid_date(date_str)
        
        if records:
            if upload_to_bigquery(client, records):
                success += 1
            else:
                failed += 1
        else:
            failed += 1
        
        time.sleep(1)  # Rate limiting
    
    logging.info("\n" + "="*60)
    logging.info(f"✅ BACKFILL COMPLETE")
    logging.info(f"Success: {success}/{len(missing_dates)} dates")
    logging.info(f"Failed: {failed}/{len(missing_dates)} dates")
    logging.info("="*60)

if __name__ == '__main__':
    main()
