#!/usr/bin/env python3
"""
EBOCF Backfill Script - Dec 14-18, 2025
Downloads pre-calculated cashflows (£) from Elexon BMRS API
HIGH VALUE: Upgrades revenue tracking coverage from 87% to 98%+
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ebocf_backfill.log'),
        logging.StreamHandler()
    ]
)

# Configuration
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BQ_TABLE = 'bmrs_ebocf'

API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'
ENDPOINT = '/balancing/settlement/indicative/cashflows/all'

# Gap period
GAP_START = '2025-12-14'
GAP_END = '2025-12-18'

def convert_datetime(dt_str):
    """Convert ISO 8601 to BigQuery DATETIME format"""
    if dt_str:
        return dt_str.replace('T', ' ').replace('Z', '').split('.')[0]
    return None


def fetch_ebocf(bid_offer, settlement_date, settlement_period):
    """
    Fetch EBOCF data for specific settlement period

    Args:
        bid_offer: "BID" or "OFFER"
        settlement_date: "YYYY-MM-DD"
        settlement_period: 1-50

    Returns:
        List of EBOCF records
    """
    url = f"{API_BASE}{ENDPOINT}/{bid_offer}/{settlement_date}/{settlement_period}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'data' in data:
            return data['data']
        else:
            logging.warning(f"No 'data' field for {settlement_date} SP{settlement_period} {bid_offer}")
            return []

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # No data for this SP (expected for some periods)
            return []
        else:
            logging.error(f"HTTP error for {settlement_date} SP{settlement_period} {bid_offer}: {e}")
            return []
    except Exception as e:
        logging.error(f"Error fetching {settlement_date} SP{settlement_period} {bid_offer}: {e}")
        return []


def transform_record(record, bid_offer):
    """Transform EBOCF record to match existing BigQuery schema"""
    ingested_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Match existing schema: settlementDate (STRING), _direction, totalCashflow
    return {
        'settlementDate': record.get('settlementDate'),  # Keep as STRING (existing schema)
        'settlementPeriod': record.get('settlementPeriod'),
        'startTime': record.get('startTime'),
        'createdDateTime': record.get('createdDateTime'),
        'bmUnit': record.get('bmUnit'),
        'bmUnitType': record.get('bmUnitType'),
        'leadPartyName': record.get('leadPartyName'),
        'nationalGridBmUnit': record.get('nationalGridBmUnit'),
        'bidOfferPairCashflows': None,  # Not in simplified API response
        'totalCashflow': record.get('cashflow', 0.0),  # API calls it 'cashflow'
        '_fetched_date': record.get('settlementDate'),
        '_fetched_sp': record.get('settlementPeriod'),
        '_direction': bid_offer.lower(),  # 'bid' or 'offer'
        '_ingested_utc': ingested_utc,
    }


def create_table_if_not_exists(client):
    """Create EBOCF table if it doesn't exist"""
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

    schema = [
        bigquery.SchemaField('settlementDate', 'DATETIME'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('acceptanceNumber', 'STRING'),
        bigquery.SchemaField('acceptanceTime', 'DATETIME'),
        bigquery.SchemaField('deemedBoFlag', 'BOOLEAN'),
        bigquery.SchemaField('soFlag', 'BOOLEAN'),
        bigquery.SchemaField('storFlag', 'BOOLEAN'),
        bigquery.SchemaField('rrFlag', 'BOOLEAN'),
        bigquery.SchemaField('cashflow', 'FLOAT64'),
        bigquery.SchemaField('volume', 'FLOAT64'),
        bigquery.SchemaField('price', 'FLOAT64'),
        bigquery.SchemaField('bidOffer', 'STRING'),
        bigquery.SchemaField('_ingested_utc', 'STRING'),
        bigquery.SchemaField('_source_api', 'STRING'),
    ]

    try:
        client.get_table(table_id)
        logging.info(f"✅ Table {BQ_TABLE} already exists")
    except:
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            field="settlementDate",
            type_=bigquery.TimePartitioningType.DAY
        )
        table.clustering_fields = ["bmUnit", "settlementPeriod"]

        table = client.create_table(table)
        logging.info(f"✅ Created table {BQ_TABLE}")


def upload_records(client, records):
    """Upload records to BigQuery using streaming insert"""
    if not records:
        return 0

    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    errors = client.insert_rows_json(table_ref, records)

    if errors:
        logging.error(f"❌ Upload errors: {errors[:3]}...")
        return 0
    else:
        return len(records)


def backfill_date_range():
    """Backfill EBOCF for gap period"""
    logging.info("=" * 60)
    logging.info("⚡ EBOCF Backfill - Pre-Calculated Cashflows")
    logging.info("=" * 60)
    logging.info(f"📅 Gap Period: {GAP_START} to {GAP_END}")
    logging.info(f"📍 Target: {BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")
    logging.info("")

    client = bigquery.Client(project=BQ_PROJECT, location='US')

    # Verify table exists
    try:
        table = client.get_table(f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")
        logging.info(f"✅ Table {BQ_TABLE} exists ({len(table.schema)} fields)")
    except:
        logging.error(f"❌ Table {BQ_TABLE} not found!")
        return

    # Parse dates
    start = datetime.strptime(GAP_START, '%Y-%m-%d').date()
    end = datetime.strptime(GAP_END, '%Y-%m-%d').date()

    total_days = (end - start).days + 1
    logging.info(f"📊 Processing {total_days} days × 50 SPs × 2 (BID/OFFER) = {total_days * 50 * 2} API calls")
    logging.info("")

    current = start
    day_num = 0
    total_records = 0

    while current <= end:
        day_num += 1
        date_str = current.strftime('%Y-%m-%d')
        logging.info(f"[{day_num}/{total_days}] Processing {date_str}...")

        day_records = []

        for sp in range(1, 51):  # Settlement periods 1-50
            for bid_offer in ['BID', 'OFFER']:
                # Fetch data
                records = fetch_ebocf(bid_offer, date_str, sp)

                # Transform
                for record in records:
                    transformed = transform_record(record, bid_offer)
                    day_records.append(transformed)

                # Rate limiting (don't hammer API)
                time.sleep(0.05)  # 50ms between calls

        # Upload day's records
        if day_records:
            uploaded = upload_records(client, day_records)
            total_records += uploaded
            logging.info(f"   ✅ Uploaded {uploaded:,} records for {date_str}")
        else:
            logging.info(f"   ⚠️  No records for {date_str}")

        current += timedelta(days=1)

    logging.info("")
    logging.info("=" * 60)
    logging.info(f"✅ EBOCF Backfill Complete!")
    logging.info(f"📊 Total records inserted: {total_records:,}")
    logging.info("=" * 60)


if __name__ == "__main__":
    backfill_date_range()
