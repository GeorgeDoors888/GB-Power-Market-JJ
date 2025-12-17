#!/usr/bin/env python3
"""
Simple backfill for Dec 15-17, 2025
Fetches FUELINST, FREQ, BOALF, MID from Elexon BMRS API
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import time

# Config
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
START_DATE = '2025-12-15'
END_DATE = '2025-12-17'
TIMEOUT = (10, 90)

# Datasets to backfill with their API endpoints
DATASETS = {
    'FUELINST': {
        'url_template': 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST',
        'table': 'bmrs_fuelinst',
        'date_param': 'publishDateTimeFrom'
    },
    'FREQ': {
        'url_template': 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FREQ',
        'table': 'bmrs_freq',
        'date_param': 'from'
    },
    'BOALF': {
        'url_template': 'https://data.elexon.co.uk/bmrs/api/v1/datasets/BOALF',
        'table': 'bmrs_boalf',
        'date_param': 'settlementDateFrom'
    },
    'MID': {
        'url_template': 'https://data.elexon.co.uk/bmrs/api/v1/datasets/MID',
        'table': 'bmrs_mid',
        'date_param': 'settlementDateFrom'
    }
}

print("=" * 80)
print("BMRS BACKFILL - Dec 15-17, 2025")
print("=" * 80)
print(f"\n📅 Date range: {START_DATE} to {END_DATE}")
print(f"📦 Datasets: {', '.join(DATASETS.keys())}\n")

# Initialize BigQuery client
client = bigquery.Client(project=BQ_PROJECT, location='US')

# Process each dataset
for dataset_name, config in DATASETS.items():
    print(f"\n{'='*80}")
    print(f"Processing {dataset_name}")
    print(f"{'='*80}")

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{config['table']}"
    all_records = []

    # Fetch data day by day
    start_dt = datetime.strptime(START_DATE, '%Y-%m-%d')
    end_dt = datetime.strptime(END_DATE, '%Y-%m-%d')
    current_date = start_dt.date()

    while current_date <= end_dt.date():
        date_str = current_date.strftime('%Y-%m-%d')

        # Build URL with date parameters
        url = config['url_template']
        params = {
            config['date_param']: f"{date_str}T00:00:00Z",
            'format': 'json'
        }

        # Add "to" parameter for date range
        if config['date_param'] == 'publishDateTimeFrom':
            params['publishDateTimeTo'] = f"{date_str}T23:59:59Z"
        elif config['date_param'] == 'from':
            params['to'] = f"{date_str}T23:59:59Z"
        elif config['date_param'] == 'settlementDateFrom':
            params['settlementDateTo'] = f"{date_str}T23:59:59Z"

        try:
            print(f"  {date_str}: Fetching...", end='', flush=True)
            response = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    records = data['data']
                    print(f" ✅ {len(records)} records")
                    all_records.extend(records)
                else:
                    print(" ⚠️  No data")

            elif response.status_code == 404:
                print(" ⚠️  404 Not Found")

            else:
                print(f" ❌ HTTP {response.status_code}")

        except Exception as e:
            print(f" ❌ Error: {str(e)[:60]}")

        current_date += timedelta(days=1)
        time.sleep(0.5)  # Rate limiting

    # Upload to BigQuery
    if not all_records:
        print(f"\n  ⚠️  No data retrieved for {dataset_name} - skipping upload")
        continue

    print(f"\n  📊 Total records: {len(all_records):,}")

    try:
        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Convert datetime strings to proper DATETIME for BigQuery
        datetime_cols = ['publishTime', 'startTime', 'settlementDate', 'measurementTime',
                        'acceptanceTime', 'createdDateTime']

        for col in datetime_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], utc=True)
                except:
                    pass  # Keep as string if conversion fails

        print(f"  📤 Uploading to {table_id}...")

        # Use WRITE_APPEND to add to existing data
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
            ]
        )

        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion

        print(f"  ✅ Uploaded {len(df):,} rows to {config['table']}")

    except Exception as e:
        print(f"  ❌ Upload failed: {str(e)[:200]}")
        print(f"     Columns: {list(df.columns)[:10]}...")

print(f"\n{'='*80}")
print("✅ BACKFILL COMPLETE")
print(f"{'='*80}\n")
