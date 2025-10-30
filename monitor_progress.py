#!/usr/bin/env python3
"""
Monitor ingestion progress and estimate completion time
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

def parse_log_file(log_file):
    """Parse the log file and extract progress information"""
    
    if not Path(log_file).exists():
        print(f"❌ Log file not found: {log_file}")
        return None
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Find the most recent dataset being processed
    dataset_matches = re.findall(r'Dataset: ([A-Z0-9]+):\s+(\d+)%.*\|\s+(\d+)/(\d+)', content)
    
    # Find start time
    start_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    start_time = None
    if start_match:
        start_time = datetime.strptime(start_match.group(1), '%Y-%m-%d %H:%M:%S')
    
    # Count successful loads
    success_pattern = r'✅ Successfully loaded \d+ rows to.*for window (202[45]-\d{2}-\d{2})'
    successful_loads = re.findall(success_pattern, content)
    
    # Find skip messages
    skip_pattern = r'Found (\d+) existing windows for ([A-Z0-9]+)\. Will skip'
    skipped_windows = re.findall(skip_pattern, content)
    
    # Get BOD specific progress
    bod_loads = [d for d in successful_loads if 'bod' in content[max(0, content.find(d)-200):content.find(d)].lower()]
    
    return {
        'current_dataset': dataset_matches[-1] if dataset_matches else None,
        'start_time': start_time,
        'successful_loads': len(successful_loads),
        'skipped_windows': skipped_windows,
        'bod_loads': len(bod_loads),
        'latest_loads': successful_loads[-10:] if successful_loads else []
    }

def estimate_completion(data):
    """Estimate completion time based on progress"""
    
    if not data or not data['start_time']:
        return None
    
    current_time = datetime.now()
    elapsed = (current_time - data['start_time']).total_seconds() / 60  # minutes
    
    # Estimate based on what we know:
    # - BOD: ~243 days total, 22 seconds per day = 89 minutes
    # - Other datasets: Mix of complete (skipped fast) and partial
    
    # If we've loaded BOD data, calculate its rate
    bod_rate_minutes = None
    if data['bod_loads'] > 0 and elapsed > 0:
        bod_rate_minutes = elapsed / data['bod_loads']
        bod_remaining = max(0, 243 - data['bod_loads'])
        bod_time_remaining = bod_remaining * bod_rate_minutes
    else:
        # Default estimate
        bod_time_remaining = 90  # ~1.5 hours
    
    # Account for other datasets (rough estimate)
    other_datasets_time = 300  # 5 hours for other partial datasets
    
    # Adjust based on skip info
    total_skipped = sum(int(count) for count, _ in data['skipped_windows'])
    if total_skipped > 1000:  # Many windows being skipped
        other_datasets_time = 120  # Reduce to 2 hours
    
    total_remaining = bod_time_remaining + other_datasets_time
    
    return {
        'elapsed_minutes': elapsed,
        'estimated_remaining_minutes': total_remaining,
        'estimated_completion': current_time + timedelta(minutes=total_remaining)
    }

def main():
    log_file = sys.argv[1] if len(sys.argv) > 1 else "jan_aug_ingest_20251027_000753.log"
    
    print("=" * 60)
    print("📊 INGESTION PROGRESS MONITOR")
    print("=" * 60)
    print(f"Log file: {log_file}")
    print()
    
    data = parse_log_file(log_file)
    
    if not data:
        return
    
    # Current status
    if data['current_dataset']:
        ds_name, pct, current, total = data['current_dataset']
        print(f"📦 Current Dataset: {ds_name}")
        print(f"   Progress: {pct}% ({current}/{total} chunks)")
        print()
    
    # Activity summary
    print(f"✅ Successful loads: {data['successful_loads']}")
    if data['bod_loads'] > 0:
        print(f"   BOD loads: {data['bod_loads']} days")
    print()
    
    # Skipped datasets
    if data['skipped_windows']:
        print("⏭️  Datasets with existing data (being skipped):")
        for count, dataset in data['skipped_windows']:
            print(f"   {dataset}: {count} windows")
        print()
    
    # Latest activity
    if data['latest_loads']:
        print("📝 Recent loads:")
        for date in data['latest_loads'][-5:]:
            print(f"   {date}")
        print()
    
    # Time estimates
    estimates = estimate_completion(data)
    if estimates:
        print("⏰ TIME ESTIMATE:")
        print(f"   Running for: {estimates['elapsed_minutes']:.1f} minutes")
        print(f"   Estimated remaining: {estimates['estimated_remaining_minutes']:.0f} minutes ({estimates['estimated_remaining_minutes']/60:.1f} hours)")
        print(f"   Expected completion: {estimates['estimated_completion'].strftime('%I:%M %p %Z')}")
        print()
    
    print("=" * 60)
    print("💡 TIP: Run this script again to update progress")
    print(f"   python3 monitor_progress.py {log_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
