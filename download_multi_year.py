#!/usr/bin/env python3
"""
Download ALL Elexon BMRS data for multiple years (2022-2025)
Uses the dynamically discovered manifest with all 44 verified datasets
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
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

# Year configurations
YEARS = {
    2025: {"start": datetime(2025, 1, 1), "end": datetime(2025, 10, 26, 23, 59, 59)},
    2024: {"start": datetime(2024, 1, 1), "end": datetime(2024, 12, 31, 23, 59, 59)},
    2023: {"start": datetime(2023, 1, 1), "end": datetime(2023, 12, 31, 23, 59, 59)},
    2022: {"start": datetime(2022, 1, 1), "end": datetime(2022, 12, 31, 23, 59, 59)},
}

# Load the dynamically discovered manifest
MANIFEST_FILE = Path(__file__).parent / "insights_manifest_dynamic.json"
if not MANIFEST_FILE.exists():
    print(f"❌ Dynamic manifest not found: {MANIFEST_FILE}")
    print("Please run: discover_all_datasets_dynamic.py first")
    sys.exit(1)

with open(MANIFEST_FILE) as f:
    manifest_data = json.load(f)

print(f"📊 Loaded manifest with {len(manifest_data.get('datasets', {}))} datasets")
print(f"Discovery date: {manifest_data.get('discovered_at', 'unknown')}")
print()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_data(url: str, params: Dict[str, Any]) -> List[Dict]:
    """Fetch data from API with retries."""
    response = httpx.get(url, params=params, timeout=120)
    
    if response.status_code == 200:
        data = response.json()
        # Handle both list and dict responses
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('data', [])
        else:
            return []
    elif response.status_code == 400:
        # May need shorter date range
        error_msg = response.text[:200]
        raise Exception(f"400 Bad Request - may need shorter range: {error_msg}")
    else:
        response.raise_for_status()
    
    return []


def get_date_chunks(start_date: datetime, end_date: datetime, days_per_chunk: int = 30) -> List[tuple]:
    """Split date range into chunks."""
    chunks = []
    current = start_date
    
    while current < end_date:
        chunk_end = min(current + timedelta(days=days_per_chunk), end_date)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(seconds=1)
    
    return chunks


def download_dataset_for_year(dataset_code: str, dataset_config: Dict, year: int, bq_client: bigquery.Client) -> Dict:
    """Download a single dataset for a specific year."""
    
    year_config = YEARS[year]
    start_date = year_config["start"]
    end_date = year_config["end"]
    
    route = dataset_config.get("route", "")
    if not route:
        return {"status": "error", "error": "No route specified"}
    
    url = f"{API_BASE}{route}"
    table_name = dataset_config.get("bq_table", f"{DATASET_ID}.{dataset_code.lower()}")
    
    # Handle special configurations
    special_config = dataset_config.get("special_config", {})
    max_hours = special_config.get("max_hours")
    max_days = special_config.get("max_days", 30)  # Default 30 days per chunk
    
    print(f"  📅 Year {year}: {start_date.date()} to {end_date.date()}")
    
    all_records = []
    
    try:
        if max_hours:
            # Need hourly chunks (MELS, MILS)
            print(f"    ⚠️  Hourly chunks required (max {max_hours} hour)")
            total_hours = int((end_date - start_date).total_seconds() / 3600)
            
            if total_hours > 2000:
                print(f"    ⚠️  {total_hours} hours = {total_hours} API calls - this will take a while!")
                response = input(f"    Continue with {dataset_code} for {year}? (y/n): ")
                if response.lower() != 'y':
                    return {"status": "skipped", "reason": "User skipped due to too many API calls"}
            
            current = start_date
            hour_count = 0
            
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
                    hour_count += 1
                    
                    if hour_count % 100 == 0:
                        print(f"      Progress: {hour_count}/{total_hours} hours, {len(all_records)} records")
                    
                except Exception as e:
                    print(f"      ⚠️  Error at hour {hour_count}: {e}")
                
                current = chunk_end + timedelta(seconds=1)
                time.sleep(0.1)  # Rate limiting
        
        else:
            # Daily/weekly chunks
            chunks = get_date_chunks(start_date, end_date, max_days)
            print(f"    📦 {len(chunks)} chunks of ~{max_days} days each")
            
            for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
                params = {
                    "from": chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "to": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "format": "json"
                }
                
                try:
                    records = fetch_data(url, params)
                    all_records.extend(records)
                    
                    if i % 5 == 0:
                        print(f"      Progress: {i}/{len(chunks)} chunks, {len(all_records)} records")
                    
                except Exception as e:
                    print(f"      ⚠️  Error in chunk {i}: {e}")
                    if "400" in str(e) and max_days > 1:
                        print(f"      🔄 Retrying with shorter chunks...")
                        # Retry this chunk with shorter range
                        shorter_chunks = get_date_chunks(chunk_start, chunk_end, max(1, max_days // 7))
                        for sc_start, sc_end in shorter_chunks:
                            try:
                                params["from"] = sc_start.strftime("%Y-%m-%dT%H:%M:%SZ")
                                params["to"] = sc_end.strftime("%Y-%m-%dT%H:%M:%SZ")
                                records = fetch_data(url, params)
                                all_records.extend(records)
                            except Exception as e2:
                                print(f"        ⚠️  Still failing: {e2}")
                
                time.sleep(0.2)  # Rate limiting
        
        if not all_records:
            return {"status": "no_data", "records": 0}
        
        # Upload to BigQuery
        df = pd.DataFrame(all_records)
        
        # Create table name with year suffix
        table_parts = table_name.split('.')
        table_with_year = f"{table_parts[0]}.{table_parts[1]}_{year}"
        
        print(f"    📤 Uploading {len(df)} records to {table_with_year}")
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True
        )
        
        job = bq_client.load_table_from_dataframe(df, table_with_year, job_config=job_config)
        job.result()
        
        return {
            "status": "success",
            "records": len(df),
            "table": table_with_year,
            "year": year
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "year": year
        }


def main():
    """Main download orchestrator."""
    
    # Get year to download
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
        if year not in YEARS:
            print(f"❌ Invalid year: {year}")
            print(f"Valid years: {list(YEARS.keys())}")
            sys.exit(1)
        years_to_download = [year]
    else:
        # Ask user which years to download
        print("Which years do you want to download?")
        print("1. 2025 only")
        print("2. 2024 only")
        print("3. 2023 only")
        print("4. 2022 only")
        print("5. All years (2022-2025)")
        print("6. Custom selection")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            years_to_download = [2025]
        elif choice == "2":
            years_to_download = [2024]
        elif choice == "3":
            years_to_download = [2023]
        elif choice == "4":
            years_to_download = [2022]
        elif choice == "5":
            years_to_download = [2025, 2024, 2023, 2022]
        elif choice == "6":
            years_input = input("Enter years (comma-separated, e.g., 2024,2023): ").strip()
            years_to_download = [int(y.strip()) for y in years_input.split(",")]
        else:
            print("Invalid choice")
            sys.exit(1)
    
    print("\n" + "="*80)
    print(f"🚀 MULTI-YEAR DATA DOWNLOAD")
    print("="*80)
    print(f"Years to download: {years_to_download}")
    print(f"Datasets per year: {len(manifest_data.get('datasets', {}))}")
    print(f"Total downloads: {len(years_to_download) * len(manifest_data.get('datasets', {}))}")
    print("="*80)
    print()
    
    # Initialize BigQuery client
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # Track results
    results = {year: {"successful": 0, "failed": 0, "skipped": 0, "no_data": 0, "total_records": 0} for year in years_to_download}
    detailed_results = []
    
    # Download each dataset for each year
    datasets = manifest_data.get("datasets", {})
    
    for dataset_code, dataset_config in datasets.items():
        print(f"\n{'='*80}")
        print(f"📊 Dataset: {dataset_code} - {dataset_config.get('name', 'Unknown')}")
        print(f"{'='*80}")
        
        for year in years_to_download:
            result = download_dataset_for_year(dataset_code, dataset_config, year, bq_client)
            
            result["dataset"] = dataset_code
            result["year"] = year
            detailed_results.append(result)
            
            if result["status"] == "success":
                results[year]["successful"] += 1
                results[year]["total_records"] += result.get("records", 0)
                print(f"    ✅ {result['records']} records")
            elif result["status"] == "skipped":
                results[year]["skipped"] += 1
                print(f"    ⏭️  Skipped: {result.get('reason', 'Unknown')}")
            elif result["status"] == "no_data":
                results[year]["no_data"] += 1
                print(f"    ⚠️  No data available")
            else:
                results[year]["failed"] += 1
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 DOWNLOAD SUMMARY")
    print("="*80)
    
    for year in years_to_download:
        stats = results[year]
        total = stats["successful"] + stats["failed"] + stats["skipped"] + stats["no_data"]
        
        print(f"\n📅 Year {year}:")
        print(f"  ✅ Successful: {stats['successful']}/{total}")
        print(f"  ❌ Failed: {stats['failed']}/{total}")
        print(f"  ⏭️  Skipped: {stats['skipped']}/{total}")
        print(f"  ⚠️  No Data: {stats['no_data']}/{total}")
        print(f"  📊 Total Records: {stats['total_records']:,}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"multi_year_download_results_{timestamp}.json"
    
    with open(results_file, "w") as f:
        json.dump({
            "years": years_to_download,
            "summary": results,
            "detailed_results": detailed_results,
            "downloaded_at": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    print("\n✅ Download complete!")


if __name__ == "__main__":
    main()
