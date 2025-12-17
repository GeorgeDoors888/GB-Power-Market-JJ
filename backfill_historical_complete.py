#!/usr/bin/env python3
"""
Comprehensive Historical Data Backfill Script
Backfills bmrs_freq, bmrs_mid, and bmrs_bod with proper datetime handling
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
from typing import List, Dict
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

client = bigquery.Client(project=PROJECT_ID, location="US")

def parse_datetime(dt_string: str):
    """Convert ISO 8601 datetime string to Python datetime object"""
    if not dt_string:
        return None
    # Remove 'Z' and parse
    dt_str = dt_string.rstrip('Z')
    try:
        return pd.to_datetime(dt_str)
    except:
        return None

def fetch_freq_data(from_date: datetime, to_date: datetime) -> pd.DataFrame:
    """Fetch FREQ data from Elexon API and return as DataFrame"""
    url = f"{API_BASE}/datasets/FREQ"
    params = {
        'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }
    
    print(f"  Fetching FREQ: {from_date} to {to_date}")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    
    data = response.json()
    records = data.get('data', [])
    
    if not records:
        print(f"    No data returned")
        return pd.DataFrame()
    
    # Convert to DataFrame and parse datetimes
    df = pd.DataFrame(records)
    if 'measurementTime' in df.columns:
        df['measurementTime'] = df['measurementTime'].apply(parse_datetime)
    
    print(f"    Retrieved {len(df)} FREQ records")
    return df

def fetch_mid_data(from_date: datetime, to_date: datetime) -> pd.DataFrame:
    """Fetch MID data from Elexon API and return as DataFrame"""
    url = f"{API_BASE}/datasets/MID"
    params = {
        'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }
    
    print(f"  Fetching MID: {from_date} to {to_date}")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    
    data = response.json()
    records = data.get('data', [])
    
    if not records:
        print(f"    No data returned")
        return pd.DataFrame()
    
    # Convert to DataFrame and parse datetimes
    df = pd.DataFrame(records)
    for field in ['settlementDate', 'publishTime']:
        if field in df.columns:
            df[field] = df[field].apply(parse_datetime)
    
    print(f"    Retrieved {len(df)} MID records")
    return df

def fetch_bod_data(from_date: datetime, to_date: datetime) -> pd.DataFrame:
    """Fetch BOD data from Elexon API and return as DataFrame"""
    url = f"{API_BASE}/datasets/BOD"
    params = {
        'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }
    
    print(f"  Fetching BOD: {from_date} to {to_date}")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    
    data = response.json()
    records = data.get('data', [])
    
    if not records:
        print(f"    No data returned")
        return pd.DataFrame()
    
    # Convert to DataFrame and parse datetimes
    df = pd.DataFrame(records)
    for field in ['settlementDate', 'timeFrom', 'timeTo', 'publishTime']:
        if field in df.columns:
            df[field] = df[field].apply(parse_datetime)
    
    print(f"    Retrieved {len(df)} BOD records")
    return df

def upload_to_bigquery(table_name: str, df: pd.DataFrame, date_str: str):
    """Upload DataFrame to BigQuery table"""
    if df.empty:
        print(f"    No data to upload for {date_str}")
        return False
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    
    print(f"  Uploading {len(df)} rows to {table_name}...")
    
    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        print(f"    ✅ Uploaded {len(df)} rows successfully")
        return True
        
    except Exception as e:
        print(f"    ⚠️ Error for {date_str}: {str(e)[:200]}")
        return False

def backfill_freq(start_date: datetime, end_date: datetime):
    """Backfill FREQ data in weekly batches"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_freq")
    print("="*80)
    
    current = start_date
    success_count = 0
    error_count = 0
    
    while current < end_date:
        batch_end = min(current + timedelta(days=7), end_date)
        
        try:
            df = fetch_freq_data(current, batch_end)
            if upload_to_bigquery('bmrs_freq', df, current.strftime('%Y-%m-%d')):
                success_count += 1
            else:
                error_count += 1
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  ❌ Failed for {current}: {str(e)[:200]}")
            error_count += 1
        
        current = batch_end
    
    print(f"\nFREQ Backfill Complete: {success_count} batches succeeded, {error_count} failed")

def backfill_mid(start_date: datetime, end_date: datetime):
    """Backfill MID data in weekly batches"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_mid")
    print("="*80)
    
    current = start_date
    success_count = 0
    error_count = 0
    
    while current < end_date:
        batch_end = min(current + timedelta(days=7), end_date)
        
        try:
            df = fetch_mid_data(current, batch_end)
            if upload_to_bigquery('bmrs_mid', df, current.strftime('%Y-%m-%d')):
                success_count += 1
            else:
                error_count += 1
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  ❌ Failed for {current}: {str(e)[:200]}")
            error_count += 1
        
        current = batch_end
    
    print(f"\nMID Backfill Complete: {success_count} batches succeeded, {error_count} failed")

def backfill_bod(start_date: datetime, end_date: datetime):
    """Backfill BOD data in daily batches (large dataset)"""
    print("\n" + "="*80)
    print("BACKFILLING bmrs_bod (daily batches - large dataset)")
    print("="*80)
    
    current = start_date
    success_count = 0
    error_count = 0
    
    while current < end_date:
        batch_end = min(current + timedelta(days=1), end_date)
        
        try:
            df = fetch_bod_data(current, batch_end)
            if upload_to_bigquery('bmrs_bod', df, current.strftime('%Y-%m-%d')):
                success_count += 1
            else:
                error_count += 1
            time.sleep(2)  # More conservative rate limiting for large dataset
            
        except Exception as e:
            print(f"  ❌ Failed for {current}: {str(e)[:200]}")
            error_count += 1
        
        current = batch_end
    
    print(f"\nBOD Backfill Complete: {success_count} batches succeeded, {error_count} failed")

if __name__ == "__main__":
    print("GB Power Market - Comprehensive Historical Backfill")
    print("="*80)
    
    # FREQ: Backfill from 2022-01-01 to 2025-10-27 (before IRIS starts Oct 28)
    print("\n[1/3] FREQ: 2022-01-01 to 2025-10-27 (before IRIS)")
    backfill_freq(
        datetime(2022, 1, 1),
        datetime(2025, 10, 28)
    )
    
    # MID: Backfill gap from Oct 31 to Dec 17
    print("\n[2/3] MID: 2025-10-31 to 2025-12-17 (gap fill)")
    backfill_mid(
        datetime(2025, 10, 31),
        datetime(2025, 12, 18)
    )
    
    # BOD: Backfill gap from Oct 29 to Dec 17
    print("\n[3/3] BOD: 2025-10-29 to 2025-12-17 (gap fill)")
    backfill_bod(
        datetime(2025, 10, 29),
        datetime(2025, 12, 18)
    )
    
    print("\n" + "="*80)
    print("✅ All backfill operations complete!")
    print("="*80)
