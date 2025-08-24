#!/usr/bin/env python3
"""
Data Backfill Script
====================
Backfills missing days in BigQuery tables by fetching data from Elexon API
and updating both BigQuery tables and GCS storage.
"""

import os
import sys
import logging
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from google.cloud import storage
from google.cloud import bigquery
import requests
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"backfill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataBackfiller:
    """
    Identifies and backfills missing data in BigQuery tables
    """
    
    def __init__(self):
        # Cloud configuration
        self.storage_client = storage.Client()
        self.bucket_name = "jibber-jabber-knowledge-bmrs-data"
        self.bucket = self.storage_client.bucket(self.bucket_name)
        
        self.bigquery_client = bigquery.Client()
        self.dataset_id = "uk_energy_prod"
        
        # API configurations
        self.elexon_base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.api_key = os.getenv('BMRS_API_KEY')
        
        # Rate limiting
        self.rate_limit = 1.0  # 1 request per second
        self.last_request = 0
        
        # Available datasets with their endpoints
        self.datasets = {
            'elexon_demand_outturn': {
                'endpoint': 'demand/outturn',
                'date_field': 'settlementDate'
            },
            'elexon_generation_outturn': {
                'endpoint': 'generation/outturn',
                'date_field': 'settlementDate'
            },
            'elexon_system_warnings': {
                'endpoint': 'datasets/SYSWARN',
                'date_field': 'settlementDate'
            },
            'neso_demand_forecasts': {
                'endpoint': 'forecast/demand/day-ahead',
                'date_field': 'settlementDate'
            },
            'neso_wind_forecasts': {
                'endpoint': 'datasets/WINDFORFUELHH',
                'date_field': 'settlementDate'
            },
            'neso_carbon_intensity': {
                'endpoint': 'datasets/FUELINST',
                'date_field': 'settlementDate'
            },
            'neso_interconnector_flows': {
                'endpoint': 'datasets/INTERFUELHH',
                'date_field': 'settlementDate'
            },
            'neso_balancing_services': {
                'endpoint': 'datasets/DISBSAD',
                'date_field': 'settlementDate'
            }
        }
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Data-Backfiller/1.0 (Energy-Research)',
            'Accept': 'application/json'
        })
        
        logger.info("✅ Data Backfiller initialized")
    
    def _sleep_for_rate_limit(self):
        """Sleep to respect API rate limits"""
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()
    
    def find_missing_dates(self, table_name, start_date=None, end_date=None):
        """Find missing dates in a BigQuery table"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
            
        date_field = self.datasets[table_name]['date_field']
        
        # Format dates for SQL
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Generate all dates in the range
        all_dates = set()
        current = start_date
        while current <= end_date:
            all_dates.add(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        # Query BigQuery for existing dates
        query = f"""
        SELECT DISTINCT DATE({date_field}) as date_only
        FROM `{self.dataset_id}.{table_name}`
        WHERE {date_field} BETWEEN '{start_str}' AND '{end_str}'
        """
        
        query_job = self.bigquery_client.query(query)
        results = query_job.result()
        
        # Extract existing dates
        existing_dates = set()
        for row in results:
            existing_dates.add(row.date_only.strftime('%Y-%m-%d'))
        
        # Find missing dates
        missing_dates = all_dates - existing_dates
        
        return sorted(list(missing_dates))
    
    def fetch_data_for_date(self, table_name, date_str):
        """Fetch data from Elexon API for a specific date"""
        endpoint = self.datasets[table_name]['endpoint']
        
        url = f"{self.elexon_base_url}/{endpoint}"
        params = {
            'settlementDateFrom': date_str,
            'settlementDateTo': date_str
        }
        
        if self.api_key:
            params['apiKey'] = self.api_key
            
        self._sleep_for_rate_limit()
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract the data array - handle different response formats
            if 'data' in data:
                items = data['data']
            elif 'items' in data:
                items = data['items']
            else:
                items = data
                
            if not items:
                logger.warning(f"⚠️ No data returned for {table_name} on {date_str}")
                return None
                
            return items
        except Exception as e:
            logger.error(f"❌ Error fetching data for {table_name} on {date_str}: {str(e)}")
            return None
    
    def save_to_gcs(self, table_name, date_str, data):
        """Save data to Google Cloud Storage"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        year = date_obj.strftime('%Y')
        month = date_obj.strftime('%m')
        
        # Create a GCS path
        blob_path = f"bmrs_data/{table_name}/{year}/{month}/{date_str}.json"
        blob = self.bucket.blob(blob_path)
        
        try:
            blob.upload_from_string(
                json.dumps(data),
                content_type='application/json'
            )
            logger.info(f"✅ Saved {len(data)} records to GCS: {blob_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving to GCS: {str(e)}")
            return False
    
    def save_to_bigquery(self, table_name, data):
        """Save data to BigQuery"""
        if not data:
            return False
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to BigQuery
        table_ref = f"{self.dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition='WRITE_APPEND',
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
            ]
        )
        
        try:
            load_job = self.bigquery_client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )
            load_job.result()  # Wait for the job to complete
            
            logger.info(f"✅ Loaded {len(df)} rows to BigQuery table {table_ref}")
            return True
        except Exception as e:
            logger.error(f"❌ Error loading to BigQuery: {str(e)}")
            return False
    
    def backfill_table(self, table_name, start_date=None, end_date=None):
        """Backfill missing data for a table"""
        logger.info(f"🔄 Starting backfill for {table_name}")
        
        # Find missing dates
        missing_dates = self.find_missing_dates(table_name, start_date, end_date)
        
        if not missing_dates:
            logger.info(f"✅ No missing dates found for {table_name}")
            return True
            
        logger.info(f"🔍 Found {len(missing_dates)} missing dates for {table_name}")
        
        success_count = 0
        for date_str in missing_dates:
            logger.info(f"🔄 Processing {table_name} for {date_str}")
            
            # Fetch data
            data = self.fetch_data_for_date(table_name, date_str)
            
            if not data:
                continue
                
            # Save to GCS
            gcs_success = self.save_to_gcs(table_name, date_str, data)
            
            # Save to BigQuery
            bq_success = self.save_to_bigquery(table_name, data)
            
            if gcs_success and bq_success:
                success_count += 1
                
        logger.info(f"✅ Backfilled {success_count}/{len(missing_dates)} dates for {table_name}")
        return success_count == len(missing_dates)
    
    def backfill_all_tables(self, start_date=None, end_date=None, tables=None):
        """Backfill all tables or specific tables"""
        if tables is None:
            tables = list(self.datasets.keys())
            
        results = {}
        for table_name in tables:
            if table_name not in self.datasets:
                logger.warning(f"⚠️ Unknown table {table_name}, skipping")
                continue
                
            success = self.backfill_table(table_name, start_date, end_date)
            results[table_name] = success
            
        return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill missing data in BigQuery tables')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--tables', nargs='+', help='Specific tables to backfill')
    
    args = parser.parse_args()
    
    start_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        
    end_date = None
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    backfiller = DataBackfiller()
    backfiller.backfill_all_tables(start_date, end_date, args.tables)
