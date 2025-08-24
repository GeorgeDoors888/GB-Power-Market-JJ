#!/usr/bin/env python3
"""
Quick check for large datasets in both GCS and BigQuery
Specifically looking for the 200+ GB dataset mentioned
"""

import os
from google.cloud import storage, bigquery
import time

def check_gcs_buckets():
    """Check GCS buckets for large datasets"""
    print("\n==== CHECKING GCS BUCKETS FOR LARGE DATASETS ====")
    storage_client = storage.Client()
    
    # List of buckets to check
    buckets_to_check = [
        'jibber-jabber-knowledge-bmrs-data',
        'jibber-jabber-knowledge-bmrs-data-eu',
        'elexon-historical-data-storage',
        'elexon-archive'
    ]
    
    # Try to get all buckets if the specific ones don't contain what we need
    all_buckets = [b.name for b in storage_client.list_buckets()]
    print(f"All available buckets: {all_buckets}")
    
    for bucket_name in buckets_to_check:
        if bucket_name not in all_buckets:
            print(f"Bucket {bucket_name} does not exist")
            continue
            
        print(f"\nChecking bucket: {bucket_name}")
        bucket = storage_client.bucket(bucket_name)
        
        # Get total size of bucket
        total_size = 0
        count = 0
        
        # Limiting to 1000 files to avoid timeout but still get a sense of size
        blobs = list(storage_client.list_blobs(bucket_name, max_results=1000))
        if blobs:
            for blob in blobs:
                total_size += blob.size
                count += 1
            
            print(f"Sample size ({count} files): {total_size / (1024**3):.2f} GB")
            print(f"Estimated full bucket size: {(total_size / count) * 1000000 / (1024**3):.2f} GB (extrapolated)")
            
            # Show the first few files to understand structure
            print("Sample files:")
            for i, blob in enumerate(blobs[:5]):
                print(f"  {blob.name}: {blob.size / (1024**2):.2f} MB")
            
            # Check if this might be a download from yesterday
            today = time.strftime("%Y-%m-%d")
            yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
            
            recent_blobs = [b for b in blobs if yesterday in b.name or today in b.name]
            if recent_blobs:
                print(f"\nFiles from today or yesterday: {len(recent_blobs)} files found")
                for blob in recent_blobs[:5]:
                    print(f"  {blob.name}: {blob.size / (1024**2):.2f} MB")
        else:
            print("No files found in this bucket")

def check_bigquery_datasets():
    """Check BigQuery datasets for large tables"""
    print("\n==== CHECKING BIGQUERY DATASETS FOR LARGE TABLES ====")
    bq_client = bigquery.Client()
    
    datasets = list(bq_client.list_datasets())
    print(f"Found {len(datasets)} BigQuery datasets")
    
    large_tables = []
    
    for dataset in datasets:
        dataset_id = dataset.dataset_id
        print(f"\nDataset: {dataset_id}")
        
        tables = list(bq_client.list_tables(dataset_id))
        if not tables:
            print("  No tables found in this dataset")
            continue
            
        print(f"  Contains {len(tables)} tables")
        
        for table in tables:
            table_id = f"{dataset_id}.{table.table_id}"
            try:
                table_ref = bq_client.get_table(table_id)
                size_gb = table_ref.num_bytes / (1024**3) if hasattr(table_ref, 'num_bytes') else 0
                
                if size_gb > 1.0:  # Only show tables larger than 1GB
                    large_tables.append((table_id, table_ref.num_rows, size_gb))
                    print(f"  - {table.table_id}: {table_ref.num_rows:,} rows, {size_gb:.2f} GB <- LARGE TABLE")
            except Exception as e:
                print(f"  - Error getting table {table_id}: {e}")
    
    if large_tables:
        print("\nLarge tables summary:")
        for table_id, rows, size_gb in sorted(large_tables, key=lambda x: x[2], reverse=True):
            print(f"  {table_id}: {rows:,} rows, {size_gb:.2f} GB")
    else:
        print("\nNo large tables found in BigQuery (>1GB)")

if __name__ == "__main__":
    print("Checking for the 200+ GB dataset...")
    check_gcs_buckets()
    check_bigquery_datasets()
    print("\nCompleted check for large datasets")
