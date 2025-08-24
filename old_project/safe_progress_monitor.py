#!/usr/bin/env python3
"""
Non-Intrusive NESO Progress Monitor
==================================
Monitors download progress by checking cloud storage without interrupting the download process.
"""

import time
import json
from google.cloud import storage
from datetime import datetime, timedelta

def safe_monitor_progress():
    """Monitor progress without interrupting the download"""
    bucket_name = "jibber-jabber-knowledge-bmrs-data"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    print("🔍 NESO Download Progress Monitor (Non-Intrusive)")
    print("=" * 60)
    
    # Get initial count
    initial_count = count_datasets(bucket)
    target_total = 116  # Total filtered datasets available
    start_time = datetime.now()
    
    print(f"📊 Starting dataset count: {initial_count}")
    print(f"🎯 Target total: {target_total}")
    print(f"⏳ Remaining: {target_total - initial_count}")
    print("\nMonitoring every 2 minutes (matching download rate)...")
    print("Press Ctrl+C to stop monitoring (won't affect download)")
    
    while True:
        try:
            # Wait 2 minutes between checks (matches download rate)
            time.sleep(120)
            
            current_count = count_datasets(bucket)
            elapsed = datetime.now() - start_time
            
            # Calculate progress
            progress_pct = (current_count / target_total) * 100
            remaining = target_total - current_count
            new_downloads = current_count - initial_count
            
            # Estimate completion time
            if new_downloads > 0:
                download_rate = new_downloads / (elapsed.total_seconds() / 3600)  # datasets per hour
                if download_rate > 0:
                    hours_remaining = remaining / download_rate
                    eta = datetime.now() + timedelta(hours=hours_remaining)
                    eta_str = eta.strftime("%H:%M")
                else:
                    eta_str = "calculating..."
            else:
                eta_str = "calculating..."
            
            print(f"\n📊 Progress Update ({datetime.now().strftime('%H:%M:%S')})")
            print(f"   ✅ Total datasets: {current_count}/{target_total} ({progress_pct:.1f}%)")
            print(f"   📥 New downloads: {new_downloads}")
            print(f"   ⏳ Remaining: {remaining}")
            print(f"   ⏱️  Elapsed: {str(elapsed).split('.')[0]}")
            if download_rate > 0:
                print(f"   📈 Rate: {download_rate:.1f} datasets/hour")
            print(f"   🎯 ETA: {eta_str}")
            
            if current_count >= target_total:
                print("\n🎉 Download Complete!")
                print(f"✅ Total time: {str(elapsed).split('.')[0]}")
                break
                
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped by user")
            print(f"📊 Final count: {current_count}/{target_total}")
            print("ℹ️  Download process continues running independently")
            break
        except Exception as e:
            print(f"\n⚠️  Monitoring error: {e}")
            print("Retrying in 30 seconds...")
            time.sleep(30)

def count_datasets(bucket):
    """Count how many NESO datasets we currently have"""
    blobs = bucket.list_blobs(prefix="neso_data/")
    datasets = set()
    
    for blob in blobs:
        if (blob.name.endswith("/") or 
            "session_summary" in blob.name or 
            "incremental_summary" in blob.name):
            continue
            
        path_parts = blob.name.split("/")
        if len(path_parts) >= 2:
            dataset_name = path_parts[1]
            datasets.add(dataset_name)
    
    return len(datasets)

if __name__ == "__main__":
    safe_monitor_progress()
