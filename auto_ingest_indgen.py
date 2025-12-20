#!/usr/bin/env python3
"""
Auto-ingest INDGEN (Individual Generation by Unit) from Elexon API
Runs every 15 min to backfill last 2 hours

Individual generation data is critical for:
- Unit-level generation tracking
- VLP battery performance analysis
- Generator availability and output verification
"""

import requests
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET_ID = 'uk_energy_prod'
TABLE_ID = 'bmrs_indgen'
API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'
LOCATION = 'US'

def clean_datetime(dt_str):
    """Clean datetime string for BigQuery (remove T and Z)"""
    if dt_str:
        return dt_str.replace('T', ' ').replace('Z', '').split('.')[0]
    return None

def get_latest_timestamp(client):
    """Get the most recent timestamp in the table"""
    try:
        query = f"""
        SELECT MAX(settlementDate) as latest
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        """
        result = client.query(query).to_dataframe()
        latest = result['latest'].iloc[0]

        if latest:
            logging.info(f"Latest INDGEN data: {latest}")
            return latest
        else:
            # No data, start from 7 days ago
            return datetime.now() - timedelta(days=7)
    except Exception as e:
        logging.error(f"Error getting latest timestamp: {e}")
        return datetime.now() - timedelta(hours=2)

def fetch_indgen_data(from_dt, to_dt):
    """Fetch INDGEN data from Elexon API"""
    url = f"{API_BASE}/datasets/INDGEN"

    params = {
        'from': from_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }

    logging.info(f"Fetching INDGEN from {from_dt} to {to_dt}")

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        records = data.get('data', [])
        logging.info(f"Retrieved {len(records)} INDGEN records")

        return records
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode failed: {e}")
        return []

def upload_to_bigquery(client, records):
    """Upload records to BigQuery"""
    if not records:
        logging.info("No records to upload")
        return

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    # Clean datetime fields and add ingestion timestamp
    for record in records:
        for field in ['settlementDate', 'startTime', 'publishTime']:
            if field in record:
                record[field] = clean_datetime(record[field])
        record['_ingested_utc'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    try:
        errors = client.insert_rows_json(table_id, records)

        if errors:
            logging.error(f"BigQuery insert errors: {errors[:5]}")
            return False
        else:
            logging.info(f"✅ Successfully uploaded {len(records)} INDGEN records")
            return True
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        return False

def main():
    """Main ingestion routine"""
    logging.info("="*60)
    logging.info("INDGEN Auto-Ingestion Starting")
    logging.info("="*60)

    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    # Get latest timestamp
    latest = get_latest_timestamp(client)

    # INDGEN: Fetch complete settlement dates (yesterday and earlier)
    from_dt = (latest + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    to_dt = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)

    # Check if there are new dates to fetch
    if from_dt > to_dt:
        logging.info(f"No new dates to fetch (latest: {latest.date()}, yesterday: {to_dt.date()})")
        logging.info("="*60)
        return

    # Fetch data
    records = fetch_indgen_data(from_dt, to_dt)

    # Upload to BigQuery
    if records:
        upload_to_bigquery(client, records)
    else:
        logging.warning("⚠️ No INDGEN data returned from API")

    logging.info("="*60)
    logging.info("INDGEN Auto-Ingestion Complete")
    logging.info("="*60)

if __name__ == '__main__':
    main()
