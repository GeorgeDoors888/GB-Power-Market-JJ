#!/usr/bin/env python3
"""
Quick Start: Download Confirmed Working Datasets
===============================================
Ready-to-run script for downloading the 5 confirmed working historical datasets
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta, date
from google.cloud import storage
from typing import List, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"
INSIGHTS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/"

class QuickStartDownloader:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuickStart-Downloader/1.0'
        })
        
        # Confirmed working datasets
        self.working_datasets = {
            "INDGEN": {"name": "Individual Generation", "priority": 1, "size_gb": 14.09},
            "NETBSAD": {"name": "Net Balancing Services", "priority": 2, "size_gb": 13.74},
            "TEMP": {"name": "Temperature Data", "priority": 3, "size_gb": 6.46},
            "WINDFOR": {"name": "Wind Forecast", "priority": 4, "size_gb": 5.28},
            "FUELINST": {"name": "Fuel Instruction", "priority": 5, "size_gb": 5.15}
        }

    def download_recent_sample(self, dataset_code: str, days_back: int = 30) -> bool:
        """Download a recent sample to test the dataset"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            url = f"{INSIGHTS_BASE}datasets/{dataset_code}"
            params = {
                'format': 'csv',
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            print(f"📥 Testing {dataset_code} ({self.working_datasets[dataset_code]['name']})...")
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                # Save to cloud
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob_name = f"quickstart_samples/{dataset_code}_sample_{timestamp}.csv"
                
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(response.text, content_type='text/csv')
                
                size_mb = len(response.text) / (1024 * 1024)
                print(f"   ✅ Success! {size_mb:.1f} MB saved to gs://{BUCKET_NAME}/{blob_name}")
                return True
            else:
                print(f"   ❌ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def estimate_full_download(self, successful_datasets: List[str]):
        """Estimate time for full historical download"""
        total_size_gb = sum(self.working_datasets[ds]['size_gb'] for ds in successful_datasets)
        
        print(f"\n📊 FULL HISTORICAL DOWNLOAD ESTIMATES:")
        print(f"💾 Total size: {total_size_gb:.1f} GB")
        print(f"⏱️ Estimated times:")
        print(f"   • Conservative (2 GB/hour): {total_size_gb/2:.1f} hours")
        print(f"   • Moderate (5 GB/hour): {total_size_gb/5:.1f} hours") 
        print(f"   • Optimistic (10 GB/hour): {total_size_gb/10:.1f} hours")

    def create_download_plan(self, successful_datasets: List[str]):
        """Create a specific download plan"""
        print(f"\n🎯 RECOMMENDED DOWNLOAD PLAN:")
        print(f"=" * 50)
        
        for i, dataset in enumerate(successful_datasets, 1):
            info = self.working_datasets[dataset]
            print(f"{i}. {dataset} - {info['name']}")
            print(f"   💾 Size: {info['size_gb']:.1f} GB")
            print(f"   ⏱️ Est. time: {info['size_gb']/5:.1f} hours @ 5 GB/hour")
            print()
        
        # Save plan to cloud
        plan_data = {
            'created': datetime.now().isoformat(),
            'successful_datasets': successful_datasets,
            'total_size_gb': sum(self.working_datasets[ds]['size_gb'] for ds in successful_datasets),
            'download_order': [
                {
                    'dataset': ds,
                    'name': self.working_datasets[ds]['name'],
                    'size_gb': self.working_datasets[ds]['size_gb'],
                    'priority': self.working_datasets[ds]['priority']
                }
                for ds in successful_datasets
            ],
            'next_steps': [
                'Run priority_historical_downloader.py with these confirmed datasets',
                'Start with recent years (2020-2025) for faster value',
                'Monitor progress and adjust rate limiting as needed',
                'Set up automated daily incremental updates'
            ]
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"download_plans/quickstart_plan_{timestamp}.json"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(plan_data, indent=2), content_type='application/json')
        
        print(f"💾 Download plan saved to: gs://{BUCKET_NAME}/{blob_name}")

    def run_quick_test(self):
        """Run quick test of all working datasets"""
        print("🚀 QUICK START: TESTING CONFIRMED WORKING DATASETS")
        print("=" * 60)
        print("Testing recent data samples to confirm API access...")
        print()
        
        successful_datasets = []
        
        for dataset_code in self.working_datasets.keys():
            if self.download_recent_sample(dataset_code):
                successful_datasets.append(dataset_code)
            time.sleep(1)  # Rate limiting
        
        print(f"\n📊 RESULTS:")
        print(f"✅ Successful: {len(successful_datasets)}/{len(self.working_datasets)} datasets")
        print(f"📂 Ready for historical download: {', '.join(successful_datasets)}")
        
        if successful_datasets:
            self.estimate_full_download(successful_datasets)
            self.create_download_plan(successful_datasets)
            
            print(f"\n🎯 IMMEDIATE NEXT STEPS:")
            print(f"1. Review the sample data in your bucket (quickstart_samples/)")
            print(f"2. Run the full historical downloader for these confirmed datasets")
            print(f"3. Start with the highest priority: {successful_datasets[0] if successful_datasets else 'None'}")
        else:
            print(f"\n⚠️ No datasets worked. Check API access or try again later.")

def main():
    """Main execution function"""
    downloader = QuickStartDownloader()
    downloader.run_quick_test()

if __name__ == "__main__":
    main()
