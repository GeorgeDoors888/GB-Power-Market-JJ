#!/usr/bin/env python3
"""
Ingest BM Settlement Data (BOAV + EBOCF) into BigQuery
Fetches acceptance volumes and cashflows for comprehensive BM revenue analysis.

Data Sources:
- BOAV: Balancing mechanism acceptance volumes (offer/bid volumes)
- EBOCF: Balancing mechanism indicative cashflows (revenue data)

Usage:
    python3 ingest_bm_settlement_data.py --start 2025-12-01 --end 2025-12-13
    python3 ingest_bm_settlement_data.py --date 2025-12-13  # Single day
    python3 ingest_bm_settlement_data.py --recent 7          # Last 7 days

Author: George Major
Date: December 14, 2025
"""

import sys
import requests
import argparse
from datetime import datetime, date, timedelta
from google.cloud import bigquery
import pandas as pd
import time

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

# Elexon API endpoints
BOAV_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all"
EBOCF_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all"

# Rate limiting
REQUESTS_PER_MINUTE = 100  # Increased from 50
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE  # 0.6 seconds

def fetch_boav_data(target_date):
    """
    Fetch BOAV data (acceptance volumes) for a specific date.
    Fetches both offer and bid data.
    
    Args:
        target_date: Date to fetch data for
    
    Returns:
        DataFrame with columns: settlementDate, settlementPeriod, bmUnit, 
                                acceptanceType, acceptedVolume, etc.
    """
    date_str = target_date.strftime('%Y-%m-%d')
    
    all_records = []
    
    for sp in range(1, 49):  # 48 settlement periods
        for direction in ['offer', 'bid']:
            url = f"{BOAV_API}/{direction}/{date_str}/{sp}"
        
        try:
            time.sleep(DELAY_BETWEEN_REQUESTS)
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and {'data': [...]} formats
                if isinstance(data, dict) and 'data' in data:
                    records = data['data']
                elif isinstance(data, list):
                    records = data
                else:
                    records = []
                
                for record in records:
                    record['_fetched_date'] = date_str
                    record['_fetched_sp'] = sp
                    record['_direction'] = direction
                    all_records.append(record)
            
            elif response.status_code == 404:
                # No data for this SP (common)
                pass
            else:
                print(f"  ⚠️  {direction.upper()} SP{sp}: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"  ❌ {direction.upper()} SP{sp} error: {e}")
    
    if all_records:
        return pd.DataFrame(all_records)
    else:
        return pd.DataFrame()

def fetch_ebocf_data(target_date):
    """
    Fetch EBOCF data (indicative cashflows) for a specific date.
    Fetches both offer and bid data.
    
    Args:
        target_date: Date to fetch data for
    
    Returns:
        DataFrame with columns: settlementDate, settlementPeriod, bmUnit,
                                category, cashflow, etc.
    """
    date_str = target_date.strftime('%Y-%m-%d')
    
    all_records = []
    
    for sp in range(1, 49):  # 48 settlement periods
        for direction in ['offer', 'bid']:
            url = f"{EBOCF_API}/{direction}/{date_str}/{sp}"
            
            try:
                time.sleep(DELAY_BETWEEN_REQUESTS)
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle both list and {'data': [...]} formats
                    if isinstance(data, dict) and 'data' in data:
                        records = data['data']
                    elif isinstance(data, list):
                        records = data
                    else:
                        records = []
                    
                    for record in records:
                        record['_fetched_date'] = date_str
                        record['_fetched_sp'] = sp
                        record['_direction'] = direction
                        all_records.append(record)
                
                elif response.status_code == 404:
                    # No data for this SP (common)
                    pass
                else:
                    print(f"  ⚠️  {direction.UPPER()} SP{sp}: HTTP {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ {direction.upper()} SP{sp} error: {e}")
    
    if all_records:
        return pd.DataFrame(all_records)
    else:
        return pd.DataFrame()

def upload_to_bigquery(df, table_name, write_disposition='WRITE_APPEND'):
    """
    Upload DataFrame to BigQuery table.
    
    Args:
        df: Pandas DataFrame
        table_name: Target table name (e.g., 'bmrs_boav')
        write_disposition: WRITE_APPEND (default) or WRITE_TRUNCATE
    """
    if df.empty:
        print(f"  ⚠️  No data to upload to {table_name}")
        return
    
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    
    # Add ingestion timestamp
    df['_ingested_utc'] = datetime.utcnow().isoformat()
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=write_disposition,
        autodetect=True,  # Auto-detect schema
        create_disposition='CREATE_IF_NEEDED'
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        print(f"  ✅ Uploaded {len(df)} rows to {table_name}")
        
    except Exception as e:
        print(f"  ❌ Upload error to {table_name}: {e}")
        raise

def ingest_day(target_date):
    """
    Ingest both BOAV and EBOCF data for a single day.
    """
    date_str = target_date.strftime('%Y-%m-%d')
    
    print(f"\n{'='*80}")
    print(f"📊 Ingesting BM Settlement Data: {date_str}")
    print(f"{'='*80}")
    
    # Fetch BOAV (acceptance volumes)
    print(f"\n⏳ Fetching BOAV data (acceptance volumes)...")
    boav_df = fetch_boav_data(target_date)
    
    if not boav_df.empty:
        print(f"  📈 Retrieved {len(boav_df)} BOAV records")
        upload_to_bigquery(boav_df, 'bmrs_boav')
    else:
        print(f"  ⚠️  No BOAV data found")
    
    # Fetch EBOCF (cashflows)
    print(f"\n⏳ Fetching EBOCF data (indicative cashflows)...")
    ebocf_df = fetch_ebocf_data(target_date)
    
    if not ebocf_df.empty:
        print(f"  📈 Retrieved {len(ebocf_df)} EBOCF records")
        upload_to_bigquery(ebocf_df, 'bmrs_ebocf')
    else:
        print(f"  ⚠️  No EBOCF data found")
    
    print(f"\n✅ Completed ingestion for {date_str}")

def ingest_date_range(start_date, end_date):
    """
    Ingest data for a date range.
    """
    current_date = start_date
    
    while current_date <= end_date:
        ingest_day(current_date)
        current_date += timedelta(days=1)
    
    print(f"\n{'='*80}")
    print(f"✅ COMPLETED: Ingested {(end_date - start_date).days + 1} days")
    print(f"{'='*80}")

def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description='Ingest BM settlement data (BOAV + EBOCF) into BigQuery')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--date', type=str, help='Single date to ingest (YYYY-MM-DD)')
    parser.add_argument('--recent', type=int, help='Ingest last N days')
    
    args = parser.parse_args()
    
    # Determine date range
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        ingest_day(target_date)
    
    elif args.recent:
        end_date = date.today() - timedelta(days=1)  # Yesterday (settlement data lags)
        start_date = end_date - timedelta(days=args.recent - 1)
        ingest_date_range(start_date, end_date)
    
    elif args.start and args.end:
        start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end, '%Y-%m-%d').date()
        ingest_date_range(start_date, end_date)
    
    else:
        # Default: yesterday
        yesterday = date.today() - timedelta(days=1)
        ingest_day(yesterday)

if __name__ == "__main__":
    main()
