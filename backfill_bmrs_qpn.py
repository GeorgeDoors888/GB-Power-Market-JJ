#!/usr/bin/env python3
"""
Backfill bmrs_qpn (Quiescent Physical Notifications) - 51 days behind
Gap: Oct 29 - Dec 18, 2025 (51 days)
Endpoint: /datasets/QPN/stream (NOT /datasets/QPN)
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_qpn"

client = bigquery.Client(project=PROJECT_ID, location="US")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ENDPOINT = "/datasets/QPN/stream"  # CRITICAL: Use /stream not /datasets/QPN

def fetch_qpn_data(from_date, to_date):
    """
    Fetch QPN data for date range

    Args:
        from_date: datetime object
        to_date: datetime object

    Note: QPN requires /stream endpoint and uses 'from'/'to' parameters (not publishDateTime)
    """
    from_str = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_str = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    url = f"{BASE_URL}{ENDPOINT}"
    params = {
        'from': from_str,  # CRITICAL: 'from' not 'publishDateTimeFrom'
        'to': to_str,      # CRITICAL: 'to' not 'publishDateTimeTo'
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        # Stream endpoint returns JSON array directly (not wrapped in 'data' key)
        records = response.json()

        return records if isinstance(records, list) else []

    except Exception as e:
        print(f"  ⚠️ Error fetching {from_date.date()}: {e}")
        return None

def insert_to_bigquery(records):
    """Insert records to BigQuery table"""
    if not records:
        return 0

    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    try:
        errors = client.insert_rows_json(table_ref, records)
        if errors:
            print(f"    ❌ BigQuery errors: {errors}")
            return 0
        return len(records)
    except Exception as e:
        print(f"    ❌ Insert failed: {e}")
        return 0

def backfill_range(start_date, end_date):
    """
    Backfill QPN data in 7-day chunks

    Args:
        start_date: datetime object
        end_date: datetime object
    """
    total_uploaded = 0

    # Break into 7-day chunks to avoid timeouts
    chunk_days = 7
    current = start_date
    chunk_num = 1

    while current < end_date:
        chunk_end = min(current + timedelta(days=chunk_days), end_date)

        print(f"\n📦 Chunk {chunk_num}: {current.date()} to {chunk_end.date()}")

        records = fetch_qpn_data(current, chunk_end)

        if records:
            uploaded = insert_to_bigquery(records)
            total_uploaded += uploaded
            print(f"  ✅ {uploaded} records uploaded")
        else:
            print(f"  ⚠️ No data retrieved")

        current = chunk_end
        chunk_num += 1
        time.sleep(1)  # Rate limiting

    return total_uploaded

if __name__ == "__main__":
    print("=" * 60)
    print("BMRS QPN Backfill - Stream Endpoint")
    print("=" * 60)

    # Gap period: Oct 29 - Dec 18, 2025 (51 days)
    start = datetime(2025, 10, 29, 0, 0, 0)
    end = datetime(2025, 12, 18, 23, 59, 59)

    print(f"\nBackfilling: {start.date()} → {end.date()}")
    print(f"Endpoint: {BASE_URL}{ENDPOINT}")
    print(f"Target table: {PROJECT_ID}.{DATASET}.{TABLE}")

    total = backfill_range(start, end)

    print("\n" + "=" * 60)
    print(f"✅ Backfill complete")
    print(f"Total records uploaded: {total:,}")
    print("=" * 60)
