#!/usr/bin/env python3
"""
Load 2016 Data from GCS to BigQuery

This script loads historical data from 2016 that's stored in the
elexon-historical-data-storage bucket into BigQuery tables.
"""

import os
import sys
import argparse
from datetime import datetime
from google.cloud import storage, bigquery

def print_with_timestamp(message):
    """Print message with timestamp."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] {message}")
    sys.stdout.flush()  # Ensure output is displayed immediately

def load_2016_data():
    """Load 2016 data from GCS to BigQuery."""
    print_with_timestamp("Starting 2016 data loading process")
    
    # Define the mapping between GCS directories and BigQuery tables
    data_mapping = [
        {
            "gcs_dir": "demand",
            "bq_dataset": "uk_energy_prod",
            "bq_table": "elexon_demand_outturn",
            "format": "JSON",
            "description": "Demand data including forecasts and actuals"
        },
        {
            "gcs_dir": "frequency",
            "bq_dataset": "uk_energy_data",
            "bq_table": "elexon_frequency",
            "format": "JSON",
            "description": "System frequency data"
        },
        {
            "gcs_dir": "generation",
            "bq_dataset": "uk_energy_prod",
            "bq_table": "elexon_generation_outturn",
            "format": "JSON",
            "description": "Generation data including fuel type breakdowns"
        },
        {
            "gcs_dir": "beb",
            "bq_dataset": "uk_energy_data",
            "bq_table": "elexon_bid_offer_acceptances",
            "format": "JSON",
            "description": "Bid-offer acceptance data"
        }
    ]
    
    # Create BigQuery client
    bq_client = bigquery.Client()
    
    # Create storage client and get bucket
    storage_client = storage.Client()
    bucket = storage_client.get_bucket("elexon-historical-data-storage")
    
    # Process each data type
    for mapping in data_mapping:
        gcs_dir = mapping["gcs_dir"]
        bq_dataset = mapping["bq_dataset"]
        bq_table = mapping["bq_table"]
        file_format = mapping["format"]
        
        print_with_timestamp(f"Processing {gcs_dir} data for {bq_dataset}.{bq_table}")
        
            # Get schema from target table
        try:
            table_ref = f"{bq_client.project}.{bq_dataset}.{bq_table}"
            
            # Check if table exists
            try:
                table = bq_client.get_table(table_ref)
                table_exists = True
            except Exception:
                print_with_timestamp(f"  Table {table_ref} does not exist. Will create it.")
                table_exists = False
            
            # List all files in the directory for 2016
            prefix = f"{gcs_dir}/"
            blobs = list(bucket.list_blobs(prefix=prefix))
            
            # Filter for 2016 files
            files_2016 = [blob for blob in blobs if "2016" in blob.name]
            
            if not files_2016:
                print_with_timestamp(f"  No 2016 files found for {gcs_dir}")
                continue
            
            print_with_timestamp(f"  Found {len(files_2016)} files from 2016")
            
            # List specific URIs instead of using wildcards
            specific_uris = [f"gs://elexon-historical-data-storage/{blob.name}" for blob in files_2016]
            
            print_with_timestamp(f"  Sample files to load (of {len(specific_uris)} total):")
            for uri in specific_uris[:3]:
                print(f"    - {uri}")
            
            # Create a load job
            job_config = bigquery.LoadJobConfig()
            
            if file_format == "JSON":
                job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
                job_config.autodetect = True
            else:  # CSV
                job_config.source_format = bigquery.SourceFormat.CSV
                job_config.skip_leading_rows = 1
                job_config.autodetect = True
            
            # Create temporary table name
            temp_table_id = f"{bq_dataset}.{bq_table}_2016_import_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            print_with_timestamp(f"  Loading data to temporary table {temp_table_id}")
            print_with_timestamp(f"  Loading {len(specific_uris)} files directly (not using wildcards)")
            
            # Create the load job using specific URIs rather than wildcards
            load_job = bq_client.load_table_from_uri(
                specific_uris, temp_table_id, job_config=job_config
            )            # Wait for the job to complete
            load_job.result()
            
            temp_table = bq_client.get_table(temp_table_id)
            print_with_timestamp(f"  Loaded {temp_table.num_rows} rows to {temp_table_id}")
            
            # Now handle the data appropriately - either merge into existing table or rename temp table
            if table_exists:
                # Merge data into the main table
                merge_query = f"""
                INSERT INTO `{table_ref}`
                SELECT * FROM `{temp_table_id}`
                """
                
                print_with_timestamp(f"  Merging data into existing table {table_ref}")
                merge_job = bq_client.query(merge_query)
                merge_job.result()
            else:
                # Rename the temp table to the final table name if it doesn't exist
                print_with_timestamp(f"  Target table doesn't exist, creating it from the loaded data")
                
                # We need to first create a dataset if it doesn't exist
                try:
                    bq_client.get_dataset(bq_dataset)
                except Exception:
                    print_with_timestamp(f"  Creating dataset {bq_dataset}")
                    dataset = bigquery.Dataset(f"{bq_client.project}.{bq_dataset}")
                    dataset.location = "US"
                    bq_client.create_dataset(dataset, exists_ok=True)
                
                # Copy the temp table to the final destination
                copy_job_config = bigquery.CopyJobConfig()
                copy_job = bq_client.copy_table(
                    temp_table_id, table_ref, job_config=copy_job_config
                )
                copy_job.result()
                print_with_timestamp(f"  Created table {table_ref} from the temporary table")
            
            # Get the table again for validation (it should exist now either way)
            table = bq_client.get_table(table_ref)
            
            # Validate the loaded data
            # First, get timestamp column name since it might vary by table
            timestamp_cols = [field.name for field in table.schema 
                             if field.field_type in ('TIMESTAMP', 'DATE', 'DATETIME')]
            
            if timestamp_cols:
                timestamp_col = timestamp_cols[0]
                validate_query = f"""
                SELECT COUNT(*) as row_count, 
                       MIN({timestamp_col}) as min_date, 
                       MAX({timestamp_col}) as max_date 
                FROM `{table_ref}`
                WHERE EXTRACT(YEAR FROM {timestamp_col}) = 2016
                """
                
                print_with_timestamp(f"  Validating loaded data using timestamp column: {timestamp_col}")
                validate_job = bq_client.query(validate_query)
                for row in validate_job:
                    print(f"    Loaded {row.row_count} rows from {row.min_date} to {row.max_date}")
            else:
                print_with_timestamp(f"  No timestamp column found in table, skipping validation")
            
        except Exception as e:
            print_with_timestamp(f"  Error processing {gcs_dir}: {str(e)}")
    
    print_with_timestamp("2016 data loading process complete")

if __name__ == "__main__":
    load_2016_data()
