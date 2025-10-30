#!/usr/bin/env python3
"""
Test: Re-download Sep-Oct 2025 to Europe West 2 dataset
Purpose: 
1. Verify download speed with EU region
2. Confirm record counts match US region
3. Test as baseline before Jan-Aug download
"""

# FIX SSL CERTIFICATE ISSUE FIRST!
import os
import certifi
from pathlib import Path

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(Path(__file__).parent / 'jibber_jabber_key.json')

import httpx
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import json
from typing import List, Dict, Any, Generator
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod_eu"  # NEW EU dataset
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

# Test period: September 1 - October 26, 2025 (same as before)
START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2025, 10, 26, 23, 59, 59)

# Streaming configuration
BATCH_SIZE = 50000
LARGE_DATASETS = ["PN", "QPN", "BOALF", "MELS", "MILS", "BOD"]

# Load manifest
MANIFEST_FILE = Path(__file__).parent / "insights_manifest_dynamic.json"
with open(MANIFEST_FILE) as f:
    manifest_data = json.load(f)

print(f"🌍 TEST: Sep-Oct 2025 → Europe West 2 Dataset")
print(f"Period: {START_DATE.date()} to {END_DATE.date()}")
print(f"Duration: 56 days")
print(f"Datasets: {len(manifest_data.get('datasets', {}))}")
print(f"Target: {DATASET_ID} (europe-west2)")
print("="*80)
print()

start_time = time.time()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_data(url: str, params: Dict[str, Any]) -> List[Dict]:
    """Fetch data from API with retries."""
    response = httpx.get(url, params=params, timeout=60.0)
    response.raise_for_status()
    return response.json()


def get_date_chunks(start_date: datetime, end_date: datetime, days_per_chunk: int = 7) -> List[tuple]:
    """Split date range into chunks."""
    chunks = []
    current = start_date
    
    while current < end_date:
        chunk_end = min(current + timedelta(days=days_per_chunk), end_date)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(seconds=1)
    
    return chunks


def stream_upload_to_bigquery(records_generator: Generator, table_name: str, bq_client: bigquery.Client) -> int:
    """Stream records to BigQuery in batches."""
    total_records = 0
    batch = []
    import sys
    
    for record in records_generator:
        batch.append(record)
        
        if len(batch) >= BATCH_SIZE:
            errors = bq_client.insert_rows_json(table_name, batch)
            if errors:
                print(f"      ⚠️  Batch upload errors: {errors[:3]}", flush=True)
                sys.stdout.flush()
            
            total_records += len(batch)
            print(f"      📤 Uploaded {total_records:,} records... [{datetime.now().strftime('%H:%M:%S')}]", flush=True)
            sys.stdout.flush()
            batch = []
    
    # Upload remaining
    if batch:
        errors = bq_client.insert_rows_json(table_name, batch)
        if errors:
            print(f"      ⚠️  Final batch errors: {errors[:3]}", flush=True)
            sys.stdout.flush()
        total_records += len(batch)
    
    return total_records


def fetch_records_generator(url: str, max_hours: int = None, max_days: int = 7) -> Generator[Dict, None, None]:
    """Generator that yields records one at a time."""
    if max_hours:
        # Hourly chunks for MELS/MILS
        current = START_DATE
        while current < END_DATE:
            chunk_end = min(current + timedelta(hours=max_hours), END_DATE)
            
            params = {
                "from": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "format": "json"
            }
            
            try:
                records = fetch_data(url, params)
                for record in records:
                    yield record
            except Exception as e:
                print(f"      ⚠️  Error: {e}")
            
            current = chunk_end + timedelta(seconds=1)
            time.sleep(0.1)  # Optimized delay
    else:
        # Daily/weekly chunks
        chunks = get_date_chunks(START_DATE, END_DATE, max_days)
        
        for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
            params = {
                "from": chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "format": "json"
            }
            
            try:
                records = fetch_data(url, params)
                for record in records:
                    yield record
                
                if i % 2 == 0:
                    import sys
                    print(f"      Progress: {i}/{len(chunks)} chunks, {len(list(generator))} records...", flush=True)
                    sys.stdout.flush()
            except Exception as e:
                print(f"      ⚠️  Error in chunk {i}: {e}")
            
            time.sleep(0.1)  # Optimized delay


def download_dataset(dataset_code: str, dataset_config: Dict, bq_client: bigquery.Client) -> Dict:
    """Download a single dataset to EU region."""
    
    route = dataset_config.get("route", "")
    if not route:
        return {"status": "error", "error": "No route specified"}
    
    url = f"{API_BASE}{route}"
    table_name = f"{DATASET_ID}.{dataset_code.lower()}_sep_oct_2025_eu"
    
    special_config = dataset_config.get("special_config", {})
    max_hours = special_config.get("max_hours")
    max_days = special_config.get("max_days", 7)
    
    use_streaming = dataset_code in LARGE_DATASETS
    
    import sys
    print(f"  📦 Dataset: {dataset_code} - Starting at {datetime.now().strftime('%H:%M:%S')}", flush=True)
    sys.stdout.flush()
    if use_streaming:
        print(f"    💾 Using STREAMING upload", flush=True)
        sys.stdout.flush()
    
    try:
        dataset_start = time.time()
        
        if max_hours:
            total_hours = int((END_DATE - START_DATE).total_seconds() / 3600)
            print(f"    ⚠️  Hourly chunks: {total_hours} API calls", flush=True)
            import sys
            sys.stdout.flush()
        else:
            chunks = get_date_chunks(START_DATE, END_DATE, max_days)
            print(f"    📦 {len(chunks)} chunks of ~{max_days} days each", flush=True)
            import sys
            sys.stdout.flush()
        
        if use_streaming:
            records_gen = fetch_records_generator(url, max_hours, max_days)
            total_records = stream_upload_to_bigquery(records_gen, table_name, bq_client)
            
            if total_records == 0:
                return {"status": "no_data", "records": 0}
            
            elapsed = time.time() - dataset_start
            
            return {
                "status": "success",
                "records": total_records,
                "table": table_name,
                "method": "streaming",
                "duration_seconds": elapsed,
                "records_per_second": total_records / elapsed if elapsed > 0 else 0
            }
        else:
            all_records = []
            
            if max_hours:
                current = START_DATE
                while current < END_DATE:
                    chunk_end = min(current + timedelta(hours=max_hours), END_DATE)
                    params = {
                        "from": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "to": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "format": "json"
                    }
                    
                    try:
                        records = fetch_data(url, params)
                        all_records.extend(records)
                    except Exception as e:
                        print(f"      ⚠️  Error: {e}")
                    
                    current = chunk_end + timedelta(seconds=1)
                    time.sleep(0.1)
            else:
                chunks = get_date_chunks(START_DATE, END_DATE, max_days)
                
                for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
                    params = {
                        "from": chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "to": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "format": "json"
                    }
                    
                    try:
                        records = fetch_data(url, params)
                        all_records.extend(records)
                        
                        if i % 2 == 0:
                            print(f"      Progress: {i}/{len(chunks)} chunks, {len(all_records):,} records...")
                    except Exception as e:
                        print(f"      ⚠️  Error: {e}")
                    
                    time.sleep(0.1)
            
            if not all_records:
                return {"status": "no_data", "records": 0}
            
            # Upload to BigQuery
            df = pd.DataFrame(all_records)
            job = bq_client.load_table_from_dataframe(df, table_name)
            job.result()
            
            elapsed = time.time() - dataset_start
            
            return {
                "status": "success",
                "records": len(all_records),
                "table": table_name,
                "method": "standard",
                "duration_seconds": elapsed,
                "records_per_second": len(all_records) / elapsed if elapsed > 0 else 0
            }
            
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    """Main function."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # Select a few key datasets for testing
    test_datasets = [
        "FUELINST", "FREQ", "INDGEN", "INDDEM",  # Fast datasets
        "PN", "QPN",  # Large datasets with streaming
        "MELS", "MILS",  # Hourly chunk datasets
        "BOD",  # Very large dataset
    ]
    
    results = {
        "successful": 0,
        "failed": 0,
        "no_data": 0,
        "total_records": 0,
        "total_duration": 0,
    }
    
    detailed_results = []
    
    for dataset_code in test_datasets:
        if dataset_code not in manifest_data.get("datasets", {}):
            print(f"⚠️  {dataset_code} not in manifest, skipping...")
            continue
        
        dataset_config = manifest_data["datasets"][dataset_code]
        
        print(f"\n{'='*80}")
        print(f"Downloading: {dataset_code}")
        print(f"{'='*80}")
        
        result = download_dataset(dataset_code, dataset_config, bq_client)
        result["dataset"] = dataset_code
        
        detailed_results.append(result)
        
        if result["status"] == "success":
            results["successful"] += 1
            results["total_records"] += result["records"]
            results["total_duration"] += result.get("duration_seconds", 0)
            print(f"  ✅ Success: {result['records']:,} records in {result.get('duration_seconds', 0):.1f}s ({result.get('records_per_second', 0):.0f} rec/s)")
        elif result["status"] == "no_data":
            results["no_data"] += 1
            print(f"  ⚠️  No data available")
        else:
            results["failed"] += 1
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
    
    total_elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("📊 TEST RESULTS - EU REGION DOWNLOAD")
    print("="*80)
    total = results["successful"] + results["failed"] + results["no_data"]
    print(f"✅ Successful: {results['successful']}/{total}")
    print(f"❌ Failed: {results['failed']}/{total}")
    print(f"⚠️  No Data: {results['no_data']}/{total}")
    print(f"📊 Total Records: {results['total_records']:,}")
    print(f"⏱️  Total Time: {total_elapsed/60:.1f} minutes")
    print(f"⚡ Overall Speed: {results['total_records']/total_elapsed:.0f} records/second")
    print("="*80)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"sep_oct_2025_eu_test_{timestamp}.json"
    
    with open(results_file, "w") as f:
        json.dump({
            "region": "europe-west2",
            "dataset": DATASET_ID,
            "period": f"{START_DATE.date()} to {END_DATE.date()}",
            "summary": results,
            "detailed_results": detailed_results,
            "total_elapsed_minutes": total_elapsed / 60,
            "downloaded_at": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ EU region test complete!")
    print("\nNext step: Compare with US region and download Jan-Aug to verify record density!")


if __name__ == "__main__":
    main()
