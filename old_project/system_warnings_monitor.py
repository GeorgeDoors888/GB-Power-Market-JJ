#!/usr/bin/env python3
"""
SYSTEM WARNINGS MONITOR

A dedicated script to monitor and process system warnings/outages data from ELEXON BMRS API.
This script runs independently from the main data updater to ensure warnings are
captured promptly and reliably.

Usage: python system_warnings_monitor.py
"""

import os
import time
import json
import logging
import tempfile
import requests
import pandas as pd
import schedule
from datetime import datetime, timedelta
from google.cloud import bigquery, storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('system_warnings_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

class SystemWarningsMonitor:
    """Monitor for ELEXON BMRS system warnings and outages"""
    
    def __init__(self):
        """Initialize the monitor"""
        logger.info("🚀 Initializing System Warnings Monitor")
        
        # API Configuration
        self.elexon_base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.endpoint = "datasets/SYSWARN"
        self.table_name = "elexon_system_warnings"
        self.check_frequency = 10  # check every 10 minutes (more frequent than hourly)
        
        # BigQuery & GCS Configuration
        self.use_bigquery = True
        self.use_cloud_storage = True
        self.dataset_id = "uk_energy"
        self.project_id = "jibber-jabber-knowledge"
        self.bucket_name = "energy-data-collection"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2  # seconds
        
        # Load API keys from environment file
        self._load_api_key()
        
        # Initialize clients
        if self.use_bigquery:
            self.bigquery_client = bigquery.Client(project=self.project_id)
            logger.info("✅ Connected to BigQuery")
        
        if self.use_cloud_storage:
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            logger.info("✅ Connected to Cloud Storage")
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'System-Warnings-Monitor/1.0 (Energy-Research)',
            'Accept': 'application/json'
        })
        
        # Statistics
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'total_checks': 0,
            'warnings_found': 0,
            'new_warnings': 0,
            'last_check': None,
            'last_warning': None,
            'errors': 0
        }
        
        logger.info("✅ System Warnings Monitor initialized")
    
    def _load_api_key(self):
        """Load the BMRS API key from environment file"""
        if not os.getenv('BMRS_API_KEY'):
            try:
                with open('api.env', 'r') as env_file:
                    for line in env_file:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key == 'BMRS_API_KEY_1':
                                os.environ['BMRS_API_KEY'] = value.strip('"\'')
                                logger.info("✅ Loaded BMRS API key from api.env file")
                                break
            except Exception as e:
                logger.error(f"❌ Failed to load API key from api.env: {e}")
                
        self.api_key = os.getenv('BMRS_API_KEY')
        if not self.api_key:
            logger.error("❌ No BMRS API key found!")
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def get_date_range(self):
        """Get date range for recent warnings (last 48 hours)"""
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=48)  # Look back further for warnings
        return start_date, end_date
    
    def check_for_warnings(self):
        """Check for system warnings and process them"""
        logger.info("🔍 Checking for system warnings...")
        self.stats['total_checks'] += 1
        self.stats['last_check'] = datetime.now().isoformat()
        
        start_date, end_date = self.get_date_range()
        
        # Format dates for API
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Construct URL and parameters
        url = f"{self.elexon_base_url}/{self.endpoint}"
        params = {
            'from': from_date,
            'to': to_date,
            'format': 'json'
        }
        
        if self.api_key:
            params['apiKey'] = self.api_key
        
        # Respect rate limits
        self._respect_rate_limit()
        
        try:
            # Make API request
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check if we have data
            if 'data' not in data or not data['data']:
                logger.info("✅ No system warnings found")
                return
            
            # Process warnings
            warnings = data['data']
            warning_count = len(warnings)
            self.stats['warnings_found'] += warning_count
            
            logger.info(f"⚠️ Found {warning_count} system warnings")
            
            # Convert to DataFrame
            df = pd.DataFrame(warnings)
            
            if df.empty:
                logger.info("✅ No system warnings to process")
                return
            
            # Save to Cloud Storage
            if self.use_cloud_storage:
                try:
                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                    with open(temp_file.name, 'w') as f:
                        json.dump(warnings, f)
                    
                    # Upload to GCS
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    cloud_path = f"elexon/system_warnings/warnings_{timestamp}.json"
                    blob = self.bucket.blob(cloud_path)
                    blob.upload_from_filename(temp_file.name)
                    
                    # Delete temporary file
                    os.unlink(temp_file.name)
                    logger.info(f"✅ Uploaded warnings to Cloud Storage: {cloud_path}")
                except Exception as e:
                    logger.error(f"❌ Error uploading to Cloud Storage: {str(e)}")
            
            # Update BigQuery
            if self.use_bigquery:
                try:
                    # Get existing warnings for deduplication
                    table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_name}"
                    query = f"""
                    SELECT id FROM `{table_ref}`
                    WHERE timestamp >= '{start_date.isoformat()}'
                    """
                    
                    existing_data = self.bigquery_client.query(query).result().to_dataframe()
                    
                    # Deduplicate based on warning ID
                    existing_ids = set(existing_data['id'].tolist()) if not existing_data.empty else set()
                    df = df[~df['id'].isin(existing_ids)]
                    
                    # Check if we have new warnings after deduplication
                    if df.empty:
                        logger.info("✅ No new system warnings after deduplication")
                        return
                    
                    # Process new warnings
                    new_warning_count = len(df)
                    self.stats['new_warnings'] += new_warning_count
                    self.stats['last_warning'] = datetime.now().isoformat()
                    
                    # Add timestamp
                    df['ingestion_timestamp'] = datetime.now().isoformat()
                    
                    # Fix schema matching
                    try:
                        table = self.bigquery_client.get_table(table_ref)
                        expected_fields = [field.name for field in table.schema]
                        
                        # Add any missing fields with default values
                        for field in expected_fields:
                            if field not in df.columns:
                                if field == 'timestamp':
                                    df['timestamp'] = datetime.now().isoformat()
                                else:
                                    df[field] = None
                        
                        # Remove any extra fields not in schema
                        df_columns = list(df.columns)
                        for col in df_columns:
                            if col not in expected_fields:
                                df = df.drop(columns=[col])
                    except Exception as e:
                        logger.warning(f"⚠️ Could not verify schema or table doesn't exist yet: {str(e)}")
                        # Create the table if it doesn't exist
                        schema = [
                            bigquery.SchemaField("id", "STRING"),
                            bigquery.SchemaField("warningType", "STRING"),
                            bigquery.SchemaField("text", "STRING"),
                            bigquery.SchemaField("timestamp", "TIMESTAMP"),
                            bigquery.SchemaField("expiryTime", "TIMESTAMP"),
                            bigquery.SchemaField("ingestion_timestamp", "TIMESTAMP")
                        ]
                        
                        try:
                            table = bigquery.Table(table_ref, schema=schema)
                            self.bigquery_client.create_table(table, exists_ok=True)
                            logger.info(f"✅ Created or confirmed table {table_ref}")
                        except Exception as create_error:
                            logger.error(f"❌ Failed to create table: {str(create_error)}")
                            self.stats['errors'] += 1
                            return
                    
                    # Load to BigQuery
                    job_config = bigquery.LoadJobConfig(
                        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
                    )
                    
                    load_job = self.bigquery_client.load_table_from_dataframe(
                        df, table_ref, job_config=job_config
                    )
                    load_job.result()  # Wait for job to complete
                    
                    # Log new warnings
                    logger.info(f"⚠️ Added {new_warning_count} new system warnings to BigQuery")
                    for _, warning in df.iterrows():
                        try:
                            warning_text = warning.get('text', 'No description')
                            warning_type = warning.get('warningType', 'Unknown')
                            logger.warning(f"⚠️ NEW WARNING: Type={warning_type}, Text={warning_text}")
                        except:
                            pass
                    
                except Exception as e:
                    logger.error(f"❌ Error updating BigQuery: {str(e)}")
                    self.stats['errors'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error checking for system warnings: {str(e)}")
            self.stats['errors'] += 1
    
    def print_status(self):
        """Print status information"""
        logger.info("📊 === SYSTEM WARNINGS MONITOR STATUS ===")
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        logger.info(f"⏱️ Uptime: {uptime}")
        logger.info(f"🔍 Total checks: {self.stats['total_checks']}")
        logger.info(f"⚠️ Total warnings found: {self.stats['warnings_found']}")
        logger.info(f"🆕 New warnings added: {self.stats['new_warnings']}")
        logger.info(f"❌ Errors encountered: {self.stats['errors']}")
        
        if self.stats['last_warning']:
            last_warning_time = datetime.fromisoformat(self.stats['last_warning'])
            time_since_last = datetime.now() - last_warning_time
            logger.info(f"⏱️ Time since last warning: {time_since_last}")
    
    def run(self):
        """Run the monitor continuously"""
        logger.info("🚀 Starting System Warnings Monitor")
        
        # Initial check
        self.check_for_warnings()
        
        # Schedule regular checks
        schedule.every(self.check_frequency).minutes.do(self.check_for_warnings)
        
        # Schedule status reports
        schedule.every(1).hours.do(self.print_status)
        
        logger.info(f"✅ Scheduled checks every {self.check_frequency} minutes")
        
        # Print initial status
        self.print_status()
        
        # Run continuously
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 System Warnings Monitor stopped by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            raise

if __name__ == "__main__":
    # First, terminate any hung processes
    logger.info("🔍 Checking for existing processes...")
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'live_data_updater.py' in line and 'python' in line:
                try:
                    pid = int(line.split()[1])
                    logger.warning(f"🛑 Terminating existing process with PID {pid}")
                    subprocess.run(['kill', str(pid)])
                except Exception as e:
                    logger.error(f"❌ Error terminating process: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Error checking for existing processes: {str(e)}")
    
    # Start the monitor
    monitor = SystemWarningsMonitor()
    monitor.run()
