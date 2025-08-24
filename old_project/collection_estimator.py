#!/usr/bin/env python3
"""
Time and Cost Estimation Calculator for BMRS Historical Data Collection
"""

from datetime import datetime, timedelta
import math

class BMRSCollectionEstimator:
    def __init__(self):
        # Performance metrics from our testing
        self.single_request_time = 0.15  # seconds (average from test results)
        self.rate_limit_delay = 0.1      # seconds between requests
        self.requests_per_day = {
            'bid_offer_acceptances': 48,  # 48 settlement periods
            'demand_outturn': 1,          # 1 request per day
            'generation_outturn': 1,      # 1 request per day  
            'system_warnings': 1,         # 1 request per day
        }
        
        # Data volume estimates (from test results)
        self.avg_records_per_request = {
            'bid_offer_acceptances': 250,  # Average per settlement period
            'demand_outturn': 48,          # 48 settlement periods worth
            'generation_outturn': 48,      # 48 settlement periods worth
            'system_warnings': 10,         # Sporadic warnings
        }
        
        # Google Cloud costs (estimated)
        self.cloud_run_cost_per_hour = 0.024  # $0.024/hour for 1 vCPU, 1GB RAM
        self.storage_cost_per_gb_month = 0.020 # $0.020/GB/month
        
    def calculate_collection_time(self, start_date, end_date, data_types=None, use_parallel=True):
        """Calculate estimated collection time"""
        if data_types is None:
            data_types = list(self.requests_per_day.keys())
            
        total_days = (end_date - start_date).days + 1
        
        # Calculate total requests
        total_requests = 0
        for data_type in data_types:
            daily_requests = self.requests_per_day[data_type]
            total_requests += daily_requests * total_days
            
        # Calculate time based on approach
        if use_parallel:
            # Async parallel processing (4-8 concurrent requests)
            parallel_factor = 6  # Conservative estimate
            request_time = (self.single_request_time + self.rate_limit_delay) / parallel_factor
            upload_overhead = 0.1  # seconds per request for upload
            total_time_seconds = total_requests * (request_time + upload_overhead)
        else:
            # Sequential processing
            total_time_seconds = total_requests * (self.single_request_time + self.rate_limit_delay)
            
        return {
            'total_days': total_days,
            'total_requests': total_requests,
            'total_time_seconds': total_time_seconds,
            'total_time_hours': total_time_seconds / 3600,
            'total_time_readable': self.format_duration(total_time_seconds),
            'requests_per_day': sum(self.requests_per_day[dt] for dt in data_types),
            'parallel_mode': use_parallel
        }
        
    def calculate_data_volume(self, start_date, end_date, data_types=None):
        """Calculate estimated data volume"""
        if data_types is None:
            data_types = list(self.requests_per_day.keys())
            
        total_days = (end_date - start_date).days + 1
        total_records = 0
        
        for data_type in data_types:
            daily_requests = self.requests_per_day[data_type]
            records_per_request = self.avg_records_per_request[data_type]
            data_type_records = daily_requests * records_per_request * total_days
            total_records += data_type_records
            
        # Estimate storage size (rough calculation)
        # Average CSV row ~ 200 bytes, with headers and formatting ~ 250 bytes
        estimated_size_bytes = total_records * 250
        estimated_size_gb = estimated_size_bytes / (1024**3)
        
        return {
            'total_records': total_records,
            'estimated_size_bytes': estimated_size_bytes,
            'estimated_size_gb': estimated_size_gb,
            'files_created': total_days * len(data_types)
        }
        
    def calculate_cloud_costs(self, collection_hours, storage_gb):
        """Calculate Google Cloud costs"""
        # Cloud Run costs (compute)
        compute_cost = collection_hours * self.cloud_run_cost_per_hour
        
        # Storage costs (per month)
        monthly_storage_cost = storage_gb * self.storage_cost_per_gb_month
        
        # Additional services (rough estimates)
        network_cost = storage_gb * 0.01  # Data transfer
        api_cost = 0.50  # Minimal for Drive API calls
        
        total_setup_cost = compute_cost + network_cost + api_cost
        
        return {
            'compute_cost': compute_cost,
            'monthly_storage_cost': monthly_storage_cost,
            'network_cost': network_cost,
            'api_cost': api_cost,
            'total_setup_cost': total_setup_cost,
            'monthly_ongoing_cost': monthly_storage_cost
        }
        
    def format_duration(self, seconds):
        """Convert seconds to readable duration"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
        else:
            days = seconds / 86400
            return f"{days:.1f} days"
            
    def generate_full_estimate(self, start_date, end_date, data_types=None):
        """Generate comprehensive estimate"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
        time_estimate = self.calculate_collection_time(start_date, end_date, data_types)
        data_estimate = self.calculate_data_volume(start_date, end_date, data_types)
        cost_estimate = self.calculate_cloud_costs(
            time_estimate['total_time_hours'], 
            data_estimate['estimated_size_gb']
        )
        
        return {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_days': time_estimate['total_days'],
                'data_types': data_types or list(self.requests_per_day.keys())
            },
            'time_estimate': time_estimate,
            'data_estimate': data_estimate,
            'cost_estimate': cost_estimate,
            'summary': {
                'collection_time': time_estimate['total_time_readable'],
                'total_files': data_estimate['files_created'],
                'total_records': f"{data_estimate['total_records']:,}",
                'storage_size': f"{data_estimate['estimated_size_gb']:.2f} GB",
                'setup_cost': f"${cost_estimate['total_setup_cost']:.2f}",
                'monthly_cost': f"${cost_estimate['monthly_ongoing_cost']:.2f}"
            }
        }

def main():
    """Generate estimates for the requested collection"""
    estimator = BMRSCollectionEstimator()
    
    print("🧮 BMRS Historical Data Collection Estimates")
    print("=" * 60)
    
    # Full historical collection (2016-01-01 to today)
    start_date = datetime(2016, 1, 1)
    end_date = datetime.now() - timedelta(days=1)
    
    full_estimate = estimator.generate_full_estimate(start_date, end_date)
    
    print(f"\n📅 FULL HISTORICAL COLLECTION")
    print(f"   Period: {full_estimate['period']['start_date']} to {full_estimate['period']['end_date']}")
    print(f"   Duration: {full_estimate['period']['total_days']} days")
    print(f"   Data types: {len(full_estimate['period']['data_types'])}")
    
    print(f"\n⏱️  TIME ESTIMATE:")
    print(f"   Total requests: {full_estimate['time_estimate']['total_requests']:,}")
    print(f"   Collection time: {full_estimate['summary']['collection_time']}")
    print(f"   Parallel processing: {full_estimate['time_estimate']['parallel_mode']}")
    
    print(f"\n📊 DATA VOLUME:")
    print(f"   Total records: {full_estimate['summary']['total_records']}")
    print(f"   Total files: {full_estimate['summary']['total_files']}")
    print(f"   Storage size: {full_estimate['summary']['storage_size']}")
    
    print(f"\n💰 COST ESTIMATE:")
    print(f"   Setup cost: {full_estimate['summary']['setup_cost']}")
    print(f"   Monthly storage: {full_estimate['summary']['monthly_cost']}")
    
    # Year-by-year breakdown
    print(f"\n📈 YEAR-BY-YEAR BREAKDOWN:")
    print("-" * 40)
    for year in range(2016, 2026):
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31)
        if year == 2025:
            year_end = datetime.now() - timedelta(days=1)
            
        year_estimate = estimator.generate_full_estimate(year_start, year_end)
        
        print(f"{year}: {year_estimate['summary']['collection_time']:>12} | "
              f"{year_estimate['summary']['total_records']:>10} records | "
              f"{year_estimate['summary']['storage_size']:>8}")
    
    # Google Cloud setup estimate
    print(f"\n☁️  GOOGLE CLOUD SETUP TIME:")
    print(f"   Project setup: 15-30 minutes")
    print(f"   API configuration: 10-15 minutes") 
    print(f"   Service deployment: 5-10 minutes")
    print(f"   Testing & validation: 10-15 minutes")
    print(f"   TOTAL SETUP TIME: 40-70 minutes")

if __name__ == "__main__":
    main()
