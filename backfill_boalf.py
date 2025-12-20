#!/usr/bin/env python3
"""
Backfill BOALF (Balancing Acceptances) data from Elexon API to BigQuery

Gap: Nov 5, 2025 - Dec 18, 2025 (44 days)
Critical for VLP revenue analysis (used in boalf_with_prices table)
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_boalf"

client = bigquery.Client(project=PROJECT_ID, location="US")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ENDPOINT = "/datasets/BOALF"

def fetch_boalf(from_dt, to_dt):
    """
    Fetch BOALF data for date range

    Args:
        from_dt: datetime object
        to_dt: datetime object
    """
    url = f"{BASE_URL}{ENDPOINT}"

    params = {
        'from': from_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }

    response = requests.get(url, params=params, timeout=90)
    response.raise_for_status()

    data = response.json()
    return data.get('data', [])

def upload_to_bigquery(records):
    """Upload records to BigQuery using load job (handles large payloads)"""
    if not records:
        return

    # Add ingestion timestamp
    now_ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    for row in records:
        row['_ingested_utc'] = now_ts  # Note: underscore prefix!

        # Convert datetime fields (keep as strings for bmrs_boalf)
        # Table has STRING types for timeFrom/timeTo, DATETIME for acceptanceTime

    # Use load job instead of insert_rows_json (avoids 413 payload limit)
    import io
    import json

    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    # Create JSONL string
    jsonl_data = '\n'.join(json.dumps(row) for row in records)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    try:
        load_job = client.load_table_from_file(
            io.BytesIO(jsonl_data.encode('utf-8')),
            table_ref,
            job_config=job_config
        )
        load_job.result()  # Wait for completion
        return True
    except Exception as e:
        print(f"  ❌ Load job error: {str(e)[:100]}")
        return False

def backfill_date_range(start_date, end_date, chunk_days=1):
    """
    Backfill BOALF data for date range

    Args:
        start_date: datetime.date object
        end_date: datetime.date object
        chunk_days: Number of days per chunk (default 1)
    """
    current = datetime.combine(start_date, datetime.min.time())
    end = datetime.combine(end_date, datetime.max.time())

    total_records = 0
    total_days = (end_date - start_date).days + 1

    print(f"Starting BOALF backfill: {start_date} to {end_date} ({total_days} days)")
    print(f"Target: {PROJECT_ID}.{DATASET}.{TABLE}")
    print(f"Chunk size: {chunk_days} day(s)")
    print("=" * 80)

    day_count = 0

    while current < end:
        chunk_end = min(current + timedelta(days=chunk_days), end)
        date_str = current.strftime('%Y-%m-%d')

        try:
            print(f"[{day_count+1}/{total_days}] Fetching {date_str}...", end=' ')

            # Fetch data
            records = fetch_boalf(current, chunk_end)

            print(f"{len(records)} records", end=' ')

            # Upload to BigQuery
            if records:
                success = upload_to_bigquery(records)
                if success:
                    print("✅")
                    total_records += len(records)
                else:
                    print("❌ Upload failed")
            else:
                print("(no data)")

            # Rate limiting
            time.sleep(0.5)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠️  404 (no data)")
            else:
                print(f"❌ HTTP {e.response.status_code}: {str(e)[:60]}")
        except Exception as e:
            print(f"❌ Error: {str(e)[:80]}")

        current = chunk_end
        day_count += chunk_days

    print("=" * 80)
    print(f"✅ Backfill complete!")
    print(f"Total records uploaded: {total_records:,}")
    print(f"Date range: {start_date} to {end_date}")

if __name__ == "__main__":
    # Backfill the 44-day gap
    start = datetime(2025, 11, 5).date()
    end = datetime(2025, 12, 18).date()

    backfill_date_range(start, end, chunk_days=1)
