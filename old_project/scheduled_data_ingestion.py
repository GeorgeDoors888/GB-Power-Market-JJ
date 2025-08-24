#!/usr/bin/env python3
"""
Scheduled Data Ingestion Pipeline
---------------------------------
This script orchestrates the entire data ingestion process for the UK Energy Dashboard.
It handles both historical backfill and incremental updates of energy market data.

Key features:
- Configurable data sources and time ranges
- Automatic schema detection and enforcement
- Logging and error reporting
- Resumable downloads
- Integration with cloud_data_collector.py and fast_cloud_backfill.py

Usage:
    python scheduled_data_ingestion.py --mode [backfill|incremental] --days [number_of_days]
"""

import os
import sys
import argparse
import logging
import subprocess
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from google.cloud import bigquery
from google.cloud import storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_ingestion.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "jibber-jabber-knowledge"
SOURCE_DATASET = "uk_energy"
TARGET_DATASET = "uk_energy_prod"
BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"
DATA_SOURCES = [
    {
        "name": "neso_demand_forecasts",
        "source_type": "elexon_api",
        "endpoint": "/demand/forecast",
        "frequency": "daily",
        "script": "cloud_elexon_downloader.py"
    },
    {
        "name": "neso_wind_forecasts",
        "source_type": "elexon_api",
        "endpoint": "/generation/wind/forecast",
        "frequency": "daily",
        "script": "cloud_elexon_downloader.py"
    },
    {
        "name": "neso_balancing_services",
        "source_type": "elexon_api",
        "endpoint": "/balancing/services",
        "frequency": "daily",
        "script": "cloud_elexon_downloader.py"
    },
    {
        "name": "elexon_system_warnings",
        "source_type": "elexon_api",
        "endpoint": "/system/warnings",
        "frequency": "daily",
        "script": "cloud_bmrs_downloader.py"
    },
    {
        "name": "neso_carbon_intensity",
        "source_type": "carbon_api",
        "endpoint": "/intensity",
        "frequency": "hourly",
        "script": "cloud_carbon_downloader.py"
    },
    {
        "name": "neso_interconnector_flows",
        "source_type": "elexon_api",
        "endpoint": "/interconnectors/flows",
        "frequency": "hourly",
        "script": "cloud_elexon_downloader.py"
    }
]

def init_clients():
    """Initialize BigQuery and Cloud Storage clients."""
    try:
        bq_client = bigquery.Client(project=PROJECT_ID)
        storage_client = storage.Client(project=PROJECT_ID)
        return bq_client, storage_client
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        return None, None

def create_table_if_not_exists(bq_client, source_table: str, target_table: str):
    """Create a table in the target dataset if it doesn't exist, using schema from source."""
    try:
        # Get source table reference
        source_table_ref = f"{PROJECT_ID}.{SOURCE_DATASET}.{source_table}"
        target_table_ref = f"{PROJECT_ID}.{TARGET_DATASET}.{target_table}"
        
        # Check if target table exists
        try:
            bq_client.get_table(target_table_ref)
            logger.info(f"Table {target_table} already exists.")
            return True
        except Exception:
            # Table doesn't exist, create it from source schema
            pass
        
        # Get schema from source table
        source_table_obj = bq_client.get_table(source_table_ref)
        schema = source_table_obj.schema
        
        # Check if source table has time partitioning
        time_partitioning = None
        clustering_fields = None
        
        if source_table_obj.time_partitioning:
            time_partitioning = bigquery.TimePartitioning(
                type_=source_table_obj.time_partitioning.type_,
                field=source_table_obj.time_partitioning.field
            )
        
        if source_table_obj.clustering_fields:
            clustering_fields = source_table_obj.clustering_fields
        
        # Create new table
        new_table = bigquery.Table(target_table_ref, schema=schema)
        if time_partitioning:
            new_table.time_partitioning = time_partitioning
        if clustering_fields:
            new_table.clustering_fields = clustering_fields
            
        new_table.description = f"Copy of {source_table} with real data"
        
        bq_client.create_table(new_table)
        logger.info(f"Created table {target_table}")
        return True
    except Exception as e:
        logger.error(f"Failed to create table {target_table}: {e}")
        return False

def download_data(data_source: Dict, start_date: datetime, end_date: datetime):
    """Download data for a specific source and date range."""
    try:
        script = data_source["script"]
        source_name = data_source["name"]
        
        # Check if script exists
        if not Path(script).exists():
            logger.error(f"Script {script} not found.")
            return False
        
        # Prepare command with appropriate parameters
        cmd = [
            sys.executable,
            script,
            "--source", source_name,
            "--start-date", start_date.strftime("%Y-%m-%d"),
            "--end-date", end_date.strftime("%Y-%m-%d"),
            "--project", PROJECT_ID,
            "--bucket", BUCKET_NAME,
            "--dataset", TARGET_DATASET
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully downloaded data for {source_name}")
            logger.debug(result.stdout)
            return True
        else:
            logger.error(f"Failed to download data for {source_name}: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error downloading data for {data_source['name']}: {e}")
        return False

def process_gcs_to_bigquery(bq_client, data_source: Dict):
    """Process data from GCS to BigQuery using the ingestion loader."""
    try:
        source_name = data_source["name"]
        target_table = f"{PROJECT_ID}.{TARGET_DATASET}.{source_name}"
        
        # Run the ingestion loader script
        cmd = [
            sys.executable,
            "ingestion_loader.py",
            "--source", source_name,
            "--target-dataset", TARGET_DATASET,
            "--project", PROJECT_ID
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully loaded data into {target_table}")
            logger.debug(result.stdout)
            return True
        else:
            logger.error(f"Failed to load data into {target_table}: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error processing data for {data_source['name']}: {e}")
        return False

def validate_data(bq_client, table_name: str):
    """Validate loaded data in BigQuery."""
    try:
        table_ref = f"{PROJECT_ID}.{TARGET_DATASET}.{table_name}"
        query = f"SELECT COUNT(*) as count FROM `{table_ref}`"
        
        query_job = bq_client.query(query)
        results = query_job.result()
        
        for row in results:
            count = row.count
            logger.info(f"Table {table_name} has {count} rows")
            return count > 0
    except Exception as e:
        logger.error(f"Error validating data for {table_name}: {e}")
        return False

def run_backfill(bq_client, days: int = 30):
    """Run a historical backfill for all data sources."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Starting backfill from {start_date.date()} to {end_date.date()}")
    
    for data_source in DATA_SOURCES:
        source_name = data_source["name"]
        logger.info(f"Processing {source_name}...")
        
        # Ensure table exists
        table_exists = create_table_if_not_exists(bq_client, source_name, source_name)
        if not table_exists:
            continue
        
        # Download data
        download_success = download_data(data_source, start_date, end_date)
        if not download_success:
            continue
        
        # Process data to BigQuery
        load_success = process_gcs_to_bigquery(bq_client, data_source)
        if not load_success:
            continue
        
        # Validate data
        validate_success = validate_data(bq_client, source_name)
        if not validate_success:
            logger.warning(f"Data validation failed for {source_name}")
    
    logger.info("Backfill completed")

def run_incremental(bq_client):
    """Run incremental update for all data sources."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)  # Get last 2 days to ensure overlap
    
    logger.info(f"Starting incremental update from {start_date.date()} to {end_date.date()}")
    
    for data_source in DATA_SOURCES:
        source_name = data_source["name"]
        logger.info(f"Processing {source_name}...")
        
        # Ensure table exists
        table_exists = create_table_if_not_exists(bq_client, source_name, source_name)
        if not table_exists:
            continue
        
        # Download data
        download_success = download_data(data_source, start_date, end_date)
        if not download_success:
            continue
        
        # Process data to BigQuery
        load_success = process_gcs_to_bigquery(bq_client, data_source)
        if not load_success:
            continue
        
        # Validate data
        validate_success = validate_data(bq_client, source_name)
        if not validate_success:
            logger.warning(f"Data validation failed for {source_name}")
    
    logger.info("Incremental update completed")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Scheduled Data Ingestion Pipeline')
    parser.add_argument('--mode', choices=['backfill', 'incremental'], default='incremental',
                       help='Operation mode: backfill for historical data, incremental for recent data')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to backfill (only used with backfill mode)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting scheduled data ingestion in {args.mode} mode")
    
    # Initialize clients
    bq_client, storage_client = init_clients()
    if not bq_client or not storage_client:
        logger.error("Failed to initialize clients. Exiting.")
        sys.exit(1)
    
    try:
        if args.mode == 'backfill':
            run_backfill(bq_client, args.days)
        else:
            run_incremental(bq_client)
    except Exception as e:
        logger.error(f"Error during {args.mode} operation: {e}")
        sys.exit(1)
    
    logger.info("Scheduled data ingestion completed successfully")

if __name__ == "__main__":
    main()
