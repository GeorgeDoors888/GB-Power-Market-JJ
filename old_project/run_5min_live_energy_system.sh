#!/bin/bash
# Run the UK energy live system with 5-minute data updates
# This script specifically enables the high-frequency data sources (system frequency and rolling demand)

# Define colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== UK Energy Live Data System with 5-Minute Updates ===${NC}"

# Directory for logs
LOGS_DIR="logs"
mkdir -p $LOGS_DIR

# Timestamp for log files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Ensure we're using the correct Python environment
source venv/bin/activate

# Kill any existing streamlit processes
pkill -f streamlit || true
echo -e "${CYAN}Cleared any existing dashboard processes${NC}"

# Kill any existing updater processes
if ps aux | grep -v grep | grep -q "live_data_updater.py"; then
    PID=$(ps aux | grep -v grep | grep "live_data_updater.py" | awk '{print $2}')
    echo -e "${CYAN}Stopping existing live data updater (PID: ${PID})${NC}"
    kill $PID
    sleep 2
fi

# Create the high-frequency version of the updater script
cat > high_frequency_data_updater.py << 'EOF'
#!/usr/bin/env python3
"""
High-Frequency Live Data Updater (5-minute data)
====================================
Monitors and updates data published within the last 24 hours
Includes 5-minute frequency data from Elexon BMRS API
"""

import os
import json
import sys
import requests
import time
import logging
from datetime import datetime, timedelta
from google.cloud import storage
from google.cloud import bigquery
from pathlib import Path
import tempfile
import pandas as pd
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("high_frequency_updates.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LiveDataUpdater:
    """
    Monitors and updates data published within the last 24 hours
    with focus on high-frequency (5-minute) data
    """
    
    def __init__(self):
        # Check if we can connect to Google Cloud
        self.use_cloud_storage = True
        self.use_bigquery = True
        
        try:
            # Cloud configuration
            self.storage_client = storage.Client()
            self.bucket_name = "jibber-jabber-knowledge-bmrs-data"
            self.bucket = self.storage_client.bucket(self.bucket_name)
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to Google Cloud Storage: {str(e)}")
            logger.warning("⚠️ Cloud Storage features will be disabled")
            self.use_cloud_storage = False
            
        try:
            self.bigquery_client = bigquery.Client()
            self.dataset_id = "uk_energy_prod"
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to BigQuery: {str(e)}")
            logger.warning("⚠️ BigQuery features will be disabled")
            self.use_bigquery = False
        
        # API configurations
        self.elexon_base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        
        # Load API keys from environment file if not already set
        if not os.getenv('BMRS_API_KEY'):
            try:
                with open('api.env', 'r') as env_file:
                    for line in env_file:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key == 'BMRS_API_KEY_1':
                                os.environ['BMRS_API_KEY'] = value.strip('"\'')
                                break
                logger.info("✅ Loaded BMRS API key from api.env file")
            except Exception as e:
                logger.error(f"❌ Failed to load API key from api.env: {e}")
        
        self.api_key = os.getenv('BMRS_API_KEY')
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Live-Data-Updater/1.0 (Energy-Research)',
            'Accept': 'application/json'
        })
        
        # High-frequency (5-minute) datasets
        self.high_frequency_datasets = {
            'system_frequency': {
                'endpoint': 'system/frequency',
                'table': 'elexon_system_frequency',
                'frequency': 5  # check every 5 minutes
            },
            'rolling_demand': {
                'endpoint': 'demand/rollingSystemDemand',
                'table': 'elexon_rolling_demand',
                'frequency': 5  # check every 5 minutes
            }
        }
        
        # Standard datasets (included for completeness)
        self.standard_datasets = {
            'demand_outturn': {
                'endpoint': 'demand/outturn',
                'table': 'elexon_demand_outturn',
                'frequency': 30  # check every 30 minutes
            },
            'generation_outturn': {
                'endpoint': 'generation/outturn',
                'table': 'elexon_generation_outturn',
                'frequency': 30  # check every 30 minutes
            },
            'system_warnings': {
                'endpoint': 'datasets/SYSWARN',
                'table': 'elexon_system_warnings',
                'frequency': 60  # check every hour
            },
            'demand_forecasts': {
                'endpoint': 'forecast/demand/day-ahead',
                'table': 'neso_demand_forecasts',
                'frequency': 60  # check every hour
            },
            'wind_forecasts': {
                'endpoint': 'datasets/WINDFORFUELHH',
                'table': 'neso_wind_forecasts',
                'frequency': 60  # check every hour
            }
        }
        
        # Statistics
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'updates': 0,
            'failures': 0,
            'last_update': None,
            'datasets': {}
        }
    
    def get_date_range(self):
        """Get date range for recent data (last 24 hours)"""
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        return start_date.strftime('%Y-%m-%dT%H:%M:%SZ'), end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def update_dataset(self, name, info):
        """Update a single dataset"""
        endpoint = info['endpoint']
        table = info['table']
        
        logger.info(f"🔄 Updating {name} from {endpoint}...")
        
        start_date, end_date = self.get_date_range()
        
        # Prepare request parameters
        params = {
            'from': start_date,
            'to': end_date,
            'apiKey': self.api_key,
            'format': 'json'
        }
        
        url = f"{self.elexon_base_url}/{endpoint}"
        
        try:
            # Make the API request
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"❌ API Error for {name}: HTTP {response.status_code}")
                logger.error(f"Response: {response.text[:500]}...")
                self.stats['failures'] += 1
                return False
            
            # Parse the response
            data = response.json()
            
            # Check if we have data
            if 'data' in data and isinstance(data['data'], list):
                items = data['data']
                if not items:
                    logger.info(f"ℹ️ No new data for {name}")
                    return True
                
                # Convert to DataFrame for easier processing
                df = pd.DataFrame(items)
                
                # Save to Cloud Storage
                if self.use_cloud_storage:
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                        json.dump(items, temp_file)
                        temp_file_path = temp_file.name
                    
                    # Upload to Cloud Storage
                    now = datetime.now()
                    blob_name = f"{name}/{now.strftime('%Y%m%d_%H%M%S')}.json"
                    blob = self.bucket.blob(blob_name)
                    blob.upload_from_filename(temp_file_path)
                    
                    # Clean up the temporary file
                    os.remove(temp_file_path)
                    
                    logger.info(f"✅ Uploaded {len(items)} records to Cloud Storage: {blob_name}")
                
                # Save to BigQuery
                if self.use_bigquery and not df.empty:
                    # Process DataFrame to ensure proper field types
                    for col in df.columns:
                        if 'date' in col.lower() or 'time' in col.lower():
                            try:
                                df[col] = pd.to_datetime(df[col])
                            except:
                                pass  # Keep as is if conversion fails
                    
                    # Upload to BigQuery
                    table_id = f"{self.bigquery_client.project}.{self.dataset_id}.{table}"
                    job_config = bigquery.LoadJobConfig(
                        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
                    )
                    
                    job = self.bigquery_client.load_table_from_dataframe(
                        df, table_id, job_config=job_config
                    )
                    job.result()  # Wait for the job to complete
                    
                    logger.info(f"✅ Loaded {len(df)} rows into BigQuery table {table}")
                
                # Update statistics
                self.stats['updates'] += 1
                self.stats['last_update'] = datetime.now().isoformat()
                
                if name not in self.stats['datasets']:
                    self.stats['datasets'][name] = {
                        'last_update': datetime.now().isoformat(),
                        'total_records': len(items)
                    }
                else:
                    self.stats['datasets'][name]['last_update'] = datetime.now().isoformat()
                    self.stats['datasets'][name]['total_records'] += len(items)
                
                return True
            else:
                logger.warning(f"⚠️ No data field or unexpected format for {name}")
                logger.debug(f"Response: {json.dumps(data)[:500]}...")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating {name}: {str(e)}")
            self.stats['failures'] += 1
            return False
    
    def update_high_frequency_datasets(self):
        """Update all high-frequency datasets"""
        logger.info("🔄 Updating high-frequency datasets (5-minute data)...")
        for name, info in self.high_frequency_datasets.items():
            self.update_dataset(name, info)
    
    def update_standard_datasets(self):
        """Update all standard datasets"""
        logger.info("🔄 Updating standard datasets...")
        for name, info in self.standard_datasets.items():
            self.update_dataset(name, info)
    
    def update_all_datasets(self):
        """Update all datasets"""
        self.update_high_frequency_datasets()
        self.update_standard_datasets()
    
    def schedule_updates(self):
        """Schedule regular updates"""
        # Schedule high-frequency datasets (5-minute)
        for name, info in self.high_frequency_datasets.items():
            frequency = info['frequency']
            schedule.every(frequency).minutes.do(
                lambda n=name, i=info: self.update_dataset(n, i)
            )
            logger.info(f"📅 Scheduled high-frequency updates for {name} every {frequency} minutes")
        
        # Schedule standard datasets
        for name, info in self.standard_datasets.items():
            frequency = info['frequency']
            schedule.every(frequency).minutes.do(
                lambda n=name, i=info: self.update_dataset(n, i)
            )
            logger.info(f"📅 Scheduled updates for {name} every {frequency} minutes")
        
        # Schedule full status report every 6 hours
        schedule.every(6).hours.do(self.print_status)
        
        logger.info("📅 All updates scheduled. Running continuous monitoring...")
        
        # Initial full update
        self.update_all_datasets()
        self.print_status()
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def print_status(self):
        """Print status information"""
        logger.info("📊 === SYSTEM STATUS ===")
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        logger.info(f"⏱️ Uptime: {uptime}")
        logger.info(f"🔄 Total updates: {self.stats['updates']}")
        logger.info(f"❌ Failures: {self.stats['failures']}")
        
        logger.info("📊 Dataset Status:")
        for name, data in self.stats['datasets'].items():
            last_update = datetime.fromisoformat(data['last_update'])
            age = datetime.now() - last_update
            logger.info(f"  - {name}: {data['total_records']} records, last update {age.seconds//60} min ago")

def main():
    """Main function"""
    updater = LiveDataUpdater()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'update':
            print("Running manual update of all datasets...")
            updater.update_all_datasets()
            print("Update complete. Check logs for details.")
        elif sys.argv[1] == 'high-frequency':
            print("Running manual update of high-frequency datasets...")
            updater.update_high_frequency_datasets()
            print("Update complete. Check logs for details.")
        elif sys.argv[1] == 'status':
            updater.print_status()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Available commands: update, high-frequency, status")
    else:
        # Start continuous monitoring
        print("Starting continuous data monitoring with 5-minute updates...")
        print("This will run in the background and update data based on configured schedules.")
        print("Use Ctrl+C to stop the service.")
        updater.schedule_updates()

if __name__ == "__main__":
    main()
EOF

# Make the new script executable
chmod +x high_frequency_data_updater.py

# Start the high-frequency data updater in the background
echo -e "${CYAN}Starting high-frequency data updater in background...${NC}"
python high_frequency_data_updater.py > $LOGS_DIR/high_frequency_updater_${TIMESTAMP}.log 2>&1 &

# Save the PID to a file
echo $! > high_frequency_updater.pid
echo -e "${GREEN}High-frequency data updater started with PID: $!${NC}"
echo -e "Log file: $LOGS_DIR/high_frequency_updater_${TIMESTAMP}.log"

# Create BigQuery tables for the high-frequency data if they don't exist yet
echo -e "${CYAN}Ensuring BigQuery tables exist for high-frequency data...${NC}"
python - << 'EOF'
from google.cloud import bigquery

# Create tables for high-frequency data
client = bigquery.Client()
dataset_id = "uk_energy_prod"

# System frequency table schema
system_frequency_schema = [
    bigquery.SchemaField("startTime", "TIMESTAMP"),
    bigquery.SchemaField("settlementDate", "TIMESTAMP"),
    bigquery.SchemaField("settlementPeriod", "INTEGER"),
    bigquery.SchemaField("frequency", "FLOAT"),
    bigquery.SchemaField("recordType", "STRING"),
]

# Rolling demand table schema
rolling_demand_schema = [
    bigquery.SchemaField("startTime", "TIMESTAMP"),
    bigquery.SchemaField("settlementDate", "TIMESTAMP"),
    bigquery.SchemaField("settlementPeriod", "INTEGER"),
    bigquery.SchemaField("demand", "FLOAT"),
    bigquery.SchemaField("recordType", "STRING"),
]

# Create tables if they don't exist
for table_id, schema in [
    ("elexon_system_frequency", system_frequency_schema),
    ("elexon_rolling_demand", rolling_demand_schema),
]:
    try:
        full_table_id = f"{client.project}.{dataset_id}.{table_id}"
        table = bigquery.Table(full_table_id, schema=schema)
        table = client.create_table(table, exists_ok=True)
        print(f"Created or updated table {full_table_id}")
    except Exception as e:
        print(f"Error creating table {table_id}: {str(e)}")
EOF

# Perform backfill for any missing data in the last 24 hours
echo -e "${CYAN}Backfilling any missing high-frequency data from the past 24 hours...${NC}"
python high_frequency_data_updater.py update > $LOGS_DIR/high_frequency_backfill_${TIMESTAMP}.log 2>&1
echo -e "${GREEN}Backfill complete${NC}"
echo -e "Log file: $LOGS_DIR/high_frequency_backfill_${TIMESTAMP}.log"

# Start the dashboard
echo -e "${CYAN}Starting live energy dashboard...${NC}"
streamlit run live_energy_dashboard.py

# Note: The script will continue running the dashboard in the foreground
# The high-frequency data updater will keep running in the background
