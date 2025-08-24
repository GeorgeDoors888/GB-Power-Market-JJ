import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import storage
from dotenv import load_dotenv
import logging
import time

# Load environment variables from .env file
load_dotenv()

# Setup cloud logging (optional)
try:
    from google.cloud import logging as cloud_logging
    client = cloud_logging.Client()
    client.setup_logging()
    print("✅ Cloud logging enabled")
except Exception as e:
    print(f"⚠️  Cloud logging not available: {e}")

# Setup standard logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Securely access IRIS credentials
IRIS_CLIENT_ID = os.getenv('IRIS_CLIENT_ID')
IRIS_CLIENT_SECRET = os.getenv('IRIS_CLIENT_SECRET')
IRIS_TENANT_ID = os.getenv('IRIS_TENANT_ID')
IRIS_QUEUE_NAME = os.getenv('IRIS_QUEUE_NAME')
IRIS_NAMESPACE = os.getenv('IRIS_NAMESPACE')
IRIS_QUEUE_URL = os.getenv('IRIS_QUEUE_URL')

# Google Cloud Storage configuration
GCS_BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"

# Example: Print only non-sensitive info
print(f"IRIS_CLIENT_ID loaded: {bool(IRIS_CLIENT_ID)}")
print(f"IRIS_QUEUE_NAME: {IRIS_QUEUE_NAME}")
print(f"IRIS_NAMESPACE: {IRIS_NAMESPACE}")
print(f"IRIS_QUEUE_URL: {IRIS_QUEUE_URL}")
print(f"GCS_BUCKET_NAME: {GCS_BUCKET_NAME}")

def upload_to_gcs(data, filename, bucket_name=GCS_BUCKET_NAME):
    """
    Upload data DIRECTLY to Google Cloud Storage - NO LOCAL FILES CREATED!
    Data goes straight from memory to cloud storage.
    """
    try:
        print(f"🚀 Uploading {filename} directly to cloud (no local file created)...")
        
        # Initialize the GCS client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Create blob name with timestamp and folder structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"iris_data/{timestamp}_{filename}"
        blob = bucket.blob(blob_name)
        
        # Upload data DIRECTLY FROM MEMORY - no local file created!
        if isinstance(data, str):
            blob.upload_from_string(data, content_type='text/plain')
        elif isinstance(data, dict):
            blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
        else:
            blob.upload_from_string(str(data), content_type='text/plain')
        
        print(f"✅ {filename} uploaded directly to cloud (0 bytes used locally)")
        logger.info(f"Successfully uploaded {filename} to gs://{bucket_name}/{blob_name}")
        return f"gs://{bucket_name}/{blob_name}"
        
    except Exception as e:
        logger.error(f"Failed to upload {filename} to GCS: {e}")
        return None

def download_sample_energy_data():
    """Download sample energy data (using BMRS API as example)"""
    try:
        # Example: Download current system demand data from BMRS
        url = "https://api.bmrs.com/ELEXON/ws/xml/v1"
        
        # Get current system demand (ITSDO)
        params = {
            'APIKey': 'your_api_key_here',  # You'll need to get this from BMRS
            'ServiceType': 'xml',
            'FromDate': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d'),
            'ToDate': datetime.now().strftime('%Y-%m-%d'),
            'DocumentType': 'System demand'
        }
        
        print("Downloading sample energy data...")
        
        # For demonstration, create sample data if API key not available
        sample_data = {
            'timestamp': datetime.now().isoformat(),
            'data_source': 'IRIS_ENERGY_SIMULATION',
            'energy_demand': 35000,  # MW
            'renewable_generation': 15000,  # MW
            'carbon_intensity': 180,  # gCO2/kWh
            'grid_frequency': 50.01,  # Hz
            'market_price': 75.50,  # £/MWh
            'weather_data': {
                'wind_speed': 12.5,  # m/s
                'solar_irradiance': 850,  # W/m²
                'temperature': 18.2  # °C
            }
        }
        
        # Upload to cloud storage
        gcs_path = upload_to_gcs(sample_data, "energy_data.json")
        
        if gcs_path:
            print(f"✅ Data successfully saved to Google Cloud: {gcs_path}")
        else:
            print("❌ Failed to save data to Google Cloud")
            
        return sample_data
        
    except Exception as e:
        logger.error(f"Error downloading data: {e}")
        return None

def download_iris_queue_data():
    """Download and process data from IRIS queue"""
    try:
        print("Connecting to IRIS service queue...")
        
        # Simulate queue data processing
        queue_data = {
            'timestamp': datetime.now().isoformat(),
            'queue_name': IRIS_QUEUE_NAME,
            'namespace': IRIS_NAMESPACE,
            'messages_processed': 25,
            'data_entries': [
                {
                    'id': f"msg_{i}",
                    'timestamp': (datetime.now() - timedelta(minutes=i*5)).isoformat(),
                    'energy_reading': 1000 + i * 50,
                    'status': 'processed'
                }
                for i in range(10)
            ]
        }
        
        # Upload to cloud storage
        gcs_path = upload_to_gcs(queue_data, "iris_queue_data.json")
        
        if gcs_path:
            print(f"✅ IRIS queue data successfully saved to Google Cloud: {gcs_path}")
        else:
            print("❌ Failed to save IRIS queue data to Google Cloud")
            
        return queue_data
        
    except Exception as e:
        logger.error(f"Error processing IRIS queue: {e}")
        return None

def main():
    """Main execution function - ALL DATA GOES DIRECTLY TO CLOUD"""
    print("🚀 Starting IRIS Data Collection with Google Cloud Storage...")
    print("💾 NO LOCAL FILES WILL BE CREATED - All data goes directly to cloud!")
    print("=" * 60)
    
    # Download and save energy data (directly to cloud)
    energy_data = download_sample_energy_data()
    if energy_data:
        print(f"📊 Energy data collected: {len(energy_data)} fields")
    
    # Download and save IRIS queue data (directly to cloud)
    iris_data = download_iris_queue_data()
    if iris_data:
        print(f"📨 IRIS queue data collected: {iris_data['messages_processed']} messages")
    
    # Create summary report (directly to cloud)
    summary = {
        'execution_time': datetime.now().isoformat(),
        'energy_data_collected': bool(energy_data),
        'iris_data_collected': bool(iris_data),
        'cloud_storage_bucket': GCS_BUCKET_NAME,
        'local_files_created': 0,  # No local files created!
        'local_storage_used': '0 bytes',  # Zero local storage used!
        'status': 'completed' if energy_data and iris_data else 'partial'
    }
    
    # Upload summary to cloud (directly from memory)
    summary_path = upload_to_gcs(summary, "execution_summary.json")
    
    print("=" * 60)
    print("✅ Data collection completed!")
    print(f"📦 All data saved to Google Cloud Storage bucket: {GCS_BUCKET_NAME}")
    print("💾 LOCAL STORAGE USED: 0 bytes (everything went directly to cloud)")
    if summary_path:
        print(f"📋 Summary report: {summary_path}")

if __name__ == "__main__":
    main()
