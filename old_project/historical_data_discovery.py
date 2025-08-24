#!/usr/bin/env python3
"""
Historical Elexon Data Discovery (2016-2025)
===========================================
Discovers what historical data is available on Elexon dating back to 2016
that is not already in the Google Cloud Storage bucket.
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta, date
from google.cloud import storage
from typing import Dict, List, Set, Tuple
import logging
from collections import defaultdict
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"
INSIGHTS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/"
BMRS_BASE = "https://api.bmrs.com/ELEXON/ws/xml/v1"

class HistoricalDataDiscovery:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Historical-Data-Discovery/1.0'
        })
        
        # Start date for historical analysis
        self.start_date = date(2016, 1, 1)
        self.end_date = date.today()
        
        # Known Elexon datasets and their historical availability
        self.elexon_datasets = {
            "FUELINST": {
                "name": "Fuel Instruction",
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 1.5
            },
            "SYSMSG": {
                "name": "System Messages", 
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 0.8
            },
            "TEMP": {
                "name": "Temperature Data",
                "available_from": "2017-01-01", 
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 2.1
            },
            "WINDFOR": {
                "name": "Wind Forecast",
                "available_from": "2017-06-01",
                "frequency": "daily", 
                "estimated_files_per_year": 365,
                "avg_size_mb": 1.8
            },
            "DERSYSDEM": {
                "name": "Derived System Demand",
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365, 
                "avg_size_mb": 1.2
            },
            "PHYBMDATA": {
                "name": "Physical BM Data",
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 5.8
            },
            "MELNGC": {
                "name": "Meter Lead Non-Generation Capacity",
                "available_from": "2018-01-01",
                "frequency": "daily", 
                "estimated_files_per_year": 365,
                "avg_size_mb": 0.9
            },
            "NONBM": {
                "name": "Non-BM Data",
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 3.2
            },
            "INDGEN": {
                "name": "Individual Generation",
                "available_from": "2016-01-01", 
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 4.1
            },
            "SYSWARN": {
                "name": "System Warnings",
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 0.5
            },
            "MID": {
                "name": "Market Index Data", 
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 6.2
            },
            "NETBSAD": {
                "name": "Net Balancing Services Adjustment Data",
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 4.0
            },
            "B1770": {
                "name": "Bid-Offer Acceptances",
                "available_from": "2016-01-01", 
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 8.5
            },
            "DISBSAD": {
                "name": "Disaggregated Balancing Services Adjustment Data",
                "available_from": "2016-01-01",
                "frequency": "daily", 
                "estimated_files_per_year": 365,
                "avg_size_mb": 2.3
            },
            "MKTDEPTH": {
                "name": "Market Depth Data",
                "available_from": "2018-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 1.7
            },
            "QAS": {
                "name": "Quiescence Application Status",
                "available_from": "2016-01-01",
                "frequency": "daily", 
                "estimated_files_per_year": 365,
                "avg_size_mb": 3.8
            },
            "FORDAYDEM": {
                "name": "Forecast Day Ahead Demand",
                "available_from": "2016-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 1.1
            },
            "ROLSYSDEM": {
                "name": "Rolling System Demand",
                "available_from": "2016-01-01", 
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 1.4
            },
            "LOLPDRM": {
                "name": "Loss of Load Probability and De-rated Margin",
                "available_from": "2019-01-01",
                "frequency": "daily",
                "estimated_files_per_year": 365,
                "avg_size_mb": 0.7
            },
            "DEVINDOD": {
                "name": "Derived Individual Output Data",
                "available_from": "2017-01-01",
                "frequency": "daily", 
                "estimated_files_per_year": 365,
                "avg_size_mb": 2.9
            }
        }
        
    def get_existing_data_coverage(self) -> Dict[str, Set[str]]:
        """Analyze what data coverage we already have in the bucket"""
        print("🔍 Analyzing existing data coverage in bucket...")
        
        coverage = defaultdict(set)
        
        try:
            # Check bmrs_data folder for historical data
            for blob in self.bucket.list_blobs(prefix="bmrs_data/"):
                blob_name = blob.name
                # Try to extract date from filename (various formats)
                if any(year in blob_name for year in ['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']):
                    # Extract dataset type and date
                    parts = blob_name.split('/')
                    if len(parts) >= 2:
                        filename = parts[-1]
                        # Try to extract date (format: YYYY-MM-DD)
                        import re
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
                        if date_match:
                            file_date = date_match.group(1)
                            # Try to identify dataset type from filename
                            if 'bid_offer' in filename.lower():
                                coverage['B1770'].add(file_date)
                            elif 'fuel' in filename.lower():
                                coverage['FUELINST'].add(file_date)
                            elif 'system' in filename.lower():
                                coverage['SYSWARN'].add(file_date)
                            # Add more pattern matching as needed
            
            # Check datasets folder for recent data
            for blob in self.bucket.list_blobs(prefix="datasets/"):
                parts = blob.name.split('/')
                if len(parts) >= 2:
                    dataset_name = parts[1]
                    if blob.time_created:
                        file_date = blob.time_created.date().strftime('%Y-%m-%d')
                        coverage[dataset_name].add(file_date)
        
        except Exception as e:
            logger.error(f"Error analyzing existing coverage: {e}")
        
        print(f"📊 Found existing data for {len(coverage)} dataset types")
        for dataset, dates in coverage.items():
            print(f"   {dataset}: {len(dates)} dates covered")
        
        return dict(coverage)
    
    def calculate_missing_historical_data(self, existing_coverage: Dict[str, Set[str]]) -> Dict[str, Dict]:
        """Calculate what historical data is missing"""
        print("\n📅 Calculating missing historical data (2016-2025)...")
        
        missing_data = {}
        total_missing_files = 0
        total_missing_size_gb = 0
        
        for dataset_code, dataset_info in self.elexon_datasets.items():
            available_from = datetime.strptime(dataset_info['available_from'], '%Y-%m-%d').date()
            
            # Calculate date range for this dataset
            start_analysis = max(self.start_date, available_from)
            
            # Generate all dates in range
            current_date = start_analysis
            all_dates = set()
            while current_date <= self.end_date:
                all_dates.add(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            # Find missing dates
            existing_dates = existing_coverage.get(dataset_code, set())
            missing_dates = all_dates - existing_dates
            
            if missing_dates:
                years_covered = self.end_date.year - start_analysis.year + 1
                estimated_total_files = len(missing_dates)
                estimated_size_gb = (estimated_total_files * dataset_info['avg_size_mb']) / 1024
                
                missing_data[dataset_code] = {
                    'name': dataset_info['name'],
                    'available_from': dataset_info['available_from'],
                    'missing_dates_count': len(missing_dates),
                    'existing_dates_count': len(existing_dates),
                    'total_possible_dates': len(all_dates),
                    'coverage_percentage': (len(existing_dates) / len(all_dates)) * 100 if all_dates else 0,
                    'estimated_files': estimated_total_files,
                    'estimated_size_gb': round(estimated_size_gb, 2),
                    'years_missing': years_covered,
                    'date_range': f"{start_analysis} to {self.end_date}",
                    'sample_missing_dates': sorted(list(missing_dates))[:10]  # Show first 10
                }
                
                total_missing_files += estimated_total_files
                total_missing_size_gb += estimated_size_gb
        
        # Sort by estimated size (largest first)
        missing_data = dict(sorted(missing_data.items(), 
                                 key=lambda x: x[1]['estimated_size_gb'], 
                                 reverse=True))
        
        print(f"📋 Analysis complete:")
        print(f"   🗃️ Datasets with missing data: {len(missing_data)}")
        print(f"   📄 Total missing files: {total_missing_files:,}")
        print(f"   💾 Total estimated size: {total_missing_size_gb:.1f} GB")
        
        return missing_data
    
    def estimate_download_time(self, missing_data: Dict[str, Dict]) -> Dict[str, float]:
        """Estimate download times for different scenarios"""
        total_size_gb = sum(data['estimated_size_gb'] for data in missing_data.values())
        
        # Various download speed scenarios (GB/hour)
        scenarios = {
            'conservative': 2.0,    # 2 GB/hour (slow API, rate limits)
            'moderate': 5.0,        # 5 GB/hour (normal conditions)
            'optimistic': 10.0,     # 10 GB/hour (fast connection, parallel)
            'ideal': 20.0           # 20 GB/hour (best case scenario)
        }
        
        estimates = {}
        for scenario, speed_gb_per_hour in scenarios.items():
            hours = total_size_gb / speed_gb_per_hour
            estimates[scenario] = {
                'hours': round(hours, 1),
                'days': round(hours / 24, 1),
                'speed_gb_per_hour': speed_gb_per_hour
            }
        
        return estimates
    
    def check_elexon_api_availability(self, sample_datasets: List[str]) -> Dict[str, bool]:
        """Test which datasets are actually available via API"""
        print("\n🌐 Testing Elexon API availability for sample datasets...")
        
        availability = {}
        
        for dataset in sample_datasets[:5]:  # Test first 5 datasets
            try:
                # Test with a recent date
                test_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                url = f"{INSIGHTS_BASE}datasets/{dataset}"
                params = {
                    'format': 'json',
                    'from': test_date,
                    'to': test_date
                }
                
                response = self.session.get(url, params=params, timeout=10)
                availability[dataset] = response.status_code == 200
                
                status = "✅ Available" if availability[dataset] else f"❌ Error {response.status_code}"
                print(f"   {dataset}: {status}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                availability[dataset] = False
                print(f"   {dataset}: ❌ Exception - {e}")
        
        return availability
    
    def generate_historical_data_report(self):
        """Generate comprehensive historical data report"""
        print("🕰️ HISTORICAL ELEXON DATA ANALYSIS (2016-2025)")
        print("=" * 70)
        print(f"📅 Analysis Period: {self.start_date} to {self.end_date}")
        print(f"🗓️ Total Days: {(self.end_date - self.start_date).days:,} days")
        print()
        
        # Step 1: Analyze existing coverage
        existing_coverage = self.get_existing_data_coverage()
        
        # Step 2: Calculate missing data
        missing_data = self.calculate_missing_historical_data(existing_coverage)
        
        if not missing_data:
            print("🎉 Amazing! You have complete historical coverage!")
            return
        
        # Step 3: Test API availability
        api_availability = self.check_elexon_api_availability(list(missing_data.keys()))
        
        # Step 4: Calculate download estimates
        time_estimates = self.estimate_download_time(missing_data)
        
        # Generate detailed report
        print("\n📊 MISSING HISTORICAL DATA SUMMARY")
        print("-" * 50)
        
        for rank, (dataset_code, info) in enumerate(missing_data.items(), 1):
            api_status = "🟢 API Available" if api_availability.get(dataset_code, False) else "🔴 API Issues"
            
            print(f"\n{rank}. {dataset_code} - {info['name']}")
            print(f"   📅 Available from: {info['available_from']}")
            print(f"   📊 Coverage: {info['coverage_percentage']:.1f}% ({info['existing_dates_count']:,}/{info['total_possible_dates']:,} dates)")
            print(f"   📄 Missing files: {info['missing_dates_count']:,}")
            print(f"   💾 Estimated size: {info['estimated_size_gb']:.2f} GB")
            print(f"   🌐 API Status: {api_status}")
            
            if info['sample_missing_dates']:
                print(f"   📝 Sample missing dates: {', '.join(info['sample_missing_dates'][:5])}...")
        
        # Summary statistics
        total_size = sum(info['estimated_size_gb'] for info in missing_data.values())
        total_files = sum(info['missing_dates_count'] for info in missing_data.values())
        
        print(f"\n📈 DOWNLOAD ESTIMATES")
        print("-" * 50)
        print(f"💾 Total missing data: {total_size:.1f} GB ({total_files:,} files)")
        print(f"🔄 Estimated download times:")
        
        for scenario, estimate in time_estimates.items():
            print(f"   {scenario.title()}: {estimate['hours']} hours ({estimate['days']} days) @ {estimate['speed_gb_per_hour']} GB/hour")
        
        print(f"\n🎯 RECOMMENDATIONS")
        print("-" * 50)
        print("1. 🥇 Priority datasets (largest, most valuable):")
        
        # Show top 5 by size
        top_datasets = list(missing_data.items())[:5]
        for dataset_code, info in top_datasets:
            api_note = "✅" if api_availability.get(dataset_code, False) else "⚠️ Check API"
            print(f"   • {dataset_code}: {info['estimated_size_gb']:.1f} GB {api_note}")
        
        print(f"\n2. 📊 Data collection strategy:")
        print(f"   • Start with recent years (2020-2025) for faster value")
        print(f"   • Use parallel downloads where possible")
        print(f"   • Consider monthly chunks to avoid timeouts")
        print(f"   • Monitor API rate limits")
        
        print(f"\n3. 💡 Quick wins (smallest datasets to complete coverage):")
        smallest_datasets = sorted(missing_data.items(), key=lambda x: x[1]['estimated_size_gb'])[:3]
        for dataset_code, info in smallest_datasets:
            print(f"   • {dataset_code}: {info['estimated_size_gb']:.2f} GB ({info['missing_dates_count']:,} files)")
        
        # Save report to cloud
        report_data = {
            'analysis_date': datetime.now().isoformat(),
            'period_analyzed': f"{self.start_date} to {self.end_date}",
            'total_missing_gb': round(total_size, 2),
            'total_missing_files': total_files,
            'missing_datasets': missing_data,
            'api_availability': api_availability,
            'time_estimates': time_estimates
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"analysis/historical_data_analysis_{timestamp}.json"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(report_data, indent=2, default=str), content_type='application/json')
        
        print(f"\n💾 Full analysis saved to: gs://{BUCKET_NAME}/{blob_name}")

def main():
    """Main execution function"""
    discovery = HistoricalDataDiscovery()
    discovery.generate_historical_data_report()

if __name__ == "__main__":
    main()
