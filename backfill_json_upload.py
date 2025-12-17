#!/usr/bin/env python3
"""
Simplified Historical Data Backfill using JSON Upload
Fixes datetime parsing issues by using BigQuery's native JSON loader
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import json
import time
import io

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

client = bigquery.Client(project=PROJECT_ID, location="US")

def clean_datetime(dt_str: str) -> str:
    """Remove 'Z' timezone suffix for BigQuery DATETIME compatibility"""
    return dt_str.rstrip('Z') if dt_str else None

def fetch_and_upload_freq(from_date: datetime, to_date: datetime) -> bool:
    """Fetch FREQ data and upload directly as JSON"""
    url = f"{API_BASE}/datasets/FREQ"
    params = {
        'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }

    print(f"  Fetching FREQ: {from_date.date()} to {to_date.date()}")

    try:
        response = requests.get(url, params=params, timeout=120)

        if response.status_code != 200:
            error_detail = response.text[:300] if response.text else "No error details"
            print(f"    ❌ HTTP {response.status_code}: {error_detail}")
            return False

        data = response.json()
        records = data.get('data', [])

        if not records:
            print(f"    No data returned")
            return True

        # Clean datetime fields
        for record in records:
            if 'measurementTime' in record:
                record['measurementTime'] = clean_datetime(record['measurementTime'])

        # Create newline-delimited JSON
        json_data = '\n'.join([json.dumps(record) for record in records])
        json_file = io.StringIO(json_data)

        # Upload to BigQuery
        table_id = f"{PROJECT_ID}.{DATASET}.bmrs_freq"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )

        job = client.load_table_from_file(json_file, table_id, job_config=job_config)
        job.result()  # Wait for completion

        print(f"    ✅ Uploaded {len(records):,} records")
        return True

    except Exception as e:
        print(f"    ❌ Error: {str(e)[:200]}")
        return False

def fetch_and_upload_mid(from_date: datetime, to_date: datetime) -> bool:
    """Fetch MID data and upload directly as JSON"""
    url = f"{API_BASE}/datasets/MID"
    params = {
        'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }

    print(f"  Fetching MID: {from_date.date()} to {to_date.date()}")

    try:
        response = requests.get(url, params=params, timeout=120)

        if response.status_code != 200:
            error_detail = response.text[:300] if response.text else "No error details"
            print(f"    ❌ HTTP {response.status_code}: {error_detail}")
            return False

        data = response.json()
        records = data.get('data', [])

        if not records:
            print(f"    No data returned")
            return True

        # Clean datetime fields
        for record in records:
            for field in ['settlementDate', 'publishTime']:
                if field in record:
                    record[field] = clean_datetime(record[field])

        # Create newline-delimited JSON
        json_data = '\n'.join([json.dumps(record) for record in records])
        json_file = io.StringIO(json_data)

        # Upload to BigQuery
        table_id = f"{PROJECT_ID}.{DATASET}.bmrs_mid"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )

        job = client.load_table_from_file(json_file, table_id, job_config=job_config)
        job.result()

        print(f"    ✅ Uploaded {len(records):,} records")
        return True

    except Exception as e:
        print(f"    ❌ Error: {str(e)[:200]}")
        return False

def fetch_and_upload_bod(from_date: datetime, to_date: datetime) -> bool:
    """Fetch BOD data and upload directly as JSON"""
    url = f"{API_BASE}/datasets/BOD"
    params = {
        'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }

    print(f"  Fetching BOD: {from_date.date()} to {to_date.date()}")

    try:
        response = requests.get(url, params=params, timeout=120)

        if response.status_code != 200:
            error_detail = response.text[:300] if response.text else "No error details"
            print(f"    ❌ HTTP {response.status_code}: {error_detail}")
            return False

        data = response.json()
        records = data.get('data', [])

        if not records:
            print(f"    No data returned")
            return True

        # Clean datetime fields
        for record in records:
            for field in ['settlementDate', 'timeFrom', 'timeTo', 'publishTime']:
                if field in record:
                    record[field] = clean_datetime(record[field])

        # Create newline-delimited JSON
        json_data = '\n'.join([json.dumps(record) for record in records])
        json_file = io.StringIO(json_data)

        # Upload to BigQuery
        table_id = f"{PROJECT_ID}.{DATASET}.bmrs_bod"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )

        job = client.load_table_from_file(json_file, table_id, job_config=job_config)
        job.result()

        print(f"    ✅ Uploaded {len(records):,} records")
        return True

    except Exception as e:
        print(f"    ❌ Error: {str(e)[:200]}")
        return False

def backfill_freq(start: datetime, end: datetime, batch_days: int = 7):
    """Backfill FREQ data"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_freq")
    print("="*80)

    current = start
    success = 0
    failed = 0

    while current < end:
        batch_end = min(current + timedelta(days=batch_days), end)

        if fetch_and_upload_freq(current, batch_end):
            success += 1
        else:
            failed += 1

        current = batch_end
        time.sleep(1)  # Rate limiting

    print(f"\n✅ FREQ: {success} batches succeeded, {failed} failed")

def backfill_mid(start: datetime, end: datetime, batch_days: int = 7):
    """Backfill MID data"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_mid")
    print("="*80)

    current = start
    success = 0
    failed = 0

    while current < end:
        batch_end = min(current + timedelta(days=batch_days), end)

        if fetch_and_upload_mid(current, batch_end):
            success += 1
        else:
            failed += 1

        current = batch_end
        time.sleep(1)

    print(f"\n✅ MID: {success} batches succeeded, {failed} failed")

def backfill_bod(start: datetime, end: datetime, batch_hours: int = 1):
    """Backfill BOD data (hourly batches - API limit: 1 hour max)"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_bod (hourly batches - API max window: 1 hour)")
    print("="*80)

    current = start
    success = 0
    failed = 0

    while current < end:
        batch_end = min(current + timedelta(hours=batch_hours), end)

        if fetch_and_upload_bod(current, batch_end):
            success += 1
        else:
            failed += 1

        current = batch_end
        time.sleep(0.5)  # Rate limiting (2 requests/sec)

    print(f"\n✅ BOD: {success} batches succeeded, {failed} failed")

if __name__ == "__main__":
    print("GB Power Market - Historical Backfill (JSON Upload Method)")
    print("="*80)

    # FREQ: 2022-01-01 to 2025-10-27
    print("\n[1/3] FREQ: 2022-01-01 to 2025-10-27")
    backfill_freq(datetime(2022, 1, 1), datetime(2025, 10, 28))

    # MID: 2025-10-31 to 2025-12-17
    print("\n[2/3] MID: 2025-10-31 to 2025-12-17")
    backfill_mid(datetime(2025, 10, 31), datetime(2025, 12, 18))

    # BOD: 2025-10-29 to 2025-12-17
    print("\n[3/3] BOD: 2025-10-29 to 2025-12-17")
    backfill_bod(datetime(2025, 10, 29), datetime(2025, 12, 18))

    print("\n" + "="*80)
    print("✅ BACKFILL COMPLETE!")
    print("="*80)
