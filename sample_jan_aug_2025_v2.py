#!/usr/bin/env python3
"""
Jan-Aug 2025 Sampling Script (Simplified & Robust)
Purpose: Test the claim that Jan-Aug has ~300k records/day vs Sep-Oct's 648k/day

Strategy:
- Download 1 week (7 days) from each month Jan-Aug
- 8 months × 7 days = 56 days total (same as Sep-Oct period!)
- Calculate records/day for each month
- Compare with Sep-Oct's 648,828 records/day baseline
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
from google.cloud.exceptions import NotFound
import json
from typing import List, Dict
import time
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"  # Using working US region
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
BATCH_SIZE = 50000

# Sample periods: First week of each month (Jan-Aug 2025)
SAMPLE_PERIODS = [
    ("january", 2025, 1, 1, 7),   # month, year, start_day, days_count
    ("february", 2025, 2, 1, 7),
    ("march", 2025, 3, 1, 7),
    ("april", 2025, 4, 1, 7),
    ("may", 2025, 5, 1, 7),
    ("june", 2025, 6, 1, 7),
    ("july", 2025, 7, 1, 7),
    ("august", 2025, 8, 1, 7),
]

# Simplified dataset list - test with key datasets first
KEY_DATASETS = [
    ("PN", "Physical Notifications", "datasets/PN"),
    ("BOD", "Bid Offer Data", "datasets/BOD"),
    ("FREQ", "System Frequency", "datasets/FREQ"),
    ("INDOD", "Indicated Generation", "datasets/INDOD"),
    ("FUELHH", "Fuel Type Generation", "datasets/FUELHH"),
    ("B1610", "Actual Generation", "datasets/B1610"),
    ("DETSYSPRICES", "System Prices", "datasets/DETSYSPRICES"),
    ("DISBSAD", "Balancing Services", "datasets/DISBSAD"),
]


def fetch_data_chunked(url: str, start_date: datetime, end_date: datetime, max_chunk_days: int = 3) -> List[Dict]:
    """Fetch data in chunks to avoid timeouts."""
    all_records = []
    current = start_date
    
    while current < end_date:
        chunk_end = min(current + timedelta(days=max_chunk_days), end_date)
        
        params = {
            "from": current.strftime("%Y-%m-%dT00:00:00Z"),
            "to": chunk_end.strftime("%Y-%m-%dT23:59:59Z"),
            "format": "json"
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                records = data.get("data", [])
                all_records.extend(records)
                time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"        ⚠️  Chunk error ({current.date()} to {chunk_end.date()}): {e}", flush=True)
        
        current = chunk_end
    
    return all_records


def upload_to_bigquery(records: List[Dict], table_id: str, client: bigquery.Client) -> int:
    """Upload records to BigQuery using streaming insert."""
    if not records:
        return 0
    
    # Ensure table exists
    try:
        client.get_table(table_id)
    except NotFound:
        print(f"        ⚠️  Table {table_id} not found, skipping", flush=True)
        return 0
    
    # Upload in batches
    total_uploaded = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        
        errors = client.insert_rows_json(table_id, batch)
        if errors:
            print(f"        ⚠️  Upload errors: {errors[:2]}", flush=True)
        else:
            total_uploaded += len(batch)
            if total_uploaded % 100000 == 0:
                print(f"        📤 {total_uploaded:,} records uploaded... [{datetime.now().strftime('%H:%M:%S')}]", flush=True)
    
    return total_uploaded


def process_dataset(dataset_code: str, dataset_name: str, endpoint: str,
                   month_name: str, year: int, month: int, start_day: int, days: int,
                   client: bigquery.Client) -> Dict:
    """Process one dataset for one month sample."""
    
    start_date = datetime(year, month, start_day)
    end_date = start_date + timedelta(days=days)
    
    # Construct table name
    table_name = f"{dataset_code.lower()}_sample_{month_name}_{year}"
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    print(f"  📦 {dataset_code}...", end=" ", flush=True)
    start_time = time.time()
    
    try:
        # Fetch data
        url = f"{API_BASE}/{endpoint}"
        records = fetch_data_chunked(url, start_date, end_date, max_chunk_days=3)
        
        if not records:
            print("⚠️  No data", flush=True)
            return {
                "dataset": dataset_code,
                "month": month_name,
                "records": 0,
                "duration": time.time() - start_time,
                "status": "no_data"
            }
        
        # Upload to BigQuery
        uploaded = upload_to_bigquery(records, table_id, client)
        duration = time.time() - start_time
        
        print(f"✅ {uploaded:,} records in {duration:.1f}s", flush=True)
        
        return {
            "dataset": dataset_code,
            "month": month_name,
            "records": uploaded,
            "duration": duration,
            "status": "success"
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Error: {str(e)[:100]}", flush=True)
        return {
            "dataset": dataset_code,
            "month": month_name,
            "records": 0,
            "duration": duration,
            "status": f"error: {str(e)[:100]}"
        }


def main():
    """Main sampling function."""
    
    print("=" * 80)
    print("🧪 JAN-AUG 2025 SAMPLING TEST (Simplified)")
    print("=" * 80)
    print()
    print("Purpose: Verify record density claim")
    print("  Baseline: Sep-Oct 2025 = 648,828 records/day")
    print("  Claim: Jan-Aug 2025 = ~300k records/day")
    print()
    print(f"Strategy: Download 1 week from each month (56 days total)")
    print(f"Datasets: {len(KEY_DATASETS)} key datasets")
    print("=" * 80)
    print()
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✅ Connected to BigQuery project: {PROJECT_ID}")
        print(f"✅ Using dataset: {DATASET_ID}")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to BigQuery: {e}")
        return
    
    all_results = []
    monthly_totals = {}
    
    # Process each month
    for month_name, year, month, start_day, days in SAMPLE_PERIODS:
        print(f"\n{'=' * 80}")
        print(f"📅 MONTH: {month_name.title()} {year} (Days {start_day} - {start_day + days - 1})")
        print(f"{'=' * 80}\n")
        
        month_records = 0
        month_start = time.time()
        
        # Process each dataset for this month
        for dataset_code, dataset_name, endpoint in KEY_DATASETS:
            result = process_dataset(
                dataset_code, dataset_name, endpoint,
                month_name, year, month, start_day, days,
                client
            )
            all_results.append(result)
            month_records += result["records"]
        
        month_duration = time.time() - month_start
        monthly_totals[month_name] = {
            "records": month_records,
            "duration": month_duration,
            "records_per_day": month_records / days
        }
        
        print(f"\n  📊 {month_name.title()} Total: {month_records:,} records in {month_duration:.1f}s")
        print(f"  📈 Average: {month_records / days:,.0f} records/day")
    
    # Final analysis
    print(f"\n{'=' * 80}")
    print("📊 SAMPLING ANALYSIS")
    print(f"{'=' * 80}\n")
    
    total_records = sum(m["records"] for m in monthly_totals.values())
    total_days = 56  # 7 days × 8 months
    avg_per_day = total_records / total_days
    
    print("Monthly Breakdown:")
    for month_name in [m[0] for m in SAMPLE_PERIODS]:
        stats = monthly_totals[month_name]
        print(f"  {month_name.title():10} {stats['records']:>12,} records  ({stats['records_per_day']:>8,.0f}/day)")
    
    print(f"\n{'=' * 80}")
    print(f"Total Sample: {total_records:,} records over {total_days} days")
    print(f"Average: {avg_per_day:,.0f} records/day")
    print()
    print(f"Sep-Oct Baseline: 648,828 records/day")
    print(f"Jan-Aug Sample:   {avg_per_day:,.0f} records/day")
    ratio = avg_per_day / 648828
    print(f"Ratio: {ratio:.2f}x")
    print()
    
    if ratio < 0.6:
        print("✅ CLAIM VALIDATED: Jan-Aug has significantly less data")
        print(f"   Full Jan-Aug download estimated: ~40-60 minutes")
    elif ratio > 0.9:
        print("❌ CLAIM REJECTED: Jan-Aug has similar data density")
        print(f"   Full Jan-Aug download estimated: ~90-120 minutes")
    else:
        print("⚠️  MIXED RESULTS: Jan-Aug has moderately less data")
        print(f"   Full Jan-Aug download estimated: ~60-90 minutes")
    
    print(f"{'=' * 80}\n")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"jan_aug_sampling_results_{timestamp}.json"
    
    output = {
        "test_date": timestamp,
        "total_records": total_records,
        "total_days": total_days,
        "avg_records_per_day": avg_per_day,
        "baseline_records_per_day": 648828,
        "ratio": ratio,
        "monthly_totals": monthly_totals,
        "all_results": all_results
    }
    
    with open(results_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"💾 Results saved to: {results_file}")


if __name__ == "__main__":
    main()
