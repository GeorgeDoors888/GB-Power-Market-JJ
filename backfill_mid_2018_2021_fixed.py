#!/usr/bin/env python3
"""
Backfill MID (Market Index Data) from 2018-2021 - FIXED VERSION
⚠️ FIX: Ingest startTime as STRING, normalize post-load

Previous Error: "Error converting Pandas column 'startTime' datatype 'object' to pyarrow"
Root Cause: Pre-2022 MID has non-ISO time formats, missing timezones
Solution: Load as STRING initially, normalize with BigQuery SQL
"""

from google.cloud import bigquery
import requests
from datetime import datetime, timedelta
import time
import os
import pandas as pd
import json

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

BMRS_BASE = 'https://data.elexon.co.uk/bmrs/api/v1/datasets'

# Define schema with startTime as STRING (will normalize later)
SCHEMA = [
    bigquery.SchemaField("dataset", "STRING"),
    bigquery.SchemaField("startTime", "STRING"),  # ← Changed from DATETIME to STRING
    bigquery.SchemaField("dataProvider", "STRING"),
    bigquery.SchemaField("settlementDate", "DATETIME"),
    bigquery.SchemaField("settlementPeriod", "INTEGER"),
    bigquery.SchemaField("price", "FLOAT"),
    bigquery.SchemaField("volume", "FLOAT"),
    bigquery.SchemaField("_ingested_utc", "TIMESTAMP"),
    bigquery.SchemaField("_backfill_year", "INTEGER"),
]

def create_staging_table():
    """Create staging table with STRING startTime"""
    table_id = 'inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_staging'

    table = bigquery.Table(table_id, schema=SCHEMA)
    table = client.create_table(table, exists_ok=True)
    print(f'✅ Created staging table: {table_id}')
    return table_id

def backfill_mid(year):
    """Backfill MID for a given year (2018-2021 only)"""
    print(f'\n📅 Backfilling MID for {year}...')
    all_records = []

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')

        url = f'{BMRS_BASE}/MID'
        params = {
            'from': f'{date_str}T00:00:00Z',
            'to': f'{date_str}T23:59:59Z'
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])

                if records:
                    all_records.extend(records)
                    if len(all_records) % 10000 == 0:
                        print(f'  📊 Progress: {len(all_records):,} records...', end='\r')
            elif response.status_code == 400:
                print(f'  ⚠️  {date_str}: 400 Bad Request (likely no data)')
            else:
                print(f'  ❌ {date_str}: HTTP {response.status_code}')

            time.sleep(0.02)  # Rate limiting
        except Exception as e:
            print(f'  ❌ {date_str}: {str(e)[:60]}')

        current_date += timedelta(days=1)

    # Upload all records for the year
    if all_records:
        print(f'\n  📤 Uploading {len(all_records):,} records for {year}...')
        upload_to_staging(all_records, year)
    else:
        print(f'  ⚠️  No records to upload for {year}')

    return len(all_records)

def upload_to_staging(records, year):
    """Upload records to staging table with STRING startTime"""
    if not records:
        return

    df = pd.DataFrame(records)

    # Convert startTime to STRING explicitly (no parsing)
    if 'startTime' in df.columns:
        df['startTime'] = df['startTime'].astype(str)

    # Add metadata
    df['_ingested_utc'] = pd.Timestamp.now(tz='UTC')
    df['_backfill_year'] = year

    # Select only columns in schema
    cols_in_schema = [field.name for field in SCHEMA]
    df = df[[col for col in cols_in_schema if col in df.columns]]

    table_id = 'inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_staging'

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition='WRITE_APPEND',
        create_disposition='CREATE_IF_NEEDED'
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion

    print(f'  ✅ Uploaded {len(records):,} records to staging for {year}')

def normalize_and_merge():
    """Normalize startTime and merge staging → production table"""
    print('\n🔧 Normalizing startTime and merging to production...')

    query = '''
    INSERT INTO `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
    (dataset, startTime, dataProvider, settlementDate, settlementPeriod,
     price, volume, _ingested_utc)
    SELECT
      dataset,
      -- Attempt to parse various date formats, fallback to NULL
      CASE
        WHEN SAFE.PARSE_DATETIME('%Y-%m-%dT%H:%M:%S', startTime) IS NOT NULL
          THEN SAFE.PARSE_DATETIME('%Y-%m-%dT%H:%M:%S', startTime)
        WHEN SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', startTime) IS NOT NULL
          THEN SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', startTime)
        WHEN SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M:%S', startTime) IS NOT NULL
          THEN SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M:%S', startTime)
        ELSE NULL
      END as startTime,
      dataProvider,
      settlementDate,
      settlementPeriod,
      price,
      volume,
      _ingested_utc
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_staging`
    WHERE settlementDate IS NOT NULL  -- Only insert valid records
    '''

    job = client.query(query)
    job.result()

    rows_added = job.num_dml_affected_rows if hasattr(job, 'num_dml_affected_rows') else 0
    print(f'  ✅ Merged {rows_added:,} records to production table')

    # Drop staging table
    client.delete_table('inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_staging', not_found_ok=True)
    print('  🗑️  Dropped staging table')

if __name__ == '__main__':
    print('=' * 100)
    print('🚀 HISTORICAL BACKFILL: MID 2018-2021 (Market Index Data) - FIXED VERSION')
    print('⚠️  API LIMITATION: MID data does NOT exist before 2018')
    print('🔧 FIX: Load startTime as STRING, normalize with BigQuery SQL')
    print('=' * 100)

    # Create staging table
    create_staging_table()

    # ONLY 2018-2021 have data available
    years = [2018, 2019, 2020, 2021]
    total_rows = 0

    for year in years:
        try:
            rows = backfill_mid(year)
            total_rows += rows
            print(f'\n  ✅ {year} complete: {rows:,} rows uploaded to staging')
        except Exception as e:
            print(f'\n  ❌ {year} failed: {str(e)}')
            continue

    # Normalize and merge to production
    if total_rows > 0:
        normalize_and_merge()

    print('\n' + '=' * 100)
    print(f'✅ BACKFILL COMPLETE: {total_rows:,} total rows processed')
    print('=' * 100)

    # Verify data
    print('\n📊 Verifying data coverage...')
    query = '''
    SELECT
      EXTRACT(YEAR FROM settlementDate) as year,
      COUNT(*) as records,
      COUNT(DISTINCT DATE(settlementDate)) as days,
      COUNT(CASE WHEN startTime IS NULL THEN 1 END) as null_starttime
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
    WHERE EXTRACT(YEAR FROM settlementDate) BETWEEN 2018 AND 2025
    GROUP BY year
    ORDER BY year
    '''

    result = client.query(query).to_dataframe()
    print(result.to_string(index=False))

    total = result['records'].sum()
    print(f'\n📈 TOTAL MID RECORDS: {total:,}')
    print('✅ MID backfill verification complete!')
