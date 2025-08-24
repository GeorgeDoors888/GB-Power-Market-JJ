#!/usr/bin/env python3
"""
Check size of historical data loaded to BigQuery and in GCS.
"""

import os
import sys
from google.cloud import bigquery, storage

def main():
    """Print size information for the loaded historical data."""
    print("Historical Data Size Check")
    print("-" * 50)
    
    # BigQuery table sizes
    print("\nBigQuery Table Sizes:")
    bq_client = bigquery.Client()
    
    tables = [
        'uk_energy_prod.elexon_demand_outturn',
        'uk_energy_data.elexon_frequency',
        'uk_energy_prod.elexon_generation_outturn',
        'uk_energy_data.elexon_bid_offer_acceptances'
    ]
    
    total_rows = 0
    total_size_bytes = 0
    
    for table in tables:
        table_ref = f'jibber-jabber-knowledge.{table}'
        try:
            bq_table = bq_client.get_table(table_ref)
            rows = bq_table.num_rows
            size_bytes = bq_table.num_bytes
            size_mb = size_bytes / (1024 * 1024)
            total_rows += rows
            total_size_bytes += size_bytes
            
            print(f"{table}: {rows:,} rows, {size_mb:.2f} MB")
        except Exception as e:
            print(f"{table}: Error getting size - {str(e)}")
    
    total_size_gb = total_size_bytes / (1024 * 1024 * 1024)
    print(f"\nTotal BigQuery data: {total_rows:,} rows, {total_size_gb:.2f} GB")
    
    # GCS bucket size
    print("\nGCS Data Size:")
    storage_client = storage.Client()
    bucket_name = 'elexon-historical-data-storage'
    
    try:
        bucket = storage_client.get_bucket(bucket_name)
        
        prefixes = ['demand/', 'frequency/', 'generation/', 'beb/']
        category_sizes = {}
        total_gcs_size = 0
        total_files = 0
        
        for prefix in prefixes:
            blobs = list(bucket.list_blobs(prefix=prefix))
            size = sum(blob.size for blob in blobs)
            size_mb = size / (1024 * 1024)
            category_sizes[prefix] = (len(blobs), size_mb)
            total_gcs_size += size
            total_files += len(blobs)
            
            print(f"{prefix}: {len(blobs)} files, {size_mb:.2f} MB")
        
        total_gcs_size_gb = total_gcs_size / (1024 * 1024 * 1024)
        print(f"\nTotal GCS data: {total_files} files, {total_gcs_size_gb:.2f} GB")
        
    except Exception as e:
        print(f"Error getting GCS sizes: {str(e)}")

if __name__ == "__main__":
    main()
