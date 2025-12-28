#!/usr/bin/env python3
"""
Backfill DISBSAD (Disaggregated BSAD) from 2016-2025
DISBSAD = Detailed breakdown of system balancing costs/volumes

API Testing Results:
- 2020-01-01: 218 records ✅ (API works!)
- Variable records/day (depends on balancing actions)

Expected backfill: ~500k-2M rows (2016-2025, 10 years)
Storage: ~5-10 GB
Runtime: ~2-3 hours
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

def backfill_disbsad(year):
    """Backfill DISBSAD for a given year"""
    print(f'\n📅 Backfilling DISBSAD for {year}...')
    all_records = []

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')

        url = f'{BMRS_BASE}/DISBSAD'
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
                    if len(all_records) % 50000 == 0:
                        print(f'  📊 Progress: {len(all_records):,} records...', end='\r')

            elif response.status_code == 400:
                print(f'  ⚠️  {date_str}: 400 Bad Request')
            else:
                print(f'  ❌ {date_str}: HTTP {response.status_code}')

            time.sleep(0.02)  # Rate limiting
        except Exception as e:
            print(f'  ❌ {date_str}: {str(e)[:60]}')

        current_date += timedelta(days=1)

        # Upload in chunks of 100k records
        if len(all_records) >= 100000:
            print(f'\n  📤 Uploading chunk: {len(all_records):,} records...')
            upload_to_bigquery(all_records, year)
            all_records = []

    # Upload remaining records
    if all_records:
        print(f'\n  📤 Uploading final chunk: {len(all_records):,} records...')
        upload_to_bigquery(all_records, year)

    return len(all_records)

def upload_to_bigquery(records, year):
    """Upload records to BigQuery bmrs_disbsad table"""
    if not records:
        return

    df = pd.DataFrame(records)

    # Add metadata
    df['_ingested_utc'] = pd.Timestamp.now(tz='UTC')
    df['_backfill_year'] = year

    table_id = 'inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad'

    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_APPEND',
        create_disposition='CREATE_IF_NEEDED'
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

    print(f'  ✅ Uploaded {len(records):,} records for {year}')

if __name__ == '__main__':
    print('=' * 100)
    print('🚀 HISTORICAL BACKFILL: DISBSAD 2016-2025')
    print('=' * 100)

    years = list(range(2016, 2022))  # 2016-2021 (2022+ already ingested)
    total_rows = 0

    for year in years:
        try:
            rows = backfill_disbsad(year)
            total_rows += rows
            print(f'\n  ✅ {year} complete: {rows:,} rows')
        except Exception as e:
            print(f'\n  ❌ {year} failed: {str(e)}')
            continue

    print('\n' + '=' * 100)
    print(f'✅ BACKFILL COMPLETE: {total_rows:,} total rows added')
    print('=' * 100)

    # Verify data
    print('\n📊 Verifying data coverage...')
    query = '''
    SELECT
      EXTRACT(YEAR FROM settlementDate) as year,
      COUNT(*) as records,
      COUNT(DISTINCT DATE(settlementDate)) as days
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
    GROUP BY year
    ORDER BY year
    '''

    result = client.query(query).to_dataframe()
    print(result.to_string(index=False))

    print('\n✅ DISBSAD backfill verification complete!')
