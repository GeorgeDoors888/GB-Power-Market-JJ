#!/usr/bin/env python3
"""
Simple Cloud BMRS Downloader
===========================
Downloads data directly to Google Cloud Storage
Uses existing dependencies only
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

class SimpleCloudDownloader:
    """
    Simple cloud downloader using existing dependencies
    """
    
    def __init__(self):
        # Load API key from api.env manually
        self.api_key = self._load_api_key()
        self.bucket_name = "jibber-jabber-knowledge-bmrs-data"
        self.base_url = 'https://data.elexon.co.uk/bmrs/api/v1'
        
        # Simple stats
        self.downloaded = 0
        self.failed = 0
        self.start_time = datetime.now()
        
        print(f"☁️  Simple Cloud Downloader initialized")
        print(f"✅ API Key: {'Available' if self.api_key else 'Missing'}")
        print(f"📦 Cloud bucket: {self.bucket_name}")
    
    def _load_api_key(self):
        """Load API key from api.env file"""
        try:
            with open('api.env', 'r') as f:
                for line in f:
                    if line.startswith('BMRS_API_KEY='):
                        return line.split('=', 1)[1].strip().strip('"\'')
        except FileNotFoundError:
            pass
        return None
    
    def _check_cloud_file_exists(self, cloud_path):
        """Check if file exists in cloud"""
        try:
            result = subprocess.run([
                'gsutil', 'ls', f'gs://{self.bucket_name}/{cloud_path}'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _upload_to_cloud(self, local_file, cloud_path):
        """Upload file to cloud and delete local copy"""
        try:
            result = subprocess.run([
                'gsutil', 'cp', str(local_file), 
                f'gs://{self.bucket_name}/{cloud_path}'
            ], capture_output=True, text=True, check=True)
            
            # Delete local file to save space
            local_file.unlink()
            return True
        except:
            return False
    
    def download_single_day(self, date_str):
        """Download data for a single day"""
        year = date_str[:4]
        month = date_str[5:7]
        
        # Check which data types need downloading
        data_types = ['bid_offer_acceptances', 'generation_outturn', 'demand_outturn']
        
        for data_type in data_types:
            cloud_path = f"bmrs_data/{data_type}/{year}/{month}/{data_type}_{date_str}.json"
            
            # Skip if already exists in cloud
            if self._check_cloud_file_exists(cloud_path):
                print(f"⏭️  {data_type} {date_str}: Already in cloud")
                continue
            
            # Download data using curl (available on macOS)
            try:
                endpoint_map = {
                    'bid_offer_acceptances': 'balancing/acceptances/all',
                    'generation_outturn': 'generation/outturn/summary', 
                    'demand_outturn': 'demand/outturn/summary'
                }
                
                endpoint = endpoint_map[data_type]
                all_data = []
                
                # For bid_offer_acceptances, get all settlement periods
                if data_type == 'bid_offer_acceptances':
                    for sp in range(1, 49):
                        url = f"{self.base_url}/{endpoint}?apikey={self.api_key}&settlementDate={date_str}&settlementPeriod={sp}"
                        
                        result = subprocess.run([
                            'curl', '-s', url
                        ], capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            try:
                                data = json.loads(result.stdout)
                                records = data.get('data', [])
                                
                                for record in records:
                                    record['settlement_period'] = sp
                                    record['download_method'] = 'simple_cloud_downloader'
                                
                                all_data.extend(records)
                            except:
                                pass
                        
                        time.sleep(0.1)  # Rate limiting
                
                else:
                    # Single request for other data types
                    url = f"{self.base_url}/{endpoint}?apikey={self.api_key}&settlementDate={date_str}"
                    
                    result = subprocess.run([
                        'curl', '-s', url
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        try:
                            data = json.loads(result.stdout)
                            records = data.get('data', [])
                            
                            for record in records:
                                record['download_method'] = 'simple_cloud_downloader'
                            
                            all_data = records
                        except:
                            pass
                
                # Save to temporary file and upload
                file_data = {
                    'date': date_str,
                    'data_type': data_type,
                    'download_timestamp': datetime.now().isoformat(),
                    'record_count': len(all_data),
                    'storage_location': 'google_cloud_storage',
                    'data': all_data
                }
                
                temp_file = Path(f"temp_{data_type}_{date_str}.json")
                
                with open(temp_file, 'w') as f:
                    json.dump(file_data, f, indent=2, default=str)
                
                # Upload to cloud
                if self._upload_to_cloud(temp_file, cloud_path):
                    self.downloaded += 1
                    print(f"☁️  {data_type} {date_str}: {len(all_data)} records → cloud")
                else:
                    self.failed += 1
                    print(f"❌ {data_type} {date_str}: Upload failed")
                    if temp_file.exists():
                        temp_file.unlink()
            
            except Exception as e:
                self.failed += 1
                print(f"❌ {data_type} {date_str}: {e}")
    
    def download_recent_data(self, days_back=30):
        """Download recent data to cloud"""
        print(f"🚀 Downloading last {days_back} days to cloud...")
        
        for i in range(days_back):
            target_date = datetime.now() - timedelta(days=i+1)
            date_str = target_date.strftime('%Y-%m-%d')
            
            print(f"\n📅 Processing {date_str}...")
            self.download_single_day(date_str)
            
            # Progress update
            if i % 5 == 0:
                duration = datetime.now() - self.start_time
                print(f"📊 Progress: {i+1}/{days_back} days, {self.downloaded} files uploaded, {duration.total_seconds():.0f}s")
        
        # Final summary
        duration = datetime.now() - self.start_time
        print(f"\n🎉 DOWNLOAD COMPLETE!")
        print(f"☁️  Files uploaded: {self.downloaded}")
        print(f"❌ Files failed: {self.failed}")
        print(f"⏱️  Total time: {duration.total_seconds():.0f}s")
        print(f"💾 Local storage used: 0 GB (cloud-only)")

def main():
    """Main execution"""
    print("☁️  SIMPLE CLOUD BMRS DOWNLOADER")
    print("=" * 50)
    print("Downloads data directly to Google Cloud Storage")
    print("Zero local hard drive space required!")
    print("=" * 50)
    
    # Check Google Cloud setup
    try:
        subprocess.run(['gsutil', 'version'], check=True, 
                      capture_output=True, text=True)
        print("✅ Google Cloud SDK available")
    except:
        print("❌ Google Cloud SDK not found!")
        return False
    
    downloader = SimpleCloudDownloader()
    
    if not downloader.api_key:
        print("❌ No API key found in api.env!")
        return False
    
    print(f"🎯 Target: Download recent data for Sunday processing")
    print(f"🕐 Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"💾 Local storage impact: ZERO")
    
    try:
        # Download last 30 days of data
        downloader.download_recent_data(days_back=30)
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Download interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
