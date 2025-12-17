#!/usr/bin/env python3
"""
Comprehensive Backfill Script for Historical Tables
Backfills: bmrs_freq (full 2022-present), bmrs_mid (Oct 30-Dec 17), bmrs_bod (Oct 28-Dec 17)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
import time
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

# Elexon API base URL
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

def fetch_freq_data(from_date, to_date):
    """Fetch FREQ data from Elexon API"""
    url = f"{BASE_URL}/FREQ"
    params = {
        'from': from_date.strftime('%Y-%m-%dT00:00Z'),
        'to': to_date.strftime('%Y-%m-%dT23:59Z')
    }

    print(f"  Fetching FREQ: {from_date} to {to_date}")
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    if 'data' in data and len(data['data']) > 0:
        df = pd.DataFrame(data['data'])
        print(f"    Retrieved {len(df)} FREQ records")
        return df
    return pd.DataFrame()

def fetch_mid_data(from_date, to_date):
    """Fetch MID data from Elexon API"""
    url = f"{BASE_URL}/MID"
    params = {
        'from': from_date.strftime('%Y-%m-%dT00:00Z'),
        'to': to_date.strftime('%Y-%m-%dT23:59Z')
    }

    print(f"  Fetching MID: {from_date} to {to_date}")
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    if 'data' in data and len(data['data']) > 0:
        df = pd.DataFrame(data['data'])
        print(f"    Retrieved {len(df)} MID records")
        return df
    return pd.DataFrame()

def fetch_bod_data(from_date, to_date):
    """Fetch BOD (Bid Offer Data) from Elexon API"""
    url = f"{BASE_URL}/BOD"
    params = {
        'from': from_date.strftime('%Y-%m-%dT00:00Z'),
        'to': to_date.strftime('%Y-%m-%dT23:59Z')
    }

    print(f"  Fetching BOD: {from_date} to {to_date}")
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    if 'data' in data and len(data['data']) > 0:
        df = pd.DataFrame(data['data'])
        print(f"    Retrieved {len(df)} BOD records")
        return df
    return pd.DataFrame()

def upload_to_bigquery(df, table_name):
    """Upload DataFrame to BigQuery with schema auto-detection"""
    if df.empty:
        print(f"  Skipping upload - no data for {table_name}")
        return 0

    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        source_format=bigquery.SourceFormat.CSV,
        autodetect=True,
    )

    print(f"  Uploading {len(df)} rows to {table_name}...")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion

    print(f"  ✅ Uploaded {len(df)} rows to {table_name}")
    return len(df)

def backfill_freq_full():
    """Backfill FREQ data from 2022-01-01 to present (full historical range)"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_freq - FULL HISTORICAL (2022-01-01 to 2025-12-17)")
    print("="*80)

    start_date = datetime(2022, 1, 1)
    end_date = datetime(2025, 12, 17)
    total_uploaded = 0

    # Fetch in 7-day chunks to avoid API timeouts
    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=7), end_date)

        try:
            df = fetch_freq_data(current, chunk_end)
            if not df.empty:
                uploaded = upload_to_bigquery(df, 'bmrs_freq')
                total_uploaded += uploaded

            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"  ⚠️ Error for {current}: {e}")

        current = chunk_end + timedelta(days=1)

    print(f"\n✅ FREQ backfill complete: {total_uploaded:,} total records")
    return total_uploaded

def backfill_mid_gap():
    """Backfill MID data from Oct 30, 2025 to Dec 17, 2025"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_mid - GAP (2025-10-30 to 2025-12-17)")
    print("="*80)

    start_date = datetime(2025, 10, 30)
    end_date = datetime(2025, 12, 17)
    total_uploaded = 0

    # Fetch in 3-day chunks
    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=3), end_date)

        try:
            df = fetch_mid_data(current, chunk_end)
            if not df.empty:
                uploaded = upload_to_bigquery(df, 'bmrs_mid')
                total_uploaded += uploaded

            time.sleep(1)

        except Exception as e:
            print(f"  ⚠️ Error for {current}: {e}")

        current = chunk_end + timedelta(days=1)

    print(f"\n✅ MID backfill complete: {total_uploaded:,} total records")
    return total_uploaded

def backfill_bod_gap():
    """Backfill BOD data from Oct 28, 2025 to Dec 17, 2025"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_bod - GAP (2025-10-28 to 2025-12-17)")
    print("="*80)

    start_date = datetime(2025, 10, 28)
    end_date = datetime(2025, 12, 17)
    total_uploaded = 0

    # BOD is large - use 1-day chunks
    current = start_date
    while current < end_date:
        chunk_end = current

        try:
            df = fetch_bod_data(current, chunk_end)
            if not df.empty:
                uploaded = upload_to_bigquery(df, 'bmrs_bod')
                total_uploaded += uploaded

            time.sleep(2)  # Longer delay for large dataset

        except Exception as e:
            print(f"  ⚠️ Error for {current}: {e}")

        current += timedelta(days=1)

    print(f"\n✅ BOD backfill complete: {total_uploaded:,} total records")
    return total_uploaded

if __name__ == "__main__":
    print("=" * 80)
    print("COMPREHENSIVE BACKFILL - Dec 17, 2025")
    print("=" * 80)
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET}")
    print(f"Started: {datetime.now()}")

    # Check credentials
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("\n⚠️ Warning: GOOGLE_APPLICATION_CREDENTIALS not set")
        print("Set it with: export GOOGLE_APPLICATION_CREDENTIALS='path/to/credentials.json'")

    results = {}

    # 1. FREQ - Full historical backfill (2022-present)
    try:
        results['freq'] = backfill_freq_full()
    except Exception as e:
        print(f"\n❌ FREQ backfill failed: {e}")
        results['freq'] = 0

    # 2. MID - Gap fill (Oct 30 - Dec 17)
    try:
        results['mid'] = backfill_mid_gap()
    except Exception as e:
        print(f"\n❌ MID backfill failed: {e}")
        results['mid'] = 0

    # 3. BOD - Gap fill (Oct 28 - Dec 17)
    try:
        results['bod'] = backfill_bod_gap()
    except Exception as e:
        print(f"\n❌ BOD backfill failed: {e}")
        results['bod'] = 0

    # Summary
    print("\n" + "=" * 80)
    print("BACKFILL SUMMARY")
    print("=" * 80)
    print(f"FREQ (2022-present):     {results.get('freq', 0):,} records")
    print(f"MID (Oct 30 - Dec 17):   {results.get('mid', 0):,} records")
    print(f"BOD (Oct 28 - Dec 17):   {results.get('bod', 0):,} records")
    print(f"\nCompleted: {datetime.now()}")
    print("=" * 80)
