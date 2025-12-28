#!/usr/bin/env python3
"""
Ingest interconnector flow data from NESO Data Portal

Interconnectors: IFA, IFA2, BritNed, NemoLink, NSL, Viking, ElecLink
Format: CSV per interconnector per year

Usage:
    python3 ingest_interconnector_flows.py --start-year 2022 --end-year 2025
    python3 ingest_interconnector_flows.py --start-year 2024 --end-year 2024 --test
"""

import os
import io
import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import argparse

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# NESO Data Portal URLs for interconnector data
# Note: These URLs may need to be updated based on actual NESO Data Portal structure
INTERCONNECTOR_URLS = {
    'IFA': 'https://data.nationalgrideso.com/backend/dataset/7a2b696b-3714-4a89-85eb-8c8d9c92c92f/resource/{resource_id}/download/interconnectordata.csv',
    'IFA2': 'https://data.nationalgrideso.com/backend/dataset/ifa2/resource/{resource_id}/download/interconnectordata.csv',
    'BritNed': 'https://data.nationalgrideso.com/backend/dataset/britned/resource/{resource_id}/download/interconnectordata.csv',
    'NemoLink': 'https://data.nationalgrideso.com/backend/dataset/nemolink/resource/{resource_id}/download/interconnectordata.csv',
    'NSL': 'https://data.nationalgrideso.com/backend/dataset/north-sea-link/resource/{resource_id}/download/interconnectordata.csv',
    'Viking': 'https://data.nationalgrideso.com/backend/dataset/viking-link/resource/{resource_id}/download/interconnectordata.csv',
    'ElecLink': 'https://data.nationalgrideso.com/backend/dataset/eleclink/resource/{resource_id}/download/interconnectordata.csv'
}

def download_interconnector_data(name, url, year, test_mode=False):
    """Download CSV for one interconnector-year"""
    try:
        # Note: Resource ID varies by year, may need manual lookup from NESO portal
        # For now, use placeholder
        url_formatted = url.replace('{resource_id}', 'NEEDS_RESOURCE_ID')
        url_formatted = url_formatted.replace('YEAR', str(year))
        
        print(f"  Attempting: {name} {year}")
        print(f"    URL: {url_formatted}")
        
        if test_mode:
            print(f"    ⚠️  Test mode - skipping actual download")
            return pd.DataFrame()
        
        response = requests.get(url_formatted, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        df['interconnector'] = name
        df['year'] = year
        df['ingested_utc'] = datetime.utcnow()
        
        print(f"    ✅ Downloaded {len(df):,} rows")
        return df
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return pd.DataFrame()

def ingest_all_interconnectors(start_year, end_year, test_mode=False):
    """Ingest all interconnectors for year range"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    all_data = []
    
    print("\n" + "="*70)
    print("Interconnector Data Download")
    print("="*70)
    print(f"⚠️  IMPORTANT: This script requires manual URL configuration")
    print(f"   Visit: https://data.nationalgrideso.com/interconnectors/")
    print(f"   Find correct resource IDs for each interconnector")
    print("")
    
    for name, base_url in INTERCONNECTOR_URLS.items():
        print(f"\n{name}:")
        for year in range(start_year, end_year + 1):
            df = download_interconnector_data(name, base_url, year, test_mode=test_mode)
            if not df.empty:
                all_data.append(df)
    
    if not all_data:
        print("\n⚠️  No data downloaded. URLs need to be configured manually.")
        print("\nManual steps:")
        print("  1. Visit https://data.nationalgrideso.com/interconnectors/")
        print("  2. For each interconnector, find the 'Download' link")
        print("  3. Update INTERCONNECTOR_URLS in this script with correct resource IDs")
        print("  4. Re-run script")
        return
    
    # Combine all
    combined = pd.concat(all_data, ignore_index=True)
    
    print("\n" + "="*70)
    print(f"Total rows collected: {len(combined):,}")
    print("="*70)
    
    if test_mode:
        print("\n📊 Sample data:")
        print(combined.head(3).to_string())
        return
    
    # Upload to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET}.neso_interconnector_flows"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(combined, table_id, job_config=job_config)
    job.result()
    
    print(f"\n✅ Total: {len(combined):,} rows to neso_interconnector_flows")

def main():
    parser = argparse.ArgumentParser(description='Ingest interconnector flow data')
    parser.add_argument('--start-year', type=int, default=2022, help='Start year')
    parser.add_argument('--end-year', type=int, default=2025, help='End year')
    parser.add_argument('--test', action='store_true', help='Test mode (no download/upload)')
    args = parser.parse_args()
    
    print("="*70)
    print("Interconnector Flow Ingestion")
    print("="*70)
    print(f"Years: {args.start_year} to {args.end_year}")
    print(f"Mode: {'TEST' if args.test else 'PRODUCTION'}")
    print("")
    
    ingest_all_interconnectors(args.start_year, args.end_year, test_mode=args.test)

if __name__ == "__main__":
    main()
