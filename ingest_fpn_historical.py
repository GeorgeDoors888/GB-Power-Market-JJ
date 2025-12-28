#!/usr/bin/env python3
"""
Ingest FPN (Final Physical Notification) data from BMRS API

FPN = Generator's forecast of expected output per settlement period
Used to detect NGSEA Feature C: Large FPN vs actual mismatch

API: GET /datasets/FPN
Docs: https://developer.data.elexon.co.uk/api-details#api=prod-insig-insights-api

Usage:
    python3 ingest_fpn_historical.py --start-date 2024-01-01 --end-date 2024-12-31
    python3 ingest_fpn_historical.py --start-date 2024-10-17 --end-date 2024-10-17  # Test single day
"""

import os
import sys
import time
import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import argparse

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FPN"

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

def fetch_fpn_day(date_str):
    """Fetch FPN data for one day from BMRS API"""
    params = {
        'settlementDate': date_str,
        'format': 'json'
    }
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Handle different response structures
        if 'data' in data and isinstance(data['data'], list):
            return pd.DataFrame(data['data'])
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            print(f"⚠️  Unexpected response structure for {date_str}")
            return pd.DataFrame()
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return pd.DataFrame()  # No data for this day
        else:
            raise
    except Exception as e:
        print(f"❌ Error fetching {date_str}: {e}")
        return pd.DataFrame()

def ingest_fpn_range(start_date, end_date, test_mode=False):
    """Ingest FPN for date range"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    total_rows = 0
    successful_days = 0
    failed_days = 0
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        try:
            df = fetch_fpn_day(date_str)
            
            if df.empty:
                print(f"⚠️  {date_str}: No data available")
                failed_days += 1
                current += timedelta(days=1)
                continue
            
            # Add metadata
            df['ingested_utc'] = datetime.utcnow()
            
            # Test mode: just show first few rows
            if test_mode:
                print(f"\n✅ {date_str}: {len(df):,} rows")
                print(f"   Columns: {', '.join(df.columns.tolist())}")
                print(f"   Sample data:")
                print(df.head(3).to_string())
                total_rows += len(df)
                successful_days += 1
                current += timedelta(days=1)
                continue
            
            # Upload to BigQuery (append mode)
            table_id = f"{PROJECT_ID}.{DATASET}.bmrs_fpn"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True
            )
            
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            print(f"✅ {date_str}: {len(df):,} rows uploaded")
            total_rows += len(df)
            successful_days += 1
            
            # Rate limiting: 1 request per second
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ {date_str}: {e}")
            failed_days += 1
        
        current += timedelta(days=1)
    
    print(f"\n{'='*70}")
    print(f"FPN Ingestion Complete")
    print(f"{'='*70}")
    print(f"Successful days: {successful_days}")
    print(f"Failed days: {failed_days}")
    print(f"Total rows: {total_rows:,}")
    
    if not test_mode:
        # Verify table exists
        try:
            table = client.get_table(f"{PROJECT_ID}.{DATASET}.bmrs_fpn")
            print(f"\n✅ Table bmrs_fpn exists with {table.num_rows:,} total rows")
        except Exception as e:
            print(f"\n⚠️  Could not verify table: {e}")

def main():
    parser = argparse.ArgumentParser(description='Ingest FPN data from BMRS API')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--test', action='store_true', help='Test mode (no upload)')
    args = parser.parse_args()
    
    print(f"{'='*70}")
    print(f"FPN Ingestion")
    print(f"{'='*70}")
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Mode: {'TEST (no upload)' if args.test else 'PRODUCTION (uploading to BigQuery)'}")
    print(f"API: {BASE_URL}")
    print(f"")
    
    ingest_fpn_range(args.start_date, args.end_date, test_mode=args.test)

if __name__ == "__main__":
    main()
