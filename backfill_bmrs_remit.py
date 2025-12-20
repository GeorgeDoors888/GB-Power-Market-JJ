#!/usr/bin/env python3
"""
Backfill bmrs_remit (REMIT - Generator Outage Messages) - EMPTY TABLE
Table currently: 0 records
Endpoint: /datasets/REMIT (standard, not /stream)
Critical for: VLP constraint analysis, generator availability tracking
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_remit"

client = bigquery.Client(project=PROJECT_ID, location="US")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ENDPOINT = "/datasets/REMIT"  # Standard endpoint (NOT /stream)

def fetch_remit_data(from_date, to_date):
    """
    Fetch REMIT data for date range

    Args:
        from_date: datetime object
        to_date: datetime object

    Note: REMIT uses standard endpoint with publishDateTimeFrom/To parameters
    """
    from_str = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_str = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    url = f"{BASE_URL}{ENDPOINT}"
    params = {
        'publishDateTimeFrom': from_str,
        'publishDateTimeTo': to_str,
        'format': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        # Standard endpoint returns {"data": [...]}
        data = response.json()
        records = data.get('data', [])

        return records

    except Exception as e:
        print(f"  ⚠️ Error fetching {from_date.date()}: {e}")
        return []

def fix_datetime(dt_str):
    """Fix datetime format for BigQuery"""
    if dt_str and 'Z' in dt_str:
        return dt_str.replace('Z', '').replace('T', ' ')
    return dt_str

def prepare_record(record):
    """Prepare record for BigQuery insertion"""
    # Fix datetime fields
    datetime_fields = ['eventStartTime', 'eventEndTime', 'publishDateTime', 'createdTime', 'lastModifiedTime']
    for field in datetime_fields:
        if field in record and record[field]:
            record[field] = fix_datetime(record[field])

    # Add ingestion timestamp
    record['ingestion_timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    return record

def backfill_date_range(start_date, end_date):
    """
    Backfill REMIT data in chunks

    Args:
        start_date: datetime object
        end_date: datetime object
    """
    print(f"🔄 Backfilling REMIT: {start_date.date()} to {end_date.date()}")

    # Process in 7-day chunks
    chunk_days = 7
    current_date = start_date
    chunk_num = 1
    total_records = 0
    total_errors = 0

    while current_date < end_date:
        chunk_end = min(current_date + timedelta(days=chunk_days), end_date)

        print(f"\n[Chunk {chunk_num}] {current_date.date()} to {chunk_end.date()}")

        # Fetch data
        records = fetch_remit_data(current_date, chunk_end)

        if not records:
            print(f"  ℹ️ No records for this period")
            current_date = chunk_end
            chunk_num += 1
            continue

        print(f"  ✅ Fetched {len(records)} records")

        # Prepare records
        prepared_records = [prepare_record(record.copy()) for record in records]

        # Upload to BigQuery
        table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"
        errors = client.insert_rows_json(table_ref, prepared_records)

        if errors:
            print(f"  ❌ Errors uploading to BigQuery:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"     {error}")
            total_errors += len(errors)
        else:
            print(f"  ✅ Uploaded {len(prepared_records)} records to BigQuery")
            total_records += len(prepared_records)

        current_date = chunk_end
        chunk_num += 1

        # Rate limiting
        time.sleep(2)

    print(f"\n{'='*60}")
    print(f"✅ Backfill complete!")
    print(f"Total records uploaded: {total_records:,}")
    print(f"Total errors: {total_errors}")
    print(f"{'='*60}")

if __name__ == "__main__":
    import sys

    # Default: backfill last 90 days (REMIT is typically recent outage data)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)

    # Allow custom date range
    if len(sys.argv) == 3:
        start_date = datetime.strptime(sys.argv[1], '%Y-%m-%d')
        end_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')
    elif len(sys.argv) == 2:
        # Single argument = number of days back
        days_back = int(sys.argv[1])
        start_date = end_date - timedelta(days=days_back)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║         REMIT Backfill - Generator Outages              ║
╚══════════════════════════════════════════════════════════╝

Dataset: {TABLE}
Period: {start_date.date()} → {end_date.date()}
Days: {(end_date - start_date).days}

Starting backfill...
""")

    backfill_date_range(start_date, end_date)

    # Verify
    print("\n📊 Verifying table status...")
    query = f"""
    SELECT
        MIN(CAST(publishDateTime AS DATE)) as earliest_date,
        MAX(CAST(publishDateTime AS DATE)) as latest_date,
        COUNT(*) as total_records,
        COUNT(DISTINCT CAST(publishDateTime AS DATE)) as unique_days,
        COUNT(DISTINCT assetId) as unique_assets
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    """

    result = client.query(query).to_dataframe()

    print(f"\n✅ Table Status:")
    print(f"   Date range: {result.earliest_date[0]} → {result.latest_date[0]}")
    print(f"   Total records: {result.total_records[0]:,}")
    print(f"   Unique days: {result.unique_days[0]:,}")
    print(f"   Unique assets: {result.unique_assets[0]:,}")
