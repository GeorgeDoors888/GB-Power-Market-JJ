#!/usr/bin/env python3
"""
Jan-Aug 2025 Sampling Script
Purpose: Test the claim that Jan-Aug has ~300k records/day vs Sep-Oct's 648k/day

Strategy:
- Download 1 week (7 days) from each month Jan-Aug
- 8 months × 7 days = 56 days total (same as Sep-Oct period!)
- Calculate records/day for each month
- Compare with Sep-Oct's 648,828 records/day baseline

This will prove or disprove the seasonal data density theory!
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
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"  # Using working US region
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

# Sample periods: First week of each month (Jan-Aug 2025)
SAMPLE_PERIODS = [
    ("January", datetime(2025, 1, 1), datetime(2025, 1, 7, 23, 59, 59)),
    ("February", datetime(2025, 2, 1), datetime(2025, 2, 7, 23, 59, 59)),
    ("March", datetime(2025, 3, 1), datetime(2025, 3, 7, 23, 59, 59)),
    ("April", datetime(2025, 4, 1), datetime(2025, 4, 7, 23, 59, 59)),
    ("May", datetime(2025, 5, 1), datetime(2025, 5, 7, 23, 59, 59)),
    ("June", datetime(2025, 6, 1), datetime(2025, 6, 7, 23, 59, 59)),
    ("July", datetime(2025, 7, 1), datetime(2025, 7, 7, 23, 59, 59)),
    ("August", datetime(2025, 8, 1), datetime(2025, 8, 7, 23, 59, 59)),
]

# Test with ALL 44 datasets for complete comparison
BATCH_SIZE = 50000
LARGE_DATASETS = ["PN", "QPN", "BOD", "MELS", "MILS"]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def fetch_data(url: str, params: Dict) -> List[Dict]:
    """Fetch data from API with retries."""
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])


def get_date_chunks(start: datetime, end: datetime, max_days: int = 7) -> List[tuple]:
    """Split date range into chunks."""
    chunks = []
    current = start
    
    while current < end:
        chunk_end = min(current + timedelta(days=max_days), end)
        chunks.append((current, chunk_end))
        current = chunk_end
    
    return chunks


def stream_upload_to_bigquery(records_generator: Generator, table_name: str, bq_client: bigquery.Client) -> int:
    """Stream records to BigQuery in batches."""
    total_records = 0
    batch = []
    
    for record in records_generator:
        batch.append(record)
        
        if len(batch) >= BATCH_SIZE:
            errors = bq_client.insert_rows_json(table_name, batch)
            if errors:
                print(f"        ⚠️  Batch upload errors: {errors[:3]}", flush=True)
                sys.stdout.flush()
            
            total_records += len(batch)
            if total_records % 100000 == 0:
                print(f"        📤 Uploaded {total_records:,} records... [{datetime.now().strftime('%H:%M:%S')}]", flush=True)
                sys.stdout.flush()
            batch = []
    
    # Upload remaining
    if batch:
        errors = bq_client.insert_rows_json(table_name, batch)
        if errors:
            print(f"        ⚠️  Final batch errors: {errors[:3]}", flush=True)
            sys.stdout.flush()
        total_records += len(batch)
    
    return total_records


def fetch_records_generator(url: str, start_date: datetime, end_date: datetime, 
                            max_hours: int = None, max_days: int = 7) -> Generator[Dict, None, None]:
    """Generator that yields records one at a time."""
    if max_hours:
        # Hourly chunks for MELS/MILS
        current = start_date
        while current < end_date:
            chunk_end = min(current + timedelta(hours=max_hours), end_date)
            
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
                print(f"        ⚠️  Error in hourly chunk: {e}", flush=True)
                sys.stdout.flush()
            
            current = chunk_end
            time.sleep(0.1)
    else:
        # Day chunks for other datasets
        chunks = get_date_chunks(start_date, end_date, max_days)
        
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
            except Exception as e:
                print(f"        ⚠️  Error in chunk {i}: {e}", flush=True)
                sys.stdout.flush()
            
            time.sleep(0.1)


def download_dataset_sample(dataset_code: str, dataset_config: Dict, month_name: str,
                            start_date: datetime, end_date: datetime, bq_client: bigquery.Client) -> Dict:
    """Download a single dataset sample for one month."""
    
    route = dataset_config.get("route", "")
    if not route:
        return {"status": "error", "error": "No route specified", "records": 0}
    
    url = f"{API_BASE}{route}"
    table_name = f"{DATASET_ID}.{dataset_code.lower()}_sample_{month_name.lower()}_2025"
    
    special_config = dataset_config.get("special_config", {})
    max_hours = special_config.get("max_hours")
    max_days = special_config.get("max_days", 7)
    
    use_streaming = dataset_code in LARGE_DATASETS
    
    try:
        dataset_start = time.time()
        
        # Fetch data
        if use_streaming:
            # Streaming for large datasets
            records_gen = fetch_records_generator(url, start_date, end_date, max_hours, max_days)
            record_count = stream_upload_to_bigquery(records_gen, table_name, bq_client)
        else:
            # Standard upload for smaller datasets
            all_records = []
            
            if max_hours:
                current = start_date
                while current < end_date:
                    chunk_end = min(current + timedelta(hours=max_hours), end_date)
                    params = {
                        "from": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "to": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "format": "json"
                    }
                    try:
                        records = fetch_data(url, params)
                        all_records.extend(records)
                    except Exception as e:
                        print(f"        ⚠️  Error: {e}", flush=True)
                    current = chunk_end
                    time.sleep(0.1)
            else:
                chunks = get_date_chunks(start_date, end_date, max_days)
                for chunk_start, chunk_end in chunks:
                    params = {
                        "from": chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "to": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "format": "json"
                    }
                    try:
                        records = fetch_data(url, params)
                        all_records.extend(records)
                    except Exception as e:
                        print(f"        ⚠️  Error: {e}", flush=True)
                    time.sleep(0.1)
            
            record_count = len(all_records)
            
            if record_count > 0:
                df = pd.DataFrame(all_records)
                job_config = bigquery.LoadJobConfig(write_disposition='WRITE_TRUNCATE')
                job = bq_client.load_table_from_dataframe(df, table_name, job_config=job_config)
                job.result()
        
        duration = time.time() - dataset_start
        
        if record_count > 0:
            return {
                "status": "success",
                "records": record_count,
                "duration_seconds": duration,
                "records_per_second": record_count / duration if duration > 0 else 0
            }
        else:
            return {"status": "no_data", "records": 0}
            
    except Exception as e:
        return {"status": "error", "error": str(e), "records": 0}


def main():
    print("=" * 80)
    print("🧪 JAN-AUG 2025 SAMPLING TEST")
    print("=" * 80)
    print()
    print("Purpose: Verify record density claim")
    print(f"  Baseline: Sep-Oct 2025 = 648,828 records/day")
    print(f"  Claim: Jan-Aug 2025 = ~300k records/day")
    print()
    print("Strategy: Download 1 week from each month (56 days total)")
    print("=" * 80)
    print()
    
    # Load manifest
    with open("insights_manifest_complete.json", "r") as f:
        manifest_data = json.load(f)
    
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    all_results = []
    monthly_totals = {}
    
    # Download samples for each month
    for month_name, start_date, end_date in SAMPLE_PERIODS:
        print(f"\n{'=' * 80}")
        print(f"📅 MONTH: {month_name} 2025 (Week 1: {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})")
        print(f"{'=' * 80}\n")
        
        month_records = 0
        month_start = time.time()
        
        for dataset_code in manifest_data.get("datasets", {}).keys():
            dataset_config = manifest_data["datasets"][dataset_code]
            
            print(f"  📦 {dataset_code}...", end=" ", flush=True)
            sys.stdout.flush()
            
            result = download_dataset_sample(
                dataset_code, dataset_config, month_name,
                start_date, end_date, bq_client
            )
            
            if result["status"] == "success":
                month_records += result["records"]
                print(f"✅ {result['records']:,} records", flush=True)
            elif result["status"] == "no_data":
                print(f"⚠️  No data", flush=True)
            else:
                print(f"❌ {result.get('error', 'Failed')}", flush=True)
            
            sys.stdout.flush()
        
        month_duration = time.time() - month_start
        records_per_day = month_records / 7  # 7 days per sample
        
        monthly_totals[month_name] = {
            "total_records": month_records,
            "records_per_day": records_per_day,
            "duration_seconds": month_duration
        }
        
        print(f"\n  📊 {month_name} Summary:")
        print(f"     Total: {month_records:,} records in 7 days")
        print(f"     Average: {records_per_day:,.0f} records/day")
        print(f"     Time: {month_duration:.1f}s")
    
    # Final analysis
    print(f"\n{'=' * 80}")
    print(f"📊 FINAL ANALYSIS - JAN-AUG 2025 SAMPLING")
    print(f"{'=' * 80}\n")
    
    total_records = sum(m["total_records"] for m in monthly_totals.values())
    total_days = 56  # 8 months × 7 days
    avg_records_per_day = total_records / total_days
    
    print(f"Sample Period: 56 days (7 days × 8 months)")
    print(f"Total Records: {total_records:,}")
    print(f"Average: {avg_records_per_day:,.0f} records/day")
    print()
    
    print(f"Monthly Breakdown:")
    for month_name, stats in monthly_totals.items():
        print(f"  {month_name:10} {stats['records_per_day']:>10,.0f} rec/day")
    
    print()
    print(f"{'=' * 80}")
    print(f"COMPARISON WITH SEP-OCT:")
    print(f"{'=' * 80}")
    
    sep_oct_avg = 648_828
    ratio = avg_records_per_day / sep_oct_avg
    
    print(f"  Sep-Oct 2025: {sep_oct_avg:,} records/day (baseline)")
    print(f"  Jan-Aug 2025: {avg_records_per_day:,.0f} records/day (sampled)")
    print(f"  Ratio: {ratio:.2f}x")
    print()
    
    if ratio < 0.6:
        print(f"  ✅ CLAIM VALIDATED: Jan-Aug has significantly less data!")
        print(f"     Jan-Aug is {(1-ratio)*100:.0f}% less dense than Sep-Oct")
        estimated_jan_aug_download = (240 * avg_records_per_day) / 5058 / 60
        print(f"     Estimated full Jan-Aug download: {estimated_jan_aug_download:.0f} minutes")
    elif ratio > 0.9:
        print(f"  ❌ CLAIM REJECTED: Jan-Aug has similar data density!")
        print(f"     Download will take longer than estimated")
        estimated_jan_aug_download = (240 * avg_records_per_day) / 5058 / 60
        print(f"     Revised Jan-Aug download estimate: {estimated_jan_aug_download:.0f} minutes")
    else:
        print(f"  ⚠️  MIXED RESULTS: Moderate difference detected")
        estimated_jan_aug_download = (240 * avg_records_per_day) / 5058 / 60
        print(f"     Estimated Jan-Aug download: {estimated_jan_aug_download:.0f} minutes")
    
    print(f"{'=' * 80}")
    
    # Save results
    results_file = f"jan_aug_sampling_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump({
            "monthly_totals": monthly_totals,
            "total_records": total_records,
            "total_days": total_days,
            "avg_records_per_day": avg_records_per_day,
            "sep_oct_baseline": sep_oct_avg,
            "ratio": ratio,
            "timestamp": str(datetime.now())
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ Sampling test complete!")


if __name__ == "__main__":
    main()
