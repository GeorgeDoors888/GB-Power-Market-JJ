#!/usr/bin/env python3
"""
Enhanced BigQuery Data Loader for Elexon & NESO Data

This script loads JSON data from Google Cloud Storage into BigQuery tables.
It handles schema inference, data transformation, and validates the data
before loading. It can be used for both batch loading and incremental updates.

Features:
- Automatic schema detection and validation
- Data transformation for BigQuery compatibility
- Support for incremental loading and backfills
- Comprehensive logging and error handling
- Parallelized loading for efficiency
"""

import os
import json
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Set
import concurrent.futures
import re

from google.cloud import storage
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'bq_data_loader_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger('bq_data_loader')

# Default settings
DEFAULT_BUCKET_NAME = 'jibber-jabber-knowledge-bmrs-data'
DEFAULT_PROJECT_ID = 'jibber-jabber-knowledge'
DEFAULT_DATASET_ID = 'uk_energy_prod'

class EnhancedBigQueryLoader:
    """
    Enhanced BigQuery loader for Elexon and NESO data
    """
    
    def __init__(self, bucket_name: str = DEFAULT_BUCKET_NAME,
                 project_id: str = DEFAULT_PROJECT_ID, 
                 dataset_id: str = DEFAULT_DATASET_ID):
        """
        Initialize the loader with Google Cloud settings
        """
        # Google Cloud settings
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.dataset_id = dataset_id
        
        # Initialize cloud clients
        try:
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            logger.info(f"✅ Connected to GCS bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to GCS: {e}")
            raise
            
        try:
            self.bigquery_client = bigquery.Client(project=self.project_id)
            logger.info(f"✅ Connected to BigQuery project: {self.project_id}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to BigQuery: {e}")
            raise
        
        # Dataset mappings configuration
        self._configure_dataset_mappings()
        
    def _configure_dataset_mappings(self):
        """
        Configure the dataset to BigQuery table mappings
        """
        self.dataset_mappings = {
            # Elexon BMRS Datasets
            'bid_offer_acceptances': {
                'table_name': 'elexon_bid_offer_acceptances',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/bid_offer_acceptances/',
                'schema_mapping': {
                    'acceptanceNumber': 'acceptance_number',
                    'acceptanceTime': 'acceptance_time',
                    'bmUnitId': 'bm_unit_id',
                    'leadPartyName': 'lead_party_name',
                    'ngcBmUnit': 'ngc_bm_unit',
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'soFlag': 'so_flag',
                    'storFlag': 'stor_flag',
                    'timeFlag': 'time_flag',
                    'acceptanceVolume': 'acceptance_volume',
                    'acceptancePrice': 'acceptance_price'
                }
            },
            'generation_outturn': {
                'table_name': 'elexon_generation_outturn',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/generation_outturn/',
                'schema_mapping': {
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'fuelType': 'fuel_type',
                    'quantity': 'quantity',
                    'publishTime': 'publish_time'
                }
            },
            'demand_outturn': {
                'table_name': 'elexon_demand_outturn',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/demand_outturn/',
                'schema_mapping': {
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'initialDemandOutturn': 'initial_demand_outturn',
                    'finalDemandOutturn': 'final_demand_outturn',
                    'publishTime': 'publish_time'
                }
            },
            'system_warnings': {
                'table_name': 'elexon_system_warnings',
                'date_field': 'published_time',
                'gcs_prefix': 'bmrs_data/system_warnings/',
                'schema_mapping': {
                    'warningText': 'warning_text',
                    'publishedTime': 'published_time',
                    'warningType': 'warning_type',
                    'messageId': 'message_id'
                }
            },
            'frequency': {
                'table_name': 'elexon_frequency',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/frequency/',
                'schema_mapping': {
                    'settlementDate': 'settlement_date',
                    'measurementTime': 'measurement_time',
                    'frequency': 'frequency',
                    'recordType': 'record_type'
                }
            },
            'fuel_instructions': {
                'table_name': 'elexon_fuel_instructions',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/fuel_instructions/',
                'schema_mapping': {
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'fuelType': 'fuel_type',
                    'generation': 'generation',
                    'timestamp': 'timestamp'
                }
            },
            'individual_generation': {
                'table_name': 'elexon_individual_generation',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/individual_generation/',
                'schema_mapping': {
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'bmUnitId': 'bm_unit_id',
                    'powerGeneration': 'power_generation',
                    'recordTime': 'record_time'
                }
            },
            'market_index': {
                'table_name': 'elexon_market_index',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/market_index/',
                'schema_mapping': {
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'dataProvider': 'data_provider',
                    'price': 'price',
                    'volume': 'volume',
                    'timestamp': 'timestamp'
                }
            },
            'wind_forecasts': {
                'table_name': 'elexon_wind_forecasts',
                'date_field': 'publish_date',
                'gcs_prefix': 'bmrs_data/wind_forecasts/',
                'schema_mapping': {
                    'publishDate': 'publish_date',
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'forecastWindGeneration': 'forecast_wind_generation',
                    'actualWindGeneration': 'actual_wind_generation'
                }
            },
            'balancing_services': {
                'table_name': 'elexon_balancing_services',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/balancing_services/',
                'schema_mapping': {
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'adjustmentValue': 'adjustment_value',
                    'adjustmentType': 'adjustment_type',
                    'timestamp': 'timestamp'
                }
            },
            'carbon_intensity': {
                'table_name': 'elexon_carbon_intensity',
                'date_field': 'settlement_date',
                'gcs_prefix': 'bmrs_data/carbon_intensity/',
                'schema_mapping': {
                    'settlementDate': 'settlement_date',
                    'settlementPeriod': 'settlement_period',
                    'intensity': 'intensity',
                    'timestamp': 'timestamp'
                }
            }
        }
        
    def list_gcs_files(self, dataset_key: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> List[str]:
        """
        List GCS files for a dataset
        
        Args:
            dataset_key: Key of the dataset
            start_date: Optional start date filter in YYYY-MM-DD format
            end_date: Optional end date filter in YYYY-MM-DD format
            
        Returns:
            List of GCS file paths
        """
        if dataset_key not in self.dataset_mappings:
            logger.error(f"❌ Unknown dataset: {dataset_key}")
            return []
            
        prefix = self.dataset_mappings[dataset_key]['gcs_prefix']
        logger.info(f"⏳ Listing files for {dataset_key} with prefix {prefix}")
        
        # Parse date filters if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # List all blobs with the prefix
        blobs = list(self.bucket.list_blobs(prefix=prefix))
        
        # Filter by date if needed
        if start_dt or end_dt:
            # Compile regex pattern for date extraction
            date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
            
            filtered_blobs = []
            for blob in blobs:
                # Extract dates from the filename
                matches = date_pattern.findall(blob.name)
                if not matches:
                    # If no date found, include the blob (could be a metadata file)
                    filtered_blobs.append(blob)
                    continue
                
                # Check each date in the filename
                for date_str in matches:
                    try:
                        file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        
                        # Apply date filters
                        if start_dt and file_date < start_dt:
                            continue
                        if end_dt and file_date > end_dt:
                            continue
                            
                        # If we get here, the file is within the date range
                        filtered_blobs.append(blob)
                        break
                        
                    except ValueError:
                        # Not a valid date, skip this match
                        continue
                        
            blobs = filtered_blobs
        
        # Return blob names
        return [blob.name for blob in blobs]
        
    def load_file_to_bigquery(self, gcs_file: str, dataset_key: str) -> bool:
        """
        Load a single GCS file to BigQuery
        
        Args:
            gcs_file: GCS file path
            dataset_key: Dataset key
            
        Returns:
            True if successful, False otherwise
        """
        if dataset_key not in self.dataset_mappings:
            logger.error(f"❌ Unknown dataset: {dataset_key}")
            return False
            
        mapping = self.dataset_mappings[dataset_key]
        table_id = f"{self.project_id}.{self.dataset_id}.{mapping['table_name']}"
        
        logger.info(f"⏳ Loading {gcs_file} to {table_id}")
        
        try:
            # Download the file
            blob = self.bucket.blob(gcs_file)
            content = blob.download_as_string()
            data = json.loads(content)
            
            # Transform data according to schema mapping
            transformed_data = self._transform_data(data, dataset_key)
            
            if not transformed_data:
                logger.warning(f"⚠️ No data to load from {gcs_file}")
                return True  # Not an error, just no data
                
            # Write to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as tmp:
                for item in transformed_data:
                    tmp.write((json.dumps(item) + '\n').encode('utf-8'))
                tmp_name = tmp.name
                
            logger.debug(f"📝 Created temporary file {tmp_name} with {len(transformed_data)} records")
            
            # Load to BigQuery
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                autodetect=True  # Can be set to False if explicit schema is preferred
            )
            
            with open(tmp_name, 'rb') as source_file:
                job = self.bigquery_client.load_table_from_file(
                    source_file, table_id, job_config=job_config
                )
                
            # Wait for the job to complete
            job.result()
            
            # Clean up temporary file
            os.unlink(tmp_name)
            
            logger.info(f"✅ Loaded {len(transformed_data)} records from {gcs_file} to {table_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading {gcs_file} to {table_id}: {str(e)}")
            return False
            
    def _transform_data(self, data: Any, dataset_key: str) -> List[Dict]:
        """
        Transform data according to schema mapping
        
        Args:
            data: Raw data from GCS
            dataset_key: Dataset key
            
        Returns:
            Transformed data ready for BigQuery
        """
        mapping = self.dataset_mappings[dataset_key]
        schema_mapping = mapping['schema_mapping']
        
        # Handle different data structures from Elexon API
        if 'data' in data and isinstance(data['data'], list):
            items = data['data']
        elif 'data' in data and isinstance(data['data'], dict) and 'items' in data['data']:
            items = data['data']['items']
        elif isinstance(data, list):
            items = data
        elif isinstance(data, dict) and 'items' in data:
            items = data['items']
        else:
            logger.warning(f"⚠️ Unexpected data structure for {dataset_key}")
            logger.debug(f"Data sample: {str(data)[:1000]}...")
            return []
            
        transformed_items = []
        
        for item in items:
            transformed_item = {}
            
            # Apply schema mapping
            for source_key, target_key in schema_mapping.items():
                # Handle nested structures with dot notation
                if '.' in source_key:
                    parts = source_key.split('.')
                    value = item
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                else:
                    value = item.get(source_key)
                    
                transformed_item[target_key] = value
                
            # Add metadata
            transformed_item['_gcs_source'] = dataset_key
            transformed_item['_load_timestamp'] = datetime.now().isoformat()
            
            transformed_items.append(transformed_item)
            
        return transformed_items
        
    def load_dataset(self, dataset_key: str, start_date: Optional[str] = None,
                    end_date: Optional[str] = None, max_workers: int = 4) -> Tuple[int, int]:
        """
        Load a dataset to BigQuery
        
        Args:
            dataset_key: Dataset key
            start_date: Optional start date filter in YYYY-MM-DD format
            end_date: Optional end date filter in YYYY-MM-DD format
            max_workers: Maximum number of parallel workers
            
        Returns:
            Tuple of (files processed, files succeeded)
        """
        if dataset_key not in self.dataset_mappings:
            logger.error(f"❌ Unknown dataset: {dataset_key}")
            return (0, 0)
            
        # List files to process
        files = self.list_gcs_files(dataset_key, start_date, end_date)
        
        if not files:
            logger.warning(f"⚠️ No files found for {dataset_key}")
            return (0, 0)
            
        logger.info(f"⏳ Processing {len(files)} files for {dataset_key}")
        
        # Check if table exists
        table_id = f"{self.project_id}.{self.dataset_id}.{self.dataset_mappings[dataset_key]['table_name']}"
        try:
            self.bigquery_client.get_table(table_id)
        except NotFound:
            logger.error(f"❌ Table {table_id} not found. Please create the table first.")
            return (0, 0)
            
        # Process files in parallel
        succeeded = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.load_file_to_bigquery, file, dataset_key): file
                for file in files
            }
            
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    if future.result():
                        succeeded += 1
                except Exception as e:
                    logger.error(f"❌ Error processing {file}: {str(e)}")
                    
        logger.info(f"✅ Loaded {succeeded}/{len(files)} files for {dataset_key}")
        return (len(files), succeeded)
        
    def load_all_datasets(self, start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         dataset_keys: Optional[List[str]] = None,
                         max_workers_per_dataset: int = 4) -> Dict[str, Tuple[int, int]]:
        """
        Load all datasets to BigQuery
        
        Args:
            start_date: Optional start date filter in YYYY-MM-DD format
            end_date: Optional end date filter in YYYY-MM-DD format
            dataset_keys: Optional list of dataset keys to load
            max_workers_per_dataset: Maximum number of parallel workers per dataset
            
        Returns:
            Dictionary of dataset keys and (files processed, files succeeded) tuples
        """
        results = {}
        
        # Determine which datasets to load
        keys_to_load = dataset_keys or list(self.dataset_mappings.keys())
        
        logger.info(f"⏳ Loading {len(keys_to_load)} datasets to BigQuery")
        
        # Process each dataset
        for key in keys_to_load:
            results[key] = self.load_dataset(key, start_date, end_date, max_workers_per_dataset)
            
        return results
        
    def validate_dataset_schema(self, dataset_key: str) -> bool:
        """
        Validate the schema of a dataset
        
        Args:
            dataset_key: Dataset key
            
        Returns:
            True if valid, False otherwise
        """
        if dataset_key not in self.dataset_mappings:
            logger.error(f"❌ Unknown dataset: {dataset_key}")
            return False
            
        table_id = f"{self.project_id}.{self.dataset_id}.{self.dataset_mappings[dataset_key]['table_name']}"
        
        try:
            # Get table schema
            table = self.bigquery_client.get_table(table_id)
            
            # Get field names
            field_names = {field.name for field in table.schema}
            
            # Check if all mapped fields exist
            mapping = self.dataset_mappings[dataset_key]['schema_mapping']
            target_fields = set(mapping.values())
            
            missing_fields = target_fields - field_names
            
            if missing_fields:
                logger.warning(f"⚠️ Missing fields in {table_id}: {missing_fields}")
                return False
                
            logger.info(f"✅ Schema validation passed for {table_id}")
            return True
            
        except NotFound:
            logger.error(f"❌ Table {table_id} not found")
            return False
        except Exception as e:
            logger.error(f"❌ Error validating schema for {table_id}: {str(e)}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enhanced BigQuery Data Loader')
    parser.add_argument('--start-date', type=str,
                        help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=str,
                        help='End date in YYYY-MM-DD format')
    parser.add_argument('--datasets', type=str, nargs='*',
                        help='Specific datasets to load (default: all)')
    parser.add_argument('--bucket', type=str, default=DEFAULT_BUCKET_NAME,
                        help=f'GCS bucket name (default: {DEFAULT_BUCKET_NAME})')
    parser.add_argument('--project', type=str, default=DEFAULT_PROJECT_ID,
                        help=f'GCP project ID (default: {DEFAULT_PROJECT_ID})')
    parser.add_argument('--dataset-id', type=str, default=DEFAULT_DATASET_ID,
                        help=f'BigQuery dataset ID (default: {DEFAULT_DATASET_ID})')
    parser.add_argument('--max-workers', type=int, default=4,
                        help='Maximum number of parallel workers per dataset (default: 4)')
    parser.add_argument('--list-datasets', action='store_true',
                        help='List available datasets and exit')
    parser.add_argument('--validate-schema', action='store_true',
                        help='Validate dataset schemas')
    
    args = parser.parse_args()
    
    try:
        loader = EnhancedBigQueryLoader(
            bucket_name=args.bucket,
            project_id=args.project,
            dataset_id=args.dataset_id
        )
        
        if args.list_datasets:
            print("\nAvailable Datasets:")
            print("------------------")
            for key, mapping in loader.dataset_mappings.items():
                print(f"{key}: {mapping['table_name']}")
                print(f"  GCS prefix: {mapping['gcs_prefix']}")
                print(f"  Date field: {mapping['date_field']}")
                print()
            return
            
        if args.validate_schema:
            datasets_to_validate = args.datasets or list(loader.dataset_mappings.keys())
            valid_count = 0
            
            for key in datasets_to_validate:
                if loader.validate_dataset_schema(key):
                    valid_count += 1
                    
            print(f"\nSchema validation: {valid_count}/{len(datasets_to_validate)} datasets valid")
            return
            
        # Load datasets
        results = loader.load_all_datasets(
            start_date=args.start_date,
            end_date=args.end_date,
            dataset_keys=args.datasets,
            max_workers_per_dataset=args.max_workers
        )
        
        # Print summary
        print("\nLoad Summary:")
        print("------------")
        total_processed = sum(processed for processed, _ in results.values())
        total_succeeded = sum(succeeded for _, succeeded in results.values())
        
        for key, (processed, succeeded) in results.items():
            print(f"{key}: {succeeded}/{processed} files succeeded")
            
        print(f"\nTotal: {total_succeeded}/{total_processed} files succeeded")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
