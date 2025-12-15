#!/usr/bin/env python3
"""
Batch ingest 3 years of BOAV + EBOCF data (2022-2025)
Processes data month-by-month to avoid memory issues and provide progress updates.

Estimated time: ~18 hours for 3 years at 100 requests/min
(1095 days × 96 requests/day ÷ 100 requests/min ÷ 60 min/hr)

Usage:
    python3 ingest_bm_3years.py --start 2022-01-01 --end 2025-12-13
    python3 ingest_bm_3years.py --year 2024  # Single year
    
Author: George Major
Date: December 14, 2025
"""

import sys
import argparse
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import subprocess
import time

def get_month_ranges(start_date, end_date):
    """Generate list of month ranges between start and end dates."""
    ranges = []
    current = start_date.replace(day=1)  # Start of first month
    
    while current <= end_date:
        # Last day of current month or end_date, whichever is earlier
        next_month = current + relativedelta(months=1)
        month_end = min(next_month - timedelta(days=1), end_date)
        
        ranges.append((current, month_end))
        current = next_month
    
    return ranges

def ingest_month(start_date, end_date):
    """Ingest a single month of data."""
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    days = (end_date - start_date).days + 1
    
    print(f"\n{'='*80}")
    print(f"📅 INGESTING: {start_str} to {end_str} ({days} days)")
    print(f"{'='*80}")
    
    # Run ingestion script
    cmd = [
        'python3',
        'ingest_bm_settlement_data.py',
        '--start', start_str,
        '--end', end_str
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        print(f"✅ Completed {start_str} to {end_str} in {elapsed/60:.1f} minutes")
        
        # Extract record counts from output if available
        if "Uploaded" in result.stdout:
            print(result.stdout.split('\n')[-5:])
        
        return True
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed {start_str} to {end_str} after {elapsed/60:.1f} minutes")
        print(f"Error: {e.stderr[-500:]}")  # Last 500 chars of error
        return False

def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description='Batch ingest 3 years of BOAV + EBOCF data')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)', default='2022-01-01')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)', default='2025-12-13')
    parser.add_argument('--year', type=int, help='Ingest single year (2022-2025)')
    
    args = parser.parse_args()
    
    # Determine date range
    if args.year:
        start_date = date(args.year, 1, 1)
        end_date = date(args.year, 12, 31)
        if args.year == 2025:
            end_date = date.today() - timedelta(days=1)  # Yesterday
    else:
        start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end, '%Y-%m-%d').date()
    
    print("=" * 80)
    print("🔋 BM SETTLEMENT DATA BATCH INGESTION")
    print("=" * 80)
    print(f"Date Range: {start_date} to {end_date}")
    
    total_days = (end_date - start_date).days + 1
    print(f"Total Days: {total_days:,}")
    print(f"Estimated API Calls: {total_days * 96:,} (96 per day)")
    print(f"Estimated Time: {total_days * 96 / 100 / 60:.1f} hours at 100 req/min")
    print("=" * 80)
    
    # Skip confirmation prompt (auto-yes for batch processing)
    # response = input("\n⚠️  This will take many hours. Continue? (yes/no): ")
    # if response.lower() not in ['yes', 'y']:
    #     print("Cancelled.")
    #     return 0
    
    print("\n✅ Starting batch ingestion...")
    
    # Generate month ranges
    month_ranges = get_month_ranges(start_date, end_date)
    
    print(f"\n📊 Processing {len(month_ranges)} month batches...")
    
    successful = 0
    failed = 0
    overall_start = time.time()
    
    for i, (month_start, month_end) in enumerate(month_ranges, 1):
        print(f"\n[Batch {i}/{len(month_ranges)}]", end=' ')
        
        if ingest_month(month_start, month_end):
            successful += 1
        else:
            failed += 1
            print(f"⚠️  Month {month_start} to {month_end} failed, continuing...")
            # Continue on failure automatically
            # response = input("\n⚠️  Month failed. Continue with next month? (yes/no): ")
            # if response.lower() not in ['yes', 'y']:
            #     print("Stopping batch ingestion.")
            #     break
    
    # Final summary
    elapsed_hours = (time.time() - overall_start) / 3600
    
    print("\n" + "=" * 80)
    print("📊 BATCH INGESTION SUMMARY")
    print("=" * 80)
    print(f"Successful Months: {successful}/{len(month_ranges)}")
    print(f"Failed Months: {failed}/{len(month_ranges)}")
    print(f"Total Time: {elapsed_hours:.1f} hours")
    print("=" * 80)
    
    # Check final data coverage
    print("\n⏳ Checking BigQuery tables...")
    check_cmd = '''python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); 
query = 'SELECT COUNT(*) as cnt, MIN(DATE(CAST(settlementDate AS STRING))) as min_date, MAX(DATE(CAST(settlementDate AS STRING))) as max_date, COUNT(DISTINCT DATE(CAST(settlementDate AS STRING))) as days FROM \\`inner-cinema-476211-u9.uk_energy_prod.bmrs_boav\\`'; 
row = list(client.query(query).result())[0]; 
print(f'BOAV: {row.cnt:,} records, {row.days} days ({row.min_date} to {row.max_date})');
query2 = 'SELECT COUNT(*) as cnt, MIN(DATE(CAST(settlementDate AS STRING))) as min_date, MAX(DATE(CAST(settlementDate AS STRING))) as max_date, COUNT(DISTINCT DATE(CAST(settlementDate AS STRING))) as days FROM \\`inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf\\`'; 
row2 = list(client.query(query2).result())[0]; 
print(f'EBOCF: {row2.cnt:,} records, {row2.days} days ({row2.min_date} to {row2.max_date})')"'''
    
    subprocess.run(check_cmd, shell=True)
    
    print("\n✅ BATCH INGESTION COMPLETE")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
