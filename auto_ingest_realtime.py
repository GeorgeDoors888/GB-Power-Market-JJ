#!/usr/bin/env python3
"""
Automated Real-Time Ingestion Script
Polls Elexon BMRS API every 15 minutes for latest data across all priority datasets
"""

import requests
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
import sys
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/auto_ingest_realtime_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET_ID = 'uk_energy_prod'
API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'

# Priority datasets for real-time ingestion (< 30 min lag)
PRIORITY_DATASETS = {
    'COSTS': {
        'endpoint': '/balancing/settlement/system-prices/{date}/{sp}',
        'table': 'bmrs_costs',
        'window': timedelta(hours=2),  # Fetch last 2 hours
        'param_format': 'path',  # date/SP in URL path (no query params)
        'timestamp_col': 'settlementDate',
    },
    'FUELINST': {
        'endpoint': '/generation/outturn/summary',
        'table': 'bmrs_fuelinst',
        'window': timedelta(hours=2),
        'param_format': 'from_to',  # from/to timestamps
        'timestamp_col': 'startTime',  # FUELINST uses startTime, not settlementDate
    },
    'FREQ': {
        'endpoint': '/system/frequency',
        'table': 'bmrs_freq',
        'window': timedelta(minutes=30),
        'param_format': 'from_to',
        'timestamp_col': 'measurementTime',  # FREQ uses measurementTime, not settlementDate!
    },
    'MID': {
        'endpoint': '/balancing/pricing/market-index',
        'table': 'bmrs_mid',
        'window': timedelta(hours=2),
        'param_format': 'from_to',
        'timestamp_col': 'settlementDate',
    },
    # BOALF and BOD handled separately (more complex)
}


def get_latest_timestamp(client, table_name, timestamp_col='settlementDate'):
    """Get the most recent timestamp in the table to avoid duplicates"""
    try:
        query = f"""
        SELECT MAX({timestamp_col}) as latest
        FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
        """
        result = client.query(query).to_dataframe()
        latest = result['latest'].iloc[0]

        if latest:
            logging.info(f"📊 {table_name}: Latest data at {latest}")
            return latest
        else:
            logging.warning(f"⚠️  {table_name}: No existing data, fetching from 24h ago")
            return datetime.now() - timedelta(hours=24)
    except Exception as e:
        logging.error(f"❌ Error checking {table_name}: {e}")
        return datetime.now() - timedelta(hours=24)


def fetch_data(endpoint, params):
    """Fetch data from Elexon API"""
    url = f"{API_BASE}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if 'data' in data:
            return data['data']
        else:
            logging.warning(f"⚠️  No 'data' field in response from {endpoint}")
            return []
    except Exception as e:
        logging.error(f"❌ Error fetching from {endpoint}: {e}")
        return []


def convert_datetime(dt_str):
    """Convert ISO 8601 datetime to BigQuery DATETIME format"""
    if dt_str:
        # "2025-12-18T16:35:00Z" → "2025-12-18 16:35:00"
        return dt_str.replace('T', ' ').replace('Z', '').split('.')[0]
    return None


def transform_costs_record(record):
    """Transform COSTS (system prices) record"""
    return {
        'settlementDate': convert_datetime(record.get('settlementDate')),
        'settlementPeriod': record.get('settlementPeriod'),
        'systemSellPrice': record.get('systemSellPrice'),
        'systemBuyPrice': record.get('systemBuyPrice'),
        'priceDerivationCode': record.get('priceDerivationCode'),
        '_ingested_utc': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        '_source_api': 'AUTO_REALTIME',
    }


def ingest_dataset(client, dataset_name, config):
    """Ingest a single dataset"""
    logging.info(f"🔄 Processing {dataset_name}...")

    table_name = config['table']
    endpoint = config['endpoint']
    window = config['window']
    timestamp_col = config.get('timestamp_col', 'settlementDate')

    # Get latest timestamp from table
    latest = get_latest_timestamp(client, table_name, timestamp_col)

    # Calculate fetch window (from latest to now)
    from_time = latest
    to_time = datetime.now()

    # Build params based on format
    if config['param_format'] == 'path':
        # COSTS uses path-based API: /system-prices/{date}/{sp}
        logging.info(f"📊 {dataset_name}: Using path-based API (individual SP calls)")
        records = []

        # Call API for recent settlement periods
        current_time = from_time
        while current_time <= to_time:
            date_str = current_time.strftime('%Y-%m-%d')
            # Calculate SP (1-50, 30-min periods starting at 23:00 previous day)
            sp = ((current_time.hour * 60 + current_time.minute) // 30) + 1
            if sp > 50:
                sp = 50

            sp_endpoint = endpoint.format(date=date_str, sp=sp)
            sp_data = fetch_data(sp_endpoint, {'format': 'json'})
            if sp_data:
                records.extend(sp_data)

            current_time += timedelta(minutes=30)

    elif config['param_format'] == 'from_to':
        params = {
            'from': from_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to': to_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'format': 'json'
        }
        records = fetch_data(endpoint, params)
    else:
        logging.error(f"❌ Unknown param format: {config['param_format']}")
        return

    if not records:
        logging.info(f"✅ {dataset_name}: No new records (up to date)")
        return

    logging.info(f"📥 {dataset_name}: Fetched {len(records)} records")

    # Transform records (dataset-specific)
    if dataset_name == 'COSTS':
        transformed = [transform_costs_record(r) for r in records]
    else:
        # Generic transformation (convert datetime fields + add metadata)
        transformed = []
        for r in records:
            # Convert all datetime-like fields to BigQuery format
            for key, value in r.items():
                if isinstance(value, str) and 'T' in value and 'Z' in value:
                    r[key] = convert_datetime(value)

            r['_ingested_utc'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            r['_source_api'] = 'AUTO_REALTIME'
            transformed.append(r)

    # Upload to BigQuery (using insert_rows_json for real-time)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    errors = client.insert_rows_json(table_ref, transformed)

    if errors:
        logging.error(f"❌ {dataset_name}: Upload errors: {errors[:3]}...")  # Show first 3
    else:
        logging.info(f"✅ {dataset_name}: Inserted {len(transformed)} records")


def main():
    """Main execution"""
    logging.info("=" * 60)
    logging.info("⚡ GB Power Market - Auto Real-Time Ingestion")
    logging.info("=" * 60)

    client = bigquery.Client(project=PROJECT_ID, location='US')

    for dataset_name, config in PRIORITY_DATASETS.items():
        try:
            ingest_dataset(client, dataset_name, config)
        except Exception as e:
            logging.error(f"❌ Failed to process {dataset_name}: {e}")
            import traceback
            traceback.print_exc()

    logging.info("✅ Auto ingestion cycle complete")
    logging.info("=" * 60 + "\n")


if __name__ == "__main__":
    main()
