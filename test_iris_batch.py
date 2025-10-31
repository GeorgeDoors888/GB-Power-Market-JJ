#!/usr/bin/env python3
"""
Test run of batched IRIS to BigQuery - processes just ONE batch then exits
"""

import os
import json
import time
import logging
from collections import defaultdict
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

IRIS_DATA_DIR = 'iris-clients/python/iris_data'
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BATCH_SIZE = 100  # Small test batch
MAX_FILES = 100   # Just process 100 files for testing

bq_client = bigquery.Client(project=BQ_PROJECT)

DATASET_TABLE_MAPPING = {
    'BOALF': 'bmrs_boalf',
    'BOD': 'bmrs_bod',
    'MILS': 'bmrs_mils',
    'MELS': 'bmrs_mels',
    'FREQ': 'bmrs_freq',
    'FUELINST': 'bmrs_fuelinst',
    'REMIT': 'bmrs_remit_unavailability',
    'MID': 'bmrs_mid',
}

def get_table_ref(table_name):
    return f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"

def scan_files():
    """Scan and collect files"""
    batches = defaultdict(lambda: {'rows': [], 'files': []})
    file_count = 0
    
    for dataset_dir in os.listdir(IRIS_DATA_DIR):
        dataset_path = os.path.join(IRIS_DATA_DIR, dataset_dir)
        
        if not os.path.isdir(dataset_path):
            continue
        
        dataset_upper = dataset_dir.upper()
        table_name = DATASET_TABLE_MAPPING.get(dataset_upper)
        
        if not table_name:
            continue
        
        for filename in os.listdir(dataset_path):
            if not filename.endswith('.json'):
                continue
            
            if file_count >= MAX_FILES:
                return batches, file_count
            
            filepath = os.path.join(dataset_path, filename)
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # IRIS files contain arrays of records
                if isinstance(data, list):
                    for record in data:
                        batches[table_name]['rows'].append(record)
                    batches[table_name]['files'].append(filepath)
                else:
                    # Single record
                    batches[table_name]['rows'].append(data)
                    batches[table_name]['files'].append(filepath)
                
                file_count += 1
                
            except Exception as e:
                logging.error(f"Failed to read {filepath}: {e}")
                try:
                    os.remove(filepath)
                except:
                    pass
    
    return batches, file_count

def process_batch(table_name, rows, files_to_remove):
    """Insert batch into BigQuery"""
    table_ref = get_table_ref(table_name)
    
    try:
        errors = bq_client.insert_rows_json(table_ref, rows)
        if errors:
            logging.error(f"❌ BigQuery errors for {table_name}: {errors[:3]}")
            return False
        else:
            logging.info(f"✅ Inserted {len(rows)} rows into {table_name}")
            
            # Remove files
            for filepath in files_to_remove:
                try:
                    os.remove(filepath)
                except OSError as e:
                    logging.error(f"Failed to remove {filepath}: {e}")
            
            return True
    except Exception as e:
        logging.error(f"❌ Failed to insert into {table_name}: {e}")
        return False

def main():
    logging.info("=" * 60)
    logging.info("🧪 IRIS to BigQuery Batch Test")
    logging.info(f"📦 Max files: {MAX_FILES}")
    logging.info(f"⚙️  Batch size: {BATCH_SIZE}")
    logging.info("=" * 60)
    
    # Scan
    start_time = time.time()
    batches, file_count = scan_files()
    scan_time = time.time() - start_time
    
    logging.info(f"✅ Scanned {file_count} files in {scan_time:.2f}s")
    logging.info(f"📊 Tables: {list(batches.keys())}")
    
    # Process
    total_processed = 0
    process_start = time.time()
    
    for table_name, batch_data in batches.items():
        rows = batch_data['rows']
        files = batch_data['files']
        
        logging.info(f"📊 Processing {len(rows)} rows for {table_name}")
        
        # Split into chunks
        for i in range(0, len(rows), BATCH_SIZE):
            chunk_rows = rows[i:i + BATCH_SIZE]
            chunk_files = files[i:i + BATCH_SIZE]
            
            success = process_batch(table_name, chunk_rows, chunk_files)
            
            if success:
                total_processed += len(chunk_rows)
    
    process_time = time.time() - process_start
    total_time = time.time() - start_time
    
    logging.info("=" * 60)
    logging.info(f"✅ TEST COMPLETE")
    logging.info(f"📊 Processed: {total_processed} messages")
    logging.info(f"⏱️  Scan time: {scan_time:.2f}s")
    logging.info(f"⏱️  Process time: {process_time:.2f}s")
    logging.info(f"⏱️  Total time: {total_time:.2f}s")
    logging.info(f"⚡ Rate: {total_processed / total_time:.0f} msg/s")
    logging.info("=" * 60)

if __name__ == "__main__":
    main()
