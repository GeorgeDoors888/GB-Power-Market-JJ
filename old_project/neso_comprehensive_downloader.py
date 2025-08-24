#!/usr/bin/env python3
"""
NESO Data Comprehensive Downloader
Downloads all NESO (National Energy System Operator) data excluding BOD and frequency
Includes Met Office weather data check and DPF missing data handling
"""

import requests
import json
import time
from datetime import datetime, timedelta
from google.cloud import storage
import os
from typing import Dict, List, Tuple
import sys

class NESOComprehensiveDownloader:
    def __init__(self):
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.client = storage.Client()
        self.bucket_name = "jibber-jabber-knowledge-bmrs-data"
        self.bucket = self.client.bucket(self.bucket_name)
        
        # NESO datasets (excluding BOD and FREQ as requested)
        self.neso_datasets = {
            'FUELINST': {
                'name': 'Fuel Instructions',
                'priority': 'Very High',
                'start_year': 2016,
                'description': 'Real-time monitoring of fuel types (gas, coal, nuclear, renewables) and output levels'
            },
            'INDGEN': {
                'name': 'Individual Generation',
                'priority': 'Very High', 
                'start_year': 2016,
                'description': 'Performance metrics for each power station including output capacity and availability'
            },
            'NETBSAD': {
                'name': 'Network Balancing Services',
                'priority': 'Very High',
                'start_year': 2016,
                'description': 'Grid balancing actions to maintain supply-demand equilibrium and frequency response'
            },
            'TEMP': {
                'name': 'Temperature Forecasts',
                'priority': 'High',
                'start_year': 2017,
                'description': 'Weather temperature predictions for electricity demand forecasting (Met Office data)'
            },
            'WINDFOR': {
                'name': 'Wind Forecasts', 
                'priority': 'High',
                'start_year': 2017,
                'description': 'Predicted wind power generation based on weather forecasts'
            },
            'MELNGC': {
                'name': 'Market Index Data',
                'priority': 'Medium',
                'start_year': 2018,
                'description': 'Electricity market pricing indices and marginal costs'
            },
            'MID': {
                'name': 'Market Depth Indicators',
                'priority': 'Medium',
                'start_year': 2016,
                'description': 'Trading volume, bid-ask spreads, and market liquidity measurements'
            },
            'SYSWARN': {
                'name': 'System Warnings',
                'priority': 'Medium',
                'start_year': 2016,
                'description': 'Grid operator alerts about supply shortages and system stability issues'
            },
            'BOALF': {
                'name': 'Balancing Services Adjustment',
                'priority': 'High',
                'start_year': 2018,
                'description': 'Adjustments to balancing mechanism actions for grid frequency control'
            },
            'DISBSAD': {
                'name': 'Disaggregated Balancing Services',
                'priority': 'Low',
                'start_year': 2016,
                'description': 'Detailed balancing services costs and volumes for grid stability'
            },
            'NONBM': {
                'name': 'Non-Balancing Mechanism',
                'priority': 'Low',
                'start_year': 2016,
                'description': 'Generation and demand outside main balancing mechanism'
            },
            'QAS': {
                'name': 'Quality Assurance System',
                'priority': 'Low',
                'start_year': 2016,
                'description': 'Data quality metrics and validation results'
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NESOComprehensiveDownloader/1.0'
        })

    def check_met_office_data(self) -> Dict:
        """Check for existing Met Office weather data in bucket"""
        print("🌤️  CHECKING MET OFFICE WEATHER DATA...")
        
        weather_data = {
            'TEMP': {'files': [], 'coverage': []},
            'weather_related': []
        }
        
        for blob in self.bucket.list_blobs():
            if any(weather_term in blob.name.lower() for weather_term in ['temp', 'weather', 'met_office', 'temperature']):
                if 'temp' in blob.name.lower():
                    weather_data['TEMP']['files'].append(blob.name)
                else:
                    weather_data['weather_related'].append(blob.name)
        
        print(f"   TEMP files found: {len(weather_data['TEMP']['files'])}")
        print(f"   Other weather files: {len(weather_data['weather_related'])}")
        
        return weather_data

    def check_existing_coverage(self, dataset: str) -> Dict:
        """Check what coverage already exists for a dataset"""
        existing_files = []
        coverage_gaps = []
        
        prefix = f"neso_data/{dataset.lower()}/"
        for blob in self.bucket.list_blobs(prefix=prefix):
            existing_files.append(blob.name)
        
        # Also check in other folders
        for blob in self.bucket.list_blobs():
            if dataset.lower() in blob.name.lower():
                existing_files.append(blob.name)
        
        return {
            'files': existing_files,
            'count': len(existing_files),
            'gaps': coverage_gaps
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

    def download_monthly_data(self, dataset: str, year: int, month: int) -> Tuple[bool, dict, int]:
        """Download one month of data for a dataset with DPF missing data handling"""
        start_date = datetime(year, month, 1)
        
        # Calculate end date (last day of month)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        url = f"{self.base_url}/{dataset.lower()}"
        params = {
            'publishDateTimeFrom': f"{start_date.strftime('%Y-%m-%d')}T00:00:00Z",
            'publishDateTimeTo': f"{end_date.strftime('%Y-%m-%d')}T23:59:59Z",
            'format': 'json'
        }
        
        try:
            print(f"   📅 Downloading {dataset} {year}-{month:02d}...")
            response = self.session.get(url, params=params, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                records = len(data.get('data', []))
                
                # DPF: Handle missing data with detailed reporting
                if records == 0:
                    print(f"   ⚠️  DPF: No data found for {dataset} {year}-{month:02d} (possible data gap)")
                    # Still save the empty response for completeness
                    data['dpf_status'] = 'no_data_available'
                    data['query_params'] = params
                    data['query_timestamp'] = datetime.now().isoformat()
                
                return True, data, records
            
            elif response.status_code == 404:
                print(f"   ❌ {dataset} {year}-{month:02d}: API endpoint not found")
                return False, {'error': 'endpoint_not_found', 'status_code': 404}, 0
            
            elif response.status_code == 400:
                print(f"   ❌ {dataset} {year}-{month:02d}: Bad request (possibly invalid date range)")
                return False, {'error': 'bad_request', 'status_code': 400}, 0
            
            else:
                print(f"   ❌ {dataset} {year}-{month:02d}: HTTP {response.status_code}")
                return False, {'error': f'http_{response.status_code}'}, 0
                
        except Exception as e:
            print(f"   ❌ {dataset} {year}-{month:02d}: Network error - {e}")
            return False, {'error': str(e)}, 0

    def download_dataset_systematically(self, dataset_code: str) -> Dict:
        """Download a complete dataset month by month from start year to present"""
        dataset_info = self.neso_datasets[dataset_code]
        print(f"\n🎯 Starting systematic download: {dataset_code} ({dataset_info['name']})")
        print(f"📊 Priority: {dataset_info['priority']}")
        print(f"📅 Coverage: {dataset_info['start_year']} to present")
        print(f"🔍 Description: {dataset_info['description']}")
        
        start_time = time.time()
        total_records = 0
        total_files = 0
        total_months = 0
        dpf_gaps = []
        
        # Check existing coverage
        existing = self.check_existing_coverage(dataset_code)
        print(f"📁 Existing files: {existing['count']}")
        
        start_year = dataset_info['start_year']
        current_date = datetime.now()
        
        # Download month by month
        for year in range(start_year, current_date.year + 1):
            start_month = 1
            end_month = 12
            
            # Adjust for current year
            if year == current_date.year:
                end_month = current_date.month
            
            for month in range(start_month, end_month + 1):
                success, data, records = self.download_monthly_data(dataset_code, year, month)
                
                if success:
                    # Upload to cloud
                    month_str = f"{year}-{month:02d}"
                    blob_path = f"neso_data/{dataset_code.lower()}/{month_str}.json"
                    
                    if self.upload_to_gcs(data, blob_path):
                        total_records += records
                        total_files += 1
                        total_months += 1
                        
                        if records == 0:
                            dpf_gaps.append(month_str)
                        
                        if total_months % 12 == 0:  # Progress every year
                            elapsed = time.time() - start_time
                            print(f"   📈 {total_months} months completed, {total_records:,} records, {elapsed/60:.1f} min")
                
                # Rate limiting
                time.sleep(0.2)
        
        elapsed_total = time.time() - start_time
        
        # Generate summary
        summary = {
            'dataset': dataset_code,
            'name': dataset_info['name'],
            'description': dataset_info['description'],
            'priority': dataset_info['priority'],
            'start_year': start_year,
            'total_records': total_records,
            'total_files': total_files,
            'total_months': total_months,
            'download_time_minutes': elapsed_total / 60,
            'dpf_gaps': dpf_gaps,
            'dpf_gap_count': len(dpf_gaps),
            'download_date': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        # Upload summary
        summary_path = f"neso_data/{dataset_code.lower()}/download_summary.json"
        self.upload_to_gcs(summary, summary_path)
        
        print(f"✅ {dataset_code} Complete:")
        print(f"   📊 {total_records:,} records across {total_months} months")
        print(f"   ⏱️  {elapsed_total/60:.1f} minutes")
        print(f"   🔍 DPF gaps: {len(dpf_gaps)} months with no data")
        
        return summary

    def update_comprehensive_report(self, session_summary: Dict):
        """Update the comprehensive project report with new NESO download results"""
        print("\n📝 UPDATING COMPREHENSIVE PROJECT REPORT...")
        
        # Read existing report
        report_file = "comprehensive_project_report_20250820_001932.txt"
        try:
            with open(report_file, 'r') as f:
                existing_report = f.read()
        except:
            existing_report = ""
        
        # Generate NESO download section
        neso_section = f"""

NESO DATA DOWNLOAD SESSION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===============================================================================

NESO (National Energy System Operator) Data Collection Results:
- Datasets Downloaded: {session_summary['completed_datasets']}
- Total Records: {session_summary['total_records']:,}
- Total Files: {session_summary['total_files']:,}
- Download Time: {session_summary['total_time_hours']:.2f} hours
- DPF Gaps Identified: {sum(d.get('dpf_gap_count', 0) for d in session_summary.get('datasets', []))}

DATASET BREAKDOWN:
"""
        
        for dataset in session_summary.get('datasets', []):
            neso_section += f"""
{dataset['dataset']} ({dataset['name']}):
- Records: {dataset['total_records']:,}
- Coverage: {dataset['total_months']} months from {dataset['start_year']}
- Priority: {dataset['priority']}
- DPF Gaps: {dataset.get('dpf_gap_count', 0)} months
- Description: {dataset['description']}
"""
        
        # Append to existing report
        updated_report = existing_report + neso_section
        
        # Save updated report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_report_file = f"comprehensive_project_report_updated_{timestamp}.txt"
        
        with open(new_report_file, 'w') as f:
            f.write(updated_report)
        
        print(f"📄 Updated report saved: {new_report_file}")
        
        # Also upload to cloud
        report_blob_path = f"reports/comprehensive_project_report_updated_{timestamp}.txt"
        blob = self.bucket.blob(report_blob_path)
        blob.upload_from_string(updated_report, content_type='text/plain')
        
        print(f"☁️  Report uploaded to: gs://{self.bucket_name}/{report_blob_path}")

    def run_neso_comprehensive_download(self):
        """Run complete NESO data download excluding BOD and FREQ"""
        print("🚀 NESO COMPREHENSIVE DATA DOWNLOADER")
        print("=" * 60)
        print("📅 Target: All NESO data (excluding BOD and FREQ as requested)")
        print("🌤️  Includes: Met Office weather data check")
        print("🔍 Features: DPF missing data handling")
        
        overall_start = time.time()
        
        # Check Met Office data first
        weather_data = self.check_met_office_data()
        
        # Download datasets in priority order
        priority_order = sorted(
            self.neso_datasets.items(),
            key=lambda x: {'Very High': 1, 'High': 2, 'Medium': 3, 'Low': 4}[x[1]['priority']]
        )
        
        completed_datasets = []
        
        print(f"\n📋 DOWNLOAD ORDER ({len(priority_order)} datasets):")
        for i, (code, info) in enumerate(priority_order, 1):
            print(f"   {i:2d}. {code}: {info['name']} ({info['priority']} priority)")
        
        print(f"\n🚀 STARTING CONSECUTIVE DOWNLOADS...")
        
        for dataset_code, info in priority_order:
            try:
                summary = self.download_dataset_systematically(dataset_code)
                completed_datasets.append(summary)
                
                # Brief pause between datasets
                time.sleep(3)
                
            except KeyboardInterrupt:
                print(f"\n⏸️  Download interrupted by user")
                break
            except Exception as e:
                print(f"❌ {dataset_code} failed: {e}")
                continue
        
        # Final session summary
        total_time = time.time() - overall_start
        total_records = sum(d['total_records'] for d in completed_datasets)
        total_files = sum(d['total_files'] for d in completed_datasets)
        
        session_summary = {
            'download_session': 'neso_comprehensive',
            'session_date': datetime.now().isoformat(),
            'completed_datasets': len(completed_datasets),
            'total_datasets': len(self.neso_datasets),
            'total_records': total_records,
            'total_files': total_files,
            'total_time_hours': total_time / 3600,
            'weather_data_check': weather_data,
            'datasets': completed_datasets
        }
        
        # Upload session summary
        session_path = f"neso_data/session_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.upload_to_gcs(session_summary, session_path)
        
        # Update comprehensive report
        self.update_comprehensive_report(session_summary)
        
        print(f"\n🎉 NESO DOWNLOAD SESSION COMPLETE")
        print(f"✅ {len(completed_datasets)}/{len(self.neso_datasets)} datasets downloaded")
        print(f"📊 {total_records:,} total records")
        print(f"📁 {total_files:,} total files")
        print(f"⏱️  {total_time/3600:.2f} hours total")
        print(f"🌤️  Met Office data: {len(weather_data['TEMP']['files'])} TEMP files found")
        print(f"☁️  All data saved to: gs://{self.bucket_name}/neso_data/")

if __name__ == "__main__":
    downloader = NESOComprehensiveDownloader()
    downloader.run_neso_comprehensive_download()
