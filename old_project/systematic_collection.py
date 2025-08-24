#!/usr/bin/env python3
"""
Systematic Multi-Year BMRS Data Collection
Collects all data types year by year with progress tracking
"""
import subprocess
import time
import sys
import os
from datetime import datetime

def run_year_collection(year, data_types=['bid_offer_acceptances', 'generation_outturn', 'demand_outturn']):
    """Run collection for a full year"""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31" if year < 2025 else "2025-08-08"
    
    print(f"\n🚀 COLLECTING YEAR {year}: {start_date} to {end_date}")
    print(f"📊 Data types: {', '.join(data_types)}")
    
    # Set environment
    env = os.environ.copy()
    env.pop('GOOGLE_APPLICATION_CREDENTIALS', None)
    env['BMRS_BUCKET'] = 'jibber-jabber-knowledge-bmrs-data'
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            'python3', 'fast_cloud_backfill.py',
            start_date, end_date,
            '--workers', '12',
            '--http-port', f'{8090 + year - 2016}',  # Unique port per year
            '--summary-every', '5',
            '--summary-min-tasks', '200'
        ], env=env, capture_output=True, text=True, timeout=3600)  # 1 hour timeout per year
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Year {year} completed in {duration/60:.1f} minutes")
            # Extract stats from output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Done:' in line and 'Failed:' in line:
                    print(f"   {line}")
                elif 'Records:' in line:
                    print(f"   {line}")
            return True
        else:
            print(f"❌ Year {year} failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Year {year} timed out after 1 hour")
        return False
    except Exception as e:
        print(f"❌ Year {year} error: {e}")
        return False

def main():
    print("🚀 SYSTEMATIC MULTI-YEAR BMRS DATA COLLECTION")
    print("=" * 60)
    print(f"Start time: {datetime.now()}")
    
    # Years to collect (oldest to newest for better progress visibility)
    years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    
    successful_years = []
    failed_years = []
    
    for year in years:
        success = run_year_collection(year)
        if success:
            successful_years.append(year)
        else:
            failed_years.append(year)
        
        # Short pause between years
        if year < years[-1]:
            print("⏱️  Pausing 10 seconds before next year...")
            time.sleep(10)
    
    print(f"\n🏁 COLLECTION COMPLETE")
    print(f"✅ Successful years: {successful_years}")
    if failed_years:
        print(f"❌ Failed years: {failed_years}")
    print(f"End time: {datetime.now()}")
    
    # Generate final summary
    print("\n📊 Generating final collection summary...")
    subprocess.run(['python3', 'generate_collection_summary.py'], check=False)

if __name__ == '__main__':
    main()
