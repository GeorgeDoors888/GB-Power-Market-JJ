#!/usr/bin/env python3
"""
Priority Historical Data Downloader
==================================
Downloads the most valuable historical datasets that are API-available
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta, date
from google.cloud import storage
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"
INSIGHTS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/"

class PriorityHistoricalDownloader:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Priority-Historical-Downloader/1.0'
        })
        
        # Priority datasets with confirmed API availability
        self.priority_datasets = {
            "MID": {
                "name": "Market Index Data",
                "priority": 1,
                "size_gb": 21.3,
                "value_score": 10
            },
            "INDGEN": {
                "name": "Individual Generation",
                "priority": 2, 
                "size_gb": 14.1,
                "value_score": 9
            },
            "NETBSAD": {
                "name": "Net Balancing Services Adjustment Data",
                "priority": 3,
                "size_gb": 13.7,
                "value_score": 8
            },
            "QAS": {
                "name": "Quiescence Application Status", 
                "priority": 4,
                "size_gb": 13.1,
                "value_score": 7
            }
        }
        
        # Statistics tracking
        self.stats = {
            'total_downloads_attempted': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'total_mb_downloaded': 0,
            'start_time': datetime.now()
        }

    def generate_date_ranges(self, start_year: int = 2020, chunk_months: int = 3) -> List[tuple]:
        """Generate date ranges for efficient downloading"""
        date_ranges = []
        
        # Start from recent years for faster value
        current_date = date(start_year, 1, 1)
        end_date = date.today()
        
        while current_date < end_date:
            chunk_end = current_date + timedelta(days=chunk_months * 30)
            if chunk_end > end_date:
                chunk_end = end_date
            
            date_ranges.append((current_date, chunk_end))
            current_date = chunk_end + timedelta(days=1)
        
        return date_ranges

    def download_dataset_chunk(self, dataset_code: str, start_date: date, end_date: date) -> bool:
        """Download a chunk of data for a specific dataset and date range"""
        try:
            # Build API request
            url = f"{INSIGHTS_BASE}datasets/{dataset_code}"
            params = {
                'format': 'csv',
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            print(f"📥 Downloading {dataset_code} from {start_date} to {end_date}...")
            
            # Make request with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        # Save directly to cloud
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        blob_name = f"historical_datasets/{dataset_code}/{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{timestamp}.csv"
                        
                        blob = self.bucket.blob(blob_name)
                        blob.upload_from_string(response.text, content_type='text/csv')
                        
                        # Update statistics
                        size_mb = len(response.text) / (1024 * 1024)
                        self.stats['successful_downloads'] += 1
                        self.stats['total_mb_downloaded'] += size_mb
                        
                        print(f"   ✅ Saved {size_mb:.1f} MB to gs://{BUCKET_NAME}/{blob_name}")
                        return True
                        
                    elif response.status_code == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        print(f"   ⏳ Rate limited, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                        
                    else:
                        print(f"   ❌ HTTP {response.status_code} for {dataset_code}")
                        break
                        
                except requests.exceptions.Timeout:
                    print(f"   ⏰ Timeout on attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    break
                    
        except Exception as e:
            print(f"   ❌ Error downloading {dataset_code}: {e}")
            
        self.stats['failed_downloads'] += 1
        return False

    def download_priority_dataset(self, dataset_code: str, max_concurrent: int = 3) -> Dict:
        """Download historical data for a priority dataset"""
        print(f"\n🎯 Starting download for {dataset_code} - {self.priority_datasets[dataset_code]['name']}")
        print(f"📊 Estimated size: {self.priority_datasets[dataset_code]['size_gb']:.1f} GB")
        
        # Generate date ranges (start with 2020 for recent valuable data)
        date_ranges = self.generate_date_ranges(start_year=2020, chunk_months=1)
        
        dataset_stats = {
            'dataset': dataset_code,
            'total_chunks': len(date_ranges),
            'successful_chunks': 0,
            'failed_chunks': 0,
            'start_time': datetime.now()
        }
        
        print(f"📅 Downloading {len(date_ranges)} monthly chunks (2020-2025)...")
        
        # Download chunks with limited concurrency to avoid overwhelming the API
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_range = {
                executor.submit(self.download_dataset_chunk, dataset_code, start_date, end_date): (start_date, end_date)
                for start_date, end_date in date_ranges
            }
            
            for future in as_completed(future_to_range):
                start_date, end_date = future_to_range[future]
                try:
                    success = future.result()
                    if success:
                        dataset_stats['successful_chunks'] += 1
                    else:
                        dataset_stats['failed_chunks'] += 1
                        
                    # Progress update every 10 chunks
                    completed = dataset_stats['successful_chunks'] + dataset_stats['failed_chunks']
                    if completed % 10 == 0:
                        progress = (completed / dataset_stats['total_chunks']) * 100
                        print(f"   📈 Progress: {completed}/{dataset_stats['total_chunks']} chunks ({progress:.1f}%)")
                        
                except Exception as e:
                    print(f"   ❌ Failed chunk {start_date} to {end_date}: {e}")
                    dataset_stats['failed_chunks'] += 1
                
                # Rate limiting between chunks
                time.sleep(0.5)
        
        dataset_stats['end_time'] = datetime.now()
        dataset_stats['duration_minutes'] = (dataset_stats['end_time'] - dataset_stats['start_time']).total_seconds() / 60
        
        success_rate = (dataset_stats['successful_chunks'] / dataset_stats['total_chunks']) * 100
        print(f"✅ {dataset_code} completed: {dataset_stats['successful_chunks']}/{dataset_stats['total_chunks']} chunks ({success_rate:.1f}% success)")
        print(f"⏱️ Duration: {dataset_stats['duration_minutes']:.1f} minutes")
        
        return dataset_stats

    def run_priority_download(self, datasets_to_download: List[str] = None):
        """Run the priority historical data download"""
        if datasets_to_download is None:
            datasets_to_download = list(self.priority_datasets.keys())
        
        print("🚀 PRIORITY HISTORICAL DATA DOWNLOAD")
        print("=" * 60)
        print(f"📅 Target period: 2020-2025 (recent high-value data)")
        print(f"🎯 Priority datasets: {', '.join(datasets_to_download)}")
        print(f"💾 Storage: Direct to Google Cloud (zero local storage)")
        print()
        
        all_dataset_stats = []
        
        for dataset_code in datasets_to_download:
            if dataset_code not in self.priority_datasets:
                print(f"⚠️ Skipping unknown dataset: {dataset_code}")
                continue
            
            dataset_result = self.download_priority_dataset(dataset_code)
            all_dataset_stats.append(dataset_result)
            
            # Brief pause between datasets
            time.sleep(2)
        
        # Generate final summary
        self.generate_download_summary(all_dataset_stats)

    def generate_download_summary(self, dataset_stats: List[Dict]):
        """Generate comprehensive download summary"""
        total_duration = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        
        print("\n" + "=" * 60)
        print("📊 DOWNLOAD SESSION SUMMARY")
        print("=" * 60)
        print(f"⏱️ Total duration: {total_duration:.1f} minutes")
        print(f"✅ Successful downloads: {self.stats['successful_downloads']}")
        print(f"❌ Failed downloads: {self.stats['failed_downloads']}")
        print(f"💾 Total data downloaded: {self.stats['total_mb_downloaded']:.1f} MB")
        print(f"🚀 Average speed: {self.stats['total_mb_downloaded']/max(total_duration, 1):.1f} MB/minute")
        print()
        
        print("📋 DATASET BREAKDOWN:")
        for stats in dataset_stats:
            success_rate = (stats['successful_chunks'] / stats['total_chunks']) * 100
            print(f"   {stats['dataset']}: {stats['successful_chunks']}/{stats['total_chunks']} chunks ({success_rate:.1f}%) - {stats['duration_minutes']:.1f} min")
        
        # Save summary to cloud
        summary_data = {
            'session_summary': {
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_minutes': total_duration,
                'total_downloads': self.stats['successful_downloads'] + self.stats['failed_downloads'],
                'successful_downloads': self.stats['successful_downloads'],
                'failed_downloads': self.stats['failed_downloads'],
                'total_mb_downloaded': round(self.stats['total_mb_downloaded'], 2)
            },
            'dataset_details': dataset_stats
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"download_sessions/priority_download_session_{timestamp}.json"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(summary_data, indent=2, default=str), content_type='application/json')
        
        print(f"\n💾 Session report saved to: gs://{BUCKET_NAME}/{blob_name}")
        print()
        print("🎯 NEXT STEPS:")
        print("   1. Review downloaded data quality")
        print("   2. Extend to earlier years (2016-2019) if needed")
        print("   3. Download additional priority datasets")
        print("   4. Set up automated incremental updates")

def main():
    """Main execution function"""
    downloader = PriorityHistoricalDownloader()
    
    # Start with highest priority dataset for testing
    print("🧪 TESTING WITH TOP PRIORITY DATASET")
    print("Starting with MID (Market Index Data) - highest value dataset")
    print("This will download recent data (2020-2025) to validate the approach")
    print()
    
    # Download just the top priority dataset first
    downloader.run_priority_download(['MID'])

if __name__ == "__main__":
    main()
