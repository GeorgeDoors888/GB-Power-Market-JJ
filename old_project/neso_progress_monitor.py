#!/usr/bin/env python3
"""
NESO Download Progress Monitor
=============================
Monitors the incremental download progress and provides regular updates.
"""

import time
import json
from google.cloud import storage
from datetime import datetime

def monitor_neso_progress():
    """Monitor NESO download progress"""
    bucket_name = "jibber-jabber-knowledge-bmrs-data"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    print("🔍 NESO Download Progress Monitor Started")
    print("=" * 50)
    
    initial_count = count_neso_datasets(bucket)
    print(f"📊 Starting dataset count: {initial_count}")
    
    target_total = 116  # Total filtered datasets available
    start_time = datetime.now()
    
    while True:
        try:
            time.sleep(60)  # Check every minute
            
            current_count = count_neso_datasets(bucket)
            elapsed = datetime.now() - start_time
            
            # Calculate progress
            progress_pct = (current_count / target_total) * 100
            remaining = target_total - current_count
            
            # Estimate completion time
            if current_count > initial_count:
                download_rate = (current_count - initial_count) / (elapsed.total_seconds() / 3600)  # datasets per hour
                if download_rate > 0:
                    hours_remaining = remaining / download_rate
                    eta = datetime.now() + timedelta(hours=hours_remaining)
                    eta_str = eta.strftime("%H:%M")
                else:
                    eta_str = "calculating..."
            else:
                eta_str = "calculating..."
            
            print(f"\n📊 Progress Update ({datetime.now().strftime('%H:%M:%S')})")
            print(f"   ✅ Datasets downloaded: {current_count}/{target_total} ({progress_pct:.1f}%)")
            print(f"   ⏳ Remaining: {remaining}")
            print(f"   ⏱️  Elapsed: {elapsed}")
            print(f"   🎯 ETA: {eta_str}")
            
            if current_count >= target_total:
                print("\n🎉 Download Complete!")
                break
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n⚠️  Monitoring error: {e}")
            time.sleep(30)  # Wait longer on error

def count_neso_datasets(bucket):
    """Count how many NESO datasets we currently have"""
    blobs = bucket.list_blobs(prefix="neso_data/")
    datasets = set()
    
    for blob in blobs:
        if blob.name.endswith("/") or "session_summary" in blob.name or "incremental_summary" in blob.name:
            continue
            
        path_parts = blob.name.split("/")
        if len(path_parts) >= 2:
            dataset_name = path_parts[1]
            datasets.add(dataset_name)
    
    return len(datasets)

if __name__ == "__main__":
    from datetime import timedelta
    monitor_neso_progress()
