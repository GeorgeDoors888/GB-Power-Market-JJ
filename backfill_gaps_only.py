#!/usr/bin/env python3
"""
Targeted Backfill for Historical Gaps
Only fills the missing data periods:
- MID: Oct 31 - Dec 17, 2025
- BOD: Oct 29 - Dec 17, 2025
(FREQ is already being processed by the other script)
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
            print(f"    ⚠️  No data returned")
            return True

        # Clean datetime fields
        for record in records:
            for field in ['settlementDate', 'publishTime', 'startTime']:
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
    """Fetch BOD data and upload directly as JSON (API max: 1 hour)"""
    url = f"{API_BASE}/datasets/BOD"
    params = {
        'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }

    print(f"  Fetching BOD: {from_date.strftime('%Y-%m-%d %H:%M')} to {to_date.strftime('%Y-%m-%d %H:%M')}")

    try:
        response = requests.get(url, params=params, timeout=120)

        if response.status_code != 200:
            error_detail = response.text[:300] if response.text else "No error details"
            print(f"    ❌ HTTP {response.status_code}: {error_detail}")
            return False

        data = response.json()
        records = data.get('data', [])

        if not records:
            print(f"    ⚠️  No data returned")
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

def backfill_mid_gap():
    """Backfill MID: Oct 31 - Dec 17, 2025 (7-day batches)"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_mid GAP (Oct 31 - Dec 17, 2025)")
    print("="*80)

    start = datetime(2025, 10, 31)
    end = datetime(2025, 12, 18)  # Exclusive
    batch_days = 7

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
        time.sleep(1)  # Rate limiting

    print(f"\n✅ MID Gap Fill: {success} batches succeeded, {failed} failed")

def backfill_bod_gap():
    """Backfill BOD: Oct 29 - Dec 17, 2025 (hourly batches - API limit)"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_bod GAP (Oct 29 - Dec 17, 2025)")
    print("API Restriction: 1-hour maximum window per request")
    print("="*80)

    start = datetime(2025, 10, 29)
    end = datetime(2025, 12, 18)

    current = start
    success = 0
    failed = 0
    total_hours = int((end - start).total_seconds() / 3600)

    print(f"Total hours to process: {total_hours:,}")
    print(f"Estimated time: ~{total_hours/2:.0f} minutes (0.5s/request + API time)\n")

    while current < end:
        batch_end = min(current + timedelta(hours=1), end)

        if fetch_and_upload_bod(current, batch_end):
            success += 1
        else:
            failed += 1

        # Progress indicator every 24 hours
        if success % 24 == 0 and success > 0:
            progress_pct = (success / total_hours) * 100
            print(f"    📊 Progress: {success}/{total_hours} hours ({progress_pct:.1f}%)")

        current = batch_end
        time.sleep(0.5)  # Rate limiting (2 requests/sec)

    print(f"\n✅ BOD Gap Fill: {success} batches succeeded, {failed} failed")

if __name__ == "__main__":
    print("="*80)
    print("GB POWER MARKET - TARGETED GAP BACKFILL")
    print("="*80)
    print("\nFilling historical data gaps:")
    print("  - MID: Oct 31 → Dec 17, 2025")
    print("  - BOD: Oct 29 → Dec 17, 2025 (hourly batches)")
    print("\n" + "="*80)

    # MID first (faster)
    backfill_mid_gap()

    # BOD second (will take ~25 minutes for 50 days * 24 hours)
    backfill_bod_gap()

    print("\n" + "="*80)
    print("✅ GAP BACKFILL COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Check data: SELECT COUNT(*), MAX(DATE(settlementDate)) FROM bmrs_mid/bmrs_bod")
    print("  2. Set up daily cron jobs for ongoing ingestion")
    print("  3. Use IRIS tables (bmrs_*_iris) for most recent data")
