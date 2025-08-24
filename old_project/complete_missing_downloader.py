#!/usr/bin/env python3
"""
Complete Missing Data Downloader
Checks bucket for existing data and downloads everything missing with time estimates
"""

import requests
import json
import time
from datetime import datetime, timedelta
from google.cloud import storage
import os
from typing import Dict, List, Tuple
import sys

class CompleteMissingDownloader:
    def __init__(self):
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.client = storage.Client()
        self.bucket_name = "jibber-jabber-knowledge-bmrs-data"
        self.bucket = self.client.bucket(self.bucket_name)
        
        # All discovered datasets with estimates
        self.all_datasets = {
            'BOD': {'size_gb': 1.4, 'priority': 'Very High', 'start_year': 2018, 'category': 'trading'},
            'FUELINST': {'size_gb': 1.0, 'priority': 'Very High', 'start_year': 2016, 'category': 'generation'},
            'INDGEN': {'size_gb': 1.0, 'priority': 'Very High', 'start_year': 2016, 'category': 'generation'},
            'NETBSAD': {'size_gb': 1.0, 'priority': 'Very High', 'start_year': 2016, 'category': 'balancing'},
            'TEMP': {'size_gb': 0.9, 'priority': 'High', 'start_year': 2017, 'category': 'weather'},
            'WINDFOR': {'size_gb': 0.9, 'priority': 'High', 'start_year': 2017, 'category': 'renewables'},
            'BOALF': {'size_gb': 0.8, 'priority': 'High', 'start_year': 2018, 'category': 'trading'},
            'MID': {'size_gb': 1.0, 'priority': 'Medium', 'start_year': 2016, 'category': 'market'},
            'MELNGC': {'size_gb': 0.3, 'priority': 'Medium', 'start_year': 2018, 'category': 'market'},
            'FREQ': {'size_gb': 0.3, 'priority': 'Medium', 'start_year': 2016, 'category': 'system'},
            'SYSWARN': {'size_gb': 0.3, 'priority': 'Medium', 'start_year': 2016, 'category': 'system'},
            'DISBSAD': {'size_gb': 0.3, 'priority': 'Low', 'start_year': 2016, 'category': 'balancing'},
            'NONBM': {'size_gb': 0.3, 'priority': 'Low', 'start_year': 2016, 'category': 'generation'},
            'QAS': {'size_gb': 0.3, 'priority': 'Low', 'start_year': 2016, 'category': 'system'}
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CompleteMissingDownloader/1.0'
        })

    def check_bucket_contents(self) -> Dict[str, List[str]]:
        """Check what datasets already exist in the bucket"""
        print("🔍 Scanning bucket for existing datasets...")
        
        existing_datasets = {}
        blobs = self.bucket.list_blobs()
        
        for blob in blobs:
            # Extract dataset name from path
            path_parts = blob.name.split('/')
            if len(path_parts) >= 2:
                if 'priority_2018_downloads' in blob.name:
                    dataset = path_parts[1].upper()
                elif any(ds.lower() in blob.name.lower() for ds in self.all_datasets.keys()):
                    for ds in self.all_datasets.keys():
                        if ds.lower() in blob.name.lower():
                            dataset = ds
                            break
                else:
                    continue
                    
                if dataset not in existing_datasets:
                    existing_datasets[dataset] = []
                existing_datasets[dataset].append(blob.name)
        
        return existing_datasets

    def calculate_download_estimates(self, missing_datasets: List[str]) -> Dict:
        """Calculate time estimates for missing datasets"""
        estimates = {}
        total_size = 0
        
        # API rate assumptions
        min_rate_mbps = 2  # MB/s
        max_rate_mbps = 5  # MB/s
        
        for dataset in missing_datasets:
            if dataset in self.all_datasets:
                info = self.all_datasets[dataset]
                size_gb = info['size_gb']
                total_size += size_gb
                
                # Convert to MB and calculate time
                size_mb = size_gb * 1024
                min_time_minutes = size_mb / (max_rate_mbps * 60)
                max_time_minutes = size_mb / (min_rate_mbps * 60)
                
                estimates[dataset] = {
                    'size_gb': size_gb,
                    'size_mb': size_mb,
                    'min_time_minutes': min_time_minutes,
                    'max_time_minutes': max_time_minutes,
                    'min_time_hours': min_time_minutes / 60,
                    'max_time_hours': max_time_minutes / 60,
                    'priority': info['priority'],
                    'start_year': info['start_year'],
                    'category': info['category']
                }
        
        # Total estimates
        total_size_mb = total_size * 1024
        total_min_hours = total_size_mb / (max_rate_mbps * 60 * 60)
        total_max_hours = total_size_mb / (min_rate_mbps * 60 * 60)
        
        return {
            'datasets': estimates,
            'total_size_gb': total_size,
            'total_min_hours': total_min_hours,
            'total_max_hours': total_max_hours,
            'total_datasets': len(missing_datasets)
        }

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

    def download_dataset_smart(self, dataset: str, start_year: int) -> Dict:
        """Smart download strategy based on dataset characteristics"""
        print(f"\n🎯 Starting {dataset} ({self.all_datasets[dataset]['category']})")
        print(f"📊 Priority: {self.all_datasets[dataset]['priority']}, Size: {self.all_datasets[dataset]['size_gb']} GB")
        
        start_time = time.time()
        total_records = 0
        total_files = 0
        
        start_date = datetime(start_year, 1, 1)
        end_date = datetime.now()
        
        # Smart strategy: try monthly chunks first, fall back to daily if needed
        try:
            # Try monthly chunks (more efficient)
            current_date = start_date
            while current_date <= end_date:
                chunk_end = min(current_date + timedelta(days=30), end_date)
                
                url = f"{self.base_url}/{dataset.lower()}"
                params = {
                    'publishDateTimeFrom': f"{current_date.strftime('%Y-%m-%d')}T00:00:00Z",
                    'publishDateTimeTo': f"{chunk_end.strftime('%Y-%m-%d')}T23:59:59Z",
                    'format': 'json'
                }
                
                response = self.session.get(url, params=params, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']:
                        # Upload to cloud
                        chunk_str = f"{current_date.strftime('%Y-%m-%d')}_to_{chunk_end.strftime('%Y-%m-%d')}"
                        blob_path = f"complete_downloads/{dataset.lower()}/{chunk_str}.json"
                        
                        if self.upload_to_gcs(data, blob_path):
                            records = len(data['data'])
                            total_records += records
                            total_files += 1
                            
                            elapsed = time.time() - start_time
                            print(f"   📈 Chunk {total_files}: {records:,} records, {elapsed/60:.1f} min total")
                
                elif response.status_code == 400:
                    # Fall back to daily downloads for this dataset
                    print(f"   ⚠️  Switching to daily downloads for {dataset}")
                    return self.download_dataset_daily(dataset, start_year)
                
                current_date = chunk_end + timedelta(days=1)
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            print(f"   ❌ Monthly download failed: {e}")
            return self.download_dataset_daily(dataset, start_year)
        
        elapsed_total = time.time() - start_time
        
        summary = {
            'dataset': dataset,
            'strategy': 'monthly_chunks',
            'total_records': total_records,
            'total_files': total_files,
            'download_time_minutes': elapsed_total / 60,
            'estimated_size_gb': self.all_datasets[dataset]['size_gb'],
            'download_date': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        print(f"✅ {dataset} Complete: {total_records:,} records, {total_files} files, {elapsed_total/60:.1f} min")
        return summary

    def download_dataset_daily(self, dataset: str, start_year: int) -> Dict:
        """Daily download fallback for datasets that require it"""
        print(f"   📅 Using daily downloads for {dataset}")
        
        start_time = time.time()
        total_records = 0
        total_files = 0
        
        start_date = datetime(start_year, 1, 1)
        end_date = datetime.now()
        current_date = start_date
        
        while current_date <= end_date:
            url = f"{self.base_url}/{dataset.lower()}"
            params = {
                'publishDateTimeFrom': f"{current_date.strftime('%Y-%m-%d')}T00:00:00Z",
                'publishDateTimeTo': f"{current_date.strftime('%Y-%m-%d')}T23:59:59Z",
                'format': 'json'
            }
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']:
                        # Upload to cloud
                        date_str = current_date.strftime('%Y-%m-%d')
                        blob_path = f"complete_downloads/{dataset.lower()}/{date_str}.json"
                        
                        if self.upload_to_gcs(data, blob_path):
                            records = len(data['data'])
                            total_records += records
                            total_files += 1
                            
                            if total_files % 30 == 0:
                                elapsed = time.time() - start_time
                                print(f"   📈 {total_files} days, {total_records:,} records, {elapsed/60:.1f} min")
            except Exception as e:
                if total_files % 100 == 0:
                    print(f"   ⚠️  Day {total_files}: {e}")
            
            current_date += timedelta(days=1)
            time.sleep(0.1)  # Rate limiting
        
        elapsed_total = time.time() - start_time
        
        return {
            'dataset': dataset,
            'strategy': 'daily_downloads',
            'total_records': total_records,
            'total_files': total_files,
            'download_time_minutes': elapsed_total / 60,
            'estimated_size_gb': self.all_datasets[dataset]['size_gb'],
            'download_date': datetime.now().isoformat(),
            'status': 'completed'
        }

    def run_complete_download(self):
        """Download all missing datasets with progress tracking"""
        print("🚀 COMPLETE MISSING DATA DOWNLOADER")
        print("=" * 50)
        
        # Check what's already downloaded
        existing = self.check_bucket_contents()
        missing_datasets = [ds for ds in self.all_datasets.keys() if ds not in existing]
        
        print(f"📊 BUCKET ANALYSIS:")
        print(f"   Total datasets: {len(self.all_datasets)}")
        print(f"   Already downloaded: {len(existing)}")
        print(f"   Missing: {len(missing_datasets)}")
        
        if existing:
            print(f"\n✅ ALREADY IN BUCKET:")
            for ds in existing:
                print(f"   {ds}: {len(existing[ds])} files")
        
        if not missing_datasets:
            print(f"\n🎉 All datasets already downloaded!")
            return
        
        # Calculate estimates
        estimates = self.calculate_download_estimates(missing_datasets)
        
        print(f"\n📈 DOWNLOAD ESTIMATES:")
        print(f"   Total missing: {estimates['total_size_gb']:.1f} GB")
        print(f"   Estimated time: {estimates['total_min_hours']:.1f}-{estimates['total_max_hours']:.1f} hours")
        print(f"   Rate assumption: 2-5 MB/s")
        
        print(f"\n🎯 MISSING DATASETS (Priority Order):")
        
        # Sort by priority
        priority_order = {'Very High': 1, 'High': 2, 'Medium': 3, 'Low': 4}
        sorted_missing = sorted(missing_datasets, 
                               key=lambda x: (priority_order.get(self.all_datasets[x]['priority'], 5),
                                             -self.all_datasets[x]['size_gb']))
        
        for i, dataset in enumerate(sorted_missing, 1):
            est = estimates['datasets'][dataset]
            print(f"   {i:2d}. {dataset}: {est['size_gb']:.1f}GB → {est['min_time_hours']:.1f}-{est['max_time_hours']:.1f}h ({est['priority']})")
        
        # Start downloads
        print(f"\n🚀 STARTING DOWNLOADS...")
        overall_start = time.time()
        completed = []
        
        for dataset in sorted_missing:
            try:
                start_year = self.all_datasets[dataset]['start_year']
                summary = self.download_dataset_smart(dataset, start_year)
                completed.append(summary)
                
                # Save progress
                progress_path = f"complete_downloads/session_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                progress_data = {
                    'session_start': overall_start,
                    'completed_datasets': len(completed),
                    'remaining_datasets': len(sorted_missing) - len(completed),
                    'completed': completed
                }
                self.upload_to_gcs(progress_data, progress_path)
                
                time.sleep(2)  # Brief pause between datasets
                
            except KeyboardInterrupt:
                print(f"\n⏸️  Download interrupted by user")
                break
            except Exception as e:
                print(f"❌ {dataset} failed: {e}")
                continue
        
        # Final summary
        total_time = time.time() - overall_start
        total_records = sum(d['total_records'] for d in completed)
        total_files = sum(d['total_files'] for d in completed)
        
        final_summary = {
            'download_session': 'complete_missing_datasets',
            'completed_datasets': len(completed),
            'total_missing': len(missing_datasets),
            'total_records': total_records,
            'total_files': total_files,
            'total_time_hours': total_time / 3600,
            'datasets': completed,
            'completion_date': datetime.now().isoformat()
        }
        
        self.upload_to_gcs(final_summary, f"complete_downloads/final_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        print(f"\n🎉 DOWNLOAD SESSION COMPLETE")
        print(f"✅ {len(completed)}/{len(missing_datasets)} datasets downloaded")
        print(f"📊 {total_records:,} total records")
        print(f"📁 {total_files:,} total files") 
        print(f"⏱️  {total_time/3600:.1f} hours total")
        print(f"☁️  All data saved to: gs://{self.bucket_name}/complete_downloads/")

if __name__ == "__main__":
    downloader = CompleteMissingDownloader()
    downloader.run_complete_download()
