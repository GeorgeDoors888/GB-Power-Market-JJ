#!/usr/bin/env python3
"""
Real-time Collection Status Dashboard
Shows progress of data collection processes
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

def check_collection_status():
    """Check current status of data collection"""
    
    print("📊 BMRS DATA COLLECTION STATUS")
    print("=" * 50)
    print(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check local directories
    data_dirs = ["bmrs_data", "bmrs_historical_data"]
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            print(f"\n📁 {data_dir.upper()}:")
            
            base_path = Path(data_dir)
            
            # Count files by data type
            for data_type_dir in base_path.iterdir():
                if data_type_dir.is_dir():
                    csv_files = list(data_type_dir.rglob("*.csv"))
                    
                    if csv_files:
                        total_size = sum(f.stat().st_size for f in csv_files) / (1024*1024)  # MB
                        latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
                        latest_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                        
                        print(f"   📊 {data_type_dir.name}:")
                        print(f"      Files: {len(csv_files)}")
                        print(f"      Size: {total_size:.1f} MB")
                        print(f"      Latest: {latest_file.name}")
                        print(f"      Modified: {latest_time.strftime('%H:%M:%S')}")
                    else:
                        print(f"   📊 {data_type_dir.name}: No files yet")
        else:
            print(f"\n📁 {data_dir.upper()}: Not created yet")
    
    # Check for test results
    test_files = [
        "updated_smoke_test_results_*.json",
        "historical_data_test_*.json", 
        "balancing_test_results_*.json"
    ]
    
    print(f"\n🧪 TEST RESULTS:")
    for pattern in test_files:
        matching_files = list(Path(".").glob(pattern))
        if matching_files:
            latest = max(matching_files, key=lambda f: f.stat().st_mtime)
            mod_time = datetime.fromtimestamp(latest.stat().st_mtime)
            print(f"   ✅ {latest.name} ({mod_time.strftime('%H:%M:%S')})")
        else:
            print(f"   ⚪ {pattern}: Not found")
    
    # Check running processes
    print(f"\n🔄 ACTIVE PROCESSES:")
    try:
        import psutil
        
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if 'python' in proc.info['name'] and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if any(script in cmdline for script in ['collection', 'test', 'smoke']):
                        create_time = datetime.fromtimestamp(proc.info['create_time'])
                        runtime = datetime.now() - create_time
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'script': cmdline.split('/')[-1] if '/' in cmdline else cmdline,
                            'runtime': str(runtime).split('.')[0]  # Remove microseconds
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if python_processes:
            for proc in python_processes:
                print(f"   🐍 PID {proc['pid']}: {proc['script']} (running {proc['runtime']})")
        else:
            print(f"   ⚪ No collection processes running")
            
    except ImportError:
        print(f"   ℹ️  Install psutil for process monitoring: pip install psutil")
    
    # Show disk usage
    print(f"\n💾 DISK USAGE:")
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            total_size = sum(f.stat().st_size for f in Path(data_dir).rglob("*") if f.is_file())
            print(f"   📁 {data_dir}: {total_size/(1024*1024):.1f} MB")

def monitor_collection(interval=30):
    """Monitor collection progress continuously"""
    
    print("🔄 Starting collection monitor...")
    print(f"   Refresh interval: {interval} seconds")
    print("   Press Ctrl+C to stop")
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
            check_collection_status()
            
            print(f"\n⏰ Next update in {interval} seconds...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n👋 Monitor stopped.")

def main():
    """Main status checker"""
    
    print("📊 Collection Status Options:")
    print("1. Show current status")
    print("2. Monitor continuously (30s intervals)")
    print("3. Quick file count")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        check_collection_status()
        
    elif choice == "2":
        monitor_collection()
        
    elif choice == "3":
        # Quick count
        for data_dir in ["bmrs_data", "bmrs_historical_data"]:
            if os.path.exists(data_dir):
                csv_count = len(list(Path(data_dir).rglob("*.csv")))
                print(f"{data_dir}: {csv_count} CSV files")
            else:
                print(f"{data_dir}: Not found")

if __name__ == "__main__":
    main()
