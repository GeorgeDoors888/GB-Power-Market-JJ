#!/usr/bin/env python3
"""
Optimized IRIS to BigQuery Integration with Batching
- Processes multiple files per batch
- Groups by table for efficient inserts
- Handles BigQuery quotas properly
"""

import os
import json
import time
import logging
from collections import defaultdict
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('iris_to_bq.log'),
        logging.StreamHandler()
    ]
)

# Configuration
IRIS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'iris-clients', 'python', 'iris_data')
BQ_PROJECT = os.environ.get('BQ_PROJECT', 'inner-cinema-476211-u9')
BQ_DATASET = os.environ.get('BQ_DATASET', 'uk_energy_prod')

# Batching Configuration
BATCH_SIZE = 500              # Max rows per BigQuery insert (limit is 10,000)
BATCH_WAIT_SECONDS = 5        # Wait time between scans
MAX_FILES_PER_SCAN = 2000     # Limit files processed per scan

# BigQuery Quotas (as of 2025):
# - Streaming inserts: 100,000 rows/second
# - API requests: 100 requests/second
# - Max row size: 10 MB
# With BATCH_SIZE=500, we can process 50,000+ rows/second

# Initialize BigQuery client
bq_client = bigquery.Client(project=BQ_PROJECT)

# Dataset name mapping (IRIS → BigQuery table names)
DATASET_TABLE_MAPPING = {
    'BOALF': 'bmrs_boalf',
    'BOD': 'bmrs_bod',
    'MILS': 'bmrs_mils',
    'MELS': 'bmrs_mels',
    'FREQ': 'bmrs_freq',
    'FUELINST': 'bmrs_fuelinst',
    'REMIT': 'bmrs_remit_unavailability',
    'MID': 'bmrs_mid',
    'BEB': 'bmrs_beb',
    'BOAV': 'bmrs_boav',
    'DISEBSP': 'bmrs_disebsp',
    'DISPTAV': 'bmrs_disptav',
    'EBOCF': 'bmrs_ebocf',
    'ISPSTACK': 'bmrs_ispstack',
    'SMSG': 'bmrs_smsg',
    'CBS': 'bmrs_cbs',
    'NDF': 'bmrs_ndf',
    'TSDF': 'bmrs_tsdf',
    'SOSO': 'bmrs_soso',
    'INDO': 'bmrs_indo',
    'INDGEN': 'bmrs_indgen',
    'INDDEM': 'bmrs_inddem',
    'FUELHH': 'bmrs_fuelhh',
    'AOBE': 'bmrs_aobe',
    'DISBSAD': 'bmrs_disbsad',
    'NETBSAD': 'bmrs_netbsad',
    'NDZ': 'bmrs_ndz',
    'ITSDO': 'bmrs_itsdo',
    'MELNGC': 'bmrs_melngc',
    'IMBALNGC': 'bmrs_imbalngc',
    'RURE': 'bmrs_rure',
    'SEL': 'bmrs_sel',
    'AGWS': 'bmrs_agws',
}

def get_table_ref(table_name):
    """Get full BigQuery table reference"""
    return f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"

def get_existing_schema(table_ref):
    """Fetch existing table schema"""
    try:
        table = bq_client.get_table(table_ref)
        return {field.name: field for field in table.schema}
    except NotFound:
        logging.warning(f"Table {table_ref} not found - will be created on first insert")
        return {}

def add_new_columns(table_ref, new_fields):
    """Add new columns to existing table"""
    try:
        table = bq_client.get_table(table_ref)
        schema = list(table.schema)
        
        for field_name, field_type in new_fields.items():
            schema.append(bigquery.SchemaField(field_name, field_type, mode="NULLABLE"))
            logging.info(f"  ➕ Adding column: {field_name} ({field_type})")
        
        table.schema = schema
        bq_client.update_table(table, ["schema"])
        logging.info(f"✅ Updated schema for {table_ref}")
    except Exception as e:
        logging.error(f"❌ Failed to add columns to {table_ref}: {e}")

def infer_bq_type(value):
    """Infer BigQuery column type from value"""
    if value is None:
        return "STRING"
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INT64"
    if isinstance(value, float):
        return "FLOAT64"
    if isinstance(value, dict):
        return "RECORD"
    if isinstance(value, list):
        return "STRING"  # Store as JSON string
    return "STRING"

def process_batch(table_name, rows, files_to_remove):
    """Insert batch of rows into BigQuery"""
    table_ref = get_table_ref(table_name)
    
    # Check schema and add new columns if needed
    existing_schema = get_existing_schema(table_ref)
    new_fields = {}
    
    for row in rows:
        for key, value in row.items():
            if key not in existing_schema and key not in new_fields:
                new_fields[key] = infer_bq_type(value)
    
    if new_fields:
        logging.info(f"🔧 Schema evolution needed for {table_name}")
        add_new_columns(table_ref, new_fields)
    
    # Insert batch
    try:
        errors = bq_client.insert_rows_json(table_ref, rows)
        if errors:
            logging.error(f"❌ BigQuery insert errors for {table_name}: {errors[:5]}")  # Show first 5
            return False
        else:
            logging.info(f"✅ Inserted {len(rows)} rows into {table_name}")
            
            # Remove successfully processed files
            for filepath in files_to_remove:
                try:
                    os.remove(filepath)
                except OSError as e:
                    logging.error(f"Failed to remove {filepath}: {e}")
            
            return True
    except Exception as e:
        logging.error(f"❌ Failed to insert batch into {table_name}: {e}")
        return False

def scan_and_batch_files():
    """Scan IRIS data directory and batch files by table"""
    batches = defaultdict(lambda: {'rows': [], 'files': []})
    file_count = 0
    
    if not os.path.exists(IRIS_DATA_DIR):
        logging.error(f"IRIS data directory not found: {IRIS_DATA_DIR}")
        return batches, 0
    
    # Scan all dataset directories
    for dataset_dir in os.listdir(IRIS_DATA_DIR):
        dataset_path = os.path.join(IRIS_DATA_DIR, dataset_dir)
        
        if not os.path.isdir(dataset_path):
            continue
        
        # Get table name from dataset
        dataset_upper = dataset_dir.upper()
        table_name = DATASET_TABLE_MAPPING.get(dataset_upper)
        
        if not table_name:
            logging.warning(f"⚠️  Unknown dataset: {dataset_dir} - skipping")
            continue
        
        # Process JSON files in this dataset
        for filename in os.listdir(dataset_path):
            if not filename.endswith('.json'):
                continue
            
            if file_count >= MAX_FILES_PER_SCAN:
                logging.info(f"⚠️  Reached max files per scan ({MAX_FILES_PER_SCAN})")
                return batches, file_count
            
            filepath = os.path.join(dataset_path, filename)
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Add to batch
                batches[table_name]['rows'].append(data)
                batches[table_name]['files'].append(filepath)
                file_count += 1
                
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"❌ Failed to read {filepath}: {e}")
                # Remove bad file
                try:
                    os.remove(filepath)
                except OSError:
                    pass
    
    return batches, file_count

def process_all_batches():
    """Process all batches with size limits"""
    batches, total_files = scan_and_batch_files()
    
    if total_files == 0:
        return 0
    
    logging.info(f"📦 Found {total_files} files across {len(batches)} tables")
    
    total_processed = 0
    
    for table_name, batch_data in batches.items():
        rows = batch_data['rows']
        files = batch_data['files']
        
        logging.info(f"📊 Processing {len(rows)} rows for {table_name}")
        
        # Split into chunks if needed
        for i in range(0, len(rows), BATCH_SIZE):
            chunk_rows = rows[i:i + BATCH_SIZE]
            chunk_files = files[i:i + BATCH_SIZE]
            
            success = process_batch(table_name, chunk_rows, chunk_files)
            
            if success:
                total_processed += len(chunk_rows)
            else:
                logging.error(f"⚠️  Failed to process chunk {i//BATCH_SIZE + 1} for {table_name}")
            
            # Small delay between chunks to avoid rate limits
            if len(rows) > BATCH_SIZE:
                time.sleep(0.5)
    
    return total_processed

def main():
    """Main loop - continuously process IRIS messages"""
    logging.info("=" * 60)
    logging.info("🚀 IRIS to BigQuery Batch Processor")
    logging.info("=" * 60)
    logging.info(f"📂 Watching: {IRIS_DATA_DIR}")
    logging.info(f"📊 Project: {BQ_PROJECT}")
    logging.info(f"📦 Dataset: {BQ_DATASET}")
    logging.info(f"⚙️  Batch Size: {BATCH_SIZE} rows")
    logging.info(f"⏱️  Scan Interval: {BATCH_WAIT_SECONDS}s")
    logging.info("=" * 60)
    
    cycle_count = 0
    total_messages_processed = 0
    
    while True:
        cycle_count += 1
        cycle_start = time.time()
        
        try:
            processed = process_all_batches()
            total_messages_processed += processed
            
            cycle_time = time.time() - cycle_start
            
            if processed > 0:
                rate = processed / cycle_time if cycle_time > 0 else 0
                logging.info(
                    f"📈 Cycle {cycle_count}: Processed {processed} messages in {cycle_time:.1f}s "
                    f"({rate:.0f} msg/s) | Total: {total_messages_processed}"
                )
            
        except KeyboardInterrupt:
            logging.info("\n👋 Shutting down gracefully...")
            break
        except Exception as e:
            logging.error(f"❌ Error in processing cycle: {e}", exc_info=True)
        
        # Wait before next scan
        time.sleep(BATCH_WAIT_SECONDS)

if __name__ == "__main__":
    main()
