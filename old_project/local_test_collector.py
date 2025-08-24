#!/usr/bin/env python3
"""
Local Test Version - BMRS Data Collection with CSV Organization
Tests the complete workflow before cloud deployment
"""

import os
import csv
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
from pathlib import Path
import concurrent.futures
import threading

# Load environment variables
load_dotenv('api.env')

class LocalBMRSCollector:
    def __init__(self):
        self.api_key = os.getenv('BMRS_API_KEY')
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Data type configurations
        self.data_types = {
            'bid_offer_acceptances': {
                'endpoint': 'balancing/acceptances/all',
                'folder': 'bid_offer_acceptances',
                'needs_periods': True,
                'description': 'Bid-Offer Acceptance Data'
            },
            'demand_outturn': {
                'endpoint': 'demand/outturn/all',
                'folder': 'demand_outturn',
                'needs_periods': False,
                'description': 'Demand Outturn Data'
            },
            'generation_outturn': {
                'endpoint': 'generation/outturn/all',
                'folder': 'generation_outturn',
                'needs_periods': False,
                'description': 'Generation Outturn Data'
            },
            'system_warnings': {
                'endpoint': 'datasets/SYSWARN',
                'folder': 'system_warnings',
                'needs_periods': False,
                'description': 'System Warnings Data'
            }
        }
        
        # Create local directory structure
        self.setup_local_directories()
        
    def setup_local_directories(self):
        """Create organized directory structure"""
        base_dir = Path("bmrs_data")
        base_dir.mkdir(exist_ok=True)
        
        print("📁 Creating directory structure...")
        for data_type, config in self.data_types.items():
            folder_path = base_dir / config['folder']
            folder_path.mkdir(exist_ok=True)
            
            # Create year subdirectories
            for year in range(2016, 2026):
                year_path = folder_path / str(year)
                year_path.mkdir(exist_ok=True)
                
                # Create month subdirectories
                for month in range(1, 13):
                    month_path = year_path / f"{month:02d}"
                    month_path.mkdir(exist_ok=True)
                    
        print("✅ Directory structure created")
        
    def download_data_for_date(self, data_type, date, settlement_period=None):
        """Download data for specific date and period"""
        try:
            config = self.data_types[data_type]
            endpoint = config['endpoint']
            
            params = {
                'apikey': self.api_key,
                'settlementDate': date.strftime('%Y-%m-%d')
            }
            
            if settlement_period:
                params['settlementPeriod'] = settlement_period
                
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])
                return records
            else:
                print(f"⚠️  {data_type} - {date.strftime('%Y-%m-%d')}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error downloading {data_type} for {date}: {e}")
            return []
            
    def save_to_csv(self, data_type, date, records):
        """Save records to organized CSV structure"""
        if not records:
            return None
            
        try:
            config = self.data_types[data_type]
            year = date.year
            month = date.month
            
            # Create filename with date
            filename = f"{data_type}_{date.strftime('%Y_%m_%d')}.csv"
            filepath = Path("bmrs_data") / config['folder'] / str(year) / f"{month:02d}" / filename
            
            # Convert to DataFrame and save
            df = pd.DataFrame(records)
            df.to_csv(filepath, index=False)
            
            file_size = filepath.stat().st_size / 1024  # KB
            print(f"💾 Saved: {filepath} ({len(records)} records, {file_size:.1f} KB)")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving CSV for {data_type}: {e}")
            return None
            
    def collect_single_day(self, date, data_types=None):
        """Collect all data types for a single day"""
        if data_types is None:
            data_types = list(self.data_types.keys())
            
        print(f"\n📅 Collecting data for {date.strftime('%Y-%m-%d')}")
        day_results = {}
        total_records = 0
        
        for data_type in data_types:
            config = self.data_types[data_type]
            print(f"   📊 {config['description']}...")
            
            if config['needs_periods']:
                # Collect all settlement periods for bid-offer acceptances
                all_records = []
                
                # Use threading for settlement periods
                def fetch_period(period):
                    return self.download_data_for_date(data_type, date, period)
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    period_futures = [executor.submit(fetch_period, p) for p in range(1, 49)]
                    
                    for future in concurrent.futures.as_completed(period_futures):
                        try:
                            records = future.result()
                            all_records.extend(records)
                        except Exception as e:
                            print(f"      ⚠️  Period failed: {e}")
                        time.sleep(0.02)  # Small delay
                        
                day_results[data_type] = all_records
                total_records += len(all_records)
                
            else:
                # Single request for other data types
                records = self.download_data_for_date(data_type, date)
                day_results[data_type] = records
                total_records += len(records)
                
            time.sleep(0.1)  # Rate limiting between data types
            
        print(f"✅ Day complete: {total_records} total records")
        return day_results
        
    def save_day_results(self, date, day_results):
        """Save all day results to CSV files"""
        saved_files = []
        
        for data_type, records in day_results.items():
            if records:
                filepath = self.save_to_csv(data_type, date, records)
                if filepath:
                    saved_files.append(filepath)
                    
        return saved_files
        
    def test_collection(self, test_days=3):
        """Test collection with recent dates"""
        print("🧪 STARTING TEST COLLECTION")
        print("=" * 50)
        
        # Test with last few days
        end_date = datetime.now() - timedelta(days=1)
        test_dates = [end_date - timedelta(days=i) for i in range(test_days)]
        
        all_files = []
        start_time = time.time()
        
        for date in test_dates:
            day_results = self.collect_single_day(date)
            saved_files = self.save_day_results(date, day_results)
            all_files.extend(saved_files)
            
        total_time = time.time() - start_time
        
        print(f"\n🎉 TEST COMPLETED!")
        print(f"   Duration: {total_time:.1f} seconds")
        print(f"   Files created: {len(all_files)}")
        print(f"   Average: {total_time/test_days:.1f} seconds per day")
        
        # Show sample files
        print(f"\n📂 Sample files created:")
        for filepath in all_files[:5]:
            print(f"   {filepath}")
            
        return all_files
        
    def collect_historical_range(self, start_date, end_date, data_types=None):
        """Collect historical data for date range"""
        print(f"🚀 HISTORICAL COLLECTION")
        print(f"📅 Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        processed_days = 0
        all_files = []
        
        start_time = time.time()
        
        while current_date <= end_date:
            day_results = self.collect_single_day(current_date, data_types)
            saved_files = self.save_day_results(current_date, day_results)
            all_files.extend(saved_files)
            
            current_date += timedelta(days=1)
            processed_days += 1
            
            # Progress update every 10 days
            if processed_days % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / processed_days
                remaining_time = avg_time * (total_days - processed_days)
                
                print(f"\n📈 Progress: {processed_days}/{total_days} days")
                print(f"   Elapsed: {elapsed/60:.1f} minutes")
                print(f"   Estimated remaining: {remaining_time/60:.1f} minutes")
                print(f"   Files created: {len(all_files)}")
                
        total_time = time.time() - start_time
        
        print(f"\n🎉 COLLECTION COMPLETED!")
        print(f"   Total time: {total_time/60:.1f} minutes")
        print(f"   Files created: {len(all_files)}")
        print(f"   Average: {total_time/total_days:.1f} seconds per day")
        
        return all_files

def main():
    """Main execution"""
    collector = LocalBMRSCollector()
    
    print("🌟 BMRS Data Collection System - Local Test")
    print("=" * 60)
    
    # Test with recent days first
    test_files = collector.test_collection(test_days=2)
    
    if test_files:
        print(f"\n✅ Test successful! Ready for historical collection.")
        
        # Ask user for next step
        print(f"\nNext options:")
        print(f"1. Collect specific month (fast test)")
        print(f"2. Collect specific year")
        print(f"3. Collect full historical data (2016-2025)")
        
        choice = input(f"\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            # Collect January 2024 as test
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)
            collector.collect_historical_range(start_date, end_date)
            
        elif choice == "2":
            year = int(input("Enter year (2016-2025): "))
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            if year == 2025:
                end_date = datetime.now() - timedelta(days=1)
            collector.collect_historical_range(start_date, end_date)
            
        elif choice == "3":
            # Full historical collection
            start_date = datetime(2016, 1, 1)
            end_date = datetime.now() - timedelta(days=1)
            collector.collect_historical_range(start_date, end_date)
            
    else:
        print("❌ Test failed. Please check API key and connection.")

if __name__ == "__main__":
    main()
