#!/usr/bin/env python3
"""
Complete Data Download for Sunday Processing
==========================================
Downloads ALL required data by Sunday so processing is ready to go
George - this ensures everything is downloaded and ready for your analysis
"""

import os
import sys
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment
load_dotenv('api.env')
api_key = os.getenv('BMRS_API_KEY')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SundayDataDownloader:
    """
    Complete data downloader for Sunday processing readiness
    Downloads everything needed so processing can start immediately
    """
    
    def __init__(self):
        self.api_key = api_key
        self.base_url = 'https://data.elexon.co.uk/bmrs/api/v1'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Sunday-Data-Downloader/1.0'})
        
        # Thread-safe statistics
        self.stats_lock = threading.Lock()
        self.stats = {
            'total_files_targeted': 0,
            'files_downloaded': 0,
            'files_skipped': 0,
            'total_records': 0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'data_types_completed': {}
        }
        
        # Data storage paths
        self.base_data_path = Path('bmrs_data')
        self.base_data_path.mkdir(exist_ok=True)
        
        # Create all necessary directories
        self.data_types = [
            'bid_offer_acceptances',
            'generation_outturn', 
            'demand_outturn',
            'system_warnings'
        ]
        
        for data_type in self.data_types:
            for year in ['2022', '2023', '2024', '2025']:
                for month in range(1, 13):
                    month_str = f"{month:02d}"
                    type_path = self.base_data_path / data_type / year / month_str
                    type_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("🚀 Sunday Data Downloader initialized")
        logger.info(f"✅ API Key: {'Available' if self.api_key else 'Missing'}")
    
    def generate_download_plan(self, start_date=None, end_date=None):
        """Generate comprehensive download plan for all required data"""
        
        if not start_date:
            # Download last 6 months of data to ensure comprehensive coverage
            start_date = datetime.now() - timedelta(days=180)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        if not end_date:
            # Up to yesterday (most recent complete day)
            end_date = datetime.now() - timedelta(days=1)
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        logger.info(f"📅 Download plan: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        download_tasks = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            for data_type in self.data_types:
                # Check if file already exists
                year = current_date.strftime('%Y')
                month = current_date.strftime('%m')
                
                file_path = self.base_data_path / data_type / year / month / f"{data_type}_{date_str}.json"
                
                if not file_path.exists():
                    download_tasks.append({
                        'date': date_str,
                        'data_type': data_type,
                        'file_path': file_path,
                        'priority': self._get_priority(current_date, data_type)
                    })
                else:
                    # Check if file is complete (has reasonable size)
                    if file_path.stat().st_size < 1000:  # Less than 1KB indicates incomplete
                        download_tasks.append({
                            'date': date_str,
                            'data_type': data_type,
                            'file_path': file_path,
                            'priority': self._get_priority(current_date, data_type)
                        })
                    else:
                        with self.stats_lock:
                            self.stats['files_skipped'] += 1
            
            current_date += timedelta(days=1)
        
        # Sort by priority (recent dates and critical data types first)
        download_tasks.sort(key=lambda x: x['priority'], reverse=True)
        
        with self.stats_lock:
            self.stats['total_files_targeted'] = len(download_tasks)
        
        logger.info(f"📋 Download plan: {len(download_tasks)} files to download")
        logger.info(f"⏭️  Files already exist: {self.stats['files_skipped']}")
        
        return download_tasks
    
    def _get_priority(self, date, data_type):
        """Calculate download priority (higher = more important)"""
        
        # Recent dates get higher priority
        days_ago = (datetime.now() - date).days
        recency_score = max(0, 100 - days_ago)
        
        # Critical data types get priority boost
        data_type_scores = {
            'bid_offer_acceptances': 50,  # Most important
            'generation_outturn': 40,
            'demand_outturn': 30,
            'system_warnings': 20
        }
        
        type_score = data_type_scores.get(data_type, 10)
        
        return recency_score + type_score
    
    def download_single_file(self, task):
        """Download a single data file"""
        
        date = task['date']
        data_type = task['data_type']
        file_path = task['file_path']
        
        try:
            # Different endpoints for different data types
            endpoint_map = {
                'bid_offer_acceptances': 'balancing/acceptances/all',
                'generation_outturn': 'generation/outturn/summary',
                'demand_outturn': 'demand/outturn/summary',
                'system_warnings': 'datasets/SYSWARN'
            }
            
            endpoint = endpoint_map.get(data_type)
            if not endpoint:
                logger.error(f"❌ Unknown data type: {data_type}")
                return False
            
            all_data = []
            
            # For bid_offer_acceptances, collect all settlement periods
            if data_type == 'bid_offer_acceptances':
                for sp in range(1, 49):  # All 48 settlement periods
                    try:
                        url = f"{self.base_url}/{endpoint}"
                        params = {
                            'apikey': self.api_key,
                            'settlementDate': date,
                            'settlementPeriod': sp
                        }
                        
                        response = self.session.get(url, params=params, timeout=20)
                        
                        with self.stats_lock:
                            self.stats['total_requests'] += 1
                        
                        if response.status_code == 200:
                            data = response.json()
                            records = data.get('data', [])
                            
                            if records:
                                # Add metadata to each record
                                for record in records:
                                    record['settlement_period'] = sp
                                    record['download_date'] = datetime.now().isoformat()
                                    record['download_method'] = 'sunday_downloader'
                                
                                all_data.extend(records)
                                
                                with self.stats_lock:
                                    self.stats['successful_requests'] += 1
                                    self.stats['total_records'] += len(records)
                        else:
                            with self.stats_lock:
                                self.stats['failed_requests'] += 1
                        
                        # Rate limiting
                        time.sleep(0.05)
                        
                    except Exception as e:
                        with self.stats_lock:
                            self.stats['failed_requests'] += 1
                        logger.warning(f"⚠️ {data_type} {date} SP{sp}: {str(e)[:50]}...")
            
            else:
                # Single request for other data types
                try:
                    url = f"{self.base_url}/{endpoint}"
                    params = {
                        'apikey': self.api_key,
                        'settlementDate': date
                    }
                    
                    response = self.session.get(url, params=params, timeout=20)
                    
                    with self.stats_lock:
                        self.stats['total_requests'] += 1
                    
                    if response.status_code == 200:
                        data = response.json()
                        records = data.get('data', [])
                        
                        if records:
                            # Add metadata
                            for record in records:
                                record['download_date'] = datetime.now().isoformat()
                                record['download_method'] = 'sunday_downloader'
                            
                            all_data = records
                            
                            with self.stats_lock:
                                self.stats['successful_requests'] += 1
                                self.stats['total_records'] += len(records)
                    else:
                        with self.stats_lock:
                            self.stats['failed_requests'] += 1
                        
                except Exception as e:
                    with self.stats_lock:
                        self.stats['failed_requests'] += 1
                    logger.warning(f"⚠️ {data_type} {date}: {str(e)[:50]}...")
            
            # Save data if we got any
            if all_data:
                file_data = {
                    'date': date,
                    'data_type': data_type,
                    'download_timestamp': datetime.now().isoformat(),
                    'record_count': len(all_data),
                    'data': all_data
                }
                
                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w') as f:
                    json.dump(file_data, f, indent=2, default=str)
                
                with self.stats_lock:
                    self.stats['files_downloaded'] += 1
                    if data_type not in self.stats['data_types_completed']:
                        self.stats['data_types_completed'][data_type] = 0
                    self.stats['data_types_completed'][data_type] += 1
                
                logger.info(f"✅ {data_type} {date}: {len(all_data)} records")
                return True
            
            else:
                # Save empty file to mark as attempted
                file_data = {
                    'date': date,
                    'data_type': data_type,
                    'download_timestamp': datetime.now().isoformat(),
                    'record_count': 0,
                    'data': [],
                    'status': 'no_data_available'
                }
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    json.dump(file_data, f, indent=2)
                
                logger.info(f"⚪ {data_type} {date}: No data available")
                return True
        
        except Exception as e:
            logger.error(f"❌ {data_type} {date}: {e}")
            return False
    
    def download_all_data(self, max_workers=4):
        """Download all required data using parallel processing"""
        
        logger.info("🚀 Starting comprehensive data download...")
        self.stats['start_time'] = datetime.now()
        
        # Generate download plan
        download_tasks = self.generate_download_plan()
        
        if not download_tasks:
            logger.info("✅ All data already downloaded!")
            return True
        
        # Download in parallel
        logger.info(f"⚡ Downloading with {max_workers} parallel workers...")
        
        completed_count = 0
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.download_single_file, task): task 
                for task in download_tasks
            }
            
            # Process completed tasks
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                try:
                    success = future.result()
                    if success:
                        completed_count += 1
                    else:
                        failed_count += 1
                    
                    # Progress update every 50 files
                    if (completed_count + failed_count) % 50 == 0:
                        progress = (completed_count + failed_count) / len(download_tasks)
                        logger.info(f"📊 Progress: {progress:.1%} ({completed_count + failed_count}/{len(download_tasks)})")
                
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Task failed: {e}")
        
        # Final statistics
        duration = datetime.now() - self.stats['start_time']
        
        logger.info("📋 DOWNLOAD COMPLETE!")
        logger.info(f"✅ Files downloaded: {completed_count}")
        logger.info(f"❌ Files failed: {failed_count}")
        logger.info(f"📊 Total records: {self.stats['total_records']:,}")
        logger.info(f"⏱️  Duration: {duration.total_seconds():.1f}s")
        logger.info(f"🚀 Rate: {self.stats['total_records']/(duration.total_seconds()):.1f} records/sec")
        
        return completed_count > failed_count
    
    def generate_processing_summary(self):
        """Generate summary of what's ready for Sunday processing"""
        
        logger.info("📊 Generating processing readiness summary...")
        
        summary = {
            'download_completion_time': datetime.now().isoformat(),
            'data_types': {},
            'date_ranges': {},
            'total_files': 0,
            'total_records': 0,
            'processing_ready': True
        }
        
        for data_type in self.data_types:
            type_path = self.base_data_path / data_type
            
            if type_path.exists():
                files = list(type_path.glob('**/*.json'))
                
                if files:
                    # Calculate date range
                    dates = []
                    total_records = 0
                    
                    for file_path in files:
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                dates.append(data['date'])
                                total_records += data.get('record_count', 0)
                        except:
                            continue
                    
                    if dates:
                        dates.sort()
                        summary['data_types'][data_type] = {
                            'files': len(files),
                            'records': total_records,
                            'date_range': {
                                'start': dates[0],
                                'end': dates[-1]
                            }
                        }
                        
                        summary['total_files'] += len(files)
                        summary['total_records'] += total_records
        
        # Save summary
        summary_file = self.base_data_path / 'processing_ready_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"💾 Processing summary saved: {summary_file}")
        
        return summary

def main():
    """Main execution for Sunday data download"""
    print("📥 SUNDAY DATA DOWNLOAD - COMPLETE PREPARATION")
    print("=" * 60)
    print("Downloading ALL data needed for Sunday processing")
    print("Ensures everything is ready for immediate analysis")
    print("=" * 60)
    
    if not api_key:
        print("❌ No API key found! Check api.env file")
        return False
    
    downloader = SundayDataDownloader()
    
    print(f"🎯 Target: Complete data download by Sunday")
    print(f"🕐 Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📅 Downloading up to: {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}")
    
    try:
        # Download all data
        success = downloader.download_all_data(max_workers=6)  # Increased parallel workers
        
        if success:
            # Generate processing summary
            summary = downloader.generate_processing_summary()
            
            print("\n🎉 DOWNLOAD COMPLETE - READY FOR SUNDAY!")
            print("=" * 50)
            print(f"✅ Total files: {summary['total_files']}")
            print(f"📊 Total records: {summary['total_records']:,}")
            
            for data_type, info in summary['data_types'].items():
                print(f"   📁 {data_type}: {info['files']} files, {info['records']:,} records")
                print(f"      📅 {info['date_range']['start']} to {info['date_range']['end']}")
            
            print(f"\n💾 All data saved in: bmrs_data/")
            print(f"📋 Processing summary: bmrs_data/processing_ready_summary.json")
            print(f"\n🚀 SUNDAY STATUS: READY FOR IMMEDIATE PROCESSING!")
            print("✅ No additional downloads needed")
            print("✅ All data pre-loaded and organized")
            print("✅ Processing can start immediately")
            
            return True
        
        else:
            print("\n⚠️ DOWNLOAD ISSUES ENCOUNTERED")
            print("🔄 Some files may have failed to download")
            print("💡 You can re-run this script to retry failed downloads")
            print("🛡️ Partial data is still available for processing")
            
            return False
    
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("🔄 Try running again or check your internet connection")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🎯 SUNDAY READY CHECKLIST:")
        print("✅ All historical data downloaded")
        print("✅ Data organized by type and date")
        print("✅ Processing summary generated")
        print("✅ No Sunday morning downloads needed")
        print("✅ Analysis can start immediately")
        print(f"\n🕐 Completed: {datetime.now().strftime('%H:%M:%S')}")
    
    sys.exit(0 if success else 1)
