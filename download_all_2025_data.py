#!/usr/bin/env python3
"""
Download all Elexon BMRS data for 2025 (January 1 - October 26)
This is a comprehensive download covering ~300 days of data.
"""

import httpx
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
from pathlib import Path
import json
from typing import List, Dict, Any
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

# Date range for 2025
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 10, 26, 23, 59, 59)
TOTAL_DAYS = (END_DATE - START_DATE).days + 1

print(f"Downloading data from {START_DATE.date()} to {END_DATE.date()}")
print(f"Total days: {TOTAL_DAYS}")

# Load manifest
MANIFEST_FILE = Path(__file__).parent / "insights_manifest_comprehensive.json"
with open(MANIFEST_FILE) as f:
    manifest_data = json.load(f)

# Convert manifest datasets to list format
MANIFEST_DATASETS = []
for key, value in manifest_data.get("datasets", {}).items():
    dataset_config = {
        "name": value.get("bq_table", "").split(".")[-1] if "." in value.get("bq_table", "") else key.lower(),
        "description": value.get("name", key),
        "endpoint": value.get("route", ""),
        "category": value.get("category", "unknown")
    }
    # Pass through special configurations like date_format
    if "date_format" in value:
        dataset_config["date_format"] = value["date_format"]
    MANIFEST_DATASETS.append(dataset_config)

# Add recovered datasets to manifest
RECOVERED_DATASETS = [
    {
        "name": "balancing_acceptances",
        "description": "Bid Offer Acceptance Level Flagged (BOALF)",
        "endpoint": "/datasets/BOALF",
        "category": "balancing",
        "max_days_per_request": 1
    },
    {
        "name": "balancing_nonbm_volumes",
        "description": "Balancing Services Volume (QAS)",
        "endpoint": "/datasets/QAS",
        "category": "balancing",
        "max_days_per_request": 1
    },
    {
        "name": "balancing_dynamic_sel",
        "description": "Stable Export Limit (SEL)",
        "endpoint": "/datasets/SEL",
        "category": "balancing",
        "max_days_per_request": 7
    },
    {
        "name": "balancing_physical_mels",
        "description": "Maximum Export Limit (MELS)",
        "endpoint": "/datasets/MELS",
        "category": "balancing",
        "max_hours_per_request": 1
    },
    {
        "name": "balancing_physical_mils",
        "description": "Maximum Import Limit (MILS)",
        "endpoint": "/datasets/MILS",
        "category": "balancing",
        "max_hours_per_request": 1
    },
]

# Combine all datasets
all_datasets = MANIFEST_DATASETS + RECOVERED_DATASETS

print(f"Total datasets to download: {len(all_datasets)}")
print()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_data(url: str, params: Dict[str, Any]) -> List[Dict]:
    """Fetch data from API with retries."""
    response = httpx.get(url, params=params, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict):
            return data.get('data', [data])
        elif isinstance(data, list):
            return data
        return []
    elif response.status_code == 404:
        return []
    elif response.status_code == 400:
        error = response.json()
        print(f"    ⚠ 400 Error: {error.get('errors', {})}")
        return []
    else:
        response.raise_for_status()
        return []


def download_dataset_chunked(dataset: Dict[str, Any]) -> pd.DataFrame:
    """Download a dataset with appropriate chunking."""
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset['name']}")
    print(f"Description: {dataset['description']}")
    print(f"{'='*60}")
    
    all_data = []
    
    # Check if this endpoint requires date-only format
    use_date_only = dataset.get('date_format') == 'date_only'
    
    # Determine chunk size
    if 'max_hours_per_request' in dataset:
        # Hour-by-hour chunking (MELS, MILS)
        chunk_hours = dataset['max_hours_per_request']
        total_chunks = TOTAL_DAYS * 24 // chunk_hours
        chunk_delta = timedelta(hours=chunk_hours)
        print(f"⚠️  High-frequency dataset: {total_chunks} chunks required")
        print(f"   This will take approximately {total_chunks * 0.5 / 60:.1f} minutes")
        
        user_confirm = input(f"   Continue with {dataset['name']}? (y/n): ")
        if user_confirm.lower() != 'y':
            print(f"   Skipped {dataset['name']}")
            return pd.DataFrame()
            
    elif 'max_days_per_request' in dataset:
        # Day-by-day or week-by-week chunking
        chunk_days = dataset['max_days_per_request']
        total_chunks = (TOTAL_DAYS + chunk_days - 1) // chunk_days
        chunk_delta = timedelta(days=chunk_days)
        print(f"Chunk size: {chunk_days} days ({total_chunks} chunks)")
    else:
        # Default: 7-day chunks
        chunk_days = 7
        total_chunks = (TOTAL_DAYS + chunk_days - 1) // chunk_days
        chunk_delta = timedelta(days=chunk_days)
        print(f"Chunk size: {chunk_days} days ({total_chunks} chunks)")
    
    # Download chunks
    current_start = START_DATE
    chunk_num = 0
    
    while current_start < END_DATE:
        chunk_num += 1
        current_end = min(current_start + chunk_delta, END_DATE)
        
        if chunk_num % 10 == 0 or chunk_num == 1:
            print(f"  Chunk {chunk_num}/{total_chunks}: {current_start.date()} to {current_end.date()}")
        
        url = f"{API_BASE}{dataset['endpoint']}"
        
        # Use date-only format for endpoints that require it
        if use_date_only:
            params = {
                'from': current_start.strftime('%Y-%m-%d'),
                'to': current_end.strftime('%Y-%m-%d'),
            }
        else:
            params = {
                'from': current_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'to': current_end.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'format': 'json'
            }
        
        try:
            data = fetch_data(url, params)
            if data:
                all_data.extend(data)
                if chunk_num % 10 == 0:
                    print(f"    ✓ Progress: {len(all_data):,} rows")
        except Exception as e:
            print(f"    ⚠ Error: {str(e)[:60]}")
        
        current_start = current_end
        
        # Rate limiting
        if chunk_num % 10 == 0:
            time.sleep(1)
        else:
            time.sleep(0.2)
    
    if not all_data:
        print(f"  ⚠ No data fetched")
        return pd.DataFrame()
    
    print(f"  ✓ Total records: {len(all_data):,}")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    df['dataset_name'] = dataset['name']
    df['category'] = dataset['category']
    df['downloaded_at'] = datetime.now().isoformat()
    
    return df


def upload_to_bigquery(df: pd.DataFrame, table_name: str):
    """Upload DataFrame to BigQuery."""
    if df.empty:
        print(f"  ⚠ Skipping upload (no data)")
        return
    
    print(f"  Uploading to BigQuery...")
    print(f"    Rows: {len(df):,}")
    print(f"    Size: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        table = client.get_table(table_id)
        print(f"  ✓ Uploaded {table.num_rows:,} rows to {table_name}")
        
    except Exception as e:
        print(f"  ✗ Upload error: {e}")
        raise


def main():
    """Main execution."""
    print("="*60)
    print("ELEXON BMRS DATA - FULL 2025 DOWNLOAD")
    print("="*60)
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Total days: {TOTAL_DAYS}")
    print(f"Datasets: {len(all_datasets)}")
    print(f"Target: {PROJECT_ID}.{DATASET_ID}")
    print()
    
    print("⚠️  WARNING: This will download ~300 days of data")
    print("   Estimated time: 2-3 hours for all datasets")
    print("   High-frequency datasets (MELS/MILS) will require confirmation")
    print()
    
    proceed = input("Proceed with full 2025 download? (y/n): ")
    if proceed.lower() != 'y':
        print("Download cancelled")
        return
    
    results = []
    start_time = time.time()
    
    for i, dataset in enumerate(all_datasets, 1):
        print(f"\n[{i}/{len(all_datasets)}]")
        
        try:
            df = download_dataset_chunked(dataset)
            
            if not df.empty:
                upload_to_bigquery(df, dataset['name'])
                results.append({
                    'name': dataset['name'],
                    'status': 'success',
                    'rows': len(df),
                    'size_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
                })
            else:
                results.append({
                    'name': dataset['name'],
                    'status': 'no_data',
                    'rows': 0
                })
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Download interrupted by user")
            break
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                'name': dataset['name'],
                'status': 'error',
                'error': str(e)[:100]
            })
    
    elapsed_time = time.time() - start_time
    
    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    
    successful = [r for r in results if r['status'] == 'success']
    no_data = [r for r in results if r['status'] == 'no_data']
    failed = [r for r in results if r['status'] == 'error']
    
    print(f"Completed: {len(results)}/{len(all_datasets)} datasets")
    print(f"Successful: {len(successful)}")
    print(f"No data: {len(no_data)}")
    print(f"Failed: {len(failed)}")
    print(f"Time elapsed: {elapsed_time / 3600:.2f} hours")
    
    if successful:
        total_rows = sum(r['rows'] for r in successful)
        total_mb = sum(r.get('size_mb', 0) for r in successful)
        print(f"\nTotal rows downloaded: {total_rows:,}")
        print(f"Total data size: {total_mb / 1024:.2f} GB")
        
        print("\nTop 10 datasets by size:")
        sorted_results = sorted(successful, key=lambda x: x['rows'], reverse=True)[:10]
        for r in sorted_results:
            print(f"  {r['name']}: {r['rows']:,} rows ({r.get('size_mb', 0):.1f} MB)")
    
    if failed:
        print(f"\nFailed datasets:")
        for r in failed:
            print(f"  ✗ {r['name']}: {r.get('error', 'Unknown error')}")
    
    # Save results
    results_file = Path(__file__).parent / "download_2025_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'downloaded_at': datetime.now().isoformat(),
            'date_range': {
                'from': START_DATE.isoformat(),
                'to': END_DATE.isoformat(),
                'days': TOTAL_DAYS
            },
            'elapsed_hours': elapsed_time / 3600,
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print("\n✅ Download complete!")


if __name__ == "__main__":
    main()
