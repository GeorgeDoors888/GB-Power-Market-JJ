#!/usr/bin/env python3
"""
BigQuery Table Creation Script

This script creates all the required BigQuery tables for the Elexon & NESO
data collection system. It defines the schemas based on the API data structure
and creates tables if they don't already exist.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

from google.cloud import bigquery
from google.api_core.exceptions import Conflict, NotFound

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'create_tables_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger('create_tables')

# Default settings
DEFAULT_PROJECT_ID = 'jibber-jabber-knowledge'
DEFAULT_DATASET_ID = 'uk_energy_prod'
DEFAULT_LOCATION = 'europe-west2'  # London region

class BigQueryTableCreator:
    """
    Creates BigQuery tables for Elexon & NESO data
    """
    
    def __init__(self, project_id: str = DEFAULT_PROJECT_ID,
                 dataset_id: str = DEFAULT_DATASET_ID,
                 location: str = DEFAULT_LOCATION):
        """
        Initialize the table creator with BigQuery settings
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.location = location
        
        # Initialize BigQuery client
        try:
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"✅ Connected to BigQuery project: {self.project_id}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to BigQuery: {e}")
            raise
            
        # Define table schemas
        self._define_table_schemas()
        
    def _define_table_schemas(self):
        """
        Define the schemas for all tables
        """
        # Common fields that appear in many tables
        self.common_fields = {
            'settlement_date': bigquery.SchemaField(
                name='settlement_date', 
                field_type='DATE', 
                mode='REQUIRED',
                description='The settlement date'
            ),
            'settlement_period': bigquery.SchemaField(
                name='settlement_period', 
                field_type='INTEGER', 
                mode='NULLABLE',
                description='The settlement period (1-48 or 1-50 during clock changes)'
            ),
            'timestamp': bigquery.SchemaField(
                name='timestamp', 
                field_type='TIMESTAMP', 
                mode='NULLABLE',
                description='Timestamp of the data point'
            ),
            '_gcs_source': bigquery.SchemaField(
                name='_gcs_source', 
                field_type='STRING', 
                mode='NULLABLE',
                description='Source GCS path'
            ),
            '_load_timestamp': bigquery.SchemaField(
                name='_load_timestamp', 
                field_type='TIMESTAMP', 
                mode='NULLABLE',
                description='Timestamp when data was loaded to BigQuery'
            )
        }
        
        # Define table schemas
        self.table_schemas = {
            'elexon_bid_offer_acceptances': [
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='acceptance_number', 
                    field_type='INTEGER', 
                    mode='NULLABLE',
                    description='The acceptance number'
                ),
                bigquery.SchemaField(
                    name='acceptance_time', 
                    field_type='TIMESTAMP', 
                    mode='NULLABLE',
                    description='The time of the acceptance'
                ),
                bigquery.SchemaField(
                    name='bm_unit_id', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The BM unit identifier'
                ),
                bigquery.SchemaField(
                    name='lead_party_name', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The lead party name'
                ),
                bigquery.SchemaField(
                    name='ngc_bm_unit', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The NGC BM unit identifier'
                ),
                bigquery.SchemaField(
                    name='so_flag', 
                    field_type='BOOLEAN', 
                    mode='NULLABLE',
                    description='System Operator flag'
                ),
                bigquery.SchemaField(
                    name='stor_flag', 
                    field_type='BOOLEAN', 
                    mode='NULLABLE',
                    description='Short Term Operating Reserve flag'
                ),
                bigquery.SchemaField(
                    name='time_flag', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='Time flag'
                ),
                bigquery.SchemaField(
                    name='acceptance_volume', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='Acceptance volume in MW'
                ),
                bigquery.SchemaField(
                    name='acceptance_price', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='Acceptance price in £/MWh'
                ),
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_generation_outturn': [
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='fuel_type', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The fuel type'
                ),
                bigquery.SchemaField(
                    name='quantity', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The generation quantity in MW'
                ),
                bigquery.SchemaField(
                    name='publish_time', 
                    field_type='TIMESTAMP', 
                    mode='NULLABLE',
                    description='The time when the data was published'
                ),
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_demand_outturn': [
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='initial_demand_outturn', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='Initial demand outturn in MW'
                ),
                bigquery.SchemaField(
                    name='final_demand_outturn', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='Final demand outturn in MW'
                ),
                bigquery.SchemaField(
                    name='publish_time', 
                    field_type='TIMESTAMP', 
                    mode='NULLABLE',
                    description='The time when the data was published'
                ),
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_system_warnings': [
                bigquery.SchemaField(
                    name='warning_text', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The warning text'
                ),
                bigquery.SchemaField(
                    name='published_time', 
                    field_type='TIMESTAMP', 
                    mode='NULLABLE',
                    description='The time when the warning was published'
                ),
                bigquery.SchemaField(
                    name='warning_type', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The type of warning'
                ),
                bigquery.SchemaField(
                    name='message_id', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The message identifier'
                ),
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_frequency': [
                self.common_fields['settlement_date'],
                bigquery.SchemaField(
                    name='measurement_time', 
                    field_type='TIMESTAMP', 
                    mode='NULLABLE',
                    description='The time of the frequency measurement'
                ),
                bigquery.SchemaField(
                    name='frequency', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The frequency measurement in Hz'
                ),
                bigquery.SchemaField(
                    name='record_type', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The record type'
                ),
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_fuel_instructions': [
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='fuel_type', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The fuel type'
                ),
                bigquery.SchemaField(
                    name='generation', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The generation in MW'
                ),
                self.common_fields['timestamp'],
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_individual_generation': [
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='bm_unit_id', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The BM unit identifier'
                ),
                bigquery.SchemaField(
                    name='power_generation', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The power generation in MW'
                ),
                bigquery.SchemaField(
                    name='record_time', 
                    field_type='TIMESTAMP', 
                    mode='NULLABLE',
                    description='The time of the record'
                ),
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_market_index': [
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='data_provider', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The data provider'
                ),
                bigquery.SchemaField(
                    name='price', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The price in £/MWh'
                ),
                bigquery.SchemaField(
                    name='volume', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The volume in MWh'
                ),
                self.common_fields['timestamp'],
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_wind_forecasts': [
                bigquery.SchemaField(
                    name='publish_date', 
                    field_type='DATE', 
                    mode='NULLABLE',
                    description='The date when the forecast was published'
                ),
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='forecast_wind_generation', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The forecasted wind generation in MW'
                ),
                bigquery.SchemaField(
                    name='actual_wind_generation', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The actual wind generation in MW (if available)'
                ),
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_balancing_services': [
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='adjustment_value', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The adjustment value'
                ),
                bigquery.SchemaField(
                    name='adjustment_type', 
                    field_type='STRING', 
                    mode='NULLABLE',
                    description='The type of adjustment'
                ),
                self.common_fields['timestamp'],
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ],
            
            'elexon_carbon_intensity': [
                self.common_fields['settlement_date'],
                self.common_fields['settlement_period'],
                bigquery.SchemaField(
                    name='intensity', 
                    field_type='FLOAT', 
                    mode='NULLABLE',
                    description='The carbon intensity in gCO2/kWh'
                ),
                self.common_fields['timestamp'],
                self.common_fields['_gcs_source'],
                self.common_fields['_load_timestamp']
            ]
        }
        
    def ensure_dataset_exists(self) -> bool:
        """
        Ensure the BigQuery dataset exists
        
        Returns:
            True if the dataset exists or was created, False otherwise
        """
        dataset_id = f"{self.project_id}.{self.dataset_id}"
        
        try:
            # Try to get the dataset
            self.client.get_dataset(dataset_id)
            logger.info(f"✅ Dataset {dataset_id} already exists")
            return True
        except NotFound:
            # Dataset doesn't exist, create it
            logger.info(f"⏳ Creating dataset {dataset_id}")
            
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = self.location
            dataset.description = "UK Energy Data from Elexon BMRS and NESO"
            
            try:
                self.client.create_dataset(dataset)
                logger.info(f"✅ Dataset {dataset_id} created")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to create dataset {dataset_id}: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking dataset {dataset_id}: {e}")
            return False
            
    def create_table(self, table_name: str) -> bool:
        """
        Create a BigQuery table if it doesn't exist
        
        Args:
            table_name: Name of the table to create
            
        Returns:
            True if the table exists or was created, False otherwise
        """
        if table_name not in self.table_schemas:
            logger.error(f"❌ Unknown table: {table_name}")
            return False
            
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        try:
            # Try to get the table
            self.client.get_table(table_id)
            logger.info(f"✅ Table {table_id} already exists")
            return True
        except NotFound:
            # Table doesn't exist, create it
            logger.info(f"⏳ Creating table {table_id}")
            
            schema = self.table_schemas[table_name]
            table = bigquery.Table(table_id, schema=schema)
            table.description = f"Elexon BMRS data for {table_name}"
            
            # Set time partitioning
            partition_field = 'settlement_date'
            if table_name == 'elexon_system_warnings':
                partition_field = 'published_time'
                
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field=partition_field
            )
            
            # Set clustering fields
            clustering_fields = ['settlement_period']
            if table_name == 'elexon_bid_offer_acceptances':
                clustering_fields.append('bm_unit_id')
            elif table_name == 'elexon_generation_outturn':
                clustering_fields.append('fuel_type')
            elif table_name == 'elexon_individual_generation':
                clustering_fields.append('bm_unit_id')
                
            if table_name != 'elexon_system_warnings':
                table.clustering_fields = clustering_fields
            
            try:
                self.client.create_table(table)
                logger.info(f"✅ Table {table_id} created")
                return True
            except Conflict:
                logger.info(f"✅ Table {table_id} already exists (race condition)")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to create table {table_id}: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking table {table_id}: {e}")
            return False
            
    def create_all_tables(self) -> dict:
        """
        Create all tables
        
        Returns:
            Dictionary of table names and success status
        """
        results = {}
        
        # Ensure dataset exists first
        if not self.ensure_dataset_exists():
            logger.error("❌ Cannot create tables without a dataset")
            return {table_name: False for table_name in self.table_schemas}
            
        # Create each table
        for table_name in self.table_schemas:
            results[table_name] = self.create_table(table_name)
            
        return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='BigQuery Table Creation Script')
    parser.add_argument('--project', type=str, default=DEFAULT_PROJECT_ID,
                        help=f'GCP project ID (default: {DEFAULT_PROJECT_ID})')
    parser.add_argument('--dataset', type=str, default=DEFAULT_DATASET_ID,
                        help=f'BigQuery dataset ID (default: {DEFAULT_DATASET_ID})')
    parser.add_argument('--location', type=str, default=DEFAULT_LOCATION,
                        help=f'BigQuery dataset location (default: {DEFAULT_LOCATION})')
    parser.add_argument('--tables', type=str, nargs='*',
                        help='Specific tables to create (default: all)')
    
    args = parser.parse_args()
    
    try:
        creator = BigQueryTableCreator(
            project_id=args.project,
            dataset_id=args.dataset,
            location=args.location
        )
        
        if args.tables:
            # Create specific tables
            results = {}
            for table_name in args.tables:
                if table_name in creator.table_schemas:
                    results[table_name] = creator.create_table(table_name)
                else:
                    logger.error(f"❌ Unknown table: {table_name}")
                    results[table_name] = False
        else:
            # Create all tables
            results = creator.create_all_tables()
            
        # Print summary
        print("\nTable Creation Summary:")
        print("----------------------")
        success_count = sum(1 for success in results.values() if success)
        for table_name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{table_name}: {status}")
            
        print(f"\nTotal: {success_count}/{len(results)} tables created or verified")
        
        if success_count == len(results):
            return 0
        else:
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
