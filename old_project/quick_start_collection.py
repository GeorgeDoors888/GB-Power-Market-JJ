#!/usr/bin/env python3
"""
Quick Start Data Collection
Bypasses cloud setup for immediate local collection with organized CSV output
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
from pathlib import Path
import concurrent.futures

# Load environment
load_dotenv('api.env')

def quick_historical_collection():
    """Start collecting historical data immediately"""
    
    api_key = os.getenv('BMRS_API_KEY')
    if not api_key:
        print("❌ Please set BMRS_API_KEY in api.env file")
        return
        
    base_url = "https://data.elexon.co.uk/bmrs/api/v1"
    
    # Create organized directory structure
    base_dir = Path("bmrs_historical_data")
    base_dir.mkdir(exist_ok=True)
    
    data_types = {
        'bid_offer_acceptances': 'balancing/acceptances/all',
        'demand_outturn': 'demand/outturn/all'
    }
    
    for data_type in data_types:
        for year in range(2016, 2026):
            year_dir = base_dir / data_type / str(year)
            year_dir.mkdir(parents=True, exist_ok=True)
    
    def download_day_data(date, data_type, endpoint):
        """Download all data for one day"""
        all_records = []
        
        if data_type == 'bid_offer_acceptances':
            # Need all 48 settlement periods
            for period in range(1, 49):
                try:
                    params = {
                        'apikey': api_key,
                        'settlementDate': date.strftime('%Y-%m-%d'),
                        'settlementPeriod': period
                    }
                    
                    response = requests.get(f"{base_url}/{endpoint}", params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        records = data.get('data', [])
                        all_records.extend(records)
                    
                    time.sleep(0.05)  # Rate limiting
                    
                except Exception as e:
                    print(f"   Error period {period}: {e}")
                    
        else:
            # Single request for other data types
            try:
                params = {
                    'apikey': api_key,
                    'settlementDate': date.strftime('%Y-%m-%d')
                }
                
                response = requests.get(f"{base_url}/{endpoint}", params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    all_records = data.get('data', [])
                    
            except Exception as e:
                print(f"   Error: {e}")
        
        return all_records
    
    def save_csv(date, data_type, records):
        """Save records to organized CSV"""
        if not records:
            return None
            
        try:
            year = date.year
            filename = f"{data_type}_{date.strftime('%Y_%m_%d')}.csv"
            filepath = base_dir / data_type / str(year) / filename
            
            df = pd.DataFrame(records)
            df.to_csv(filepath, index=False)
            
            return filepath, len(records)
            
        except Exception as e:
            print(f"   Save error: {e}")
            return None, 0
    
    # Get user choice for collection period
    print("🚀 QUICK START - BMRS Historical Data Collection")
    print("=" * 60)
    print("\nChoose collection period:")
    print("1. Last week (test)")
    print("2. Last month (test)")
    print("3. Specific year")
    print("4. Full historical (2016-2025)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now() - timedelta(days=1)
    elif choice == "2":
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() - timedelta(days=1)
    elif choice == "3":
        year = int(input("Enter year (2016-2025): "))
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        if year == 2025:
            end_date = datetime.now() - timedelta(days=1)
    elif choice == "4":
        start_date = datetime(2016, 1, 1)
        end_date = datetime.now() - timedelta(days=1)
    else:
        print("Invalid choice")
        return
    
    print(f"\n📅 Collecting: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    total_days = (end_date - start_date).days + 1
    current_date = start_date
    processed_days = 0
    total_files = 0
    total_records = 0
    
    start_time = time.time()
    
    while current_date <= end_date:
        print(f"\n📅 {current_date.strftime('%Y-%m-%d')} ({processed_days+1}/{total_days})")
        
        day_files = 0
        day_records = 0
        
        for data_type, endpoint in data_types.items():
            print(f"   📊 {data_type}...")
            
            records = download_day_data(current_date, data_type, endpoint)
            
            if records:
                result = save_csv(current_date, data_type, records)
                if result:
                    filepath, count = result
                    print(f"      ✅ {filepath.name} ({count} records)")
                    day_files += 1
                    day_records += count
            else:
                print(f"      ⚠️  No data")
        
        total_files += day_files
        total_records += day_records
        
        current_date += timedelta(days=1)
        processed_days += 1
        
        # Progress update
        if processed_days % 5 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / processed_days
            remaining = avg_time * (total_days - processed_days)
            
            print(f"\n📈 Progress: {processed_days}/{total_days} days")
            print(f"   Files created: {total_files}")
            print(f"   Records collected: {total_records:,}")
            print(f"   Estimated remaining: {remaining/60:.1f} minutes")
    
    total_time = time.time() - start_time
    
    print(f"\n🎉 COLLECTION COMPLETED!")
    print(f"   Duration: {total_time/60:.1f} minutes")
    print(f"   Files created: {total_files}")
    print(f"   Total records: {total_records:,}")
    print(f"   Data location: {base_dir}")
    
    # Show directory structure
    print(f"\n📂 Created files structure:")
    for data_type in data_types:
        type_dir = base_dir / data_type
        if type_dir.exists():
            csv_files = list(type_dir.rglob("*.csv"))
            print(f"   {data_type}/: {len(csv_files)} CSV files")

if __name__ == "__main__":
    quick_historical_collection()
