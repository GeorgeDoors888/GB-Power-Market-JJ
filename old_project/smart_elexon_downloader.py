#!/usr/bin/env python3
"""
Smart Elexon Data Downloader with Progress Estimation
====================================================
1. Checks what's already in Google Cloud Storage
2. Discovers available Elexon/BMRS datasets
3. Downloads only missing data with time estimates
4. Saves everything directly to cloud (zero local storage)
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import storage
from typing import Dict, List, Set, Optional, Tuple
import logging
from collections import defaultdict
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"
INSIGHTS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/"
BMRS_BASE = "https://api.bmrs.com/ELEXON/ws/xml/v1"

@dataclass
class DatasetInfo:
    name: str
    endpoint: str
    estimated_size_mb: float
    supports_csv: bool
    last_updated: Optional[str] = None
    record_count: Optional[int] = None

@dataclass
class DownloadProgress:
    total_datasets: int
    completed: int
    failed: int
    total_size_mb: float
    downloaded_size_mb: float
    start_time: datetime
    estimated_completion: Optional[datetime] = None

class SmartElexonDownloader:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.progress = DownloadProgress(0, 0, 0, 0.0, 0.0, datetime.now())
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Smart-Elexon-Downloader/1.0'
        })
        
        # Available datasets from Elexon Insights API
        self.available_datasets = {
            "FUELINST": DatasetInfo("FUELINST", "datasets/FUELINST", 5.2, True),
            "PN": DatasetInfo("PN", "datasets/PN", 12.8, True),
            "MELNGC": DatasetInfo("MELNGC", "datasets/MELNGC", 3.1, True),
            "TEMP": DatasetInfo("TEMP", "datasets/TEMP", 8.9, True),
            "DERSYSDEM": DatasetInfo("DERSYSDEM", "datasets/DERSYSDEM", 4.3, True),
            "WINDFOR": DatasetInfo("WINDFOR", "datasets/WINDFOR", 6.7, True),
            "PHYBMDATA": DatasetInfo("PHYBMDATA", "datasets/PHYBMDATA", 25.4, True),
            "B1770": DatasetInfo("B1770", "datasets/B1770", 15.2, True),
            "DISBSAD": DatasetInfo("DISBSAD", "datasets/DISBSAD", 8.1, True),
            "NONBM": DatasetInfo("NONBM", "datasets/NONBM", 11.3, True),
            "MKTDEPTH": DatasetInfo("MKTDEPTH", "datasets/MKTDEPTH", 7.8, True),
            "LOLPDRM": DatasetInfo("LOLPDRM", "datasets/LOLPDRM", 2.4, True),
            "INDGEN": DatasetInfo("INDGEN", "datasets/INDGEN", 18.6, True),
            "DEVINDOD": DatasetInfo("DEVINDOD", "datasets/DEVINDOD", 9.2, True),
            "SYSWARN": DatasetInfo("SYSWARN", "datasets/SYSWARN", 1.8, True),
            "MID": DatasetInfo("MID", "datasets/MID", 22.1, True),
            "QAS": DatasetInfo("QAS", "datasets/QAS", 13.7, True),
            "FORDAYDEM": DatasetInfo("FORDAYDEM", "datasets/FORDAYDEM", 4.9, True),
            "ROLSYSDEM": DatasetInfo("ROLSYSDEM", "datasets/ROLSYSDEM", 6.3, True),
            "NETBSAD": DatasetInfo("NETBSAD", "datasets/NETBSAD", 14.5, True),
        }

    def get_existing_files_in_bucket(self) -> Set[str]:
        """Get list of all files already in the bucket"""
        print("🔍 Scanning Google Cloud Storage bucket for existing files...")
        existing_files = set()
        
        try:
            blobs = self.bucket.list_blobs()
            for blob in blobs:
                # Extract dataset name from blob path
                path_parts = blob.name.split('/')
                if len(path_parts) >= 2:
                    # Assuming structure like: datasets/FUELINST/20250819_data.csv
                    dataset_name = path_parts[1] if path_parts[0] == 'datasets' else path_parts[0]
                    existing_files.add(dataset_name)
                    
        except Exception as e:
            logger.error(f"Error scanning bucket: {e}")
            
        print(f"📦 Found {len(existing_files)} existing dataset types in bucket")
        for file in sorted(existing_files):
            print(f"   ✅ {file}")
            
        return existing_files

    def discover_available_datasets(self) -> Dict[str, DatasetInfo]:
        """Discover what datasets are available from Elexon"""
        print("\n🌐 Discovering available datasets from Elexon...")
        
        try:
            # Try to get dataset list from Insights API
            response = self.session.get(f"{INSIGHTS_BASE}datasets", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"📡 Connected to Elexon Insights API successfully")
                
                # Update dataset info with real data if available
                if 'data' in data:
                    for item in data['data']:
                        dataset_name = item.get('name', '').upper()
                        if dataset_name in self.available_datasets:
                            self.available_datasets[dataset_name].last_updated = item.get('lastUpdated')
                            
        except Exception as e:
            print(f"⚠️ Could not connect to Elexon API: {e}")
            print("📝 Using predefined dataset catalog")
        
        print(f"📊 Total available datasets: {len(self.available_datasets)}")
        return self.available_datasets

    def identify_missing_datasets(self, existing: Set[str], available: Dict[str, DatasetInfo]) -> List[DatasetInfo]:
        """Identify which datasets are missing from the bucket"""
        print("\n🔍 Identifying missing datasets...")
        
        missing = []
        for dataset_name, dataset_info in available.items():
            if dataset_name not in existing:
                missing.append(dataset_info)
        
        if missing:
            print(f"📋 Found {len(missing)} missing datasets:")
            total_size = sum(d.estimated_size_mb for d in missing)
            for dataset in missing:
                print(f"   ❌ {dataset.name} (~{dataset.estimated_size_mb:.1f} MB)")
            print(f"📏 Total estimated download size: {total_size:.1f} MB")
        else:
            print("✅ All datasets already present in bucket!")
            
        return missing

    def estimate_download_time(self, datasets: List[DatasetInfo]) -> Tuple[float, float]:
        """Estimate download time based on dataset sizes"""
        total_size_mb = sum(d.estimated_size_mb for d in datasets)
        
        # Conservative estimates based on typical cloud download speeds
        # Assuming 5 MB/s average (accounting for API rate limits, processing time)
        estimated_seconds = (total_size_mb / 5.0) + (len(datasets) * 2)  # 2 seconds overhead per dataset
        
        return total_size_mb, estimated_seconds

    def download_dataset(self, dataset: DatasetInfo) -> bool:
        """Download a single dataset directly to cloud storage"""
        try:
            print(f"🚀 Downloading {dataset.name}...")
            
            # Build API URL
            url = f"{INSIGHTS_BASE}{dataset.endpoint}"
            params = {
                'format': 'csv' if dataset.supports_csv else 'json',
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Download data
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                # Create blob path
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = 'csv' if dataset.supports_csv else 'json'
                blob_name = f"datasets/{dataset.name}/{timestamp}_{dataset.name}.{file_extension}"
                
                # Upload directly to cloud
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(
                    response.text,
                    content_type='text/csv' if dataset.supports_csv else 'application/json'
                )
                
                # Update progress
                self.progress.completed += 1
                self.progress.downloaded_size_mb += dataset.estimated_size_mb
                
                print(f"   ✅ {dataset.name} saved to gs://{BUCKET_NAME}/{blob_name}")
                return True
            else:
                print(f"   ❌ Failed to download {dataset.name}: HTTP {response.status_code}")
                self.progress.failed += 1
                return False
                
        except Exception as e:
            print(f"   ❌ Error downloading {dataset.name}: {e}")
            self.progress.failed += 1
            return False

    def update_progress_estimate(self):
        """Update time estimates based on current progress"""
        if self.progress.completed > 0:
            elapsed = (datetime.now() - self.progress.start_time).total_seconds()
            rate_mb_per_second = self.progress.downloaded_size_mb / elapsed
            
            remaining_mb = self.progress.total_size_mb - self.progress.downloaded_size_mb
            remaining_seconds = remaining_mb / max(rate_mb_per_second, 0.1)
            
            self.progress.estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)

    def print_progress(self):
        """Print current progress"""
        elapsed = (datetime.now() - self.progress.start_time).total_seconds()
        
        print(f"\n📊 Progress Update:")
        print(f"   ✅ Completed: {self.progress.completed}/{self.progress.total_datasets}")
        print(f"   ❌ Failed: {self.progress.failed}")
        print(f"   📏 Downloaded: {self.progress.downloaded_size_mb:.1f}/{self.progress.total_size_mb:.1f} MB")
        print(f"   ⏱️ Elapsed: {elapsed/60:.1f} minutes")
        
        if self.progress.estimated_completion:
            remaining = (self.progress.estimated_completion - datetime.now()).total_seconds()
            print(f"   🎯 Estimated completion: {remaining/60:.1f} minutes remaining")

    def download_missing_datasets(self, missing_datasets: List[DatasetInfo]):
        """Download all missing datasets with progress tracking"""
        if not missing_datasets:
            print("✅ No datasets to download!")
            return
        
        # Initialize progress tracking
        self.progress.total_datasets = len(missing_datasets)
        self.progress.total_size_mb = sum(d.estimated_size_mb for d in missing_datasets)
        
        total_size_mb, estimated_seconds = self.estimate_download_time(missing_datasets)
        
        print(f"\n🚀 Starting download of {len(missing_datasets)} datasets...")
        print(f"📏 Total size: {total_size_mb:.1f} MB")
        print(f"⏱️ Estimated time: {estimated_seconds/60:.1f} minutes")
        print("💾 All data will be saved directly to Google Cloud Storage (0 local storage used)")
        print("=" * 60)
        
        # Download datasets
        for i, dataset in enumerate(missing_datasets, 1):
            print(f"\n[{i}/{len(missing_datasets)}] Processing {dataset.name}...")
            
            success = self.download_dataset(dataset)
            
            # Update estimates and show progress every few downloads
            if i % 3 == 0 or i == len(missing_datasets):
                self.update_progress_estimate()
                self.print_progress()
        
        # Final summary
        print("\n" + "=" * 60)
        print("📋 Download Summary:")
        print(f"   ✅ Successfully downloaded: {self.progress.completed} datasets")
        print(f"   ❌ Failed downloads: {self.progress.failed} datasets")
        print(f"   📦 Total data saved to cloud: {self.progress.downloaded_size_mb:.1f} MB")
        print(f"   💾 Local storage used: 0 bytes")
        
        elapsed_minutes = (datetime.now() - self.progress.start_time).total_seconds() / 60
        print(f"   ⏱️ Total time: {elapsed_minutes:.1f} minutes")

def main():
    """Main execution function"""
    print("🌟 Smart Elexon Data Downloader")
    print("=" * 50)
    
    downloader = SmartElexonDownloader()
    
    # Step 1: Check what's already in the bucket
    existing_files = downloader.get_existing_files_in_bucket()
    
    # Step 2: Discover available datasets
    available_datasets = downloader.discover_available_datasets()
    
    # Step 3: Identify missing datasets
    missing_datasets = downloader.identify_missing_datasets(existing_files, available_datasets)
    
    # Step 4: Download missing datasets with progress tracking
    if missing_datasets:
        downloader.download_missing_datasets(missing_datasets)
    
    print("\n🎉 Process completed!")
    print(f"📦 All data available in: gs://{BUCKET_NAME}")

if __name__ == "__main__":
    main()
