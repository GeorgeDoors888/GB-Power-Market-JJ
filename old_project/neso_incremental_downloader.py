#!/usr/bin/env python3
"""
NESO Incremental Downloader - Smart Resume Capability
====================================================
Downloads only missing NESO datasets by checking what's already in cloud storage.
Much faster and more accurate than downloading everything again.
"""

import requests
import time
import json
import csv
import os
from datetime import datetime
from google.cloud import storage
from io import StringIO
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('neso_incremental_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NESOIncrementalDownloader:
    def __init__(self, bucket_name="jibber-jabber-knowledge-bmrs-data"):
        self.base_url = "https://api.neso.energy/api/3/action/"
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        
        # Rate limiting (conservative)
        self.ckan_delay = 1.0  # 1 second between CKAN calls
        self.datastore_delay = 120  # 2 minutes between datastore calls
        
        # Track progress
        self.downloaded_datasets = set()
        self.already_have_datasets = set()
        self.failed_datasets = []
        self.skipped_datasets = []  # BOD/frequency exclusions
        
    def get_existing_datasets(self):
        """Check what datasets we already have in cloud storage"""
        logger.info("🔍 Checking existing datasets in cloud storage...")
        
        existing_datasets = set()
        blobs = self.bucket.list_blobs(prefix="neso_data/")
        
        for blob in blobs:
            if blob.name.endswith("/") or "session_summary" in blob.name:
                continue
                
            # Extract dataset name from path: neso_data/dataset-name/file.csv
            path_parts = blob.name.split("/")
            if len(path_parts) >= 2:
                dataset_name = path_parts[1]
                existing_datasets.add(dataset_name)
        
        logger.info(f"✅ Found {len(existing_datasets)} existing datasets in cloud storage")
        self.already_have_datasets = existing_datasets
        return existing_datasets
    
    def discover_all_datasets(self):
        """Get complete list of available NESO datasets"""
        logger.info("🔍 Discovering all available NESO datasets...")
        
        try:
            response = requests.get(f"{self.base_url}package_list")
            response.raise_for_status()
            time.sleep(self.ckan_delay)
            
            data = response.json()
            if not data.get('success', False):
                raise Exception(f"API returned error: {data}")
            
            all_packages = data['result']
            logger.info(f"📊 Total packages discovered: {len(all_packages)}")
            
            return all_packages
            
        except Exception as e:
            logger.error(f"❌ Failed to discover datasets: {e}")
            return []
    
    def filter_datasets(self, packages):
        """Filter out BOD and frequency data as requested"""
        logger.info("🔧 Filtering datasets (excluding BOD and frequency data)...")
        
        excluded_keywords = [
            'bod', 'frequency', 'freq', 'bid-offer', 'bid offer',
            'balancing-offer', 'balancing offer'
        ]
        
        filtered_packages = []
        excluded_count = 0
        
        for package in packages:
            package_lower = package.lower()
            is_excluded = any(keyword in package_lower for keyword in excluded_keywords)
            
            if is_excluded:
                self.skipped_datasets.append(package)
                excluded_count += 1
                logger.debug(f"⏭️  Skipping (BOD/frequency): {package}")
            else:
                filtered_packages.append(package)
        
        logger.info(f"✅ Filtered to {len(filtered_packages)} datasets ({excluded_count} excluded)")
        return filtered_packages
    
    def calculate_missing_datasets(self, available_datasets):
        """Calculate which datasets we need to download"""
        existing = self.get_existing_datasets()
        filtered_available = self.filter_datasets(available_datasets)
        
        # Convert existing dataset names to match package names
        existing_slugs = set()
        for existing_name in existing:
            # Convert from folder name back to package slug
            slug = existing_name.replace('_', '-').lower()
            existing_slugs.add(slug)
        
        missing_datasets = []
        for package in filtered_available:
            if package not in existing_slugs:
                missing_datasets.append(package)
        
        logger.info(f"📊 Dataset Analysis:")
        logger.info(f"   • Total available (filtered): {len(filtered_available)}")
        logger.info(f"   • Already downloaded: {len(existing)}")
        logger.info(f"   • Missing to download: {len(missing_datasets)}")
        
        return missing_datasets
    
    def get_package_details(self, package_id):
        """Get detailed information about a specific package"""
        try:
            response = requests.get(f"{self.base_url}package_show?id={package_id}")
            response.raise_for_status()
            time.sleep(self.ckan_delay)
            
            data = response.json()
            if data.get('success', False):
                return data['result']
            else:
                logger.warning(f"⚠️  Package details failed for {package_id}: {data}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get package details for {package_id}: {e}")
            return None
    
    def safe_filename(self, name):
        """Convert names to filesystem-safe strings"""
        # Replace problematic characters
        safe = name.replace('/', '_').replace('\\', '_').replace(':', '_')
        safe = safe.replace('?', '_').replace('*', '_').replace('<', '_')
        safe = safe.replace('>', '_').replace('|', '_').replace('"', '_')
        return safe.strip()
    
    def download_resource(self, resource, dataset_folder):
        """Download a single resource (file) from a dataset"""
        try:
            resource_name = resource.get('name', 'unknown')
            resource_url = resource.get('url')
            
            if not resource_url:
                logger.warning(f"⚠️  No URL for resource: {resource_name}")
                return False
            
            logger.info(f"📥 Downloading: {resource_name}")
            
            # Download with timeout
            response = requests.get(resource_url, timeout=300)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'csv' in content_type or resource_url.endswith('.csv'):
                extension = '.csv'
            elif 'json' in content_type or resource_url.endswith('.json'):
                extension = '.json'
            elif 'png' in content_type or resource_url.endswith('.png'):
                extension = '.png'
            elif 'pdf' in content_type or resource_url.endswith('.pdf'):
                extension = '.pdf'
            else:
                extension = '.txt'  # Default
            
            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self.safe_filename(resource_name)
            filename = f"{timestamp}_{safe_name}{extension}"
            
            # Upload to cloud storage
            blob_path = f"neso_data/{dataset_folder}/{filename}"
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(response.content, content_type=content_type)
            
            logger.info(f"✅ Uploaded: {blob_path}")
            time.sleep(self.datastore_delay)  # Rate limiting
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download resource {resource_name}: {e}")
            return False
    
    def download_dataset(self, package_id):
        """Download all resources from a single dataset"""
        logger.info(f"📦 Processing dataset: {package_id}")
        
        # Get package details
        package_details = self.get_package_details(package_id)
        if not package_details:
            self.failed_datasets.append(package_id)
            return False
        
        # Create safe folder name
        dataset_folder = self.safe_filename(package_id)
        
        # Download all resources
        resources = package_details.get('resources', [])
        if not resources:
            logger.warning(f"⚠️  No resources found for {package_id}")
            return False
        
        success_count = 0
        for resource in resources:
            if self.download_resource(resource, dataset_folder):
                success_count += 1
        
        if success_count > 0:
            self.downloaded_datasets.add(package_id)
            logger.info(f"✅ Dataset complete: {package_id} ({success_count} files)")
            return True
        else:
            self.failed_datasets.append(package_id)
            logger.error(f"❌ Dataset failed: {package_id}")
            return False
    
    def save_progress_summary(self):
        """Save detailed progress summary to cloud storage"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        summary = {
            'timestamp': timestamp,
            'session_type': 'incremental_download',
            'downloaded_count': len(self.downloaded_datasets),
            'already_had_count': len(self.already_have_datasets),
            'failed_count': len(self.failed_datasets),
            'skipped_count': len(self.skipped_datasets),
            'downloaded_datasets': list(self.downloaded_datasets),
            'already_had_datasets': list(self.already_have_datasets),
            'failed_datasets': self.failed_datasets,
            'skipped_datasets': self.skipped_datasets,
            'status': 'incremental_complete'
        }
        
        # Upload summary
        blob_path = f"neso_data/incremental_summary_{timestamp}.json"
        blob = self.bucket.blob(blob_path)
        blob.upload_from_string(json.dumps(summary, indent=2))
        
        logger.info(f"📊 Progress summary saved: {blob_path}")
        return summary
    
    def run_incremental_download(self):
        """Execute the incremental download process"""
        logger.info("🚀 Starting NESO Incremental Download...")
        start_time = datetime.now()
        
        try:
            # Discover what's available
            all_packages = self.discover_all_datasets()
            if not all_packages:
                logger.error("❌ No packages discovered. Exiting.")
                return
            
            # Calculate what we need to download
            missing_datasets = self.calculate_missing_datasets(all_packages)
            
            if not missing_datasets:
                logger.info("🎉 All datasets already downloaded! Nothing to do.")
                self.save_progress_summary()
                return
            
            logger.info(f"📥 Starting download of {len(missing_datasets)} missing datasets...")
            
            # Download missing datasets
            for i, package_id in enumerate(missing_datasets, 1):
                logger.info(f"📦 [{i}/{len(missing_datasets)}] {package_id}")
                
                try:
                    self.download_dataset(package_id)
                except KeyboardInterrupt:
                    logger.info("🛑 Download interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"❌ Unexpected error downloading {package_id}: {e}")
                    self.failed_datasets.append(package_id)
                    continue
            
            # Final summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("🎯 INCREMENTAL DOWNLOAD COMPLETE!")
            logger.info(f"⏱️  Duration: {duration}")
            logger.info(f"✅ New downloads: {len(self.downloaded_datasets)}")
            logger.info(f"🗂️  Already had: {len(self.already_have_datasets)}")
            logger.info(f"❌ Failed: {len(self.failed_datasets)}")
            logger.info(f"⏭️  Skipped (BOD/freq): {len(self.skipped_datasets)}")
            
            # Save final summary
            summary = self.save_progress_summary()
            
            # Estimate total data
            total_datasets = (len(self.downloaded_datasets) + 
                            len(self.already_have_datasets))
            logger.info(f"📊 Total NESO datasets now available: {total_datasets}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Critical error in incremental download: {e}")
            return None

def main():
    """Main execution function"""
    downloader = NESOIncrementalDownloader()
    
    try:
        summary = downloader.run_incremental_download()
        
        if summary:
            print("\n" + "="*60)
            print("NESO INCREMENTAL DOWNLOAD SUMMARY")
            print("="*60)
            print(f"New Downloads: {summary['downloaded_count']}")
            print(f"Already Had: {summary['already_had_count']}")
            print(f"Failed: {summary['failed_count']}")
            print(f"Skipped (BOD/freq): {summary['skipped_count']}")
            print(f"Total Available: {summary['downloaded_count'] + summary['already_had_count']}")
            print("="*60)
            
    except KeyboardInterrupt:
        print("\n🛑 Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
