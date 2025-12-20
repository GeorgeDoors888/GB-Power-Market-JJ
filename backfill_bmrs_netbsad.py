#!/usr/bin/env python3
"""
Backfill bmrs_netbsad (Net Balancing Services Adjustment Data) - 51 days behind
Gap: Oct 29 - Dec 18, 2025 (51 days)
Endpoint: /datasets/NETBSAD (NOT /balancing/netbsad)
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_netbsad"

client = bigquery.Client(project=PROJECT_ID, location="US")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ENDPOINT = "/datasets/NETBSAD/stream"  # CRITICAL: Use /stream not /datasets/NETBSAD

def fetch_netbsad_data(from_date, to_date):
    """
    Fetch NETBSAD data for date range

    Args:
        from_date: datetime object
        to_date: datetime object

    Note: NETBSAD requires /stream endpoint and uses 'from'/'to' parameters (not publishDateTime)
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
        return []

def fix_datetime(dt_str):
    """Fix datetime format for BigQuery"""
    if dt_str and 'Z' in dt_str:
        return dt_str.replace('Z', '').replace('T', ' ')
    return dt_str

def backfill_date_range(start_date, end_date):
    """Backfill NETBSAD data for date range (using load jobs for large datasets)"""

    from_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"Fetching data from {start_date.date()} to {end_date.date()}...")

    # Fetch all data for range
    records = fetch_netbsad_data(start_date, to_date=end_date)

    if not records:
        print(f"  ⚠️ No data returned")
        return 0

    print(f"  ✅ Fetched {len(records):,} records")

    # Add metadata fields
    ingested_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    for record in records:
        # Fix datetime fields
        for field in ['settlementDate', 'publishTime']:
            if field in record:
                record[field] = fix_datetime(record.get(field))

        # Add metadata
        record['_dataset'] = 'NETBSAD'
        record['_ingested_utc'] = ingested_utc
        record['_source_api'] = 'NETBSAD'

    # Use load job for large datasets (better than streaming insert)
    print(f"  Uploading via load job...")

    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=False,  # Use existing schema
    )

    job = client.load_table_from_json(
        records,
        table_ref,
        job_config=job_config
    )

    job.result()  # Wait for completion

    if job.errors:
        print(f"  ❌ Upload errors: {job.errors[:3]}")
        return 0
    else:
        print(f"  ✅ Uploaded {len(records):,} records")
        return len(records)

def main():
    """Main backfill execution"""

    # Gap: Oct 29 - Dec 18, 2025 (51 days)
    start_date = datetime(2025, 10, 29)
    end_date = datetime(2025, 12, 18)

    days = (end_date - start_date).days + 1

    print("=" * 80)
    print("bmrs_netbsad Backfill - Oct 29 - Dec 18, 2025")
    print(f"Target: {days} days")
    print("=" * 80)
    print()

    # Process in weekly chunks to avoid timeouts
    current = start_date
    total_records = 0
    chunk_num = 1

    while current <= end_date:
        chunk_end = min(current + timedelta(days=6), end_date)  # 7-day chunks

        print(f"[Chunk {chunk_num}] {current.date()} to {chunk_end.date()}")

        records = backfill_date_range(current, chunk_end)
        total_records += records

        print()

        current = chunk_end + timedelta(days=1)
        chunk_num += 1
        time.sleep(1)  # Rate limiting between chunks

    print("=" * 80)
    print(f"✅ Backfill Complete!")
    print(f"   Total records uploaded: {total_records:,}")
    print(f"   Target days: {days}")
    print("=" * 80)

if __name__ == "__main__":
    main()
