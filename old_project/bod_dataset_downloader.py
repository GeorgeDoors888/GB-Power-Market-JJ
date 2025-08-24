#!/usr/bin/env python3
"""
BOD Dataset Downloader
=====================
Downloads BOD (Bid-Offer Data) and BOALF datasets from 2018 onwards
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta, date
from google.cloud import storage
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"
INSIGHTS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/"

class BODDataDownloader:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BOD-Downloader/1.0'
        })
        
        self.bod_datasets = {
            "BOD": {
                "name": "Bid-Offer Data",
                "description": "Energy market bid and offer prices",
                "estimated_records_per_day": 3419,
                "high_value": True
            },
            "BOALF": {
                "name": "Bid-Offer Acceptance Level Flagged", 
                "description": "Accepted bids with flags and levels",
                "estimated_records_per_day": 3,
                "high_value": False
            }
        }
        
        self.stats = {
            'downloads_attempted': 0,
            'downloads_successful': 0,
            'total_records_downloaded': 0,
            'total_mb_downloaded': 0,
            'start_time': datetime.now()
        }

    def download_bod_dataset_sample(self, dataset_code: str, days_back: int = 7) -> bool:
        """Download a recent sample of BOD data"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            url = f"{INSIGHTS_BASE}datasets/{dataset_code}"
            params = {
                'format': 'csv',
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            print(f"📥 Downloading {dataset_code} sample ({start_date} to {end_date})...")
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                # Save to cloud
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob_name = f"bod_datasets/{dataset_code}/{dataset_code}_sample_{timestamp}.csv"
                
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(response.text, content_type='text/csv')
                
                # Calculate stats
                size_mb = len(response.text) / (1024 * 1024)
                record_count = response.text.count('\\n') - 1  # Minus header
                
                self.stats['downloads_successful'] += 1
                self.stats['total_mb_downloaded'] += size_mb
                self.stats['total_records_downloaded'] += record_count
                
                print(f"   ✅ Success! {size_mb:.1f} MB, {record_count:,} records")
                print(f"   📁 Saved to: gs://{BUCKET_NAME}/{blob_name}")
                return True
            else:
                print(f"   ❌ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        finally:
            self.stats['downloads_attempted'] += 1

    def download_bod_historical_chunk(self, dataset_code: str, start_date: date, end_date: date) -> bool:
        """Download a chunk of historical BOD data"""
        try:
            url = f"{INSIGHTS_BASE}datasets/{dataset_code}"
            params = {
                'format': 'csv',
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            print(f"📥 {dataset_code}: {start_date} to {end_date}...")
            
            response = self.session.get(url, params=params, timeout=45)
            
            if response.status_code == 200:
                # Save to cloud
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob_name = f"bod_datasets/{dataset_code}/{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{timestamp}.csv"
                
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(response.text, content_type='text/csv')
                
                # Calculate stats
                size_mb = len(response.text) / (1024 * 1024)
                record_count = response.text.count('\\n') - 1
                
                self.stats['downloads_successful'] += 1
                self.stats['total_mb_downloaded'] += size_mb
                self.stats['total_records_downloaded'] += record_count
                
                print(f"   ✅ {size_mb:.1f} MB, {record_count:,} records -> gs://{BUCKET_NAME}/{blob_name}")
                return True
            else:
                print(f"   ❌ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        finally:
            self.stats['downloads_attempted'] += 1

    def generate_download_plan(self, start_year: int = 2020):
        """Generate date ranges for downloading"""
        # Start with recent years for immediate value
        start_date = date(start_year, 1, 1)
        end_date = date.today()
        
        # Monthly chunks to avoid timeouts
        date_ranges = []
        current_date = start_date
        
        while current_date < end_date:
            chunk_end = current_date + timedelta(days=30)  # ~1 month chunks
            if chunk_end > end_date:
                chunk_end = end_date
            
            date_ranges.append((current_date, chunk_end))
            current_date = chunk_end + timedelta(days=1)
        
        return date_ranges

    def run_bod_sample_test(self):
        """Test BOD datasets with recent samples"""
        print("🧪 BOD DATASET SAMPLE TEST")
        print("=" * 50)
        print("Testing BOD datasets with recent 7-day samples...")
        print()
        
        successful_datasets = []
        
        for dataset_code, info in self.bod_datasets.items():
            print(f"🎯 Testing {dataset_code} - {info['name']}")
            if self.download_bod_dataset_sample(dataset_code):
                successful_datasets.append(dataset_code)
            print()
        
        # Summary
        print("📊 TEST RESULTS:")
        print(f"✅ Successful: {len(successful_datasets)}/{len(self.bod_datasets)} datasets")
        print(f"📁 Ready datasets: {', '.join(successful_datasets)}")
        print(f"📄 Total records: {self.stats['total_records_downloaded']:,}")
        print(f"💾 Total size: {self.stats['total_mb_downloaded']:.1f} MB")
        
        return successful_datasets

    def run_historical_download(self, datasets: list, start_year: int = 2020, max_chunks: int = 6):
        """Download historical BOD data"""
        print(f"\\n🚀 BOD HISTORICAL DOWNLOAD (from {start_year})")
        print("=" * 50)
        
        date_ranges = self.generate_download_plan(start_year)
        
        print(f"📅 Downloading {len(date_ranges)} monthly chunks")
        print(f"🎯 Datasets: {', '.join(datasets)}")
        print(f"⚠️ Limited to first {max_chunks} chunks for testing")
        print()
        
        # Limit chunks for testing
        limited_ranges = date_ranges[:max_chunks]
        
        for dataset_code in datasets:
            print(f"🎯 Processing {dataset_code}...")
            
            for i, (start_date, end_date) in enumerate(limited_ranges, 1):
                print(f"   [{i}/{len(limited_ranges)}] ", end="")
                self.download_bod_historical_chunk(dataset_code, start_date, end_date)
                time.sleep(0.5)  # Rate limiting
            
            print()
        
        # Final summary
        total_time = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        print(f"📋 DOWNLOAD SUMMARY:")
        print(f"   ✅ Successful: {self.stats['downloads_successful']}/{self.stats['downloads_attempted']}")
        print(f"   📄 Total records: {self.stats['total_records_downloaded']:,}")
        print(f"   💾 Total size: {self.stats['total_mb_downloaded']:.1f} MB")
        print(f"   ⏱️ Time: {total_time:.1f} minutes")
        print(f"   🚀 Speed: {self.stats['total_mb_downloaded']/max(total_time, 1):.1f} MB/min")

def main():
    """Main execution"""
    downloader = BODDataDownloader()
    
    # First test with samples
    successful_datasets = downloader.run_bod_sample_test()
    
    if successful_datasets:
        # Then download some historical data
        downloader.run_historical_download(successful_datasets, start_year=2020, max_chunks=6)
        
        print("\\n🎯 NEXT STEPS:")
        print("1. Review downloaded BOD data in your bucket")
        print("2. Extend to full historical range (2018-2025)")
        print("3. Integrate BOD data with your existing energy market analysis")
    else:
        print("\\n⚠️ No BOD datasets worked. Check API status.")

if __name__ == "__main__":
    main()
