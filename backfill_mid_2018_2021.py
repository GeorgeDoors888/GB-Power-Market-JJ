#!/usr/bin/env python3
"""
Backfill MID (Market Index Data) from 2018-2021
⚠️ API LIMITATION: MID data does NOT exist before 2018!

API Testing Results:
- 2016-2017: 0 records (no data)
- 2018+: 96 records/day ✅ (2 records × 48 settlement periods)

Expected backfill: ~140k rows (1,461 days: 2018-2021 = 96 × 1,461)
Storage: <1 GB
Runtime: ~20-30 minutes
"""

from google.cloud import bigquery
import requests
from datetime import datetime, timedelta
import time
import os
import pandas as pd

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

BMRS_BASE = 'https://data.elexon.co.uk/bmrs/api/v1/datasets'

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

                if not records:
                    print(f'  ℹ️  {date_str}: API returned empty data')
                else:
                    all_records.extend(records)
                    if len(all_records) % 10000 == 0:
                        print(f'  📊 Progress: {len(all_records):,} records...', end='\r')
            elif response.status_code == 400:
                print(f'  ⚠️  {date_str}: 400 Bad Request')
            else:
                print(f'  ❌ {date_str}: HTTP {response.status_code}')

            time.sleep(0.02)  # Rate limiting (faster than BOD)
        except Exception as e:
            print(f'  ❌ {date_str}: {str(e)[:60]}')

        current_date += timedelta(days=1)

    # Upload all records for the year
    if all_records:
        print(f'\n  📤 Uploading {len(all_records):,} records for {year}...')
        upload_to_bigquery(all_records, year)
    else:
        print(f'  ⚠️  No records to upload for {year}')

    return len(all_records)

def upload_to_bigquery(records, year):
    """Upload records to BigQuery bmrs_mid table"""
    if not records:
        return

    df = pd.DataFrame(records)

    # Add metadata
    df['_ingested_utc'] = pd.Timestamp.now(tz='UTC')
    df['_backfill_year'] = year

    table_id = 'inner-cinema-476211-u9.uk_energy_prod.bmrs_mid'

    # Configure write disposition to append
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_APPEND',
        create_disposition='CREATE_IF_NEEDED'
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion

    print(f'  ✅ Uploaded {len(records):,} records for {year}')

if __name__ == '__main__':
    print('=' * 100)
    print('🚀 HISTORICAL BACKFILL: MID 2018-2021 (Market Index Data)')
    print('⚠️  API LIMITATION: MID data does NOT exist before 2018')
    print('=' * 100)

    # ONLY 2018-2021 have data available
    years = [2018, 2019, 2020, 2021]  # NOT 2016-2017! API returns empty
    total_rows = 0

    for year in years:
        try:
            rows = backfill_mid(year)
            total_rows += rows
            print(f'\n  ✅ {year} complete: {rows:,} rows')
        except Exception as e:
            print(f'\n  ❌ {year} failed: {str(e)}')
            continue

    print('\n' + '=' * 100)
    print(f'✅ BACKFILL COMPLETE: {total_rows:,} total rows')
    print('=' * 100)

    # Verify data
    print('\n📊 Verifying data coverage...')
    query = '''
    SELECT
      EXTRACT(YEAR FROM settlementDate) as year,
      COUNT(*) as records,
      COUNT(DISTINCT DATE(settlementDate)) as days
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
