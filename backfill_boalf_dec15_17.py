#!/usr/bin/env python3
"""
Backfill BOALF data for Dec 15-17, 2025
Uses settlement period API (requires per-SP queries)
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import time

BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
TIMEOUT = (10, 90)

print("=" * 80)
print("BOALF BACKFILL - Dec 15-17, 2025 (Settlement Period API)")
print("=" * 80)

# Initialize BigQuery client
client = bigquery.Client(project=BQ_PROJECT, location='US')
table_id = f"{BQ_PROJECT}.{BQ_DATASET}.bmrs_boalf"

all_records = []
dates = ['2025-12-15', '2025-12-16', '2025-12-17']

total_calls = len(dates) * 48
print(f"\nTotal API calls required: {total_calls}")
print("Estimated time: ~5 minutes (with rate limiting)\n")

call_count = 0

for date_str in dates:
    print(f"\n{'='*80}")
    print(f"Processing {date_str}")
    print(f"{'='*80}")

    date_records = 0

    for sp in range(1, 49):  # Settlement periods 1-48
        call_count += 1

        url = "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances/all"
        params = {
            'settlementDate': date_str,
            'settlementPeriod': sp,
            'format': 'json'
        }

        try:
            print(f"  SP {sp:2d}: ", end='', flush=True)
            response = requests.get(url, params=params, timeout=TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    records = data['data']
                    print(f"✅ {len(records):4d} records")
                    all_records.extend(records)
                    date_records += len(records)
                else:
                    print("⚠️  No data")

            elif response.status_code == 404:
                print("⚠️  404")

            else:
                print(f"❌ HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ {str(e)[:40]}")

        # Rate limiting: 2 requests per second max
        if call_count % 100 == 0:
            print(f"\n  Progress: {call_count}/{total_calls} calls ({call_count*100//total_calls}%)")

        time.sleep(0.6)  # ~1.67 requests/second

    print(f"\n  {date_str} total: {date_records:,} records")

print(f"\n{'='*80}")
print(f"FETCHING COMPLETE")
print(f"{'='*80}")
print(f"Total records: {len(all_records):,}")

if not all_records:
    print("\n❌ No data retrieved - EXITING")
    exit(1)

# Convert to DataFrame
print(f"\nConverting to DataFrame...")
df = pd.DataFrame(all_records)

# Convert datetime columns
datetime_cols = ['timeFrom', 'timeTo', 'acceptanceTime', 'settlementDate']
for col in datetime_cols:
    if col in df.columns:
        try:
            if col == 'settlementDate':
                # Keep as date string, will convert to DATE in BigQuery
                pass
            else:
                df[col] = pd.to_datetime(df[col], utc=True)
        except:
            pass

# Convert numeric columns
numeric_cols = ['settlementPeriodFrom', 'settlementPeriodTo', 'levelFrom', 'levelTo', 'acceptanceNumber']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Convert boolean columns
bool_cols = ['deemedBoFlag', 'soFlag', 'storFlag', 'rrFlag']
for col in bool_cols:
    if col in df.columns:
        df[col] = df[col].astype(bool)

print(f"DataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Upload to BigQuery
print(f"\n{'='*80}")
print(f"Uploading to {table_id}...")
print(f"{'='*80}")

try:
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion

    print(f"\n✅ Successfully uploaded {len(df):,} rows to bmrs_boalf")

    # Verify upload
    query = f"""
    SELECT
        settlementDate,
        COUNT(*) as records
    FROM `{table_id}`
    WHERE settlementDate IN ('2025-12-15', '2025-12-16', '2025-12-17')
    GROUP BY settlementDate
    ORDER BY settlementDate
    """

    print(f"\n{'='*80}")
    print("Verification:")
    print(f"{'='*80}")

    for row in client.query(query).result():
        print(f"  {row.settlementDate}: {row.records:,} records")

except Exception as e:
    print(f"\n❌ Upload failed: {str(e)[:200]}")
    exit(1)

print(f"\n{'='*80}")
print("✅ BOALF BACKFILL COMPLETE")
print(f"{'='*80}\n")
