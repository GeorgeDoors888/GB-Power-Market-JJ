#!/usr/bin/env python3
"""
IRIS to BigQuery Uploader - Unified Version
Processes downloaded IRIS JSON files and uploads to BigQuery
Handles all BMRS data streams with table-specific logic
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from google.cloud import bigquery
from google.api_core import exceptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/iris-pipeline/logs/iris_uploader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('BQ_PROJECT', 'inner-cinema-476211-u9')
DATASET = 'uk_energy_prod'
DATA_DIR = Path('/opt/iris-pipeline/data')

# Table mapping: reportType -> BigQuery table suffix
TABLE_MAPPING = {
    'FUELINST': 'bmrs_fuelinst_iris',
    'WINDFOR': 'bmrs_windfor_iris',
    'FREQ': 'bmrs_freq_iris',
    'MID': 'bmrs_mid_iris',
    'BOALF': 'bmrs_boalf_iris',
    'BOD': 'bmrs_bod_iris',
    'COSTS': 'bmrs_costs_iris',
    'INDGEN': 'bmrs_indgen_iris',
    'INDO': 'bmrs_indo_iris',
    'B1620': 'bmrs_fuelinst_iris',  # Alternative naming
    'B1440': 'bmrs_windfor_iris',
    'B1610': 'bmrs_freq_iris',
    'B1770': 'bmrs_mid_iris',
    'B1430': 'bmrs_boalf_iris',
    'B1420': 'bmrs_bod_iris',
    'B1780': 'bmrs_costs_iris',
}


class IrisUploader:
    """Uploads IRIS data to BigQuery"""
    
    def __init__(self, project_id=PROJECT_ID, dataset=DATASET):
        """Initialize BigQuery client"""
        self.project_id = project_id
        self.dataset = dataset
        self.client = bigquery.Client(project=project_id)
        logger.info(f"Connected to BigQuery: {project_id}.{dataset}")
    
    def process_file(self, filepath):
        """
        Process a single JSON file and upload to BigQuery
        
        Args:
            filepath: Path to JSON file (str or Path object)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert string to Path if needed
            if isinstance(filepath, str):
                filepath = Path(filepath)
            
            # Read JSON file
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Handle both array and dict formats
            if isinstance(data, list):
                # Array format (e.g., WINDFOR) - extract dataset name from first record
                if not data:
                    logger.warning(f"Empty array in {filepath.name}")
                    return False
                report_type = data[0].get('dataset', 'UNKNOWN')
            else:
                # Dict format (e.g., FUELINST) - extract reportType
                report_type = data.get('reportType', 'UNKNOWN')
            
            # Get table name
            table_name = TABLE_MAPPING.get(report_type)
            if not table_name:
                logger.warning(f"Unknown report type: {report_type} in {filepath.name}")
                return False
            
            # Extract records
            records = self._extract_records(data, report_type)
            if not records:
                logger.warning(f"No records extracted from {filepath.name}")
                return False
            
            # Upload to BigQuery
            self._upload_records(table_name, records)
            
            # Delete processed file
            filepath.unlink()
            logger.info(f"Processed and deleted: {filepath.name}")
            
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing {filepath.name}: {e}")
            return False
    
    def _extract_records(self, data, report_type):
        """
        Extract records from IRIS message based on report type
        
        Args:
            data: Parsed JSON data (dict or list)
            report_type: BMRS report type
        
        Returns:
            list: List of record dictionaries
        """
        records = []
        
        # Handle array format (e.g., WINDFOR)
        if isinstance(data, list):
            records = data
        # Handle dict format with nested data
        elif 'data' in data:
            records = data['data']
        elif 'items' in data:
            records = data['items']
        else:
            # Single record format
            records = [data]
        
        # Add metadata to each record
        for record in records:
            record['ingested_utc'] = datetime.utcnow().isoformat()
            record['source'] = 'IRIS'
        
        return records
    
    def _upload_records(self, table_name, records):
        """
        Upload records to BigQuery table
        
        Args:
            table_name: Target table name
            records: List of records to upload
        """
        table_id = f"{self.project_id}.{self.dataset}.{table_name}"
        
        try:
            # Insert rows
            errors = self.client.insert_rows_json(table_id, records)
            
            if errors:
                logger.error(f"Errors inserting into {table_name}: {errors}")
            else:
                logger.info(f"Inserted {len(records)} rows into {table_name}")
                
        except exceptions.NotFound:
            logger.error(f"Table not found: {table_id}")
        except Exception as e:
            logger.error(f"Upload failed for {table_name}: {e}")
    
    def process_all_files(self):
        """Process all JSON files in data directory"""
        json_files = list(DATA_DIR.glob('*.json'))
        
        if not json_files:
            logger.info("No files to process")
            return 0
        
        logger.info(f"Found {len(json_files)} files to process")
        
        success_count = 0
        for filepath in json_files:
            if self.process_file(filepath):
                success_count += 1
        
        logger.info(f"Successfully processed {success_count}/{len(json_files)} files")
        return success_count
    
    def get_table_stats(self):
        """Get row counts for all IRIS tables"""
        stats = {}
        
        for table_name in set(TABLE_MAPPING.values()):
            try:
                query = f"""
                    SELECT 
                        COUNT(*) as row_count,
                        MAX(_ingestion_time) as latest_ingestion
                    FROM `{self.project_id}.{self.dataset}.{table_name}`
                """
                result = self.client.query(query).to_dataframe()
                stats[table_name] = {
                    'rows': int(result['row_count'].iloc[0]),
                    'latest': str(result['latest_ingestion'].iloc[0])
                }
            except exceptions.NotFound:
                stats[table_name] = {'status': 'table_not_found'}
            except Exception as e:
                stats[table_name] = {'error': str(e)}
        
        return stats


def main():
    """Main entry point"""
    import sys
    
    uploader = IrisUploader()
    
    try:
        # Process all files
        processed = uploader.process_all_files()
        
        # Show stats if requested
        if '--stats' in sys.argv:
            stats = uploader.get_table_stats()
            logger.info("Table statistics:")
            for table, data in stats.items():
                logger.info(f"  {table}: {data}")
        
        sys.exit(0 if processed > 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
