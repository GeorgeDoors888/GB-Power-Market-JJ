#!/usr/bin/env python3
"""
Quick test: Download September and October 2025 data only
"""

import httpx
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
from pathlib import Path
import json
from typing import List, Dict, Any, Generator
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

# Test period: September 1 - October 26, 2025
START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2025, 10, 26, 23, 59, 59)

# Streaming configuration
BATCH_SIZE = 50000
LARGE_DATASETS = ["PN", "QPN", "BOALF", "MELS", "MILS"]

# Load manifest
MANIFEST_FILE = Path(__file__).parent / "insights_manifest_dynamic.json"
with open(MANIFEST_FILE) as f:
    manifest_data = json.load(f)

print(f"📊 TEST DOWNLOAD: September & October 2025")
print(f"Period: {START_DATE.date()} to {END_DATE.date()}")
print(f"Duration: 56 days")
print(f"Datasets: {len(manifest_data.get('datasets', {}))}")
print("="*80)
print()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_data(url: str, params: Dict[str, Any]) -> List[Dict]:
    """Fetch data from API with retries."""
    response = httpx.get(url, params=params, timeout=120)
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('data', [])
        else:
            return []
    elif response.status_code == 400:
        error_msg = response.text[:200]
        raise Exception(f"400 Bad Request - may need shorter range: {error_msg}")
    else:
        response.raise_for_status()
    
    return []


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
    total_uploaded = 0
    batch = []
    first_batch = True
    
    for record in records_generator:
        batch.append(record)
        
        if len(batch) >= BATCH_SIZE:
            df = pd.DataFrame(batch)
            
            if first_batch:
                job_config = bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                    autodetect=True
                )
                first_batch = False
            else:
                job_config = bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                    autodetect=True
                )
            
            job = bq_client.load_table_from_dataframe(df, table_name, job_config=job_config)
            job.result()
            
            total_uploaded += len(batch)
            print(f"      📤 Uploaded batch: {total_uploaded:,} records so far...")
            batch = []
    
    # Upload final batch
    if batch:
        df = pd.DataFrame(batch)
        
        if first_batch:
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                autodetect=True
            )
        else:
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                autodetect=True
            )
        
        job = bq_client.load_table_from_dataframe(df, table_name, job_config=job_config)
        job.result()
        total_uploaded += len(batch)
    
    return total_uploaded


def fetch_records_generator(url: str, max_hours: int = None, max_days: int = 7) -> Generator[Dict, None, None]:
    """Generator that yields records one at a time."""
    if max_hours:
        # Hourly chunks
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
            time.sleep(0.1)
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
                    print(f"      Progress: {i}/{len(chunks)} chunks processed...")
            except Exception as e:
                print(f"      ⚠️  Error in chunk {i}: {e}")
            
            time.sleep(0.2)


def download_dataset(dataset_code: str, dataset_config: Dict, bq_client: bigquery.Client) -> Dict:
    """Download a single dataset."""
    
    route = dataset_config.get("route", "")
    if not route:
        return {"status": "error", "error": "No route specified"}
    
    url = f"{API_BASE}{route}"
    table_name = dataset_config.get("bq_table", f"{DATASET_ID}.{dataset_code.lower()}")
    
    # Add test suffix
    table_parts = table_name.split('.')
    table_with_suffix = f"{table_parts[0]}.{table_parts[1]}_sep_oct_2025"
    
    special_config = dataset_config.get("special_config", {})
    max_hours = special_config.get("max_hours")
    max_days = special_config.get("max_days", 7)
    
    use_streaming = dataset_code in LARGE_DATASETS
    
    print(f"  📦 Dataset: {dataset_code}")
    if use_streaming:
        print(f"    💾 Using STREAMING upload")
    
    try:
        if max_hours:
            total_hours = int((END_DATE - START_DATE).total_seconds() / 3600)
            print(f"    ⚠️  Hourly chunks: {total_hours} API calls")
        else:
            chunks = get_date_chunks(START_DATE, END_DATE, max_days)
            print(f"    📦 {len(chunks)} chunks of ~{max_days} days each")
        
        if use_streaming:
            records_gen = fetch_records_generator(url, max_hours, max_days)
            total_records = stream_upload_to_bigquery(records_gen, table_with_suffix, bq_client)
            
            if total_records == 0:
                return {"status": "no_data", "records": 0}
            
            return {
                "status": "success",
                "records": total_records,
                "table": table_with_suffix,
                "method": "streaming"
            }
        else:
            all_records = []
            records_gen = fetch_records_generator(url, max_hours, max_days)
            
            for record in records_gen:
                all_records.append(record)
            
            if not all_records:
                return {"status": "no_data", "records": 0}
            
            df = pd.DataFrame(all_records)
            print(f"    📤 Uploading {len(df):,} records to {table_with_suffix}")
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                autodetect=True
            )
            
            job = bq_client.load_table_from_dataframe(df, table_with_suffix, job_config=job_config)
            job.result()
            
            return {
                "status": "success",
                "records": len(df),
                "table": table_with_suffix,
                "method": "standard"
            }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def main():
    """Main function."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    results = {"successful": 0, "failed": 0, "no_data": 0, "total_records": 0}
    detailed_results = []
    
    datasets = manifest_data.get("datasets", {})
    
    for dataset_code, dataset_config in datasets.items():
        print(f"\n{'='*80}")
        result = download_dataset(dataset_code, dataset_config, bq_client)
        
        result["dataset"] = dataset_code
        detailed_results.append(result)
        
        if result["status"] == "success":
            results["successful"] += 1
            results["total_records"] += result.get("records", 0)
            method = result.get("method", "unknown")
            print(f"  ✅ {result['records']:,} records ({method})")
        elif result["status"] == "no_data":
            results["no_data"] += 1
            print(f"  ⚠️  No data available")
        else:
            results["failed"] += 1
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80)
    print("📊 TEST DOWNLOAD SUMMARY")
    print("="*80)
    total = results["successful"] + results["failed"] + results["no_data"]
    print(f"✅ Successful: {results['successful']}/{total}")
    print(f"❌ Failed: {results['failed']}/{total}")
    print(f"⚠️  No Data: {results['no_data']}/{total}")
    print(f"📊 Total Records: {results['total_records']:,}")
    print("="*80)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"sep_oct_2025_test_results_{timestamp}.json"
    
    with open(results_file, "w") as f:
        json.dump({
            "period": f"{START_DATE.date()} to {END_DATE.date()}",
            "summary": results,
            "detailed_results": detailed_results,
            "downloaded_at": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ Test download complete!")


if __name__ == "__main__":
    main()
