#!/usr/bin/env python3
"""
BOALF Gap Backfill Script - Oct 29 - Nov 3, 2025
Downloads missing BOALF data from Elexon BMRS API to fill the gap between historical and IRIS tables
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
        logging.FileHandler('boalf_backfill.log'),
        logging.StreamHandler()
    ]
)

# BigQuery setup
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BQ_TABLE = 'bmrs_boalf'

# BMRS API endpoint (no auth required for public data)
BMRS_API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'
BOALF_ENDPOINT = '/datasets/BOALF'

# Gap period to fill
GAP_START = '2025-11-05'
GAP_END = '2025-12-18'

# BigQuery schema for BOALF (25 fields total - matches production table)
BOALF_SCHEMA = [
    bigquery.SchemaField('dataset', 'STRING'),
    bigquery.SchemaField('settlementDate', 'DATETIME'),
    bigquery.SchemaField('settlementPeriodFrom', 'INTEGER'),
    bigquery.SchemaField('settlementPeriodTo', 'INTEGER'),
    bigquery.SchemaField('timeFrom', 'STRING'),
    bigquery.SchemaField('timeTo', 'STRING'),
    bigquery.SchemaField('levelFrom', 'INTEGER'),
    bigquery.SchemaField('levelTo', 'INTEGER'),
    bigquery.SchemaField('acceptanceNumber', 'INTEGER'),
    bigquery.SchemaField('acceptanceTime', 'DATETIME'),
    bigquery.SchemaField('deemedBoFlag', 'BOOLEAN'),
    bigquery.SchemaField('soFlag', 'BOOLEAN'),
    bigquery.SchemaField('amendmentFlag', 'STRING'),
    bigquery.SchemaField('storFlag', 'BOOLEAN'),
    bigquery.SchemaField('rrFlag', 'BOOLEAN'),
    bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
    bigquery.SchemaField('bmUnit', 'STRING'),
    bigquery.SchemaField('_dataset', 'STRING'),
    bigquery.SchemaField('_window_from_utc', 'STRING'),
    bigquery.SchemaField('_window_to_utc', 'STRING'),
    bigquery.SchemaField('_ingested_utc', 'STRING'),
    bigquery.SchemaField('_source_columns', 'STRING'),
    bigquery.SchemaField('_source_api', 'STRING'),
    bigquery.SchemaField('_hash_source_cols', 'STRING'),
    bigquery.SchemaField('_hash_key', 'STRING'),
]


def download_boalf_data(from_date, to_date):
    """Download BOALF data from Elexon API"""
    url = f"{BMRS_API_BASE}{BOALF_ENDPOINT}"

    params = {
        'from': f'{from_date}T00:00:00Z',
        'to': f'{to_date}T23:59:59Z',
        'format': 'json'
    }

    logging.info(f"📥 Downloading BOALF from {from_date} to {to_date}...")
    logging.info(f"   URL: {url}")
    logging.info(f"   Params: {params}")

    all_records = []

    try:
        response = requests.get(url, params=params, timeout=600)
        response.raise_for_status()
        data = response.json()

        if 'data' in data:
            records = data['data']
            logging.info(f"✅ Downloaded {len(records)} BOALF records")
            all_records.extend(records)
        else:
            logging.warning(f"⚠️  No 'data' field in response")
            logging.info(f"   Response keys: {data.keys()}")

        # Check for pagination
        page = 1
        while 'metadata' in data and 'pagination' in data['metadata']:
            pagination = data['metadata']['pagination']
            if 'next' in pagination and pagination['next']:
                page += 1
                logging.info(f"📄 Fetching page {page}...")

                next_url = pagination['next']
                response = requests.get(next_url, timeout=600)
                response.raise_for_status()
                data = response.json()

                if 'data' in data:
                    records = data['data']
                    logging.info(f"✅ Downloaded {len(records)} more records (page {page})")
                    all_records.extend(records)
            else:
                break

        return all_records

    except Exception as e:
        logging.error(f"❌ Error downloading BOALF: {e}")
        import traceback
        traceback.print_exc()
        return []


def transform_record(record):
    """Transform API record to BigQuery format (all 25 fields)"""
    ingested_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Convert ISO 8601 datetime strings to BigQuery DATETIME format
    # API returns: "2025-12-18T16:35:00Z" → BigQuery needs: "2025-12-18 16:35:00"
    def convert_datetime(dt_str):
        if dt_str:
            return dt_str.replace('T', ' ').replace('Z', '').split('.')[0]
        return None

    # Extract time windows for metadata
    time_from = record.get('timeFrom', '')
    time_to = record.get('timeTo', '')

    transformed = {
        # Core BOALF fields (from API)
        'dataset': record.get('dataset', 'BOALF'),
        'settlementDate': convert_datetime(record.get('settlementDate')),
        'settlementPeriodFrom': record.get('settlementPeriodFrom'),
        'settlementPeriodTo': record.get('settlementPeriodTo'),
        'timeFrom': time_from,
        'timeTo': time_to,
        'levelFrom': record.get('levelFrom'),
        'levelTo': record.get('levelTo'),
        'acceptanceNumber': record.get('acceptanceNumber'),
        'acceptanceTime': convert_datetime(record.get('acceptanceTime')),
        'deemedBoFlag': record.get('deemedBoFlag', False),
        'soFlag': record.get('soFlag', False),
        'amendmentFlag': record.get('amendmentFlag'),
        'storFlag': record.get('storFlag', False),
        'rrFlag': record.get('rrFlag', False),
        'nationalGridBmUnit': record.get('nationalGridBmUnit'),
        'bmUnit': record.get('bmUnit'),

        # Metadata fields (generated)
        '_dataset': 'BOALF',
        '_window_from_utc': time_from,
        '_window_to_utc': time_to,
        '_ingested_utc': ingested_utc,
        '_source_columns': None,  # Not tracking source columns in backfill
        '_source_api': 'ELEXON_BMRS_BACKFILL_GAP',
        '_hash_source_cols': None,  # Not computing hashes in backfill
        '_hash_key': None,
    }

    return transformed


def upload_to_bigquery(records):
    """Upload records to BigQuery, avoiding duplicates"""
    if not records:
        logging.info("⚠️  No records to upload")
        return 0

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

    client = bigquery.Client(project=BQ_PROJECT, location='US')

    # Transform records
    logging.info(f"🔄 Transforming {len(records)} records...")
    rows = [transform_record(r) for r in records]

    # Upload using load job
    logging.info(f"📤 Uploading to {table_id}...")

    try:
        # Create temp table
        temp_table_id = f"{table_id}_gap_temp"
        client.delete_table(temp_table_id, not_found_ok=True)

        # Load to temp table
        job_config = bigquery.LoadJobConfig(
            schema=BOALF_SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        job = client.load_table_from_json(rows, temp_table_id, job_config=job_config)
        job.result()

        logging.info(f"✅ Loaded {len(rows)} rows to temp table")

        # Merge only new records (avoid duplicates)
        logging.info("🔀 Merging new records (deduplicating)...")
        merge_query = f"""
        MERGE `{table_id}` T
        USING `{temp_table_id}` S
        ON T.acceptanceNumber = S.acceptanceNumber
           AND T.settlementDate = S.settlementDate
           AND T.bmUnit = S.bmUnit
        WHEN NOT MATCHED THEN
          INSERT ROW
        """

        merge_job = client.query(merge_query)
        result = merge_job.result()

        # Get count of inserted rows
        rows_inserted = merge_job.num_dml_affected_rows

        # Clean up temp table
        client.delete_table(temp_table_id, not_found_ok=True)

        logging.info(f"✅ Successfully inserted {rows_inserted} new rows to {table_id}")
        return rows_inserted

    except Exception as e:
        logging.error(f"❌ Error uploading to BigQuery: {e}")
        import traceback
        traceback.print_exc()
        return 0


def verify_gap_filled():
    """Verify the gap is now filled"""
    client = bigquery.Client(project=BQ_PROJECT, location='US')

    query = f"""
    SELECT
        DATE(settlementDate) as date,
        COUNT(*) as acceptances,
        COUNT(DISTINCT bmUnit) as units
    FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
    WHERE DATE(settlementDate) BETWEEN '{GAP_START}' AND '{GAP_END}'
    GROUP BY date
    ORDER BY date
    """

    logging.info("\n" + "="*70)
    logging.info("📊 Verification - Gap Coverage:")
    logging.info("="*70)

    try:
        df = client.query(query).to_dataframe()

        if len(df) == 0:
            logging.warning("⚠️  No data found in gap period!")
            return False

        print("\n" + df.to_string(index=False))

        total_acceptances = df['acceptances'].sum()
        avg_units = df['units'].mean()

        logging.info(f"\n📈 Gap Summary:")
        logging.info(f"   Total Acceptances: {total_acceptances:,}")
        logging.info(f"   Avg Units/Day: {avg_units:.0f}")
        logging.info(f"   Days Covered: {len(df)}")

        if len(df) >= 5:  # Should have at least 5 days (Oct 29-Nov 2)
            logging.info(f"✅ Gap successfully filled!")
            return True
        else:
            logging.warning(f"⚠️  Only {len(df)} days found, expected ~6 days")
            return False

    except Exception as e:
        logging.error(f"❌ Verification failed: {e}")
        return False


def main():
    """Main backfill function"""
    logging.info("="*70)
    logging.info(f"⚡ BOALF Gap Backfill - {GAP_START} to {GAP_END}")
    logging.info("="*70)
    logging.info(f"📍 Target: {BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")
    logging.info(f"📅 Gap Period: {GAP_START} to {GAP_END}")
    logging.info(f"⚠️  Chunking by day (API limit)")
    logging.info("")

    # Calculate date range
    start_dt = datetime.strptime(GAP_START, '%Y-%m-%d')
    end_dt = datetime.strptime(GAP_END, '%Y-%m-%d')
    total_days = (end_dt - start_dt).days + 1

    logging.info(f"📊 Processing {total_days} days...")

    total_records = 0
    total_inserted = 0

    # Process day by day
    current = start_dt
    day_count = 1

    while current <= end_dt:
        date_str = current.strftime('%Y-%m-%d')
        logging.info(f"\n[{day_count}/{total_days}] Processing {date_str}...")

        # Download single day
        records = download_boalf_data(date_str, date_str)

        if records:
            total_records += len(records)
            logging.info(f"   Downloaded: {len(records)} records")

            # Upload to BigQuery
            inserted = upload_to_bigquery(records)
            total_inserted += inserted
            logging.info(f"   Inserted: {inserted} new rows")
        else:
            logging.warning(f"   No data for {date_str}")

        # Move to next day
        current += timedelta(days=1)
        day_count += 1

    # Verify gap is filled
    logging.info("\n" + "="*70)
    logging.info("📊 Running verification...")
    verification_passed = verify_gap_filled()

    logging.info("\n" + "="*70)
    logging.info(f"🏁 Backfill Complete!")
    logging.info(f"   Days Processed: {total_days}")
    logging.info(f"   Downloaded: {total_records:,} records")
    logging.info(f"   Inserted: {total_inserted:,} new rows")
    logging.info(f"   Status: {'✅ SUCCESS' if verification_passed else '⚠️  PARTIAL'}")
    logging.info("="*70)

    return 0 if verification_passed else 1


if __name__ == '__main__':
    try:
        result = main()
        sys.exit(result)
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
