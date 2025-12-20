#!/usr/bin/env python3
"""
Backfill large datasets with gaps from late October to December 2025:
- NETBSAD: Oct 29 - Dec 18 (51 days)
- PN: Oct 29 - Dec 18 (51 days, ~173M rows normally)
- QPN: Oct 29 - Dec 18 (51 days, ~153M rows normally)
- INDGEN: Oct 31 - Dec 18 (49 days)
- INDDEM: Oct 31 - Dec 18 (49 days)

Uses proven BOALF backfill pattern with pagination support.
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT_ID, location="US")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

# Dataset configurations
DATASET_CONFIGS = {
    'NETBSAD': {
        'table': 'bmrs_netbsad',
        'start_date': datetime(2025, 10, 29).date(),
        'end_date': datetime(2025, 12, 18).date(),
        'api_name': 'NETBSAD',
        'chunk_size': '1d',  # Daily chunks
    },
    'PN': {
        'table': 'bmrs_pn',
        'start_date': datetime(2025, 10, 29).date(),
        'end_date': datetime(2025, 12, 18).date(),
        'api_name': 'PN',
        'chunk_size': '1d',
    },
    'QPN': {
        'table': 'bmrs_qpn',
        'start_date': datetime(2025, 10, 29).date(),
        'end_date': datetime(2025, 12, 18).date(),
        'api_name': 'QPN',
        'chunk_size': '1d',
    },
    'INDGEN': {
        'table': 'bmrs_indgen',
        'start_date': datetime(2025, 10, 31).date(),
        'end_date': datetime(2025, 12, 18).date(),
        'api_name': 'INDGEN',
        'chunk_size': '1d',
    },
    'INDDEM': {
        'table': 'bmrs_inddem',
        'start_date': datetime(2025, 10, 31).date(),
        'end_date': datetime(2025, 12, 18).date(),
        'api_name': 'INDDEM',
        'chunk_size': '1d',
    },
}

def fix_datetime(dt_str):
    """Fix datetime format for BigQuery (remove Z, replace T with space)"""
    if dt_str and 'Z' in dt_str:
        return dt_str.replace('Z', '').replace('T', ' ')
    return dt_str

def download_dataset(api_name, from_date, to_date):
    """
    Download dataset from Elexon API with pagination

    Args:
        api_name: API dataset name (e.g., 'NETBSAD')
        from_date: datetime.date
        to_date: datetime.date

    Returns:
        List of records
    """
    all_records = []

    # Use publishDateTime for most datasets (better availability)
    from_dt = datetime.combine(from_date, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
    to_dt = datetime.combine(to_date, datetime.max.time()).strftime('%Y-%m-%dT%H:%M:%SZ')

    url = f"{BASE_URL}/{api_name}?publishDateTimeFrom={from_dt}&publishDateTimeTo={to_dt}&format=json"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        data = response.json()
        records = data.get('data', [])

        return records

    except Exception as e:
        print(f"  ❌ Error downloading {api_name}: {e}")
        return []

def transform_record(record, dataset_name):
    """Transform API record to BigQuery schema (fix datetime fields)"""

    # Create a copy to avoid modifying original
    transformed = dict(record)

    # Fix all datetime fields
    for key, value in transformed.items():
        if isinstance(value, str) and ('T' in value or 'Z' in value):
            transformed[key] = fix_datetime(value)

    # Add ingestion timestamp
    transformed['_ingested_utc'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    return transformed

def get_table_schema(table_name):
    """Get existing table schema from BigQuery"""
    try:
        table = client.get_table(f"{PROJECT_ID}.{DATASET}.{table_name}")
        return table.schema
    except Exception as e:
        print(f"  ⚠️ Could not get schema for {table_name}: {e}")
        return None

def upload_to_bigquery(records, table_name):
    """Upload records to BigQuery using load job (handles large datasets)"""

    if not records:
        print(f"  No records to upload for {table_name}")
        return 0

    table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"

    # Get schema
    schema = get_table_schema(table_name)
    if not schema:
        print(f"  ❌ Cannot upload - schema not found")
        return 0

    # Use load job for large datasets (avoids 413 errors)
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    try:
        job = client.load_table_from_json(records, table_ref, job_config=job_config)
        job.result()  # Wait for completion

        return len(records)
    except Exception as e:
        print(f"  ⚠️ Upload failed: {e}")
        return 0

def backfill_dataset(dataset_key):
    """Backfill a single dataset"""

    config = DATASET_CONFIGS[dataset_key]

    print(f"\n{'=' * 70}")
    print(f"Backfilling {dataset_key} ({config['table']})")
    print(f"Period: {config['start_date']} to {config['end_date']}")
    print(f"{'=' * 70}\n")

    current_date = config['start_date']
    end_date = config['end_date']

    total_uploaded = 0
    total_days = (end_date - current_date).days + 1
    day_count = 0

    while current_date <= end_date:
        day_count += 1
        print(f"[{day_count}/{total_days}] Processing {current_date}...")

        # Download data for this day
        records = download_dataset(config['api_name'], current_date, current_date)

        if records:
            # Transform records
            transformed = [transform_record(r, dataset_key) for r in records]

            # Upload to BigQuery
            uploaded = upload_to_bigquery(transformed, config['table'])
            total_uploaded += uploaded

            print(f"  ✅ Uploaded {uploaded:,} records")
        else:
            print(f"  ⚠️ No data available")

        # Rate limiting
        time.sleep(0.5)

        current_date += timedelta(days=1)

    print(f"\n{'=' * 70}")
    print(f"✅ {dataset_key} Complete: {total_uploaded:,} records uploaded")
    print(f"{'=' * 70}\n")

    return total_uploaded

def main():
    """Main backfill execution"""

    # Allow user to specify which dataset to backfill
    if len(sys.argv) > 1:
        dataset_key = sys.argv[1].upper()
        if dataset_key not in DATASET_CONFIGS:
            print(f"❌ Unknown dataset: {dataset_key}")
            print(f"Available: {', '.join(DATASET_CONFIGS.keys())}")
            sys.exit(1)

        datasets_to_process = [dataset_key]
    else:
        # Process all datasets
        datasets_to_process = list(DATASET_CONFIGS.keys())

    print(f"\n{'*' * 70}")
    print(f"LARGE DATASET BACKFILL")
    print(f"Datasets: {', '.join(datasets_to_process)}")
    print(f"{'*' * 70}\n")

    grand_total = 0

    for dataset_key in datasets_to_process:
        total = backfill_dataset(dataset_key)
        grand_total += total

    print(f"\n{'*' * 70}")
    print(f"🎉 ALL BACKFILLS COMPLETE")
    print(f"Total records uploaded: {grand_total:,}")
    print(f"{'*' * 70}\n")

if __name__ == "__main__":
    main()
