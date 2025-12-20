#!/usr/bin/env python3
"""
Backfill bmrs_mid (Market Index Data) - 24 missing days
Gap: Four 6-day blocks in 2024 (likely weekend/API maintenance outages)
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_mid"

client = bigquery.Client(project=PROJECT_ID, location="US")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ENDPOINT = "/datasets/MID"  # Market Index Data

def fetch_mid_data(from_date, to_date):
    """
    Fetch Market Index Data for date range

    Args:
        from_date: datetime object
        to_date: datetime object
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
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

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

def transform_record(record):
    """Transform API record to BigQuery schema"""
    ingested_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    return {
        # Core MID fields (from API)
        'dataset': record.get('dataset', 'MID'),
        'startTime': fix_datetime(record.get('startTime')),
        'dataProvider': record.get('dataProvider', 'Elexon'),
        'settlementDate': fix_datetime(record.get('settlementDate')),
        'settlementPeriod': record.get('settlementPeriod'),
        'price': record.get('price'),
        'volume': record.get('volume'),

        # Metadata fields (underscore prefix)
        '_dataset': 'MID',
        '_window_from_utc': fix_datetime(record.get('startTime', '')),
        '_window_to_utc': fix_datetime(record.get('startTime', '')),
        '_ingested_utc': ingested_utc,
        '_source_columns': 'settlementDate,settlementPeriod,price,volume',
        '_source_api': 'MID',
        '_hash_source_cols': '',
        '_hash_key': f"{record.get('settlementDate', '')}_{record.get('settlementPeriod', '')}"
    }

def backfill_date_range(start_date, end_date):
    """Backfill MID data for date range"""
    current = start_date
    total_uploaded = 0

    while current <= end_date:
        print(f"Processing {current.date()}...")

        # Fetch full day (00:00 to 23:59)
        from_dt = current.replace(hour=0, minute=0, second=0)
        to_dt = current.replace(hour=23, minute=59, second=59)

        records = fetch_mid_data(from_dt, to_dt)

        if records:
            # Transform records
            transformed = [transform_record(r) for r in records]

            # Upload to BigQuery
            table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"
            errors = client.insert_rows_json(table_ref, transformed)

            if errors:
                print(f"  ❌ Upload error: {errors[:3]}")  # Show first 3 errors
            else:
                print(f"  ✅ Uploaded {len(transformed)} records")
                total_uploaded += len(transformed)
        else:
            print(f"  ⚠️ No data returned for {current.date()}")

        current += timedelta(days=1)
        time.sleep(0.5)  # Rate limiting

    return total_uploaded

def main():
    """Main backfill execution"""

    # Missing date ranges (from earlier analysis)
    gaps = [
        (datetime(2024, 4, 16), datetime(2024, 4, 21)),   # 6 days
        (datetime(2024, 7, 16), datetime(2024, 7, 21)),   # 6 days
        (datetime(2024, 9, 10), datetime(2024, 9, 15)),   # 6 days
        (datetime(2024, 10, 8), datetime(2024, 10, 13)),  # 6 days
    ]

    print("=" * 80)
    print("bmrs_mid Backfill - Missing Date Ranges")
    print("=" * 80)
    print()

    total_records = 0

    for idx, (start, end) in enumerate(gaps, 1):
        days = (end - start).days + 1
        print(f"[{idx}/{len(gaps)}] Gap: {start.date()} to {end.date()} ({days} days)")
        print()

        records = backfill_date_range(start, end)
        total_records += records

        print()

    print("=" * 80)
    print(f"✅ Backfill Complete!")
    print(f"   Total records uploaded: {total_records}")
    print("=" * 80)

if __name__ == "__main__":
    main()
