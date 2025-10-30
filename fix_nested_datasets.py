#!/usr/bin/env python3
"""
Fix and download the 3 datasets with nested JSON structures:
1. GENERATION_ACTUAL_PER_TYPE
2. GENERATION_OUTTURN  
3. DISBSAD
"""

import httpx
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import json

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_data(url, params):
    """Fetch data from API with retry logic"""
    client = httpx.Client(timeout=60.0)
    try:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    finally:
        client.close()

def flatten_generation_actual_per_type(data_list):
    """
    Flatten nested 'data' field in GENERATION_ACTUAL_PER_TYPE
    
    Input:
      [{"startTime": "...", "settlementPeriod": 1, "data": [{"psrType": "WIND", "quantity": 100}, ...]}]
    
    Output:
      [{"startTime": "...", "settlementPeriod": 1, "psrType": "WIND", "quantity": 100, ...}, ...]
    """
    flattened = []
    
    for record in data_list:
        base_fields = {
            'startTime': record.get('startTime'),
            'settlementPeriod': record.get('settlementPeriod')
        }
        
        # Flatten nested 'data' array
        nested_data = record.get('data', [])
        if isinstance(nested_data, list):
            for item in nested_data:
                flat_record = {**base_fields, **item}
                flattened.append(flat_record)
        else:
            # If data is not a list, keep original record
            flattened.append(record)
    
    return flattened

def flatten_generation_outturn(data_list):
    """
    Flatten nested 'data' field in GENERATION_OUTTURN
    Same structure as GENERATION_ACTUAL_PER_TYPE
    """
    return flatten_generation_actual_per_type(data_list)

def fix_disbsad_types(df):
    """
    Fix DISBSAD data type issues
    - Convert isTendered to string to avoid pyarrow errors
    - Ensure proper types for other fields
    """
    if 'isTendered' in df.columns:
        # Convert to string explicitly
        df['isTendered'] = df['isTendered'].astype(str)
    
    # Fix other potential type issues
    if 'soFlag' in df.columns:
        df['soFlag'] = df['soFlag'].astype(bool)
    if 'storFlag' in df.columns:
        df['storFlag'] = df['storFlag'].astype(bool)
    
    return df

def upload_to_bigquery(df, table_name):
    """Upload dataframe to BigQuery"""
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace existing data
        autodetect=True
    )
    
    print(f"  📤 Uploading {len(df)} rows to {table_name}...")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    print(f"  ✅ Successfully uploaded {len(df)} rows")
    
    return table_id

def download_generation_actual_per_type(start_date, end_date):
    """Download and fix GENERATION_ACTUAL_PER_TYPE"""
    print("\n" + "="*80)
    print("1. GENERATION_ACTUAL_PER_TYPE")
    print("="*80)
    
    url = f"{BASE_URL}/generation/actual/per-type"
    params = {
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
        "format": "json"
    }
    
    print(f"  📥 Fetching from: {url}")
    print(f"  📅 Date range: {params['from']} to {params['to']}")
    
    response = fetch_data(url, params)
    
    if isinstance(response, dict) and 'data' in response:
        data_list = response['data']
    else:
        data_list = response
    
    print(f"  📊 Retrieved {len(data_list)} records")
    print(f"  🔧 Flattening nested 'data' field...")
    
    flattened = flatten_generation_actual_per_type(data_list)
    print(f"  ✨ Flattened to {len(flattened)} rows")
    
    if flattened:
        df = pd.DataFrame(flattened)
        print(f"  📋 Columns: {list(df.columns)}")
        table_id = upload_to_bigquery(df, "generation_actual_per_type_fixed")
        return df
    else:
        print(f"  ⚠️  No data to upload")
        return None

def download_generation_outturn(start_date, end_date):
    """Download and fix GENERATION_OUTTURN"""
    print("\n" + "="*80)
    print("2. GENERATION_OUTTURN")
    print("="*80)
    
    url = f"{BASE_URL}/generation/outturn/summary"
    params = {
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
        "format": "json"
    }
    
    print(f"  📥 Fetching from: {url}")
    print(f"  📅 Date range: {params['from']} to {params['to']}")
    
    response = fetch_data(url, params)
    
    # This endpoint returns direct list
    if isinstance(response, list):
        data_list = response
    elif isinstance(response, dict) and 'data' in response:
        data_list = response['data']
    else:
        data_list = response
    
    print(f"  📊 Retrieved {len(data_list)} records")
    print(f"  🔧 Flattening nested 'data' field...")
    
    flattened = flatten_generation_outturn(data_list)
    print(f"  ✨ Flattened to {len(flattened)} rows")
    
    if flattened:
        df = pd.DataFrame(flattened)
        print(f"  📋 Columns: {list(df.columns)}")
        table_id = upload_to_bigquery(df, "generation_outturn_fixed")
        return df
    else:
        print(f"  ⚠️  No data to upload")
        return None

def download_disbsad(start_date, end_date):
    """Download and fix DISBSAD"""
    print("\n" + "="*80)
    print("3. DISBSAD (Balancing Services Adjustment Data)")
    print("="*80)
    
    url = f"{BASE_URL}/datasets/DISBSAD/stream"
    params = {
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
        "format": "json"
    }
    
    print(f"  📥 Fetching from: {url}")
    print(f"  📅 Date range: {params['from']} to {params['to']}")
    
    response = fetch_data(url, params)
    
    # This endpoint returns direct list
    if isinstance(response, list):
        data_list = response
    elif isinstance(response, dict) and 'data' in response:
        data_list = response['data']
    else:
        data_list = response
    
    print(f"  📊 Retrieved {len(data_list)} records")
    
    if data_list:
        df = pd.DataFrame(data_list)
        print(f"  📋 Original columns: {list(df.columns)}")
        print(f"  🔧 Fixing data types...")
        
        df = fix_disbsad_types(df)
        print(f"  ✨ Fixed! Data types: {df.dtypes.to_dict()}")
        
        table_id = upload_to_bigquery(df, "disbsad_fixed")
        return df
    else:
        print(f"  ⚠️  No data to upload")
        return None

def main():
    print("="*80)
    print("🔧 FIXING 3 RECOVERABLE DATASETS WITH NESTED STRUCTURES")
    print("="*80)
    
    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"\n📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"🎯 Target Project: {PROJECT_ID}")
    print(f"🗄️  Target Dataset: {DATASET_ID}")
    
    results = {}
    
    # Fix each dataset
    try:
        results['generation_actual_per_type'] = download_generation_actual_per_type(start_date, end_date)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        results['generation_actual_per_type'] = None
    
    try:
        results['generation_outturn'] = download_generation_outturn(start_date, end_date)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        results['generation_outturn'] = None
    
    try:
        results['disbsad'] = download_disbsad(start_date, end_date)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        results['disbsad'] = None
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    success_count = sum(1 for v in results.values() if v is not None)
    total_rows = sum(len(v) for v in results.values() if v is not None)
    
    print(f"\n✅ Successfully fixed: {success_count}/3 datasets")
    print(f"📈 Total rows added: {total_rows:,}")
    
    for name, df in results.items():
        if df is not None:
            print(f"   ✓ {name}: {len(df):,} rows")
        else:
            print(f"   ✗ {name}: Failed")
    
    print("\n🎉 Done! Check BigQuery for new tables:")
    print(f"   • {DATASET_ID}.generation_actual_per_type_fixed")
    print(f"   • {DATASET_ID}.generation_outturn_fixed")
    print(f"   • {DATASET_ID}.disbsad_fixed")

if __name__ == "__main__":
    main()
