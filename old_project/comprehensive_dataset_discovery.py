#!/usr/bin/env python3
"""
Comprehensive Historical Data Discovery (2016+)
==============================================
Automatically discovers and includes datasets introduced from 2016 onwards,
including those that started in 2018, 2019, 2020, etc.
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta, date
from google.cloud import storage
from typing import Dict, List, Set, Tuple, Optional
import logging
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"
INSIGHTS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/"

class ComprehensiveDatasetDiscovery:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Comprehensive-Dataset-Discovery/1.0'
        })
        
        # Base year for historical analysis
        self.base_year = 2016
        self.current_date = date.today()
        
        # Known datasets with their actual introduction years
        self.dataset_catalog = {
            # 2016 introductions
            "FUELINST": {"introduced": 2016, "priority": "high", "category": "generation"},
            "INDGEN": {"introduced": 2016, "priority": "high", "category": "generation"},
            "NETBSAD": {"introduced": 2016, "priority": "high", "category": "balancing"},
            "PHYBMDATA": {"introduced": 2016, "priority": "high", "category": "market"},
            "NONBM": {"introduced": 2016, "priority": "medium", "category": "generation"},
            "SYSWARN": {"introduced": 2016, "priority": "medium", "category": "system"},
            "MID": {"introduced": 2016, "priority": "high", "category": "market"},
            "B1770": {"introduced": 2016, "priority": "high", "category": "trading"},
            "DISBSAD": {"introduced": 2016, "priority": "medium", "category": "balancing"},
            "QAS": {"introduced": 2016, "priority": "medium", "category": "system"},
            "FORDAYDEM": {"introduced": 2016, "priority": "medium", "category": "demand"},
            "ROLSYSDEM": {"introduced": 2016, "priority": "medium", "category": "demand"},
            "DERSYSDEM": {"introduced": 2016, "priority": "medium", "category": "demand"},
            
            # 2017 introductions
            "TEMP": {"introduced": 2017, "priority": "high", "category": "weather"},
            "DEVINDOD": {"introduced": 2017, "priority": "medium", "category": "generation"},
            
            # 2017 mid-year introductions
            "WINDFOR": {"introduced": 2017, "priority": "high", "category": "renewables", "start_month": 6},
            
            # 2018 introductions
            "MELNGC": {"introduced": 2018, "priority": "medium", "category": "capacity"},
            "MKTDEPTH": {"introduced": 2018, "priority": "medium", "category": "market"},
            "BOD": {"introduced": 2018, "priority": "very_high", "category": "trading"},
            "BOALF": {"introduced": 2018, "priority": "high", "category": "trading"},
            
            # 2019 introductions
            "LOLPDRM": {"introduced": 2019, "priority": "medium", "category": "reliability"},
            
            # 2020+ introductions (to be discovered)
            "CARBINT": {"introduced": 2020, "priority": "high", "category": "environment", "estimated": True},
            "STORAGEDATA": {"introduced": 2021, "priority": "high", "category": "storage", "estimated": True},
            "SOSO": {"introduced": 2022, "priority": "medium", "category": "system", "estimated": True},
        }
        
        # Additional datasets to test (potential discoveries)
        self.test_datasets = [
            # Carbon and environmental
            "CARBON", "CARBINT", "CO2", "EMISSIONS", "GREEN",
            # Storage and batteries
            "STORAGE", "BATTERY", "BESS", "ESS", "STOR",
            # Demand response
            "DR", "DSR", "DEMAND", "FLEX", "FLEXDEM",
            # Interconnectors
            "INTER", "IFIC", "FLOWS", "XBORDER", "IMP", "EXP",
            # New market mechanisms
            "FAST", "FFR", "EFR", "PFR", "DERSTACK", "VPP",
            # Frequency response
            "FREQ", "FREQRESP", "PFR", "SFR", "EFR", "FFR",
            # Capacity market
            "CM", "CAPACITY", "CAPMARKET", "DERATING",
            # Network charging
            "TNT", "TUOS", "DUOS", "RCRC", "BSU",
            # ORDC and new mechanisms
            "ORDC", "SCARCITY", "VLL", "VOLL"
        ]

    def auto_detect_dataset_availability(self, dataset_code: str) -> Dict:
        """Automatically detect when a dataset becomes available"""
        print(f"🔍 Auto-detecting availability for {dataset_code}...")
        
        detection_result = {
            'dataset': dataset_code,
            'available': False,
            'introduction_year': None,
            'introduction_month': None,
            'sample_record_count': 0,
            'api_access_method': None,
            'data_characteristics': {}
        }
        
        # Test current availability first
        try:
            test_date = '2025-08-18'
            url = f"{INSIGHTS_BASE}datasets/{dataset_code}"
            
            # Try single-day access first (works for most datasets)
            params = {'format': 'json', 'from': test_date, 'to': test_date}
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])
                
                detection_result['available'] = True
                detection_result['sample_record_count'] = len(records)
                detection_result['api_access_method'] = 'single_day'
                
                if records:
                    sample = records[0]
                    detection_result['data_characteristics'] = {
                        'fields': list(sample.keys()),
                        'sample_values': {k: str(v)[:50] for k, v in list(sample.items())[:3]}
                    }
                
                # Now try to find introduction date by binary search
                introduction_date = self.find_introduction_date(dataset_code)
                if introduction_date:
                    detection_result['introduction_year'] = introduction_date.year
                    detection_result['introduction_month'] = introduction_date.month
                
                print(f"   ✅ {dataset_code}: Available, {len(records)} records, introduced ~{introduction_date}")
                
            else:
                # Try multi-day access
                params = {
                    'format': 'json', 
                    'from': '2025-08-17', 
                    'to': '2025-08-18'
                }
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    detection_result['available'] = True
                    detection_result['api_access_method'] = 'multi_day'
                    print(f"   ✅ {dataset_code}: Available via multi-day access")
                else:
                    print(f"   ❌ {dataset_code}: Not available (HTTP {response.status_code})")
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ {dataset_code}: Error - {e}")
        
        return detection_result

    def find_introduction_date(self, dataset_code: str) -> Optional[date]:
        """Binary search to find when a dataset was first introduced"""
        try:
            start_date = date(2016, 1, 1)
            end_date = date.today()
            
            # Binary search for introduction date
            while (end_date - start_date).days > 32:  # Stop when within a month
                mid_date = start_date + (end_date - start_date) // 2
                
                url = f"{INSIGHTS_BASE}datasets/{dataset_code}"
                params = {
                    'format': 'json',
                    'from': mid_date.strftime('%Y-%m-%d'),
                    'to': mid_date.strftime('%Y-%m-%d')
                }
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        end_date = mid_date  # Data exists, look earlier
                    else:
                        start_date = mid_date  # No data, look later
                else:
                    start_date = mid_date  # API error, assume no data, look later
                
                time.sleep(0.3)  # Rate limiting for binary search
            
            return start_date
            
        except Exception as e:
            print(f"   ⚠️ Could not determine introduction date for {dataset_code}: {e}")
            return None

    def discover_new_datasets(self) -> List[Dict]:
        """Discover potentially new datasets not in our catalog"""
        print("\n🔬 DISCOVERING NEW DATASETS...")
        print("Testing potential dataset names...")
        
        discovered_datasets = []
        
        for test_name in self.test_datasets:
            result = self.auto_detect_dataset_availability(test_name)
            if result['available']:
                discovered_datasets.append(result)
                
                # Add to our catalog for future use
                introduction_year = result.get('introduction_year', 2020)
                self.dataset_catalog[test_name] = {
                    'introduced': introduction_year,
                    'priority': 'unknown',
                    'category': 'discovered',
                    'discovered_now': True
                }
        
        return discovered_datasets

    def build_comprehensive_dataset_list(self) -> Dict[str, Dict]:
        """Build comprehensive list including all datasets from 2016+"""
        print("\n📊 BUILDING COMPREHENSIVE DATASET LIST...")
        
        comprehensive_list = {}
        
        # Include all known datasets from 2016+
        for dataset_code, info in self.dataset_catalog.items():
            if info['introduced'] >= self.base_year:
                # Calculate date range
                start_year = info['introduced']
                start_month = info.get('start_month', 1)
                start_date = date(start_year, start_month, 1)
                
                # Calculate missing data size estimate
                days_available = (self.current_date - start_date).days
                
                # Estimate size based on category and priority
                size_estimates = {
                    'very_high': 0.5,  # MB per day
                    'high': 0.3,
                    'medium': 0.1,
                    'low': 0.05
                }
                
                daily_size_mb = size_estimates.get(info['priority'], 0.1)
                estimated_size_gb = (days_available * daily_size_mb) / 1024
                
                comprehensive_list[dataset_code] = {
                    'name': dataset_code,
                    'introduced_year': start_year,
                    'start_date': start_date,
                    'days_available': days_available,
                    'estimated_size_gb': round(estimated_size_gb, 2),
                    'priority': info['priority'],
                    'category': info['category'],
                    'estimated': info.get('estimated', False),
                    'discovered_now': info.get('discovered_now', False)
                }
        
        # Test availability for all datasets
        print("🧪 Testing availability for all datasets...")
        available_datasets = {}
        
        for dataset_code, info in comprehensive_list.items():
            detection = self.auto_detect_dataset_availability(dataset_code)
            
            if detection['available']:
                info.update({
                    'api_available': True,
                    'api_method': detection['api_access_method'],
                    'sample_records': detection['sample_record_count'],
                    'actual_introduction_year': detection.get('introduction_year'),
                    'data_fields': detection['data_characteristics'].get('fields', [])
                })
                available_datasets[dataset_code] = info
            else:
                info['api_available'] = False
        
        return available_datasets

    def calculate_total_opportunity(self, available_datasets: Dict) -> Dict:
        """Calculate total data opportunity"""
        total_stats = {
            'total_datasets': len(available_datasets),
            'total_size_gb': 0,
            'by_year': defaultdict(lambda: {'count': 0, 'size_gb': 0}),
            'by_category': defaultdict(lambda: {'count': 0, 'size_gb': 0}),
            'by_priority': defaultdict(lambda: {'count': 0, 'size_gb': 0}),
            'high_value_datasets': [],
            'new_discoveries': []
        }
        
        for dataset_code, info in available_datasets.items():
            year = info['introduced_year']
            category = info['category']
            priority = info['priority']
            size_gb = info['estimated_size_gb']
            
            total_stats['total_size_gb'] += size_gb
            total_stats['by_year'][year]['count'] += 1
            total_stats['by_year'][year]['size_gb'] += size_gb
            total_stats['by_category'][category]['count'] += 1
            total_stats['by_category'][category]['size_gb'] += size_gb
            total_stats['by_priority'][priority]['count'] += 1
            total_stats['by_priority'][priority]['size_gb'] += size_gb
            
            if priority in ['very_high', 'high']:
                total_stats['high_value_datasets'].append((dataset_code, info))
            
            if info.get('discovered_now'):
                total_stats['new_discoveries'].append((dataset_code, info))
        
        return total_stats

    def generate_comprehensive_report(self):
        """Generate comprehensive historical data report"""
        print("🎯 COMPREHENSIVE HISTORICAL DATA DISCOVERY (2016+)")
        print("=" * 70)
        
        # Discover new datasets
        new_datasets = self.discover_new_datasets()
        
        # Build comprehensive list
        available_datasets = self.build_comprehensive_dataset_list()
        
        # Calculate opportunity
        stats = self.calculate_total_opportunity(available_datasets)
        
        print(f"\n📊 DISCOVERY RESULTS:")
        print(f"✅ Available datasets: {stats['total_datasets']}")
        print(f"💾 Total estimated size: {stats['total_size_gb']:.1f} GB")
        print(f"🆕 New discoveries: {len(stats['new_discoveries'])}")
        
        print(f"\n📅 DATASETS BY INTRODUCTION YEAR:")
        for year in sorted(stats['by_year'].keys()):
            year_data = stats['by_year'][year]
            print(f"   {year}: {year_data['count']} datasets, {year_data['size_gb']:.1f} GB")
        
        print(f"\n🏷️ DATASETS BY CATEGORY:")
        for category in sorted(stats['by_category'].keys()):
            cat_data = stats['by_category'][category]
            print(f"   {category}: {cat_data['count']} datasets, {cat_data['size_gb']:.1f} GB")
        
        print(f"\n⭐ HIGH-VALUE DATASETS (Priority: High/Very High):")
        high_value = sorted(stats['high_value_datasets'], key=lambda x: x[1]['estimated_size_gb'], reverse=True)
        for dataset_code, info in high_value[:10]:  # Top 10
            print(f"   {dataset_code}: {info['estimated_size_gb']:.1f} GB ({info['introduced_year']}, {info['category']})")
        
        if stats['new_discoveries']:
            print(f"\n🎉 NEW DATASETS DISCOVERED:")
            for dataset_code, info in stats['new_discoveries']:
                print(f"   {dataset_code}: {info['category']} dataset, ~{info['estimated_size_gb']:.1f} GB")
        
        print(f"\n🎯 RECOMMENDED DOWNLOAD ORDER:")
        print("Based on value, size, and API availability:")
        
        # Sort by priority and size
        priority_order = {'very_high': 4, 'high': 3, 'medium': 2, 'low': 1, 'unknown': 0}
        sorted_datasets = sorted(
            available_datasets.items(),
            key=lambda x: (priority_order.get(x[1]['priority'], 0), x[1]['estimated_size_gb']),
            reverse=True
        )
        
        for i, (dataset_code, info) in enumerate(sorted_datasets[:15], 1):
            api_status = "✅" if info.get('api_available') else "❌"
            print(f"   {i:2d}. {dataset_code}: {info['estimated_size_gb']:.1f} GB ({info['introduced_year']}) {api_status}")
        
        # Save comprehensive report
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'base_year': self.base_year,
            'total_datasets_found': stats['total_datasets'],
            'total_estimated_size_gb': round(stats['total_size_gb'], 2),
            'available_datasets': available_datasets,
            'statistics': dict(stats),
            'new_discoveries': [d[0] for d in stats['new_discoveries']]
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"comprehensive_analysis/dataset_discovery_{timestamp}.json"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(report_data, indent=2, default=str), content_type='application/json')
        
        print(f"\n💾 Comprehensive report saved to: gs://{BUCKET_NAME}/{blob_name}")
        
        return available_datasets, stats

def main():
    """Main execution function"""
    discovery = ComprehensiveDatasetDiscovery()
    available_datasets, stats = discovery.generate_comprehensive_report()
    
    print(f"\n🚀 READY TO DOWNLOAD:")
    print(f"   📊 {stats['total_datasets']} datasets available")
    print(f"   💾 {stats['total_size_gb']:.1f} GB total opportunity")
    print(f"   🎯 Focus on high-priority datasets first")

if __name__ == "__main__":
    main()
