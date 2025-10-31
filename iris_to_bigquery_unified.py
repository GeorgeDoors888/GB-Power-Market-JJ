#!/usr/bin/env python3
"""
IRIS to BigQuery - Unified Schema Version
Handles IRIS data with new Insights API schema, separate from historic data
"""

import os
import json
import time
import logging
from collections import defaultdict
from datetime import datetime
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('iris_to_bq_unified.log'),
        logging.StreamHandler()
    ]
)

# Configuration
IRIS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'iris-clients', 'python', 'iris_data')
BQ_PROJECT = os.environ.get('BQ_PROJECT', 'inner-cinema-476211-u9')
BQ_DATASET = os.environ.get('BQ_DATASET', 'uk_energy_prod')

# Batching Configuration
BATCH_SIZE = 500
BATCH_WAIT_SECONDS = 5
MAX_FILES_PER_SCAN = 2000

# Initialize BigQuery client
bq_client = bigquery.Client(project=BQ_PROJECT)

# Dataset name mapping (IRIS → BigQuery table names)
# These will go to separate *_iris tables
DATASET_TABLE_MAPPING = {
    'BOALF': 'bmrs_boalf_iris',
    'BOD': 'bmrs_bod_iris',
    'MILS': 'bmrs_mils_iris',
    'MELS': 'bmrs_mels_iris',
    'FREQ': 'bmrs_freq_iris',
    'FUELINST': 'bmrs_fuelinst_iris',
    'REMIT': 'bmrs_remit_iris',
    'MID': 'bmrs_mid_iris',
    'BEB': 'bmrs_beb_iris',
    'BOAV': 'bmrs_boav_iris',
    'DISEBSP': 'bmrs_disebsp_iris',
    'DISPTAV': 'bmrs_disptav_iris',
    'EBOCF': 'bmrs_ebocf_iris',
    'ISPSTACK': 'bmrs_ispstack_iris',
    'SMSG': 'bmrs_smsg_iris',
}

def get_table_ref(table_name):
    """Get full BigQuery table reference"""
    return f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"

def ensure_table_exists(table_ref):
    """Create table if it doesn't exist (with auto schema)"""
    try:
        bq_client.get_table(table_ref)
        return True
    except NotFound:
        logging.info(f"📝 Table {table_ref} doesn't exist - will be created on first insert")
        return False

def convert_datetime_fields(data):
    """Convert ISO 8601 datetime strings to BigQuery DATETIME format
    
    BigQuery DATETIME requires format: YYYY-MM-DD HH:MM:SS (no timezone)
    IRIS sends: 2025-10-28T14:25:00.000Z (ISO 8601 with Z)
    """
    # Convert ANY field containing ISO 8601 datetime strings
    # This catches all datetime fields regardless of name
    for field, value in list(data.items()):
        if isinstance(value, str) and 'T' in value and 'Z' in value:
            # Looks like ISO 8601 datetime: "2025-10-28T14:25:00.000Z"
            # Convert to: "2025-10-28 14:25:00"
            try:
                dt_str = value.replace('T', ' ').replace('Z', '').split('.')[0]
                data[field] = dt_str
            except:
                # If conversion fails, leave as-is
                pass
    
    # Add metadata (keep ingested_utc as TIMESTAMP format)
    if 'ingested_utc' not in data:
        data['ingested_utc'] = datetime.utcnow().isoformat() + 'Z'
    if 'source' not in data:
        data['source'] = 'IRIS'
    return data

def process_batch(table_name, rows, files_to_remove):
    """Insert batch of rows into BigQuery and delete source files on success"""
    table_ref = get_table_ref(table_name)
    
    # Ensure table exists
    ensure_table_exists(table_ref)
    
    # Add metadata to each row
    processed_rows = [convert_datetime_fields(row) for row in rows]
    
    # Insert batch
    try:
        errors = bq_client.insert_rows_json(
            table_ref,
            processed_rows,
            skip_invalid_rows=False,  # Fail fast to catch schema issues
        )
        
        if errors:
            # Log first few errors
            for i, error in enumerate(errors[:3]):
                logging.error(f"❌ Row {error.get('index', '?')}: {error.get('errors', [])}")
            
            if len(errors) > 3:
                logging.error(f"... and {len(errors) - 3} more errors")
            
            return False, 0
        else:
            logging.info(f"✅ Inserted {len(rows)} rows into {table_name}")
            
            # Remove successfully processed files
            deleted_count = 0
            for filepath in files_to_remove:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except OSError as e:
                    logging.error(f"⚠️ Failed to remove {filepath}: {e}")
            
            if deleted_count > 0:
                logging.info(f"🗑️  Deleted {deleted_count} processed JSON files")
            
            return True, deleted_count
            
    except Exception as e:
        logging.error(f"❌ Failed to insert batch into {table_name}: {e}")
        return False, 0

def scan_and_batch_files():
    """Scan IRIS data directory and batch files by table"""
    batches = defaultdict(lambda: {'rows': [], 'files': []})
    file_count = 0
    record_count = 0
    
    if not os.path.exists(IRIS_DATA_DIR):
        logging.error(f"IRIS data directory not found: {IRIS_DATA_DIR}")
        return batches, file_count, record_count
    
    # Scan all dataset directories
    for dataset_dir in os.listdir(IRIS_DATA_DIR):
        dataset_path = os.path.join(IRIS_DATA_DIR, dataset_dir)
        
        if not os.path.isdir(dataset_path):
            continue
        
        # Get table name from dataset
        dataset_upper = dataset_dir.upper()
        table_name = DATASET_TABLE_MAPPING.get(dataset_upper)
        
        if not table_name:
            # Skip unmapped datasets
            continue
        
        # Process JSON files in this dataset
        for filename in os.listdir(dataset_path):
            if not filename.endswith('.json'):
                continue
            
            if file_count >= MAX_FILES_PER_SCAN:
                logging.info(f"⚠️  Reached max files per scan ({MAX_FILES_PER_SCAN})")
                return batches, file_count, record_count
            
            filepath = os.path.join(dataset_path, filename)
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # IRIS files contain arrays of records
                if isinstance(data, list):
                    for record in data:
                        batches[table_name]['rows'].append(record)
                        record_count += 1
                    batches[table_name]['files'].append(filepath)
                else:
                    # Single record
                    batches[table_name]['rows'].append(data)
                    batches[table_name]['files'].append(filepath)
                    record_count += 1
                
                file_count += 1
                
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"❌ Failed to read {filepath}: {e}")
                # Remove bad file
                try:
                    os.remove(filepath)
                except OSError:
                    pass
    
    return batches, file_count, record_count

def process_all_batches():
    """Process all batches with size limits"""
    batches, total_files, total_records = scan_and_batch_files()
    
    if total_files == 0:
        return 0, 0
    
    logging.info(f"📦 Found {total_files} files ({total_records} records) across {len(batches)} tables")
    
    total_processed = 0
    total_deleted = 0
    
    for table_name, batch_data in batches.items():
        rows = batch_data['rows']
        files = batch_data['files']
        
        logging.info(f"📊 Processing {len(rows)} rows from {len(files)} files for {table_name}")
        
        # Process all rows and delete ALL files on success
        # (since each file was fully read into rows)
        success, deleted = process_batch(table_name, rows, files)
        
        if success:
            total_processed += len(rows)
            total_deleted += deleted
        else:
            logging.error(f"⚠️  Failed to process batch for {table_name} - files kept for retry")
    
    return total_processed, total_deleted

def main():
    """Main loop - continuously process IRIS messages"""
    logging.info("=" * 60)
    logging.info("🚀 IRIS to BigQuery (Unified Schema)")
    logging.info("=" * 60)
    logging.info(f"📂 Watching: {IRIS_DATA_DIR}")
    logging.info(f"📊 Project: {BQ_PROJECT}")
    logging.info(f"📦 Dataset: {BQ_DATASET}")
    logging.info(f"⚙️  Batch Size: {BATCH_SIZE} rows")
    logging.info(f"⏱️  Scan Interval: {BATCH_WAIT_SECONDS}s")
    logging.info(f"💡 Strategy: Separate *_iris tables + unified views")
    logging.info("=" * 60)
    
    cycle_count = 0
    total_messages_processed = 0
    total_files_deleted = 0
    
    while True:
        cycle_count += 1
        cycle_start = time.time()
        
        try:
            processed, deleted = process_all_batches()
            total_messages_processed += processed
            total_files_deleted += deleted
            
            cycle_time = time.time() - cycle_start
            
            if processed > 0:
                rate = processed / cycle_time if cycle_time > 0 else 0
                logging.info(
                    f"📈 Cycle {cycle_count}: Processed {processed} records, deleted {deleted} files "
                    f"in {cycle_time:.1f}s ({rate:.0f} msg/s) | Total: {total_messages_processed} records, "
                    f"{total_files_deleted} files deleted"
                )
            
        except KeyboardInterrupt:
            logging.info(f"\n👋 Shutting down gracefully... Total files deleted: {total_files_deleted}")
            break
        except Exception as e:
            logging.error(f"❌ Error in processing cycle: {e}", exc_info=True)
        
        # Wait before next scan
        time.sleep(BATCH_WAIT_SECONDS)

if __name__ == "__main__":
    main()
