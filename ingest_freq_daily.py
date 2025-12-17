#!/usr/bin/env python3
"""
FREQ Historical Data Ingestion - Cron Compatible
Fetches yesterday's FREQ data from Elexon API and uploads to BigQuery
Run daily via cron to keep bmrs_freq table updated
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import json
import io
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

def clean_datetime(dt_str: str) -> str:
    """Remove 'Z' timezone suffix"""
    return dt_str.rstrip('Z') if dt_str else None

def ingest_freq_yesterday():
    """Fetch and upload yesterday's FREQ data"""
    # Get yesterday's date range
    yesterday = datetime.now() - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)

    print(f"Ingesting FREQ data for {start.date()}")

    try:
        # Fetch from API
        url = f"{API_BASE}/datasets/FREQ"
        params = {
            'from': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to': end.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'format': 'json'
        }

        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
        records = data.get('data', [])

        if not records:
            print(f"No data returned for {start.date()}")
            return 0

        print(f"Retrieved {len(records):,} records")

        # Clean datetimes
        for record in records:
            if 'measurementTime' in record:
                record['measurementTime'] = clean_datetime(record['measurementTime'])

        # Upload to BigQuery
        client = bigquery.Client(project=PROJECT_ID, location="US")
        table_id = f"{PROJECT_ID}.{DATASET}.bmrs_freq"

        json_data = '\n'.join([json.dumps(record) for record in records])
        json_file = io.StringIO(json_data)

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )

        job = client.load_table_from_file(json_file, table_id, job_config=job_config)
        job.result()  # Wait for completion

        print(f"✅ Uploaded {len(records):,} records to {table_id}")
        return len(records)

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    record_count = ingest_freq_yesterday()
    print(f"Ingestion complete: {record_count:,} records")
