#!/usr/bin/env python3
"""
Priority 2018+ Dataset Downloader
Downloads datasets introduced from 2018 onwards as specifically requested
"""

import requests
import json
import time
from datetime import datetime, timedelta
from google.cloud import storage
import os
from typing import Dict, List, Tuple
import sys

class Priority2018Downloader:
    def __init__(self):
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.client = storage.Client()
        self.bucket_name = "jibber-jabber-knowledge-bmrs-data"
        self.bucket = self.client.bucket(self.bucket_name)
        
        # Priority 2018+ datasets (as discovered)
        self.datasets_2018_plus = {
            'BOD': {
                'name': 'Bid-Offer Data',
                'size_gb': 1.4,
                'start_year': 2018,
                'priority': 'Very High',
                'api_strategy': 'single_day'  # BOD requires single-day calls
            },
            'BOALF': {
                'name': 'Balancing Services Adjustment Data',
                'size_gb': 0.8,
                'start_year': 2018,
                'priority': 'High',
                'api_strategy': 'multi_day'
            },
            'MELNGC': {
                'name': 'Market Index Data',
                'size_gb': 0.3,
                'start_year': 2018,
                'priority': 'Medium',
                'api_strategy': 'multi_day'
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Priority2018DataCollector/1.0'
        })

    def upload_to_gcs(self, data: dict, blob_path: str) -> bool:
        """Upload data directly to Google Cloud Storage"""
        try:
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            return True
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False

    def download_dataset_single_day(self, dataset: str, date: datetime) -> Tuple[bool, dict]:
        """Download single day for datasets that require daily API calls (like BOD)"""
        date_str = date.strftime('%Y-%m-%d')
        url = f"{self.base_url}/{dataset.lower()}"
        
        params = {
            'publishDateTimeFrom': f"{date_str}T00:00:00Z",
            'publishDateTimeTo': f"{date_str}T23:59:59Z",
            'format': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return False, {'error': str(e)}

    def download_dataset_multi_day(self, dataset: str, start_date: datetime, end_date: datetime) -> Tuple[bool, dict]:
        """Download multi-day range for datasets that support it"""
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        url = f"{self.base_url}/{dataset.lower()}"
        
        params = {
            'publishDateTimeFrom': f"{start_str}T00:00:00Z",
            'publishDateTimeTo': f"{end_str}T23:59:59Z",
            'format': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return False, {'error': str(e)}

    def download_priority_dataset(self, dataset_code: str) -> Dict:
        """Download a priority 2018+ dataset with progress tracking"""
        dataset_info = self.datasets_2018_plus[dataset_code]
        print(f"\n🎯 Starting {dataset_code} ({dataset_info['name']})")
        print(f"📊 Priority: {dataset_info['priority']}, Est. Size: {dataset_info['size_gb']} GB")
        
        start_time = time.time()
        total_records = 0
        total_files = 0
        
        # Calculate date range from start year to present
        start_date = datetime(dataset_info['start_year'], 1, 1)
        end_date = datetime.now()
        
        if dataset_info['api_strategy'] == 'single_day':
            # Download day by day (required for BOD)
            current_date = start_date
            while current_date <= end_date:
                success, data = self.download_dataset_single_day(dataset_code, current_date)
                
                if success and 'data' in data and data['data']:
                    # Upload to cloud
                    date_str = current_date.strftime('%Y-%m-%d')
                    blob_path = f"priority_2018_downloads/{dataset_code.lower()}/{date_str}.json"
                    
                    if self.upload_to_gcs(data, blob_path):
                        records = len(data['data'])
                        total_records += records
                        total_files += 1
                        
                        if total_files % 30 == 0:  # Progress every 30 days
                            elapsed = time.time() - start_time
                            print(f"   📈 {total_files} days, {total_records:,} records, {elapsed/60:.1f} min")
                
                current_date += timedelta(days=1)
                time.sleep(0.1)  # Rate limiting
                
        else:
            # Download in monthly chunks for efficiency
            current_date = start_date
            while current_date <= end_date:
                chunk_end = min(current_date + timedelta(days=30), end_date)
                success, data = self.download_dataset_multi_day(dataset_code, current_date, chunk_end)
                
                if success and 'data' in data and data['data']:
                    # Upload to cloud
                    chunk_str = f"{current_date.strftime('%Y-%m-%d')}_to_{chunk_end.strftime('%Y-%m-%d')}"
                    blob_path = f"priority_2018_downloads/{dataset_code.lower()}/{chunk_str}.json"
                    
                    if self.upload_to_gcs(data, blob_path):
                        records = len(data['data'])
                        total_records += records
                        total_files += 1
                        
                        elapsed = time.time() - start_time
                        print(f"   📈 Chunk {total_files}: {records:,} records, {elapsed/60:.1f} min total")
                
                current_date = chunk_end + timedelta(days=1)
                time.sleep(0.5)  # Rate limiting for larger chunks

        elapsed_total = time.time() - start_time
        
        # Save summary
        summary = {
            'dataset': dataset_code,
            'name': dataset_info['name'],
            'start_year': dataset_info['start_year'],
            'priority': dataset_info['priority'],
            'total_records': total_records,
            'total_files': total_files,
            'download_time_minutes': elapsed_total / 60,
            'estimated_size_gb': dataset_info['size_gb'],
            'download_date': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        # Upload summary
        summary_path = f"priority_2018_downloads/{dataset_code.lower()}/download_summary.json"
        self.upload_to_gcs(summary, summary_path)
        
        print(f"✅ {dataset_code} Complete: {total_records:,} records, {total_files} files, {elapsed_total/60:.1f} min")
        return summary

    def run_priority_downloads(self):
        """Download all 2018+ datasets in priority order"""
        print("🚀 PRIORITY 2018+ DATASET DOWNLOADER")
        print("=" * 50)
        print(f"📅 Target: Datasets introduced 2018 onwards")
        print(f"📦 Total: {sum(d['size_gb'] for d in self.datasets_2018_plus.values()):.1f} GB")
        
        overall_start = time.time()
        completed_datasets = []
        
        # Download in priority order
        priority_order = sorted(
            self.datasets_2018_plus.items(),
            key=lambda x: {'Very High': 1, 'High': 2, 'Medium': 3}[x[1]['priority']]
        )
        
        for dataset_code, info in priority_order:
            try:
                summary = self.download_priority_dataset(dataset_code)
                completed_datasets.append(summary)
                
                # Brief pause between datasets
                time.sleep(2)
                
            except KeyboardInterrupt:
                print(f"\n⏸️  Download interrupted by user")
                break
            except Exception as e:
                print(f"❌ {dataset_code} failed: {e}")
                continue
        
        # Final summary
        total_time = time.time() - overall_start
        total_records = sum(d['total_records'] for d in completed_datasets)
        total_files = sum(d['total_files'] for d in completed_datasets)
        
        final_summary = {
            'download_session': 'priority_2018_datasets',
            'completed_datasets': len(completed_datasets),
            'total_datasets': len(self.datasets_2018_plus),
            'total_records': total_records,
            'total_files': total_files,
            'total_time_hours': total_time / 3600,
            'datasets': completed_datasets,
            'completion_date': datetime.now().isoformat()
        }
        
        # Upload final summary
        self.upload_to_gcs(final_summary, f"priority_2018_downloads/session_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        print(f"\n🎉 DOWNLOAD SESSION COMPLETE")
        print(f"✅ {len(completed_datasets)}/{len(self.datasets_2018_plus)} datasets")
        print(f"📊 {total_records:,} total records")
        print(f"📁 {total_files:,} total files")
        print(f"⏱️  {total_time/3600:.1f} hours total")
        print(f"☁️  All data saved to: gs://{self.bucket_name}/priority_2018_downloads/")

if __name__ == "__main__":
    downloader = Priority2018Downloader()
    downloader.run_priority_downloads()
