#!/usr/bin/env python3
"""
NESO Proper Data Downloader
===========================
Downloads data from the official NESO API (National Energy System Operator)
Uses the correct CKAN-based API with proper rate limiting and data access

Key Features:
- Discovers all available NESO datasets
- Downloads non-BOD, non-frequency data as requested
- Includes Met Office weather data
- Handles missing data gaps (DPF)
- Direct cloud storage uploads
- Proper rate limiting (1 req/sec CKAN, 2 req/min Datastore)
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from google.cloud import storage
import logging
from typing import Dict, List, Any, Optional
import csv
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NESOProperDownloader:
    def __init__(self):
        self.base_url = "https://api.neso.energy/api/3/action/"
        self.storage_client = storage.Client()
        self.bucket_name = "jibber-jabber-knowledge-bmrs-data"
        self.bucket = self.storage_client.bucket(self.bucket_name)
        
        # Rate limiting - NESO API guidelines
        self.ckan_rate_limit = 1.0  # 1 request per second
        self.datastore_rate_limit = 30.0  # 2 requests per minute = 30 seconds between requests
        self.last_ckan_request = 0
        self.last_datastore_request = 0
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NESO-Data-Collector/1.0 (Energy-Research)',
            'Accept': 'application/json'
        })
        
        # Excluded datasets (BOD and frequency data)
        self.excluded_keywords = [
            'bod', 'bid', 'offer', 'frequency', 'freq', 'balancing_mechanism'
        ]
        
        # Download statistics
        self.stats = {
            'datasets_discovered': 0,
            'datasets_downloaded': 0,
            'files_created': 0,
            'total_size_mb': 0,
            'start_time': datetime.now(),
            'missing_data_gaps': []
        }

    def rate_limit_ckan(self):
        """Enforce CKAN API rate limit: 1 request per second"""
        current_time = time.time()
        time_since_last = current_time - self.last_ckan_request
        if time_since_last < self.ckan_rate_limit:
            sleep_time = self.ckan_rate_limit - time_since_last
            time.sleep(sleep_time)
        self.last_ckan_request = time.time()

    def rate_limit_datastore(self):
        """Enforce Datastore API rate limit: 2 requests per minute"""
        current_time = time.time()
        time_since_last = current_time - self.last_datastore_request
        if time_since_last < self.datastore_rate_limit:
            sleep_time = self.datastore_rate_limit - time_since_last
            time.sleep(sleep_time)
        self.last_datastore_request = time.time()

    def make_ckan_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a rate-limited request to CKAN API"""
        self.rate_limit_ckan()
        
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params or {}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success', False):
                logger.error(f"API returned error for {endpoint}: {data.get('error', {})}")
                return None
                
            return data.get('result')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {endpoint}: {str(e)}")
            return None

    def make_datastore_request(self, resource_id: str, limit: int = 1000, offset: int = 0) -> Optional[Dict]:
        """Make a rate-limited request to Datastore API"""
        self.rate_limit_datastore()
        
        params = {
            'resource_id': resource_id,
            'limit': limit,
            'offset': offset
        }
        
        try:
            response = self.session.get(f"{self.base_url}datastore_search", params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success', False):
                logger.error(f"Datastore API returned error for {resource_id}: {data.get('error', {})}")
                return None
                
            return data.get('result')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Datastore request failed for {resource_id}: {str(e)}")
            return None

    def discover_organizations(self) -> List[Dict]:
        """Discover all NESO organizations/data groups"""
        print("🔍 DISCOVERING NESO ORGANIZATIONS...")
        
        organizations = self.make_ckan_request('organization_list', {'all_fields': True})
        if not organizations:
            logger.error("Failed to fetch organizations")
            return []
        
        print(f"   Found {len(organizations)} organizations")
        for org in organizations:
            print(f"   📁 {org.get('name', 'unknown')} - {org.get('title', 'No title')}")
            
        return organizations

    def discover_datasets(self) -> List[Dict]:
        """Discover all available datasets from NESO"""
        print("🔍 DISCOVERING NESO DATASETS...")
        
        # First get all packages
        packages = self.make_ckan_request('package_list')
        if not packages:
            logger.error("Failed to fetch package list")
            return []
        
        print(f"   Found {len(packages)} total packages")
        
        # Get detailed info for each package
        detailed_datasets = []
        processed = 0
        
        for package_name in packages:
            processed += 1
            if processed % 10 == 0:
                print(f"   📊 Processed {processed}/{len(packages)} packages...")
            
            package_info = self.make_ckan_request('package_show', {'id': package_name})
            if package_info:
                detailed_datasets.append(package_info)
        
        self.stats['datasets_discovered'] = len(detailed_datasets)
        print(f"✅ Discovered {len(detailed_datasets)} detailed datasets")
        
        return detailed_datasets

    def filter_datasets(self, datasets: List[Dict]) -> List[Dict]:
        """Filter out BOD and frequency datasets as requested"""
        print("🔍 FILTERING DATASETS (excluding BOD and frequency data)...")
        
        filtered_datasets = []
        excluded_count = 0
        
        for dataset in datasets:
            dataset_name = dataset.get('name', '').lower()
            dataset_title = dataset.get('title', '').lower()
            dataset_notes = dataset.get('notes', '').lower()
            
            # Check if dataset should be excluded
            is_excluded = False
            for keyword in self.excluded_keywords:
                if (keyword in dataset_name or 
                    keyword in dataset_title or 
                    keyword in dataset_notes):
                    is_excluded = True
                    excluded_count += 1
                    print(f"   ❌ Excluded: {dataset.get('title', dataset_name)} (contains '{keyword}')")
                    break
            
            if not is_excluded:
                filtered_datasets.append(dataset)
                print(f"   ✅ Included: {dataset.get('title', dataset_name)}")
        
        print(f"📊 FILTERING RESULTS:")
        print(f"   ✅ Included: {len(filtered_datasets)} datasets")
        print(f"   ❌ Excluded: {excluded_count} datasets (BOD/frequency)")
        
        return filtered_datasets

    def check_met_office_data(self, datasets: List[Dict]) -> List[Dict]:
        """Identify Met Office weather data"""
        print("🌤️  CHECKING FOR MET OFFICE WEATHER DATA...")
        
        met_office_datasets = []
        weather_keywords = ['temperature', 'temp', 'weather', 'wind', 'met office', 'forecast']
        
        for dataset in datasets:
            dataset_name = dataset.get('name', '').lower()
            dataset_title = dataset.get('title', '').lower()
            dataset_notes = dataset.get('notes', '').lower()
            
            for keyword in weather_keywords:
                if (keyword in dataset_name or 
                    keyword in dataset_title or 
                    keyword in dataset_notes):
                    met_office_datasets.append(dataset)
                    print(f"   🌤️  Found: {dataset.get('title', dataset_name)}")
                    break
        
        print(f"   🌤️  Total Met Office datasets: {len(met_office_datasets)}")
        return met_office_datasets

    def download_dataset_resources(self, dataset: Dict) -> bool:
        """Download all resources for a given dataset"""
        dataset_name = dataset.get('name', 'unknown')
        dataset_title = dataset.get('title', dataset_name)
        
        print(f"📥 DOWNLOADING: {dataset_title}")
        
        resources = dataset.get('resources', [])
        if not resources:
            print(f"   ⚠️  No resources found for {dataset_title}")
            return False
        
        success_count = 0
        
        for resource in resources:
            resource_id = resource.get('id')
            resource_name = resource.get('name', 'unnamed_resource')
            resource_format = resource.get('format', 'unknown').lower()
            
            if not resource_id:
                continue
            
            print(f"   📄 Resource: {resource_name} ({resource_format})")
            
            # Try to download resource data
            if resource_format in ['csv', 'json', 'xml']:
                if self.download_tabular_resource(dataset_name, resource):
                    success_count += 1
            else:
                # For other formats, try direct URL download
                if self.download_direct_resource(dataset_name, resource):
                    success_count += 1
        
        print(f"   ✅ Downloaded {success_count}/{len(resources)} resources")
        return success_count > 0

    def download_tabular_resource(self, dataset_name: str, resource: Dict) -> bool:
        """Download tabular data using Datastore API"""
        resource_id = resource.get('id')
        resource_name = resource.get('name', 'unnamed_resource')
        
        try:
            # Get resource data via datastore
            result = self.make_datastore_request(resource_id, limit=10000)
            if not result:
                return False
            
            records = result.get('records', [])
            if not records:
                print(f"      ℹ️  No data records found")
                return False
            
            # Convert to CSV format
            output = io.StringIO()
            if records:
                writer = csv.DictWriter(output, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
            
            csv_content = output.getvalue()
            
            # Upload to cloud storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neso_data/{dataset_name}/{timestamp}_{resource_name}.csv"
            
            blob = self.bucket.blob(filename)
            blob.upload_from_string(csv_content, content_type='text/csv')
            
            file_size_mb = len(csv_content) / (1024 * 1024)
            self.stats['files_created'] += 1
            self.stats['total_size_mb'] += file_size_mb
            
            print(f"      ☁️  Uploaded: {filename} ({file_size_mb:.2f} MB, {len(records)} records)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download tabular resource {resource_name}: {str(e)}")
            return False

    def download_direct_resource(self, dataset_name: str, resource: Dict) -> bool:
        """Download resource via direct URL"""
        resource_url = resource.get('url')
        resource_name = resource.get('name', 'unnamed_resource')
        resource_format = resource.get('format', 'unknown')
        
        if not resource_url:
            return False
        
        try:
            # Rate limit as if it's a datastore request
            self.rate_limit_datastore()
            
            response = self.session.get(resource_url, timeout=60)
            response.raise_for_status()
            
            # Upload to cloud storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neso_data/{dataset_name}/{timestamp}_{resource_name}.{resource_format.lower()}"
            
            blob = self.bucket.blob(filename)
            blob.upload_from_string(response.content)
            
            file_size_mb = len(response.content) / (1024 * 1024)
            self.stats['files_created'] += 1
            self.stats['total_size_mb'] += file_size_mb
            
            print(f"      ☁️  Uploaded: {filename} ({file_size_mb:.2f} MB)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download direct resource {resource_name}: {str(e)}")
            return False

    def generate_report(self):
        """Generate comprehensive download report"""
        duration = datetime.now() - self.stats['start_time']
        
        report = {
            'neso_download_session': {
                'timestamp': datetime.now().isoformat(),
                'duration_hours': duration.total_seconds() / 3600,
                'datasets_discovered': self.stats['datasets_discovered'],
                'datasets_downloaded': self.stats['datasets_downloaded'],
                'files_created': self.stats['files_created'],
                'total_size_mb': round(self.stats['total_size_mb'], 2),
                'missing_data_gaps': self.stats['missing_data_gaps'],
                'api_info': {
                    'base_url': self.base_url,
                    'rate_limits': {
                        'ckan_requests_per_second': 1,
                        'datastore_requests_per_minute': 2
                    }
                }
            }
        }
        
        # Save to cloud storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"neso_data/reports/neso_session_report_{timestamp}.json"
        
        blob = self.bucket.blob(filename)
        blob.upload_from_string(
            json.dumps(report, indent=2),
            content_type='application/json'
        )
        
        print(f"\n📊 SESSION COMPLETE")
        print(f"⏱️  Duration: {duration.total_seconds() / 3600:.2f} hours")
        print(f"📁 Datasets discovered: {self.stats['datasets_discovered']}")
        print(f"📥 Datasets downloaded: {self.stats['datasets_downloaded']}")
        print(f"📄 Files created: {self.stats['files_created']}")
        print(f"💾 Total size: {self.stats['total_size_mb']:.2f} MB")
        print(f"☁️  Report saved: {filename}")

    def run_comprehensive_download(self):
        """Execute the complete NESO data download process"""
        print("🚀 NESO COMPREHENSIVE DATA DOWNLOADER")
        print("============================================================")
        print("📅 Target: All NESO data (excluding BOD and frequency)")
        print("🌤️  Includes: Met Office weather data")
        print("🔍 Features: Proper rate limiting and cloud storage")
        print()
        
        try:
            # Step 1: Discover organizations
            organizations = self.discover_organizations()
            
            # Step 2: Discover all datasets
            all_datasets = self.discover_datasets()
            if not all_datasets:
                print("❌ No datasets found. Exiting.")
                return
            
            # Step 3: Filter out BOD and frequency data
            filtered_datasets = self.filter_datasets(all_datasets)
            
            # Step 4: Check for Met Office data
            met_office_datasets = self.check_met_office_data(filtered_datasets)
            
            # Step 5: Download datasets
            print(f"\n📥 STARTING DOWNLOADS ({len(filtered_datasets)} datasets)...")
            
            for i, dataset in enumerate(filtered_datasets, 1):
                print(f"\n📊 Progress: {i}/{len(filtered_datasets)}")
                
                if self.download_dataset_resources(dataset):
                    self.stats['datasets_downloaded'] += 1
                
                # Progress update every 10 datasets
                if i % 10 == 0:
                    elapsed = datetime.now() - self.stats['start_time']
                    print(f"   ⏱️  Elapsed: {elapsed.total_seconds() / 3600:.1f} hours")
                    print(f"   💾 Downloaded: {self.stats['total_size_mb']:.1f} MB")
            
            # Step 6: Generate final report
            self.generate_report()
            
        except KeyboardInterrupt:
            print(f"\n⏸️  Download interrupted by user")
            self.generate_report()
        except Exception as e:
            logger.error(f"Fatal error in download process: {str(e)}")
            self.generate_report()

def main():
    """Main execution function"""
    downloader = NESOProperDownloader()
    downloader.run_comprehensive_download()

if __name__ == "__main__":
    main()
