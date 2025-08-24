#!/usr/bin/env python3
"""
Find large datasets in GCS and BigQuery across the entire project.
"""

import os
import sys
from datetime import datetime
from google.cloud import storage, bigquery

def print_with_timestamp(message):
    """Print message with timestamp."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] {message}")
    sys.stdout.flush()  # Ensure output is displayed immediately

def scan_all_gcs_buckets():
    """Scan all GCS buckets for large datasets."""
    print_with_timestamp("Scanning all GCS buckets...")
    storage_client = storage.Client()
    
    try:
        # List all buckets
        buckets = list(storage_client.list_buckets())
        print_with_timestamp(f"Found {len(buckets)} buckets:")
        
        for i, bucket in enumerate(buckets):
            print_with_timestamp(f"  {i+1}. {bucket.name}")
            
            # Get bucket size
            try:
                # Count only top-level folders to avoid listing every file
                blobs = list(bucket.list_blobs(delimiter='/'))
                folders = bucket.list_blobs(delimiter='/')
                prefixes = list(folders.prefixes)
                
                print_with_timestamp(f"    - Found {len(prefixes)} top-level folders")
                
                # List some folders for context
                for prefix in prefixes[:5]:
                    print_with_timestamp(f"      * {prefix}")
                
                if len(prefixes) > 5:
                    print_with_timestamp(f"      * ... and {len(prefixes) - 5} more")
                
                # Try to estimate size if not too many files
                if len(prefixes) < 20:  # Only check detailed size for smaller buckets
                    try:
                        all_blobs = list(bucket.list_blobs())
                        size_bytes = sum(blob.size for blob in all_blobs)
                        size_gb = size_bytes / (1024**3)
                        print_with_timestamp(f"    - Approximate size: {size_gb:.2f} GB ({len(all_blobs)} files)")
                    except Exception as e:
                        print_with_timestamp(f"    - Error estimating size: {str(e)}")
                else:
                    print_with_timestamp(f"    - Too many folders to estimate size quickly")
                    
                # Look for 'historical' or 'archive' in folder names
                historical_folders = [p for p in prefixes if 'historical' in p.lower() or 'archive' in p.lower() 
                                     or 'history' in p.lower() or '2016' in p or '2017' in p or '2018' in p]
                if historical_folders:
                    print_with_timestamp(f"    - Possible historical data folders:")
                    for hf in historical_folders:
                        print_with_timestamp(f"      * {hf}")
                
            except Exception as e:
                print_with_timestamp(f"    - Error listing contents: {str(e)}")
            
            print_with_timestamp("")  # Empty line for readability
    
    except Exception as e:
        print_with_timestamp(f"Error listing buckets: {str(e)}")

def scan_all_bigquery_datasets():
    """Scan all BigQuery datasets for large tables."""
    print_with_timestamp("\nScanning all BigQuery datasets...")
    bq_client = bigquery.Client()
    
    try:
        # List all datasets
        datasets = list(bq_client.list_datasets())
        print_with_timestamp(f"Found {len(datasets)} datasets:")
        
        total_storage = 0
        
        for dataset in datasets:
            dataset_id = dataset.dataset_id
            print_with_timestamp(f"  - Dataset: {dataset_id}")
            
            # List tables in dataset
            try:
                tables = list(bq_client.list_tables(dataset_id))
                print_with_timestamp(f"    - Contains {len(tables)} tables")
                
                if not tables:
                    continue
                
                # Get total dataset size
                dataset_size_bytes = 0
                largest_tables = []
                
                for table in tables:
                    table_ref = f"{dataset_id}.{table.table_id}"
                    try:
                        table_full = bq_client.get_table(table_ref)
                        table_size_bytes = table_full.num_bytes
                        table_rows = table_full.num_rows
                        dataset_size_bytes += table_size_bytes
                        
                        size_mb = table_size_bytes / (1024**2)
                        largest_tables.append((table.table_id, size_mb, table_rows))
                        
                    except Exception as e:
                        print_with_timestamp(f"      * Error getting table {table.table_id}: {str(e)}")
                
                # Sort and display largest tables
                largest_tables.sort(key=lambda x: x[1], reverse=True)
                dataset_size_gb = dataset_size_bytes / (1024**3)
                print_with_timestamp(f"    - Total dataset size: {dataset_size_gb:.2f} GB")
                
                # Only show tables if dataset is significant in size
                if dataset_size_gb > 1.0:  # Only show details for datasets > 1GB
                    print_with_timestamp(f"    - Largest tables:")
                    for i, (table_id, size_mb, rows) in enumerate(largest_tables[:5]):
                        print_with_timestamp(f"      * {table_id}: {size_mb:.2f} MB, {rows:,} rows")
                
                total_storage += dataset_size_bytes
                
            except Exception as e:
                print_with_timestamp(f"    - Error listing tables: {str(e)}")
            
            print_with_timestamp("")  # Empty line for readability
        
        # Show total storage
        total_storage_gb = total_storage / (1024**3)
        print_with_timestamp(f"Total BigQuery storage used: {total_storage_gb:.2f} GB")
    
    except Exception as e:
        print_with_timestamp(f"Error listing datasets: {str(e)}")

def main():
    """Run the data scanning tool."""
    print_with_timestamp("Starting large dataset scan")
    print_with_timestamp("=" * 50)
    
    scan_all_gcs_buckets()
    scan_all_bigquery_datasets()
    
    print_with_timestamp("=" * 50)
    print_with_timestamp("Scan complete")

if __name__ == "__main__":
    main()
