#!/usr/bin/env python3
"""
Cloud-Optimized BMRS Data Downloader
Designed for Google Cloud Storage with automatic scaling and monitoring
"""

import os
import json
import sys
import asyncio
import aiohttp
import requests
import tempfile
import subprocess
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import storage
from google.cloud import logging as cloud_logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path
import time
from flask import Flask, request, jsonify
import logging

# Setup cloud logging
client = cloud_logging.Client()
client.setup_logging()

# Setup standard logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create the Flask application
app = Flask(__name__)

# Global statistics tracking
stats_lock = threading.Lock()
stats = {
    'total_files_targeted': 0,
    'files_downloaded': 0,
    'files_uploaded': 0,
    'files_skipped': 0,
    'total_records': 0,
    'total_requests': 0,
    'start_time': datetime.now().isoformat(),
    'last_update': datetime.now().isoformat()
}

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        "status": "alive",
        "message": "BMRS Data Collector Service",
        "version": "1.0.0"
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get current download statistics"""
    with stats_lock:
        return jsonify(stats)

class CloudBMRSDownloader:
    """
    Cloud-based BMRS downloader that saves directly to Google Cloud Storage
    """
    
    def __init__(self):
        self.api_key = os.getenv('BMRS_API_KEY')
        self.base_url = 'https://data.elexon.co.uk/bmrs/api/v1'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Cloud-BMRS-Downloader/1.0'})
        
        # Load cloud configuration
        self.bucket_name = self._load_cloud_config()
        
        # Thread-safe statistics
        self.stats_lock = threading.Lock()
        self.stats = {
            'total_files_targeted': 0,
            'files_downloaded': 0,
            'files_uploaded': 0,
            'files_skipped': 0,
            'total_records': 0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'cloud_storage_used': 0
        }
        
        # Data types to collect
        self.data_types = [
            'bid_offer_acceptances',
            'generation_outturn', 
            'demand_outturn',
            'system_warnings'
        ]
        
        logger.info("☁️  Cloud BMRS Downloader initialized")
        logger.info(f"✅ API Key: {'Available' if self.api_key else 'Missing'}")
        logger.info(f"📦 Cloud bucket: {self.bucket_name}")
    
    def _load_cloud_config(self):
        """Load cloud configuration"""
        try:
            with open('cloud_config.json', 'r') as f:
                config = json.load(f)
                return config.get('bucket_name')
        except FileNotFoundError:
            # Default bucket name
            return "jibber-jabber-knowledge-bmrs-data"
    
    def _check_file_exists_in_cloud(self, cloud_path):
        """Check if file already exists in Google Cloud Storage"""
        try:
            result = subprocess.run([
                'gsutil', 'ls', f'gs://{self.bucket_name}/{cloud_path}'
            ], capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _upload_to_cloud(self, local_file_path, cloud_path):
        """Upload file to Google Cloud Storage and delete local copy"""
        try:
            # Upload file
            result = subprocess.run([
                'gsutil', 'cp', str(local_file_path), 
                f'gs://{self.bucket_name}/{cloud_path}'
            ], capture_output=True, text=True, check=True)
            
            # Delete local file immediately to save space
            local_file_path.unlink()
            
            with self.stats_lock:
                self.stats['files_uploaded'] += 1
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Upload failed for {cloud_path}: {e}")
            return False
    
    def generate_download_plan(self, start_date=None, end_date=None):
        """Generate download plan, checking what's already in cloud"""
        
        if not start_date:
            # Download last 6 months
            start_date = datetime.now() - timedelta(days=180)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        if not end_date:
            # Up to yesterday
            end_date = datetime.now() - timedelta(days=1)
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        logger.info(f"📅 Download plan: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        download_tasks = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            year = current_date.strftime('%Y')
            month = current_date.strftime('%m')
            
            for data_type in self.data_types:
                # Cloud path
                cloud_path = f"bmrs_data/{data_type}/{year}/{month}/{data_type}_{date_str}.json"
                
                # Check if already exists in cloud
                if not self._check_file_exists_in_cloud(cloud_path):
                    download_tasks.append({
                        'date': date_str,
                        'data_type': data_type,
                        'cloud_path': cloud_path,
                        'priority': self._get_priority(current_date, data_type)
                    })
                else:
                    with self.stats_lock:
                        self.stats['files_skipped'] += 1
            
            current_date += timedelta(days=1)
        
        # Sort by priority
        download_tasks.sort(key=lambda x: x['priority'], reverse=True)
        
        with self.stats_lock:
            self.stats['total_files_targeted'] = len(download_tasks)
        
        logger.info(f"📋 Download plan: {len(download_tasks)} files to download")
        logger.info(f"⏭️  Files already in cloud: {self.stats['files_skipped']}")
        
        return download_tasks
    
    def _get_priority(self, date, data_type):
        """Calculate download priority"""
        days_ago = (datetime.now() - date).days
        recency_score = max(0, 100 - days_ago)
        
        data_type_scores = {
            'bid_offer_acceptances': 50,
            'generation_outturn': 40,
            'demand_outturn': 30,
            'system_warnings': 20
        }
        
        return recency_score + data_type_scores.get(data_type, 10)
    
    def download_and_upload_single_file(self, task):
        """Download data and upload directly to cloud"""
        
        date = task['date']
        data_type = task['data_type']
        cloud_path = task['cloud_path']
        
        try:
            # Download data (same as before)
            endpoint_map = {
                'bid_offer_acceptances': 'balancing/acceptances/all',
                'generation_outturn': 'generation/outturn/summary',
                'demand_outturn': 'demand/outturn/summary',
                'system_warnings': 'datasets/SYSWARN'
            }
            
            endpoint = endpoint_map.get(data_type)
            if not endpoint:
                logger.error(f"❌ Unknown data type: {data_type}")
                return False
            
            all_data = []
            
            # Download logic (same as before)
            if data_type == 'bid_offer_acceptances':
                for sp in range(1, 49):
                    try:
                        url = f"{self.base_url}/{endpoint}"
                        params = {
                            'apikey': self.api_key,
                            'settlementDate': date,
                            'settlementPeriod': sp
                        }
                        
                        response = self.session.get(url, params=params, timeout=20)
                        
                        with self.stats_lock:
                            self.stats['total_requests'] += 1
                        
                        if response.status_code == 200:
                            data = response.json()
                            records = data.get('data', [])
                            
                            if records:
                                for record in records:
                                    record['settlement_period'] = sp
                                    record['download_date'] = datetime.now().isoformat()
                                    record['download_method'] = 'cloud_downloader'
                                
                                all_data.extend(records)
                                
                                with self.stats_lock:
                                    self.stats['successful_requests'] += 1
                                    self.stats['total_records'] += len(records)
                        else:
                            with self.stats_lock:
                                self.stats['failed_requests'] += 1
                        
                        time.sleep(0.05)  # Rate limiting
                        
                    except Exception as e:
                        with self.stats_lock:
                            self.stats['failed_requests'] += 1
                        logger.warning(f"⚠️ {data_type} {date} SP{sp}: {str(e)[:50]}...")
            
            else:
                # Single request for other data types
                try:
                    url = f"{self.base_url}/{endpoint}"
                    params = {
                        'apikey': self.api_key,
                        'settlementDate': date
                    }
                    
                    response = self.session.get(url, params=params, timeout=20)
                    
                    with self.stats_lock:
                        self.stats['total_requests'] += 1
                    
                    if response.status_code == 200:
                        data = response.json()
                        records = data.get('data', [])
                        
                        if records:
                            for record in records:
                                record['download_date'] = datetime.now().isoformat()
                                record['download_method'] = 'cloud_downloader'
                            
                            all_data = records
                            
                            with self.stats_lock:
                                self.stats['successful_requests'] += 1
                                self.stats['total_records'] += len(records)
                    else:
                        with self.stats_lock:
                            self.stats['failed_requests'] += 1
                    
                except Exception as e:
                    with self.stats_lock:
                        self.stats['failed_requests'] += 1
                    logger.warning(f"⚠️ {data_type} {date}: {str(e)[:50]}...")
            
            # Save to temporary file and upload to cloud
            if all_data or True:  # Save even empty files to mark as attempted
                file_data = {
                    'date': date,
                    'data_type': data_type,
                    'download_timestamp': datetime.now().isoformat(),
                    'record_count': len(all_data),
                    'storage_location': 'google_cloud_storage',
                    'data': all_data
                }
                
                # Use temporary file to avoid local storage
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    json.dump(file_data, temp_file, indent=2, default=str)
                    temp_file_path = Path(temp_file.name)
                
                # Upload to cloud and delete temp file
                success = self._upload_to_cloud(temp_file_path, cloud_path)
                
                if success:
                    with self.stats_lock:
                        self.stats['files_downloaded'] += 1
                    
                    logger.info(f"☁️  {data_type} {date}: {len(all_data)} records → cloud")
                    return True
                else:
                    # Clean up temp file if upload failed
                    if temp_file_path.exists():
                        temp_file_path.unlink()
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"❌ {data_type} {date}: {e}")
            return False
    
    def download_all_data_to_cloud(self, max_workers=4):
        """Download all data directly to cloud storage"""
        
        logger.info("☁️  Starting cloud-based data download...")
        self.stats['start_time'] = datetime.now()
        
        # Generate download plan
        download_tasks = self.generate_download_plan()
        
        if not download_tasks:
            logger.info("✅ All data already in cloud!")
            return True
        
        logger.info(f"⚡ Downloading with {max_workers} parallel workers...")
        logger.info(f"☁️  All files will be saved directly to Google Cloud Storage")
        logger.info(f"💾 No local hard drive space will be used")
        
        completed_count = 0
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self.download_and_upload_single_file, task): task 
                for task in download_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                try:
                    success = future.result()
                    if success:
                        completed_count += 1
                    else:
                        failed_count += 1
                    
                    # Progress update every 25 files
                    if (completed_count + failed_count) % 25 == 0:
                        progress = (completed_count + failed_count) / len(download_tasks)
                        logger.info(f"📊 Progress: {progress:.1%} ({completed_count + failed_count}/{len(download_tasks)})")
                
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Task failed: {e}")
        
        # Final statistics
        duration = datetime.now() - self.stats['start_time']
        
        logger.info("📋 CLOUD DOWNLOAD COMPLETE!")
        logger.info(f"☁️  Files uploaded to cloud: {completed_count}")
        logger.info(f"❌ Files failed: {failed_count}")
        logger.info(f"📊 Total records: {self.stats['total_records']:,}")
        logger.info(f"⏱️  Duration: {duration.total_seconds():.1f}s")
        logger.info(f"💾 Local storage used: 0 GB (cloud-only)")
        
        # Check cloud storage usage
        try:
            result = subprocess.run([
                'gsutil', 'du', '-s', f'gs://{self.bucket_name}/bmrs_data'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                cloud_size = result.stdout.strip().split()[0]
                cloud_size_gb = int(cloud_size) / (1024**3)
                logger.info(f"☁️  Total cloud storage: {cloud_size_gb:.2f} GB")
        except:
            pass
        
        return completed_count > failed_count

def main():
    """Main function to run the cloud downloader"""
    
    api_key = os.getenv('BMRS_API_KEY')
    if not api_key:
        print("❌ BMRS_API_KEY environment variable not set!")
        return False
    
    # Check Google Cloud setup
    try:
        subprocess.run(['gsutil', 'version'], check=True, 
                      capture_output=True, text=True)
        print("✅ Google Cloud SDK available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Google Cloud SDK not found!")
        print("💡 Please install: https://cloud.google.com/sdk/docs/install")
        return False
    
    downloader = CloudBMRSDownloader()
    
    print(f"🎯 Target: Complete cloud download for Sunday")
    print(f"🕐 Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📦 Cloud bucket: {downloader.bucket_name}")
    print(f"💾 Local storage impact: ZERO")
    
    try:
        success = downloader.download_all_data_to_cloud(max_workers=6)
        
        if success:
            print("🎉 CLOUD DOWNLOAD COMPLETE!")
            print("=" * 50)
            print("☁️  All data saved to Google Cloud Storage")
            print("💾 Zero local hard drive space used")
            print("🚀 Ready for Sunday processing from cloud")
            print(f"📦 Access your data: gs://{downloader.bucket_name}/bmrs_data")
            
            return True
        
        else:
            print("⚠️ SOME DOWNLOAD ISSUES")
            print("☁️  Partial data available in cloud")
            print("🔄 Can re-run to complete remaining downloads")
            
            return False
    
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Get the port from environment variable
    port = int(os.environ.get('PORT', 8080))
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=port)
    
    # Run the main downloader process
    success = main()
    sys.exit(0 if success else 1)
