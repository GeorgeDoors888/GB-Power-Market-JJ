#!/usr/bin/env python3
"""
Backfill Missing Data Gaps - December 20, 2025
Fills specific known gaps:
- BOD: Dec 18-19 (Dec 17 → Dec 20)
- WINDFOR: Oct 31 - Dec 19 (50 days)
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

def fetch_bod_range(from_date, to_date):
    """Fetch BOD data for date range"""
    url = f"{API_BASE}/datasets/BOD"
    params = {
        'from': from_date.strftime('%Y-%m-%dT00:00:00Z'),
        'to': to_date.strftime('%Y-%m-%dT23:59:59Z'),
        'format': 'json'
    }

    logging.info(f"Fetching BOD: {from_date.date()} → {to_date.date()}")

    try:
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
        records = data.get('data', [])

        if not records:
            logging.warning(f"No BOD data returned for {from_date.date()}")
            return []

        # Clean datetime fields
        for record in records:
            for field in ['settlementDate', 'acceptanceTime']:
                if field in record:
                    record[field] = clean_datetime(record[field])

        logging.info(f"✅ Retrieved {len(records)} BOD records")
        return records

    except requests.exceptions.RequestException as e:
        logging.error(f"BOD API error: {e}")
        return []

def fetch_windfor_range(from_date, to_date):
    """Fetch WINDFOR data for date range"""
    url = f"{API_BASE}/datasets/WINDFOR"
    params = {
        'from': from_date.strftime('%Y-%m-%dT00:00:00Z'),
        'to': to_date.strftime('%Y-%m-%dT23:59:59Z'),
        'format': 'json'
    }

    logging.info(f"Fetching WINDFOR: {from_date.date()} → {to_date.date()}")

    try:
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
        records = data.get('data', [])

        if not records:
            logging.warning(f"No WINDFOR data returned for {from_date.date()}")
            return []

        # Clean datetime fields
        for record in records:
            for field in ['startTime', 'publishTime']:
                if field in record:
                    record[field] = clean_datetime(record[field])

        logging.info(f"✅ Retrieved {len(records)} WINDFOR records")
        return records

    except requests.exceptions.RequestException as e:
        logging.error(f"WINDFOR API error: {e}")
        return []

def upload_to_bigquery(client, table_name, records):
    """Upload records to BigQuery"""
    if not records:
        return False

    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"

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
        logging.info(f"✅ Uploaded {len(records)} records to {table_name}")
        return True
    except Exception as e:
        logging.error(f"Upload error to {table_name}: {e}")
        return False

def backfill_bod_gap():
    """Backfill BOD: Dec 18-19, 2025"""
    logging.info("\n" + "="*60)
    logging.info("BACKFILLING BOD GAP (Dec 18-19)")
    logging.info("="*60)

    client = bigquery.Client(project=PROJECT_ID, location='US')

    # Dec 18-19 (2 days)
    dates_to_fill = [
        (datetime(2025, 12, 18), datetime(2025, 12, 18)),
        (datetime(2025, 12, 19), datetime(2025, 12, 19)),
    ]

    for from_date, to_date in dates_to_fill:
        records = fetch_bod_range(from_date, to_date)
        if records:
            upload_to_bigquery(client, 'bmrs_bod', records)
        time.sleep(2)  # Rate limiting

def backfill_windfor_gap():
    """Backfill WINDFOR: Oct 31 - Dec 19, 2025 (50 days)"""
    logging.info("\n" + "="*60)
    logging.info("BACKFILLING WINDFOR GAP (Oct 31 - Dec 19)")
    logging.info("="*60)

    client = bigquery.Client(project=PROJECT_ID, location='US')

    # Process in 7-day chunks to avoid timeouts
    start_date = datetime(2025, 10, 31)
    end_date = datetime(2025, 12, 19)

    current_date = start_date
    while current_date <= end_date:
        chunk_end = min(current_date + timedelta(days=6), end_date)

        records = fetch_windfor_range(current_date, chunk_end)
        if records:
            upload_to_bigquery(client, 'bmrs_windfor', records)

        current_date = chunk_end + timedelta(days=1)
        time.sleep(3)  # Rate limiting

def main():
    """Run all backfills"""
    logging.info("🚀 Starting Backfill Process - Dec 20, 2025")
    logging.info(f"Project: {PROJECT_ID}")
    logging.info(f"Dataset: {DATASET}\n")

    # BOD: 2 days
    backfill_bod_gap()

    # WINDFOR: 50 days
    backfill_windfor_gap()

    logging.info("\n" + "="*60)
    logging.info("✅ BACKFILL COMPLETE")
    logging.info("="*60)
    logging.info("\nNext steps:")
    logging.info("1. Verify data arrived: Check BigQuery tables")
    logging.info("2. Monitor cron jobs: tail -f logs/*_ingest.log")
    logging.info("3. Check IRIS retention: ~50 days for real-time data")

if __name__ == '__main__':
    main()
