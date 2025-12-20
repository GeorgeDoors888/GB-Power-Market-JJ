#!/usr/bin/env python3
"""
Backfill Missing Data - Dec 19-20, 2025
Uses Elexon API to fetch and upload missing BOALF, FREQ data
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET_ID = 'uk_energy_prod'
API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'

def backfill_boalf(client, start_date, end_date):
    """Backfill BOALF (Balancing Acceptances) via API"""
    logger.info(f"Backfilling BOALF from {start_date} to {end_date}")

    current = start_date
    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        logger.info(f"Fetching BOALF for {date_str}")

        # BOALF endpoint: /datasets/BOALF
        url = f"{API_BASE}/datasets/BOALF"
        params = {
            'from': f"{date_str}T00:00:00Z",
            'to': f"{date_str}T23:59:59Z",
            'format': 'json',
        }

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and data['data']:
                records = data['data']
                logger.info(f"  Found {len(records)} BOALF records")

                # Upload to BigQuery bmrs_boalf_iris table
                table_id = f"{PROJECT_ID}.{DATASET_ID}.bmrs_boalf_iris"

                # Add ingested timestamp
                for record in records:
                    record['ingested_utc'] = datetime.utcnow().isoformat()

                errors = client.insert_rows_json(table_id, records)
                if errors:
                    logger.error(f"  Errors inserting BOALF: {errors}")
                else:
                    logger.info(f"  ✅ Uploaded {len(records)} BOALF records")
            else:
                logger.warning(f"  No BOALF data for {date_str}")

        except Exception as e:
            logger.error(f"  Error fetching BOALF for {date_str}: {e}")

        current += timedelta(days=1)
        time.sleep(2)  # Rate limiting

def backfill_freq(client, start_date, end_date):
    """Backfill FREQ (System Frequency) via API"""
    logger.info(f"Backfilling FREQ from {start_date} to {end_date}")

    current = start_date
    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        logger.info(f"Fetching FREQ for {date_str}")

        # FREQ endpoint: /datasets/FREQ
        url = f"{API_BASE}/datasets/FREQ"
        params = {
            'from': f"{date_str}T00:00:00Z",
            'to': f"{date_str}T23:59:59Z",
            'format': 'json',
        }

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and data['data']:
                records = data['data']
                logger.info(f"  Found {len(records)} FREQ records")

                # Upload to BigQuery bmrs_freq_iris table
                table_id = f"{PROJECT_ID}.{DATASET_ID}.bmrs_freq_iris"

                # Add ingested timestamp
                for record in records:
                    record['ingested_utc'] = datetime.utcnow().isoformat()

                errors = client.insert_rows_json(table_id, records)
                if errors:
                    logger.error(f"  Errors inserting FREQ: {errors}")
                else:
                    logger.info(f"  ✅ Uploaded {len(records)} FREQ records")
            else:
                logger.warning(f"  No FREQ data for {date_str}")

        except Exception as e:
            logger.error(f"  Error fetching FREQ for {date_str}: {e}")

        current += timedelta(days=1)
        time.sleep(2)  # Rate limiting

def backfill_fuelinst(client, start_date, end_date):
    """Backfill FUELINST (Generation) if any gaps"""
    logger.info(f"Backfilling FUELINST from {start_date} to {end_date}")

    current = start_date
    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        logger.info(f"Fetching FUELINST for {date_str}")

        # FUELINST endpoint: /datasets/FUELINST
        url = f"{API_BASE}/datasets/FUELINST"
        params = {
            'from': f"{date_str}T00:00:00Z",
            'to': f"{date_str}T23:59:59Z",
            'format': 'json',
        }

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and data['data']:
                records = data['data']
                logger.info(f"  Found {len(records)} FUELINST records")

                # Upload to BigQuery bmrs_fuelinst_iris table
                table_id = f"{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_iris"

                # Add ingested timestamp
                for record in records:
                    record['ingested_utc'] = datetime.utcnow().isoformat()

                errors = client.insert_rows_json(table_id, records)
                if errors:
                    logger.error(f"  Errors inserting FUELINST: {errors}")
                else:
                    logger.info(f"  ✅ Uploaded {len(records)} FUELINST records")
            else:
                logger.warning(f"  No FUELINST data for {date_str}")

        except Exception as e:
            logger.error(f"  Error fetching FUELINST for {date_str}: {e}")

        current += timedelta(days=1)
        time.sleep(2)  # Rate limiting

def main():
    """Main backfill process"""
    client = bigquery.Client(project=PROJECT_ID, location='US')

    # Missing dates: Dec 19-20, 2025
    start_date = datetime(2025, 12, 19)
    end_date = datetime(2025, 12, 20)

    logger.info("=" * 70)
    logger.info("BACKFILL MISSING DATA - Dec 19-20, 2025")
    logger.info("=" * 70)

    # Backfill each dataset
    backfill_boalf(client, start_date, end_date)
    backfill_freq(client, start_date, end_date)
    backfill_fuelinst(client, start_date, end_date)

    logger.info("=" * 70)
    logger.info("✅ BACKFILL COMPLETE")
    logger.info("=" * 70)

if __name__ == '__main__':
    main()
