#!/usr/bin/env python3
"""
Download recovered datasets that require special handling
After API research, found these datasets ARE available but need specific constraints:
- BOALF: 1-day max range
- QAS (NONBM_VOLUMES): 1-day max range  
- MELS: 1-hour max range
- MILS: 1-hour max range
- SEL (Dynamic): 7-day range works
"""

import httpx
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
from pathlib import Path
import json
from typing import List, Dict, Any
import time

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
DAYS_TO_DOWNLOAD = 7

# Datasets to recover with their constraints
DATASETS = [
    {
        "name": "balancing_acceptances",
        "description": "Bid Offer Acceptance Level Flagged (BOALF)",
        "endpoint": "/datasets/BOALF",
        "max_hours": 24,  # 1 day max
        "category": "balancing"
    },
    {
        "name": "balancing_nonbm_volumes",
        "description": "Balancing Services Volume (QAS)",
        "endpoint": "/datasets/QAS",
        "max_hours": 24,  # 1 day max
        "category": "balancing"
    },
    {
        "name": "balancing_dynamic_sel",
        "description": "Stable Export Limit (SEL)",
        "endpoint": "/datasets/SEL",
        "max_hours": 24 * 7,  # 7 days works
        "category": "balancing"
    },
    {
        "name": "balancing_physical_mels",
        "description": "Maximum Export Limit (MELS)",
        "endpoint": "/datasets/MELS",
        "max_hours": 1,  # 1 hour max - high frequency
        "category": "balancing"
    },
    {
        "name": "balancing_physical_mils",
        "description": "Maximum Import Limit (MILS)",
        "endpoint": "/datasets/MILS",
        "max_hours": 1,  # 1 hour max - high frequency
        "category": "balancing"
    },
]


def fetch_data_with_retries(url: str, params: Dict[str, Any], max_retries: int = 3) -> List[Dict]:
    """Fetch data from API with retries."""
    for attempt in range(max_retries):
        try:
            response = httpx.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict):
                    if 'data' in data:
                        return data['data']
                    else:
                        return [data]
                elif isinstance(data, list):
                    return data
                else:
                    print(f"  ⚠ Unknown response format: {type(data)}")
                    return []
            
            elif response.status_code == 404:
                print(f"  ✗ 404 Not Found")
                return []
            
            elif response.status_code == 400:
                error = response.json()
                print(f"  ✗ 400 Validation Error: {error.get('errors', {})}")
                return []
            
            else:
                print(f"  ⚠ Status {response.status_code}, retrying...")
                time.sleep(2 ** attempt)
                
        except Exception as e:
            print(f"  ⚠ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return []


def download_dataset(dataset: Dict[str, Any], end_date: datetime, total_days: int) -> pd.DataFrame:
    """Download a dataset with appropriate time chunking."""
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset['name']}")
    print(f"Description: {dataset['description']}")
    print(f"Max chunk size: {dataset['max_hours']} hours")
    print(f"{'='*60}")
    
    all_data = []
    chunk_size = timedelta(hours=dataset['max_hours'])
    
    # Calculate number of chunks needed
    total_hours = total_days * 24
    num_chunks = (total_hours + dataset['max_hours'] - 1) // dataset['max_hours']
    
    print(f"Will fetch {num_chunks} chunks to cover {total_days} days")
    
    # Work backwards from end_date
    current_end = end_date
    
    for chunk_num in range(num_chunks):
        current_start = current_end - chunk_size
        
        # Don't go before the target start date
        target_start = end_date - timedelta(days=total_days)
        if current_start < target_start:
            current_start = target_start
        
        print(f"\nChunk {chunk_num + 1}/{num_chunks}: {current_start.date()} to {current_end.date()}")
        
        url = f"{API_BASE}{dataset['endpoint']}"
        params = {
            'from': current_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to': current_end.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'format': 'json'
        }
        
        data = fetch_data_with_retries(url, params)
        
        if data:
            all_data.extend(data)
            print(f"  ✓ Fetched {len(data)} records (total: {len(all_data)})")
        else:
            print(f"  ⚠ No data returned")
        
        # Move to next chunk
        current_end = current_start
        
        # Stop if we've reached the start date
        if current_end <= target_start:
            break
        
        # Rate limiting
        time.sleep(0.5)
    
    if not all_data:
        print(f"\n⚠ No data fetched for {dataset['name']}")
        return pd.DataFrame()
    
    print(f"\n✓ Total records fetched: {len(all_data)}")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    # Add metadata
    df['dataset_name'] = dataset['name']
    df['category'] = dataset['category']
    df['downloaded_at'] = datetime.now().isoformat()
    
    return df


def upload_to_bigquery(df: pd.DataFrame, table_name: str):
    """Upload DataFrame to BigQuery."""
    if df.empty:
        print(f"⚠ Skipping upload for {table_name} (no data)")
        return
    
    print(f"\nUploading to BigQuery: {PROJECT_ID}.{DATASET_ID}.{table_name}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Size: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        table = client.get_table(table_id)
        print(f"✓ Loaded {table.num_rows} rows into {table_id}")
        
    except Exception as e:
        print(f"✗ Error uploading to BigQuery: {e}")
        raise


def main():
    """Main execution."""
    print("="*60)
    print("RECOVERED DATASETS DOWNLOADER")
    print("="*60)
    print(f"Date range: Last {DAYS_TO_DOWNLOAD} days")
    print(f"Target: {PROJECT_ID}.{DATASET_ID}")
    print(f"Datasets to download: {len(DATASETS)}")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_TO_DOWNLOAD)
    
    print(f"From: {start_date.date()}")
    print(f"To: {end_date.date()}")
    
    results = []
    
    for dataset in DATASETS:
        try:
            df = download_dataset(dataset, end_date, DAYS_TO_DOWNLOAD)
            
            if not df.empty:
                upload_to_bigquery(df, dataset['name'])
                results.append({
                    'name': dataset['name'],
                    'status': 'success',
                    'rows': len(df)
                })
            else:
                results.append({
                    'name': dataset['name'],
                    'status': 'no_data',
                    'rows': 0
                })
                
        except Exception as e:
            print(f"\n✗ Error processing {dataset['name']}: {e}")
            results.append({
                'name': dataset['name'],
                'status': 'error',
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful = [r for r in results if r['status'] == 'success']
    no_data = [r for r in results if r['status'] == 'no_data']
    failed = [r for r in results if r['status'] == 'error']
    
    print(f"Successful: {len(successful)}/{len(DATASETS)}")
    for r in successful:
        print(f"  ✓ {r['name']}: {r['rows']:,} rows")
    
    if no_data:
        print(f"\nNo data: {len(no_data)}")
        for r in no_data:
            print(f"  ⚠ {r['name']}")
    
    if failed:
        print(f"\nFailed: {len(failed)}")
        for r in failed:
            print(f"  ✗ {r['name']}: {r.get('error', 'Unknown error')}")
    
    total_rows = sum(r.get('rows', 0) for r in successful)
    print(f"\nTotal new rows: {total_rows:,}")
    
    # Save results
    results_file = Path(__file__).parent / "recovered_datasets_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'downloaded_at': datetime.now().isoformat(),
            'date_range': {
                'from': start_date.isoformat(),
                'to': end_date.isoformat()
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
