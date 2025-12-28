#!/usr/bin/env python3
"""
Auto-ingest BOD (Bid-Offer Data) from Elexon API
Runs every 30 min to backfill last 2 hours

BOD (Bid-Offer Data) is critical for:
- VLP battery revenue analysis
- Balancing mechanism pricing
- Individual unit offer/bid prices

IRIS coverage exists but is unreliable (often incomplete messages)
Therefore use API as primary source
"""

import requests
import json
import time
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
TABLE_ID = 'bmrs_bod'
API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'
LOCATION = 'US'

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
            logging.info(f"Latest BOD data: {latest}")
            return latest
        else:
            # No data, start from 7 days ago
            return datetime.now() - timedelta(days=7)
    except Exception as e:
        logging.error(f"Error getting latest timestamp: {e}")
        return datetime.now() - timedelta(hours=2)

def fetch_bod_data(from_dt, to_dt):
    """Fetch BOD data from Elexon API (1-hour batches - API restriction)"""
    all_records = []
    current = from_dt

    # BOD API has 1-hour maximum window restriction
    while current < to_dt:
        batch_end = min(current + timedelta(hours=1), to_dt)

        url = f"{API_BASE}/datasets/BOD"
        params = {
            'from': current.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to': batch_end.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'format': 'json'
        }

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            records = data.get('data', [])
            if records:
                all_records.extend(records)

        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed for {current}: {e}")

        current = batch_end
        time.sleep(0.5)  # Rate limiting

    logging.info(f"Retrieved {len(all_records)} total BOD records")
    return all_records

def clean_datetime(dt_str):
    """Clean datetime string - remove T and Z for BigQuery compatibility"""
    if dt_str:
        return dt_str.replace('T', ' ').replace('Z', '').split('.')[0]
    return None

def upload_to_bigquery(client, records, batch_size=500):
    """Upload records to BigQuery in batches to avoid 413 errors"""
    if not records:
        logging.info("No records to upload")
        return

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    # Clean datetime fields and add ingestion timestamp
    datetime_fields = ['settlementDate', 'timeFrom', 'timeTo', 'publishTime']
    for record in records:
        for field in datetime_fields:
            if field in record:
                record[field] = clean_datetime(record[field])
        record['_ingested_utc'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Upload in batches to avoid 413 Request Too Large
    total_uploaded = 0
    total_errors = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        try:
            errors = client.insert_rows_json(table_id, batch)

            if errors:
                logging.error(f"Batch {i//batch_size + 1} errors: {errors[:3]}")
                total_errors += len(errors)
            else:
                total_uploaded += len(batch)
                logging.info(f"✅ Uploaded batch {i//batch_size + 1}: {len(batch)} records")
        except Exception as e:
            logging.error(f"Batch {i//batch_size + 1} upload failed: {e}")
            total_errors += len(batch)

    logging.info(f"📊 Upload complete: {total_uploaded} successful, {total_errors} errors")
    return total_errors == 0

def main():
    """Main ingestion routine"""
    logging.info("="*60)
    logging.info("BOD Auto-Ingestion Starting")
    logging.info("="*60)

    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    # Get latest timestamp
    latest = get_latest_timestamp(client)

    # BOD data only available for complete settlement dates (not intraday)
    # Fetch from day after latest to yesterday
    from_dt = (latest + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    to_dt = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)

    # Check if there are new dates to fetch
    if from_dt > to_dt:
        logging.info(f"No new dates to fetch (latest: {latest.date()}, yesterday: {to_dt.date()})")
        logging.info("="*60)
        return

    # Fetch data
    records = fetch_bod_data(from_dt, to_dt)

    # Upload to BigQuery
    if records:
        upload_to_bigquery(client, records)
    else:
        logging.warning("⚠️ No BOD data returned from API")

    logging.info("="*60)
    logging.info("BOD Auto-Ingestion Complete")
    logging.info("="*60)

if __name__ == '__main__':
    main()
