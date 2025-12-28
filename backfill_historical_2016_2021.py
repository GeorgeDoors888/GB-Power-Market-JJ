#!/usr/bin/env python3
"""
Backfill BMRS data from 2016-2021 (6 years of missing historical data)
Fetches from Elexon BMRS API v1 and uploads to BigQuery
"""

from google.cloud import bigquery
import requests
from datetime import datetime, timedelta
import time
import os
import pandas as pd

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

def backfill_costs(year):
    """Backfill bmrs_costs for a given year"""
    print(f'\n📅 Backfilling bmrs_costs for {year}...')
    all_records = []

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        url = f'https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/{date_str}'

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])
                all_records.extend(records)
                if len(all_records) % 1000 == 0:
                    print(f'  Progress: {len(all_records)} records...', end='\r')
            time.sleep(0.05)
        except Exception as e:
            print(f'  ❌ {date_str}: {str(e)[:60]}')

        current_date += timedelta(days=1)

    if all_records:
        # Convert to DataFrame with proper types
        df = pd.DataFrame(all_records)

        # Get existing table schema to match columns
        table = client.get_table('inner-cinema-476211-u9.uk_energy_prod.bmrs_costs')
        existing_cols = {field.name for field in table.schema}

        # Only keep columns that exist in target table
        df = df[[col for col in df.columns if col in existing_cols]]

        # Convert all datetime columns
        datetime_cols = ['settlementDate', 'startTime', 'createdDateTime']
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Ensure numeric columns
        numeric_cols = ['systemSellPrice', 'systemBuyPrice', 'settlementPeriod',
                       'reserveScarcityPrice', 'netImbalanceVolume', 'sellPriceAdjustment',
                       'buyPriceAdjustment', 'replacementPrice', 'replacementPriceReferenceVolume',
                       'totalAcceptedOfferVolume', 'totalAcceptedBidVolume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Upload to BigQuery
        table_id = 'inner-cinema-476211-u9.uk_energy_prod.bmrs_costs'
        job_config = bigquery.LoadJobConfig(
            write_disposition='WRITE_APPEND',
            autodetect=False  # Use existing schema
        )

        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()

        print(f'  ✅ Uploaded {len(all_records):,} records for {year}')
        return len(all_records)
    else:
        print(f'  ⚠️  No records for {year}')
        return 0

if __name__ == '__main__':
    print('=' * 100)
    print('🚀 HISTORICAL BACKFILL: 2016-2021')
    print('=' * 100)

    years = [2016, 2017, 2018, 2019, 2020, 2021]
    total_uploaded = 0

    for year in years:
        count = backfill_costs(year)
        total_uploaded += count
        print(f'  Cumulative: {total_uploaded:,} records')

    print('\n' + '=' * 100)
    print(f'✅ COMPLETE: {total_uploaded:,} records uploaded (2016-2021)')
    print('=' * 100)
