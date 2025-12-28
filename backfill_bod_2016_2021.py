#!/usr/bin/env python3
"""
Backfill BOD (Bid-Offer Data) from 2020-2021 ONLY
⚠️ CRITICAL DISCOVERY: BOD data NOT available before 2020!

API Testing Results:
- 2016-2019: {"data":[]} (empty response)
- 2020-01-01: 6,502 records ✅
- 2022-01-01: 7,614 records ✅

CONFIRMED: bmrs_bod table already contains per-BM-unit data (bmUnit column)
- NOT aggregated as originally assumed
- derive_boalf_prices.py joins BOALF to BOD by bmUnit (line 195)
- 407M existing rows (2022-2025) with 1,657 unique BM Units

Expected backfill: ~7-10M rows (2020-2021 = 730 days × ~7k records/day)
Storage: ~5-7 GB (partitioned by settlementDate)
Runtime: ~1-2 hours
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

def backfill_bod(year):
    """Backfill BOD for a given year (2020-2021 only)"""
    print(f'\n📅 Backfilling BOD for {year}...')
    all_records = []

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')

        # BOD API format - matches ingest_elexon_fixed.py line 708
        url = f'{BMRS_BASE}/BOD/stream'
        params = {
            'from': f'{date_str}T00:00:00Z',
            'to': f'{date_str}T23:59:59Z',
            'settlementPeriodFrom': '1',
            'settlementPeriodTo': '50'
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()

                # /stream endpoint returns array directly, not {"data": [...]}
                if isinstance(data, list):
                    records = data
                else:
                    records = data.get('data', [])

                if not records:
                    print(f'  ℹ️  {date_str}: API returned empty data (no BOD exists for this date)')
                else:
                    all_records.extend(records)
                    print(f'  ✅ {date_str}: {len(records):,} records')

                    if len(all_records) % 100000 == 0:
                        print(f'  📊 Progress: {len(all_records):,} records total...', end='\r')
            elif response.status_code == 400:
                print(f'  ⚠️  {date_str}: 400 Bad Request - likely no data exists')
            else:
                print(f'  ❌ {date_str}: HTTP {response.status_code}')

            time.sleep(0.05)  # Rate limiting
        except Exception as e:
            print(f'  ❌ {date_str}: {str(e)[:60]}')

        current_date += timedelta(days=1)

        # Upload in chunks of 100k records to avoid memory issues
        if len(all_records) >= 100000:
            print(f'\n  📤 Uploading chunk: {len(all_records):,} records...')
            upload_to_bigquery(all_records, year)
            all_records = []

    # Upload remaining records
    if all_records:
        print(f'\n  📤 Uploading final chunk: {len(all_records):,} records...')
        upload_to_bigquery(all_records, year)

    return True

def upload_to_bigquery(records, year):
    """Upload records to BigQuery with proper type conversion"""
    df = pd.DataFrame(records)

    # Get existing table schema
    table = client.get_table('inner-cinema-476211-u9.uk_energy_prod.bmrs_bod')
    existing_cols = {field.name for field in table.schema}

    # Only keep columns that exist in target table
    df = df[[col for col in df.columns if col in existing_cols]]

    # Convert datetime columns
    datetime_cols = ['settlementDate', 'timeFrom', 'timeTo', 'createdDateTime']
    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Convert numeric columns
    numeric_cols = ['settlementPeriod', 'pairId', 'bid', 'offer',
                   'levelFrom', 'levelTo', 'offerVolume', 'bidVolume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Upload to BigQuery
    table_id = 'inner-cinema-476211-u9.uk_energy_prod.bmrs_bod'
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_APPEND',
        autodetect=False
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

    print(f'  ✅ Uploaded {len(records):,} records for {year}')

if __name__ == '__main__':
    print('=' * 100)
    print('🚀 HISTORICAL BACKFILL: BOD 2020-2021 ONLY (Per-BM-Unit Data)')
    print('⚠️  CRITICAL DISCOVERY: BOD already per-unit (bmUnit column exists in table!)')
    print('⚠️  API LIMITATION: BOD data does NOT exist before 2020 (API returns empty)')
    print('=' * 100)

    # ONLY 2020-2021 have data available!
    years = [2020, 2021]  # Changed from [2016, 2017, 2018, 2019, 2020, 2021]

    for year in years:
        try:
            backfill_bod(year)
            print(f'\n  ✅ {year} complete')
        except Exception as e:
            print(f'\n  ❌ {year} failed: {str(e)}')
            continue

    print('\n' + '=' * 100)
    print('✅ BACKFILL COMPLETE')
    print('=' * 100)

    # Verify data
    print('\n📊 Verifying data coverage...')
    query = '''
    SELECT
      EXTRACT(YEAR FROM settlementDate) as year,
      COUNT(*) as records,
      COUNT(DISTINCT DATE(settlementDate)) as days
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
    WHERE EXTRACT(YEAR FROM settlementDate) BETWEEN 2020 AND 2025
    GROUP BY year
    ORDER BY year
    '''

    result = client.query(query).to_dataframe()
    print(result.to_string(index=False))

