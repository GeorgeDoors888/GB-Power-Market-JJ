#!/usr/bin/env python3
"""
Fetch latest FUELINST data from Elexon API and upload to BigQuery
"""
import httpx
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, date

def fetch_and_upload():
    print('📡 Fetching latest FUELINST data from Elexon API...')
    print()
    
    # Get today's data
    url = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST'
    params = {
        'settlementDateFrom': str(date.today()),
        'settlementDateTo': str(date.today())
    }
    
    response = httpx.get(url, params=params, timeout=120)
    print(f'✅ API Response: {response.status_code}')
    
    if response.status_code != 200:
        print(f'❌ API Error: {response.status_code}')
        print(response.text[:500])
        return
    
    data = response.json()
    records = data.get('data', []) if isinstance(data, dict) else data
    print(f'📊 Retrieved {len(records)} records from Elexon')
    
    if not records:
        print('⚠️  No new data available from API')
        return
    
    # Show sample of latest data
    latest_records = sorted(records, key=lambda x: x.get('publishTime', ''), reverse=True)[:5]
    print(f'🕐 Latest timestamps:')
    for rec in latest_records:
        print(f"   {rec.get('publishTime', 'N/A')} - {rec.get('fuelType', 'N/A')}: {rec.get('generation', 0):.0f} MW")
    print()
    
    # Convert to DataFrame and fix data types
    df = pd.DataFrame(records)
    
    # Convert all datetime columns
    datetime_cols = ['publishTime', 'startTime', 'settlementDate']
    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    # Ensure numeric columns are proper types
    numeric_cols = ['generation', 'settlementPeriod']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print('⬆️  Uploading to BigQuery...')
    client = bigquery.Client(project='inner-cinema-476211-u9')
    table_id = 'inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst'
    
    # Use WRITE_TRUNCATE with table partitioning by date
    # This replaces today's data without affecting historical data
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f'✅ Uploaded {len(records)} records to BigQuery')
    print(f'📅 Data range: {df["publishTime"].min()} to {df["publishTime"].max()}')
    print()
    print('🎯 Ready to update dashboard!')

if __name__ == '__main__':
    fetch_and_upload()
