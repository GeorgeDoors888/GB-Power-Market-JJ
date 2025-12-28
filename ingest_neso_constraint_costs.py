#!/usr/bin/env python3
"""
Ingest NESO Constraint Cost Publications to BigQuery

Tables created:
- neso_constraint_breakdown: Monthly Emergency Instructions costs
- neso_mbss: Daily emergency service costs
- neso_annual_reports: Yearly NGSEA event counts
- neso_constraint_forecast: 24-month constraint cost forecast
- neso_modelled_costs: Historical NGSEA cost attribution
- neso_skip_rates: Monthly skip rate metrics

Usage:
    # First download data from NESO Data Portal manually to neso_downloads/
    python3 ingest_neso_constraint_costs.py --data-dir neso_downloads/constraint_costs
    python3 ingest_neso_constraint_costs.py --data-dir neso_downloads/constraint_costs --test
"""

import os
import glob
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import argparse

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

def ingest_constraint_breakdown(client, data_dir, test_mode=False):
    """Ingest monthly constraint breakdown CSVs"""
    print("\n" + "="*70)
    print("Ingesting Constraint Breakdown (Monthly)")
    print("="*70)
    
    files = glob.glob(f"{data_dir}/constraint_breakdown/*.csv")
    
    if not files:
        print(f"⚠️  No files found in {data_dir}/constraint_breakdown/")
        return
    
    print(f"Found {len(files)} CSV files")
    
    dfs = []
    for file in sorted(files):
        try:
            df = pd.read_csv(file)
            df['file_source'] = os.path.basename(file)
            df['ingested_utc'] = datetime.utcnow()
            dfs.append(df)
            print(f"  ✅ {os.path.basename(file)}: {len(df):,} rows")
        except Exception as e:
            print(f"  ❌ {os.path.basename(file)}: {e}")
    
    if not dfs:
        print("⚠️  No data loaded")
        return
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal rows: {len(combined):,}")
    
    if test_mode:
        print("\n📊 Sample data:")
        print(combined.head(3).to_string())
        return
    
    # Upload to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET}.neso_constraint_breakdown"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(combined, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Loaded {len(combined):,} rows to neso_constraint_breakdown")

def ingest_mbss(client, data_dir, test_mode=False):
    """Ingest MBSS daily emergency service costs"""
    print("\n" + "="*70)
    print("Ingesting MBSS (Daily Emergency Services)")
    print("="*70)
    
    files = glob.glob(f"{data_dir}/mbss/*.csv")
    
    if not files:
        print(f"⚠️  No files found in {data_dir}/mbss/")
        return
    
    print(f"Found {len(files)} CSV files")
    
    dfs = []
    for file in sorted(files):
        try:
            df = pd.read_csv(file)
            df['file_source'] = os.path.basename(file)
            df['ingested_utc'] = datetime.utcnow()
            dfs.append(df)
            print(f"  ✅ {os.path.basename(file)}: {len(df):,} rows")
        except Exception as e:
            print(f"  ❌ {os.path.basename(file)}: {e}")
    
    if not dfs:
        print("⚠️  No data loaded")
        return
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal rows: {len(combined):,}")
    
    if test_mode:
        print("\n📊 Sample data:")
        print(combined.head(3).to_string())
        return
    
    table_id = f"{PROJECT_ID}.{DATASET}.neso_mbss"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(combined, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Loaded {len(combined):,} rows to neso_mbss")

def ingest_skip_rates(client, data_dir, test_mode=False):
    """Ingest skip rate data"""
    print("\n" + "="*70)
    print("Ingesting Skip Rates (Monthly)")
    print("="*70)
    
    files = glob.glob(f"{data_dir}/skip_rates/*.csv")
    
    if not files:
        print(f"⚠️  No files found in {data_dir}/skip_rates/")
        return
    
    print(f"Found {len(files)} CSV files")
    
    dfs = []
    for file in sorted(files):
        try:
            df = pd.read_csv(file)
            df['file_source'] = os.path.basename(file)
            df['ingested_utc'] = datetime.utcnow()
            dfs.append(df)
            print(f"  ✅ {os.path.basename(file)}: {len(df):,} rows")
        except Exception as e:
            print(f"  ❌ {os.path.basename(file)}: {e}")
    
    if not dfs:
        print("⚠️  No data loaded")
        return
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal rows: {len(combined):,}")
    
    if test_mode:
        print("\n📊 Sample data:")
        print(combined.head(3).to_string())
        return
    
    table_id = f"{PROJECT_ID}.{DATASET}.neso_skip_rates"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(combined, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Loaded {len(combined):,} rows to neso_skip_rates")

def check_data_dir_structure(data_dir):
    """Check if data directory has expected structure"""
    print("\n" + "="*70)
    print("Checking Data Directory Structure")
    print("="*70)
    print(f"Base directory: {data_dir}")
    
    expected_dirs = [
        'constraint_breakdown',
        'mbss',
        'annual_reports',
        'forecast',
        'modelled_costs',
        'skip_rates'
    ]
    
    for dir_name in expected_dirs:
        path = os.path.join(data_dir, dir_name)
        exists = os.path.exists(path)
        file_count = len(glob.glob(f"{path}/*.csv")) if exists else 0
        status = "✅" if exists and file_count > 0 else "⚠️"
        print(f"  {status} {dir_name}: {file_count} CSV files")
    
    print("")

def main():
    parser = argparse.ArgumentParser(description='Ingest NESO constraint cost data')
    parser.add_argument('--data-dir', required=True, 
                       help='Path to neso_downloads/constraint_costs directory')
    parser.add_argument('--test', action='store_true', 
                       help='Test mode (no upload to BigQuery)')
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.exists(args.data_dir):
        print(f"❌ Directory not found: {args.data_dir}")
        print(f"\nTo download NESO data:")
        print(f"  1. Visit: https://data.nationalgrideso.com/constraint-management/")
        print(f"  2. Download datasets to: {args.data_dir}/")
        print(f"  3. Organize in subfolders: constraint_breakdown/, mbss/, skip_rates/")
        return
    
    check_data_dir_structure(args.data_dir)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("\n" + "="*70)
    print(f"NESO Constraint Cost Ingestion")
    print("="*70)
    print(f"Mode: {'TEST (no upload)' if args.test else 'PRODUCTION (uploading to BigQuery)'}")
    print("")
    
    # Ingest each dataset
    ingest_constraint_breakdown(client, args.data_dir, test_mode=args.test)
    ingest_mbss(client, args.data_dir, test_mode=args.test)
    ingest_skip_rates(client, args.data_dir, test_mode=args.test)
    
    print("\n" + "="*70)
    print("NESO Ingestion Complete")
    print("="*70)
    
    if not args.test:
        # List created tables
        print("\n📊 Tables created:")
        for table_name in ['neso_constraint_breakdown', 'neso_mbss', 'neso_skip_rates']:
            try:
                table = client.get_table(f"{PROJECT_ID}.{DATASET}.{table_name}")
                print(f"  ✅ {table_name}: {table.num_rows:,} rows")
            except:
                print(f"  ⚠️  {table_name}: Not found")

if __name__ == "__main__":
    main()
