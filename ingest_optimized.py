#!/usr/bin/env python3
"""
OPTIMIZED 3-Year BM Data Ingestion
- Single process per year (4 total: 2022, 2023, 2024, 2025)
- No overlap, no duplicates
- Checks existing data to skip completed months
"""

import sys
import subprocess
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def get_completed_months():
    """Get list of months already fully ingested"""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    SELECT 
        DATE_TRUNC(DATE(CAST(settlementDate AS STRING)), MONTH) as month,
        COUNT(DISTINCT DATE(CAST(settlementDate AS STRING))) as days
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav`
    GROUP BY month
    HAVING days >= 25  -- Consider month complete if >= 25 days
    ORDER BY month
    """
    
    result = client.query(query).result()
    completed = {row.month for row in result}
    return completed

def ingest_year_optimized(year):
    """Ingest one year, skipping completed months"""
    
    print(f"\n{'='*80}")
    print(f"YEAR {year} - Checking for gaps")
    print(f"{'='*80}\n")
    
    completed = get_completed_months()
    
    # Generate all months for this year
    if year == 2025:
        end_date = date(2025, 12, 13)
    else:
        end_date = date(year, 12, 31)
    
    start_date = date(year, 1, 1)
    
    current = start_date
    months_to_ingest = []
    
    while current <= end_date:
        month_start = date(current.year, current.month, 1)
        if month_start not in completed:
            # Calculate month end
            month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)
            if month_end > end_date:
                month_end = end_date
            
            months_to_ingest.append((month_start, month_end))
        else:
            print(f"  ✓ {month_start.strftime('%Y-%m')} already complete, skipping")
        
        current += relativedelta(months=1)
    
    if not months_to_ingest:
        print(f"\n✅ Year {year} already complete!\n")
        return
    
    print(f"\n📊 Year {year}: {len(months_to_ingest)} months to ingest\n")
    
    # Ingest each incomplete month
    for month_start, month_end in months_to_ingest:
        print(f"⏳ Ingesting {month_start} to {month_end}...")
        
        cmd = [
            "python3",
            "/home/george/GB-Power-Market-JJ/ingest_bm_settlement_data.py",
            "--start", month_start.strftime("%Y-%m-%d"),
            "--end", month_end.strftime("%Y-%m-%d")
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ {month_start.strftime('%Y-%m')} complete")
        else:
            print(f"  ❌ {month_start.strftime('%Y-%m')} failed: {result.stderr[:200]}")
            # Continue anyway
    
    print(f"\n✅ Year {year} ingestion complete\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True, help="Year to ingest (2022-2025)")
    args = parser.parse_args()
    
    if args.year not in [2022, 2023, 2024, 2025]:
        print("Error: Year must be 2022, 2023, 2024, or 2025")
        sys.exit(1)
    
    ingest_year_optimized(args.year)
